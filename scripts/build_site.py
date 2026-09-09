#!/usr/bin/env python3
"""Build the homepage, archive, and one Markdown report reader."""

from __future__ import annotations

import argparse
from collections import defaultdict
import html
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil

from content_store import get_repo_root
from site_content import apply_base_url, read_reports
from report_settings import load_infrastructure, research_topics as load_research_topics


SITE_ASSETS = Path(__file__).resolve().parent / 'site_assets'


def escape(value):
    return html.escape(str(value), quote=True)


def normalize_base_url(value):
    value = (value or '').strip().strip('/')
    return '/' + value if value else ''


def asset_url(name, base_url):
    digest = hashlib.sha256((SITE_ASSETS / name).read_bytes()).hexdigest()[:12]
    return apply_base_url(f'/assets/{name}?v={digest}', base_url)


def load_site_settings(root):
    for name in ('config.yaml', 'config.example.yaml'):
        path = root / name
        if path.is_file():
            return load_infrastructure(root, path)
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
    reader_scripts = ''.join(f'<script defer src="{escape(asset_url(name, base_url))}"></script>'
                             for name in ('vendor/markdown-it.min.js', 'reader.js')) if page_kind in {'report', 'not-found'} else ''
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Daily computer science research reports.">
  <title>{escape(title)} - {escape(site_title)}</title>
  <link rel="stylesheet" href="{escape(asset_url('style.css', base_url))}">
  <script defer src="{escape(asset_url('site.js', base_url))}"></script>
  {reader_scripts}
</head>
<body class="page-{page_kind}" id="top" data-base-url="{escape(base_url)}" data-site-title="{escape(site_title)}">
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


def homepage(reports, base_url, research_topics):
    if not reports:
        return '<section class="empty-state"><p class="eyebrow">DAILYPAPER</p><h1>No report yet</h1><p>Published reports will appear here.</p></section>'
    report = reports[0]
    link = escape(apply_base_url(report.path, base_url))
    subtitle = f'<p class="hero-description">{escape(" · ".join(research_topics))}</p>' if research_topics else ''
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
        <h1>Computer science.</h1>
        {subtitle}
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


def reader_page():
    return '''
    <div class="reader-tools"><label for="report-date">Report date</label><select id="report-date" disabled aria-label="Choose report date"><option>Loading…</option></select></div>
    <div id="reader-status" class="empty-state" role="status" aria-live="polite"><h1>Loading report…</h1></div>
    <noscript><p>This reader needs JavaScript to display the selected report.</p></noscript>
    <div id="reader-content" aria-busy="true"></div>
    <dialog id="figure-dialog" aria-label="Enlarged paper figure">
      <div class="dialog-toolbar">
        <button class="dialog-fit" type="button">Fit</button>
        <button class="dialog-actual" type="button" aria-label="Show original image size">100%</button>
        <button class="dialog-smaller" type="button" aria-label="Zoom out">−</button>
        <button class="dialog-larger" type="button" aria-label="Zoom in">+</button>
        <output class="dialog-scale" aria-label="Zoom level" aria-live="polite">100%</output>
        <button class="dialog-close" type="button" aria-label="Close enlarged figure">×</button>
      </div>
      <div class="figure-viewport" tabindex="0" aria-label="Figure; scroll to explore"><img alt=""></div>
      <p class="dialog-caption"></p>
    </dialog>'''


def copy_assets(root, output):
    for name in ('style.css', 'site.js', 'reader.js'):
        shutil.copy2(SITE_ASSETS / name, output / 'assets' / name)
    shutil.copytree(SITE_ASSETS / 'vendor', output / 'assets/vendor')
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

    write(Path(), 'Computer science', homepage(reports, base, load_research_topics(root)), 'home')
    write(Path('archive'), 'Archive', archive_page(reports, base), 'archive')
    write(Path('reader'), 'Read report', reader_page(), 'report')
    (output / '404.html').write_text(layout(site_title, 'Page not found',
        '<section class="empty-state"><h1>Page not found</h1><p>Find a report in the archive.</p>'
        f'<a class="button" href="{escape(apply_base_url("/archive/", base))}">Browse archive →</a></section>',
        base, 'not-found'), encoding='utf-8')
    (output / 'reports').mkdir()
    manifest = []
    for report in reports:
        raw = report.source.read_bytes()
        (output / 'reports' / report.source.name).write_bytes(raw)
        manifest.append({'date': report.date.isoformat(), 'title': report.title,
                         'formatted_date': formatted_date(report), 'weekday': report.date.strftime('%A'),
                         'reading_minutes': reading_time(report), 'sha256': hashlib.sha256(raw).hexdigest(),
                         'papers': [{'title': p.title, 'short_title': p.short_title,
                                     'category': p.category, 'anchor': p.anchor} for p in report.papers],
                         'trends_title': report.trends_title, 'source_spans': report.source_spans})
    (output / 'reports/index.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
    copy_assets(root, output)
    print(f'Built one reader, {len(reports)} Markdown reports, homepage, and archive in {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
