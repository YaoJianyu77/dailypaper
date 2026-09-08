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


def reasoning_guidance(top='ultra'):
    return f'''### Reasoning effort (`model_reasoning_effort`)

- **`{top}`**: Use for the deepest reasoning when the selected model supports it.
- **`max`** and **`xhigh`**: Use for especially demanding reasoning when supported.
- **`high`**: Use for complex logic.
- **`medium`**: A balanced default.
- **`low`**: Use for straightforward tasks.

Higher reasoning effort needs more time.
</ContentModeSwitch>
'''


def completed_events():
    return [
        {'method': 'item/completed', 'params': {'threadId': 'fixture-thread',
            'item': {'type': 'agentMessage', 'phase': 'final_answer', 'text': '{"ok": true}'}}},
        {'method': 'turn/completed', 'params': {'threadId': 'fixture-thread',
            'turn': {'id': 'fixture-turn', 'status': 'completed'}}}]


class FakeServer:
    def __init__(self, *args, **kwargs):
        self.events = []
        self.pending = iter(self.final_events)
        self.selected = self.catalog_model
        self.effort = self.supported[-1]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def receive(self, deadline):
        event = next(self.pending)
        self.thread_overrides.update(event.get('fixture_thread_changes', {}))
        return event

    def call(self, method, params):
        self.calls.append((method, params))
        if method == 'account/read':
            return {'account': {'type': 'chatgpt'} if self.authenticated else None}
        if method == 'model/list':
            return {'data': [{'model': self.catalog_model, 'hidden': False,
                    'supportedReasoningEfforts': [{'reasoningEffort': level} for level in self.supported],
                    'inputModalities': ['text', 'image']}]
                    if self.available else [], 'nextCursor': None}
        if method == 'skills/list':
            return {'data': [{'skills': [{'name': name, 'enabled': True, 'path': str(REPO / 'skills' / name / 'SKILL.md')}
                                        for name in runtime.skill_names()]}]}
        if method == 'thread/start':
            self.selected = self.model_override or params['model']
            self.effort = self.effort_override or params['config']['model_reasoning_effort']
            return {'model': self.selected, 'reasoningEffort': self.effort, 'modelProvider': 'openai',
                    'approvalPolicy': 'on-request', 'sandbox': {'type': 'workspaceWrite'}, 'thread': {'id': 'fixture-thread'}}
        if method == 'thread/read':
            thread = {'id': params['threadId'], 'model': self.selected, 'reasoningEffort': self.effort,
                      'modelProvider': 'openai', 'cliVersion': 'fixture-cli'}
            thread.update(self.thread_overrides.get(params['threadId'], {}))
            return {'thread': thread}
        if method == 'turn/start':
            return {'turn': {'id': 'fixture-turn'}}
        raise AssertionError(method)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings(REPO)
        FakeServer.calls = []
        FakeServer.catalog_model = 'fixture-research'
        FakeServer.supported = ['low', 'medium', 'high', 'xhigh', 'max', 'ultra']
        FakeServer.available = True
        FakeServer.authenticated = True
        FakeServer.model_override = None
        FakeServer.effort_override = None
        FakeServer.thread_overrides = {}
        FakeServer.final_events = completed_events()
        self.resolution = {'model': 'fixture-research', 'mode': 'ultra', 'cli_version': 'fixture-cli',
                           'executable': '/fixture/codex', 'settings_sha256': self.settings.sha256}

    def resolve(self, models=None, guidance=None):
        documents = [(models or recommendation(), {'url': 'official-fixture', 'sha256': 'a'}),
                     (guidance or reasoning_guidance(), {'url': 'official-fixture', 'sha256': 'b'})]
        with patch.object(runtime, 'official_document', side_effect=documents), \
             patch.object(runtime.shutil, 'which', return_value='/fixture/codex'), \
             patch.object(runtime.subprocess, 'check_output', return_value='fixture-cli'), \
             patch.object(runtime, 'AppServer', FakeServer):
            return runtime.resolve_runtime(REPO, self.settings)

    def execute(self):
        with patch.object(runtime, 'AppServer', FakeServer), \
             patch.object(runtime.subprocess, 'check_output', return_value='fixture-cli'):
            return runtime.execute('/fixture/codex', self.resolution, REPO, 'fixture', {}, images=[REPO / 'fixture.png'])

    def test_current_official_recommendation_is_dynamic_and_unambiguous(self):
        self.assertEqual(runtime.recommended_model(recommendation('new-recommended-model')), 'new-recommended-model')
        for document in ('unrecognized format', recommendation().replace('research', 'coding'),
                         recommendation().replace('## Other models', recommendation('another-research'))):
            with self.assertRaises(runtime.RuntimeVerificationError):
                runtime.recommended_model(document)

    def test_new_flagship_wins_over_newer_names_or_defaults(self):
        FakeServer.catalog_model = 'future-research-flagship'
        models = recommendation(FakeServer.catalog_model).replace('## Other models',
            '<ModelDetails slug="newer-fast-default" description="Our newest model and default for quick tasks." '
            'data={{features: [{ title: "Codex CLI", value: true }]}} />\n## Other models')
        value = self.resolve(models=models)
        self.assertEqual(value['model'], FakeServer.catalog_model)
        self.assertIn('most capable', value['selection_evidence']['model_recommendation']['description'])

    def test_available_model_requires_official_maximum_and_effective_confirmation(self):
        value = self.resolve()
        self.assertEqual((value['model'], value['mode']), ('fixture-research', 'ultra'))
        start = next(params for method, params in FakeServer.calls if method == 'thread/start')
        self.assertFalse(start['allowProviderModelFallback'])
        self.assertEqual(start['config']['agents.default_subagent_reasoning_effort'], 'ultra')
        self.assertNotIn('approvalPolicy', start)
        self.assertNotIn('approvalsReviewer', start)
        self.assertEqual(start['config']['agents.default_subagent_model'], value['model'])
        self.assertEqual(value['selection_evidence']['reasoning']['selected'], 'ultra')
        self.assertEqual(value['cli_version'], 'fixture-cli')

    def test_new_reasoning_level_is_selected_from_guidance_and_account_support(self):
        FakeServer.supported = ['zenith', 'low', 'ultra', 'max', 'xhigh']
        guidance = reasoning_guidance('zenith').replace('- **`max`**',
            '- **`ultra`**: Use for demanding reasoning.\n- **`max`**')
        value = self.resolve(guidance=guidance)
        self.assertEqual(value['mode'], 'zenith')
        start = next(params for method, params in FakeServer.calls if method == 'thread/start')
        self.assertEqual(start['config']['model_reasoning_effort'], 'zenith')
        self.assertEqual(start['config']['agents.default_subagent_reasoning_effort'], 'zenith')
        self.resolution = value
        self.assertTrue(self.execute()[0]['ok'])
        turn = next(params for method, params in FakeServer.calls if method == 'turn/start')
        self.assertEqual(turn['effort'], 'zenith')
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'does not document'):
            self.resolve()

    def test_ambiguous_or_conflicting_reasoning_order_stops(self):
        FakeServer.supported = ['max', 'xhigh']
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'does not uniquely order'):
            self.resolve()
        guidance = reasoning_guidance().replace('Higher reasoning',
            'Reasoning effort order: `xhigh` < `max` < `ultra`.\n\nHigher reasoning')
        resolved = self.resolve(guidance=guidance)
        self.assertEqual(resolved['mode'], 'max')
        self.assertIn('Reasoning effort order: `xhigh` < `max` < `ultra`.',
                      resolved['selection_evidence']['reasoning']['ordering_statements'])
        contradictory = guidance.replace('`xhigh` < `max` < `ultra`', '`ultra` < `max` < `xhigh`')
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'contradictory ordering'):
            self.resolve(guidance=contradictory)
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'format changed'):
            self.resolve(guidance='Unrecognized future reasoning documentation')

    def test_unavailable_account_or_model_never_falls_back(self):
        FakeServer.available = False
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'not available'):
            self.resolve()
        FakeServer.available = True
        FakeServer.authenticated = False
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'not authenticated'):
            self.resolve()
        self.assertFalse(any(method == 'turn/start' for method, _ in FakeServer.calls))

    def test_each_actual_turn_uses_exact_verified_model_mode_and_images(self):
        result, _ = self.execute()
        self.assertTrue(result['ok'])
        start = next(params for method, params in FakeServer.calls if method == 'turn/start')
        self.assertEqual(start['model'], self.resolution['model'])
        self.assertEqual(start['effort'], 'ultra')
        self.assertEqual(start['input'][1]['type'], 'localImage')
        self.assertEqual(start['input'][1]['detail'], 'original')
        self.assertIn('Explicitly use these exact values', start['input'][0]['text'])

    def test_runtime_substitution_is_rejected_before_generation(self):
        for field, value in (('effort_override', 'xhigh'), ('model_override', 'other-model')):
            with self.subTest(field=field):
                setattr(FakeServer, field, value)
                FakeServer.calls = []
                with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'substituted'):
                    self.execute()
                self.assertFalse(any(method == 'turn/start' for method, _ in FakeServer.calls))
                setattr(FakeServer, field, None)
        # The initial settings can match while the effective end-of-turn settings differ.
        for field, value in (('model', 'other-model'), ('reasoningEffort', 'xhigh')):
            FakeServer.thread_overrides = {}
            FakeServer.final_events = completed_events()
            FakeServer.final_events[-1]['fixture_thread_changes'] = {'fixture-thread': {field: value}}
            with self.subTest(late_change=field), self.assertRaisesRegex(runtime.RuntimeVerificationError, 'substituted'):
                self.execute()

    def test_runtime_reroute_during_parent_or_child_turn_is_rejected(self):
        for thread in ('fixture-thread', 'child'):
            FakeServer.final_events = [{'method': 'model/rerouted', 'params': {
                'threadId': thread, 'fromModel': self.resolution['model'], 'toModel': 'substitute'}}] + completed_events()
            with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'rerouted'):
                self.execute()

    def test_subagents_and_grandchildren_require_exact_effective_settings(self):
        def activity(parent, child, kind):
            return {'method': 'item/completed', 'params': {'threadId': parent, 'item': {
                'type': 'subAgentActivity', 'agentThreadId': child, 'kind': kind}}}
        FakeServer.final_events = [activity('fixture-thread', 'child', 'started'),
            activity('child', 'grandchild', 'started'), activity('child', 'grandchild', 'completed'),
            activity('fixture-thread', 'child', 'completed')] + completed_events()
        self.assertTrue(self.execute()[0]['ok'])
        reads = {params['threadId'] for method, params in FakeServer.calls if method == 'thread/read'}
        self.assertEqual(reads, {'fixture-thread', 'child', 'grandchild'})
        for field, value in (('model', 'other'), ('reasoningEffort', 'high'), ('reasoningEffort', None),
                             ('modelProvider', 'other'), ('cliVersion', 'changed')):
            with self.subTest(field=field, value=value):
                FakeServer.thread_overrides = {'grandchild': {field: value}}
                with self.assertRaises(runtime.RuntimeVerificationError):
                    self.execute()

    def test_unfinished_subagent_prevents_accepting_parent_result(self):
        FakeServer.final_events.insert(0, {'method': 'item/completed', 'params': {
            'threadId': 'fixture-thread', 'item': {'type': 'subAgentActivity', 'agentThreadId': 'child', 'kind': 'started'}}})
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'still running'):
            self.execute()

    def test_codex_version_cannot_change_between_calls(self):
        self.resolution['cli_version'] = 'previous-version'
        with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'version changed'):
            self.execute()
        self.assertEqual(FakeServer.calls, [])

    def test_preflight_is_frozen_and_callers_cannot_mutate_it(self):
        backend = CodexBackend(REPO, self.settings, {})
        with patch('codex_enrich.resolve_runtime', return_value=dict(self.resolution)) as resolve, \
             patch('codex_enrich.check_capabilities', return_value={'fixture': True}):
            first = backend.preflight()
            first['mode'] = 'other'
            self.assertEqual(backend.preflight()['mode'], 'ultra')
            self.assertEqual(resolve.call_count, 1)
            backend.resolution['model'] = 'other'
            with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'configuration was changed'):
                backend.preflight()

    def test_retry_keeps_runtime_evidence_and_rejects_mixed_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            runtime.bind_report(stage, self.resolution)
            (stage / 'selection.json').write_text('["existing-selection"]')
            before = {p.name: p.read_bytes() for p in stage.iterdir()}
            refreshed = {**self.resolution, 'checked_at': 'later'}
            self.assertEqual(runtime.bind_report(stage, refreshed), self.resolution)
            for key in ('model', 'mode', 'cli_version', 'settings_sha256'):
                with self.subTest(key=key), self.assertRaisesRegex(runtime.RuntimeVerificationError, 'Mixed configurations'):
                    runtime.bind_report(stage, {**refreshed, key: 'new-value'})
            self.assertEqual({p.name: p.read_bytes() for p in stage.iterdir()}, before)
            (stage / 'runtime.json').unlink()
            with self.assertRaisesRegex(runtime.RuntimeVerificationError, 'lacks a verified runtime'):
                runtime.bind_report(stage, self.resolution)

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
        with self.assertRaisesRegex(RuntimeError, 'cannot verify this policy'):
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
