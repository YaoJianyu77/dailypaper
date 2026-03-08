#!/usr/bin/env python3
"""Run full-paper analysis for top papers using local Codex CLI."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ai_enrich import (
    build_editorial_instruction_text,
    build_skill_prompt_text,
    get_repo_root,
    load_config,
    normalize_model_text,
)
from content_store import write_json

logger = logging.getLogger(__name__)

SECTION_ALIASES = {
    'abstract': ['abstract'],
    'introduction': ['introduction', 'background', 'motivation'],
    'method': ['method', 'approach', 'framework', 'model', 'architecture', 'preliminaries'],
    'experiments': ['experiment', 'evaluation', 'results', 'analysis', 'ablation'],
    'conclusion': ['conclusion', 'discussion', 'limitation', 'limitations', 'future work'],
}
DEFAULT_ANALYSIS_SETTINGS = {
    'enabled': True,
    'top_n': 3,
    'refresh_existing': False,
    'max_full_text_chars': 24000,
    'section_char_budget': 4500,
    'pdf_page_limit': 18,
}

DEFAULT_SCORE_CARD = {
    'innovation': 6,
    'technical_quality': 6,
    'experimental_rigor': 6,
    'writing_clarity': 6,
    'practical_value': 6,
}
INSTITUTION_HINTS = (
    'university', 'institute', 'laboratory', 'lab', 'school', 'college', 'department',
    'academy', 'hospital', 'centre', 'center', 'research', 'microsoft', 'google',
    'deepmind', 'meta', 'openai', 'anthropic', 'nvidia', 'amazon', 'alibaba', 'tencent',
)
RELATION_PRIORITY = {
    'related': 0,
    'follows': 1,
    'extends': 2,
    'compares': 3,
    'improves': 4,
}


def normalize_image_token(value: str) -> str:
    text = str(value or '').strip().lower()
    text = re.sub(r'\\', '/', text)
    text = text.split('/')[-1]
    text = re.sub(r'\.[a-z0-9]+$', '', text)
    text = re.sub(r'_page\d+$', '', text)
    text = re.sub(r'[^a-z0-9]+', '', text)
    return text


def normalize_paper_id(raw: str) -> str:
    return str(raw or '').replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '').replace('arXiv:', '').strip()


def looks_like_arxiv_id(value: str) -> bool:
    return bool(re.fullmatch(r'\d{4}\.\d+(?:v\d+)?', str(value or '').strip()))


def analysis_priority_rank(paper: Dict[str, Any]) -> int:
    try:
        rank = int(paper.get('analysis_priority_rank', 0) or 0)
    except (TypeError, ValueError):
        rank = 0
    return rank if rank > 0 else 10**6


def coerce_string_list(value: Any, max_items: int) -> List[str]:
    if not isinstance(value, list):
        return []
    items: List[str] = []
    for item in value:
        raw = normalize_model_text(item)
        if not raw:
            continue
        pieces = [raw]
        for pattern in (r"'\s*,\s*'", r'"\s*,\s*"'):
            next_pieces: List[str] = []
            for piece in pieces:
                next_pieces.extend(re.split(pattern, piece))
            pieces = next_pieces
        for piece in pieces:
            text = normalize_model_text(piece)
            if text:
                items.append(text)
    return items[:max_items]


def coerce_score_card(value: Any) -> Dict[str, int]:
    raw = value if isinstance(value, dict) else {}
    result: Dict[str, int] = {}
    for key, default in DEFAULT_SCORE_CARD.items():
        try:
            score = int(raw.get(key, default))
        except (TypeError, ValueError, AttributeError):
            score = default
        result[key] = max(1, min(10, score))
    return result


def coerce_related_work_comparisons(value: Any, max_items: int) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    items: List[Dict[str, str]] = []
    for item in value[:max_items]:
        if not isinstance(item, dict):
            continue
        title = normalize_model_text(item.get('title') or '')
        comparison = normalize_model_text(item.get('comparison_zh') or '')
        relation = normalize_model_text(item.get('relation') or '')
        paper_id = normalize_paper_id(item.get('paper_id') or '')
        if not title or not comparison:
            continue
        items.append({
            'paper_id': paper_id,
            'title': title,
            'relation': relation or 'related',
            'comparison_zh': comparison,
        })
    return items


def normalize_analysis_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = config.get('analysis', {}) if isinstance(config, dict) else {}
    result = dict(DEFAULT_ANALYSIS_SETTINGS)
    if isinstance(raw, dict):
        for key, default in DEFAULT_ANALYSIS_SETTINGS.items():
            if key not in raw:
                continue
            value = raw[key]
            if isinstance(default, bool):
                result[key] = bool(value)
            elif isinstance(default, int):
                try:
                    result[key] = int(value)
                except (TypeError, ValueError):
                    result[key] = default
    return result


def paper_slug_name(paper: Dict[str, Any]) -> str:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
    title = str(paper.get('title') or '').strip()
    from content_store import paper_slug

    return paper_slug(paper_id, title)


def safe_extract_tarball(archive: Path, target_dir: Path) -> None:
    with tarfile.open(archive, 'r:*') as tar:
        safe_members = []
        for member in tar.getmembers():
            name = member.name
            if name.startswith('/') or '..' in Path(name).parts:
                continue
            safe_members.append(member)
        tar.extractall(path=target_dir, members=safe_members)


def download_to_path(url: str, path: Path, timeout_seconds: int = 120) -> Path:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def strip_latex_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        current = []
        escaped = False
        for char in line:
            if char == '%' and not escaped:
                break
            current.append(char)
            escaped = (char == '\\' and not escaped)
        lines.append(''.join(current))
    return '\n'.join(lines)


def resolve_tex_reference(base_dir: Path, reference: str) -> Path | None:
    ref = reference.strip()
    if not ref:
        return None
    candidates = [base_dir / ref]
    if not Path(ref).suffix:
        candidates.append(base_dir / f'{ref}.tex')
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def expand_tex_file(path: Path, seen: set[Path]) -> str:
    resolved = path.resolve()
    if resolved in seen:
        return ''
    seen.add(resolved)

    text = path.read_text(encoding='utf-8', errors='ignore')
    text = strip_latex_comments(text)

    pattern = re.compile(r'\\(?:input|include)\{([^}]+)\}')

    def replace(match: re.Match[str]) -> str:
        nested = resolve_tex_reference(path.parent, match.group(1))
        if not nested:
            return ''
        return expand_tex_file(nested, seen)

    return pattern.sub(replace, text)


def latex_to_text(text: str) -> str:
    text = re.sub(r'\\(?:section|subsection|subsubsection|paragraph)\*?\{([^{}]+)\}', r'\n\n## \1\n\n', text)
    text = re.sub(r'\\(?:caption|title)\{([^{}]+)\}', r'\n\1\n', text)
    text = re.sub(r'\\(?:textbf|textit|emph|underline|mbox|mathrm|mathbf|textrm)\{([^{}]+)\}', r'\1', text)
    text = re.sub(r'\\(?:cite|citet|citep|ref|eqref|label|url|footnote)\{[^{}]*\}', '', text)
    text = re.sub(r'\\begin\{(?:equation|align|aligned|gather|multline|table|figure)\*?\}.*?\\end\{(?:equation|align|aligned|gather|multline|table|figure)\*?\}', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\$[^$]*\$', ' ', text)
    text = re.sub(r'\\\[.*?\\\]', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?', ' ', text)
    text = text.replace('{', ' ').replace('}', ' ')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_braced_value(text: str, start_index: int) -> tuple[str, int]:
    if start_index >= len(text) or text[start_index] != '{':
        return '', start_index
    depth = 0
    result: List[str] = []
    index = start_index
    while index < len(text):
        char = text[index]
        if char == '{':
            depth += 1
            if depth > 1:
                result.append(char)
        elif char == '}':
            depth -= 1
            if depth == 0:
                return ''.join(result), index + 1
            if depth > 0:
                result.append(char)
        else:
            result.append(char)
        index += 1
    return ''.join(result), index


def command_argument(block: str, command: str) -> str:
    match = re.search(rf'\\{command}\*?(?:\[[^\]]*\])?\{{', block)
    if not match:
        return ''
    start = match.end() - 1
    value, _ = extract_braced_value(block, start)
    return value


def command_arguments(block: str, command: str) -> List[str]:
    values: List[str] = []
    for match in re.finditer(rf'\\{command}\*?(?:\[[^\]]*\])?\{{', block):
        start = match.end() - 1
        value, _ = extract_braced_value(block, start)
        if value:
            values.append(value)
    return values


def clean_metadata_text(text: str) -> str:
    value = latex_to_text(text)
    value = re.sub(r'\b[\w.\-]+@[\w.\-]+\b', '', value)
    value = value.replace('\u200b', ' ')
    value = re.sub(r'^[\d\W_]+(?=[A-Za-z])', '', value)
    value = re.sub(
        r'\b(?:equal contribution|corresponding author|work done during.*|internship)\b.*$',
        '',
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r'\s+', ' ', value).strip(' ,;:-')
    return value.strip()


def split_metadata_candidates(text: str) -> List[str]:
    parts = re.split(r'(?:\\\\|\\and|;|\n|\|)', text)
    return [clean_metadata_text(part) for part in parts if clean_metadata_text(part)]


def looks_like_institution(text: str) -> bool:
    normalized = text.lower()
    if len(normalized) < 5:
        return False
    return any(token in normalized for token in INSTITUTION_HINTS)


def dedupe_texts(items: Iterable[str], max_items: int) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        cleaned = clean_metadata_text(item)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= max_items:
            break
    return result


def extract_source_metadata_from_latex(latex_source: str) -> Dict[str, Any]:
    institutions: List[str] = []

    simple_commands = [
        'affiliation', 'affiliations', 'institute', 'institution', 'affaddr', 'address', 'affil'
    ]
    for command in simple_commands:
        for raw in command_arguments(latex_source, command):
            institutions.extend(
                candidate for candidate in split_metadata_candidates(raw)
                if looks_like_institution(candidate)
            )

    for raw in re.findall(r'\\icmlaffiliation\*?(?:\[[^\]]*\])?\{[^{}]*\}\{([^{}]+)\}', latex_source):
        institutions.extend(
            candidate for candidate in split_metadata_candidates(raw)
            if looks_like_institution(candidate)
        )

    if not institutions:
        author_block = command_argument(latex_source, 'author')
        for candidate in split_metadata_candidates(author_block):
            if looks_like_institution(candidate):
                institutions.append(candidate)

    return {
        'institutions': dedupe_texts(institutions, 8),
    }


def classify_figure_role(text: str) -> str:
    normalized = normalize_heading(text)
    if any(token in normalized for token in ['framework', 'pipeline', 'overview', 'architecture', 'method', 'model', 'system', 'workflow']):
        return 'method'
    if any(token in normalized for token in ['result', 'performance', 'benchmark', 'evaluation', 'experiment', 'ablation', 'tsne', 'accuracy', 'comparison', 'analysis']):
        return 'results'
    if any(token in normalized for token in ['dataset', 'example', 'case', 'visual', 'qualitative']):
        return 'examples'
    return 'other'


def classify_table_role(text: str) -> str:
    normalized = normalize_heading(text)
    if any(token in normalized for token in ['ablation', 'analysis', 'sensitivity']):
        return 'ablation'
    if any(token in normalized for token in ['result', 'performance', 'benchmark', 'evaluation', 'latency', 'throughput', 'memory', 'speedup', 'comparison']):
        return 'results'
    if any(token in normalized for token in ['setup', 'configuration', 'dataset', 'hyperparameter']):
        return 'setup'
    return 'other'


def compact_latex_inline(text: str) -> str:
    value = latex_to_text(text)
    value = re.sub(r'\s+', ' ', value).strip(' |')
    return value


def strip_latex_table_commands(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r'\\(?:toprule|midrule|bottomrule|cmidrule(?:\[[^\]]*\])?\{[^}]*\}|hline|cline\{[^}]*\}|addlinespace)', '', cleaned)
    cleaned = re.sub(r'\\(?:small|footnotesize|scriptsize|tiny|centering|resizebox(?:\[[^\]]*\])?\{[^}]*\}\{[^}]*\})', '', cleaned)
    cleaned = re.sub(r'\\(?:label|caption)\{[^{}]*\}', '', cleaned)
    cleaned = re.sub(r'\\(?:multirow|multicolumn)(?:\[[^\]]*\])?\{[^{}]*\}\{[^{}]*\}\{([^{}]*)\}', r'\1', cleaned)
    return cleaned


def extract_table_rows_from_block(block: str) -> List[str]:
    tabular_match = re.search(r'\\begin\{tabular\*?\}(?:\[[^\]]*\])?\{.*?\}(.*?)\\end\{tabular\*?\}', block, flags=re.DOTALL)
    if not tabular_match:
        tabular_match = re.search(r'\\begin\{array\}(?:\[[^\]]*\])?\{.*?\}(.*?)\\end\{array\}', block, flags=re.DOTALL)
    if not tabular_match:
        return []

    tabular = strip_latex_table_commands(tabular_match.group(1))
    raw_rows = [row.strip() for row in re.split(r'\\\\', tabular) if row.strip()]
    rows: List[str] = []
    for row in raw_rows:
        cells = [compact_latex_inline(cell) for cell in row.split('&')]
        cells = [cell for cell in cells if cell]
        if len(cells) >= 2:
            rows.append(' | '.join(cells))
        elif cells:
            rows.append(cells[0])
        if len(rows) >= 8:
            break
    return rows


def extract_table_context(latex_source: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    table_blocks = re.finditer(r'\\begin\{table\*?\}(.*?)\\end\{table\*?\}', latex_source, flags=re.DOTALL)

    for match in table_blocks:
        block = match.group(1)
        caption_raw = command_argument(block, 'caption')
        caption = latex_to_text(caption_raw)[:500] if caption_raw else ''
        label = command_argument(block, 'label')
        rows = extract_table_rows_from_block(block)
        key = (caption, '\n'.join(rows[:3]))
        if key in seen or (not caption and not rows):
            continue
        seen.add(key)
        entries.append({
            'caption': caption,
            'label': label,
            'role_hint': classify_table_role(caption + ' ' + ' '.join(rows[:2])),
            'rows': rows[:8],
        })
    return entries[:12]


def extract_figure_context(latex_source: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    figure_blocks = re.finditer(r'\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}', latex_source, flags=re.DOTALL)

    for match in figure_blocks:
        block = match.group(1)
        caption_raw = command_argument(block, 'caption')
        caption = latex_to_text(caption_raw)[:500] if caption_raw else ''
        refs = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', block)
        if not refs:
            continue
        role_hint = classify_figure_role(' '.join(refs) + ' ' + caption)
        for ref in refs:
            token = normalize_image_token(ref)
            if not token:
                continue
            key = (token, caption)
            if key in seen:
                continue
            seen.add(key)
            entries.append({
                'image_ref': ref,
                'image_token': token,
                'caption': caption,
                'role_hint': role_hint,
            })
    return entries[:20]


def score_tex_file(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding='utf-8', errors='ignore')
    score = 0
    if '\\documentclass' in text:
        score += 100
    if '\\begin{document}' in text:
        score += 50
    score += len(text) // 1000
    return score, len(text)


def extract_text_figures_and_metadata_from_source_tree(root: Path) -> tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    tex_files = [path for path in root.rglob('*.tex') if path.is_file()]
    if not tex_files:
        return '', [], [], {'institutions': []}
    main_tex = sorted(tex_files, key=score_tex_file, reverse=True)[0]
    expanded = expand_tex_file(main_tex, seen=set())
    return (
        latex_to_text(expanded),
        extract_figure_context(expanded),
        extract_table_context(expanded),
        extract_source_metadata_from_latex(expanded),
    )


def extract_text_from_pdf(pdf_path: Path, page_limit: int) -> str:
    try:
        import fitz  # type: ignore
    except ImportError:
        logger.warning('PyMuPDF not installed; PDF full-text extraction unavailable')
        return ''

    pages: List[str] = []
    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            if index >= page_limit:
                break
            text = page.get_text('text').strip()
            if text:
                pages.append(f'\n\n## Page {index + 1}\n{text}')
    return '\n'.join(pages).strip()


def normalize_heading(heading: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', heading.lower()).strip()


def split_sections(text: str) -> Dict[str, str]:
    if not text:
        return {}
    sections: Dict[str, List[str]] = {}
    current = 'preamble'
    sections[current] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if raw_line.startswith('## '):
            current = raw_line[3:].strip()
            sections.setdefault(current, [])
            continue
        if line:
            sections.setdefault(current, []).append(line)
    return {heading: '\n'.join(lines).strip() for heading, lines in sections.items() if '\n'.join(lines).strip()}


def pick_section_text(sections: Dict[str, str], aliases: Iterable[str], max_chars: int) -> str:
    for heading, content in sections.items():
        normalized = normalize_heading(heading)
        if any(alias in normalized for alias in aliases):
            return content[:max_chars].strip()
    return ''


def build_text_context(text: str, max_full_text_chars: int, section_char_budget: int) -> Dict[str, Any]:
    sections = split_sections(text)
    headings = [heading for heading in sections.keys() if heading != 'preamble'][:20]
    payload = {
        'headings': headings,
        'abstract': pick_section_text(sections, SECTION_ALIASES['abstract'], section_char_budget),
        'introduction': pick_section_text(sections, SECTION_ALIASES['introduction'], section_char_budget),
        'method': pick_section_text(sections, SECTION_ALIASES['method'], section_char_budget),
        'experiments': pick_section_text(sections, SECTION_ALIASES['experiments'], section_char_budget),
        'conclusion': pick_section_text(sections, SECTION_ALIASES['conclusion'], section_char_budget),
        'full_text_excerpt': text[:max_full_text_chars].strip(),
    }
    return payload


def extract_paper_context(paper: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
    if not paper_id:
        return {
            'source_kind': 'none',
            'text_context': build_text_context('', settings['max_full_text_chars'], settings['section_char_budget']),
            'figure_context': [],
            'table_context': [],
            'metadata': {
                'institutions': [],
            },
        }

    with tempfile.TemporaryDirectory(prefix='full-paper-analysis-') as tmp:
        tmp_dir = Path(tmp)
        source_path = tmp_dir / f'{paper_id}.tar.gz'
        pdf_path = tmp_dir / f'{paper_id}.pdf'

        text = ''
        source_kind = 'none'
        figure_context: List[Dict[str, Any]] = []
        table_context: List[Dict[str, Any]] = []
        metadata: Dict[str, Any] = {
            'institutions': [],
        }

        if looks_like_arxiv_id(paper_id):
            try:
                download_to_path(f'https://arxiv.org/e-print/{paper_id}', source_path)
                extract_dir = tmp_dir / 'source'
                extract_dir.mkdir(parents=True, exist_ok=True)
                safe_extract_tarball(source_path, extract_dir)
                text, figure_context, table_context, metadata = extract_text_figures_and_metadata_from_source_tree(extract_dir)
                if text:
                    source_kind = 'arxiv_source'
            except Exception as exc:
                logger.warning('Source extraction failed for %s: %s', paper_id, exc)

        if not text:
            try:
                pdf_source = str(paper.get('pdf_url') or '').strip()
                if not pdf_source:
                    source_url = str(paper.get('source_url') or paper.get('url') or '').strip()
                    if source_url.lower().endswith('.pdf'):
                        pdf_source = source_url
                if not pdf_source and looks_like_arxiv_id(paper_id):
                    pdf_source = f'https://arxiv.org/pdf/{paper_id}.pdf'
                if not pdf_source:
                    raise FileNotFoundError('no pdf source available')
                download_to_path(pdf_source, pdf_path)
                text = extract_text_from_pdf(pdf_path, settings['pdf_page_limit'])
                if text:
                    source_kind = 'pdf'
            except Exception as exc:
                logger.warning('PDF extraction failed for %s: %s', paper_id, exc)

        text_context = build_text_context(text, settings['max_full_text_chars'], settings['section_char_budget'])
        return {
            'source_kind': source_kind,
            'text_context': text_context,
            'text_char_count': len(text),
            'figure_context': figure_context[:12],
            'table_context': table_context[:8],
            'metadata': metadata,
        }


def image_manifest(repo_root: Path, paper: Dict[str, Any]) -> List[str]:
    note_dir = repo_root / 'content' / 'papers' / paper_slug_name(paper) / 'images'
    if not note_dir.exists():
        return []
    result = []
    for path in sorted(note_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.svg'}:
            result.append(path.name)
    return result[:12]


def paper_keyword_set(paper: Dict[str, Any]) -> set[str]:
    keywords = paper.get('matched_keywords') or paper.get('ai', {}).get('keywords') or []
    if not isinstance(keywords, list):
        return set()
    return {str(item).strip().lower() for item in keywords if str(item).strip()}


def related_paper_candidates(current_paper: Dict[str, Any], papers: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    current_id = normalize_paper_id(current_paper.get('arxiv_id') or current_paper.get('arxivId') or current_paper.get('id', ''))
    current_domain = str(current_paper.get('matched_domain') or '').strip()
    current_keywords = paper_keyword_set(current_paper)
    scored: List[tuple[int, float, Dict[str, Any]]] = []

    for other in papers:
        other_id = normalize_paper_id(other.get('arxiv_id') or other.get('arxivId') or other.get('id', ''))
        if not other_id or other_id == current_id:
            continue
        overlap = len(current_keywords & paper_keyword_set(other))
        score = overlap
        if current_domain and other.get('matched_domain') == current_domain:
            score += 2
        if score <= 0:
            continue
        scored.append((score, float(other.get('scores', {}).get('recommendation', 0) or 0), other))

    scored.sort(key=lambda item: (-item[0], -item[1], str(item[2].get('title') or '')))
    candidates: List[Dict[str, Any]] = []
    for _, _, paper in scored[:limit]:
        candidates.append({
            'paper_id': normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', '')),
            'title': str(paper.get('title') or ''),
            'domain': str(paper.get('matched_domain') or ''),
            'summary': normalize_model_text(paper.get('ai', {}).get('summary_zh') or paper.get('summary') or ''),
            'keywords': list(paper_keyword_set(paper))[:6],
            'recommendation_score': paper.get('scores', {}).get('recommendation', 0),
        })
    return candidates


def infer_relation_label(current_paper: Dict[str, Any], candidate: Dict[str, Any]) -> str:
    current_text = ' '.join([
        str(current_paper.get('title') or ''),
        str(current_paper.get('summary') or ''),
        str(current_paper.get('ai', {}).get('summary_zh') or ''),
    ]).lower()
    candidate_text = ' '.join([
        str(candidate.get('title') or ''),
        str(candidate.get('summary') or ''),
    ]).lower()

    if any(token in current_text for token in ['benchmark', 'evaluation', 'probe', 'mapping', 'analysis', 'rethinking', 'compare']):
        return 'compares'
    if any(token in current_text for token in ['extend', 'build on', 'adapter', 'augment']):
        return 'extends'
    if any(token in current_text for token in ['faster', 'efficient', 'improve', 'enhance', 'memory-efficient', 'scaling', 'better']):
        if any(token in candidate_text for token in ['training', 'inference', 'reinforcement', 'reasoning', 'retrieval']):
            return 'improves'
    return 'compares'


def fallback_related_work_comparisons(
    current_paper: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    analysis: Dict[str, Any],
) -> List[Dict[str, str]]:
    if not candidates:
        return []

    route = normalize_model_text(analysis.get('technical_route_zh') or '')
    comparisons: List[Dict[str, str]] = []
    for candidate in candidates[:2]:
        relation = infer_relation_label(current_paper, candidate)
        title = str(candidate.get('title') or '').strip()
        paper_id = normalize_paper_id(candidate.get('paper_id') or '')
        candidate_summary = normalize_model_text(candidate.get('summary') or '')
        if not title or not paper_id:
            continue
        comparison = (
            f"两篇都落在{str(current_paper.get('matched_domain') or '相近问题').strip()}方向。"
            f"当前论文更侧重{route or '当前这条方法链路'}，而《{title}》更像是“{candidate_summary[:80]}”这一路线，"
            f"因此更适合作为横向比较而不是直接替代。"
        )
        comparisons.append({
            'paper_id': paper_id,
            'title': title,
            'relation': relation,
            'comparison_zh': comparison,
        })
    return comparisons[:3]


def infer_technical_route_from_paper(paper: Dict[str, Any]) -> str:
    text = ' '.join([
        str(paper.get('title') or ''),
        str(paper.get('matched_domain') or ''),
        ' '.join(str(item) for item in (paper.get('matched_keywords') or [])),
    ]).lower()
    if any(token in text for token in ['flashattention', 'attention kernel', 'kernel', 'cuda', 'triton', 'ptx', 'sass']):
        return '这篇论文属于算子级 / kernel 级 GPU 加速路线，主要解决 attention 或 GPU kernel 的底层执行效率问题。'
    if any(token in text for token in ['kv cache', 'serving', 'prefill', 'decode', 'runtime']):
        return '这篇论文属于 serving runtime / KV cache 优化路线，主要解决 LLM 推理链路中的缓存与执行效率问题。'
    if any(token in text for token in ['quantization', '4bit', '4-bit', 'gptq']):
        return '这篇论文属于量化推理路线，主要通过更低比特表示来降低部署成本并提升推理可行性。'
    return '这篇论文属于 systems 导向的方法路线，但提取文本没有充分说明它在完整系统栈中的精确位置。'


def load_existing_full_analysis_map(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}

    result: Dict[str, Dict[str, Any]] = {}
    papers = payload.get('top_papers', []) if isinstance(payload, dict) else []
    if not isinstance(papers, list):
        return result
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('paper_id') or paper.get('id', ''))
        full_analysis = paper.get('full_analysis')
        if paper_id and isinstance(full_analysis, dict):
            result[paper_id] = full_analysis
    return result


def merge_analysis_metadata(previous: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(previous.get('metadata', {})) if isinstance(previous.get('metadata'), dict) else {}
    fresh = context.get('metadata', {})
    if isinstance(fresh, dict):
        for key, value in fresh.items():
            if value:
                merged[key] = value
    return merged


def reuse_previous_full_analysis(previous: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    reused = copy.deepcopy(previous)
    reused['enabled'] = True
    reused['source_kind'] = context.get('source_kind') or previous.get('source_kind', 'none')
    reused['text_char_count'] = context.get('text_char_count') or previous.get('text_char_count', 0)
    reused['figure_context'] = context.get('figure_context') or previous.get('figure_context', [])
    reused['table_context'] = context.get('table_context') or previous.get('table_context', [])
    reused['metadata'] = merge_analysis_metadata(previous, context)
    reused['reused_from_previous'] = True
    return reused


def heuristic_full_analysis(
    paper: Dict[str, Any],
    context: Dict[str, Any],
    related_candidates: List[Dict[str, Any]],
    reason: str,
) -> Dict[str, Any]:
    ai = paper.get('ai', {}) if isinstance(paper.get('ai'), dict) else {}
    content = normalize_full_analysis({
        'abstract_translation_zh': ai.get('summary_zh') or ai.get('fallback_summary') or '',
        'background_zh': ai.get('background_zh') or '',
        'problem_zh': ai.get('problem_zh') or '',
        'method_overview_zh': ai.get('approach_zh') or '',
        'method_details': ai.get('core_contributions') or [],
        'experiment_setup_zh': ai.get('evidence_zh') or '提取文本没有充分说明实验设置。',
        'datasets_or_benchmarks': [],
        'baselines': [],
        'metrics': [],
        'ablation_or_analysis': [],
        'evaluation_validity': ai.get('risks') or ['提取文本没有充分说明 baseline 公平性与实验边界。'],
        'main_results_zh': ai.get('evidence_zh') or '提取文本没有充分说明主要结果。',
        'strengths': ai.get('why_read') or [],
        'limitations': ai.get('risks') or [],
        'technical_route_zh': infer_technical_route_from_paper(paper),
        'relation_to_prior_work_zh': '当前未能调用模型完成全文比较，因此这里只保守保留基于题目、摘要与候选论文的路线级比较。',
        'related_work_comparisons': [],
        'score_card': DEFAULT_SCORE_CARD,
        'practical_value_zh': ai.get('value_zh') or '',
        'future_work': ai.get('open_questions') or [],
        'reading_checklist': ai.get('open_questions') or [],
        'overall_assessment_zh': (
            f"{normalize_model_text(ai.get('value_zh') or '')} "
            f"当前由于 {reason} 未能生成新的模型级全文分析，因此这份 memo 主要复用已有摘要信息与提取上下文，"
            "可信度应按保守草稿理解。"
        ).strip(),
    })
    if not content.get('related_work_comparisons'):
        content['related_work_comparisons'] = fallback_related_work_comparisons(
            paper,
            related_candidates,
            content,
        )
    return {
        'enabled': True,
        'source_kind': context.get('source_kind', 'none'),
        'text_char_count': context.get('text_char_count', 0),
        'figure_context': context.get('figure_context', []),
        'table_context': context.get('table_context', []),
        'metadata': context.get('metadata', {}),
        'content': content,
        'fallback_reason': reason,
    }


def build_prompt(
    repo_root: Path,
    config: Dict[str, Any],
    paper: Dict[str, Any],
    context: Dict[str, Any],
    related_candidates: List[Dict[str, Any]],
) -> str:
    editorial = build_editorial_instruction_text(config)
    skills = build_skill_prompt_text(repo_root, config)
    payload = {
        'paper': {
            'paper_id': normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', '')),
            'title': paper.get('title', ''),
            'authors': paper.get('authors', [])[:12],
            'domain': paper.get('matched_domain', 'Uncategorized'),
            'published': paper.get('published', paper.get('publicationDate', '')),
            'venue': paper.get('venue', ''),
            'journal_ref': paper.get('journal_ref', ''),
            'comments': paper.get('comments', ''),
            'citation_count': paper.get('citationCount'),
            'influential_citation_count': paper.get('influentialCitationCount'),
            'abstract': paper.get('summary') or paper.get('abstract') or '',
            'categories': paper.get('categories', [])[:8],
            'matched_keywords': paper.get('matched_keywords', [])[:8],
            'scores': paper.get('scores', {}),
            'ai_digest': paper.get('ai', {}),
            'image_files': image_manifest(repo_root, paper),
        },
        'full_text_context': context,
        'figure_context': context.get('figure_context', [])[:8],
        'table_context': context.get('table_context', [])[:6],
        'related_paper_candidates': related_candidates[:3],
    }

    instructions = [
        '你是一个严格的论文分析助手，需要为单篇论文生成接近研究笔记风格的全文分析。',
        '你必须只基于下面提供的标题、摘要、全文提取片段、图名和已有元数据作答，不要读取仓库文件，不要运行命令，不要调用工具，不要自行搜索额外信息。',
        '要求：\n'
        '1. 输出语言为简体中文。\n'
        '2. 不要编造实验数字、对比基线、实现细节、作者机构或代码信息。\n'
        '3. 如果全文提取片段没有覆盖某部分，要明确写“提取文本没有充分说明”。\n'
        '4. 输出必须匹配给定 schema。\n'
        '5. 这不是摘要改写，而是 compact full paper analysis，要覆盖背景、方法、实验、价值、局限和进一步阅读重点。\n'
        '6. `method_details` 要给出 3 到 5 个足够具体的技术点。\n'
        '7. `main_results_zh` 只写提取文本真正支持的结论。\n'
        '8. `relation_to_prior_work_zh` 要说明它相对常见路线的差异，而不是泛泛说“有创新”。\n'
        '9. `overall_assessment_zh` 要给出一段客观评价，指出最值得信和最该怀疑的地方。\n'
        '10. `technical_route_zh` 要说明这篇论文属于哪条技术路线、解决链路中的哪一段问题。\n'
        '11. `score_card` 必须保守打分，1 到 10 的整数，分别评价创新性、技术质量、实验严谨性、写作清晰度和实用价值。\n'
        '12. `related_work_comparisons` 只允许对给定的候选论文做比较；如果候选论文与当前论文明显同领域或同问题，优先给出 1 到 2 条保守比较，而不是全部留空。\n'
        '13. `datasets_or_benchmarks`、`baselines`、`metrics`、`ablation_or_analysis`、`evaluation_validity` 要尽量做结构化抽取；只写提取文本明确支持的条目。\n'
        '14. 如果输入里提供了 table_context，要优先从表格 caption 和行内容中抽取实验设置、基线、指标和结果边界。',
    ]
    if editorial:
        instructions.append('仓库编辑偏好：\n' + editorial)
    if skills:
        instructions.append('项目技能说明：\n' + skills)

    return '\n\n'.join(instructions) + '\n\n下面是输入数据：\n' + json.dumps(payload, ensure_ascii=False, indent=2)


def normalize_full_analysis(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'abstract_translation_zh': normalize_model_text(raw.get('abstract_translation_zh') or ''),
        'background_zh': normalize_model_text(raw.get('background_zh') or ''),
        'problem_zh': normalize_model_text(raw.get('problem_zh') or ''),
        'method_overview_zh': normalize_model_text(raw.get('method_overview_zh') or ''),
        'method_details': coerce_string_list(raw.get('method_details'), 5),
        'experiment_setup_zh': normalize_model_text(raw.get('experiment_setup_zh') or ''),
        'datasets_or_benchmarks': coerce_string_list(raw.get('datasets_or_benchmarks'), 6),
        'baselines': coerce_string_list(raw.get('baselines'), 6),
        'metrics': coerce_string_list(raw.get('metrics'), 6),
        'ablation_or_analysis': coerce_string_list(raw.get('ablation_or_analysis'), 4),
        'evaluation_validity': coerce_string_list(raw.get('evaluation_validity'), 4),
        'main_results_zh': normalize_model_text(raw.get('main_results_zh') or ''),
        'strengths': coerce_string_list(raw.get('strengths'), 4),
        'limitations': coerce_string_list(raw.get('limitations'), 4),
        'technical_route_zh': normalize_model_text(raw.get('technical_route_zh') or ''),
        'relation_to_prior_work_zh': normalize_model_text(raw.get('relation_to_prior_work_zh') or ''),
        'related_work_comparisons': coerce_related_work_comparisons(raw.get('related_work_comparisons'), 3),
        'score_card': coerce_score_card(raw.get('score_card')),
        'practical_value_zh': normalize_model_text(raw.get('practical_value_zh') or ''),
        'future_work': coerce_string_list(raw.get('future_work'), 4),
        'reading_checklist': coerce_string_list(raw.get('reading_checklist'), 4),
        'overall_assessment_zh': normalize_model_text(raw.get('overall_assessment_zh') or ''),
    }


def analyze_paper(
    repo_root: Path,
    config: Dict[str, Any],
    paper: Dict[str, Any],
    papers: List[Dict[str, Any]],
    codex_path: str,
) -> Dict[str, Any]:
    context = extract_paper_context(paper, normalize_analysis_settings(config))
    related_candidates = related_paper_candidates(paper, papers)
    prompt = build_prompt(
        repo_root,
        config,
        paper,
        context,
        related_candidates,
    )
    schema_path = repo_root / 'scripts' / 'full_paper_analysis_schema.json'

    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.json', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    cmd = [
        codex_path,
        'exec',
        '--cd', str(repo_root),
        '--skip-git-repo-check',
        '--output-schema', str(schema_path),
        '--output-last-message', str(tmp_path),
        prompt,
    ]

    try:
        subprocess.run(cmd, check=True)
        raw = json.loads(tmp_path.read_text(encoding='utf-8'))
        normalized = normalize_full_analysis(raw)
        if not normalized.get('related_work_comparisons'):
            normalized['related_work_comparisons'] = fallback_related_work_comparisons(
                paper,
                related_candidates,
                normalized,
            )
        return {
            'enabled': True,
            'source_kind': context.get('source_kind', 'none'),
            'text_char_count': context.get('text_char_count', 0),
            'figure_context': context.get('figure_context', []),
            'table_context': context.get('table_context', []),
            'metadata': context.get('metadata', {}),
            'content': normalized,
        }
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Run full-paper analysis for top papers using local Codex CLI')
    parser.add_argument('--input', required=True, help='Input enriched JSON')
    parser.add_argument('--output', required=True, help='Output analyzed JSON')
    parser.add_argument('--config', default=None, help='Config YAML path')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    parser.add_argument('--paper-id', default=None, help='Analyze only the specified paper ID')
    parser.add_argument('--top-n', type=int, default=None, help='Override how many top analysis candidates to process')
    parser.add_argument('--strict', action='store_true', help='Fail instead of falling back on errors')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    config = load_config(args.config)
    settings = normalize_analysis_settings(config)
    if args.top_n is not None:
        settings['top_n'] = max(0, int(args.top_n))
    target_paper_id = normalize_paper_id(args.paper_id or '')

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_absolute():
        input_path = repo_root / input_path
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    payload = json.loads(input_path.read_text(encoding='utf-8'))
    papers = payload.get('top_papers', [])
    if not settings['enabled']:
        write_json(output_path, payload)
        return 0

    codex_path = shutil.which('codex')
    if not codex_path:
        if args.strict:
            raise FileNotFoundError('codex command not found in PATH')
        write_json(output_path, payload)
        return 0

    existing_full_analysis_map = load_existing_full_analysis_map(output_path)
    result = copy.deepcopy(payload)

    ranked_papers = sorted(
        result.get('top_papers', []),
        key=lambda paper: (
            analysis_priority_rank(paper),
            -float(paper.get('analysis_candidate_score', 0) or 0),
            -float(paper.get('scores', {}).get('recommendation', 0) or 0),
        ),
    )
    if target_paper_id:
        ranked_papers = [
            paper for paper in ranked_papers
            if normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', '')) == target_paper_id
        ]
        if not ranked_papers:
            raise SystemExit(f'Paper ID not found in input: {target_paper_id}')
        settings['top_n'] = len(ranked_papers)

    for paper in result.get('top_papers', []):
        paper['selected_for_full_analysis'] = False

    for index, paper in enumerate(ranked_papers, start=1):
        if index > settings['top_n']:
            break
        paper['selected_for_full_analysis'] = True
        if paper.get('full_analysis', {}).get('enabled') and not settings['refresh_existing']:
            continue
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        logger.info(
            'Running full-paper analysis for %s (analysis rank=%s, score=%s)',
            paper_id or f'paper-{index}',
            paper.get('analysis_priority_rank', index),
            paper.get('analysis_candidate_score', 'N/A'),
        )
        try:
            paper['full_analysis'] = analyze_paper(repo_root, config, paper, result.get('top_papers', []), codex_path)
        except Exception as exc:
            logger.exception('Full-paper analysis failed for %s: %s', paper_id, exc)
            if args.strict:
                raise
            context: Dict[str, Any] = {
                'source_kind': 'none',
                'text_char_count': 0,
                'figure_context': [],
                'table_context': [],
                'metadata': {},
            }
            try:
                context = extract_paper_context(paper, settings)
            except Exception:
                logger.warning('Context extraction also failed for %s during fallback', paper_id)
            previous = existing_full_analysis_map.get(paper_id)
            if isinstance(previous, dict) and previous.get('enabled'):
                paper['full_analysis'] = reuse_previous_full_analysis(previous, context)
                paper['full_analysis']['fallback_reason'] = f'reused_previous:{type(exc).__name__}'
            else:
                paper['full_analysis'] = heuristic_full_analysis(
                    paper,
                    context,
                    related_paper_candidates(paper, result.get('top_papers', [])),
                    f'error:{type(exc).__name__}',
                )

    write_json(output_path, result)
    logger.info('Full-paper analysis completed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
