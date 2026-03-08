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
    'skills/paper-deep-analysis/SKILL.md',
    'skills/paper-image-extractor/SKILL.md',
]
DEFAULT_EDITORIAL_PREFERENCES = {
    'audience': '关注大模型、Agent、多模态系统与高价值方法论文的研究者和工程师',
    'tone': '简洁、直接、高信息密度，少空话',
    'overview_goal': '先点出今天最值得读的主线，再给阅读顺序建议',
    'daily_brief_style': '像研究日报编辑，不像宣传文案',
    'prioritize': [
        '为什么这篇论文现在值得读',
        '方法或问题定义的新意在哪里',
        '最大的风险、边界或摘要未说明之处',
    ],
    'avoid': [
        '空泛赞美',
        '复述标题',
        '编造实验细节、数字或作者背景',
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
        return '摘要未提供足够信息。'
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
        return '可信性与事实核验'
    if any(token in text for token in ['latency', 'memory', 'throughput', 'speculative', 'training', 'inference', 'scaling', 'vocabulary']):
        return '训练与推理效率'
    if any(token in text for token in ['multimodal', 'vision-language', 'image', 'speech', 'audio', 'graph reasoning']):
        return '多模态建模与推理'
    if any(token in text for token in ['agent', 'planning', 'exploration', 'belief', 'spatial']):
        return 'agent 与主动探索'
    if any(token in text for token in ['biomedical', 'clinical', 'medical']):
        return '医疗与生物医药证据'
    domain = str(paper.get('matched_domain') or '').strip()
    if domain:
        return domain
    return '当前研究重点问题'


def fallback_value_text(paper: Dict[str, Any], focus_label: str) -> str:
    title = str(paper.get('title') or '')
    text = title.lower() + ' ' + str(paper.get('summary') or paper.get('abstract') or '').lower()
    if any(token in text for token in ['latency', 'memory', 'throughput', 'training', 'inference', 'speculative']):
        return '如果方法成立，它的直接价值是把训练或推理成本进一步压低，并把效率收益变成更可落地的系统设计选择。'
    if any(token in text for token in ['hallucination', 'fact', 'verify', 'evidence', 'citation']):
        return '如果方法成立，它会提升模型输出的可核验性，价值不只在 benchmark，而在真实高风险场景里的可信使用。'
    if any(token in text for token in ['multimodal', 'vision', 'speech', 'audio', 'graph']):
        return '如果方法成立，它的价值在于把跨模态建模从单一配对任务推进到更强约束、更复杂结构或更低成本的设置。'
    if any(token in text for token in ['agent', 'planning', 'exploration', 'belief']):
        return '如果方法成立，它的价值在于让 agent 在需要持续观察、更新状态和决策的环境里更可靠。'
    return f'如果方法成立，它对{focus_label}方向的研究和工程都有直接参考价值，但关键收益仍要靠正文实验核对。'


def fallback_open_questions(paper: Dict[str, Any], evidence_sentence: str) -> List[str]:
    title = str(paper.get('title') or '').lower()
    questions = [
        '关键增益到底来自核心方法本身，还是来自数据构造、训练配方或评测口径？',
        '作者是否和足够强的基线做了公平比较，并覆盖了真正困难的设置？',
    ]
    if any(token in title for token in ['latency', 'memory', 'training', 'inference', 'speculative']):
        questions.append('效率收益在更大模型、更长上下文或更真实部署条件下是否仍然成立？')
    elif any(token in title for token in ['hallucination', 'verify', 'evidence', 'fact', 'citation']):
        questions.append('方法在分布外事实、复杂证据冲突和高风险场景下是否仍然可靠？')
    elif any(token in title for token in ['multimodal', 'vision', 'speech', 'audio']):
        questions.append('方法在跨模态冲突、噪声输入或更复杂任务链路上是否仍然稳定？')
    else:
        questions.append('摘要没有充分说明实验边界，正文是否明确交代失败案例、消融和适用范围？')
    if not evidence_sentence:
        questions[1] = '摘要没有充分说明证据，正文是否给出足够清楚的实验设置、指标和结果？'
    return questions[:3]


def fallback_recommended_for(paper: Dict[str, Any], focus_label: str) -> List[str]:
    domain = str(paper.get('matched_domain') or '').strip()
    items = [f'关注{focus_label}的研究者']
    if domain:
        items.append(f'{domain}系统与方法工程师')
    items.append('需要快速判断论文是否值得全文阅读的读者')
    return items[:3]


def fallback_reading_priority(paper: Dict[str, Any], focus_label: str) -> tuple[str, str]:
    score = float(paper.get('scores', {}).get('recommendation', 0) or 0)
    if score >= 8.5:
        return 'high', f'推荐分较高，而且它直接落在{focus_label}主线上，值得优先阅读全文。'
    if score >= 7.5:
        return 'medium', f'主题相关性不错，但是否值得深读仍取决于正文能否支撑摘要里的关键主张。'
    return 'low', '可以先保留在候选清单里，等确认主线论文后再决定是否投入全文阅读时间。'


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

    one_liner = f"这篇工作聚焦{focus_label}，重点在于用更明确的方法机制去处理“{clip_text(problem_sentence, 72)}”这类问题。"
    summary_parts = [
        f"这篇论文聚焦{focus_label}，摘要把核心问题放在“{clip_text(problem_sentence, 110)}”上。",
        f"它给出的主要做法是“{clip_text(method_sentence, 110)}”。",
    ]
    if evidence_sentence:
        summary_parts.append(f"摘要提到的证据是“{clip_text(evidence_sentence, 100)}”，但具体实验细节仍需要阅读全文确认。")
    else:
        summary_parts.append('摘要没有充分说明实验设置和结果细节，因此当前更适合把它当成值得核对的方法线索，而不是已被完全证实的结论。')

    background = (
        f"这篇工作位于{str(paper.get('matched_domain') or '相关').strip()}方向，摘要把背景放在“{clip_text(intro_sentence, 150)}”这一类问题上。"
        f"它对应当前{focus_label}研究里对能力、效率或可靠性的持续需求。"
    )
    problem = f"论文想解决的核心问题是：{clip_text(problem_sentence, 180)}"
    approach = f"摘要给出的主要方法线索是：{clip_text(method_sentence, 180)}"
    if evidence_sentence:
        evidence = f"摘要里提到的证据主要是：{clip_text(evidence_sentence, 180)}"
    else:
        evidence = '摘要没有充分说明实验设置、对比基线和结果细节，目前只能确认作者声称方法在目标任务上有效。'

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
            f'把问题明确放到{focus_label}这条主线上。',
            f'提出了摘要里最核心的方法动作：{clip_text(method_sentence, 80)}',
            '给出了一组需要进一步核对的结果或应用声称。',
        ],
        'why_read': [
            f'它直接命中{focus_label}这个当前仍在快速演化的主题。',
            '摘要至少给出了可复述的方法动作，值得核对正文是否真的站得住。',
            '即使最终结论一般，这篇论文也可能提供问题定义、评测或系统设计上的参考。',
        ],
        'risks': [
            '摘要层面的信息仍然有限，很多关键结论必须靠正文实验和消融确认。',
            '如果摘要里的收益主要来自数据、训练细节或评测口径，方法本身的通用价值可能会被高估。',
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
        overview_bits.append('今天最值得读的主线是' + '、'.join(top_themes[:2]) + '。')
    if lead_titles:
        overview_bits.append('优先看 ' + '、'.join(lead_titles[:2]) + '，因为它们最直接代表今天的主干问题。')
    if len(lead_titles) >= 3:
        overview_bits.append(f'第三篇可用 {lead_titles[2]} 来判断这条方法线是否具备更强的证据或工程价值。')

    reading_strategy: List[str] = []
    for index, paper in enumerate(papers[:3], start=1):
        label = clip_text(str(paper.get('title') or normalize_paper_id(paper.get('id') or '')), 36)
        focus_label = infer_focus_label(paper)
        if index == 1:
            reading_strategy.append(f'先读 {label}，重点核对它对{focus_label}问题的任务定义和核心机制是否清楚。')
        elif index == 2:
            reading_strategy.append(f'再读 {label}，判断它的方法新意到底来自模型设计、训练流程还是评测重设。')
        else:
            reading_strategy.append(f'最后读 {label}，把它当成对今天主线的补充验证，重点看实验边界和真实价值。')

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
        'preferred_language': 'zh-CN',
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
        'You are a rigorous research editor producing a high-signal daily paper digest in Simplified Chinese. '
        'Use only the metadata and abstracts provided. Do not invent metrics, experiments, authors, or claims not present in the input. '
        'If the abstract is vague, explicitly say the abstract does not make the point clear. '
        'Return valid JSON only. '
        'The JSON object must have keys daily_brief and papers. '
        'daily_brief must contain overview_zh (string), top_themes (array of 3 short strings), and reading_strategy (array of 3 short strings). '
        'papers must be an array where each item contains: paper_id (string), one_liner_zh (string), summary_zh (string, 2-4 sentences), '
        'background_zh (string), problem_zh (string), approach_zh (string), evidence_zh (string), value_zh (string), open_questions (array of 2-3 strings), '
        'core_contributions (array of 3 strings), why_read (array of 3 strings), risks (array of 2 strings), '
        'recommended_for (array of 2-3 strings), keywords (array of 4-6 short strings), reading_priority (one of high, medium, low), '
        'and reading_priority_reason (string). '
        'background_zh should explain the field context and motivation in 1-2 sentences. '
        'problem_zh should explain the task and why it matters now. '
        'approach_zh should explain the main mechanism or modeling move. '
        'evidence_zh should state what the abstract actually claims about evaluation, or say the abstract does not make it clear. '
        'value_zh should explain the likely research or engineering value if the paper works as claimed. '
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
