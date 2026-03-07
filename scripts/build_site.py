#!/usr/bin/env python3
"""Build a static website from repository content/."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from content_store import get_content_root, get_daily_root, get_meta_root, get_papers_root, get_repo_root, iter_markdown_files, load_markdown, read_json

DEFAULT_SITE_TITLE = 'DailyPaper'

CSS = """
:root {
  --bg: #f4efe6;
  --panel: rgba(255, 252, 245, 0.92);
  --ink: #1f1c16;
  --muted: #6a5f50;
  --accent: #af3f2f;
  --accent-2: #1d6b63;
  --line: rgba(31, 28, 22, 0.12);
  --shadow: 0 20px 50px rgba(45, 28, 16, 0.12);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(175,63,47,0.16), transparent 30%),
    radial-gradient(circle at top right, rgba(29,107,99,0.14), transparent 28%),
    linear-gradient(180deg, #f8f3eb 0%, #f0e8dd 100%);
  font-family: "IBM Plex Sans", "Avenir Next", "Segoe UI", sans-serif;
}
a { color: var(--accent); }
a:hover { color: var(--accent-2); }
.shell {
  width: min(1100px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 28px 0 64px;
}
.hero {
  border: 1px solid var(--line);
  border-radius: 28px;
  padding: 28px;
  background: linear-gradient(135deg, rgba(255,255,255,0.72), rgba(255,245,233,0.92));
  box-shadow: var(--shadow);
}
.hero h1 {
  margin: 0;
  font-size: clamp(2.4rem, 5vw, 4.4rem);
  line-height: 0.95;
  letter-spacing: -0.05em;
}
.hero p {
  max-width: 66ch;
  color: var(--muted);
  font-size: 1rem;
}
.nav {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 18px;
}
.nav a, .pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 10px 16px;
  background: rgba(255,255,255,0.7);
  color: var(--ink);
}
.grid {
  display: grid;
  grid-template-columns: 2.2fr 1fr;
  gap: 24px;
  margin-top: 24px;
}
.card {
  border: 1px solid var(--line);
  border-radius: 24px;
  background: var(--panel);
  box-shadow: var(--shadow);
  padding: 24px;
}
.card h2, .card h3 { margin-top: 0; }
.article {
  font-family: "Iowan Old Style", "Source Serif 4", Georgia, serif;
  line-height: 1.75;
  font-size: 1.05rem;
}
.article img { max-width: 100%; border-radius: 18px; }
.article pre, .article code {
  font-family: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
}
.article pre {
  overflow-x: auto;
  padding: 14px;
  border-radius: 16px;
  background: #201b17;
  color: #f8efe1;
}
.list { list-style: none; margin: 0; padding: 0; }
.list li + li { margin-top: 12px; }
.meta {
  color: var(--muted);
  font-size: 0.95rem;
}
.footer {
  margin-top: 32px;
  color: var(--muted);
  font-size: 0.92rem;
}
@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
  .hero { padding: 22px; }
}
"""


def load_site_settings(repo_root: Path) -> Dict:
    config_path = repo_root / 'config.yaml'
    if not config_path.exists():
        config_path = repo_root / 'config.example.yaml'

    if not config_path.exists():
        return {}

    return yaml.safe_load(config_path.read_text(encoding='utf-8')) or {}


def normalize_base_url(value: str) -> str:
    value = (value or '').strip()
    if not value or value == '/':
        return ''
    if not value.startswith('/'):
        value = '/' + value
    return value.rstrip('/')


def apply_base_url(url: str, base_url: str) -> str:
    if not url:
        return url
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url) or url.startswith('//'):
        return url
    if url == '/':
        return f'{base_url}/' if base_url else '/'
    if url.startswith('/'):
        return f'{base_url}{url}' if base_url else url
    return url


def render_inline(text: str, base_url: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        lambda match: (
            f'<img alt="{html.escape(match.group(1), quote=True)}" '
            f'src="{html.escape(apply_base_url(match.group(2), base_url), quote=True)}">'
        ),
        escaped,
    )
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    escaped = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', escaped)
    escaped = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda match: f'<a href="{html.escape(apply_base_url(match.group(2), base_url), quote=True)}">{match.group(1)}</a>',
        escaped,
    )
    return escaped


def flush_list(buffer: List[str], ordered: bool, base_url: str) -> str:
    if not buffer:
        return ''
    tag = 'ol' if ordered else 'ul'
    items = ''.join(f'<li>{render_inline(item, base_url)}</li>' for item in buffer)
    buffer.clear()
    return f'<{tag}>{items}</{tag}>'


def md_to_html(text: str, base_url: str) -> str:
    html_parts: List[str] = []
    paragraph: List[str] = []
    list_buffer: List[str] = []
    list_ordered = False
    in_code = False
    code_lines: List[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            html_parts.append(f'<p>{render_inline(" ".join(paragraph), base_url)}</p>')
            paragraph.clear()

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if line.startswith('```'):
            flush_paragraph()
            html_parts.append(flush_list(list_buffer, list_ordered, base_url))
            if in_code:
                html_parts.append(f'<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>')
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if not line.strip():
            flush_paragraph()
            html_parts.append(flush_list(list_buffer, list_ordered, base_url))
            continue

        if line.startswith('#'):
            flush_paragraph()
            html_parts.append(flush_list(list_buffer, list_ordered, base_url))
            level = len(line) - len(line.lstrip('#'))
            title = line[level:].strip()
            html_parts.append(f'<h{level}>{render_inline(title, base_url)}</h{level}>')
            continue

        unordered_match = re.match(r'^-\s+(.*)', line)
        ordered_match = re.match(r'^\d+\.\s+(.*)', line)
        if unordered_match:
            flush_paragraph()
            if list_buffer and list_ordered:
                html_parts.append(flush_list(list_buffer, list_ordered, base_url))
            list_ordered = False
            list_buffer.append(unordered_match.group(1))
            continue
        if ordered_match:
            flush_paragraph()
            if list_buffer and not list_ordered:
                html_parts.append(flush_list(list_buffer, list_ordered, base_url))
            list_ordered = True
            list_buffer.append(ordered_match.group(1))
            continue

        paragraph.append(line.strip())

    flush_paragraph()
    html_parts.append(flush_list(list_buffer, list_ordered, base_url))
    if in_code:
        html_parts.append(f'<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>')

    return ''.join(part for part in html_parts if part)


def render_layout(site_title: str, title: str, body_html: str, sidebar_html: str, base_url: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)} - {html.escape(site_title)}</title>
  <link rel=\"stylesheet\" href=\"{apply_base_url('/assets/style.css', base_url)}\">
</head>
<body>
  <main class=\"shell\">
    <section class=\"hero\">
      <h1>{html.escape(site_title)}</h1>
      <p>Automated paper watchtower. Today first, archive second, raw repository history always available.</p>
      <nav class=\"nav\">
        <a href=\"{apply_base_url('/', base_url)}\">Home</a>
        <a href=\"{apply_base_url('/archive/', base_url)}\">Archive</a>
        <a href=\"{apply_base_url('/papers/', base_url)}\">Papers</a>
      </nav>
    </section>
    <section class=\"grid\">
      <article class=\"card article\">{body_html}</article>
      <aside class=\"card\">{sidebar_html}</aside>
    </section>
    <footer class=\"footer\">Generated from the repository content store. Clone the repo to browse and edit the source markdown locally.</footer>
  </main>
</body>
</html>
"""


def copy_asset_dirs(repo_root: Path, dist_root: Path) -> None:
    papers_root = get_papers_root(repo_root)
    for image_dir in papers_root.glob('*/images'):
        target = dist_root / 'papers' / image_dir.parent.name / 'images'
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(image_dir, target)


def build_sidebar(latest: Dict, daily_index: List[Dict], papers: List[Tuple[Dict, Path]], base_url: str) -> str:
    latest_html = '<p class="meta">No daily report published yet.</p>'
    if latest:
        latest_html = f'<p><a href="{apply_base_url(latest["path"], base_url)}">Latest report</a></p><p class="meta">{latest.get("date", "")}</p>'

    archive_items = ''.join(
        f'<li><a href="{apply_base_url(entry["path"], base_url)}">{entry["date"]}</a></li>' for entry in daily_index[:10]
    ) or '<li class="meta">No history yet.</li>'
    paper_item_parts = []
    for frontmatter, path in papers[:12]:
        slug = frontmatter.get('slug', path.parent.name)
        title = html.escape(frontmatter.get('title', path.parent.name))
        href = apply_base_url(f'/papers/{slug}/', base_url)
        paper_item_parts.append(f'<li><a href="{href}">{title}</a></li>')
    paper_items = ''.join(paper_item_parts) or '<li class="meta">No paper pages yet.</li>'

    return (
        '<h2>Latest</h2>'
        f'{latest_html}'
        '<h3>Recent Reports</h3>'
        f'<ul class="list">{archive_items}</ul>'
        '<h3>Paper Pages</h3>'
        f'<ul class="list">{paper_items}</ul>'
    )


def build_page(dist_root: Path, out_path: Path, site_title: str, title: str, body_md: str, sidebar_html: str, base_url: str) -> None:
    html_text = render_layout(site_title, title, md_to_html(body_md, base_url), sidebar_html, base_url)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text, encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Build the static paper site')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    parser.add_argument('--output-dir', default='dist', help='Output directory')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    settings = load_site_settings(repo_root)
    site_settings = settings.get('site', {})
    site_title = os.environ.get('SITE_TITLE', site_settings.get('title', DEFAULT_SITE_TITLE))
    base_url = normalize_base_url(os.environ.get('SITE_BASE_URL', site_settings.get('base_url', '')))

    dist_root = Path(args.output_dir)
    if not dist_root.is_absolute():
        dist_root = repo_root / dist_root

    if dist_root.exists():
        shutil.rmtree(dist_root)
    (dist_root / 'assets').mkdir(parents=True, exist_ok=True)
    (dist_root / 'assets' / 'style.css').write_text(CSS, encoding='utf-8')
    (dist_root / '.nojekyll').write_text('', encoding='utf-8')

    content_root = get_content_root(repo_root)
    latest = read_json(get_meta_root(repo_root) / 'latest.json', {}) or {}
    daily_index = read_json(get_meta_root(repo_root) / 'daily-index.json', []) or []

    paper_docs = []
    for path in iter_markdown_files(get_papers_root(repo_root)):
        frontmatter, body = load_markdown(path)
        paper_docs.append((frontmatter, path))

    sidebar_html = build_sidebar(latest, daily_index, paper_docs, base_url)

    daily_docs = []
    for path in sorted(get_daily_root(repo_root).glob('*.md'), reverse=True):
        frontmatter, body = load_markdown(path)
        daily_docs.append((frontmatter, body, path))
        build_page(dist_root, dist_root / 'daily' / path.stem / 'index.html', site_title, frontmatter.get('title', path.stem), body, sidebar_html, base_url)

    if daily_docs:
        latest_frontmatter, latest_body, _ = daily_docs[0]
        build_page(dist_root, dist_root / 'index.html', site_title, latest_frontmatter.get('title', 'Latest Report'), latest_body, sidebar_html, base_url)
    else:
        build_page(dist_root, dist_root / 'index.html', site_title, 'No Report Yet', '# No report yet\n\nRun the daily workflow to publish the first report.\n', sidebar_html, base_url)

    archive_md = '# Archive\n\n' + '\n'.join(
        f'- [{item["date"]}]({item["path"]})' for item in daily_index
    )
    build_page(dist_root, dist_root / 'archive' / 'index.html', site_title, 'Archive', archive_md, sidebar_html, base_url)

    papers_md = '# Papers\n\n' + '\n'.join(
        f'- [{frontmatter.get("title", path.parent.name)}](/papers/{frontmatter.get("slug", path.parent.name)}/)' for frontmatter, path in paper_docs
    )
    build_page(dist_root, dist_root / 'papers' / 'index.html', site_title, 'Papers', papers_md, sidebar_html, base_url)

    for frontmatter, path in paper_docs:
        _, body = load_markdown(path)
        slug = frontmatter.get('slug', path.parent.name)
        build_page(dist_root, dist_root / 'papers' / slug / 'index.html', site_title, frontmatter.get('title', slug), body, sidebar_html, base_url)

    if content_root.exists():
        copy_asset_dirs(repo_root, dist_root)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
