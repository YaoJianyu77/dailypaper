"""Manage the single DailyPaper crontab entry and whole-run advisory lock."""

import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from zoneinfo import ZoneInfo

from report_settings import load_settings

BEGIN = '# BEGIN DailyPaper managed daily job'
END = '# END DailyPaper managed daily job'


@contextmanager
def exclusive_lock(root, name='run'):
    path = Path(root) / f'.cache/dailypaper/{name}.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps({'pid': os.getpid(), 'started_at': datetime.now().astimezone().isoformat()}))
        handle.flush()
        try:
            yield True
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def daily_schedule(settings):
    value = settings.tables['time windows'].get('daily schedule', '')
    match = re.match(r'(\d{2}):(\d{2})\s+([A-Za-z_/]+)\b', value)
    if not match:
        raise RuntimeError('Daily schedule must begin with HH:MM and an IANA timezone in the settings page')
    hour, minute, zone = int(match[1]), int(match[2]), match[3]
    if hour > 23 or minute > 59 or zone != settings.timezone:
        raise RuntimeError('Daily schedule is invalid or conflicts with Date and timezone')
    ZoneInfo(zone)
    return hour, minute, zone


def system_timezone():
    localtime = str(Path('/etc/localtime').resolve())
    if '/zoneinfo/' in localtime:
        zone = localtime.split('/zoneinfo/', 1)[1]
    elif Path('/etc/timezone').is_file():
        zone = Path('/etc/timezone').read_text().strip()
    else:
        raise RuntimeError('Cannot verify the system timezone needed to preserve unrelated cron schedules')
    ZoneInfo(zone)
    return zone


def read_crontab():
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    if result.returncode == 1 and 'no crontab for' in result.stderr.lower():
        return ''
    raise RuntimeError(f'Could not read existing crontab; nothing replaced: {result.stderr.strip()}')


def render_crontab(existing, root, python, path, schedule, default_timezone):
    root = str(Path(root).resolve())
    if any(character in root + python + path for character in ('\n', '\r')):
        raise RuntimeError('Newlines in runtime paths cannot be represented safely in cron')
    retained, in_block = [], False
    for line in existing.splitlines(keepends=True):
        if line.strip() == BEGIN:
            if in_block:
                raise RuntimeError('Malformed DailyPaper cron block; refusing to replace schedules')
            in_block = True
        elif line.strip() == END:
            if not in_block:
                raise RuntimeError('Malformed DailyPaper cron block; refusing to replace schedules')
            in_block = False
        elif not in_block:
            # Migrate only this checkout's old installer entry, never another project's job.
            try:
                tokens = shlex.split(line, comments=True)
            except ValueError:
                tokens = []  # Preserve unrelated syntax that this installer does not own.
            legacy = str(Path(root) / 'scripts/run_local_daily.py') in tokens
            if not legacy:
                retained.append(line)
    if in_block:
        raise RuntimeError('Unterminated DailyPaper cron block; nothing replaced')
    prefix = ''.join(retained)
    if prefix and not prefix.endswith('\n'):
        prefix += '\n'
    previous_zone = default_timezone
    for line in retained:
        match = re.match(r'^\s*CRON_TZ\s*=\s*(.*?)\s*$', line)
        if match:
            previous_zone = match[1]
    hour, minute, zone = schedule
    log = str(Path(root) / 'state/logs/local_daily.log')
    command = (f'cd {shlex.quote(root)} && PATH={shlex.quote(path)} '
               f'{shlex.quote(python)} {shlex.quote(str(Path(root) / "scripts/run_local_daily.py"))} '
               f'--repo-root {shlex.quote(root)} >> {shlex.quote(log)} 2>&1')
    # Cron interprets percent even inside shell quotes.
    command = command.replace('%', r'\%')
    return (prefix + f'{BEGIN}\nCRON_TZ={zone}\n{minute} {hour} * * * {command}\n'
            f'CRON_TZ={previous_zone}\n{END}\n')


def install(root, python, path):
    version = subprocess.run(['crontab', '-V'], capture_output=True, text=True)
    if version.returncode or 'cronie' not in (version.stdout + version.stderr).lower():
        raise RuntimeError('A Cronie scheduler with CRON_TZ support is required; no UTC approximation installed')
    active = subprocess.run(['pgrep', '-x', 'crond'], capture_output=True, text=True)
    if active.returncode:
        raise RuntimeError('Cronie is not running; enable the existing crond service before installation')
    # Cronie documents CRON_TZ. Other cron implementations must be verified before use.
    settings = load_settings(root)
    schedule = daily_schedule(settings)
    before = read_crontab()
    desired = render_crontab(before, root, python, path, schedule, system_timezone())
    if desired != before:
        if read_crontab() != before:
            raise RuntimeError('Crontab changed concurrently; retry installation without overwriting other schedules')
        subprocess.run(['crontab', '-'], input=desired, text=True, check=True)
    if read_crontab() != desired:
        raise RuntimeError('Installed crontab did not verify; inspect crontab -l')
    print(f'DailyPaper installed: {schedule[0]:02}:{schedule[1]:02} {schedule[2]}; one job, overlap lock enabled.')


def status(root):
    table = read_crontab()
    lines = table.splitlines()
    managed = False
    jobs = []
    for line in lines:
        if line == BEGIN:
            managed = True
        elif line == END:
            managed = False
        elif managed and line and not line.startswith(('CRON_TZ=', '#')):
            jobs.append(line)
    print(f'Managed DailyPaper jobs: {len(jobs)}')
    for job in jobs:
        print(job)
    hour, minute, zone = daily_schedule(load_settings(root))
    print(f'Configured daily time: {hour:02}:{minute:02} {zone} (daylight saving time follows the timezone)')
    active = subprocess.run(['pgrep', '-x', 'crond'], capture_output=True, text=True)
    print('Cron daemon: running' if active.returncode == 0 else 'Cron daemon: not running')
    with exclusive_lock(root) as acquired:
        print('Run status: idle' if acquired else 'Run status: running (lock held)')
    receipt = Path(root) / 'state/logs/runtime.json'
    if receipt.exists():
        value = json.loads(receipt.read_text())
        print(f'Last runtime verification: {value["checked_at"]}; model={value["model"]}; mode={value["mode"]}')
    print(f'Log: {Path(root) / "state/logs/local_daily.log"}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['install', 'status'])
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--path', default=os.environ.get('PATH', ''))
    args = parser.parse_args()
    if args.action == 'status':
        status(args.repo_root)
    else:
        install(args.repo_root, args.python, args.path)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.SubprocessError, OSError, ValueError) as error:
        raise SystemExit(f'DailyPaper schedule error: {error}')
