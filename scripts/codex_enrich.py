#!/usr/bin/env python3
"""Use local Codex CLI to enrich ranked papers into structured daily digest content."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ai_enrich import (
    build_editorial_instruction_text,
    build_prompt_payload,
    build_skill_prompt_text,
    get_repo_root,
    load_config,
    merge_enrichment,
    normalize_paper_id,
    passthrough_payload,
)
from content_store import write_json

logger = logging.getLogger(__name__)

DEFAULT_CODEX_TIMEOUT_SECONDS = 600


def build_instruction_blocks(repo_root: Path, config: Dict[str, Any]) -> List[str]:
    editorial_instructions = build_editorial_instruction_text(config)
    skill_instructions = build_skill_prompt_text(repo_root, config)
    instruction_blocks = [
        '你是一个严格的研究论文编辑。请只基于给定的论文标题、作者、摘要和评分信息，输出一个 JSON 对象，不要输出任何额外解释。',
        '禁止事项：不要读取仓库文件，不要运行任何命令，不要调用任何工具，不要自行搜索额外信息。你需要的规则和输入都已经在下面给出。',
        '要求：\n'
        '1. 输出语言为简体中文。\n'
        '2. 不要编造实验细节、性能数字、作者背景、代码链接。\n'
        '3. 如果摘要信息不足，要明确写出“摘要没有充分说明”。\n'
        '4. JSON 结构必须匹配提供的 schema。\n'
        '5. `summary_zh` 控制在 2 到 4 句。\n'
        '6. `background_zh` 要先交代研究背景和动机，`problem_zh`、`approach_zh`、`evidence_zh` 要分别回答“问题是什么/方法是什么/摘要给了什么证据”。\n'
        '7. `value_zh` 要说明这篇工作如果成立，对研究或工程有什么实际价值。\n'
        '8. `open_questions` 给出 2 到 3 个读论文时最该核对的具体问题。\n'
        '9. `core_contributions`、`why_read`、`risks` 都尽量具体，避免泛泛而谈。',
    ]
    if editorial_instructions:
        instruction_blocks.append('仓库编辑偏好：\n' + editorial_instructions)
    if skill_instructions:
        instruction_blocks.append('项目技能说明：\n' + skill_instructions)
    return instruction_blocks


def build_paper_prompt(repo_root: Path, report_date: str, config: Dict[str, Any], paper: Dict[str, Any]) -> str:
    ai_settings = config.get('ai', {}) if isinstance(config, dict) else {}
    max_abstract_chars = int(ai_settings.get('codex_abstract_chars', 1200))
    prompt_payload = build_prompt_payload(
        report_date,
        config,
        [paper],
        paper_limit=1,
        max_abstract_chars=max_abstract_chars,
    )
    instruction_blocks = build_instruction_blocks(repo_root, config)
    return (
        '\n\n'.join(instruction_blocks)
        + '\n\n下面是单篇论文输入数据：\n'
        + json.dumps(prompt_payload, ensure_ascii=False, indent=2)
    )


def run_codex_json(
    codex_path: str,
    repo_root: Path,
    model: str,
    schema_path: Path,
    prompt: str,
    timeout_seconds: int,
) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.json', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    cmd = [
        codex_path,
        'exec',
        '--cd', str(repo_root),
        '--skip-git-repo-check',
        '--output-schema', str(schema_path),
        '--output-last-message', str(tmp_path),
    ]
    if model:
        cmd.extend(['--model', model])
    cmd.append(prompt)

    try:
        subprocess.run(cmd, check=True, timeout=timeout_seconds)
        return json.loads(tmp_path.read_text(encoding='utf-8'))
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

    parser = argparse.ArgumentParser(description='Use local Codex CLI to enrich ranked paper results')
    parser.add_argument('--input', required=True, help='Input ranked paper JSON')
    parser.add_argument('--output', required=True, help='Output enriched JSON')
    parser.add_argument('--config', default=None, help='Config YAML path')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    parser.add_argument('--strict', action='store_true', help='Fail instead of falling back when Codex enrichment fails')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_absolute():
        input_path = repo_root / input_path
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    payload = json.loads(input_path.read_text(encoding='utf-8'))
    config = load_config(args.config)
    codex_path = shutil.which('codex')
    if not codex_path:
        if args.strict:
            raise FileNotFoundError('codex command not found in PATH')
        logger.warning('codex command not found, falling back')
        write_json(output_path, passthrough_payload(payload, 'missing_codex_cli'))
        return 0

    report_date = payload.get('target_date') or ''
    model = os.environ.get('CODEX_MODEL', '').strip()
    ai_settings = config.get('ai', {}) if isinstance(config, dict) else {}
    paper_limit = int(ai_settings.get('codex_paper_limit', len(payload.get('top_papers', [])) or 10))
    timeout_seconds = int(ai_settings.get('codex_timeout_seconds', DEFAULT_CODEX_TIMEOUT_SECONDS))
    schema_path = repo_root / 'scripts' / 'codex_enrich_paper_schema.json'
    selected_papers = list(payload.get('top_papers', []))[:paper_limit]
    paper_results: List[Dict[str, Any]] = []
    failures = 0

    try:
        logger.info('Running local Codex CLI enrichment per paper (%d papers)', len(selected_papers))
        for index, paper in enumerate(selected_papers, start=1):
            paper_id = normalize_paper_id(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('id', ''))
            logger.info('Enriching paper %d/%d: %s', index, len(selected_papers), paper_id or paper.get('title', 'unknown'))
            prompt = build_paper_prompt(repo_root, report_date, config, paper)
            try:
                raw_item = run_codex_json(codex_path, repo_root, model, schema_path, prompt, timeout_seconds)
                if not isinstance(raw_item, dict):
                    raise ValueError('Codex paper enrichment returned non-object JSON')
                raw_item['paper_id'] = normalize_paper_id(raw_item.get('paper_id') or paper_id)
                paper_results.append(raw_item)
            except Exception as exc:
                failures += 1
                logger.warning('Codex enrichment failed for %s: %s', paper_id or paper.get('title', 'unknown'), exc)

        raw_ai = {
            'daily_brief': {},
            'papers': paper_results,
        }
        enriched = merge_enrichment(payload, raw_ai, model or 'codex-cli')
        enriched['ai_enrichment']['provider'] = 'codex-cli'
        enriched['ai_enrichment']['strategy'] = 'per-paper'
        enriched['ai_enrichment']['paper_results'] = len(paper_results)
        enriched['ai_enrichment']['paper_failures'] = failures
        write_json(output_path, enriched)
        logger.info('Codex enrichment completed with %d successes and %d failures', len(paper_results), failures)
        return 0
    except Exception as exc:
        logger.exception('Codex enrichment failed: %s', exc)
        if args.strict:
            raise
        write_json(output_path, passthrough_payload(payload, f'codex_error:{type(exc).__name__}'))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
