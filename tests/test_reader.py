"""Exercise the actual shared reader offline; never run research or publication."""

import mimetypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from site_content import apply_base_url, markdown_parser, read_reports


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, chromium_sandbox=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.daily = self.root / 'content/daily'
        self.daily.mkdir(parents=True)
        self.dist = self.root / 'dist'
        self.base = '/dailypaper'
        self.requests, self.errors = [], []
        self.overrides = {}

    def build(self, root=None):
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_site.py'), '--repo-root', str(root or self.root),
                        '--output-dir', str(self.dist)], check=True, capture_output=True,
                       env={**os.environ, 'SITE_BASE_URL': self.base})

    def page(self):
        context = self.browser.new_context(service_workers='block', accept_downloads=False)
        self.addCleanup(context.close)
        context.set_offline(True)

        def resource(route):
            url = urlparse(route.request.url)
            self.requests.append(url.path)
            if url.netloc != 'dailypaper.invalid' or not url.path.startswith(self.base + '/'):
                self.errors.append('External resource: ' + route.request.url)
                route.abort()
                return
            relative = unquote(url.path[len(self.base) + 1:])
            if relative in self.overrides:
                route.fulfill(**self.overrides[relative])
                return
            path = (self.dist / relative).resolve()
            if not path.is_relative_to(self.dist):
                route.abort()
                return
            if path.is_dir():
                path /= 'index.html'
            status = 200
            if not path.is_file():
                # Match GitHub Pages' single custom 404 fallback.
                path, status = self.dist / '404.html', 404
            route.fulfill(path=str(path), status=status,
                          content_type=mimetypes.guess_type(str(path))[0] or 'text/plain',
                          headers={'Content-Security-Policy': "default-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'"})

        context.route('**/*', resource)
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        return page

    def open(self, page, path):
        page.goto('https://dailypaper.invalid' + self.base + path)

    def test_date_selection_links_back_legacy_redirects_and_mobile_anchor(self):
        for day in ('2026-09-07', '2026-09-08'):
            (self.daily / f'{day}.md').write_text(f'# Report {day}\n\n## Latest 1 — Paper {day}\n\nText for {day}.\n')
        for base in ('', '/dailypaper'):
            with self.subTest(base=base):
                self.base = base
                self.build()
                page = self.page()
                self.open(page, '/')
                page.get_by_role('link', name='Read report').click()
                page.locator('#report-body').wait_for()
                self.assertIn('date=2026-09-08', page.url)
                page.locator('#report-date').select_option('2026-09-07')
                page.locator('#paper-1 h2').get_by_text('Paper 2026-09-07', exact=True).wait_for()
                page.go_back()
                page.locator('#paper-1 h2').get_by_text('Paper 2026-09-08', exact=True).wait_for()
                page.get_by_role('link', name='Older report', exact=False).click()
                page.locator('#paper-1 h2').get_by_text('Paper 2026-09-07', exact=True).wait_for()
                page.get_by_role('link', name='Newer report', exact=False).click()
                page.locator('#report-body').wait_for()
                page.set_viewport_size({'width': 390, 'height': 850})
                for suffix in ('/', '/index.html', ''):
                    self.open(page, f'/daily/2026-09-07{suffix}#paper-1')
                    page.wait_for_url('**/reader/?date=2026-09-07#paper-1')
                    page.locator('#report-body').wait_for()
                    self.assertFalse(page.locator('.toc details').evaluate('e => e.open'))
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                self.open(page, '/archive/')
                page.locator('#archive-search').fill('2026-09-07')
                self.assertEqual(page.locator('[data-report]:visible').count(), 1)
                page.locator('.archive-row:visible').click()
                page.locator('#report-body').wait_for()
                self.assertIn('date=2026-09-07', page.url)
        self.assertIn('/dailypaper/reports/2026-09-08.md', self.requests)
        self.assertEqual(self.errors, [])

    def test_missing_dates_download_failures_stale_markdown_and_untrusted_text(self):
        (self.daily / '2026-09-08.md').write_text('''---
title: '<img src=x onerror=alert(1)>'
---
# Report

## Latest 1 — Safe paper

<script>window.injected = true</script>

[Unsafe](javascript:alert(1))

[Source](/papers/?a=1&b=2)

| Model | Speed |
| --- | --- |
| A | 2x |
''')
        self.build()
        page = self.page()
        self.open(page, '/reader/')
        page.locator('#report-body').wait_for()
        self.assertEqual(page.locator('#report-body table td').all_text_contents(), ['A', '2x'])
        self.assertEqual(page.locator('#report-body script, #report-body a[href^="javascript:"]').count(), 0)
        self.assertFalse(page.evaluate('!!window.injected'))
        self.assertEqual(page.get_by_role('link', name='Source').get_attribute('href'), '/dailypaper/papers/?a=1&b=2')
        for query in ('2020-01-01', '../../credentials', '<script>alert(1)</script>'):
            self.open(page, '/reader/?date=' + query)
            page.locator('#reader-retry').wait_for()
            self.assertIn('No report was published', page.locator('#reader-status').inner_text())
            self.assertEqual(page.locator('#report-body').count(), 0)
        for override, message in (({'status': 404, 'body': 'missing'}, 'Could not load'),
                                  ({'status': 200, 'body': 'old cached Markdown'}, 'being updated')):
            self.overrides['reports/2026-09-08.md'] = override
            self.open(page, '/reader/?date=2026-09-08')
            page.locator('#reader-retry').wait_for()
            self.assertIn(message, page.locator('#reader-status').inner_text())
        self.overrides.clear()
        page.get_by_role('button', name='Try again').click()
        page.locator('#report-body').wait_for()
        self.assertEqual(self.errors, [])

    def test_every_archive_renders_unchanged_prose_links_tables_and_images(self):
        self.build(ROOT)
        page = self.page()
        # Compare the browser's rendered sections with the existing archive parser,
        # including legacy Chinese reports and the modern frontmatter format.
        signature = '''html => {
          const doc = new DOMParser().parseFromString(html, 'text/html');
          doc.querySelectorAll('.figure-hint').forEach(e => e.remove());
          return {text: doc.body.textContent.replace(/\\s+/g, ' ').trim(),
            images: [...doc.images].map(e => [e.getAttribute('src'), e.alt]),
            links: [...doc.querySelectorAll('a')].map(e => [e.getAttribute('href'), e.textContent]),
            tables: [...doc.querySelectorAll('table')].map(e => e.textContent.replace(/\\s+/g, ' ').trim())};
        }'''
        reports = read_reports(ROOT)
        self.assertEqual(len(list(self.dist.glob('reports/*.md'))), len(reports))
        self.assertFalse((self.dist / 'daily').exists())
        for report in reports:
            with self.subTest(date=report.date):
                self.assertEqual((self.dist / 'reports' / report.source.name).read_bytes(), report.source.read_bytes())
                self.open(page, report.path)
                page.locator('#report-body').wait_for()
                actual = page.locator('#report-body .prose').all_inner_texts()
                sections = [s for s in [report.intro, *(p.body for p in report.papers), report.trends] if s]
                self.assertEqual(len(actual), len(sections))
                for index, section in enumerate(sections):
                    expected = page.evaluate(signature, markdown_parser().render(section))
                    for field in ('images', 'links'):
                        for item in expected[field]:
                            item[0] = apply_base_url(item[0], self.base)
                    rendered = page.evaluate(signature, page.locator('#report-body .prose').nth(index).inner_html())
                    self.assertEqual(rendered, expected)
                page.locator('#report-body img').evaluate_all("images => images.forEach(img => img.loading = 'eager')")
                page.wait_for_function("() => [...document.querySelectorAll('#report-body img')].every(img => img.complete)")
                self.assertTrue(page.locator('#report-body img').evaluate_all('images => images.every(img => img.naturalWidth > 0)'))
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
