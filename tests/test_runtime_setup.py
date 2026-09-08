"""Offline model/permission/scheduler tests. No live account, cron or history writes."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
import codex_runtime as runtime
from codex_enrich import CodexBackend
from daily_pipeline import make_backend
from local_schedule import BEGIN, END, daily_schedule, exclusive_lock, install, read_crontab, render_crontab
from report_settings import load_settings


def recommendation(name='fixture-research'):
    return f'''## Recommended models
<ModelDetails name="Fixture" slug="{name}" description="Our most capable model for research."
data={{{{features: [{{ title: "Codex CLI", value: true }}]}}}} />
## Other models
'''


class FakeServer:
    mode = 'ultra'
    available = True
    calls = []
    final_events = []

    def __init__(self, *args, **kwargs):
        self.events = []
        self.pending = iter(self.final_events)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def receive(self, deadline):
        return next(self.pending)

    def call(self, method, params):
        self.calls.append((method, params))
        if method == 'account/read':
            return {'account': {'type': 'chatgpt'}}
        if method == 'model/list':
            return {'data': [{'model': 'fixture-research', 'hidden': False,
                    'supportedReasoningEfforts': [{'reasoningEffort': self.mode}], 'inputModalities': ['text', 'image']}]
                    if self.available else [], 'nextCursor': None}
        if method == 'skills/list':
            return {'data': [{'skills': [{'name': name, 'enabled': True, 'path': str(REPO / 'skills' / name / 'SKILL.md')}
                                        for name in runtime.skill_names()]}]}
        if method == 'thread/start':
            return {'model': params['model'], 'reasoningEffort': self.mode, 'modelProvider': 'openai',
                    'approvalPolicy': 'on-request', 'sandbox': {'type': 'workspaceWrite'}, 'thread': {'id': 'fixture-thread'}}
        if method == 'turn/start':
            return {'turn': {'id': 'fixture-turn'}}
        raise AssertionError(method)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings(REPO)
        FakeServer.calls = []
        FakeServer.mode = 'ultra'
        FakeServer.available = True

    def resolve(self):
        documents = [(recommendation(), {'url': 'official-fixture', 'sha256': 'a'}),
                     ('model_reasoning_effort **`ultra`**', {'url': 'official-fixture', 'sha256': 'b'})]
        with patch.object(runtime, 'official_document', side_effect=documents), \
             patch.object(runtime.shutil, 'which', return_value='/fixture/codex'), \
             patch.object(runtime.subprocess, 'check_output', return_value='fixture-cli'), \
             patch.object(runtime, 'AppServer', FakeServer):
            return runtime.resolve_runtime(REPO, self.settings)

    def test_current_official_recommendation_is_dynamic_and_unambiguous(self):
        self.assertEqual(runtime.recommended_model(recommendation('new-recommended-model')), 'new-recommended-model')
        for document in ('unrecognized format', recommendation().replace('research', 'coding'),
                         recommendation().replace('## Other models', recommendation('another-research'))):
            with self.assertRaises(runtime.RuntimeVerificationError):
                runtime.recommended_model(document)

    def test_available_model_requires_ultra_and_effective_confirmation(self):
        value = self.resolve()
        self.assertEqual((value['model'], value['mode']), ('fixture-research', 'ultra'))
        start = next(params for method, params in FakeServer.calls if method == 'thread/start')
        self.assertFalse(start['allowProviderModelFallback'])
        self.assertEqual(start['config']['agents.default_subagent_reasoning_effort'], 'ultra')
        self.assertNotIn('approvalPolicy', start)
        self.assertNotIn('approvalsReviewer', start)
        for mode in ('xhigh', 'max'):
            FakeServer.mode = mode
            with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'not advertise Ultra'):
                self.resolve()
        FakeServer.mode = 'ultra'
        FakeServer.available = False
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'not available'):
            self.resolve()

    def test_each_actual_turn_uses_exact_verified_model_mode_and_images(self):
        resolution = {'model': 'fixture-research', 'mode': 'ultra'}
        FakeServer.final_events = [
            {'method': 'item/completed', 'params': {'threadId': 'fixture-thread',
                'item': {'type': 'agentMessage', 'phase': 'final_answer', 'text': '{"ok": true}'}}},
            {'method': 'turn/completed', 'params': {'threadId': 'fixture-thread',
                'turn': {'id': 'fixture-turn', 'status': 'completed'}}}]
        with patch.object(runtime, 'AppServer', FakeServer):
            result, _ = runtime.execute('/fixture/codex', resolution, REPO, 'fixture', {}, images=[REPO / 'fixture.png'])
        self.assertTrue(result['ok'])
        start = next(params for method, params in FakeServer.calls if method == 'turn/start')
        self.assertEqual(start['model'], resolution['model'])
        self.assertEqual(start['effort'], 'ultra')
        self.assertEqual(start['input'][1]['type'], 'localImage')
        self.assertEqual(start['input'][1]['detail'], 'original')
        FakeServer.mode = 'xhigh'
        FakeServer.calls = []
        with patch.object(runtime, 'AppServer', FakeServer), self.assertRaisesRegex(runtime.RuntimeVerificationError, 'accept Ultra exactly'):
            runtime.execute('/fixture/codex', resolution, REPO, 'fixture', {})
        self.assertFalse(any(method == 'turn/start' for method, _ in FakeServer.calls))

    def test_discovery_uses_canonical_links_and_keeps_production_outside_scratch(self):
        runtime.verify_skill_links(REPO)
        with tempfile.TemporaryDirectory() as directory:
            runtime.prepare_workspace(REPO, directory)
            scratch = Path(directory)
            for name in runtime.skill_names():
                link = scratch / '.agents/skills' / name
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.resolve(), REPO / 'skills' / name)
            self.assertFalse((scratch / 'content').exists())
            self.assertFalse((scratch / 'state').exists())

    def test_preflight_failure_prevents_production_calls_and_no_api_fallback(self):
        backend = CodexBackend(REPO, self.settings, {})
        with patch('codex_enrich.resolve_runtime', return_value={}), \
             patch('codex_enrich.check_capabilities', side_effect=runtime.RuntimeVerificationError('Tool access failed')), \
             patch('codex_enrich.execute') as execute:
            with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'Tool access failed'):
                backend.generate('select', {})
            execute.assert_not_called()
        with self.assertRaisesRegex(RuntimeError, 'cannot verify this mode'):
            make_backend('github_models', REPO, self.settings, {})

    def test_unattended_protocol_never_grants_new_permissions(self):
        # Real subprocess exercises buffered notifications and authorization requests.
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'codex-fixture'
            executable.write_text('''#!/usr/bin/env python3
import sys,json
for line in sys.stdin:
    value=json.loads(line)
    if value.get('method') == 'initialize':
        print(json.dumps({'method':'notice','params':{}}),flush=True)
        print(json.dumps({'id':value['id'],'result':{}}),flush=True)
    elif value.get('method') == 'test':
        print(json.dumps({'id':99,'method':'item/commandExecution/requestApproval','params':{}}),flush=True)
''')
            executable.chmod(0o755)
            with runtime.AppServer(str(executable), directory, timeout=3) as server:
                with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'interactive authorization'):
                    server.call('test', {})


class ScheduleTests(unittest.TestCase):
    def test_reinstall_migrates_only_owned_job_preserves_unrelated_and_timezone(self):
        root = '/tmp/dailypaper project'
        before = ('MAILTO=owner@example.invalid\nCRON_TZ=Europe/London\n'
                  '3 2 * * * /another/scripts/run_local_daily.py\n'
                  "0 7 * * * python '/tmp/dailypaper project/scripts/run_local_daily.py'\n"
                  '# an unrelated comment\n4 5 * * * echo keep\n')
        args = (root, '/tmp/venv/bin/python', '/usr/bin:/bin', (7, 0, 'America/New_York'), 'UTC')
        first = render_crontab(before, *args)
        self.assertEqual(render_crontab(first, *args), first)
        self.assertEqual(first.count(BEGIN), 1)
        self.assertEqual(first.count(root + '/scripts/run_local_daily.py'), 1)
        self.assertIn('3 2 * * * /another/scripts/run_local_daily.py\n', first)
        self.assertIn('# an unrelated comment\n4 5 * * * echo keep\n', first)
        self.assertIn('CRON_TZ=America/New_York\n0 7 * * *', first)
        self.assertIn('CRON_TZ=Europe/London\n' + END, first)
        changed = render_crontab(first, root, '/new/python', '/usr/bin', (7, 0, 'America/New_York'), 'UTC')
        self.assertNotIn('/tmp/venv/bin/python', changed)
        self.assertEqual(changed.count(BEGIN), 1)

    def test_settings_schedule_and_dst_use_local_wall_time(self):
        settings = load_settings(REPO)
        self.assertEqual(daily_schedule(settings), (7, 0, 'America/New_York'))
        for day, hour_utc in ((datetime(2026, 1, 15, 7), 12), (datetime(2026, 7, 15, 7), 11)):
            self.assertEqual(day.replace(tzinfo=ZoneInfo(settings.timezone)).astimezone(timezone.utc).hour, hour_utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'DAILY_REPORT_PRODUCT_REQUIREMENTS.md'
            path.write_text(settings.raw.replace('07:00 America/New_York', '08:15 America/New_York'))
            self.assertEqual(daily_schedule(load_settings(directory)), (8, 15, 'America/New_York'))

    def test_install_updates_same_crontab_and_failure_does_not_replace_it(self):
        table = '4 5 * * * /unrelated/job\n'
        writes = []

        def run(cmd, **kwargs):
            nonlocal table
            if cmd == ['crontab', '-V']:
                output = 'cronie 1.5.7'
            elif cmd == ['pgrep', '-x', 'crond']:
                output = '123'
            elif cmd == ['crontab', '-l']:
                output = table
            else:
                self.assertEqual(cmd, ['crontab', '-'])
                table = kwargs['input']
                writes.append(table)
                output = ''
            return subprocess.CompletedProcess(cmd, 0, output, '')
        with patch('local_schedule.subprocess.run', side_effect=run), patch('local_schedule.system_timezone', return_value='UTC'):
            install(REPO, '/fixture/python', '/usr/bin')
            install(REPO, '/fixture/python', '/usr/bin')
        self.assertEqual(len(writes), 1)
        self.assertTrue(table.startswith('4 5 * * * /unrelated/job\n'))
        error = subprocess.CompletedProcess(['crontab', '-l'], 1, '', 'Permission denied')
        with patch('local_schedule.subprocess.run', return_value=error), self.assertRaisesRegex(RuntimeError, 'nothing replaced'):
            read_crontab()

    def test_lock_blocks_other_process_and_releases_after_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, '-c',
                'import sys; sys.path.insert(0,sys.argv[1]); from local_schedule import exclusive_lock; '
                'lock=exclusive_lock(sys.argv[2]); print(lock.__enter__()); lock.__exit__(None,None,None)',
                str(REPO / 'scripts'), directory]
            with exclusive_lock(directory) as acquired:
                self.assertTrue(acquired)
                self.assertEqual(subprocess.check_output(command, text=True).strip(), 'False')
            self.assertEqual(subprocess.check_output(command, text=True).strip(), 'True')

    def test_overlapping_runner_never_reaches_git_or_model_calls(self):
        import run_local_daily
        with tempfile.TemporaryDirectory() as directory, exclusive_lock(directory), \
             patch.object(sys, 'argv', ['run_local_daily.py', '--repo-root', directory]), \
             patch.object(run_local_daily, 'run_locked') as body:
            self.assertEqual(run_local_daily.main(), 75)
            body.assert_not_called()

    def test_malformed_owned_block_is_never_overwritten(self):
        with self.assertRaisesRegex(RuntimeError, 'Unterminated'):
            render_crontab(BEGIN + '\n', '/tmp/repo', '/python', '/bin', (7, 0, 'America/New_York'), 'UTC')


if __name__ == '__main__':
    unittest.main()
