#!/usr/bin/env python3
"""Enrich ranked paper results with AI-generated Chinese summaries and editorial guidance."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from content_store import get_repo_root, write_json

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = 'github_models'
DEFAULT_OPENAI_MODEL = 'gpt-4.1-mini'
DEFAULT_OPENAI_API_BASE = 'https://api.openai.com/v1'
DEFAULT_GITHUB_MODELS_API_BASE = 'https://models.github.ai'
DEFAULT_GITHUB_MODELS_PREFERRED_MODELS = [
    'openai/gpt-5.4',
    'openai/gpt-5',
    'openai/gpt-4.1',
    'openai/gpt-4o',
]
DEFAULT_TIMEOUT = 180
DEFAULT_MAX_OUTPUT_TOKENS = 5000
DEFAULT_GITHUB_API_VERSION = '2022-11-28'
DEFAULT_GITHUB_MODELS_PAPER_LIMIT = 8
DEFAULT_GITHUB_MODELS_ABSTRACT_CHARS = 650
DEFAULT_GITHUB_MODELS_RETRY_PAPER_LIMIT = 6
DEFAULT_GITHUB_MODELS_RETRY_ABSTRACT_CHARS = 400


def normalize_paper_id(raw: str) -> str:
    return str(raw or '').replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '').replace('arXiv:', '').strip()


def load_config(config_path: str | None) -> Dict[str, Any]:
    if not config_path:
        return {}
    path = Path(config_path)
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}


def short_fallback_summary(paper: Dict[str, Any]) -> str:
    text = (paper.get('summary') or paper.get('abstract') or '').replace('\n', ' ').strip()
    if not text:
        return '摘要未提供足够信息。'
    sentence = text.split('. ')[0].strip()
    if not sentence.endswith('.'):
        sentence += '.'
    return sentence


def trim_text(text: str, max_chars: int) -> str:
    value = str(text or '').replace('\n', ' ').strip()
    if len(value) <= max_chars:
        return value
    clipped = value[: max(0, max_chars - 1)].rsplit(' ', 1)[0].strip()
    if not clipped:
        clipped = value[: max(0, max_chars - 1)].strip()
    return clipped + '…'


def compact_scores(scores: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(scores, dict):
        return {}
    result: Dict[str, Any] = {}
    for key in ['recommendation', 'relevance', 'recency']:
        if key in scores:
            result[key] = scores[key]
    return result


def build_prompt_payload(
    report_date: str,
    config: Dict[str, Any],
    papers: List[Dict[str, Any]],
    *,
    paper_limit: int,
    max_abstract_chars: int,
    max_authors: int = 4,
) -> Dict[str, Any]:
    domains = list((config.get('research_domains') or {}).keys())
    prompt_papers: List[Dict[str, Any]] = []
    for paper in papers[:paper_limit]:
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        prompt_papers.append({
            'paper_id': paper_id,
            'title': paper.get('title', ''),
            'authors': (paper.get('authors') or [])[:max_authors],
            'domain': paper.get('matched_domain', 'Uncategorized'),
            'published': paper.get('published', paper.get('publicationDate', '')),
            'abstract': trim_text(paper.get('summary') or paper.get('abstract') or '', max_abstract_chars),
            'scores': compact_scores(paper.get('scores', {})),
        })

    return {
        'report_date': report_date,
        'preferred_language': 'zh-CN',
        'research_domains': domains,
        'papers': prompt_papers,
    }


def build_messages(
    report_date: str,
    config: Dict[str, Any],
    papers: List[Dict[str, Any]],
    *,
    paper_limit: int,
    max_abstract_chars: int,
    max_authors: int = 4,
) -> List[Dict[str, str]]:
    system_prompt = (
        'You are a rigorous research editor producing a high-signal daily paper digest in Simplified Chinese. '
        'Use only the metadata and abstracts provided. Do not invent metrics, experiments, authors, or claims not present in the input. '
        'If the abstract is vague, explicitly say the abstract does not make the point clear. '
        'Return valid JSON only. '
        'The JSON object must have keys daily_brief and papers. '
        'daily_brief must contain overview_zh (string), top_themes (array of 3 short strings), and reading_strategy (array of 3 short strings). '
        'papers must be an array where each item contains: paper_id (string), one_liner_zh (string), summary_zh (string, 2-4 sentences), '
        'core_contributions (array of 3 strings), why_read (array of 3 strings), risks (array of 2 strings), '
        'recommended_for (array of 2-3 strings), keywords (array of 4-6 short strings), reading_priority (one of high, medium, low), '
        'and reading_priority_reason (string).'
    )
    user_payload = build_prompt_payload(
        report_date,
        config,
        papers,
        paper_limit=paper_limit,
        max_abstract_chars=max_abstract_chars,
        max_authors=max_authors,
    )
    user_prompt = 'Generate the daily digest JSON for the following paper set:\n' + json.dumps(user_payload, ensure_ascii=False, indent=2)
    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ]


def extract_output_text(payload: Dict[str, Any]) -> str:
    direct = payload.get('output_text')
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    texts: List[str] = []
    for item in payload.get('output', []):
        if item.get('type') != 'message':
            continue
        for content in item.get('content', []):
            content_type = content.get('type')
            if content_type == 'refusal':
                raise RuntimeError(f"Model refusal: {content.get('refusal', '')}")
            if content_type in {'output_text', 'text'}:
                text = content.get('text') or content.get('output_text') or ''
                if text:
                    texts.append(text)

    return '\n'.join(texts).strip()


def extract_chat_completion_text(payload: Dict[str, Any]) -> str:
    choices = payload.get('choices', [])
    if not choices:
        return ''
    message = choices[0].get('message', {})
    content = message.get('content', '')
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get('text') or item.get('content') or ''
            if text:
                texts.append(str(text))
        return '\n'.join(texts).strip()
    return ''


def parse_json_output(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def call_openai(messages: List[Dict[str, str]], api_key: str, model: str, api_base: str, timeout_seconds: int, max_output_tokens: int) -> Dict[str, Any]:
    endpoint = api_base.rstrip('/') + '/responses'
    response = requests.post(
        endpoint,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': model,
            'store': False,
            'input': messages,
            'text': {
                'format': {
                    'type': 'json_object',
                }
            },
            'max_output_tokens': max_output_tokens,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def list_github_models(token: str, api_base: str, timeout_seconds: int) -> List[Dict[str, Any]]:
    endpoint = api_base.rstrip('/') + '/catalog/models'
    response = requests.get(
        endpoint,
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}',
            'X-GitHub-Api-Version': DEFAULT_GITHUB_API_VERSION,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError('Unexpected GitHub Models catalog response')
    return payload


def score_openai_model(model_id: str) -> tuple[int, int]:
    lowered = model_id.lower()
    if lowered.startswith('openai/gpt-5.4'):
        return (6, len(model_id))
    if lowered.startswith('openai/gpt-5'):
        return (5, len(model_id))
    if lowered.startswith('openai/gpt-4.1'):
        return (4, len(model_id))
    if lowered.startswith('openai/gpt-4o'):
        return (3, len(model_id))
    return (1, len(model_id))


def pick_github_model(catalog: List[Dict[str, Any]], explicit_model: str, preferred_models: List[str]) -> str:
    available_ids = [str(item.get('id') or '').strip() for item in catalog if str(item.get('id') or '').strip()]
    available_set = set(available_ids)

    if explicit_model and explicit_model.lower() != 'auto':
        return explicit_model

    for candidate in preferred_models:
        if candidate in available_set:
            return candidate

    openai_models = [model_id for model_id in available_ids if model_id.startswith('openai/')]
    if openai_models:
        return sorted(openai_models, key=score_openai_model, reverse=True)[0]

    if available_ids:
        return available_ids[0]

    raise RuntimeError('GitHub Models catalog is empty')


def call_github_models(messages: List[Dict[str, str]], token: str, model: str, api_base: str, timeout_seconds: int, max_output_tokens: int) -> Dict[str, Any]:
    endpoint = api_base.rstrip('/') + '/inference/chat/completions'
    response = requests.post(
        endpoint,
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-GitHub-Api-Version': DEFAULT_GITHUB_API_VERSION,
        },
        json={
            'model': model,
            'messages': messages,
            'temperature': 0.2,
            'max_tokens': max_output_tokens,
            'response_format': {
                'type': 'json_object',
            },
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def coerce_string_list(value: Any, *, min_items: int = 0, max_items: int = 10, fallback: List[str] | None = None) -> List[str]:
    if fallback is None:
        fallback = []
    if not isinstance(value, list):
        items = []
    else:
        items = [str(item).strip() for item in value if str(item).strip()]
    items = items[:max_items]
    if len(items) < min_items:
        items.extend(fallback[: max(0, min_items - len(items))])
    return items


def normalize_daily_brief(data: Dict[str, Any]) -> Dict[str, Any]:
    daily = data.get('daily_brief', {}) if isinstance(data, dict) else {}
    overview = str(daily.get('overview_zh') or '').strip()
    top_themes = coerce_string_list(daily.get('top_themes'), min_items=0, max_items=3)
    reading_strategy = coerce_string_list(daily.get('reading_strategy'), min_items=0, max_items=3)
    return {
        'overview_zh': overview,
        'top_themes': top_themes,
        'reading_strategy': reading_strategy,
    }


def normalize_paper_ai(item: Dict[str, Any], fallback_paper: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'one_liner_zh': str(item.get('one_liner_zh') or '').strip(),
        'summary_zh': str(item.get('summary_zh') or '').strip(),
        'core_contributions': coerce_string_list(item.get('core_contributions'), max_items=3),
        'why_read': coerce_string_list(item.get('why_read'), max_items=3),
        'risks': coerce_string_list(item.get('risks'), max_items=2),
        'recommended_for': coerce_string_list(item.get('recommended_for'), max_items=3),
        'keywords': coerce_string_list(item.get('keywords'), max_items=6),
        'reading_priority': str(item.get('reading_priority') or 'medium').strip().lower() or 'medium',
        'reading_priority_reason': str(item.get('reading_priority_reason') or '').strip(),
        'fallback_summary': short_fallback_summary(fallback_paper),
    }


def merge_enrichment(payload: Dict[str, Any], raw_ai: Dict[str, Any], model: str) -> Dict[str, Any]:
    enriched = copy.deepcopy(payload)
    papers = enriched.get('top_papers', [])
    normalized_daily = normalize_daily_brief(raw_ai)
    ai_by_id: Dict[str, Dict[str, Any]] = {}

    for item in raw_ai.get('papers', []) if isinstance(raw_ai, dict) else []:
        paper_id = normalize_paper_id(item.get('paper_id', ''))
        if not paper_id:
            continue
        ai_by_id[paper_id] = item

    for paper in papers:
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        ai_payload = ai_by_id.get(paper_id, {})
        paper['ai'] = normalize_paper_ai(ai_payload, paper)

    enriched['daily_brief'] = normalized_daily
    enriched['ai_enrichment'] = {
        'enabled': True,
        'model': model,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
    }
    return enriched


def passthrough_payload(payload: Dict[str, Any], reason: str) -> Dict[str, Any]:
    result = copy.deepcopy(payload)
    result['daily_brief'] = result.get('daily_brief', {
        'overview_zh': '',
        'top_themes': [],
        'reading_strategy': [],
    })
    for paper in result.get('top_papers', []):
        paper.setdefault('ai', {
            'one_liner_zh': '',
            'summary_zh': '',
            'core_contributions': [],
            'why_read': [],
            'risks': [],
            'recommended_for': [],
            'keywords': [],
            'reading_priority': 'medium',
            'reading_priority_reason': '',
            'fallback_summary': short_fallback_summary(paper),
        })
    result['ai_enrichment'] = {
        'enabled': False,
        'reason': reason,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
    }
    return result


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Enrich ranked paper results with AI-generated digest content')
    parser.add_argument('--input', required=True, help='Input ranked paper JSON')
    parser.add_argument('--output', required=True, help='Output enriched JSON')
    parser.add_argument('--config', default=None, help='Config YAML path')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    parser.add_argument('--strict', action='store_true', help='Fail instead of falling back when AI enrichment errors')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_absolute():
        input_path = repo_root / input_path
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    payload = json.loads(input_path.read_text(encoding='utf-8'))
    config = load_config(args.config)
    ai_settings = config.get('ai', {}) if isinstance(config, dict) else {}

    provider = os.environ.get('AI_PROVIDER', ai_settings.get('provider', DEFAULT_PROVIDER)).strip() or DEFAULT_PROVIDER
    model = os.environ.get('AI_MODEL', ai_settings.get('model', '')).strip()
    openai_api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    openai_api_base = os.environ.get('OPENAI_API_BASE', ai_settings.get('api_base', DEFAULT_OPENAI_API_BASE)).strip() or DEFAULT_OPENAI_API_BASE
    github_models_token = os.environ.get('GITHUB_MODELS_TOKEN', os.environ.get('GITHUB_TOKEN', '')).strip()
    github_models_api_base = os.environ.get('GITHUB_MODELS_API_BASE', ai_settings.get('github_models_api_base', DEFAULT_GITHUB_MODELS_API_BASE)).strip() or DEFAULT_GITHUB_MODELS_API_BASE
    preferred_models = ai_settings.get('preferred_models', DEFAULT_GITHUB_MODELS_PREFERRED_MODELS)
    if not isinstance(preferred_models, list):
        preferred_models = DEFAULT_GITHUB_MODELS_PREFERRED_MODELS
    preferred_models = [str(item).strip() for item in preferred_models if str(item).strip()]
    preferred_models_env = os.environ.get('GITHUB_MODELS_PREFERRED_MODELS', '').strip()
    if preferred_models_env:
        preferred_models = [part.strip() for part in preferred_models_env.split(',') if part.strip()]
    timeout_seconds = int(ai_settings.get('timeout_seconds', DEFAULT_TIMEOUT))
    max_output_tokens = int(ai_settings.get('max_output_tokens', DEFAULT_MAX_OUTPUT_TOKENS))
    enabled = ai_settings.get('enabled', True)

    if not enabled:
        logger.info('AI enrichment disabled in config')
        write_json(output_path, passthrough_payload(payload, 'disabled_in_config'))
        return 0

    report_date = payload.get('target_date') or datetime.now().strftime('%Y-%m-%d')
    papers = payload.get('top_papers', [])
    github_models_paper_limit = int(ai_settings.get('github_models_paper_limit', DEFAULT_GITHUB_MODELS_PAPER_LIMIT))
    github_models_abstract_chars = int(ai_settings.get('github_models_abstract_chars', DEFAULT_GITHUB_MODELS_ABSTRACT_CHARS))

    try:
        if provider == 'github_models':
            if not github_models_token:
                logger.info('GITHUB_MODELS_TOKEN or GITHUB_TOKEN not set, skipping AI enrichment')
                write_json(output_path, passthrough_payload(payload, 'missing_github_models_token'))
                return 0
            catalog = list_github_models(github_models_token, github_models_api_base, timeout_seconds)
            model = pick_github_model(catalog, model, preferred_models)
            logger.info('Using GitHub Models provider with model %s', model)
            try:
                messages = build_messages(
                    report_date,
                    config,
                    papers,
                    paper_limit=github_models_paper_limit,
                    max_abstract_chars=github_models_abstract_chars,
                )
                response_payload = call_github_models(messages, github_models_token, model, github_models_api_base, timeout_seconds, max_output_tokens)
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code != 413:
                    raise
                logger.warning(
                    'GitHub Models request was too large; retrying with smaller prompt (papers=%s, abstract_chars=%s)',
                    DEFAULT_GITHUB_MODELS_RETRY_PAPER_LIMIT,
                    DEFAULT_GITHUB_MODELS_RETRY_ABSTRACT_CHARS,
                )
                messages = build_messages(
                    report_date,
                    config,
                    papers,
                    paper_limit=min(github_models_paper_limit, DEFAULT_GITHUB_MODELS_RETRY_PAPER_LIMIT),
                    max_abstract_chars=min(github_models_abstract_chars, DEFAULT_GITHUB_MODELS_RETRY_ABSTRACT_CHARS),
                )
                response_payload = call_github_models(messages, github_models_token, model, github_models_api_base, timeout_seconds, max_output_tokens)
            response_text = extract_chat_completion_text(response_payload)
        elif provider == 'openai':
            model = os.environ.get('OPENAI_MODEL', model).strip() or DEFAULT_OPENAI_MODEL
            if not openai_api_key:
                logger.info('OPENAI_API_KEY not set, skipping AI enrichment')
                write_json(output_path, passthrough_payload(payload, 'missing_api_key'))
                return 0
            logger.info('Using OpenAI provider with model %s', model)
            messages = build_messages(
                report_date,
                config,
                papers,
                paper_limit=len(papers),
                max_abstract_chars=1200,
            )
            response_payload = call_openai(messages, openai_api_key, model, openai_api_base, timeout_seconds, max_output_tokens)
            response_text = extract_output_text(response_payload)
        else:
            raise RuntimeError(f'Unsupported AI provider: {provider}')

        parsed = parse_json_output(response_text)
        enriched = merge_enrichment(payload, parsed, model)
        enriched['ai_enrichment']['provider'] = provider
        if response_payload.get('usage'):
            enriched['ai_enrichment']['usage'] = response_payload.get('usage')
        write_json(output_path, enriched)
        logger.info('AI enrichment completed with provider %s and model %s', provider, model)
        return 0
    except Exception as exc:
        logger.exception('AI enrichment failed: %s', exc)
        if args.strict:
            raise
        write_json(output_path, passthrough_payload(payload, f'error:{type(exc).__name__}'))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
