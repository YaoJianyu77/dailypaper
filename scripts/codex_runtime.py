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
    require(re.match(r'^Ultra(?:,|$)', rows.get('required codex mode', '')), 'The production policy must require Ultra; no downgrade is allowed')
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


def recommended_model(document):
    match = re.search(r'^## Recommended models\s*$(.*?)(?=^## Other models\s*$|\Z)', document, re.M | re.S)
    require(match, 'Official recommendation format changed; the strongest research model cannot be verified')
    strongest = []
    for card in re.findall(r'<ModelDetails\b.*?/>', match.group(1), re.S):
        slug = re.search(r'\bslug="([a-zA-Z0-9._-]+)"', card)
        description = re.search(r'\bdescription="([^"]+)"', card)
        if slug and description and re.search(r'most (?:capable|intelligent) model\b', description.group(1), re.I):
            if re.search(r'\bresearch\b', description.group(1), re.I) and re.search(r'title:\s*"Codex CLI",\s*value:\s*true', card):
                strongest.append(slug.group(1))
    require(len(set(strongest)) == 1, 'Official guidance does not uniquely identify the most capable recommended Codex research model; no fallback selected')
    return strongest[0]


def runtime_overrides(resolution):
    return {'model_reasoning_effort': resolution['mode'],
            'agents.default_subagent_model': resolution['model'],
            'agents.default_subagent_reasoning_effort': resolution['mode']}


def verify_effective(server, resolution, directory):
    result = server.call('thread/start', {'model': resolution['model'], 'cwd': str(directory),
        'sandbox': 'workspace-write', 'ephemeral': True, 'allowProviderModelFallback': False,
        'config': runtime_overrides(resolution)})
    require(result.get('model') == resolution['model'], 'Codex substituted a different model; generation stopped')
    require(result.get('reasoningEffort') == resolution['mode'], 'Codex did not accept Ultra exactly; generation stopped')
    require(result.get('modelProvider') == 'openai', 'Model availability was not verified against the OpenAI account')
    require(result.get('sandbox', {}).get('type') == 'workspaceWrite', 'The isolated workspace sandbox could not be verified')
    require(all(Path(path).resolve().is_relative_to(Path(directory).resolve())
                for path in result['sandbox'].get('writableRoots', [])),
            'Existing Codex configuration grants extra writable roots; unattended research requires an isolated scratch workspace')
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
    model = recommended_model(recommendations)
    require('model_reasoning_effort' in modes and re.search(r'\*\*`ultra`\*\*', modes),
            'Official guidance does not verify Ultra as a supported Codex setting')
    resolution = {'model': model, 'mode': 'ultra', 'executable': str(Path(executable).resolve()),
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
            require(any(level['reasoningEffort'] == 'ultra' for level in matches[0]['supportedReasoningEfforts']),
                    f'This account/runtime does not advertise Ultra for {model}; xhigh and max are not substitutes')
            require('image' in matches[0].get('inputModalities', []), f'{model} does not advertise image inputs for paper inspection')
            discovered = server.call('skills/list', {'cwds': [directory], 'forceReload': True})
            entries = [entry for row in discovered['data'] for entry in row['skills']]
            active = {entry['name'] for entry in entries if entry['enabled'] and
                      Path(entry['path']).resolve() == Path(root).resolve() / 'skills' / entry['name'] / 'SKILL.md'}
            require(set(skill_names()) <= active, 'Installed Codex cannot discover all canonical DailyPaper skills')
            resolution['effective'] = verify_effective(server, resolution, directory)
    logger.info('Codex policy resolved: model=%s mode=%s cli=%s checked_at=%s',
                model, resolution['mode'], resolution['cli_version'], resolution['checked_at'])
    return resolution


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
        logger.info('Codex stage call: model=%s mode=%s sandbox=workspace-write scratch=%s',
                    resolution['model'], resolution['mode'], directory)
        with AppServer(executable, directory) as server:
            effective = verify_effective(server, resolution, directory)
            inputs = [{'type': 'text', 'text': prompt}]
            inputs.extend({'type': 'localImage', 'path': str(Path(path).resolve()), 'detail': 'original'} for path in images)
            started = server.call('turn/start', {'threadId': effective['thread_id'], 'input': inputs,
                'model': resolution['model'], 'effort': resolution['mode'], 'outputSchema': schema})
            turn_id = started['turn']['id']
            deadline = time.monotonic() + timeout
            items = []
            pending = list(server.events)
            server.events.clear()
            while True:
                event = pending.pop(0) if pending else server.receive(deadline)
                server.events.append(event)
                params = event.get('params', {})
                if params.get('threadId') != effective['thread_id']:
                    continue
                if event.get('method') == 'item/completed':
                    items.append(params['item'])
                if event.get('method') == 'turn/completed' and params['turn']['id'] == turn_id:
                    turn = params['turn']
                    require(turn['status'] == 'completed', f'Codex execution failed: {turn.get("error")}; no downgrade selected')
                    finals = [item['text'] for item in items if item['type'] == 'agentMessage' and item.get('phase') == 'final_answer']
                    require(finals, 'Codex did not return a complete final result')
                    return json.loads(finals[-1]), items
