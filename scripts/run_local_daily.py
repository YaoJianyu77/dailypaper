#!/usr/bin/env python3
"""Run the local daily-paper pipeline and push results to GitHub."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from content_store import get_repo_root
from daily_pipeline import prepare, make_backend
from local_schedule import exclusive_lock
from publish_daily import publish, verify_archived_run
from recommendation_history import HISTORY_PATH, load_history
from report_settings import load_infrastructure, load_settings

logger = logging.getLogger(__name__)


def load_local_env(repo_root: Path) -> None:
    for env_name in ('.env.local', '.env'):
        env_path = repo_root / env_name
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[len('export '):].strip()
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value


def run(cmd: List[str], *, cwd: Path, env: Dict[str, str] | None = None) -> None:
    logger.info('Running: %s', ' '.join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True, env=env)


def capture(cmd: List[str], *, cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=True)
    return result.stdout.strip()


def is_git_clean(repo_root: Path) -> bool:
    return not capture(['git', 'status', '--porcelain'], cwd=repo_root)


def pick_remote(repo_root: Path, preferred: str | None) -> str:
    remotes = [line.strip() for line in capture(['git', 'remote'], cwd=repo_root).splitlines() if line.strip()]
    if preferred:
        if preferred not in remotes:
            raise SystemExit(f'Remote {preferred!r} not found. Available remotes: {", ".join(remotes) or "(none)"}')
        return preferred

    try:
        upstream = capture(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}'], cwd=repo_root)
        upstream_remote = upstream.split('/', 1)[0]
        if upstream_remote in remotes:
            return upstream_remote
    except subprocess.CalledProcessError:
        pass

    for candidate in ['origin', 'dailypaper']:
        if candidate in remotes:
            return candidate

    if remotes:
        return remotes[0]

    raise SystemExit('No git remote configured. Add a GitHub remote before running the local pipeline.')


def infer_site_base_url(repo_root: Path, remote_name: str, config: Dict[str, Any]) -> str:
    site_settings = config.get('site', {}) if isinstance(config, dict) else {}
    configured = str(site_settings.get('base_url') or '').strip()
    if configured:
        return configured

    try:
        remote_url = capture(['git', 'remote', 'get-url', remote_name], cwd=repo_root)
    except subprocess.CalledProcessError:
        return ''

    match = re.search(r'[:/]([^/:]+)/([^/]+?)(?:\.git)?$', remote_url)
    if not match:
        return ''

    owner, repo_name = match.groups()
    if repo_name == f'{owner}.github.io':
        return ''
    return f'/{repo_name}'


def verify_runtime(repo_root, enricher='codex'):
    settings = load_settings(repo_root)
    backend = make_backend(enricher, repo_root, settings, load_infrastructure(repo_root))
    resolution = backend.preflight()
    log_dir = repo_root / 'state/logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    from recommendation_history import atomic_write
    atomic_write(log_dir / 'runtime.json', (json.dumps(resolution, indent=2) + '\n').encode(), replace=True)
    logger.info('Run %s runtime verified: model=%s mode=%s', settings.run_id(settings.local_date()),
                resolution['model'], resolution['mode'])
    return backend


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Run local daily paper generation and push results')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    parser.add_argument('--skip-push', action='store_true', help='Generate locally without pushing')
    parser.add_argument('--dry-run', action='store_true', help='Prepare and render in a temporary workspace without publishing, committing, or pushing')
    parser.add_argument('--check-runtime', action='store_true', help='Verify the strongest model/reasoning, subagents, tools and skill routing using a synthetic PDF; no report or history writes')
    parser.add_argument('--enricher', choices=['codex', 'openai', 'github_models'], default='codex', help='Production requires the verified strongest Codex model and reasoning; API transports fail closed')
    parser.add_argument('--remote', default=None, help='Git remote to pull from and push to (auto-detected by default)')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    load_local_env(repo_root)
    with exclusive_lock(repo_root) as acquired:
        if not acquired:
            logger.warning('Another DailyPaper run holds the lock; overlapping invocation skipped')
            return 75
        return run_locked(repo_root, args)


def run_locked(repo_root, args):
    logger.info('DailyPaper invocation started (pid=%s)', os.getpid())
    if args.check_runtime:
        verify_runtime(repo_root, args.enricher)
        return 0
    if args.dry_run:
        import tempfile
        backend = verify_runtime(repo_root, args.enricher)
        with tempfile.TemporaryDirectory(prefix='dailypaper-dry-run-') as directory:
            bundle = prepare(repo_root, args.enricher, backend=backend, stage_dir=Path(directory))
            logger.info('Isolated preparation verified: %s; production content and history unchanged', bundle['run_id'])
        return 0
    if capture(['git', 'branch', '--show-current'], cwd=repo_root) != 'main':
        raise RuntimeError('Daily generation must run on the existing main branch')
    remote_name = pick_remote(repo_root, args.remote)
    clean = is_git_clean(repo_root)
    if clean:
        run(['git', 'pull', '--ff-only', remote_name, 'main'], cwd=repo_root)
    # Read settings after synchronization, never retain a pre-pull configuration.
    settings = load_settings(repo_root)
    config = load_infrastructure(repo_root)
    current_run = load_history(repo_root).run(settings.run_id(settings.local_date()))
    if not clean:
        if not current_run:
            raise RuntimeError('Unrelated uncommitted changes; refusing to include them in generation')
        allowed = {HISTORY_PATH, f'content/daily/{current_run["local_date"]}.md',
                   *[asset.get('path') or asset.get('repo_path') for asset in current_run.get('visual_assets', [])]}
        changed = set(capture(['git', 'diff', '--name-only', 'HEAD'], cwd=repo_root).splitlines())
        untracked = set(capture(['git', 'ls-files', '--others', '--exclude-standard'], cwd=repo_root).splitlines())
        if (changed | untracked) - allowed:
            raise RuntimeError('Unrelated changes exist alongside the recoverable run')
    backend = verify_runtime(repo_root, args.enricher)
    bundle = prepare(repo_root, args.enricher, backend=backend)
    if bundle.get('already_archived'):
        current_run = load_history(repo_root).run(bundle['run_id'])
        report_path = verify_archived_run(repo_root, current_run)
        result = {'paths': [HISTORY_PATH, report_path,
                           *[a.get('path') or a.get('repo_path') for a in current_run.get('visual_assets', [])]]}
    else:
        run(['git', 'fetch', remote_name, 'main'], cwd=repo_root)
        if clean:
            run(['git', 'merge', '--ff-only', f'{remote_name}/main'], cwd=repo_root)
        result = publish(repo_root, bundle)
    env = dict(os.environ)
    env.setdefault('SITE_BASE_URL', infer_site_base_url(repo_root, remote_name, config))
    run([sys.executable, str(repo_root / 'scripts/build_site.py'), '--repo-root', str(repo_root)], cwd=repo_root, env=env)
    run(['git', 'add', '--', *result['paths']], cwd=repo_root)
    diff = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=str(repo_root))
    if diff.returncode == 1:
        staged = set(capture(['git', 'diff', '--cached', '--name-only'], cwd=repo_root).splitlines())
        if staged - set(result['paths']):
            raise RuntimeError('Unrelated staged changes; refusing to commit')
        run(['git', 'commit', '-m', f'chore: archive {bundle["run_id"]}'], cwd=repo_root)
    elif diff.returncode != 0:
        raise RuntimeError('Could not verify staged content')
    if not args.skip_push:
        outgoing = set(capture(['git', 'diff', '--name-only', f'{remote_name}/main', 'HEAD'], cwd=repo_root).splitlines())
        if outgoing - set(result['paths']):
            raise RuntimeError('Unrelated outgoing commits or concurrent changes; refusing to push')
        run(['git', 'push', remote_name, 'HEAD:main'], cwd=repo_root)
    logger.info('Run verified: %s', bundle['run_id'])
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        logger.error('DailyPaper stopped: %s', error)
        raise SystemExit(1)
