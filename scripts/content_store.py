#!/usr/bin/env python3
"""Shared content repository helpers for the static paper site."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

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


def get_content_root(repo_root: Path) -> Path:
    return repo_root / "content"


def get_papers_root(repo_root: Path) -> Path:
    return get_content_root(repo_root) / "papers"


def get_deep_dives_root(repo_root: Path) -> Path:
    return get_content_root(repo_root) / "deep-dives"


def get_asset_root(repo_root: Path) -> Path:
    return get_content_root(repo_root) / "assets"


def get_paper_assets_root(repo_root: Path) -> Path:
    return get_asset_root(repo_root) / "papers"


def get_daily_root(repo_root: Path) -> Path:
    return get_content_root(repo_root) / "daily"


def get_meta_root(repo_root: Path) -> Path:
    return get_content_root(repo_root) / "meta"


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "paper"


def safe_filename(value: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', '_', value).strip() or "paper"


def paper_slug(paper_id: str, title: str) -> str:
    pid = paper_id.replace("arXiv:", "").strip()
    base = pid if pid else title
    slug = slugify(base)
    if pid and title:
        title_slug = slugify(title)
        if title_slug and title_slug != slug:
            return f"{slug}-{title_slug[:48]}".strip("-")
    return slug


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


def write_markdown(path: Path, frontmatter: Dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_markdown(frontmatter, body), encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def relative_site_url(path: Path, repo_root: Path) -> str:
    rel = path.relative_to(get_content_root(repo_root)).as_posix()
    if rel.endswith("index.md"):
        rel = rel[:-8]
    elif rel.endswith(".md"):
        rel = rel[:-3] + "/"
    return "/" + rel.strip("/") + "/"


def iter_markdown_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.md"))


def iter_paper_note_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    # Paper pages live at content/papers/<slug>/index.md. Nested manifests such
    # as content/papers/<slug>/images/index.md should not be treated as papers.
    return sorted(root.glob("*/index.md"))


def iter_deep_dive_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("*/index.md"))
