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
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ai_enrich import build_prompt_payload, get_repo_root, load_config, merge_enrichment, passthrough_payload
from content_store import write_json

logger = logging.getLogger(__name__)


def build_prompt(report_date: str, config: Dict[str, Any], payload: Dict[str, Any]) -> str:
    top_papers = payload.get('top_papers', [])
    ai_settings = config.get('ai', {}) if isinstance(config, dict) else {}
    paper_limit = int(ai_settings.get('codex_paper_limit', len(top_papers) or 10))
    max_abstract_chars = int(ai_settings.get('codex_abstract_chars', 1200))
    prompt_payload = build_prompt_payload(
        report_date,
        config,
        top_papers,
        paper_limit=paper_limit,
        max_abstract_chars=max_abstract_chars,
    )
    return (
        '你是一个严格的研究论文编辑。请只基于给定的论文标题、作者、摘要和评分信息，'
        '输出一个 JSON 对象，不要输出任何额外解释。\n\n'
        '要求：\n'
        '1. 输出语言为简体中文。\n'
        '2. 不要编造实验细节、性能数字、作者背景、代码链接。\n'
        '3. 如果摘要信息不足，要明确写出“摘要没有充分说明”。\n'
        '4. JSON 结构必须匹配提供的 schema。\n'
        '5. `daily_brief.overview_zh` 要像日报编辑写的导语，不要空话。\n'
        '6. 每篇论文的 `summary_zh` 控制在 2 到 4 句。\n'
        '7. `core_contributions`、`why_read`、`risks` 都尽量具体，避免泛泛而谈。\n\n'
        '下面是输入数据：\n'
        + json.dumps(prompt_payload, ensure_ascii=False, indent=2)
    )


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
    prompt = build_prompt(report_date, config, payload)
    schema_path = repo_root / 'scripts' / 'codex_enrich_schema.json'

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
        logger.info('Running local Codex CLI enrichment')
        subprocess.run(cmd, check=True)
        raw_ai = json.loads(tmp_path.read_text(encoding='utf-8'))
        enriched = merge_enrichment(payload, raw_ai, model or 'codex-cli')
        enriched['ai_enrichment']['provider'] = 'codex-cli'
        write_json(output_path, enriched)
        logger.info('Codex enrichment completed')
        return 0
    except Exception as exc:
        logger.exception('Codex enrichment failed: %s', exc)
        if args.strict:
            raise
        write_json(output_path, passthrough_payload(payload, f'codex_error:{type(exc).__name__}'))
        return 0
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == '__main__':
    raise SystemExit(main())
