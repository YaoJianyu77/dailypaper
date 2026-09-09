#!/usr/bin/env python3
"""Shared content repository helpers for the static paper site."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


def get_repo_root(cli_root: str | None = None, script_file: str | None = None) -> Path:
    if cli_root:
        return Path(cli_root).expanduser().resolve()

    candidates = []
    if script_file:
        candidates.append(Path(script_file).resolve())
    candidates.append(Path.cwd().resolve())

    for candidate in candidates:
        current = candidate if candidate.is_dir() else candidate.parent
        for path in [current, *current.parents]:
            if (path / ".git").exists() or (path / "README.md").exists():
                return path

    return Path.cwd().resolve()


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    frontmatter = yaml.safe_load(parts[0][4:]) or {}
    body = parts[1]
    return frontmatter, body


def load_markdown(path: Path) -> Tuple[Dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    return parse_frontmatter(text)


def dump_markdown(frontmatter: Dict[str, Any], body: str) -> str:
    yaml_text = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{yaml_text}\n---\n\n{body.rstrip()}\n"
