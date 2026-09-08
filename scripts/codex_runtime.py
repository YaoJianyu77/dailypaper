"""Verify current official recommendations against the authenticated Codex runtime."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import queue
import re
import signal
import shutil
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlparse

import requests

from pipeline_prompts import STAGE_SKILLS

logger = logging.getLogger(__name__)
OFFICIAL_HOSTS = {'learn.chatgpt.com', 'developers.openai.com', 'platform.openai.com'}


class RuntimeVerificationError(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise RuntimeVerificationError(message)


def skill_names():
    return tuple(dict.fromkeys(name for names in STAGE_SKILLS.values() for name in names))


def verify_skill_links(root):
    root = Path(root).resolve()
    for name in skill_names():
        link = root / '.agents/skills' / name
        require(link.is_symlink() and link.resolve() == root / 'skills' / name,
                f'Skill discovery link is missing or incorrect: {link}')
        require((link / 'SKILL.md').is_file(), f'Skill instructions are missing: {link}')


def prepare_workspace(root, directory):
    """Expose source instructions through links; only the scratch root is writable."""
    root, directory = Path(root).resolve(), Path(directory).resolve()
    verify_skill_links(root)
    for name in ('AGENTS.md', 'PROJECT_STATE.md', 'DAILY_REPORT_PRODUCT_REQUIREMENTS.md', 'skills', 'scripts'):
        source = root / name
        if source.exists():
            (directory / name).symlink_to(source, target_is_directory=source.is_dir())
    links = directory / '.agents/skills'
    links.mkdir(parents=True)
    for name in skill_names():
        (links / name).symlink_to(root / 'skills' / name, target_is_directory=True)


class AppServer:
    """Installed non-interactive Codex protocol, retaining permission safeguards."""
    def __init__(self, executable, cwd, timeout=45):
        self.executable, self.cwd, self.timeout = executable, str(cwd), timeout

    def __enter__(self):
        self.process = subprocess.Popen([self.executable, '--search', 'app-server', '--strict-config', '--listen', 'stdio://'],
            cwd=self.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1, start_new_session=True)
        self.messages = queue.Queue()
        self.events = []

        def read_messages():
            for line in self.process.stdout:
                self.messages.put(line)
            self.messages.put(None)
        self.reader = threading.Thread(target=read_messages, daemon=True)
        self.reader.start()
        self.sequence = 0
        try:
            self.call('initialize', {'clientInfo': {'name': 'dailypaper', 'version': '1'},
                                     'capabilities': {'experimentalApi': True}})
            self.send({'method': 'initialized', 'params': {}})
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def send(self, value):
        self.process.stdin.write(json.dumps(value) + '\n')
        self.process.stdin.flush()

    def call(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.send({'id': request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            value = self.receive(deadline)
            if value.get('id') == request_id and ('result' in value or 'error' in value):
                require('error' not in value, f'Codex could not verify {method}: {value.get("error")}')
                return value['result']
            self.events.append(value)
        raise RuntimeVerificationError(f'Timed out verifying Codex {method}; generation stopped')

    def receive(self, deadline):
        try:
            line = self.messages.get(timeout=max(0, deadline - time.monotonic()))
        except queue.Empty as error:
            raise RuntimeVerificationError('Codex runtime timed out; generation stopped without a fallback') from error
        require(line, 'Codex app-server stopped unexpectedly')
        value = json.loads(line)
        if 'method' in value and 'id' in value:
            # This unattended client never approves escalation, login, or new permissions.
            raise RuntimeVerificationError(f'Codex requires interactive authorization ({value["method"]}); unattended run stopped. Use the existing login/permission controls interactively.')
        return value

    def __exit__(self, *args):
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGTERM)
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
        self.reader.join(timeout=2)
        self.process.stdin.close()
        self.process.stdout.close()


def policy_sources(settings):
    section = settings.sections['per-paper content']
    rows = settings.tables['per-paper content']
    require(rows.get('required codex mode', '').startswith('Strongest supported reasoning'),
            'The settings must require the strongest supported reasoning verified against official guidance')
    require('most capable' in rows.get('production model policy', '').lower(), 'The unified production model policy is missing')
    urls = []
    for label in ('Production model policy', 'Required Codex mode'):
        match = re.search(r'^\|\s*' + re.escape(label) + r'\s*\|(.+)$', section, re.M)
        links = re.findall(r'\]\((https://[^)]+)\)', match.group(1) if match else '')
        require(len(links) == 1, f'{label} needs one official evidence link in the settings file')
        require(urlparse(links[0]).hostname in OFFICIAL_HOSTS, 'Model-policy evidence must come from official OpenAI documentation')
        urls.append(links[0])
    return urls


def official_document(url):
    response = requests.get(url, headers={'Cache-Control': 'no-cache'}, timeout=45)
    response.raise_for_status()
    require(urlparse(response.url).hostname in OFFICIAL_HOSTS, 'Official documentation redirected to an unverified host')
    require(response.text.strip(), 'Official documentation is empty; generation stopped')
    return response.text, {'url': response.url, 'sha256': hashlib.sha256(response.content).hexdigest()}


def model_recommendation(document):
    match = re.search(r'^## Recommended models\s*$(.*?)(?=^## Other models\s*$|\Z)', document, re.M | re.S)
    require(match, 'Official recommendation format changed; the strongest research model cannot be verified')
    strongest = []
    for card in re.findall(r'<ModelDetails\b.*?/>', match.group(1), re.S):
        slug = re.search(r'\bslug="([a-zA-Z0-9._-]+)"', card)
        description = re.search(r'\bdescription="([^"]+)"', card)
        if slug and description and re.search(r'most (?:capable|intelligent) model\b', description.group(1), re.I):
            if re.search(r'\bresearch\b', description.group(1), re.I) and re.search(r'title:\s*"Codex CLI",\s*value:\s*true', card):
                strongest.append({'model': slug.group(1), 'description': description.group(1)})
    require(len(strongest) == 1, 'Official guidance does not uniquely identify the most capable recommended Codex research model; no fallback selected')
    return strongest[0]


def recommended_model(document):
    return model_recommendation(document)['model']


def strongest_reasoning(document, supported):
    """Establish a unique maximum from official statements, never name/list order.

    An explicit deepest-reasoning statement establishes a top tier. Explicit
    inequality chains can establish additional relationships. Grouped levels
    remain incomparable unless the source separately orders them.
    """
    section = re.search(r'^### Reasoning effort \(`model_reasoning_effort`\)\s*\n(.*?)(?=^#{1,3} |</ContentModeSwitch>|\Z)',
                        document, re.M | re.S)
    require(section, 'Official reasoning guidance format changed; ordering cannot be verified')
    text = section[1]
    entries, maxima = {}, []
    for match in re.finditer(r'^- (.+?)(?=\n\n|\n- |\Z)', text, re.M | re.S):
        label, separator, description = match[1].partition(':')
        names = re.findall(r'`([a-zA-Z0-9_-]+)`', label)
        require(separator and names, 'Official reasoning entry cannot be interpreted safely')
        description = ' '.join(description.split())
        for name in names:
            require(name not in entries, 'Official reasoning guidance contains duplicate or conflicting levels')
            entries[name] = description
        if re.match(r'Use for (?:the )?(?:deepest|strongest|highest|maximum) reasoning(?: when|[.,]|$)', description, re.I):
            maxima.append(names)
    levels = [entry.get('reasoningEffort') for entry in supported]
    require(levels and all(isinstance(level, str) and level for level in levels) and len(set(levels)) == len(levels),
            'The selected model has no verifiable supported reasoning settings')
    require(set(levels) <= set(entries),
            f'Official guidance does not document supported reasoning levels: {sorted(set(levels) - set(entries))}; no lower level selected')
    require(len(maxima) <= 1, 'Official guidance names conflicting strongest reasoning tiers')
    stronger = {name: set() for name in entries}
    ordering_statements = []
    if maxima:
        ordering_statements.append(entries[maxima[0][0]])
        for name in maxima[0]:
            stronger[name].update(set(entries) - set(maxima[0]))
    for line in text.splitlines():
        if not line.startswith('Reasoning effort order:'):
            continue
        ordering_statements.append(line)
        chain = line.removeprefix('Reasoning effort order:').strip().rstrip('.')
        require(re.fullmatch(r'`[a-zA-Z0-9_-]+`(?:\s*[<>]\s*`[a-zA-Z0-9_-]+`)+', chain),
                'Official reasoning order cannot be interpreted safely')
        names = re.findall(r'`([^`]+)`', chain)
        signs = re.findall(r'[<>]', chain)
        require(len(set(names)) == len(names) and set(names) <= set(entries) and len(set(signs)) == 1,
                'Official reasoning ordering is contradictory or incomplete')
        for left, right, sign in zip(names, names[1:], signs):
            higher, lower = (left, right) if sign == '>' else (right, left)
            stronger[higher].add(lower)
    for _ in entries:
        for name in entries:
            stronger[name].update({other for lower in list(stronger[name]) for other in stronger[lower]})
    require(all(name not in below for name, below in stronger.items()), 'Official reasoning guidance has a contradictory ordering')
    winners = [name for name in levels if set(levels) - {name} <= stronger[name]]
    require(len(winners) == 1, 'Official guidance does not uniquely order the strongest supported reasoning setting; no downgrade selected')
    selected = winners[0]
    return selected, {'supported': supported, 'documented': entries,
                      'stronger_than': {name: sorted(below) for name, below in stronger.items()},
                      'selected': selected, 'ordering_statements': ordering_statements}


def resolution_identity(resolution):
    require(all(resolution.get(key) for key in ('model', 'mode', 'cli_version', 'settings_sha256')),
            'Report runtime identity is incomplete; generation stopped')
    return {key: resolution[key] for key in ('model', 'mode', 'cli_version', 'settings_sha256')}


def bind_report(stage, resolution):
    """Freeze the resolved configuration beside existing preparation checkpoints."""
    from recommendation_history import atomic_write, json_bytes
    stage = Path(stage)
    stage.mkdir(parents=True, exist_ok=True)
    path = stage / 'runtime.json'
    if path.exists():
        original = json.loads(path.read_text())
        require(resolution_identity(original) == resolution_identity(resolution),
                'Current policy resolves a different model, reasoning, Codex version, or settings than this pending report; '
                'keep its selection and explicitly revalidate before resuming. Mixed configurations are forbidden.')
        return original
    require(not any(stage.iterdir()), 'Pending report lacks a verified runtime record; existing checkpoints cannot be silently reused')
    atomic_write(path, json_bytes(resolution))
    return resolution


def runtime_overrides(resolution):
    return {'model_reasoning_effort': resolution['mode'],
            'agents.default_subagent_model': resolution['model'],
            'agents.default_subagent_reasoning_effort': resolution['mode']}


def verify_thread(server, resolution, thread_id):
    thread = server.call('thread/read', {'threadId': thread_id, 'includeTurns': False})['thread']
    require(thread.get('id') == thread_id and thread.get('model') == resolution['model'],
            f'Codex thread {thread_id} substituted a different or unverifiable model; generation stopped')
    require(thread.get('reasoningEffort') == resolution['mode'],
            f'Codex thread {thread_id} substituted a different or unverifiable reasoning setting; generation stopped')
    require(thread.get('modelProvider') == 'openai', 'Codex thread changed model provider; generation stopped')
    require(thread.get('cliVersion') == resolution['cli_version'].removeprefix('codex-cli '),
            'Codex version changed during this report; generation stopped')
    logger.info('Effective Codex thread verified: thread=%s model=%s reasoning=%s cli=%s',
                thread_id, thread['model'], thread['reasoningEffort'], thread['cliVersion'])
    return thread


def verify_effective(server, resolution, directory):
    result = server.call('thread/start', {'model': resolution['model'], 'cwd': str(directory),
        'sandbox': 'workspace-write', 'ephemeral': True, 'allowProviderModelFallback': False,
        'config': runtime_overrides(resolution)})
    require(result.get('model') == resolution['model'], 'Codex substituted a different model; generation stopped')
    require(result.get('reasoningEffort') == resolution['mode'], 'Codex substituted a different reasoning setting; generation stopped')
    require(result.get('modelProvider') == 'openai', 'Model availability was not verified against the OpenAI account')
    require(result.get('sandbox', {}).get('type') == 'workspaceWrite', 'The isolated workspace sandbox could not be verified')
    require(all(Path(path).resolve().is_relative_to(Path(directory).resolve())
                for path in result['sandbox'].get('writableRoots', [])),
            'Existing Codex configuration grants extra writable roots; unattended research requires an isolated scratch workspace')
    verify_thread(server, resolution, result['thread']['id'])
    return {'model': result['model'], 'mode': result['reasoningEffort'],
            'approval_policy': result['approvalPolicy'], 'sandbox': result['sandbox'], 'thread_id': result['thread']['id']}


def resolve_runtime(root, settings):
    """Fresh documentation + account catalog + exact effective runtime settings."""
    executable = shutil.which('codex')
    require(executable, 'Codex is not installed; run bash scripts/install_local_cron.sh')
    verify_skill_links(root)
    model_url, mode_url = policy_sources(settings)
    recommendations, model_source = official_document(model_url)
    modes, mode_source = official_document(mode_url)
    recommendation = model_recommendation(recommendations)
    model = recommendation['model']
    resolution = {'model': model, 'executable': str(Path(executable).resolve()),
                  'checked_at': datetime.now(timezone.utc).isoformat(), 'settings_sha256': settings.sha256,
                  'sources': [model_source, mode_source],
                  'cli_version': subprocess.check_output([executable, '--version'], text=True, stderr=subprocess.DEVNULL).strip()}
    with tempfile.TemporaryDirectory(prefix='dailypaper-runtime-') as directory:
        prepare_workspace(root, directory)
        with AppServer(executable, directory) as server:
            account = server.call('account/read', {'refreshToken': False})
            require(account.get('account'), 'Codex is not authenticated; sign in with codex login before scheduling')
            rows, cursor = [], None
            while True:
                page = server.call('model/list', {'cursor': cursor, 'includeHidden': False, 'limit': 100})
                rows.extend(page['data'])
                cursor = page.get('nextCursor')
                if not cursor:
                    break
            matches = [row for row in rows if row['model'] == model and not row['hidden']]
            require(len(matches) == 1, f'The officially recommended model {model} is not available to this Codex account; no downgrade selected')
            resolution['mode'], reasoning_evidence = strongest_reasoning(modes, matches[0]['supportedReasoningEfforts'])
            resolution['selection_evidence'] = {'model_recommendation': recommendation, 'reasoning': reasoning_evidence,
                'account_type': account['account'].get('type'), 'catalog_model': matches[0]['model']}
            require('image' in matches[0].get('inputModalities', []), f'{model} does not advertise image inputs for paper inspection')
            discovered = server.call('skills/list', {'cwds': [directory], 'forceReload': True})
            entries = [entry for row in discovered['data'] for entry in row['skills']]
            active = {entry['name'] for entry in entries if entry['enabled'] and
                      Path(entry['path']).resolve() == Path(root).resolve() / 'skills' / entry['name'] / 'SKILL.md'}
            require(set(skill_names()) <= active, 'Installed Codex cannot discover all canonical DailyPaper skills')
            resolution['effective'] = verify_effective(server, resolution, directory)
    logger.info('Codex policy resolved: model=%s mode=%s cli=%s checked_at=%s',
                model, resolution['mode'], resolution['cli_version'], resolution['checked_at'])
    logger.info('Codex selection evidence: %s', json.dumps({'sources': resolution['sources'],
                'selection': resolution['selection_evidence']}, sort_keys=True))
    return resolution


class ExecutionGuard:
    """Audit parent and native subagent settings, including reroutes mid-turn."""
    def __init__(self, server, resolution, thread_id):
        self.server, self.resolution, self.root_thread = server, resolution, thread_id
        self.threads = {thread_id}
        self.active_turns = set()
        self.active_agents = set()

    def verify(self, thread_id):
        require(thread_id, 'Codex emitted a subagent without a verifiable thread identity')
        verify_thread(self.server, self.resolution, thread_id)
        self.threads.add(thread_id)

    def inspect(self, event):
        method, params = event.get('method'), event.get('params', {})
        require(method != 'model/rerouted', f'Codex rerouted a model during execution: {params}; generation stopped')
        if method == 'thread/started':
            self.verify(params['thread']['id'])
        if method in {'turn/started', 'turn/completed'}:
            thread_id = params['threadId']
            self.verify(thread_id)
            if method == 'turn/started':
                self.active_turns.add(thread_id)
            else:
                require(params['turn']['status'] == 'completed',
                        f'Codex thread {thread_id} did not complete successfully: {params["turn"].get("error")}')
                self.active_turns.discard(thread_id)
        item = params.get('item', {})
        if method in {'item/started', 'item/completed'}:
            if item.get('type') == 'subAgentActivity':
                child = item.get('agentThreadId')
                self.verify(child)
                if item.get('kind') == 'started':
                    self.active_agents.add(child)
                elif item.get('kind') == 'completed':
                    self.active_agents.discard(child)
                else:
                    raise RuntimeVerificationError('Unrecognized subagent activity; completion cannot be verified')
            if item.get('type') == 'collabAgentToolCall':
                for key, required in (('model', self.resolution['model']), ('reasoningEffort', self.resolution['mode'])):
                    require(item.get(key) in (None, required), f'Subagent requested a conflicting {key}; generation stopped')
                for child in item.get('receiverThreadIds', []):
                    self.verify(child)

    def finish(self):
        require(not self.active_turns and not self.active_agents, 'A subagent is still running; report completion cannot be verified')
        for thread_id in self.threads:
            self.verify(thread_id)


def execute(executable, resolution, root, prompt, schema, images=(), timeout=1200, workspace=None):
    """Every call verifies its effective model/mode before starting an actual turn."""
    @contextmanager
    def workspace_context():
        if workspace is not None:
            yield Path(workspace)
        else:
            with tempfile.TemporaryDirectory(prefix='dailypaper-agent-') as temporary:
                prepare_workspace(root, temporary)
                yield Path(temporary)
    with workspace_context() as directory:
        actual_version = subprocess.check_output([executable, '--version'], text=True, stderr=subprocess.DEVNULL).strip()
        require(actual_version == resolution['cli_version'], 'Codex executable version changed during this report; generation stopped')
        logger.info('Codex stage call: model=%s mode=%s cli=%s sandbox=workspace-write scratch=%s',
                    resolution['model'], resolution['mode'], actual_version, directory)
        with AppServer(executable, directory) as server:
            effective = verify_effective(server, resolution, directory)
            contract = (f'The verified DailyPaper runtime for this report is model={resolution["model"]}, '
                        f'reasoning_effort={resolution["mode"]}. Explicitly use these exact values for every native '
                        'subagent spawn, including further delegation. Do not select another model, effort, or custom '
                        'agent configuration that changes them. Do not launch a nested Codex runtime or model API '
                        'to evade this policy. Stop if the required settings cannot be used.\n\n')
            inputs = [{'type': 'text', 'text': contract + prompt}]
            inputs.extend({'type': 'localImage', 'path': str(Path(path).resolve()), 'detail': 'original'} for path in images)
            started = server.call('turn/start', {'threadId': effective['thread_id'], 'input': inputs,
                'model': resolution['model'], 'effort': resolution['mode'], 'outputSchema': schema})
            turn_id = started['turn']['id']
            deadline = time.monotonic() + timeout
            items = []
            guard = ExecutionGuard(server, resolution, effective['thread_id'])
            pending = list(server.events)
            server.events.clear()
            while True:
                event = pending.pop(0) if pending else server.receive(deadline)
                guard.inspect(event)
                pending.extend(server.events)
                server.events.clear()
                params = event.get('params', {})
                if params.get('threadId') != effective['thread_id']:
                    continue
                if event.get('method') == 'item/completed':
                    items.append(params['item'])
                if event.get('method') == 'turn/completed' and params['turn']['id'] == turn_id:
                    # Verify notifications received while reading effective settings too.
                    while pending:
                        guard.inspect(pending.pop(0))
                        pending.extend(server.events)
                        server.events.clear()
                    guard.finish()
                    while server.events:
                        pending.extend(server.events)
                        server.events.clear()
                        while pending:
                            guard.inspect(pending.pop(0))
                    require(not guard.active_turns and not guard.active_agents, 'A subagent is still running; report completion cannot be verified')
                    turn = params['turn']
                    require(turn['status'] == 'completed', f'Codex execution failed: {turn.get("error")}; no downgrade selected')
                    finals = [item['text'] for item in items if item['type'] == 'agentMessage' and item.get('phase') == 'final_answer']
                    require(finals, 'Codex did not return a complete final result')
                    return json.loads(finals[-1]), items
