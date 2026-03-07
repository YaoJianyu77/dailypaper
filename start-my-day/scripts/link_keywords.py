#!/usr/bin/env python3
"""Replace plain keywords with standard Markdown links to existing paper pages."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from common_words import COMMON_WORDS

logger = logging.getLogger(__name__)


def parse_markdown_lines(content: str) -> List[Tuple[str, str]]:
    lines: List[Tuple[str, str]] = []
    in_code_block = False
    in_frontmatter = False
    frontmatter_seen = 0

    for line in content.split('\n'):
        if line.strip() == '---':
            frontmatter_seen += 1
            in_frontmatter = frontmatter_seen == 1
            if frontmatter_seen == 2:
                in_frontmatter = False
            lines.append((line, 'frontmatter'))
            continue

        if in_frontmatter:
            lines.append((line, 'frontmatter'))
            continue

        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            lines.append((line, 'code'))
            continue

        if in_code_block:
            lines.append((line, 'code'))
            continue

        if line.strip().startswith('#'):
            lines.append((line, 'heading'))
            continue

        if re.search(r'!\[.*?\]\(.*?\)', line):
            lines.append((line, 'image'))
            continue

        if re.search(r'\[.*?\]\(.*?\)', line):
            lines.append((line, 'link'))
            continue

        if '`' in line:
            lines.append((line, 'inline_code'))
            continue

        lines.append((line, 'normal'))

    return lines


def link_keywords_in_text(text: str, keyword_index: Dict[str, List[str]]) -> str:
    filtered = {
        keyword: urls
        for keyword, urls in keyword_index.items()
        if keyword.lower() not in COMMON_WORDS and 3 <= len(keyword) <= 50 and not keyword.isdigit() and urls
    }

    segments = re.split(r'(\[.*?\]\(.*?\))', text)

    for index, segment in enumerate(segments):
        if index % 2 == 1:
            continue
        updated = segment
        for keyword in sorted(filtered.keys(), key=len, reverse=True):
            url = filtered[keyword][0]
            pattern = r'(?<![A-Za-z0-9_\-/])' + re.escape(keyword) + r'(?![A-Za-z0-9_\-/])'
            updated = re.sub(pattern, lambda m: f'[{m.group(0)}]({url})', updated, flags=re.IGNORECASE)
        segments[index] = updated

    return ''.join(segments)


def link_keywords_in_file(input_file: Path, output_file: Path, keyword_index: Dict[str, List[str]]) -> None:
    content = input_file.read_text(encoding='utf-8')
    lines = parse_markdown_lines(content)
    output_lines: List[str] = []

    for line, line_type in lines:
        if line_type == 'normal':
            output_lines.append(link_keywords_in_text(line, keyword_index))
        else:
            output_lines.append(line)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('\n'.join(output_lines), encoding='utf-8')


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Link keywords with Markdown links')
    parser.add_argument('--index', required=True, help='Keyword index JSON file')
    parser.add_argument('--input', required=True, help='Input markdown file')
    parser.add_argument('--output', required=True, help='Output markdown file')
    args = parser.parse_args()

    index_path = Path(args.index)
    input_path = Path(args.input)
    output_path = Path(args.output)

    index_data = json.loads(index_path.read_text(encoding='utf-8'))
    keyword_index = index_data.get('keyword_to_notes', {})
    link_keywords_in_file(input_path, output_path, keyword_index)

    logger.info('Linked keywords from %s -> %s', input_path, output_path)
    print(output_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
