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


def classify_figure_role(text: str) -> str:
    normalized = normalize_heading(text)
    if any(token in normalized for token in ['framework', 'pipeline', 'overview', 'architecture', 'method', 'model', 'system', 'workflow']):
        return 'method'
    if any(token in normalized for token in ['result', 'performance', 'benchmark', 'evaluation', 'experiment', 'ablation', 'tsne', 'accuracy', 'comparison', 'analysis']):
        return 'results'
    if any(token in normalized for token in ['dataset', 'example', 'case', 'visual', 'qualitative']):
        return 'examples'
    return 'other'


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


def extract_text_and_figures_from_source_tree(root: Path) -> tuple[str, List[Dict[str, Any]]]:
    tex_files = [path for path in root.rglob('*.tex') if path.is_file()]
    if not tex_files:
        return '', []
    main_tex = sorted(tex_files, key=score_tex_file, reverse=True)[0]
    expanded = expand_tex_file(main_tex, seen=set())
    return latex_to_text(expanded), extract_figure_context(expanded)


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
        }

    with tempfile.TemporaryDirectory(prefix='full-paper-analysis-') as tmp:
        tmp_dir = Path(tmp)
        source_path = tmp_dir / f'{paper_id}.tar.gz'
        pdf_path = tmp_dir / f'{paper_id}.pdf'

        text = ''
        source_kind = 'none'
        figure_context: List[Dict[str, Any]] = []

        try:
            download_to_path(f'https://arxiv.org/e-print/{paper_id}', source_path)
            extract_dir = tmp_dir / 'source'
            extract_dir.mkdir(parents=True, exist_ok=True)
            safe_extract_tarball(source_path, extract_dir)
            text, figure_context = extract_text_and_figures_from_source_tree(extract_dir)
            if text:
                source_kind = 'arxiv_source'
        except Exception as exc:
            logger.warning('Source extraction failed for %s: %s', paper_id, exc)

        if not text:
            try:
                download_to_path(f'https://arxiv.org/pdf/{paper_id}.pdf', pdf_path)
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


def build_prompt(repo_root: Path, config: Dict[str, Any], paper: Dict[str, Any], context: Dict[str, Any]) -> str:
    editorial = build_editorial_instruction_text(config)
    skills = build_skill_prompt_text(repo_root, config)
    payload = {
        'paper': {
            'paper_id': normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', '')),
            'title': paper.get('title', ''),
            'authors': paper.get('authors', [])[:12],
            'domain': paper.get('matched_domain', 'Uncategorized'),
            'published': paper.get('published', paper.get('publicationDate', '')),
            'abstract': paper.get('summary') or paper.get('abstract') or '',
            'categories': paper.get('categories', [])[:8],
            'matched_keywords': paper.get('matched_keywords', [])[:8],
            'scores': paper.get('scores', {}),
            'ai_digest': paper.get('ai', {}),
            'image_files': image_manifest(repo_root, paper),
        },
        'full_text_context': context,
        'figure_context': context.get('figure_context', [])[:8],
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
        '9. `overall_assessment_zh` 要给出一段客观评价，指出最值得信和最该怀疑的地方。',
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
        'main_results_zh': normalize_model_text(raw.get('main_results_zh') or ''),
        'strengths': coerce_string_list(raw.get('strengths'), 4),
        'limitations': coerce_string_list(raw.get('limitations'), 4),
        'relation_to_prior_work_zh': normalize_model_text(raw.get('relation_to_prior_work_zh') or ''),
        'practical_value_zh': normalize_model_text(raw.get('practical_value_zh') or ''),
        'future_work': coerce_string_list(raw.get('future_work'), 4),
        'reading_checklist': coerce_string_list(raw.get('reading_checklist'), 4),
        'overall_assessment_zh': normalize_model_text(raw.get('overall_assessment_zh') or ''),
    }


def analyze_paper(repo_root: Path, config: Dict[str, Any], paper: Dict[str, Any], codex_path: str) -> Dict[str, Any]:
    context = extract_paper_context(paper, normalize_analysis_settings(config))
    prompt = build_prompt(repo_root, config, paper, context)
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
        return {
            'enabled': True,
            'source_kind': context.get('source_kind', 'none'),
            'text_char_count': context.get('text_char_count', 0),
            'figure_context': context.get('figure_context', []),
            'content': normalize_full_analysis(raw),
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
    parser.add_argument('--strict', action='store_true', help='Fail instead of falling back on errors')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    config = load_config(args.config)
    settings = normalize_analysis_settings(config)

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

    result = copy.deepcopy(payload)

    for index, paper in enumerate(result.get('top_papers', []), start=1):
        if index > settings['top_n']:
            break
        if paper.get('full_analysis', {}).get('enabled') and not settings['refresh_existing']:
            continue
        paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
        logger.info('Running full-paper analysis for %s', paper_id or f'paper-{index}')
        try:
            paper['full_analysis'] = analyze_paper(repo_root, config, paper, codex_path)
        except Exception as exc:
            logger.exception('Full-paper analysis failed for %s: %s', paper_id, exc)
            if args.strict:
                raise
            paper['full_analysis'] = {
                'enabled': False,
                'reason': f'error:{type(exc).__name__}',
            }

    write_json(output_path, result)
    logger.info('Full-paper analysis completed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
