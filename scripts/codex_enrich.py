#!/usr/bin/env python3
"""Local Codex transport for the same full-paper stages used by API models."""

import copy
from pathlib import Path

import jsonschema

from pipeline_prompts import build_messages, stage_schema
from codex_runtime import execute, resolve_runtime, require, bind_report, resolution_identity
from codex_checks import check_capabilities
from report_settings import load_settings


class CodexBackend:
    def __init__(self, root, settings, infrastructure):
        self.root, self.settings = Path(root), settings
        self.options = infrastructure.get('ai', {})
        self.resolution = None

    def preflight(self):
        if self.resolution is None:
            resolution = resolve_runtime(self.root, self.settings)
            resolution['capabilities'] = check_capabilities(self.root, resolution,
                timeout=int(self.options.get('codex_timeout_seconds', 1200)))
            self.resolution = resolution
            self.identity = resolution_identity(resolution)
        require(resolution_identity(self.resolution) == self.identity, 'Resolved report configuration was changed; generation stopped')
        return copy.deepcopy(self.resolution)

    def bind_report(self, stage):
        return bind_report(stage, self.preflight())

    def generate(self, stage, context, images=()):
        resolution = self.preflight()
        require(resolution['settings_sha256'] == self.settings.sha256 == load_settings(self.root).sha256,
                'Settings changed after model verification; generation stopped')
        messages = build_messages(self.root, self.settings, stage, context)
        schema = stage_schema(stage, self.settings)
        prompt = '\n\n'.join(message['content'] for message in messages)
        result, _ = execute(resolution['executable'], resolution, self.root, prompt, schema, images,
                            timeout=int(self.options.get('codex_timeout_seconds', 1200)))
        jsonschema.validate(result, schema)
        return result


def main():
    from daily_pipeline import enrichment_cli
    return enrichment_cli('codex')


if __name__ == '__main__':
    raise SystemExit(main())
