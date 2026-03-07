#!/usr/bin/env python3
"""Publish a daily report and paper pages into the repository content store."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

from content_store import (
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


def normalize_paper_id(raw: str) -> str:
    return str(raw or '').replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '').replace('arXiv:', '').strip()


def paper_urls(paper_id: str) -> tuple[str, str]:
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


def analysis_value(full: Dict[str, Any], ai: Dict[str, Any], full_key: str, ai_key: str | None = None) -> Any:
    value = full.get(full_key)
    if value:
        return value
    if ai_key:
        return ai.get(ai_key)
    return None


def author_text(paper: Dict[str, Any]) -> str:
    authors = paper.get('authors', [])
    if isinstance(authors, list):
        return ', '.join(authors)
    return str(authors or 'Unknown')


def bullet_section(lines: List[str], title: str, items: List[str], limit: int | None = None) -> None:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if limit is not None:
        cleaned = cleaned[:limit]
    if not cleaned:
        return
    lines.extend(['', f'## {title}'])
    lines.extend(f'- {item}' for item in cleaned)


def inline_bullets(prefix: str, items: List[str], limit: int | None = None) -> List[str]:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
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


def maybe_extract_images(repo_root: Path, note_dir: Path, paper: Dict[str, Any], settings: Dict[str, Any], rank: int) -> None:
    if not settings['enabled'] or rank > settings['auto_extract_top_n']:
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


def ensure_paper_page(repo_root: Path, paper: Dict[str, Any], papers: List[Dict[str, Any]], settings: Dict[str, Any], rank: int) -> str:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
    title = paper.get('title', 'Untitled Paper').strip()
    slug = paper_slug(paper_id, title)
    note_path = get_papers_root(repo_root) / slug / 'index.md'
    source_url, pdf_url = paper_urls(paper_id)
    ai = ai_fields(paper)
    full = full_analysis_fields(paper)
    note_dir = note_path.parent

    maybe_extract_images(repo_root, note_dir, paper, settings, rank)
    maybe_update_graph(repo_root, paper, papers, settings)

    embedded_images = image_markdown_lines(note_dir, settings['max_images_per_paper'])

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
    if ai.get('keywords'):
        frontmatter['keywords'] = ai.get('keywords', [])
    if ai.get('reading_priority'):
        frontmatter['reading_priority'] = ai.get('reading_priority')
    if embedded_images:
        frontmatter['image_count'] = len(embedded_images) // 2
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
        f'- Domain: {paper.get("matched_domain", "Uncategorized")}',
        f'- Published: {paper.get("published", paper.get("publicationDate", "Unknown"))}',
        f'- arXiv: [abstract]({source_url})',
        f'- PDF: [download]({pdf_url})',
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
    bullet_section(body_lines, 'Method Details', full.get('method_details', []), limit=5)
    if analysis_value(full, ai, 'experiment_setup_zh', 'evidence_zh'):
        body_lines.extend([
            '',
            '## Experimental Setup And Evidence',
            analysis_value(full, ai, 'experiment_setup_zh', 'evidence_zh'),
        ])
    if full.get('main_results_zh'):
        body_lines.extend([
            '',
            '## Main Results And Claims',
            full.get('main_results_zh', ''),
        ])
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
    bullet_section(body_lines, 'Strengths', full.get('strengths', []), limit=4)
    bullet_section(body_lines, 'Future Work', full.get('future_work', []), limit=4)
    bullet_section(body_lines, 'Reading Checklist', full.get('reading_checklist', []) or ai.get('open_questions', []), limit=4)

    bullet_section(body_lines, 'Core Contributions', ai.get('core_contributions', []), limit=3)
    bullet_section(body_lines, 'Why Read It', ai.get('why_read', []), limit=3)
    bullet_section(body_lines, 'Risks Or Limits', full.get('limitations', []) or ai.get('risks', []), limit=4)
    bullet_section(body_lines, 'Recommended For', ai.get('recommended_for', []), limit=3)
    bullet_section(body_lines, 'Keywords', ai.get('keywords', []), limit=6)

    if embedded_images:
        body_lines.extend(['', '## Figures'])
        body_lines.extend(embedded_images)
        body_lines.append('- Full asset manifest: [images/index.md](images/index.md)')

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
    ])

    images_index = note_dir / 'images' / 'index.md'
    if images_index.exists():
        body_lines.extend([
            '',
            '## Assets',
            '- Extracted assets are stored in the `images/` folder next to this page.',
            '- Browse the image manifest here: [images/index.md](images/index.md)',
        ])

    write_markdown(note_path, frontmatter, '\n'.join(body_lines) + '\n')
    return relative_site_url(note_path, repo_root)


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


def build_overview(payload: Dict[str, Any], papers: List[Dict[str, Any]]) -> str:
    daily_brief = payload.get('daily_brief', {}) if isinstance(payload.get('daily_brief'), dict) else {}
    return daily_brief.get('overview_zh') or fallback_overview(papers)


def build_daily_body(report_date: str, payload: Dict[str, Any], papers: List[Dict[str, Any]], paper_urls_map: Dict[str, str]) -> str:
    daily_brief = payload.get('daily_brief', {}) if isinstance(payload.get('daily_brief'), dict) else {}
    lines = [
        f'# Daily Paper Report - {report_date}',
        '',
        '## Overview',
        build_overview(payload, papers),
    ]

    top_themes = daily_brief.get('top_themes', [])
    reading_strategy = daily_brief.get('reading_strategy', [])
    if top_themes:
        lines.extend(['', '## Top Themes'])
        lines.extend(f'- {theme}' for theme in top_themes[:3])
    if reading_strategy:
        lines.extend(['', '## Reading Strategy'])
        lines.extend(f'- {step}' for step in reading_strategy[:3])

    lines.extend(['', '## Recommended Papers'])

    for index, paper in enumerate(papers, start=1):
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
        title = paper.get('title', 'Untitled Paper')
        url = paper_urls_map[paper_id]
        abs_url, pdf_url = paper_urls(paper_id)
        ai = ai_fields(paper)
        score = paper.get('scores', {}).get('recommendation', 'N/A')
        lines.extend([
            '',
            f'### {index}. [{title}]({url})',
            f'- Score: **{score}**',
            f'- Domain: {paper.get("matched_domain", "Uncategorized")}',
            f'- Reading priority: {ai.get("reading_priority", "medium")}',
            f'- Authors: {author_text(paper) or "Unknown"}',
            f'- Published: {paper.get("published", paper.get("publicationDate", "Unknown"))}',
            f'- Links: [arXiv]({abs_url}) | [PDF]({pdf_url})',
            f'- One-line view: {summarize_paper(paper)}',
        ])
        if ai.get('reading_priority_reason'):
            lines.append(f'- Why now: {ai.get("reading_priority_reason")}')
        lines.extend(inline_bullets('Core contribution', ai.get('core_contributions', []), limit=3))
        lines.extend(inline_bullets('Why read', ai.get('why_read', []), limit=3))
        lines.extend(inline_bullets('Risk', ai.get('risks', []), limit=2))
        recommended_for = ai.get('recommended_for', [])
        if recommended_for:
            lines.append(f'- Recommended for: {", ".join(recommended_for[:3])}')

    return '\n'.join(lines) + '\n'


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

    paper_page_urls: Dict[str, str] = {}
    for rank, paper in enumerate(papers, start=1):
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
        paper_page_urls[paper_id] = ensure_paper_page(repo_root, paper, papers, settings, rank)

    daily_path = get_daily_root(repo_root) / f'{report_date}.md'
    frontmatter = {
        'title': f'Daily Paper Report - {report_date}',
        'date': report_date,
        'paper_count': len(papers),
        'tags': ['daily-report'],
    }
    enrichment_meta = payload.get('ai_enrichment', {}) if isinstance(payload.get('ai_enrichment'), dict) else {}
    if 'enabled' in enrichment_meta:
        frontmatter['ai_enriched'] = bool(enrichment_meta.get('enabled'))
    if enrichment_meta.get('model'):
        frontmatter['ai_model'] = enrichment_meta.get('model')

    body = build_daily_body(report_date, payload, papers, paper_page_urls)
    write_markdown(daily_path, frontmatter, body)
    run_linking(repo_root, daily_path)

    latest_entry = {
        'date': report_date,
        'path': f'/daily/{report_date}/',
        'source_path': daily_path.relative_to(repo_root).as_posix(),
        'paper_count': len(papers),
    }
    rebuild_indexes(repo_root, latest_entry)
    print(daily_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
