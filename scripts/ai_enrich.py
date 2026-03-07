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

DEFAULT_MODEL = 'gpt-4.1-mini'
DEFAULT_API_BASE = 'https://api.openai.com/v1'
DEFAULT_TIMEOUT = 180
DEFAULT_MAX_OUTPUT_TOKENS = 5000


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


def build_prompt_payload(report_date: str, config: Dict[str, Any], papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    domains = list((config.get('research_domains') or {}).keys())
    prompt_papers: List[Dict[str, Any]] = []
    for paper in papers:
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        prompt_papers.append({
            'paper_id': paper_id,
            'title': paper.get('title', ''),
            'authors': paper.get('authors', []),
            'domain': paper.get('matched_domain', 'Uncategorized'),
            'published': paper.get('published', paper.get('publicationDate', '')),
            'abstract': (paper.get('summary') or paper.get('abstract') or '').strip(),
            'scores': paper.get('scores', {}),
        })

    return {
        'report_date': report_date,
        'preferred_language': 'zh-CN',
        'research_domains': domains,
        'papers': prompt_papers,
    }


def build_messages(report_date: str, config: Dict[str, Any], papers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    system_prompt = (
        'You are a rigorous research editor producing a high-signal daily paper digest in Simplified Chinese. '\
        'Use only the metadata and abstracts provided. Do not invent metrics, experiments, authors, or claims not present in the input. '\
        'If the abstract is vague, explicitly say the abstract does not make the point clear. '\
        'Return valid JSON only. '\
        'The JSON object must have keys daily_brief and papers. '\
        'daily_brief must contain overview_zh (string), top_themes (array of 3 short strings), and reading_strategy (array of 3 short strings). '\
        'papers must be an array where each item contains: paper_id (string), one_liner_zh (string), summary_zh (string, 2-4 sentences), '\
        'core_contributions (array of 3 strings), why_read (array of 3 strings), risks (array of 2 strings), '\
        'recommended_for (array of 2-3 strings), keywords (array of 4-6 short strings), reading_priority (one of high, medium, low), '\
        'and reading_priority_reason (string).'
    )
    user_payload = build_prompt_payload(report_date, config, papers)
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

    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    api_base = os.environ.get('OPENAI_API_BASE', ai_settings.get('api_base', DEFAULT_API_BASE)).strip() or DEFAULT_API_BASE
    model = os.environ.get('OPENAI_MODEL', ai_settings.get('model', DEFAULT_MODEL)).strip() or DEFAULT_MODEL
    timeout_seconds = int(ai_settings.get('timeout_seconds', DEFAULT_TIMEOUT))
    max_output_tokens = int(ai_settings.get('max_output_tokens', DEFAULT_MAX_OUTPUT_TOKENS))
    enabled = ai_settings.get('enabled', True)

    if not enabled:
        logger.info('AI enrichment disabled in config')
        write_json(output_path, passthrough_payload(payload, 'disabled_in_config'))
        return 0

    if not api_key:
        logger.info('OPENAI_API_KEY not set, skipping AI enrichment')
        write_json(output_path, passthrough_payload(payload, 'missing_api_key'))
        return 0

    report_date = payload.get('target_date') or datetime.now().strftime('%Y-%m-%d')
    papers = payload.get('top_papers', [])
    messages = build_messages(report_date, config, papers)

    try:
        response_payload = call_openai(messages, api_key, model, api_base, timeout_seconds, max_output_tokens)
        response_text = extract_output_text(response_payload)
        parsed = parse_json_output(response_text)
        enriched = merge_enrichment(payload, parsed, model)
        if response_payload.get('usage'):
            enriched['ai_enrichment']['usage'] = response_payload.get('usage')
        write_json(output_path, enriched)
        logger.info('AI enrichment completed with model %s', model)
        return 0
    except Exception as exc:
        logger.exception('AI enrichment failed: %s', exc)
        if args.strict:
            raise
        write_json(output_path, passthrough_payload(payload, f'error:{type(exc).__name__}'))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
