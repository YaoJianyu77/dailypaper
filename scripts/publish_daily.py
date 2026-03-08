#!/usr/bin/env python3
"""Publish a daily report and paper pages into the repository content store."""

from __future__ import annotations

import argparse
import json
import logging
import re
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
    get_papers_root,
    get_repo_root,
    paper_slug,
    relative_site_url,
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


def full_analysis_fields(paper: Dict[str, Any]) -> Dict[str, Any]:
    raw = paper.get('full_analysis', {})
    if not isinstance(raw, dict) or not raw.get('enabled'):
        return {}
    content = raw.get('content', {})
    return content if isinstance(content, dict) else {}


def full_analysis_metadata(paper: Dict[str, Any]) -> Dict[str, Any]:
    raw = paper.get('full_analysis', {})
    if not isinstance(raw, dict) or not raw.get('enabled'):
        return {}
    metadata = raw.get('metadata', {})
    return metadata if isinstance(metadata, dict) else {}


def full_analysis_figure_context(paper: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = paper.get('full_analysis', {})
    if not isinstance(raw, dict) or not raw.get('enabled'):
        return []
    context = raw.get('figure_context', [])
    if not isinstance(context, list):
        return []
    return [item for item in context if isinstance(item, dict)]


def full_analysis_table_context(paper: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = paper.get('full_analysis', {})
    if not isinstance(raw, dict) or not raw.get('enabled'):
        return []
    context = raw.get('table_context', [])
    if not isinstance(context, list):
        return []
    return [item for item in context if isinstance(item, dict)]


def full_analysis_score_card(paper: Dict[str, Any]) -> Dict[str, int]:
    full = full_analysis_fields(paper)
    card = full.get('score_card', {})
    if not isinstance(card, dict):
        return {}
    result: Dict[str, int] = {}
    for key in ['innovation', 'technical_quality', 'experimental_rigor', 'writing_clarity', 'practical_value']:
        value = card.get(key)
        if isinstance(value, int):
            result[key] = max(1, min(10, value))
    return result


def full_analysis_related_work(paper: Dict[str, Any]) -> List[Dict[str, str]]:
    full = full_analysis_fields(paper)
    value = full.get('related_work_comparisons', [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def clean_render_text(value: Any) -> str:
    text = str(value or '').replace('\r', ' ').replace('\n', ' ').replace('\u200b', ' ').strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*(?:\?{2,}|`{2,}|"{2,}|\'{2,})\s*$', '', text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"', '`'}:
        text = text[1:-1].strip()
    return text.strip(' ,;:|')


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

    metadata = full_analysis_metadata(paper)
    return normalize_string_list(metadata.get('institutions'), limit=8, cleaner=clean_institution_name)


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
        return 'Classic systems paper'
    if source == 'arxiv_hot_fallback':
        return 'arXiv hot-window candidate'
    if source == 'semantic_scholar':
        return 'Semantic Scholar hot-paper search'
    return 'arXiv preprint'


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


def split_daily_papers(papers: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    primary = [paper for paper in papers if selection_lane(paper) != 'classic']
    classics = [paper for paper in papers if selection_lane(paper) == 'classic']
    return primary, classics


def deep_dive_paper(papers: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    candidates = [paper for paper in papers if selected_for_full_analysis(paper)]
    if not candidates:
        return papers[0] if papers else None
    return min(
        candidates,
        key=lambda paper: (
            analysis_priority_rank(paper, 9999),
            -float(paper.get('analysis_candidate_score', 0) or 0),
            -float(paper.get('scores', {}).get('recommendation', 0) or 0),
        ),
    )


def ordered_primary_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    primary, _ = split_daily_papers(papers)
    if not primary:
        return []

    deep_dive = deep_dive_paper(primary)
    remaining = [
        paper for paper in primary
        if normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        != normalize_paper_id((deep_dive or {}).get('arxiv_id') or (deep_dive or {}).get('arxivId') or (deep_dive or {}).get('id', ''))
    ]
    lane_rank = {'fresh': 0, 'established': 1, 'classic': 2}
    remaining.sort(
        key=lambda paper: (
            lane_rank.get(selection_lane(paper), 9),
            -float(paper.get('scores', {}).get('recommendation', 0) or 0),
            -float(paper.get('analysis_candidate_score', 0) or 0),
            str(paper.get('title') or '').lower(),
        )
    )
    return ([deep_dive] if deep_dive else []) + remaining


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
    deep_dive = deep_dive_paper(papers)
    parts: List[str] = []

    if themes:
        parts.append(f'今天主线集中在{"、".join(themes)}。')

    mix: List[str] = []
    if lane_counts.get('fresh'):
        mix.append(f'{lane_counts["fresh"]} 篇 fresh systems 论文')
    if lane_counts.get('established'):
        mix.append(f'{lane_counts["established"]} 篇 established 论文')
    if classics:
        mix.append(f'{len(classics)} 篇 classic 补课论文')
    if mix:
        parts.append(f'本轮实际保留了{"、".join(mix)}，没有为凑数强行补满。')

    if deep_dive:
        paper_id = normalize_paper_id(deep_dive.get('arxiv_id') or deep_dive.get('arxivId') or deep_dive.get('id', ''))
        page_url = paper_meta_map.get(paper_id, {}).get('page_url')
        title = str(deep_dive.get('title') or 'Untitled Paper')
        if page_url:
            parts.append(f'今天唯一的 full analysis 给到 [{title}]({page_url})。')
        else:
            parts.append(f'今天唯一的 full analysis 给到 {title}。')

    if classics:
        classic = classics[0]
        paper_id = normalize_paper_id(classic.get('arxiv_id') or classic.get('arxivId') or classic.get('id', ''))
        page_url = paper_meta_map.get(paper_id, {}).get('page_url')
        title = str(classic.get('title') or 'Untitled Paper')
        if page_url:
            parts.append(f'经典补课位是 [{title}]({page_url})，默认只做阅读调度，不占用今日 deep-dive 名额。')
        else:
            parts.append(f'经典补课位是 {title}，默认只做阅读调度，不占用今日 deep-dive 名额。')

    if not primary and classics:
        parts.append('今天的新论文候选偏弱，因此结果以经典补课为主。')

    return ' '.join(parts)


def analysis_value(full: Dict[str, Any], ai: Dict[str, Any], full_key: str, ai_key: str | None = None) -> Any:
    value = full.get(full_key)
    if value:
        return value
    if ai_key:
        return ai.get(ai_key)
    return None


def paper_url_by_id(repo_root: Path, papers: List[Dict[str, Any]], paper_id: str, fallback_title: str = '') -> str | None:
    normalized = normalize_paper_id(paper_id)
    if not normalized:
        return None
    for paper in papers:
        current_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        if current_id == normalized:
            slug = paper_slug(current_id, str(paper.get('title') or fallback_title or 'paper'))
            path = get_papers_root(repo_root) / slug / 'index.md'
            return relative_site_url(path, repo_root)
    if fallback_title:
        path = get_papers_root(repo_root) / paper_slug(normalized, fallback_title) / 'index.md'
        if path.exists():
            return relative_site_url(path, repo_root)
    return None


def scorecard_lines(score_card: Dict[str, int]) -> List[str]:
    if not score_card:
        return []
    labels = {
        'innovation': 'Innovation',
        'technical_quality': 'Technical Quality',
        'experimental_rigor': 'Experimental Rigor',
        'writing_clarity': 'Writing Clarity',
        'practical_value': 'Practical Value',
    }
    avg = round(sum(score_card.values()) / len(score_card), 1)
    lines = [
        '',
        '## Scorecard',
        f'- Overall: {avg}/10',
    ]
    for key in ['innovation', 'technical_quality', 'experimental_rigor', 'writing_clarity', 'practical_value']:
        if key in score_card:
            lines.append(f'- {labels[key]}: {score_card[key]}/10')
    return lines


def related_work_lines(repo_root: Path, papers: List[Dict[str, Any]], comparisons: List[Dict[str, str]]) -> List[str]:
    if not comparisons:
        return []
    lines = ['', '## Related Paper Comparisons']
    for item in comparisons[:3]:
        paper_id = normalize_paper_id(item.get('paper_id') or '')
        title = clean_render_text(item.get('title') or paper_id or 'Related paper')
        relation = clean_render_text(item.get('relation') or 'related')
        comparison = clean_render_text(item.get('comparison_zh') or '')
        url = paper_url_by_id(repo_root, papers, paper_id, title)
        if url:
            lines.append(f'- [{title}]({url}) ({relation}): {comparison}')
        else:
            lines.append(f'- {title} ({relation}): {comparison}')
    return lines


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


def history_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = config.get('search', {}).get('history', {}) if isinstance(config, dict) else {}
    if not isinstance(raw, dict):
        raw = {}
    return {
        'index_path': str(raw.get('index_path') or 'state/paper_index.json').strip() or 'state/paper_index.json',
        'recommended_cooldown_days': max(0, int(raw.get('recommended_cooldown_days', 60))),
        'classic_recommended_cooldown_days': max(0, int(raw.get('classic_recommended_cooldown_days', 21))),
        'analyzed_cooldown_days': max(0, int(raw.get('analyzed_cooldown_days', 365))),
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
        item['analysis_priority_rank'] = analysis_priority_rank(paper)
        item['selected_for_full_analysis'] = bool(paper.get('selected_for_full_analysis'))
        item['topics'] = normalize_string_list(
            ai_fields(paper).get('keywords') or paper.get('matched_keywords') or item.get('topics') or [],
            limit=12,
        )
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
            'analysis_candidate': float(paper.get('analysis_candidate_score', 0) or 0),
            'lane': item['source_lane'],
        })
        item['scores_history'] = scores_history[-12:]

        full_analysis = paper.get('full_analysis', {})
        if isinstance(full_analysis, dict) and full_analysis.get('enabled'):
            item['last_analysis_date'] = report_date
            item['analyzed_count'] = int(item.get('analyzed_count', 0)) + 1
            cooldown = report_dt + timedelta(days=settings['analyzed_cooldown_days'])
        else:
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


def analysis_priority_rank(paper: Dict[str, Any], fallback_rank: int = 0) -> int:
    try:
        rank = int(paper.get('analysis_priority_rank', 0) or 0)
    except (TypeError, ValueError):
        rank = 0
    return rank if rank > 0 else fallback_rank


def selected_for_full_analysis(paper: Dict[str, Any], fallback_rank: int = 0) -> bool:
    if bool(paper.get('selected_for_full_analysis')):
        return True
    rank = analysis_priority_rank(paper, fallback_rank)
    return bool(rank and rank <= 1)


def rich_asset_enabled(paper: Dict[str, Any], settings: Dict[str, Any], fallback_rank: int) -> bool:
    if not settings['enabled']:
        return False
    return analysis_priority_rank(paper, fallback_rank) <= settings['auto_extract_top_n']


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


def maybe_extract_images(repo_root: Path, note_dir: Path, paper: Dict[str, Any], settings: Dict[str, Any], rank: int) -> None:
    if not rich_asset_enabled(paper, settings, rank):
        return

    image_dir = note_dir / 'images'
    index_path = image_dir / 'index.md'
    existing_images = [
        path for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ] if image_dir.exists() else []
    if existing_images and index_path.exists() and not settings['refresh_existing']:
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


def image_markdown_lines(note_dir: Path, max_images: int) -> List[str]:
    image_dir = note_dir / 'images'
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


def available_image_files(note_dir: Path) -> List[Path]:
    image_dir = note_dir / 'images'
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


def contextual_figure_entries(note_dir: Path, paper: Dict[str, Any], max_images: int) -> List[Dict[str, Any]]:
    image_files = available_image_files(note_dir)
    if not image_files:
        return []
    limit = max_images if max_images > 0 else None

    entries: List[Dict[str, Any]] = []
    used_paths: set[str] = set()
    for item in full_analysis_figure_context(paper):
        image_path = resolve_image_file(image_files, item.get('image_token') or item.get('image_ref') or '')
        if not image_path or str(image_path) in used_paths:
            continue
        used_paths.add(str(image_path))
        caption = str(item.get('caption') or '').strip()
        inferred_role = classify_figure_role(f'{caption} {image_path.stem}')
        role = inferred_role if inferred_role != 'other' else str(item.get('role_hint') or '').strip() or 'other'
        entries.append({
            'path': image_path,
            'caption': caption,
            'role': role,
        })

    if entries:
        for path in image_files:
            if str(path) in used_paths:
                continue
            entries.append({
                'path': path,
                'caption': '',
                'role': classify_figure_role(path.stem),
            })
        return entries[:limit] if limit else entries

    fallback_files = image_files[:limit] if limit else image_files
    for path in fallback_files:
        entries.append({
            'path': path,
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
    lines = ['', f'### {title}', f'![{path.stem}](images/{path.name})', '']
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


def daily_feature_figure(repo_root: Path, note_dir: Path, paper: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, str]:
    entries = contextual_figure_entries(note_dir, paper, settings['max_images_per_paper'])
    used: set[str] = set()
    preferred = (
        pick_figure(entries, ['results', 'method', 'examples', 'other'], used)
        or (entries[0] if entries else None)
    )
    if not preferred:
        return {}
    return {
        'url': relative_asset_url(preferred['path'], repo_root),
        'caption': str(preferred.get('caption') or '').strip(),
        'alt': preferred['path'].stem,
    }


def daily_feature_table(paper: Dict[str, Any]) -> Dict[str, Any]:
    entries = full_analysis_table_context(paper)
    if not entries:
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
    semantic_targets = {
        normalize_paper_id(item.get('paper_id') or '')
        for item in full_analysis_related_work(paper)
        if normalize_paper_id(item.get('paper_id') or '')
    }
    related = [
        item for item in related_paper_ids(paper, papers, settings['max_graph_related'])
        if item not in semantic_targets
    ]
    if related:
        cmd.extend(['--related', *related])
    for item in full_analysis_related_work(paper):
        target_id = normalize_paper_id(item.get('paper_id') or '')
        if not target_id:
            continue
        edge_type = normalize_graph_edge_type(item.get('relation') or '')
        weight = 0.8 if edge_type in {'improves', 'extends'} else 0.7
        cmd.extend(['--related-spec', f'{target_id}|{edge_type}|{weight}'])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.warning('Graph update failed for %s: %s', paper_id, exc.stderr.strip() or exc.stdout.strip() or exc)


def ensure_paper_page(repo_root: Path, paper: Dict[str, Any], papers: List[Dict[str, Any]], settings: Dict[str, Any], rank: int) -> Dict[str, str]:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
    title = paper.get('title', 'Untitled Paper').strip()
    slug = paper_slug(paper_id, title)
    note_path = get_papers_root(repo_root) / slug / 'index.md'
    source_url, pdf_url = paper_urls(paper_id, paper)
    ai = ai_fields(paper)
    full = full_analysis_fields(paper)
    institutions = paper_institutions(paper)
    venue_or_journal = paper_venue_or_journal(paper)
    citation_summary = paper_citation_summary(paper)
    note_dir = note_path.parent

    maybe_extract_images(repo_root, note_dir, paper, settings, rank)
    maybe_update_graph(repo_root, paper, papers, settings)

    enable_rich_assets = rich_asset_enabled(paper, settings, rank)
    figure_entries = contextual_figure_entries(note_dir, paper, settings['max_images_per_paper']) if enable_rich_assets else []
    table_entries = full_analysis_table_context(paper)[:3]
    used_figure_paths: set[str] = set()
    used_table_indexes: set[int] = set()
    method_figure = pick_figure(figure_entries, ['method', 'other', 'examples'], used_figure_paths)
    results_figure = pick_figure(figure_entries, ['results', 'examples', 'other'], used_figure_paths)
    analysis_figure = pick_figure(figure_entries, ['results', 'examples', 'other'], used_figure_paths)
    method_table = pick_table(table_entries, ['method', 'other'], used_table_indexes) if table_entries else None
    results_table = pick_table(table_entries, ['results', 'other'], used_table_indexes) if table_entries else None
    remaining_figures = [
        entry for entry in figure_entries
        if str(entry['path']) not in used_figure_paths
    ]
    daily_figure = daily_feature_figure(repo_root, note_dir, paper, settings) if enable_rich_assets else {}
    daily_table = daily_feature_table(paper) if full else {}

    frontmatter = {
        'paper_id': paper_id,
        'title': title,
        'authors': paper.get('authors', []) if isinstance(paper.get('authors', []), list) else [author_text(paper)],
        'domain': paper.get('matched_domain', 'Uncategorized'),
        'slug': slug,
        'published': paper.get('published', paper.get('publicationDate', '')),
        'summary': summarize_paper(paper),
        'source_url': source_url,
        'pdf_url': pdf_url,
        'scores': paper.get('scores', {}),
        'tags': ['paper-note'],
        'status': 'generated',
        'updated': datetime.now().strftime('%Y-%m-%d'),
    }
    if institutions:
        frontmatter['institutions'] = institutions
    if venue_or_journal:
        frontmatter['venue_or_journal'] = venue_or_journal
    frontmatter['citation_summary'] = citation_summary
    if ai.get('keywords'):
        frontmatter['keywords'] = ai.get('keywords', [])
    if ai.get('reading_priority'):
        frontmatter['reading_priority'] = ai.get('reading_priority')
    frontmatter['analysis_priority_rank'] = analysis_priority_rank(paper, rank)
    frontmatter['selected_for_full_analysis'] = selected_for_full_analysis(paper, rank)
    if figure_entries:
        frontmatter['image_count'] = len(figure_entries)
    if table_entries:
        frontmatter['table_count'] = len(table_entries)
    if full:
        frontmatter['analysis_depth'] = 'full'
        frontmatter['full_analysis_source'] = str(paper.get('full_analysis', {}).get('source_kind') or '')

    body_lines = [
        f'# {title}',
        '',
        '## TL;DR',
        summarize_paper(paper),
        '',
        '## 中文摘要',
        detail_summary(paper),
        '',
        '## Quick Facts',
        f'- Paper ID: `{paper_id}`',
        f'- Authors: {author_text(paper) or "Unknown"}',
        f'- Institutions: {", ".join(institutions) if institutions else "Institution information not extracted"}',
        f'- Domain: {paper.get("matched_domain", "Uncategorized")}',
        f'- Venue / Journal: {venue_or_journal}',
        f'- Citations: {citation_summary}',
        f'- Published: {paper.get("published", paper.get("publicationDate", "Unknown"))}',
        f'- Source page: [open]({source_url})',
        f'- PDF: [download]({pdf_url})' if pdf_url else '- PDF: not found from current source metadata',
        f'- Reading priority: {ai.get("reading_priority", "medium")}',
    ]

    if ai.get('reading_priority_reason'):
        body_lines.append(f'- Why this priority: {ai.get("reading_priority_reason")}')

    if full.get('abstract_translation_zh'):
        body_lines.extend([
            '',
            '## Abstract Translation',
            full.get('abstract_translation_zh', ''),
        ])
    if analysis_value(full, ai, 'background_zh', 'background_zh'):
        body_lines.extend([
            '',
            '## Research Background And Motivation',
            analysis_value(full, ai, 'background_zh', 'background_zh'),
        ])
    if analysis_value(full, ai, 'problem_zh', 'problem_zh'):
        body_lines.extend([
            '',
            '## Problem Framing',
            analysis_value(full, ai, 'problem_zh', 'problem_zh'),
        ])
    if analysis_value(full, ai, 'method_overview_zh', 'approach_zh'):
        body_lines.extend([
            '',
            '## Method Overview',
            analysis_value(full, ai, 'method_overview_zh', 'approach_zh'),
        ])
        if method_figure:
            body_lines.extend(figure_block('Method Figure', method_figure))
        if method_table:
            body_lines.extend(table_block('Implementation Table', method_table))
    bullet_section(body_lines, 'Method Details', full.get('method_details', []), limit=5)
    if analysis_value(full, ai, 'experiment_setup_zh', 'evidence_zh'):
        body_lines.extend([
            '',
            '## Experimental Setup And Evidence',
            analysis_value(full, ai, 'experiment_setup_zh', 'evidence_zh'),
        ])
        if results_figure:
            body_lines.extend(figure_block('Experiment Figure', results_figure))
        if results_table:
            body_lines.extend(table_block('Evidence Table', results_table))
    bullet_section(body_lines, 'Datasets And Benchmarks', full.get('datasets_or_benchmarks', []), limit=6)
    bullet_section(body_lines, 'Baselines', full.get('baselines', []), limit=6)
    bullet_section(body_lines, 'Metrics', full.get('metrics', []), limit=6)
    bullet_section(body_lines, 'Ablations And Analysis', full.get('ablation_or_analysis', []), limit=4)
    if analysis_figure:
        body_lines.extend(figure_block('Analysis Figure', analysis_figure))
    bullet_section(body_lines, 'Evaluation Validity And Fairness', full.get('evaluation_validity', []), limit=4)
    if full.get('main_results_zh'):
        body_lines.extend([
            '',
            '## Main Results And Claims',
            full.get('main_results_zh', ''),
        ])
        if results_figure and '### Experiment Figure' not in body_lines:
            body_lines.extend(figure_block('Results Figure', results_figure))
    if analysis_value(full, ai, 'practical_value_zh', 'value_zh'):
        body_lines.extend([
            '',
            '## Research Or Engineering Value',
            analysis_value(full, ai, 'practical_value_zh', 'value_zh'),
        ])
    if full.get('relation_to_prior_work_zh'):
        body_lines.extend([
            '',
            '## Relation To Prior Work',
            full.get('relation_to_prior_work_zh', ''),
        ])
    if full.get('overall_assessment_zh'):
        body_lines.extend([
            '',
            '## Overall Assessment',
            full.get('overall_assessment_zh', ''),
        ])
    if full.get('technical_route_zh'):
        body_lines.extend([
            '',
            '## Technical Route Positioning',
            full.get('technical_route_zh', ''),
        ])
    body_lines.extend(scorecard_lines(full_analysis_score_card(paper)))
    body_lines.extend(related_work_lines(repo_root, papers, full_analysis_related_work(paper)))
    bullet_section(body_lines, 'Strengths', full.get('strengths', []), limit=4)
    bullet_section(body_lines, 'Future Work', full.get('future_work', []), limit=4)
    bullet_section(body_lines, 'Reading Checklist', full.get('reading_checklist', []) or ai.get('open_questions', []), limit=4)

    bullet_section(body_lines, 'Core Contributions', ai.get('core_contributions', []), limit=3)
    bullet_section(body_lines, 'Why Read It', ai.get('why_read', []), limit=3)
    bullet_section(body_lines, 'Risks Or Limits', full.get('limitations', []) or ai.get('risks', []), limit=4)
    bullet_section(body_lines, 'Recommended For', ai.get('recommended_for', []), limit=3)
    bullet_section(body_lines, 'Keywords', ai.get('keywords', []), limit=6)

    if remaining_figures:
        body_lines.extend([
            '',
            '## Additional Assets',
            '- 其余提取到的 figures 保存在 `images/` 目录，默认不全部展开，避免让页面被资产列表主导。',
            '- Full asset manifest: [images/index.md](images/index.md)',
        ])

    body_lines.extend([
        '',
        '## Abstract',
        (paper.get('summary') or paper.get('abstract') or 'No abstract available.').strip(),
        '',
        '## Recommendation Signals',
        f'- Recommendation score: {paper.get("scores", {}).get("recommendation", "N/A")}',
        f'- Relevance score: {paper.get("scores", {}).get("relevance", "N/A")}',
        f'- Recency score: {paper.get("scores", {}).get("recency", "N/A")}',
        f'- Popularity score: {paper.get("scores", {}).get("popularity", "N/A")}',
        f'- Quality score: {paper.get("scores", {}).get("quality", "N/A")}',
        f'- Analysis candidate score: {paper.get("analysis_candidate_score", "N/A")}',
        f'- Analysis priority rank: {analysis_priority_rank(paper, rank)}',
    ])
    analysis_signals = paper.get('analysis_signals', [])
    if isinstance(analysis_signals, list) and analysis_signals:
        body_lines.append(f'- Analysis signals: {", ".join(str(item) for item in analysis_signals[:8])}')

    images_index = note_dir / 'images' / 'index.md'
    if images_index.exists() and available_image_files(note_dir):
        body_lines.extend([
            '',
            '## Assets',
            '- Extracted assets are stored in the `images/` folder next to this page.',
            '- Browse the image manifest here: [images/index.md](images/index.md)',
        ])

    write_markdown(note_path, frontmatter, '\n'.join(body_lines) + '\n')
    result = {
        'page_url': relative_site_url(note_path, repo_root),
    }
    if daily_figure.get('url'):
        result['daily_figure_url'] = daily_figure['url']
    if daily_figure.get('caption'):
        result['daily_figure_caption'] = daily_figure['caption']
    if daily_figure.get('alt'):
        result['daily_figure_alt'] = daily_figure['alt']
    if daily_table.get('caption'):
        result['daily_table_caption'] = daily_table['caption']
    if daily_table.get('rows'):
        result['daily_table_rows'] = daily_table['rows']
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
    deep_dive = deep_dive_paper(papers)
    steps: List[str] = []

    def paper_link(paper: Dict[str, Any]) -> str:
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        url = paper_meta_map.get(paper_id, {}).get('page_url')
        title = str(paper.get('title') or 'Untitled Paper')
        return f'[{title}]({url})' if url else title

    if deep_dive:
        steps.append(
            f'先精读 {paper_link(deep_dive)}，它是今天 analysis candidate score 最高、最适合做全文核对的一篇。'
        )

    follow_up = [
        paper for paper in primary
        if normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        != normalize_paper_id((deep_dive or {}).get('arxiv_id') or (deep_dive or {}).get('arxivId') or (deep_dive or {}).get('id', ''))
    ]
    if follow_up:
        titles = '、'.join(paper_link(paper) for paper in follow_up[:2])
        steps.append(f'再快速浏览 {titles}，判断它们是 kernel/runtime 机会，还是只停留在局部优化。')

    if classics:
        steps.append(f'最后把 {paper_link(classics[0])} 当成经典补课位，重点补路线背景，不和今日 deep-dive 竞争预算。')

    return steps[:3]


def daily_mix_lines(papers: List[Dict[str, Any]]) -> List[str]:
    counts = Counter(selection_lane(paper) for paper in papers)
    lines: List[str] = []
    if counts.get('fresh'):
        lines.append(f'- Fresh systems papers: {counts["fresh"]}')
    if counts.get('established'):
        lines.append(f'- Established papers: {counts["established"]}')
    if counts.get('classic'):
        lines.append(f'- Classic revisit papers: {counts["classic"]}')
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


def render_daily_asset(lines: List[str], paper_meta: Dict[str, Any], title: str) -> None:
    figure_url = paper_meta.get('daily_figure_url')
    if figure_url:
        lines.extend([
            '',
            f'![{paper_meta.get("daily_figure_alt", title)}]({figure_url})',
            '',
        ])
        if paper_meta.get('daily_figure_caption'):
            lines.append(f'*Visual cue:* {paper_meta["daily_figure_caption"]}')
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
            lines.append(f'*Table cue:* {paper_meta["daily_table_caption"]}')


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
    url = paper_meta.get('page_url', '#')
    abs_url, pdf_url = paper_urls(paper_id, paper)
    ai = ai_fields(paper)
    score = paper.get('scores', {}).get('recommendation', 'N/A')
    institutions = paper_institutions(paper)
    source_label = daily_source_label(paper)
    heading_prefix = 'Lead' if role == 'lead' else index_label
    heading = f'### {heading_prefix}. [{title}]({url})' if heading_prefix else f'### [{title}]({url})'
    published = clean_render_text(paper.get('published', paper.get('publicationDate', 'Unknown')))
    priority = clean_render_text(ai.get('reading_priority', 'medium'))
    meta_bits = [
        lane_label(paper),
        f'score {score}',
        f'{priority} priority',
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
        summarize_paper(paper),
    ])

    summary = detail_summary(paper)
    if summary and summary != summarize_paper(paper):
        lines.extend(['', summary])

    if role == 'lead':
        render_daily_asset(lines, paper_meta, title)

    why_now = clean_render_text(ai.get('reading_priority_reason') or '')
    if why_now:
        lines.extend(['', f'Why it matters today: {why_now}'])

    note_links = [f'[paper page]({url})', f'[Source]({abs_url})']
    if pdf_url:
        note_links.append(f'[PDF]({pdf_url})')
    else:
        note_links.append('PDF unavailable')
    lines.append(f'- Institution: {", ".join(institutions) if institutions else "Institution information not extracted"}')
    lines.append(f'- Source: {source_label}')
    lines.append(f'- Note: {" | ".join(note_links)}')

    why_read = normalize_string_list(ai.get('why_read', []), limit=2)
    if why_read:
        lines.append(f'- Why read: {"；".join(why_read[:2])}')

    risks = normalize_string_list(full_analysis_fields(paper).get('limitations', []) or ai.get('risks', []), limit=2)
    if risks:
        lines.append(f'- What to verify: {"；".join(risks[:2])}')

    if selected_for_full_analysis(paper):
        lines.append("- Reading mode: today's full paper analysis target")
    elif is_classic_section:
        lines.append("- Reading mode: classic background reading slot, not today's deep-dive target")


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
        '## Overview',
        build_overview(papers, paper_meta_map),
    ]

    if primary_papers:
        lines.extend(['', '## Lead Paper'])
        render_daily_paper_entry(lines, primary_papers[0], paper_meta_map, '', role='lead')
        supporting = primary_papers[1:]
        if supporting:
            lines.extend(['', '## Supporting Reads'])
            for index, paper in enumerate(supporting, start=1):
                render_daily_paper_entry(lines, paper, paper_meta_map, str(index), role='supporting')

    if classic_papers:
        title = '## Classic Revisit' if len(classic_papers) == 1 else '## Classic Revisits'
        lines.extend(['', title])
        for paper in classic_papers:
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
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    report_date = payload.get('target_date') or datetime.now().strftime('%Y-%m-%d')
    papers = payload.get('top_papers', [])

    paper_page_meta: Dict[str, Dict[str, str]] = {}
    for rank, paper in enumerate(papers, start=1):
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
        paper_page_meta[paper_id] = ensure_paper_page(repo_root, paper, papers, settings, rank)

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
    note_links = [f'[paper page]({url})', f'[Source]({abs_url})']
    if pdf_url:
        note_links.append(f'[PDF]({pdf_url})')
    else:
        note_links.append('PDF unavailable')
