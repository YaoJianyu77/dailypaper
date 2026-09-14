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
APPROVAL_POLICY = 'never'
REASONING_MODE = 'medium'


class RuntimeVerificationError(RuntimeError):
    pass


class RuntimeRPCError(RuntimeVerificationError):
    def __init__(self, method, error):
        self.method, self.error = method, error
        super().__init__(f'Codex could not verify {method}: {error}')


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
    """Expose source instructions through links inside the existing workspace sandbox."""
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
        self.process = subprocess.Popen([self.executable, '--search', '--ask-for-approval', APPROVAL_POLICY,
            'app-server', '--strict-config', '--listen', 'stdio://'],
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
                if 'error' in value:
                    raise RuntimeRPCError(method, value['error'])
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
            raise RuntimeVerificationError(f'Codex requested interactive authorization ({value["method"]}) despite approvalPolicy={APPROVAL_POLICY}; unattended run stopped without granting permissions.')
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
    configured = rows.get('required codex mode', '').lower()
    require(configured.startswith('balanced reasoning') and REASONING_MODE in configured,
            f'The settings must require the documented balanced reasoning mode ({REASONING_MODE})')
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


def configured_reasoning(document, supported, requested=REASONING_MODE):
    """Verify the configured balanced mode against docs and account support."""
    section = re.search(r'^### Reasoning effort \(`model_reasoning_effort`\)\s*\n(.*?)(?=^#{1,3} |</ContentModeSwitch>|\Z)',
                        document, re.M | re.S)
    require(section, 'Official reasoning guidance format changed; configured mode cannot be verified')
    text = section[1]
    entries = {}
    for match in re.finditer(r'^- (.+?)(?=\n\n|\n- |\Z)', text, re.M | re.S):
        label, separator, description = match[1].partition(':')
        names = re.findall(r'`([a-zA-Z0-9_-]+)`', label)
        require(separator and names, 'Official reasoning entry cannot be interpreted safely')
        description = ' '.join(description.split())
        for name in names:
            require(name not in entries, 'Official reasoning guidance contains duplicate or conflicting levels')
            entries[name] = description
    levels = [entry.get('reasoningEffort') for entry in supported]
    require(levels and all(isinstance(level, str) and level for level in levels) and len(set(levels)) == len(levels),
            'The selected model has no verifiable supported reasoning settings')
    require(requested in entries, f'Official guidance does not document configured reasoning mode {requested}')
    require(requested in levels, f'The selected model does not support configured reasoning mode {requested}')
    require(re.search(r'\bbalanc', entries[requested], re.I),
            f'Official guidance no longer describes {requested} as a balanced mode')
    return requested, {'supported': supported, 'documented': entries,
                       'selected': requested, 'selection_statement': entries[requested]}


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
    return {'model_reasoning_effort': resolution['mode']}


def verify_thread(server, resolution, thread_id, *, timeout=45):
    deadline = time.monotonic() + timeout
    while True:
        try:
            thread = server.call('thread/read', {'threadId': thread_id, 'includeTurns': False})['thread']
            break
        except RuntimeRPCError as error:
            # Codex can announce a new thread before its buffered session metadata
            # is visible on disk. Retry this read only; never resume/start a turn
            # or accept missing settings. Other protocol failures remain fatal.
            message = error.error.get('message', '')
            transient = (error.method == 'thread/read' and error.error.get('code') == -32603
                         and 'failed to read session metadata' in message and message.endswith(' is empty'))
            if not transient:
                raise
            require(time.monotonic() < deadline,
                    f'Codex thread {thread_id} session metadata remained empty; generation stopped')
            time.sleep(0.1)
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


def verify_permissions(result, directory, expected_sandbox=None):
    require(result.get('approvalPolicy') == APPROVAL_POLICY,
            'Codex did not apply approvalPolicy=never; unattended execution stopped')
    sandbox = result.get('sandbox', {})
    require(sandbox.get('type') == 'workspaceWrite', 'The isolated workspace sandbox could not be verified')
    require(sandbox.get('networkAccess') is False, 'Codex sandbox network access is not disabled; generation stopped')
    roots = sandbox.get('writableRoots', []) + result.get('runtimeWorkspaceRoots', [])
    require(all(Path(path).resolve().is_relative_to(Path(directory).resolve()) for path in roots),
            'Existing Codex configuration grants extra writable roots; unattended research requires an isolated scratch workspace')
    require(expected_sandbox is None or sandbox == expected_sandbox,
            'Codex changed sandbox permissions during execution; generation stopped')


def read_turn_permissions(thread, turn_id=None, timeout=45):
    """Read Codex's effective turn receipt without resuming or altering a child."""
    path = Path(thread.get('path') or '')
    require(path.is_absolute() and path.name.endswith(thread['id'] + '.jsonl'),
            'Codex has no verifiable turn permission receipt; generation stopped')
    deadline = time.monotonic() + timeout
    while True:
        context, owner = None, None
        if path.is_file():
            with path.open() as stream:
                for line in stream:
                    # The last record can still be in the process of being appended.
                    if not line.endswith('\n'):
                        break
                    record = json.loads(line)
                    if record.get('type') == 'session_meta':
                        owner = record['payload']['id']
                    elif record.get('type') == 'turn_context':
                        payload = record['payload']
                        if turn_id is None or payload.get('turn_id') == turn_id:
                            context = payload
        if context is not None:
            require(owner == thread['id'], 'Permission receipt belongs to another Codex thread')
            sandbox = context.get('sandbox_policy', {})
            return {'approvalPolicy': context.get('approval_policy'),
                    'runtimeWorkspaceRoots': context.get('workspace_roots', []),
                    'sandbox': {'type': 'workspaceWrite' if sandbox.get('type') == 'workspace-write' else sandbox.get('type'),
                        'writableRoots': sandbox.get('writable_roots', []), 'networkAccess': sandbox.get('network_access'),
                        'excludeTmpdirEnvVar': sandbox.get('exclude_tmpdir_env_var', False),
                        'excludeSlashTmp': sandbox.get('exclude_slash_tmp', False)}}
        require(time.monotonic() < deadline, 'Codex did not record effective turn permissions; generation stopped')
        time.sleep(0.05)


def read_token_usage(thread):
    """Read the final cumulative usage receipt written by Codex for one thread."""
    path = Path(thread.get('path') or '')
    if not path.is_file():
        return None
    usage, limit = None, None
    with path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):
                break
            record = json.loads(line)
            if record.get('type') == 'token_usage_record':
                usage = record.get('payload', {}).get('thread_token_usage') or usage
            elif record.get('type') == 'event_msg' and record.get('payload', {}).get('type') == 'token_count':
                primary = (record['payload'].get('rate_limits') or {}).get('primary')
                if primary:
                    limit = primary
    return {'usage': usage, 'rate_limit': limit} if usage else None


def verify_effective(server, resolution, directory, *, ephemeral=True):
    result = server.call('thread/start', {'model': resolution['model'], 'cwd': str(directory),
        'sandbox': 'workspace-write', 'approvalPolicy': APPROVAL_POLICY,
        'ephemeral': ephemeral, 'allowProviderModelFallback': False,
        'config': runtime_overrides(resolution)})
    require(result.get('model') == resolution['model'], 'Codex substituted a different model; generation stopped')
    require(result.get('reasoningEffort') == resolution['mode'], 'Codex substituted a different reasoning setting; generation stopped')
    require(result.get('modelProvider') == 'openai', 'Model availability was not verified against the OpenAI account')
    verify_permissions(result, directory)
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
            resolution['mode'], reasoning_evidence = configured_reasoning(modes, matches[0]['supportedReasoningEfforts'])
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
    """Audit the single stage thread and reject reroutes or delegation."""
    def __init__(self, server, resolution, thread_id, directory, sandbox):
        self.server, self.resolution, self.root_thread = server, resolution, thread_id
        self.directory, self.sandbox = directory, sandbox
        self.threads = {thread_id}
        self.active_turns = set()

    def verify(self, thread_id, turn_id=None):
        require(thread_id, 'Codex emitted a thread without a verifiable identity')
        thread = verify_thread(self.server, self.resolution, thread_id)
        live = read_turn_permissions(thread, turn_id)
        verify_permissions(live, self.directory, self.sandbox)
        logger.info('Effective Codex permissions verified: thread=%s approvalPolicy=%s sandbox=%s networkAccess=%s',
                    thread_id, live['approvalPolicy'], live['sandbox']['type'], live['sandbox']['networkAccess'])
        self.threads.add(thread_id)
        return thread

    def inspect(self, event):
        method, params = event.get('method'), event.get('params', {})
        require(method != 'model/rerouted', f'Codex rerouted a model during execution: {params}; generation stopped')
        if method == 'thread/settings/updated':
            require(params['threadId'] == self.root_thread,
                    'Codex attempted subagent delegation; token-efficient stages require one thread')
            settings = params['threadSettings']
            verify_permissions({'approvalPolicy': settings.get('approvalPolicy'),
                                'sandbox': settings.get('sandboxPolicy')}, self.directory, self.sandbox)
            self.verify(params['threadId'])
        if method == 'thread/started':
            child = params['thread']['id']
            require(child == self.root_thread, 'Codex attempted subagent delegation; token-efficient stages require one thread')
            self.verify(child)
        if method in {'turn/started', 'turn/completed'}:
            thread_id = params['threadId']
            require(thread_id == self.root_thread,
                    'Codex attempted subagent delegation; token-efficient stages require one thread')
            self.verify(thread_id, params['turn']['id'])
            if method == 'turn/started':
                self.active_turns.add(thread_id)
            else:
                require(params['turn']['status'] == 'completed',
                        f'Codex thread {thread_id} did not complete successfully: {params["turn"].get("error")}')
                self.active_turns.discard(thread_id)
        item = params.get('item', {})
        if method in {'item/started', 'item/completed'}:
            if item.get('type') == 'subAgentActivity':
                raise RuntimeVerificationError('Codex attempted subagent delegation; token-efficient stages require one thread')
            if item.get('type') == 'collabAgentToolCall':
                raise RuntimeVerificationError('Codex attempted a collaboration-agent call; token-efficient stages require one thread')

    def finish(self):
        require(not self.active_turns, 'A Codex turn is still running; report completion cannot be verified')
        receipts = []
        for thread_id in self.threads:
            thread = self.verify(thread_id)
            receipt = read_token_usage(thread)
            if receipt:
                receipts.append(receipt)
        return receipts


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
            effective = verify_effective(server, resolution, directory, ephemeral=False)
            contract = (f'The verified DailyPaper runtime for this report is model={resolution["model"]}, '
                        f'reasoning_effort={resolution["mode"]}. Complete this stage in the current thread. Do not spawn, '
                        'message, or delegate to subagents, and do not select another model, effort, or custom '
                        'agent configuration. Do not launch a nested Codex runtime or model API '
                        f'to evade this policy. Approval policy is {APPROVAL_POLICY} for this thread and all descendants. '
                        'Keep the inherited workspace-write sandbox and its existing permissions. Operations outside '
                        'that sandbox must fail; do not request escalation, extra permissions, or a different approval policy. '
                        'Stop if the required settings cannot be used.\n\n')
            inputs = [{'type': 'text', 'text': contract + prompt}]
            inputs.extend({'type': 'localImage', 'path': str(Path(path).resolve()), 'detail': 'original'} for path in images)
            started = server.call('turn/start', {'threadId': effective['thread_id'], 'input': inputs,
                'model': resolution['model'], 'effort': resolution['mode'],
                'approvalPolicy': APPROVAL_POLICY, 'outputSchema': schema})
            turn_id = started['turn']['id']
            deadline = time.monotonic() + timeout
            items = []
            guard = ExecutionGuard(server, resolution, effective['thread_id'], directory, effective['sandbox'])
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
                    receipts = guard.finish()
                    while server.events:
                        pending.extend(server.events)
                        server.events.clear()
                        while pending:
                            guard.inspect(pending.pop(0))
                    require(not guard.active_turns, 'A Codex turn is still running; report completion cannot be verified')
                    turn = params['turn']
                    require(turn['status'] == 'completed', f'Codex execution failed: {turn.get("error")}; no downgrade selected')
                    finals = [item['text'] for item in items if item['type'] == 'agentMessage' and item.get('phase') == 'final_answer']
                    require(finals, 'Codex did not return a complete final result')
                    if receipts:
                        totals = {key: sum((receipt['usage'].get(key) or 0) for receipt in receipts)
                                  for key in ('input_tokens', 'cached_input_tokens', 'output_tokens',
                                              'reasoning_output_tokens', 'total_tokens')}
                        limits = [receipt['rate_limit'] for receipt in receipts if receipt.get('rate_limit')]
                        if limits:
                            latest = limits[-1]
                            totals.update(rate_limit_used_percent=latest.get('used_percent'),
                                          rate_limit_window_minutes=latest.get('window_minutes'),
                                          rate_limit_resets_at=latest.get('resets_at'))
                        logger.info('Codex call token usage: %s', json.dumps(totals, sort_keys=True))
                    return json.loads(finals[-1]), items
