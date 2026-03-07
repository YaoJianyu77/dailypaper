#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate or update a paper note inside the repository content store."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from content_store import get_repo_root, get_papers_root, paper_slug, write_markdown

logger = logging.getLogger(__name__)


def build_note_frontmatter(args: argparse.Namespace, slug: str, date: str) -> dict:
    return {
        "paper_id": args.paper_id,
        "title": args.title,
        "authors": [a.strip() for a in args.authors.split(",") if a.strip()],
        "domain": args.domain,
        "slug": slug,
        "published": args.published,
        "source_url": args.source_url,
        "pdf_url": args.pdf_url,
        "summary": args.summary,
        "tags": ["paper-note"],
        "status": args.status,
        "created": date,
        "updated": date,
    }


def build_note_body(args: argparse.Namespace) -> str:
    abstract_section = args.abstract.strip() if args.abstract else "待补充。"
    summary = args.summary.strip() if args.summary else "待补充。"

    lines = [
        f"# {args.title}",
        "",
        "## Quick Facts",
        f"- Paper ID: `{args.paper_id}`",
        f"- Authors: {args.authors or 'Unknown'}",
        f"- Domain: {args.domain or 'Uncategorized'}",
        f"- Published: {args.published or 'Unknown'}",
        f"- Source: [arXiv abstract]({args.source_url})" if args.source_url else "- Source: N/A",
        f"- PDF: [download]({args.pdf_url})" if args.pdf_url else "- PDF: N/A",
        "",
        "## Summary",
        summary,
        "",
        "## Abstract",
        abstract_section,
        "",
        "## Notes",
        "- This page is generated automatically.",
        "- Add your own commentary here if you want to keep permanent annotations in Git.",
    ]

    if args.images_index:
        lines.extend([
            "",
            "## Assets",
            f"- Image index: [{args.images_index}]({args.images_index})",
        ])

    return "\n".join(lines) + "\n"


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Generate a paper note in content/papers')
    parser.add_argument('--paper-id', required=True, help='Paper identifier, usually arXiv ID')
    parser.add_argument('--title', required=True, help='Paper title')
    parser.add_argument('--authors', default='', help='Comma-separated authors')
    parser.add_argument('--domain', default='Uncategorized', help='Research domain')
    parser.add_argument('--published', default='', help='Publication date')
    parser.add_argument('--summary', default='', help='Short summary')
    parser.add_argument('--abstract', default='', help='Abstract text')
    parser.add_argument('--source-url', default='', help='Canonical abstract URL')
    parser.add_argument('--pdf-url', default='', help='PDF URL')
    parser.add_argument('--images-index', default='images/index.md', help='Relative path to extracted image index')
    parser.add_argument('--status', default='generated', help='Note status')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    papers_root = get_papers_root(repo_root)
    slug = paper_slug(args.paper_id, args.title)
    note_dir = papers_root / slug
    note_path = note_dir / 'index.md'
    date = datetime.now().strftime('%Y-%m-%d')

    frontmatter = build_note_frontmatter(args, slug, date)
    body = build_note_body(args)
    write_markdown(note_path, frontmatter, body)

    logger.info('Paper note written to %s', note_path)
    print(note_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
