#!/usr/bin/env python3
"""Publish a daily report and paper pages into the repository content store."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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


def normalize_paper_id(raw: str) -> str:
    return str(raw or '').replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '').replace('arXiv:', '').strip()


def paper_urls(paper_id: str) -> tuple[str, str]:
    pid = normalize_paper_id(paper_id)
    return f'https://arxiv.org/abs/{pid}', f'https://arxiv.org/pdf/{pid}.pdf'


def ai_fields(paper: Dict[str, Any]) -> Dict[str, Any]:
    return paper.get('ai', {}) if isinstance(paper.get('ai'), dict) else {}


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


def ensure_paper_page(repo_root: Path, paper: Dict[str, Any]) -> str:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
    title = paper.get('title', 'Untitled Paper').strip()
    slug = paper_slug(paper_id, title)
    note_path = get_papers_root(repo_root) / slug / 'index.md'
    source_url, pdf_url = paper_urls(paper_id)
    ai = ai_fields(paper)

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

    bullet_section(body_lines, 'Core Contributions', ai.get('core_contributions', []), limit=3)
    bullet_section(body_lines, 'Why Read It', ai.get('why_read', []), limit=3)
    bullet_section(body_lines, 'Risks Or Limits', ai.get('risks', []), limit=2)
    bullet_section(body_lines, 'Recommended For', ai.get('recommended_for', []), limit=3)
    bullet_section(body_lines, 'Keywords', ai.get('keywords', []), limit=6)

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

    images_index = note_path.parent / 'images' / 'index.md'
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
    parser = argparse.ArgumentParser(description='Publish a daily report into content/')
    parser.add_argument('--input', required=True, help='Path to search or enriched JSON output')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    report_date = payload.get('target_date') or datetime.now().strftime('%Y-%m-%d')
    papers = payload.get('top_papers', [])

    paper_page_urls: Dict[str, str] = {}
    for paper in papers:
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
        paper_page_urls[paper_id] = ensure_paper_page(repo_root, paper)

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
