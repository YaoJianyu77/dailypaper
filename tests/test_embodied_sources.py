"""Offline coverage for robotics/ML publication sources added to DailyPaper."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))

from codex_enrich import CodexBackend
from daily_pipeline import needs_web_discovery
from paper_sources import EvidenceError, PageMetadata, Sources, label_matches, official_landing


class FixtureSources(Sources):
    def __init__(self, files=None, openreview=None):
        super().__init__({'search': {'request_interval_seconds': 0}})
        self.files = files or {}
        self.openreview = openreview

    def get(self, url, params=None, *, max_bytes=8_000_000):
        if url == 'https://api2.openreview.net/notes':
            raw = json.dumps(self.openreview).encode()
            return raw, url + '?id=' + params['id']
        raw = self.files[url]
        if len(raw) > max_bytes:
            raise EvidenceError('Fixture exceeds max_bytes')
        return raw, url


class EmbodiedSourceTests(unittest.TestCase):
    def test_production_always_supplements_sparse_indexes_with_topic_search(self):
        quotas = {'latest': 4, 'classic': 1}
        full = {'latest': 4, 'classic': 1}
        production = CodexBackend.__new__(CodexBackend)
        self.assertTrue(needs_web_discovery(production, full, quotas))
        self.assertFalse(needs_web_discovery(object(), full, quotas))
        self.assertTrue(needs_web_discovery(object(), {'latest': 3, 'classic': 1}, quotas))
        self.assertFalse(needs_web_discovery(None, {'latest': 0, 'classic': 0}, quotas))

    def test_robotics_journal_spelling_aliases(self):
        self.assertTrue(label_matches('IEEE Trans. Robotics', 'IEEE T-RO / IEEE Transactions on Robotics'))
        self.assertTrue(label_matches('IEEE Robotics Autom. Lett.', 'IEEE RA-L / IEEE Robotics and Automation Letters'))
        self.assertTrue(label_matches('Int. J. Robotics Res.', 'IJRR / The International Journal of Robotics Research'))
        self.assertTrue(label_matches('NIPS', 'NeurIPS / Advances in Neural Information Processing Systems'))

    def test_new_official_hosts_still_require_venue_binding(self):
        page = PageMetadata(
            '<meta name="citation_conference_title" content="CVPR">'
            '<meta name="citation_title" content="Fixture">')
        self.assertTrue(official_landing('https://openaccess.thecvf.com/content/CVPR2026/html/fixture.html', page, 'CVPR'))
        self.assertFalse(official_landing('https://openaccess.thecvf.com.example/content/CVPR2026/html/fixture.html', page, 'CVPR'))
        self.assertFalse(official_landing('https://openaccess.thecvf.com/content/CVPR2026/html/fixture.html', page, 'ICCV'))

    def test_pmlr_article_uses_exact_volume_publication_date(self):
        article = 'https://proceedings.mlr.press/v999/fixture26a.html'
        volume = 'https://proceedings.mlr.press/v999/'
        pdf = 'https://raw.githubusercontent.com/mlresearch/v999/main/assets/fixture26a/fixture26a.pdf'
        files = {
            article: (
                '<meta name="citation_title" content="Embodied Fixture">'
                '<meta name="citation_pdf_url" content="' + pdf + '">'
                '<p>Proceedings of The 9th Conference on Robot Learning, PMLR 999:1-20, 2026.</p>'
            ).encode(),
            volume: (
                '<title>Proceedings of Machine Learning Research | Proceedings of The 9th Conference on Robot Learning '
                'Published as Volume 999 by the Proceedings of Machine Learning Research on 15 May 2026.</title>'
                '<h2>Volume 999: Conference on Robot Learning, 10-12 May 2026, Test City</h2>'
                '<p>Embodied Fixture</p>'
            ).encode(),
        }
        sources = FixtureSources(files)
        candidate = {'title': 'Embodied Fixture', 'venue': 'CoRL / Conference on Robot Learning',
                     'doi': '', 'source_urls': [article], 'official_urls': [article], 'pdf_urls': []}

        verified = sources.verify_publication(candidate)

        self.assertEqual(verified['publication_date'], '2026-05-15')
        self.assertIn(pdf, verified['pdf_urls'])
        evidence = next(item for item in verified['publication_evidence'] if item['kind'] == 'pmlr-volume-publication')
        self.assertEqual(evidence['volume'], '999')
        self.assertEqual(evidence['url'], volume)

    def test_pmlr_volume_must_match_configured_venue(self):
        article = 'https://proceedings.mlr.press/v999/fixture26a.html'
        files = {
            article: ('<meta name="citation_title" content="Embodied Fixture">'
                      '<p>Proceedings of The 9th Conference on Robot Learning, PMLR 999:1-20, 2026.</p>').encode(),
            'https://proceedings.mlr.press/v999/': (
                '<title>Published as Volume 999 by the Proceedings of Machine Learning Research on 15 May 2026.</title>'
                '<h2>Volume 999: Conference on Robot Learning</h2><p>Embodied Fixture</p>').encode(),
        }
        sources = FixtureSources(files)
        candidate = {'title': 'Embodied Fixture', 'venue': 'ICML / International Conference on Machine Learning',
                     'doi': '', 'source_urls': [article], 'official_urls': [article], 'pdf_urls': []}
        with self.assertRaisesRegex(EvidenceError, 'No exact official publication date'):
            sources.verify_publication(candidate)

    def test_openreview_uses_accepted_note_pdate_not_submission_time(self):
        forum = 'https://openreview.net/forum?id=Accepted123'
        pdate = int(datetime(2026, 4, 24, 18, 30, tzinfo=timezone.utc).timestamp() * 1000)
        payload = {'notes': [{'id': 'Accepted123', 'pdate': pdate,
                             'content': {'title': {'value': 'ICLR Fixture'},
                                         'venueid': {'value': 'ICLR.cc/2026/Conference'},
                                         'venue': {'value': 'ICLR 2026 Poster'}}}]}
        sources = FixtureSources({forum: b'<html><body>OpenReview forum</body></html>'}, payload)
        candidate = {'title': 'ICLR Fixture', 'venue': 'ICLR / International Conference on Learning Representations',
                     'doi': '', 'source_urls': [forum], 'official_urls': [forum], 'pdf_urls': []}

        verified = sources.verify_publication(candidate)

        self.assertEqual(verified['publication_date'], '2026-04-24')
        self.assertIn('https://openreview.net/pdf?id=Accepted123', verified['pdf_urls'])
        evidence = next(item for item in verified['publication_evidence'] if item['kind'] == 'openreview-accepted-note')
        self.assertEqual(evidence['pdate'], pdate)

    def test_openreview_workshop_or_unaccepted_note_cannot_pass(self):
        forum = 'https://openreview.net/forum?id=Workshop123'
        pdate = int(datetime(2026, 4, 24, tzinfo=timezone.utc).timestamp() * 1000)
        for venue_id, published in [('ICLR.cc/2026/Workshop/EmbodiedAI', pdate),
                                    ('ICLR.cc/2026/Conference', None)]:
            payload = {'notes': [{'id': 'Workshop123', 'pdate': published,
                                 'content': {'title': {'value': 'ICLR Fixture'},
                                             'venueid': {'value': venue_id},
                                             'venue': {'value': 'ICLR 2026'}}}]}
            sources = FixtureSources({forum: b'<html></html>'}, payload)
            candidate = {'title': 'ICLR Fixture', 'venue': 'ICLR / International Conference on Learning Representations',
                         'doi': '', 'source_urls': [forum], 'official_urls': [forum], 'pdf_urls': []}
            with self.subTest(venue_id=venue_id, published=published):
                with self.assertRaisesRegex(EvidenceError, 'No exact official publication date'):
                    sources.verify_publication(candidate)


if __name__ == '__main__':
    unittest.main()
