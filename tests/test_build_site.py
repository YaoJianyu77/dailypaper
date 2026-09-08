"""Regression checks for publishing reports without running the local publisher."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from site_content import md_to_html, read_report, read_reports, markdown_parser
from content_store import load_markdown


BUILD_SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'build_site.py'


class BuildSiteTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.daily = self.root / 'content' / 'daily'
        self.meta = self.root / 'content' / 'meta'
        self.daily.mkdir(parents=True)
        self.meta.mkdir(parents=True)
        self.output = self.root / 'dist'

    def build(self, base_url='/dailypaper'):
        subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), '--repo-root', str(self.root)],
            env={**os.environ, 'SITE_BASE_URL': base_url, 'SITE_TITLE': 'DailyPaper'},
            check=True,
            capture_output=True,
            text=True,
        )

    def test_directly_archived_reports_override_stale_navigation(self):
        old_report = '---\ntitle: Earlier report\n---\n\n# Earlier report\n'
        new_report = '# Newly archived report\n\nLatest paper analysis.\n'
        (self.daily / '2026-05-04.md').write_text(old_report)
        (self.daily / '2026-09-07.md').write_text(new_report)
        stale = {'date': '2026-05-04', 'path': '/daily/2026-05-04/'}
        (self.meta / 'latest.json').write_text(json.dumps(stale))
        (self.meta / 'daily-index.json').write_text(json.dumps([stale]))
        source_files = {p: p.read_bytes() for p in (self.root / 'content').rglob('*') if p.is_file()}

        self.build()

        home = (self.output / 'index.html').read_text()
        archive = (self.output / 'archive' / 'index.html').read_text()
        reader = (self.output / 'daily/2026-09-07/index.html').read_text()
        self.assertIn('<title>Newly archived report - DailyPaper</title>', reader)
        self.assertIn('Latest paper analysis.', reader)
        self.assertIn('href="/dailypaper/daily/2026-09-07/">Read this issue', home)
        self.assertNotIn('href="/dailypaper/daily/2026-05-04/">Read this issue', home)
        self.assertNotIn('Latest report', home + archive + reader)
        self.assertEqual(archive.count('href="/dailypaper/daily/2026-09-07/"'), 1)
        self.assertEqual(archive.count('href="/dailypaper/daily/2026-05-04/"'), 1)
        self.assertLess(archive.index('datetime="2026-09-07"'), archive.index('datetime="2026-05-04"'))
        for date in ['2026-05-04', '2026-09-07']:
            self.assertTrue((self.output / 'daily' / date / 'index.html').is_file())
        for path, before in source_files.items():
            self.assertEqual(path.read_bytes(), before)

    def test_report_without_metadata_builds_at_site_root(self):
        (self.daily / '2026-09-07.md').write_text(
            '---\ntitle: Title from frontmatter\n---\n\n# Body heading\n'
        )
        self.build(base_url='')
        home = (self.output / 'index.html').read_text()
        reader = (self.output / 'daily/2026-09-07/index.html').read_text()
        self.assertIn('<title>Title from frontmatter - DailyPaper</title>', reader)
        self.assertIn('href="/daily/2026-09-07/">Read this issue', home)

    def test_deleted_reports_do_not_survive_in_navigation(self):
        stale = {'date': '2026-05-04', 'path': '/daily/2026-05-04/'}
        (self.meta / 'latest.json').write_text(json.dumps(stale))
        (self.meta / 'daily-index.json').write_text(json.dumps([stale]))
        self.build()
        home = (self.output / 'index.html').read_text()
        archive = (self.output / 'archive' / 'index.html').read_text()
        self.assertIn('No report yet', home)
        self.assertNotIn('/daily/2026-05-04/', home)
        self.assertNotIn('/daily/2026-05-04/', archive)

    def test_paper_directory_does_not_treat_analysis_subheadings_as_papers(self):
        path = self.daily / '2026-09-07.md'
        path.write_text('''# Report

**Run ID:** test.

## Latest 1 — Example: GPU serving

Published metadata.

### 1. Paper in brief

This is the complete summary.

### 2. Problem and core insight

```
### 3. This is code, not another paper
```

## Classic — Earlier system

Classic evidence.

# Clear Research Trends in Today's Papers

Evidence connecting both papers.
''')
        report = read_report(path)
        self.assertEqual([p.title for p in report.papers], ['Example: GPU serving', 'Earlier system'])
        self.assertEqual([p.category for p in report.papers], ['Latest', 'Classic'])
        self.assertIn('This is code', report.papers[0].body)
        self.assertNotIn('Evidence connecting', report.papers[-1].body)
        self.build()
        reader = (self.output / 'daily/2026-09-07/index.html').read_text()
        home = (self.output / 'index.html').read_text()
        for anchor in ('paper-1', 'paper-2'):
            self.assertIn(f'id="{anchor}"', reader)
            self.assertIn(f'href="#{anchor}"', reader)
            self.assertIn(f'/daily/2026-09-07/#{anchor}', home)
        self.assertIn('id="research-trends"', reader)

    def test_markdown_preserves_link_queries_and_renders_tables(self):
        rendered = md_to_html('''[Source](/papers/?a=1&b=2)

![A & B](/assets/figure.png)

*Figure 1. Caption.*

| Model | Throughput |
| --- | --- |
| A | 2x |

<script>alert(1)</script>
''', '/dailypaper')
        self.assertIn('href="/dailypaper/papers/?a=1&amp;b=2"', rendered)
        self.assertNotIn('&amp;amp;', rendered)
        self.assertIn('src="/dailypaper/assets/figure.png"', rendered)
        self.assertIn('class="figure-caption"', rendered)
        self.assertIn('<table>', rendered)
        self.assertIn('<td>2x</td>', rendered)
        self.assertNotIn('<script>', rendered)

    def test_all_archived_prose_and_figures_survive_report_splitting(self):
        def content_blocks(text):
            tokens = markdown_parser().parse(text)
            return Counter(token.content for i, token in enumerate(tokens)
                           if token.type == 'inline' and tokens[i - 1].type != 'heading_open')
        for report in read_reports(BUILD_SCRIPT.parent.parent):
            with self.subTest(date=report.date):
                original = content_blocks(load_markdown(report.source)[1])
                extracted = content_blocks(report.intro)
                for paper in report.papers:
                    extracted.update(content_blocks(paper.body))
                extracted.update(content_blocks(report.trends))
                self.assertEqual(original, extracted)


if __name__ == '__main__':
    unittest.main()
