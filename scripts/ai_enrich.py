#!/usr/bin/env python3
"""Hosted model transport; prompts and generation stages are shared with Codex."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import jsonschema
import requests

from pipeline_prompts import build_messages, stage_schema


def image_data(path):
    path = Path(path)
    mime = 'image/png' if path.suffix == '.png' else 'image/jpeg'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()


def parse_output(text):
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError('Model output must be a JSON object')
    return result


class APIBackend:
    def __init__(self, root, settings, infrastructure, provider=None, session=None):
        self.root, self.settings = Path(root), settings
        self.options = infrastructure.get('ai', {})
        self.provider = provider or os.environ.get('AI_PROVIDER') or self.options.get('provider', 'github_models')
        self.session = session or requests.Session()
        self.timeout = int(self.options.get('timeout_seconds', 240))
        self.model = os.environ.get('AI_MODEL') or self.options.get('model', '')
        self.max_tokens = int(self.options.get('max_output_tokens', 16000))
        self._resolved = False

    def resolve(self):
        if self._resolved:
            return
        if self.provider == 'github_models':
            self.token = os.environ.get('GITHUB_MODELS_TOKEN') or os.environ.get('GITHUB_TOKEN')
            self.base = os.environ.get('GITHUB_MODELS_API_BASE') or self.options.get('github_models_api_base', 'https://models.github.ai')
            if not self.token:
                raise RuntimeError('GitHub Models credentials are missing; generation stopped')
            if not self.model or self.model == 'auto':
                response = self.session.get(self.base.rstrip('/') + '/catalog/models',
                    headers=self.headers(), timeout=self.timeout)
                response.raise_for_status()
                available = {entry['id'] for entry in response.json()}
                preferred = (os.environ['GITHUB_MODELS_PREFERRED_MODELS'].split(',')
                             if os.environ.get('GITHUB_MODELS_PREFERRED_MODELS') else self.options.get('preferred_models', []))
                self.model = next((name.strip() for name in preferred if name.strip() in available), '')
                if not self.model:
                    raise RuntimeError('No configured model is available in the GitHub Models catalog')
        elif self.provider == 'openai':
            self.token = os.environ.get('OPENAI_API_KEY')
            self.base = os.environ.get('OPENAI_API_BASE') or self.options.get('api_base', 'https://api.openai.com/v1')
            self.model = os.environ.get('OPENAI_MODEL') or self.model
            if not self.token or not self.model or self.model == 'auto':
                raise RuntimeError('OpenAI credentials and an explicit model are required; generation stopped')
        else:
            raise ValueError(f'Unsupported model transport: {self.provider}')
        self._resolved = True

    def headers(self):
        return {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json',
                'X-GitHub-Api-Version': '2022-11-28'}

    def generate(self, stage, context, images=()):
        self.resolve()
        messages = build_messages(self.root, self.settings, stage, context)
        schema = stage_schema(stage, self.settings)
        if self.provider == 'openai':
            messages[1]['content'] = [{'type': 'input_text', 'text': messages[1]['content']},
                *[{'type': 'input_image', 'image_url': image_data(path), 'detail': 'high'} for path in images]]
            body = {'model': self.model, 'store': False, 'input': messages, 'max_output_tokens': self.max_tokens,
                    'text': {'format': {'type': 'json_schema', 'name': stage, 'schema': schema, 'strict': True}}}
            endpoint = '/responses'
        else:
            messages[1]['content'] = [{'type': 'text', 'text': messages[1]['content']},
                *[{'type': 'image_url', 'image_url': {'url': image_data(path), 'detail': 'high'}} for path in images]]
            body = {'model': self.model, 'messages': messages, 'max_tokens': self.max_tokens,
                    'response_format': {'type': 'json_object'}}
            endpoint = '/inference/chat/completions'
        response = self.session.post(self.base.rstrip('/') + endpoint, headers=self.headers(), json=body, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if self.provider == 'openai':
            if data.get('status') == 'incomplete' or data.get('error'):
                raise RuntimeError('OpenAI returned incomplete analysis; inputs will not be truncated')
            text = data.get('output_text') or '\n'.join(item['text'] for message in data.get('output', [])
                    if message.get('type') == 'message' for item in message.get('content', []) if item.get('type') == 'output_text')
        else:
            choice = data['choices'][0]
            if choice.get('finish_reason') != 'stop':
                raise RuntimeError('GitHub Models returned incomplete analysis; inputs will not be truncated')
            text = choice['message']['content']
        result = parse_output(text)
        jsonschema.validate(result, schema)
        return result


def main():
    from daily_pipeline import enrichment_cli
    return enrichment_cli('api')


if __name__ == '__main__':
    raise SystemExit(main())
