#!/usr/bin/env python3
"""Local Codex transport for the same full-paper stages used by API models."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import jsonschema

from pipeline_prompts import build_messages, stage_schema


class CodexBackend:
    def __init__(self, root, settings, infrastructure):
        self.root, self.settings = Path(root), settings
        self.options = infrastructure.get('ai', {})
        self.model = os.environ.get('CODEX_MODEL', '')

    def generate(self, stage, context, images=()):
        executable = shutil.which('codex')
        if not executable:
            raise RuntimeError('Codex CLI is missing; generation stopped')
        messages = build_messages(self.root, self.settings, stage, context)
        schema = stage_schema(stage, self.settings)
        prompt = '\n\n'.join(message['content'] for message in messages)
        with tempfile.TemporaryDirectory(prefix='dailypaper-codex-') as directory:
            schema_path = Path(directory) / 'schema.json'
            output_path = Path(directory) / 'result.json'
            schema_path.write_text(json.dumps(schema), encoding='utf-8')
            cmd = [executable, 'exec', '--cd', directory, '--skip-git-repo-check', '--sandbox', 'read-only',
                   '--ephemeral', '--output-schema', str(schema_path), '--output-last-message', str(output_path)]
            if self.model:
                cmd.extend(['--model', self.model])
            for path in images:
                cmd.extend(['--image', str(Path(path).resolve())])
            cmd.append('-')
            subprocess.run(cmd, input=prompt, text=True, check=True,
                           timeout=int(self.options.get('codex_timeout_seconds', 1200)),
                           stdout=subprocess.DEVNULL)
            result = json.loads(output_path.read_text(encoding='utf-8'))
        jsonschema.validate(result, schema)
        return result


def main():
    from daily_pipeline import enrichment_cli
    return enrichment_cli('codex')


if __name__ == '__main__':
    raise SystemExit(main())
