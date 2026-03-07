#!/usr/bin/env python3
"""Scan repository paper notes and build a keyword-to-URL index."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml

from content_store import get_papers_root, get_repo_root, iter_markdown_files, load_markdown, relative_site_url, write_json
from common_words import COMMON_WORDS

logger = logging.getLogger(__name__)


def extract_keywords_from_title(title: str) -> List[str]:
    if not title:
        return []

    keywords: List[str] = []
    acronym = re.match(r'^([A-Z]{2,})(?:\s*:|\s+)', title)
    if acronym:
        keywords.append(acronym.group(1))

    before_colon = title.split(':', 1)[0].strip()
    if 3 <= len(before_colon) <= 48:
        keywords.append(before_colon)

    for term in re.findall(r'\b[A-Z][A-Za-z0-9]+(?:-[A-Z][A-Za-z0-9]+)+\b', title):
        if term.lower() not in COMMON_WORDS:
            keywords.append(term)

    return list(dict.fromkeys(keywords))


def normalize_tags(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: List[str] = []
        for item in value:
            if isinstance(item, str):
                result.append(item)
        return result
    return []


def scan_notes(repo_root: Path) -> List[Dict]:
    notes: List[Dict] = []
    papers_root = get_papers_root(repo_root)

    for md_file in iter_markdown_files(papers_root):
        frontmatter, _ = load_markdown(md_file)
        title = frontmatter.get('title', md_file.parent.name)
        tags = normalize_tags(frontmatter.get('tags', []))
        slug = frontmatter.get('slug', md_file.parent.name)
        notes.append({
            'title': title,
            'slug': slug,
            'source_path': md_file.relative_to(repo_root).as_posix(),
            'url': relative_site_url(md_file, repo_root),
            'title_keywords': extract_keywords_from_title(title),
            'tag_keywords': [tag for tag in tags if 3 <= len(tag) <= 30 and tag.lower() not in COMMON_WORDS],
        })

    return notes


def build_keyword_index(notes: List[Dict]) -> Dict[str, List[str]]:
    keyword_index: Dict[str, List[str]] = {}

    for note in notes:
        candidates = list(note['title_keywords']) + list(note['tag_keywords']) + [note['slug']]
        for keyword in candidates:
            normalized = keyword.lower().strip()
            if not normalized or normalized in COMMON_WORDS:
                continue
            if len(normalized) < 3 or len(normalized) > 50:
                continue
            keyword_index.setdefault(normalized, [])
            if note['url'] not in keyword_index[normalized]:
                keyword_index[normalized].append(note['url'])

    return keyword_index


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Scan repository paper notes and build keyword index')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    parser.add_argument('--output', default='state/existing_notes_index.json', help='Output JSON path')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    notes = scan_notes(repo_root)
    keyword_index = build_keyword_index(notes)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    write_json(output_path, {
        'notes': notes,
        'keyword_to_notes': keyword_index,
    })

    logger.info('Indexed %d notes and %d keywords', len(notes), len(keyword_index))
    print(output_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
