"""Regression checks for publishing reports without running the local publisher."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


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
        self.assertIn('<title>Newly archived report - DailyPaper</title>', home)
        self.assertIn('Latest paper analysis.', home)
        self.assertIn('href="/dailypaper/daily/2026-09-07/">Latest report</a>', home)
        self.assertNotIn('href="/dailypaper/daily/2026-05-04/">Latest report</a>', home)
        self.assertIn('href="/dailypaper/daily/2026-09-07/">2026-09-07</a>', archive)
        self.assertIn('href="/dailypaper/daily/2026-05-04/">2026-05-04</a>', archive)
        self.assertEqual(archive.count('>2026-09-07</a>'), 1)
        self.assertEqual(archive.count('>2026-05-04</a>'), 1)
        self.assertLess(archive.index('>2026-09-07</a>'), archive.index('>2026-05-04</a>'))
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
        self.assertIn('<title>Title from frontmatter - DailyPaper</title>', home)
        self.assertIn('href="/daily/2026-09-07/">Latest report</a>', home)

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


if __name__ == '__main__':
    unittest.main()
