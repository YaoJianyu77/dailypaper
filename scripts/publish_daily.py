#!/usr/bin/env python3
"""Publish the daily report into the content store."""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml

from content_store import (
    get_content_root,
    get_daily_root,
    get_meta_root,
    get_paper_assets_root,
    get_papers_root,
    get_repo_root,
    paper_slug,
    write_json,
    write_markdown,
)


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SCAN_SCRIPT = REPO_ROOT / 'start-my-day' / 'scripts' / 'scan_existing_notes.py'
LINK_SCRIPT = REPO_ROOT / 'start-my-day' / 'scripts' / 'link_keywords.py'
EXTRACT_IMAGES_SCRIPT = REPO_ROOT / 'extract-paper-images' / 'scripts' / 'extract_images.py'
UPDATE_GRAPH_SCRIPT = REPO_ROOT / 'paper-analyze' / 'scripts' / 'update_graph.py'
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}

logger = logging.getLogger(__name__)

KNOWN_VENUE_ALIASES = {
    'cvpr': 'CVPR',
    'iccv': 'ICCV',
    'eccv': 'ECCV',
    'iclr': 'ICLR',
    'icml': 'ICML',
    'neurips': 'NeurIPS',
    'acl': 'ACL',
    'emnlp': 'EMNLP',
    'naacl': 'NAACL',
    'coling': 'COLING',
    'aaai': 'AAAI',
    'ijcai': 'IJCAI',
    'kdd': 'KDD',
    'sigir': 'SIGIR',
    'www': 'WWW',
    'uai': 'UAI',
    'aistats': 'AISTATS',
    'icra': 'ICRA',
    'rss': 'RSS',
    'corl': 'CoRL',
    'wacv': 'WACV',
    'icassp': 'ICASSP',
}
VENUE_HINTS = (
    'conference', 'journal', 'transactions', 'proceedings', 'workshop', 'symposium',
    'review', 'letters', 'nature', 'science', 'technical report',
)
REVISION_NOTE_HINTS = (
    'this version', 'clarity of our research', 'camera-ready', 'updated version',
    'minor revision', 'major revision', 'supplementary material',
)


def normalize_paper_id(raw: str) -> str:
    return str(raw or '').replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '').replace('arXiv:', '').strip()


def normalize_title_key(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', str(title or '').lower()).strip()


def looks_like_arxiv_id(value: str) -> bool:
    return bool(re.fullmatch(r'\d{4}\.\d+(?:v\d+)?', str(value or '').strip()))


def normalize_image_token(value: str) -> str:
    text = str(value or '').strip().lower()
    text = text.replace('\\', '/').split('/')[-1]
    text = text.rsplit('.', 1)[0]
    text = text.removesuffix('_page1')
    text = ''.join(ch for ch in text if ch.isalnum())
    return text


def relative_asset_url(path: Path, repo_root: Path) -> str:
    rel = path.relative_to(get_content_root(repo_root)).as_posix()
    return '/' + rel.lstrip('/')


def paper_urls(paper_id: str, paper: Dict[str, Any] | None = None) -> tuple[str, str]:
    if isinstance(paper, dict):
        source_url = clean_render_text(paper.get('source_url') or paper.get('url') or '')
        pdf_url = clean_render_text(paper.get('pdf_url') or '')
        if source_url or pdf_url:
            return source_url or pdf_url, pdf_url
    pid = normalize_paper_id(paper_id)
    return f'https://arxiv.org/abs/{pid}', f'https://arxiv.org/pdf/{pid}.pdf'


def ai_fields(paper: Dict[str, Any]) -> Dict[str, Any]:
    return paper.get('ai', {}) if isinstance(paper.get('ai'), dict) else {}

def clean_render_text(value: Any) -> str:
    text = str(value or '').replace('\r', ' ').replace('\n', ' ').replace('\u200b', ' ').strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*(?:\?{2,}|`{2,}|"{2,}|\'{2,})\s*$', '', text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"', '`'}:
        text = text[1:-1].strip()
    return text.strip(' ,;:|')


def clip_text(text: str, max_chars: int) -> str:
    value = clean_render_text(text)
    if len(value) <= max_chars:
        return value
    clipped = value[: max(0, max_chars - 1)].rsplit(' ', 1)[0].strip()
    if not clipped:
        clipped = value[: max(0, max_chars - 1)].strip()
    return clipped + '…'


def clean_institution_name(value: Any) -> str:
    text = clean_render_text(value)
    text = re.sub(r'^[\d\W_]+(?=[A-Za-z])', '', text)
    text = re.sub(r'^(?:affiliation|institution)\s*[:：-]\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(
        r'\b(?:equal contribution|corresponding author|work done during.*|internship)\b.*$',
        '',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r'\s+', ' ', text).strip(' ,;:-')
    if not text or text.lower() == 'institution information not extracted':
        return ''
    if len(text) < 4 or re.fullmatch(r'[\d\W_]+', text):
        return ''
    return text


def looks_like_venue_metadata(text: str) -> bool:
    lowered = clean_render_text(text).lower()
    if not lowered:
        return False
    if any(token in lowered for token in REVISION_NOTE_HINTS):
        return False
    if re.fullmatch(r'\d+\s+pages?(?:,\s*\d+\s+figures?)?', lowered):
        return False
    if lowered in {'preprint', 'pre-print', 'arxiv preprint'}:
        return True
    if any(token in lowered for token in VENUE_HINTS):
        return True
    return any(alias in lowered for alias in KNOWN_VENUE_ALIASES)


def normalize_venue_label(value: Any) -> str:
    text = clean_render_text(value)
    lowered = text.lower()
    if not text:
        return ''
    for prefix in ('published at ', 'accepted at ', 'to appear in ', 'appearing in '):
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip()
            lowered = text.lower()
            break
    if lowered in {'preprint', 'pre-print', 'arxiv preprint'}:
        return 'arXiv preprint'
    if lowered.startswith('technical report'):
        return 'Technical report'
    if re.fullmatch(r'\d+\s+pages?(?:,\s*\d+\s+figures?)?', lowered):
        return ''
    if any(token in lowered for token in REVISION_NOTE_HINTS):
        return ''
    if not looks_like_venue_metadata(text):
        return ''
    for alias, canonical in KNOWN_VENUE_ALIASES.items():
        text = re.sub(rf'\b{re.escape(alias)}\b', canonical, text, flags=re.IGNORECASE)
    return clean_render_text(text)


def normalize_string_list(
    value: Any,
    limit: int = 8,
    cleaner: Callable[[Any], str] = clean_render_text,
) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    seen: set[str] = set()
    for item in value:
        text = cleaner(item)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def paper_institutions(paper: Dict[str, Any]) -> List[str]:
    institutions = normalize_string_list(paper.get('institutions'), limit=8, cleaner=clean_institution_name)
    if institutions:
        return institutions

    author_details = paper.get('author_details')
    if isinstance(author_details, list):
        extracted = []
        for item in author_details:
            if not isinstance(item, dict):
                continue
            text = str(item.get('affiliation') or '').strip()
            if text:
                extracted.append(text)
        institutions = normalize_string_list(extracted, limit=8, cleaner=clean_institution_name)
        if institutions:
            return institutions

    return []


def paper_venue_or_journal(paper: Dict[str, Any]) -> str:
    for key in ['journal_ref', 'venue', 'comments']:
        text = normalize_venue_label(paper.get(key) or '')
        if text:
            return text
    source = str(paper.get('source') or '').strip()
    if source in {'dblp_venue', 'openalex_venue'}:
        fallback = clean_render_text(paper.get('venue_source_name') or paper.get('venue') or '')
        if fallback:
            return fallback
    return 'arXiv preprint'


def paper_citation_summary(paper: Dict[str, Any]) -> str:
    citation_count = paper.get('citationCount')
    influential_count = paper.get('influentialCitationCount')
    if citation_count is None and influential_count is None:
        return 'Citation count unavailable'
    if citation_count is not None and influential_count is not None:
        return f'{citation_count} citations ({influential_count} influential)'
    if citation_count is not None:
        return f'{citation_count} citations'
    return f'{influential_count} influential citations'


def daily_source_label(paper: Dict[str, Any]) -> str:
    venue = paper_venue_or_journal(paper)
    source = str(paper.get('source') or '').strip()
    if venue and venue != 'arXiv preprint':
        return venue
    if source == 'dblp_venue':
        return clean_render_text(paper.get('venue_source_name') or paper.get('venue') or 'DBLP venue paper')
    if source == 'openalex_venue':
        return clean_render_text(paper.get('venue_source_name') or paper.get('venue') or 'OpenAlex venue paper')
    if source == 'classic_backlog':
        return '经典 systems 论文'
    if source == 'arxiv_hot_fallback':
        return 'arXiv 热门窗口候选'
    if source == 'semantic_scholar':
        return 'Semantic Scholar 热门检索'
    return 'arXiv 预印本'


def fallback_summary(paper: Dict[str, Any]) -> str:
    text = (paper.get('summary') or paper.get('abstract') or '').replace('\n', ' ').strip()
    if not text:
        return 'No summary available.'
    sentence = text.split('. ')[0].strip()
    if not sentence.endswith('.'):
        sentence += '.'
    return sentence


def summarize_paper(paper: Dict[str, Any]) -> str:
    ai = ai_fields(paper)
    return ai.get('one_liner_zh') or ai.get('fallback_summary') or fallback_summary(paper)


def detail_summary(paper: Dict[str, Any]) -> str:
    ai = ai_fields(paper)
    return ai.get('summary_zh') or ai.get('fallback_summary') or fallback_summary(paper)


def unique_texts(values: List[Any], limit: int | None = None) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_render_text(value)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
        if limit is not None and len(result) >= limit:
            break
    return result


def join_analysis_text(values: List[Any], limit: int | None = None) -> str:
    parts = unique_texts(values, limit=limit)
    return ' '.join(parts)


def daily_context_text(paper: Dict[str, Any]) -> str:
    ai = ai_fields(paper)
    return join_analysis_text([
        ai.get('background_zh'),
        ai.get('problem_zh'),
    ])


def daily_method_evidence_text(paper: Dict[str, Any]) -> str:
    ai = ai_fields(paper)
    return join_analysis_text([
        ai.get('approach_zh'),
        ai.get('evidence_zh'),
    ])


def daily_value_text(paper: Dict[str, Any]) -> str:
    ai = ai_fields(paper)
    why_read = normalize_string_list(ai.get('why_read', []), limit=2)
    return join_analysis_text([
        ai.get('value_zh'),
        ai.get('reading_priority_reason'),
        '；'.join(why_read) if why_read else '',
    ])


def daily_risk_text(paper: Dict[str, Any]) -> str:
    ai = ai_fields(paper)
    risks = normalize_string_list(ai.get('risks', []), limit=3)
    return '；'.join(unique_texts(risks, limit=3))


def compact_analysis_text(paper: Dict[str, Any]) -> str:
    primary = detail_summary(paper)
    parts: List[str] = []
    if primary and primary != summarize_paper(paper):
        parts.append(primary)
    else:
        parts.extend([
            daily_context_text(paper),
            daily_method_evidence_text(paper),
        ])
    return clip_text(join_analysis_text(parts, limit=3), 420)


def compact_evaluation_text(paper: Dict[str, Any]) -> str:
    ai = ai_fields(paper)
    why_read = normalize_string_list(ai.get('why_read', []), limit=1)
    parts = [
        ai.get('value_zh'),
        why_read[0] if why_read else '',
    ]
    value_text = join_analysis_text(parts, limit=2)
    risk_text = daily_risk_text(paper)
    if value_text and risk_text:
        return clip_text(f'{value_text} 但要先核对：{risk_text}', 280)
    return clip_text(value_text or risk_text, 280)


def selection_lane(paper: Dict[str, Any]) -> str:
    lane = str(paper.get('selection_lane') or paper.get('source_lane') or '').strip().lower()
    if lane in {'fresh', 'established', 'classic'}:
        return lane
    return 'fresh'


def lane_label(paper: Dict[str, Any]) -> str:
    lane = selection_lane(paper)
    if lane == 'classic':
        return '经典补课位'
    if lane == 'established':
        return '已验证的 systems 论文'
    return 'fresh systems 论文'


def reading_priority_label(value: str) -> str:
    text = clean_render_text(value).lower()
    if text == 'high':
        return '高优先级'
    if text == 'medium':
        return '中优先级'
    if text == 'low':
        return '低优先级'
    return clean_render_text(value) or '未标注优先级'


def split_daily_papers(papers: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    primary = [paper for paper in papers if selection_lane(paper) != 'classic']
    classics = [paper for paper in papers if selection_lane(paper) == 'classic']
    return primary, classics


def lead_paper(papers: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not papers:
        return None
    return max(
        papers,
        key=lambda paper: (
            float(paper.get('scores', {}).get('recommendation', 0) or 0),
            str(paper.get('title') or '').lower(),
        ),
    )


def ordered_primary_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    primary, _ = split_daily_papers(papers)
    if not primary:
        return []

    lead = lead_paper(primary)
    remaining = [
        paper for paper in primary
        if normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        != normalize_paper_id((lead or {}).get('arxiv_id') or (lead or {}).get('arxivId') or (lead or {}).get('id', ''))
    ]
    lane_rank = {'fresh': 0, 'established': 1, 'classic': 2}
    remaining.sort(
        key=lambda paper: (
            lane_rank.get(selection_lane(paper), 9),
            -float(paper.get('scores', {}).get('recommendation', 0) or 0),
            str(paper.get('title') or '').lower(),
        )
    )
    return ([lead] if lead else []) + remaining


def inferred_top_themes(papers: List[Dict[str, Any]]) -> List[str]:
    theme_rules = [
        (('flashattention', 'attention kernel', 'attention'), 'attention kernel 优化'),
        (('sparse', 'sparsity', 'tensor core'), '结构化稀疏'),
        (('speculative decoding', 'draft model', 'vocabulary trimming'), 'speculative decoding'),
        (('prefill', 'decode', 'ttft', 'tpot', 'slo'), 'P/D 资源调度'),
        (('quantization', 'gptq', '4bit', '4-bit', 'int8'), '低比特量化'),
        (('cuda', 'cute', 'triton', 'ptx', 'sass', 'kernel'), 'CUDA kernel 与编译器协同设计'),
    ]
    themes: List[str] = []
    for paper in papers:
        text_parts = [
            str(paper.get('title') or ''),
            str(paper.get('matched_domain') or ''),
        ]
        text_parts.extend(str(item) for item in (ai_fields(paper).get('keywords') or []))
        haystack = ' '.join(text_parts).lower()
        for keywords, label in theme_rules:
            if label in themes:
                continue
            if any(keyword in haystack for keyword in keywords):
                themes.append(label)
        if len(themes) >= 4:
            break
    if not themes and papers:
        themes.append('LLM systems')
    return themes[:4]


def build_overview(papers: List[Dict[str, Any]], paper_meta_map: Dict[str, Dict[str, str]]) -> str:
    if not papers:
        return '今天没有筛到满足当前 systems 规则的论文。'

    primary, classics = split_daily_papers(papers)
    lane_counts = Counter(selection_lane(paper) for paper in papers)
    themes = inferred_top_themes(papers)
    lead = lead_paper(papers)
    parts: List[str] = []

    if themes:
        parts.append(f'今天主线集中在{"、".join(themes)}。')

    mix: List[str] = []
    if lane_counts.get('fresh'):
        mix.append(f'{lane_counts["fresh"]} 篇新论文主线')
    if lane_counts.get('established'):
        mix.append(f'{lane_counts["established"]} 篇已验证论文')
    if classics:
        mix.append(f'{len(classics)} 篇经典补课论文')
    if mix:
        parts.append(f'本轮实际保留了{"、".join(mix)}，没有为凑数强行补满。')

    if lead:
        title = str(lead.get('title') or 'Untitled Paper')
        parts.append(f'如果你今天只想先判断一篇值不值得继续跟进，优先从 {title} 开始。')

    if classics:
        classic = classics[0]
        title = str(classic.get('title') or 'Untitled Paper')
        parts.append(f'经典补课位是 {title}，主要用来补路线背景，不需要放到今天的优先阅读队列最前面。')

    if not primary and classics:
        parts.append('今天的新论文候选偏弱，因此结果以经典补课为主。')

    return ' '.join(parts)


def author_text(paper: Dict[str, Any]) -> str:
    authors = paper.get('authors', [])
    if isinstance(authors, list):
        return ', '.join(authors)
    return str(authors or 'Unknown')


def bullet_section(lines: List[str], title: str, items: List[str], limit: int | None = None) -> None:
    cleaned: List[str] = []
    for item in items:
        raw = clean_render_text(item)
        if not raw:
            continue
        pieces = [raw]
        for pattern in (r"'\s*,\s*'", r'"\s*,\s*"', r'`\s*,\s*`'):
            next_pieces: List[str] = []
            for piece in pieces:
                next_pieces.extend(part for part in re.split(pattern, piece) if part)
            pieces = next_pieces
        cleaned.extend(
            text for piece in pieces
            if (text := clean_render_text(piece))
        )
    if limit is not None:
        cleaned = cleaned[:limit]
    if not cleaned:
        return
    lines.extend(['', f'## {title}'])
    lines.extend(f'- {item}' for item in cleaned)


def inline_bullets(prefix: str, items: List[str], limit: int | None = None) -> List[str]:
    cleaned: List[str] = []
    for item in items:
        raw = clean_render_text(item)
        if not raw:
            continue
        pieces = [raw]
        for pattern in (r"'\s*,\s*'", r'"\s*,\s*"', r'`\s*,\s*`'):
            next_pieces: List[str] = []
            for piece in pieces:
                next_pieces.extend(part for part in re.split(pattern, piece) if part)
            pieces = next_pieces
        cleaned.extend(
            text for piece in pieces
            if (text := clean_render_text(piece))
        )
    if limit is not None:
        cleaned = cleaned[:limit]
    return [f'- {prefix}: {item}' for item in cleaned]


def load_config(repo_root: Path, config_path: str | None) -> Dict[str, Any]:
    candidates: List[Path] = []
    if config_path:
        explicit = Path(config_path)
        if not explicit.is_absolute():
            explicit = repo_root / explicit
        candidates.append(explicit)
    candidates.extend([repo_root / 'config.yaml', repo_root / 'config.example.yaml'])

    for path in candidates:
        if path.exists():
            return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    return {}


def asset_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = config.get('assets', {}) if isinstance(config, dict) else {}
    return {
        'enabled': bool(raw.get('enabled', True)),
        'auto_extract_top_n': max(0, int(raw.get('auto_extract_top_n', 3))),
        'max_images_per_paper': max(0, int(raw.get('max_images_per_paper', 5))),
        'refresh_existing': bool(raw.get('refresh_existing', False)),
        'graph_enabled': bool(raw.get('graph_enabled', True)),
        'max_graph_related': max(0, int(raw.get('max_graph_related', 3))),
    }


def publish_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = config.get('publish', {}) if isinstance(config, dict) else {}
    if not isinstance(raw, dict):
        raw = {}
    return {
        'link_keywords_to_notes': bool(raw.get('link_keywords_to_notes', False)),
    }


def history_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = config.get('search', {}).get('history', {}) if isinstance(config, dict) else {}
    if not isinstance(raw, dict):
        raw = {}
    return {
        'index_path': str(raw.get('index_path') or 'state/paper_index.json').strip() or 'state/paper_index.json',
        'recommended_cooldown_days': max(0, int(raw.get('recommended_cooldown_days', 60))),
        'classic_recommended_cooldown_days': max(0, int(raw.get('classic_recommended_cooldown_days', 21))),
    }


def paper_index_path(repo_root: Path, config: Dict[str, Any]) -> Path:
    path = Path(history_settings(config)['index_path'])
    if not path.is_absolute():
        path = repo_root / path
    return path


def load_paper_index(path: Path) -> Dict[str, Any]:
    payload = {'last_updated': '', 'papers': []}
    if not path.exists():
        return payload
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return payload
    papers = data.get('papers', [])
    if not isinstance(papers, list):
        papers = []
    return {
        'last_updated': str(data.get('last_updated') or ''),
        'papers': [item for item in papers if isinstance(item, dict)],
    }


def update_paper_index(repo_root: Path, config: Dict[str, Any], papers: List[Dict[str, Any]], report_date: str) -> None:
    path = paper_index_path(repo_root, config)
    settings = history_settings(config)
    payload = load_paper_index(path)
    existing = {
        normalize_paper_id(item.get('paper_id') or '') or normalize_title_key(str(item.get('title') or '')): item
        for item in payload['papers']
    }
    report_dt = datetime.strptime(report_date, '%Y-%m-%d')

    for paper in papers:
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('paper_id') or '')
        key = paper_id or normalize_title_key(str(paper.get('title') or ''))
        if not key:
            continue
        item = existing.get(key, {})
        item['paper_id'] = paper_id
        item['title'] = str(paper.get('title') or item.get('title') or '').strip()
        item['domain'] = str(paper.get('matched_domain') or item.get('domain') or '').strip()
        item['published'] = str(paper.get('published') or paper.get('publicationDate') or item.get('published') or '').strip()
        item['source_lane'] = str(paper.get('selection_lane') or item.get('source_lane') or '').strip()
        item['topics'] = normalize_string_list(
            ai_fields(paper).get('keywords') or paper.get('matched_keywords') or item.get('topics') or [],
            limit=12,
        )
        item.pop('analysis_priority_rank', None)
        item.pop('selected_for_full_analysis', None)
        item.pop('last_analysis_date', None)
        item.pop('analyzed_count', None)
        item['reading_status'] = str(item.get('reading_status') or 'unread')
        item['first_seen_date'] = str(item.get('first_seen_date') or report_date)
        item['last_seen_date'] = report_date
        item['last_recommended_date'] = report_date
        item['recommended_count'] = int(item.get('recommended_count', 0)) + 1

        scores_history = item.get('scores_history', [])
        if not isinstance(scores_history, list):
            scores_history = []
        scores_history.append({
            'date': report_date,
            'recommendation': float(paper.get('scores', {}).get('recommendation', 0) or 0),
            'lane': item['source_lane'],
        })
        item['scores_history'] = scores_history[-12:]

        recommended_cooldown_days = settings['recommended_cooldown_days']
        if item['source_lane'] == 'classic':
            recommended_cooldown_days = settings['classic_recommended_cooldown_days']
        cooldown = report_dt + timedelta(days=recommended_cooldown_days)
        item['cooldown_until'] = cooldown.strftime('%Y-%m-%d')
        existing[key] = item

    updated_papers = sorted(existing.values(), key=lambda item: str(item.get('title') or '').lower())
    write_json(path, {
        'last_updated': report_date,
        'papers': updated_papers,
    })


def paper_keyword_set(paper: Dict[str, Any]) -> set[str]:
    ai = ai_fields(paper)
    keywords = ai.get('keywords') or paper.get('matched_keywords') or []
    return {str(item).strip().lower() for item in keywords if str(item).strip()}


def related_paper_ids(current_paper: Dict[str, Any], papers: List[Dict[str, Any]], limit: int) -> List[str]:
    current_id = normalize_paper_id(current_paper.get('arxiv_id') or current_paper.get('arxivId') or current_paper.get('id', ''))
    current_domain = str(current_paper.get('matched_domain') or '').strip()
    current_keywords = paper_keyword_set(current_paper)
    scored: List[tuple[int, float, str]] = []

    for other in papers:
        other_id = normalize_paper_id(other.get('arxiv_id') or other.get('arxivId') or other.get('id', ''))
        if not other_id or other_id == current_id:
            continue
        score = 0
        if current_domain and other.get('matched_domain') == current_domain:
            score += 2
        score += len(current_keywords & paper_keyword_set(other))
        if score <= 0:
            continue
        scored.append((score, float(other.get('scores', {}).get('recommendation', 0) or 0), other_id))

    scored.sort(reverse=True)
    return [paper_id for _, _, paper_id in scored[:limit]]


def rich_asset_enabled(paper: Dict[str, Any], settings: Dict[str, Any], fallback_rank: int) -> bool:
    if not settings['enabled']:
        return False
    return fallback_rank <= settings['auto_extract_top_n']


def normalize_graph_edge_type(value: str) -> str:
    text = str(value or '').strip().lower()
    if any(token in text for token in ['improve', 'improves', 'better', 'beats', '超越', '改进']):
        return 'improves'
    if any(token in text for token in ['extend', 'extends', 'builds on', 'based on', '扩展', '建立在']):
        return 'extends'
    if any(token in text for token in ['follow', 'follows', 'same line', '后续', '沿着', '下游', '衔接', '相邻环节']):
        return 'follows'
    if any(token in text for token in ['compare', 'compares', 'vs', '对比', '比较', '互补', '同属', '不同', '区别']):
        return 'compares'
    return 'related'


def maybe_copy_legacy_assets(repo_root: Path, asset_dir: Path, paper: Dict[str, Any]) -> bool:
    image_dir = asset_dir / 'images'
    existing_images = [
        path for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ] if image_dir.exists() else []
    if existing_images:
        return True

    legacy_dir = legacy_paper_note_dir(repo_root, paper) / 'images'
    if not legacy_dir.exists():
        return False

    image_dir.mkdir(parents=True, exist_ok=True)
    copied = False
    for path in legacy_dir.iterdir():
        if not path.is_file():
            continue
        target = image_dir / path.name
        shutil.copy2(path, target)
        copied = True
    return copied


def maybe_extract_images(repo_root: Path, asset_dir: Path, paper: Dict[str, Any], settings: Dict[str, Any], rank: int) -> None:
    if not rich_asset_enabled(paper, settings, rank):
        return

    image_dir = asset_dir / 'images'
    index_path = image_dir / 'index.md'
    existing_images = [
        path for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ] if image_dir.exists() else []
    if existing_images and index_path.exists() and not settings['refresh_existing']:
        return
    if maybe_copy_legacy_assets(repo_root, asset_dir, paper) and not settings['refresh_existing']:
        return

    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
    if not paper_id:
        return
    source_url = clean_render_text(paper.get('source_url') or paper.get('url') or '')
    if not looks_like_arxiv_id(paper_id) and 'arxiv.org' not in source_url:
        return

    image_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(EXTRACT_IMAGES_SCRIPT),
        paper_id,
        str(image_dir),
        str(index_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        extracted_files = [
            path for path in image_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ]
        if extracted_files:
            logger.info('Extracted %d paper assets for %s', len(extracted_files), paper_id)
        else:
            logger.warning('Image extraction completed for %s but no image files were found', paper_id)
    except subprocess.CalledProcessError as exc:
        logger.warning('Image extraction failed for %s: %s', paper_id, exc.stderr.strip() or exc.stdout.strip() or exc)


def image_markdown_lines(asset_dir: Path, max_images: int) -> List[str]:
    image_dir = asset_dir / 'images'
    if not image_dir.exists() or max_images <= 0:
        return []

    image_files = [
        path for path in sorted(image_dir.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ][:max_images]

    lines: List[str] = []
    for path in image_files:
        lines.extend([f'![{path.stem}](images/{path.name})', ''])
    return lines


def available_image_files(asset_dir: Path) -> List[Path]:
    image_dir = asset_dir / 'images'
    if not image_dir.exists():
        return []
    return [
        path for path in sorted(image_dir.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]


def classify_figure_role(text: str) -> str:
    value = str(text or '').lower()
    if any(token in value for token in ['result', 'performance', 'benchmark', 'evaluation', 'experiment', 'ablation', 'tsne', 'accuracy', 'comparison', 'analysis', 'latency', 'memory', 'throughput', 'ppl', 'perplexity', 'roc-auc', 'auc', 'score']):
        return 'results'
    if any(token in value for token in ['framework', 'pipeline', 'overview', 'architecture', 'method', 'model', 'system', 'illustration', 'scheme', 'parameterization', 'router']):
        return 'method'
    if any(token in value for token in ['dataset', 'example', 'case', 'visual', 'qualitative']):
        return 'examples'
    return 'other'


def figure_priority(entry: Dict[str, Any], target: str) -> int:
    text = f"{entry['path'].stem} {entry.get('caption', '')}".lower()
    if target == 'method':
        score = 0
        if any(token in text for token in ['overview', 'framework', 'pipeline', 'architecture', 'illustration', 'scheme', 'parameterization', 'router', 'workflow']):
            score += 5
        if any(token in text for token in ['method', 'model', 'approach', 'alignment']):
            score += 3
        if any(token in text for token in ['latency', 'memory', 'throughput', 'perplexity', 'roc-auc', 'auc', 'tsne', 'result', 'evaluation', 'benchmark']):
            score -= 3
        return score
    if target == 'results':
        score = 0
        if any(token in text for token in ['result', 'evaluation', 'benchmark', 'latency', 'memory', 'throughput', 'perplexity', 'roc-auc', 'auc', 'accuracy', 'tsne', 'comparison', 'analysis', 'score']):
            score += 5
        if any(token in text for token in ['overview', 'framework', 'pipeline', 'architecture', 'illustration', 'scheme']):
            score -= 2
        return score
    if target == 'examples':
        return 2 if any(token in text for token in ['visual', 'example', 'dataset', 'qualitative', 'case']) else 0
    return 0


def resolve_image_file(image_files: List[Path], token: str) -> Path | None:
    normalized = normalize_image_token(token)
    if not normalized:
        return None
    scored: List[tuple[int, Path]] = []
    for path in image_files:
        candidate = normalize_image_token(path.name)
        if not candidate:
            continue
        if candidate == normalized:
            scored.append((3, path))
        elif candidate.startswith(normalized) or normalized.startswith(candidate):
            scored.append((2, path))
        elif normalized in candidate or candidate in normalized:
            scored.append((1, path))
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1].name))
    return scored[0][1]


def contextual_figure_entries(repo_root: Path, asset_dir: Path, paper: Dict[str, Any], max_images: int) -> List[Dict[str, Any]]:
    image_files = available_image_files(asset_dir)
    if not image_files:
        return []
    limit = max_images if max_images > 0 else None

    entries: List[Dict[str, Any]] = []
    used_paths: set[str] = set()
    fallback_files = image_files[:limit] if limit else image_files
    for path in fallback_files:
        entries.append({
            'path': path,
            'url': relative_asset_url(path, repo_root),
            'caption': '',
            'role': classify_figure_role(path.stem),
        })
    return entries


def pick_figure(entries: List[Dict[str, Any]], preferred_roles: List[str], used: set[str]) -> Dict[str, Any] | None:
    for role in preferred_roles:
        candidates = [
            entry for entry in entries
            if str(entry['path']) not in used and entry.get('role') == role
        ]
        if candidates:
            candidates.sort(key=lambda entry: (-figure_priority(entry, role), entry['path'].name))
            used.add(str(candidates[0]['path']))
            return candidates[0]
    return None


def figure_block(title: str, entry: Dict[str, Any]) -> List[str]:
    path = entry['path']
    lines = ['', f'### {title}', f'![{path.stem}]({entry["url"]})', '']
    caption = str(entry.get('caption') or '').strip()
    if caption:
        lines.append(f'*Figure cue:* {caption}')
    return lines


def table_block(title: str, entry: Dict[str, Any]) -> List[str]:
    lines = ['', f'### {title}']
    caption = clean_render_text(entry.get('caption') or '')
    if caption:
        lines.extend([f'*Table cue:* {caption}', ''])
    rows = entry.get('rows', [])
    if isinstance(rows, list) and rows:
        lines.append('```text')
        for row in rows[:8]:
            text = clean_render_text(row)
            if text:
                lines.append(text)
        lines.append('```')
    elif caption:
        lines.append('提取到了表格标题，但未稳定抽出可直接展示的行内容。')
    return lines


def classify_table_role(entry: Dict[str, Any]) -> str:
    role = clean_render_text(entry.get('role_hint') or '').lower()
    if role in {'method', 'results', 'examples'}:
        return role
    text = ' '.join(
        [
            clean_render_text(entry.get('caption') or ''),
            *[
                clean_render_text(item)
                for item in entry.get('rows', [])[:3]
                if clean_render_text(item)
            ],
        ]
    ).lower()
    if any(token in text for token in ['compile', 'implementation', 'compiler', 'kernel', 'cute', 'dsl', 'latency breakdown']):
        return 'method'
    if any(token in text for token in ['speedup', 'throughput', 'latency', 'accuracy', 'result', 'benchmark', 'memory', 'tflops', 'utilization']):
        return 'results'
    return 'other'


def table_priority(entry: Dict[str, Any], target: str) -> int:
    text = ' '.join(
        [
            clean_render_text(entry.get('caption') or ''),
            *[
                clean_render_text(item)
                for item in entry.get('rows', [])[:3]
                if clean_render_text(item)
            ],
        ]
    ).lower()
    if target == 'method':
        score = 0
        if any(token in text for token in ['compile', 'implementation', 'cute', 'dsl', 'kernel', 'algorithm', 'pipeline']):
            score += 5
        if any(token in text for token in ['speedup', 'throughput', 'latency', 'accuracy']):
            score -= 2
        return score
    if target == 'results':
        score = 0
        if any(token in text for token in ['speedup', 'throughput', 'latency', 'accuracy', 'memory', 'benchmark', 'tflops', 'utilization']):
            score += 5
        if any(token in text for token in ['compile', 'implementation', 'cute', 'dsl']):
            score -= 1
        return score
    return 0


def pick_table(entries: List[Dict[str, Any]], preferred_roles: List[str], used: set[int]) -> Dict[str, Any] | None:
    indexed_entries = list(enumerate(entries))
    for role in preferred_roles:
        candidates = [
            (index, entry)
            for index, entry in indexed_entries
            if index not in used and classify_table_role(entry) == role
        ]
        if candidates:
            candidates.sort(key=lambda item: (-table_priority(item[1], role), item[0]))
            used.add(candidates[0][0])
            return candidates[0][1]
    return None


def daily_feature_figure(repo_root: Path, asset_dir: Path, paper: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, str]:
    entries = contextual_figure_entries(repo_root, asset_dir, paper, settings['max_images_per_paper'])
    used: set[str] = set()
    preferred = (
        pick_figure(entries, ['results', 'method', 'examples', 'other'], used)
        or (entries[0] if entries else None)
    )
    if not preferred:
        return {}
    return {
        'url': str(preferred.get('url') or relative_asset_url(preferred['path'], repo_root)),
        'caption': str(preferred.get('caption') or '').strip(),
        'alt': preferred['path'].stem,
        'role': str(preferred.get('role') or 'other'),
    }


def daily_feature_table(paper: Dict[str, Any]) -> Dict[str, Any]:
    entries = paper.get('daily_tables')
    if not entries:
        return {}
    if not isinstance(entries, list):
        return {}
    used: set[int] = set()
    preferred = (
        pick_table(entries, ['results', 'method', 'other'], used)
        or entries[0]
    )
    rows = preferred.get('rows', [])
    if not isinstance(rows, list):
        rows = []
    return {
        'caption': clean_render_text(preferred.get('caption') or ''),
        'rows': [clean_render_text(row) for row in rows[:4] if clean_render_text(row)],
        'role': classify_table_role(preferred),
    }


def maybe_update_graph(repo_root: Path, paper: Dict[str, Any], papers: List[Dict[str, Any]], settings: Dict[str, Any]) -> None:
    if not settings['graph_enabled']:
        return

    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
    if not paper_id:
        return

    cmd = [
        sys.executable,
        str(UPDATE_GRAPH_SCRIPT),
        '--repo-root', str(repo_root),
        '--paper-id', paper_id,
        '--title', str(paper.get('title') or 'Untitled Paper'),
        '--domain', str(paper.get('matched_domain') or 'Uncategorized'),
        '--score', str(float(paper.get('scores', {}).get('recommendation', 0) or 0)),
    ]
    related = related_paper_ids(paper, papers, settings['max_graph_related'])
    if related:
        cmd.extend(['--related', *related])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.warning('Graph update failed for %s: %s', paper_id, exc.stderr.strip() or exc.stdout.strip() or exc)


def paper_storage_slug(paper: Dict[str, Any]) -> str:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
    title = str(paper.get('title') or 'Untitled Paper').strip()
    return paper_slug(paper_id, title)


def legacy_paper_note_dir(repo_root: Path, paper: Dict[str, Any]) -> Path:
    return get_papers_root(repo_root) / paper_storage_slug(paper)


def paper_asset_dir(repo_root: Path, paper: Dict[str, Any]) -> Path:
    return get_paper_assets_root(repo_root) / paper_storage_slug(paper)

def collect_daily_publication_meta(
    repo_root: Path,
    paper: Dict[str, Any],
    papers: List[Dict[str, Any]],
    settings: Dict[str, Any],
    rank: int,
) -> Dict[str, str]:
    asset_dir = paper_asset_dir(repo_root, paper)
    maybe_extract_images(repo_root, asset_dir, paper, settings, rank)
    maybe_update_graph(repo_root, paper, papers, settings)

    enable_rich_assets = rich_asset_enabled(paper, settings, rank)
    daily_figure = daily_feature_figure(repo_root, asset_dir, paper, settings) if enable_rich_assets else {}
    daily_table = daily_feature_table(paper)
    result: Dict[str, str] = {}
    if daily_figure.get('url'):
        result['daily_figure_url'] = daily_figure['url']
    if daily_figure.get('caption'):
        result['daily_figure_caption'] = daily_figure['caption']
    if daily_figure.get('alt'):
        result['daily_figure_alt'] = daily_figure['alt']
    if daily_figure.get('role'):
        result['daily_figure_role'] = daily_figure['role']
    if daily_table.get('caption'):
        result['daily_table_caption'] = daily_table['caption']
    if daily_table.get('rows'):
        result['daily_table_rows'] = daily_table['rows']
    if daily_table.get('role'):
        result['daily_table_role'] = daily_table['role']
    return result


def fallback_overview(papers: List[Dict[str, Any]]) -> str:
    domains = Counter(p.get('matched_domain', 'Uncategorized') for p in papers)
    scores = [p.get('scores', {}).get('recommendation', 0) for p in papers]
    leading_domains = ', '.join(f"{domain} x{count}" for domain, count in domains.most_common(3)) or 'No dominant domain'
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    return (
        f'Today surfaces {len(papers)} papers. The strongest clusters are {leading_domains}. '
        f'Recommendation scores range from {min_score:.2f} to {max_score:.2f}. Start with the top two papers if you only have limited time.'
    )


def build_reading_strategy(papers: List[Dict[str, Any]], paper_meta_map: Dict[str, Dict[str, str]]) -> List[str]:
    if not papers:
        return []

    primary, classics = split_daily_papers(papers)
    lead = lead_paper(papers)
    steps: List[str] = []

    def paper_link(paper: Dict[str, Any]) -> str:
        return str(paper.get('title') or 'Untitled Paper')

    if lead:
        steps.append(f'先看 {paper_link(lead)}，它最适合作为今天的起始判断样本。')

    follow_up = [
        paper for paper in primary
        if normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        != normalize_paper_id((lead or {}).get('arxiv_id') or (lead or {}).get('arxivId') or (lead or {}).get('id', ''))
    ]
    if follow_up:
        titles = '、'.join(paper_link(paper) for paper in follow_up[:2])
        steps.append(f'再浏览 {titles}，判断它们是值得继续跟进的 systems 机会，还是只停留在局部优化。')

    if classics:
        steps.append(f'最后把 {paper_link(classics[0])} 当成经典补课位，重点补路线背景，不需要和今天的新论文争夺第一阅读顺位。')

    return steps[:3]


def recommendation_score(paper: Dict[str, Any]) -> float:
    return float(paper.get('scores', {}).get('recommendation', 0) or 0)


def short_paper_title(paper: Dict[str, Any]) -> str:
    return clean_render_text(paper.get('title') or 'Untitled Paper')


def build_ordering_rationale(papers: List[Dict[str, Any]]) -> List[str]:
    primary, classics = split_daily_papers(papers)
    if not primary:
        return []

    lead = ordered_primary_papers(papers)[0]
    lead_title = short_paper_title(lead)
    lead_recommendation = recommendation_score(lead)

    highest_recommendation_paper = max(primary, key=recommendation_score)
    highest_recommendation_title = short_paper_title(highest_recommendation_paper)
    highest_recommendation = recommendation_score(highest_recommendation_paper)

    lines = [
        f'- 主推位先放 {lead_title}。这里优先看它是否最适合作为今天最先判断的一篇，同时兼顾推荐分和方向贴合度；它当前的推荐分是 {lead_recommendation:.2f}。'
    ]

    if normalize_paper_id(lead.get('arxiv_id') or lead.get('arxivId') or lead.get('id', '')) != normalize_paper_id(highest_recommendation_paper.get('arxiv_id') or highest_recommendation_paper.get('arxivId') or highest_recommendation_paper.get('id', '')):
        lines.append(
            f'- 推荐分最高的是 {highest_recommendation_title}（{highest_recommendation:.2f}），但它被放在继续跟进位，因为首页第一位更强调“今天最值得先判断哪一篇”，不是机械按分数排第一。'
        )
    else:
        lines.append(f'- 其余新论文按推荐分和 lane 顺序继续往后排，所以主推位同时也是今天分数最高、最值得先读的条目。')

    if len(primary) > 1:
        lines.append('- 继续跟进位仍然按 fresh / established 的主线优先级和推荐分排序，目的是先保证方向贴合，再保证强弱顺序。')
    if classics:
        lines.append('- 经典补课位单独放在最后，不和今天的新论文争夺注意力。')
    return lines


def daily_mix_lines(papers: List[Dict[str, Any]]) -> List[str]:
    counts = Counter(selection_lane(paper) for paper in papers)
    lines: List[str] = []
    if counts.get('fresh'):
        lines.append(f'- 新论文主线: {counts["fresh"]} 篇')
    if counts.get('established'):
        lines.append(f'- 已验证论文: {counts["established"]} 篇')
    if counts.get('classic'):
        lines.append(f'- 经典补课位: {counts["classic"]} 篇')
    return lines


def compressed_author_text(paper: Dict[str, Any], limit: int = 4) -> str:
    authors = paper.get('authors', [])
    if not isinstance(authors, list) or not authors:
        text = author_text(paper)
        return clean_render_text(text)
    cleaned = [clean_render_text(item) for item in authors if clean_render_text(item)]
    if len(cleaned) <= limit:
        return ', '.join(cleaned)
    return ', '.join(cleaned[:limit]) + ' et al.'


def daily_visual_reason(paper_meta: Dict[str, Any]) -> str:
    role = clean_render_text(paper_meta.get('daily_figure_role') or paper_meta.get('daily_table_role')).lower()
    if role == 'results':
        return '这张图或表对应最直接的结果证据，先看它能最快判断收益是不是值得追。'
    if role == 'method':
        return '这张图或表主要用来解释方法机制，先看它能更快理解这篇论文到底改了哪一层系统路径。'
    if role == 'examples':
        return '这张图主要帮助你快速判断方法在具体样例里的行为是否可信。'
    return '这里保留的视觉线索只服务正文判断，不是资产展示。'


def render_daily_asset(lines: List[str], paper_meta: Dict[str, Any], title: str) -> None:
    figure_url = paper_meta.get('daily_figure_url')
    if figure_url:
        lines.extend([
            '',
            f'![{paper_meta.get("daily_figure_alt", title)}]({figure_url})',
            '',
        ])
        if paper_meta.get('daily_figure_caption'):
            lines.append(f'*图示线索：* {paper_meta["daily_figure_caption"]}')
        lines.append(f'*为什么放这张图：* {daily_visual_reason(paper_meta)}')
        return

    rows = paper_meta.get('daily_table_rows')
    if isinstance(rows, list) and rows:
        lines.extend(['', '```text'])
        for row in rows[:4]:
            text = clean_render_text(row)
            if text:
                lines.append(text)
        lines.append('```')
        if paper_meta.get('daily_table_caption'):
            lines.append(f'*表格线索：* {paper_meta["daily_table_caption"]}')
        lines.append(f'*为什么放这张表：* {daily_visual_reason(paper_meta)}')


def daily_reading_judgment_text(paper: Dict[str, Any]) -> str:
    value_text = daily_value_text(paper)
    risk_text = daily_risk_text(paper)
    if value_text and risk_text:
        return f'{value_text} 但要先核对：{risk_text}'
    return value_text or risk_text


def render_daily_paper_entry(
    lines: List[str],
    paper: Dict[str, Any],
    paper_meta_map: Dict[str, Dict[str, str]],
    index_label: str,
    is_classic_section: bool = False,
    role: str = 'supporting',
) -> None:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
    title = paper.get('title', 'Untitled Paper')
    paper_meta = paper_meta_map.get(paper_id, {})
    abs_url, pdf_url = paper_urls(paper_id, paper)
    ai = ai_fields(paper)
    score = paper.get('scores', {}).get('recommendation', 'N/A')
    institutions = paper_institutions(paper)
    source_label = daily_source_label(paper)
    heading_prefix = '主推' if role == 'lead' else index_label
    heading = f'### {heading_prefix}. {title}' if heading_prefix else f'### {title}'
    published = clean_render_text(paper.get('published', paper.get('publicationDate', 'Unknown')))
    priority = reading_priority_label(str(ai.get('reading_priority', 'medium')))
    meta_bits = [
        lane_label(paper),
        f'推荐分 {score}',
        priority,
        source_label,
        published,
        compressed_author_text(paper),
    ]

    lines.extend([
        '',
        heading,
        '',
        f'*{" | ".join(bit for bit in meta_bits if bit)}*',
        '',
        f'> {summarize_paper(paper)}',
    ])

    analysis_text = compact_analysis_text(paper)
    if analysis_text:
        lines.extend(['', analysis_text])

    if paper_meta:
        render_daily_asset(lines, paper_meta, title)

    judgment_text = compact_evaluation_text(paper)
    if judgment_text:
        lines.extend(['', f'**评估：** {judgment_text}'])

    link_parts = [f'[Source]({abs_url})']
    if pdf_url:
        link_parts.append(f'[PDF]({pdf_url})')
    else:
        link_parts.append('PDF unavailable')
    context_line = [
        source_label,
        ', '.join(institutions) if institutions else '',
        published,
    ]
    lines.extend(['', f'**来源与上下文：** {" · ".join(part for part in context_line if part)}'])
    lines.append(f'**链接：** {" | ".join(link_parts)}')

    if role == 'lead':
        lines.append('**阅读建议：** 如果时间有限，先从这篇开始。')
    elif is_classic_section:
        lines.append('**阅读建议：** 这篇更适合作为补路线背景的经典阅读，不需要和今天的新论文争夺最前面的阅读顺位。')


def build_daily_body(
    report_date: str,
    payload: Dict[str, Any],
    papers: List[Dict[str, Any]],
    paper_meta_map: Dict[str, Dict[str, str]],
) -> str:
    primary_papers = ordered_primary_papers(papers)
    classic_papers = [paper for paper in papers if selection_lane(paper) == 'classic']
    lines = [
        f'# Daily Paper Report - {report_date}',
        '',
        '## 今日概览',
        build_overview(papers, paper_meta_map),
    ]

    strategy = build_reading_strategy(papers, paper_meta_map)
    if strategy:
        lines.extend(['', '## 今日阅读顺序'])
        lines.extend(f'- {item}' for item in strategy)

    mix_lines = daily_mix_lines(papers)
    if mix_lines:
        lines.extend(['', '## 今日选择结构'])
        lines.extend(mix_lines)

    ordering_lines = build_ordering_rationale(papers)
    if ordering_lines:
        lines.extend(['', '## 排序说明'])
        lines.extend(ordering_lines)

    if primary_papers:
        lines.extend(['', '## 今日主推'])
        render_daily_paper_entry(lines, primary_papers[0], paper_meta_map, '', role='lead')
        supporting = primary_papers[1:]
        if supporting:
            lines.extend(['', '## 继续跟进'])
            for index, paper in enumerate(supporting, start=1):
                if index > 1:
                    lines.extend(['', '---'])
                render_daily_paper_entry(lines, paper, paper_meta_map, str(index), role='supporting')

    if classic_papers:
        title = '## 经典补课'
        lines.extend(['', title])
        for index, paper in enumerate(classic_papers, start=1):
            if index > 1:
                lines.extend(['', '---'])
            render_daily_paper_entry(lines, paper, paper_meta_map, '', is_classic_section=True, role='classic')

    return '\n'.join(lines) + '\n'


def daily_keywords(papers: List[Dict[str, Any]]) -> List[str]:
    counts: Counter[str] = Counter()
    for paper in papers:
        ai = ai_fields(paper)
        raw_keywords = ai.get('keywords') or paper.get('matched_keywords') or []
        if not isinstance(raw_keywords, list):
            continue
        for keyword in raw_keywords:
            text = str(keyword).strip()
            if text:
                counts[text] += 1
    return [keyword for keyword, _ in counts.most_common(12)]


def rebuild_indexes(repo_root: Path, latest_entry: Dict[str, Any]) -> None:
    meta_root = get_meta_root(repo_root)
    daily_root = get_daily_root(repo_root)
    entries: List[Dict[str, Any]] = []
    for path in sorted(daily_root.glob('*.md'), reverse=True):
        date_str = path.stem
        entries.append({
            'date': date_str,
            'path': f'/daily/{date_str}/',
            'source_path': path.relative_to(repo_root).as_posix(),
        })

    write_json(meta_root / 'daily-index.json', entries)
    write_json(meta_root / 'latest.json', latest_entry)


def run_linking(repo_root: Path, daily_path: Path) -> None:
    index_path = repo_root / 'state' / 'existing_notes_index.json'
    linked_path = daily_path.with_suffix('.linked.md')

    subprocess.run([sys.executable, str(SCAN_SCRIPT), '--repo-root', str(repo_root), '--output', str(index_path)], check=True)
    subprocess.run([
        sys.executable,
        str(LINK_SCRIPT),
        '--index', str(index_path),
        '--input', str(daily_path),
        '--output', str(linked_path),
    ], check=True)
    linked_path.replace(daily_path)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Publish a daily report into content/')
    parser.add_argument('--input', required=True, help='Path to search or enriched JSON output')
    parser.add_argument('--config', default=None, help='Config YAML path')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    config = load_config(repo_root, args.config)
    settings = asset_settings(config)
    publication = publish_settings(config)
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    report_date = payload.get('target_date') or datetime.now().strftime('%Y-%m-%d')
    papers = payload.get('top_papers', [])

    paper_page_meta: Dict[str, Dict[str, str]] = {}
    for rank, paper in enumerate(papers, start=1):
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
        paper_page_meta[paper_id] = collect_daily_publication_meta(repo_root, paper, papers, settings, rank)

    daily_path = get_daily_root(repo_root) / f'{report_date}.md'
    frontmatter = {
        'title': f'Daily Paper Report - {report_date}',
        'date': report_date,
        'paper_count': len(papers),
        'tags': ['daily-report'],
    }
    keywords = daily_keywords(papers)
    if keywords:
        frontmatter['keywords'] = keywords
    enrichment_meta = payload.get('ai_enrichment', {}) if isinstance(payload.get('ai_enrichment'), dict) else {}
    if 'enabled' in enrichment_meta:
        frontmatter['ai_enriched'] = bool(enrichment_meta.get('enabled'))
    if enrichment_meta.get('model'):
        frontmatter['ai_model'] = enrichment_meta.get('model')

    body = build_daily_body(report_date, payload, papers, paper_page_meta)
    write_markdown(daily_path, frontmatter, body)
    if publication['link_keywords_to_notes']:
        run_linking(repo_root, daily_path)

    latest_entry = {
        'date': report_date,
        'path': f'/daily/{report_date}/',
        'source_path': daily_path.relative_to(repo_root).as_posix(),
        'paper_count': len(papers),
    }
    rebuild_indexes(repo_root, latest_entry)
    update_paper_index(repo_root, config, papers, report_date)
    print(daily_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
