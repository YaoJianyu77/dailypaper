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
from typing import Dict, List

from content_store import (
    get_daily_root,
    get_meta_root,
    get_papers_root,
    get_repo_root,
    paper_slug,
    read_json,
    relative_site_url,
    write_json,
    write_markdown,
)


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SCAN_SCRIPT = REPO_ROOT / 'start-my-day' / 'scripts' / 'scan_existing_notes.py'
LINK_SCRIPT = REPO_ROOT / 'start-my-day' / 'scripts' / 'link_keywords.py'


def normalize_paper_id(raw: str) -> str:
    return raw.replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '').replace('arXiv:', '').strip()


def paper_urls(paper_id: str) -> tuple[str, str]:
    pid = normalize_paper_id(paper_id)
    return f'https://arxiv.org/abs/{pid}', f'https://arxiv.org/pdf/{pid}.pdf'


def ensure_paper_page(repo_root: Path, paper: Dict) -> str:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
    title = paper.get('title', 'Untitled Paper').strip()
    slug = paper_slug(paper_id, title)
    note_path = get_papers_root(repo_root) / slug / 'index.md'
    source_url, pdf_url = paper_urls(paper_id)
    authors = paper.get('authors', [])
    if isinstance(authors, list):
        author_text = ', '.join(authors)
    else:
        author_text = str(authors)

    frontmatter = {
        'paper_id': paper_id,
        'title': title,
        'authors': authors if isinstance(authors, list) else [author_text],
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

    body_lines = [
        f"# {title}",
        "",
        "## Summary",
        summarize_paper(paper),
        "",
        "## Quick Facts",
        f"- Paper ID: `{paper_id}`",
        f"- Authors: {author_text or 'Unknown'}",
        f"- Domain: {paper.get('matched_domain', 'Uncategorized')}",
        f"- Published: {paper.get('published', paper.get('publicationDate', 'Unknown'))}",
        f"- arXiv: [abstract]({source_url})",
        f"- PDF: [download]({pdf_url})",
        "",
        "## Abstract",
        paper.get('summary', paper.get('abstract', 'No abstract available.')).strip(),
        "",
        "## Recommendation Signals",
        f"- Recommendation score: {paper.get('scores', {}).get('recommendation', 'N/A')}",
        f"- Relevance score: {paper.get('scores', {}).get('relevance', 'N/A')}",
        f"- Recency score: {paper.get('scores', {}).get('recency', 'N/A')}",
        f"- Popularity score: {paper.get('scores', {}).get('popularity', 'N/A')}",
        f"- Quality score: {paper.get('scores', {}).get('quality', 'N/A')}",
    ]

    images_index = note_path.parent / 'images' / 'index.md'
    if images_index.exists():
        body_lines.extend([
            "",
            "## Assets",
            "- Extracted assets are stored in the `images/` folder next to this page.",
            "- Browse the image manifest here: [images/index.md](images/index.md)",
        ])

    write_markdown(note_path, frontmatter, '\n'.join(body_lines) + '\n')
    return relative_site_url(note_path, repo_root)


def summarize_paper(paper: Dict) -> str:
    abstract = (paper.get('summary') or paper.get('abstract') or '').strip()
    if not abstract:
        return 'No summary available.'
    abstract = abstract.replace('\n', ' ')
    sentence = abstract.split('. ')[0].strip()
    if not sentence.endswith('.'):
        sentence += '.'
    return sentence


def build_overview(papers: List[Dict]) -> str:
    domains = Counter(p.get('matched_domain', 'Uncategorized') for p in papers)
    scores = [p.get('scores', {}).get('recommendation', 0) for p in papers]
    leading_domains = ', '.join(f"{domain} x{count}" for domain, count in domains.most_common(3)) or 'No dominant domain'
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    return (
        f"Today surfaces {len(papers)} papers. The strongest clusters are {leading_domains}. "
        f"Recommendation scores range from {min_score:.2f} to {max_score:.2f}. Start with the top two papers if you only have limited time."
    )


def build_daily_body(report_date: str, papers: List[Dict], paper_urls_map: Dict[str, str]) -> str:
    lines = [
        f"# Daily Paper Report - {report_date}",
        "",
        "## Overview",
        build_overview(papers),
        "",
        "## Recommended Papers",
    ]

    for index, paper in enumerate(papers, start=1):
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', 'unknown'))
        title = paper.get('title', 'Untitled Paper')
        url = paper_urls_map[paper_id]
        abs_url, pdf_url = paper_urls(paper_id)
        authors = paper.get('authors', [])
        author_text = ', '.join(authors) if isinstance(authors, list) else str(authors)
        score = paper.get('scores', {}).get('recommendation', 'N/A')
        lines.extend([
            "",
            f"### {index}. [{title}]({url})",
            f"- Score: **{score}**",
            f"- Domain: {paper.get('matched_domain', 'Uncategorized')}",
            f"- Authors: {author_text or 'Unknown'}",
            f"- Published: {paper.get('published', paper.get('publicationDate', 'Unknown'))}",
            f"- Links: [arXiv]({abs_url}) | [PDF]({pdf_url})",
            f"- Summary: {summarize_paper(paper)}",
        ])

    return '\n'.join(lines) + '\n'


def rebuild_indexes(repo_root: Path, latest_entry: Dict) -> None:
    meta_root = get_meta_root(repo_root)
    daily_root = get_daily_root(repo_root)
    entries: List[Dict] = []
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
    parser.add_argument('--input', required=True, help='Path to search_arxiv.py JSON output')
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
    body = build_daily_body(report_date, papers, paper_page_urls)
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
