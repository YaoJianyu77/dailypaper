#!/usr/bin/env python3
"""Build the homepage, searchable archive, and complete report reading pages."""

from __future__ import annotations

import argparse
from collections import defaultdict
import html
import math
import os
from pathlib import Path
import re
import shutil

import yaml

from content_store import get_repo_root
from site_content import Report, apply_base_url, md_to_html, read_reports


SITE_ASSETS = Path(__file__).resolve().parent / 'site_assets'


def escape(value):
    return html.escape(str(value), quote=True)


def normalize_base_url(value):
    value = (value or '').strip().strip('/')
    return '/' + value if value else ''


def load_site_settings(root):
    for name in ('config.yaml', 'config.example.yaml'):
        path = root / name
        if path.is_file():
            return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    return {}


def formatted_date(report):
    return f'{report.date:%B} {report.date.day}, {report.date.year}'


def report_count(report):
    count = len(report.papers)
    return f'{count} paper' + ('' if count == 1 else 's')


def reading_time(report):
    text = ' '.join([report.intro, report.trends, *(p.body for p in report.papers)])
    words = len(re.findall(r'\b[A-Za-z0-9]+\b', text))
    characters = len(re.findall(r'[\u4e00-\u9fff]', text))
    return max(1, math.ceil(words / 220 + characters / 400))


def layout(site_title, title, content, base_url, page_kind):
    home_url = escape(apply_base_url('/', base_url))
    archive_url = escape(apply_base_url('/archive/', base_url))
    current = ' aria-current="page"' if page_kind == 'archive' else ''
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Research notes on AI, machine learning, and computer systems.">
  <title>{escape(title)} - {escape(site_title)}</title>
  <link rel="stylesheet" href="{escape(apply_base_url('/assets/style.css', base_url))}">
  <script defer src="{escape(apply_base_url('/assets/site.js', base_url))}"></script>
</head>
<body class="page-{page_kind}" id="top">
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{home_url}" aria-label="{escape(site_title)} home">
        <span class="brand-mark" aria-hidden="true">dp<span>.</span></span>
        <span class="brand-name">{escape(site_title)}<small>RESEARCH NOTES</small></span>
      </a>
      <nav aria-label="Main navigation">
        <a class="archive-nav" href="{archive_url}"{current}>Archive <span aria-hidden="true">↗</span></a>
      </nav>
    </div>
    <div class="reading-progress" aria-hidden="true"><span></span></div>
  </header>
  <main id="main" class="site-main">{content}</main>
</body>
</html>
'''


def category_badge(category):
    return f'<span class="badge {"badge-classic" if category == "Classic" else ""}">{escape(category)}</span>'


def homepage(reports, base_url):
    if not reports:
        return '<section class="empty-state"><p class="eyebrow">DAILYPAPER</p><h1>No report yet</h1><p>Published reports will appear here.</p></section>'
    report = reports[0]
    link = escape(apply_base_url(report.path, base_url))
    previews = []
    for index, paper in enumerate(report.papers, 1):
        excerpt = f'<p>{escape(paper.excerpt)}</p>' if paper.excerpt else ''
        previews.append(f'''<li>
          <a class="paper-preview" href="{link}#{paper.anchor}">
            <span class="preview-number">{index:02}</span>
            <div>{category_badge(paper.category)}<h3>{escape(paper.title)}</h3>{excerpt}</div>
            <span class="preview-arrow" aria-hidden="true">↗</span>
          </a>
        </li>''')
    return f'''
    <section class="home-hero">
      <div class="hero-copy"><p class="eyebrow">DAILY RESEARCH NOTES</p>
        <h1>AI &amp; computer science.<br><em>A closer look.</em></h1>
        <p class="hero-description">Papers and ideas across AI, machine learning, and computer systems.</p>
      </div>
      <div class="issue-cover">
        <p class="eyebrow">CURRENT REPORT</p>
        <time datetime="{report.date}"><span>{report.date:%B}</span><strong>{report.date.day:02}</strong><span>{report.date:%Y · %A}</span></time>
        <div class="cover-meta">{report_count(report)} <span>·</span> ~{reading_time(report)} min read</div>
        <a class="button button-primary" href="{link}">Read report <span aria-hidden="true">→</span></a>
      </div>
    </section>
    <section class="issue-preview" aria-labelledby="issue-heading">
      <div class="section-heading"><div><p class="eyebrow">{formatted_date(report)}</p><h2 id="issue-heading">Featured papers</h2></div><span class="count-label">{report_count(report)}</span></div>
      <ol class="paper-preview-list">{''.join(previews)}</ol>
    </section>'''


def archive_page(reports, base_url):
    months = defaultdict(list)
    for report in reports:
        months[report.month].append(report)
    options = ['<option value="">All months</option>']
    groups = []
    for month, entries in months.items():
        label = entries[0].date.strftime('%B %Y')
        options.append(f'<option value="{month}">{label}</option>')
        rows = []
        for report in entries:
            titles = ' / '.join(p.short_title for p in report.papers[:3]) or report.title
            more = f' +{len(report.papers) - 3} more' if len(report.papers) > 3 else ''
            rows.append(f'''<li data-report data-month="{month}" data-search="{escape(report.search_text)}">
              <a class="archive-row" href="{escape(apply_base_url(report.path, base_url))}">
                <time class="date-tile" datetime="{report.date}"><span>{report.date:%b}</span><strong>{report.date.day:02}</strong></time>
                <div class="archive-row-copy"><h3>{formatted_date(report)}</h3><p>{escape(titles)}<span class="more-label">{more}</span></p></div>
                <span class="row-count">{report_count(report)}</span><span class="row-arrow" aria-hidden="true">↗</span>
              </a>
            </li>''')
        groups.append(f'<section class="archive-month" data-month-group><h2>{label}</h2><ul>{"".join(rows)}</ul></section>')
    return f'''
    <header class="page-heading"><p class="eyebrow">THE COLLECTION</p><h1>The archive<span>.</span></h1><p>Browse past reports. Find a paper, a topic, or a date.</p></header>
    <section class="archive-tools" data-enhanced hidden aria-label="Filter reports">
      <div class="search-field"><label for="archive-search">Search the archive</label><div class="input-wrap"><span aria-hidden="true">⌕</span><input id="archive-search" type="search" placeholder="Paper title, keyword, or date…" autocomplete="off" aria-controls="archive-results"></div></div>
      <div class="month-field"><label for="archive-month">Month</label><select id="archive-month" aria-controls="archive-results">{''.join(options)}</select></div>
      <button type="button" class="button button-quiet" id="reset-filters" hidden>Clear filters</button>
    </section>
    <div class="archive-summary"><p id="result-count" role="status" aria-live="polite">{len(reports)} {'report' if len(reports) == 1 else 'reports'}</p><span>Newest first</span></div>
    <div id="archive-results">{''.join(groups)}</div>
    <div class="empty-state" id="no-results" hidden><h2>No matching reports</h2><p>Try another paper title, keyword, or month.</p></div>'''


def report_page(report: Report, older, newer, base_url):
    toc = []
    papers = []
    for index, paper in enumerate(report.papers, 1):
        toc.append(f'<li><a href="#{paper.anchor}"><span>{index:02}</span>{escape(paper.short_title)}</a></li>')
        papers.append(f'''<section class="paper-section" id="{paper.anchor}">
          <header class="paper-heading"><div class="paper-kicker"><span class="paper-number">{index:02}</span>{category_badge(paper.category)}</div><h2>{escape(paper.title)}</h2></header>
          <div class="prose">{md_to_html(paper.body, base_url)}</div>
        </section>''')
    if report.trends:
        toc.append('<li><a href="#research-trends"><span>↳</span>Research trends</a></li>')
        papers.append(f'<section class="trends-section" id="research-trends"><p class="eyebrow">CONNECTING THE PAPERS</p><h2>{escape(report.trends_title)}</h2><div class="prose">{md_to_html(report.trends, base_url)}</div></section>')
    intro = ''
    if report.intro:
        rendered = md_to_html(report.intro, base_url)
        if re.search(r'Run ID|Permanent history|执行日期|归档位置', report.intro):
            intro = f'<details class="report-notes"><summary>Publication &amp; verification notes <span aria-hidden="true">+</span></summary><div class="prose">{rendered}</div></details>'
        else:
            intro = f'<div class="report-intro prose">{rendered}</div>'
    navigation = []
    for neighbor, label, arrow in ((older, 'Older report', '←'), (newer, 'Newer report', '→')):
        if neighbor:
            navigation.append(f'<a class="issue-neighbor" href="{escape(apply_base_url(neighbor.path, base_url))}"><span>{label} {arrow}</span><strong>{formatted_date(neighbor)}</strong></a>')
    contents = f'<aside class="toc"><details open><summary>In this report <span>{len(report.papers):02}</span></summary><nav aria-label="Report contents"><ol>{"".join(toc)}</ol></nav></details><a class="back-top" href="#top">Back to top ↑</a></aside>' if toc else ''
    return f'''
    <header class="report-header"><p class="eyebrow">DAILY BRIEFING <span>/</span> {report.date:%A}</p><h1>{formatted_date(report)}</h1><div class="report-meta"><span>{report_count(report)}</span><span>~{reading_time(report)} min read</span></div></header>
    <div class="reader-layout">{contents}<article id="report-body">{intro}{''.join(papers)}<nav class="issue-pagination" aria-label="Adjacent reports">{''.join(navigation)}</nav></article></div>
    <dialog id="figure-dialog" aria-label="Enlarged paper figure"><button class="dialog-close" type="button" aria-label="Close enlarged figure">×</button><img alt=""><p></p></dialog>'''


def copy_assets(root, output):
    for name in ('style.css', 'site.js'):
        shutil.copy2(SITE_ASSETS / name, output / 'assets' / name)
    for source_root, target_root in ((root / 'content/assets/papers', output / 'assets/papers'),
                                     (root / 'content/papers', output / 'papers')):
        for directory in source_root.glob('*/images'):
            shutil.copytree(directory, target_root / directory.parent.name / 'images',
                            ignore=shutil.ignore_patterns('*.md'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root')
    parser.add_argument('--output-dir', default='dist')
    args = parser.parse_args()
    root = get_repo_root(args.repo_root, __file__)
    settings = load_site_settings(root).get('site', {})
    site_title = os.environ.get('SITE_TITLE', settings.get('title', 'DailyPaper'))
    base = normalize_base_url(os.environ.get('SITE_BASE_URL', settings.get('base_url', '')))
    output = Path(args.output_dir)
    if not output.is_absolute():
        output = root / output
    reports = read_reports(root)
    if output.exists():
        shutil.rmtree(output)
    (output / 'assets').mkdir(parents=True)
    (output / '.nojekyll').write_text('')

    def write(path, title, content, kind):
        target = output / path / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(layout(site_title, title, content, base, kind), encoding='utf-8')

    write(Path(), 'AI & Computer Science Research', homepage(reports, base), 'home')
    write(Path('archive'), 'Archive', archive_page(reports, base), 'archive')
    for index, report in enumerate(reports):
        older = reports[index + 1] if index + 1 < len(reports) else None
        newer = reports[index - 1] if index else None
        write(Path('daily') / report.date.isoformat(), report.title,
              report_page(report, older, newer, base), 'report')
    copy_assets(root, output)
    print(f'Built {len(reports)} reports, homepage, and archive in {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
