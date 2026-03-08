#!/usr/bin/env python3
"""Enrich ranked paper results with AI-generated English summaries and editorial guidance."""

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

from content_store import get_repo_root, parse_frontmatter, write_json

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
DEFAULT_SKILL_PATHS = [
    'skills/daily-paper-search/SKILL.md',
    'skills/daily-paper-editor/SKILL.md',
    'skills/paper-note-search/SKILL.md',
    'skills/paper-image-extractor/SKILL.md',
]
DEFAULT_EDITORIAL_PREFERENCES = {
    'audience': 'Researchers and engineers working on LLM systems, inference acceleration, compilers, and low-level code generation',
    'tone': 'Concise, direct, and judgment-oriented, like an internal systems reading memo',
    'overview_goal': "Summarize the day's systems threads without adding reading-order advice",
    'daily_brief_style': "Read like a research editor's note, not a marketing blurb",
    'prioritize': [
        'Compress each paper into a compact mini analysis that helps decide whether to read further',
        'Explain which system path changes, and what evidence supports the claimed gains',
        'Surface the biggest boundary, hardware assumption, or missing detail in the abstract',
    ],
    'avoid': [
        'Generic praise',
        'Restating the title',
        'Repeating the same point across fields',
        'Recommendation slogans such as "worth reading first" or "read this before others"',
        'Inventing experiment details, numbers, or author background',
    ],
    'custom_instruction': '',
}


def normalize_paper_id(raw: str) -> str:
    return str(raw or '').replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '').replace('arXiv:', '').strip()


def normalize_model_text(value: Any) -> str:
    text = str(value or '').replace('\r', ' ').replace('\n', ' ').replace('\u200b', ' ').strip()
    text = re.sub(r'【[^】]*oops[^】]*】', '', text, flags=re.IGNORECASE)
    text = re.sub(r'【INVALID JSON】.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\]\}\]\}\"?$', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*(?:\?{2,}|`{2,}|"{2,}|\'{2,})\s*$', '', text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"', '`'}:
        text = text[1:-1].strip()
    text = re.sub(r"^[\s'\"`,]+", '', text)
    text = re.sub(r"[\s'\"`,]+$", '', text)
    return text


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
        return 'The abstract does not provide enough information.'
    sentence = text.split('. ')[0].strip()
    if not sentence.endswith('.'):
        sentence += '.'
    return sentence


def split_sentences(text: str) -> List[str]:
    cleaned = re.sub(r'\s+', ' ', str(text or '')).strip()
    if not cleaned:
        return []
    parts = re.split(r'(?<=[.!?。！？])\s+', cleaned)
    return [part.strip() for part in parts if part.strip()]


def clip_text(text: str, max_chars: int = 180) -> str:
    value = re.sub(r'\s+', ' ', str(text or '')).strip()
    if len(value) <= max_chars:
        return value
    clipped = value[: max(0, max_chars - 1)].rsplit(' ', 1)[0].strip()
    if not clipped:
        clipped = value[: max(0, max_chars - 1)].strip()
    return clipped + '…'


def pick_sentence(sentences: List[str], keywords: List[str]) -> str:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for sentence in sentences:
        text = sentence.lower()
        if any(keyword in text for keyword in lowered_keywords):
            return sentence
    return ''


def fallback_keywords(paper: Dict[str, Any]) -> List[str]:
    items: List[str] = []
    domain = str(paper.get('matched_domain') or '').strip()
    if domain:
        items.append(domain)
    for key in paper.get('matched_keywords') or []:
        text = str(key).strip()
        if text and text not in items:
            items.append(text)
    for category in paper.get('categories') or []:
        text = str(category).strip()
        if text and text not in items:
            items.append(text)
    return items[:6]


def infer_focus_label(paper: Dict[str, Any]) -> str:
    title = str(paper.get('title') or '').lower()
    abstract = str(paper.get('summary') or paper.get('abstract') or '').lower()
    text = f'{title} {abstract}'
    if any(token in text for token in ['hallucination', 'fact', 'verify', 'verification', 'citation', 'evidence attribution', 'misattribution']):
        return 'factual reliability and verification'
    if any(token in text for token in ['latency', 'memory', 'throughput', 'speculative', 'training', 'inference', 'scaling', 'vocabulary']):
        return 'training and inference efficiency'
    if any(token in text for token in ['multimodal', 'vision-language', 'image', 'speech', 'audio', 'graph reasoning']):
        return 'multimodal modeling and reasoning'
    if any(token in text for token in ['agent', 'planning', 'exploration', 'belief', 'spatial']):
        return 'agents and active exploration'
    if any(token in text for token in ['biomedical', 'clinical', 'medical']):
        return 'medical and biomedical evidence'
    domain = str(paper.get('matched_domain') or '').strip()
    if domain:
        return domain
    return 'the main problem behind this paper'


def fallback_value_text(paper: Dict[str, Any], focus_label: str) -> str:
    title = str(paper.get('title') or '')
    text = title.lower() + ' ' + str(paper.get('summary') or paper.get('abstract') or '').lower()
    if any(token in text for token in ['latency', 'memory', 'throughput', 'training', 'inference', 'speculative']):
        return 'If the method works as claimed, its main value is lower training or inference cost and a more practical efficiency tradeoff for real systems.'
    if any(token in text for token in ['hallucination', 'fact', 'verify', 'evidence', 'citation']):
        return 'If the method works as claimed, it could improve verifiability beyond benchmarks and matter in higher-risk real deployments.'
    if any(token in text for token in ['multimodal', 'vision', 'speech', 'audio', 'graph']):
        return 'If the method works as claimed, it may push multimodal modeling toward stronger constraints, richer structure, or lower-cost deployment.'
    if any(token in text for token in ['agent', 'planning', 'exploration', 'belief']):
        return 'If the method works as claimed, it could make agents more reliable in environments that require persistent observation, state updates, and decisions.'
    return f'If the method works as claimed, it could matter for both research and engineering in {focus_label}, but the key gains still need to be checked in the full paper.'


def fallback_open_questions(paper: Dict[str, Any], evidence_sentence: str) -> List[str]:
    title = str(paper.get('title') or '').lower()
    questions = [
        'Do the gains come from the core method itself, or from data construction, training choices, or evaluation setup?',
        'Do the authors compare against strong enough baselines under genuinely difficult settings?',
    ]
    if any(token in title for token in ['latency', 'memory', 'training', 'inference', 'speculative']):
        questions.append('Do the efficiency gains still hold for larger models, longer contexts, or more realistic deployment settings?')
    elif any(token in title for token in ['hallucination', 'verify', 'evidence', 'fact', 'citation']):
        questions.append('Does the method remain reliable under out-of-distribution facts, conflicting evidence, or higher-risk scenarios?')
    elif any(token in title for token in ['multimodal', 'vision', 'speech', 'audio']):
        questions.append('Does the method stay stable under cross-modal conflict, noisy input, or more complex task pipelines?')
    else:
        questions.append('The abstract does not define the experimental boundary well; does the paper clearly report failure cases, ablations, and scope?')
    if not evidence_sentence:
        questions[1] = 'The abstract does not describe the evidence clearly; does the paper give a concrete setup, metrics, and results?'
    return questions[:3]


def fallback_recommended_for(paper: Dict[str, Any], focus_label: str) -> List[str]:
    domain = str(paper.get('matched_domain') or '').strip()
    items = [f'Researchers tracking {focus_label}']
    if domain:
        items.append(f'Engineers working on {domain} systems and methods')
    items.append('Readers who need a fast judgment on whether the paper deserves a full read')
    return items[:3]


def fallback_reading_priority(paper: Dict[str, Any], focus_label: str) -> tuple[str, str]:
    score = float(paper.get('scores', {}).get('recommendation', 0) or 0)
    if score >= 8.5:
        return 'high', f'The paper scores well and lands directly on the {focus_label} line.'
    if score >= 7.5:
        return 'medium', f'The topic fit is good, but the abstract still leaves open whether the full paper can support the central claim.'
    return 'low', 'Keep it in the candidate set for now and decide later whether it deserves full reading time.'


def fallback_paper_ai(paper: Dict[str, Any]) -> Dict[str, Any]:
    abstract = str(paper.get('summary') or paper.get('abstract') or '').strip()
    sentences = split_sentences(abstract)
    intro_sentence = sentences[0] if sentences else short_fallback_summary(paper)
    problem_sentence = pick_sentence(
        sentences,
        ['challenge', 'problem', 'task', 'goal', 'requires', 'whether', 'essential', 'understudied'],
    ) or intro_sentence
    method_sentence = pick_sentence(
        sentences,
        ['we propose', 'we introduce', 'we present', 'we develop', 'we address', 'we cast', 'our method', 'in this work'],
    ) or (sentences[1] if len(sentences) > 1 else intro_sentence)
    evidence_sentence = pick_sentence(
        sentences,
        ['experiments show', 'results show', 'achieves', 'outperforms', 'competitive', 'benchmark', 'use case', 'demo samples'],
    )
    focus_label = infer_focus_label(paper)
    keywords = fallback_keywords(paper)
    reading_priority, reading_reason = fallback_reading_priority(paper, focus_label)

    one_liner = f'The paper turns a key bottleneck in {focus_label} into a more concrete and testable method change.'
    summary_parts = [
        f'The paper frames the problem around "{clip_text(problem_sentence, 88)}."',
        f'The central move is "{clip_text(method_sentence, 92)}."',
    ]
    if evidence_sentence:
        summary_parts.append(f'The abstract cites evidence that "{clip_text(evidence_sentence, 84)}," but the key experimental assumptions still need to be checked in the full paper.')
    else:
        summary_parts.append('The abstract does not explain the setup or results clearly, so this is best treated as a method lead rather than a settled result.')

    background = f'The surrounding context is that {focus_label} is still constrained by issues such as "{clip_text(intro_sentence, 96)}."'
    problem = f'The concrete problem is: {clip_text(problem_sentence, 118)}'
    approach = f'The method signal is: {clip_text(method_sentence, 118)}'
    if evidence_sentence:
        evidence = f'The abstract-level evidence is: {clip_text(evidence_sentence, 118)}'
    else:
        evidence = 'The abstract does not clearly specify the setup, comparison baselines, or result details, so only the claimed direction is clear so far.'

    return {
        'one_liner_zh': one_liner,
        'summary_zh': ' '.join(summary_parts),
        'background_zh': background,
        'problem_zh': problem,
        'approach_zh': approach,
        'evidence_zh': evidence,
        'value_zh': fallback_value_text(paper, focus_label),
        'open_questions': fallback_open_questions(paper, evidence_sentence),
        'core_contributions': [
            f'It places the problem squarely on the {focus_label} line.',
            f'It proposes the core method move signaled in the abstract: {clip_text(method_sentence, 80)}',
            'It puts forward a set of results or application claims that require deeper verification.',
        ],
        'why_read': [
            f'It lands directly on the still-fast-moving topic of {focus_label}.',
            'The abstract at least exposes a concrete method move that can be checked against the full paper.',
            'Even if the final results are modest, the paper may still be useful for problem framing, evaluation, or system design.',
        ],
        'risks': [
            'The abstract-level evidence is limited, so many key conclusions still depend on the full experiments and ablations.',
            'If the gains depend mostly on data choices, training details, or evaluation setup, the method itself may be less generally useful than it appears.',
        ],
        'recommended_for': fallback_recommended_for(paper, focus_label),
        'keywords': keywords,
        'reading_priority': reading_priority,
        'reading_priority_reason': reading_reason,
        'fallback_summary': short_fallback_summary(paper),
    }


def fallback_daily_brief(papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not papers:
        return {
            'overview_zh': '',
            'top_themes': [],
            'reading_strategy': [],
        }

    theme_counts: Dict[str, int] = {}
    for paper in papers:
        label = infer_focus_label(paper)
        theme_counts[label] = theme_counts.get(label, 0) + 1
    top_themes = [theme for theme, _ in sorted(theme_counts.items(), key=lambda item: (-item[1], item[0]))[:3]]

    lead_titles = [clip_text(str(paper.get('title') or normalize_paper_id(paper.get('id') or '')), 36) for paper in papers[:3]]
    overview_bits = []
    if top_themes:
        overview_bits.append('Today\'s main threads are ' + ', '.join(top_themes[:2]) + '.')
    if lead_titles:
        overview_bits.append('The set is anchored by ' + ' and '.join(lead_titles[:2]) + '.')
    if len(lead_titles) >= 3:
        overview_bits.append(f'{lead_titles[2]} adds another data point on whether the same line of work carries stronger evidence or engineering value.')

    reading_strategy: List[str] = []
    for index, paper in enumerate(papers[:3], start=1):
        label = clip_text(str(paper.get('title') or normalize_paper_id(paper.get('id') or '')), 36)
        focus_label = infer_focus_label(paper)
        if index == 1:
            reading_strategy.append(f'Start with {label} and verify whether it defines the {focus_label} problem clearly and exposes a real mechanism.')
        elif index == 2:
            reading_strategy.append(f'Then read {label} to see whether the novelty comes from model design, training procedure, or evaluation reframing.')
        else:
            reading_strategy.append(f'Use {label} as a final cross-check on experimental boundaries and practical value.')

    return {
        'overview_zh': ' '.join(overview_bits).strip(),
        'top_themes': top_themes[:3],
        'reading_strategy': reading_strategy[:3],
    }


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
    for key in ['recommendation', 'relevance', 'recency', 'popularity', 'quality']:
        if key in scores:
            result[key] = scores[key]
    return result


def normalize_editorial_preferences(config: Dict[str, Any]) -> Dict[str, Any]:
    ai_settings = config.get('ai', {}) if isinstance(config, dict) else {}
    raw_preferences = ai_settings.get('editorial_preferences', {})
    if not isinstance(raw_preferences, dict):
        raw_preferences = {}

    prioritize = coerce_string_list(raw_preferences.get('prioritize'), max_items=6)
    avoid = coerce_string_list(raw_preferences.get('avoid'), max_items=6)
    if not prioritize:
        prioritize = list(DEFAULT_EDITORIAL_PREFERENCES['prioritize'])
    if not avoid:
        avoid = list(DEFAULT_EDITORIAL_PREFERENCES['avoid'])

    return {
        'audience': str(raw_preferences.get('audience') or DEFAULT_EDITORIAL_PREFERENCES['audience']).strip(),
        'tone': str(raw_preferences.get('tone') or DEFAULT_EDITORIAL_PREFERENCES['tone']).strip(),
        'overview_goal': str(raw_preferences.get('overview_goal') or DEFAULT_EDITORIAL_PREFERENCES['overview_goal']).strip(),
        'daily_brief_style': str(raw_preferences.get('daily_brief_style') or DEFAULT_EDITORIAL_PREFERENCES['daily_brief_style']).strip(),
        'prioritize': prioritize,
        'avoid': avoid,
        'custom_instruction': str(raw_preferences.get('custom_instruction') or DEFAULT_EDITORIAL_PREFERENCES['custom_instruction']).strip(),
    }


def normalize_skill_paths(config: Dict[str, Any]) -> List[str]:
    ai_settings = config.get('ai', {}) if isinstance(config, dict) else {}
    raw_paths = ai_settings.get('skill_paths')
    if raw_paths is None:
        raw_paths = list(DEFAULT_SKILL_PATHS)

    if isinstance(raw_paths, str):
        paths = [part.strip() for part in raw_paths.split(',') if part.strip()]
    elif isinstance(raw_paths, list):
        paths = [str(part).strip() for part in raw_paths if str(part).strip()]
    else:
        paths = list(DEFAULT_SKILL_PATHS)

    return list(dict.fromkeys(paths))


def load_skill_blocks(repo_root: Path, config: Dict[str, Any]) -> List[Dict[str, str]]:
    blocks: List[Dict[str, str]] = []

    for relative_path in normalize_skill_paths(config):
        path = Path(relative_path)
        if not path.is_absolute():
            path = repo_root / path
        if not path.exists() or not path.is_file():
            continue

        text = path.read_text(encoding='utf-8')
        frontmatter, body = parse_frontmatter(text)
        skill_name = str(frontmatter.get('name') or path.stem).strip() or path.stem
        try:
            display_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            display_path = str(path)

        blocks.append({
            'name': skill_name,
            'path': display_path,
            'body': body.strip() or text.strip(),
        })

    return blocks


def build_skill_prompt_text(repo_root: Path, config: Dict[str, Any]) -> str:
    blocks = load_skill_blocks(repo_root, config)
    if not blocks:
        return ''

    parts = []
    for block in blocks:
        parts.append(f"Skill `{block['name']}` from `{block['path']}`:\n{block['body']}")
    return '\n\n'.join(parts)


def build_editorial_instruction_text(config: Dict[str, Any]) -> str:
    preferences = normalize_editorial_preferences(config)
    lines = [
        f"Audience: {preferences['audience']}",
        f"Tone: {preferences['tone']}",
        f"Daily brief goal: {preferences['overview_goal']}",
        f"Daily brief style: {preferences['daily_brief_style']}",
        'Mini-analysis target: each paper should be compressible into one compact evaluation note with minimal repetition.',
        'Prioritize:',
    ]
    lines.extend(f"- {item}" for item in preferences['prioritize'])
    lines.append('Avoid:')
    lines.extend(f"- {item}" for item in preferences['avoid'])
    if preferences['custom_instruction']:
        lines.append(f"Custom instruction: {preferences['custom_instruction']}")
    return '\n'.join(lines)


def build_prompt_payload(
    report_date: str,
    config: Dict[str, Any],
    papers: List[Dict[str, Any]],
    *,
    paper_limit: int,
    max_abstract_chars: int,
    max_authors: int = 4,
) -> Dict[str, Any]:
    domain_configs = config.get('research_domains', {}) if isinstance(config, dict) else {}
    domains = []
    if isinstance(domain_configs, dict):
        for name, domain_config in domain_configs.items():
            priority = 0
            if isinstance(domain_config, dict):
                try:
                    priority = int(domain_config.get('priority', 0))
                except (TypeError, ValueError):
                    priority = 0
            domains.append({'name': str(name), 'priority': priority})

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
            'categories': (paper.get('categories') or [])[:6],
            'matched_keywords': (paper.get('matched_keywords') or [])[:6],
            'selection_signals': {
                'source': paper.get('source', ''),
                'is_hot_paper': bool(paper.get('is_hot_paper')),
                'domain_priority': paper.get('matched_domain_priority', 0),
                'domain_preference_bonus': paper.get('domain_preference_bonus', 0),
            },
            'scores': compact_scores(paper.get('scores', {})),
        })

    return {
        'report_date': report_date,
        'preferred_language': 'en-US',
        'research_domains': domains,
        'editorial_preferences': normalize_editorial_preferences(config),
        'papers': prompt_papers,
    }


def build_messages(
    repo_root: Path,
    report_date: str,
    config: Dict[str, Any],
    papers: List[Dict[str, Any]],
    *,
    paper_limit: int,
    max_abstract_chars: int,
    max_authors: int = 4,
) -> List[Dict[str, str]]:
    system_prompt = (
        'You are a rigorous research editor producing a high-signal daily paper digest in English. '
        'Use only the metadata and abstracts provided. Do not invent metrics, experiments, authors, or claims not present in the input. '
        'If the abstract is vague, explicitly say the abstract does not make the point clear. '
        'Return valid JSON only. '
        'The JSON object must have keys daily_brief and papers. '
        'daily_brief must contain overview_zh (string), top_themes (array of 3 short strings), and reading_strategy (array of 3 short strings). '
        'papers must be an array where each item contains: paper_id (string), one_liner_zh (string), summary_zh (string, 2-3 sentences), '
        'background_zh (string), problem_zh (string), approach_zh (string), evidence_zh (string), value_zh (string), open_questions (array of 2-3 strings), '
        'core_contributions (array of 3 strings), why_read (array of 3 strings), risks (array of 2 strings), '
        'recommended_for (array of 2-3 strings), keywords (array of 4-6 short strings), reading_priority (one of high, medium, low), '
        'and reading_priority_reason (string). '
        'The fields must be short and non-overlapping so they can be recomposed into one concise mini-analysis. '
        'background_zh, problem_zh, approach_zh, evidence_zh, value_zh should each stay to one high-signal sentence. '
        'summary_zh should already read like a compact editor assessment instead of a field dump. '
        'All string fields should be written in English even though the field names end with _zh for compatibility. '
        'one_liner_zh and summary_zh should describe the paper itself, not use recommendation slogans such as "worth reading first" or "read this before others." '
        'evidence_zh should state what the abstract actually claims about evaluation, or say the abstract does not make it clear. '
        'open_questions should list the most important things to verify when reading the full paper.'
    )
    editorial_instructions = build_editorial_instruction_text(config)
    skill_instructions = build_skill_prompt_text(repo_root, config)
    if editorial_instructions:
        system_prompt += '\n\nRepository editorial preferences:\n' + editorial_instructions
    if skill_instructions:
        system_prompt += '\n\nProject skill instructions:\n' + skill_instructions
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
        items = []
        for item in value:
            raw = normalize_model_text(item)
            if not raw:
                continue
            pieces = [raw]
            for pattern in (
                r"'\s*,\s*'",
                r'"\s*,\s*"',
                r'`\s*,\s*`',
                r"[\"'`]\s*,\s*[\"'`]",
            ):
                next_pieces = []
                for piece in pieces:
                    next_pieces.extend(re.split(pattern, piece))
                pieces = next_pieces
            for piece in pieces:
                cleaned = normalize_model_text(piece)
                if cleaned:
                    items.append(cleaned)
    deduped: List[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    items = deduped[:max_items]
    if len(items) < min_items:
        items.extend(fallback[: max(0, min_items - len(items))])
    return items


def normalize_daily_brief(data: Dict[str, Any], papers: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    daily = data.get('daily_brief', {}) if isinstance(data, dict) else {}
    fallback = fallback_daily_brief(papers or [])
    overview = str(daily.get('overview_zh') or fallback.get('overview_zh') or '').strip()
    top_themes = coerce_string_list(
        daily.get('top_themes'),
        min_items=min(3, len(fallback.get('top_themes', []))),
        max_items=3,
        fallback=fallback.get('top_themes', []),
    )
    reading_strategy = coerce_string_list(
        daily.get('reading_strategy'),
        min_items=min(3, len(fallback.get('reading_strategy', []))),
        max_items=3,
        fallback=fallback.get('reading_strategy', []),
    )
    return {
        'overview_zh': overview,
        'top_themes': top_themes,
        'reading_strategy': reading_strategy,
    }


def normalize_paper_ai(item: Dict[str, Any], fallback_paper: Dict[str, Any]) -> Dict[str, Any]:
    fallback_ai = fallback_paper_ai(fallback_paper)
    summary = normalize_model_text(item.get('summary_zh') or '')
    background = normalize_model_text(item.get('background_zh') or '')
    problem = normalize_model_text(item.get('problem_zh') or '')
    approach = normalize_model_text(item.get('approach_zh') or '')
    evidence = normalize_model_text(item.get('evidence_zh') or '')
    value = normalize_model_text(item.get('value_zh') or '')
    return {
        'one_liner_zh': normalize_model_text(item.get('one_liner_zh') or '') or fallback_ai['one_liner_zh'],
        'summary_zh': summary or fallback_ai['summary_zh'],
        'background_zh': background or fallback_ai['background_zh'],
        'problem_zh': problem or fallback_ai['problem_zh'],
        'approach_zh': approach or fallback_ai['approach_zh'],
        'evidence_zh': evidence or fallback_ai['evidence_zh'],
        'value_zh': value or fallback_ai['value_zh'],
        'open_questions': coerce_string_list(item.get('open_questions'), min_items=3, max_items=3, fallback=fallback_ai['open_questions']),
        'core_contributions': coerce_string_list(item.get('core_contributions'), min_items=3, max_items=3, fallback=fallback_ai['core_contributions']),
        'why_read': coerce_string_list(item.get('why_read'), min_items=3, max_items=3, fallback=fallback_ai['why_read']),
        'risks': coerce_string_list(item.get('risks'), min_items=2, max_items=2, fallback=fallback_ai['risks']),
        'recommended_for': coerce_string_list(item.get('recommended_for'), min_items=3, max_items=3, fallback=fallback_ai['recommended_for']),
        'keywords': coerce_string_list(item.get('keywords'), min_items=min(4, len(fallback_ai['keywords'])), max_items=6, fallback=fallback_ai['keywords']),
        'reading_priority': normalize_model_text(item.get('reading_priority') or fallback_ai['reading_priority']).lower() or fallback_ai['reading_priority'],
        'reading_priority_reason': normalize_model_text(item.get('reading_priority_reason') or '') or fallback_ai['reading_priority_reason'],
        'fallback_summary': fallback_ai['fallback_summary'],
    }


def merge_enrichment(payload: Dict[str, Any], raw_ai: Dict[str, Any], model: str) -> Dict[str, Any]:
    enriched = copy.deepcopy(payload)
    papers = enriched.get('top_papers', [])
    normalized_daily = normalize_daily_brief(raw_ai, papers)
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
    result['daily_brief'] = fallback_daily_brief(result.get('top_papers', []))
    for paper in result.get('top_papers', []):
        paper['ai'] = fallback_paper_ai(paper)
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
                    repo_root,
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
                    repo_root,
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
                repo_root,
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
