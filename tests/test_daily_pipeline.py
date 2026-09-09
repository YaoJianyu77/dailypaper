"""Offline integration fixtures: never write production content or call a model."""

import copy
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import fitz
import jsonschema
import requests

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))

from codex_enrich import CodexBackend
from daily_pipeline import discovery, prepare
from paper_sources import EvidenceError, Sources, label_matches, publication_venue_matches
from pipeline_prompts import build_messages, stage_schema
from publish_daily import publish
from recommendation_history import (HISTORY_PATH, HistoryError, assert_unchanged, json_bytes,
                                    identifier_tokens, load_history, match_record, write_history)
from report_settings import SettingsError, calendar_shift, load_infrastructure, load_settings
from report_validation import ValidationError, prepare_visuals, validate_analysis, validate_document, validate_trends
from site_content import read_report

DAY = date(2026, 9, 8)


def review_result():
    checks = ('language', 'topic_fit', 'identity', 'publication', 'full_paper', 'technical_claims',
              'visual_fidelity', 'structure', 'trend_evidence')
    return {'approved': True, 'problems': [],
            **{key: {'passed': True, 'evidence': 'Offline test receipt; no claim of scientific verification.'} for key in checks}}


def analysis_result(document, settings):
    visual = {'kind': 'crop', 'page': 1, 'bbox': [.1, .25, .9, .65], 'label': 'Figure 1',
              'caption': 'Fixture data flow', 'explanation': 'Fixture supports data flow.',
              'caveat': 'Fixture contains synthetic evidence.', 'headers': [], 'rows': []}
    visuals = [copy.deepcopy(visual) for _ in range(min(settings.visual_max, max(settings.visual_min, 2)))]
    if len(visuals) > 1:
        visuals[1].update(kind='table', page=2, label='Table 1', headers=['System', 'Latency (ms)'],
                          rows=[['Baseline', '10'], ['Fixture', '5']])
    target = (settings.summary_min + settings.summary_max) // 2 - len(visuals) * 8
    counts = [(settings.brief_min + settings.brief_max) // 2] + [0] * (len(settings.headings) - 2) + [min(80, settings.assessment_max)]
    remaining = target - sum(counts)
    for index in range(1, len(counts) - 1):
        counts[index] = remaining // (len(counts) - 1 - index)
        remaining -= counts[index]
    return {'document_sha256': document['sha256'], 'read_pages': [p['page'] for p in document['pages']],
            'visual_section': settings.headings[3],
            'visual_labels': {'pdf_page': 'PDF page', 'paraphrased_caption': 'Caption (paraphrased)'},
            'sections': [{'heading': heading, 'text': ' '.join(['Evidence'] * count)} for heading, count in zip(settings.headings, counts)],
            'insights': [{'text': 'Fixture only', 'page': 1}], 'findings': [{'text': 'Fixture only', 'page': 2}], 'visuals': visuals}


class FixtureSources(Sources):
    """Use the real publisher parser and complete-PDF reader with local bytes."""
    def __init__(self, settings, infrastructure):
        super().__init__(infrastructure)
        self.calls = []
        self.candidates, self.files = [], {}
        for index, (title, published) in enumerate([
            ('GPU Scheduling Fixture', '2026-09-01'), ('Storage Compaction Fixture', '2026-08-01'),
            ('Network Admission Fixture', '2026-07-01'), ('Compiler Optimization Fixture', '2026-06-01'),
            ('Distributed Recovery Fixture', '2024-04-01')]):
            doi = f'10.9999/fixture-{index}'
            url = f'https://publisher.example/paper/{index}'
            pdf_url = url + '.pdf'
            candidate = {'candidate_id': 'doi:' + doi, 'title': title, 'doi': doi,
                         'venue': settings.venues[0], 'authors': ['Fixture Author'],
                         'source_urls': [url], 'official_urls': [url], 'pdf_urls': [pdf_url],
                         'index_evidence': {'url': 'https://index.example', 'record': {'fixture': True}}, 'abstract': 'Screening only.'}
            self.candidates.append(candidate)
            crossref = {'message': {'title': [title], 'type': 'proceedings-article',
                        'container-title': [settings.venues[0]],
                        'published-online': {'date-parts': [[int(n) for n in published.split('-')]]},
                        'URL': url, 'link': [{'URL': pdf_url, 'content-type': 'application/pdf'}]}}
            self.files['https://api.crossref.org/works/' + doi.replace('/', '%2F')] = json_bytes(crossref)
            self.files[url] = (f'<meta name="citation_title" content="{title}">'
                               f'<meta name="citation_online_date" content="{published}">'
                               f'<meta name="citation_pdf_url" content="{pdf_url}">').encode()
            pdf = fitz.open()
            page = pdf.new_page(width=600, height=800)
            page.insert_text((40, 50), title, fontsize=14)
            page.insert_text((40, 90), 'Full paper fixture, including Figure 1 and Table 1.')
            page.draw_rect(fitz.Rect(100, 250, 230, 340))
            page.draw_rect(fitz.Rect(350, 250, 480, 340))
            page.draw_line(fitz.Point(230, 295), fitz.Point(350, 295))
            page.insert_text((110, 280), 'Input queue')
            page.insert_text((360, 280), 'GPU worker')
            page = pdf.new_page(width=600, height=800)
            inserted = page.insert_textbox(fitz.Rect(40, 40, 560, 660), ' '.join(['Complete experimental evidence.'] * 120), fontsize=9)
            assert inserted >= 0, 'Fixture PDF text must fit on the page'
            page.insert_text((40, 700), 'Table 1: Baseline 10 ms; Fixture 5 ms. TAIL_EVIDENCE_NOT_IN_ABSTRACT')
            self.files[pdf_url] = pdf.tobytes()
            pdf.close()
        self.files['https://influence.example/adoption'] = b'<p>A later system adopts the recovery protocol as its baseline.</p>'

    def get(self, url, params=None, *, max_bytes=8_000_000):
        self.calls.append(url)
        raw = self.files[url]
        if len(raw) > max_bytes:
            raise EvidenceError('Fixture input exceeds infrastructure limit')
        return raw, url

    def discover(self, settings, day):
        self.discovery_settings = settings
        return copy.deepcopy(self.candidates)


class FixtureBackend:
    def __init__(self, root):
        self.root, self.calls = root, []
        self.reject = False

    def generate(self, stage, context, images=()):
        settings = load_settings(self.root)
        messages = build_messages(self.root, settings, stage, context)
        self.calls.append((stage, copy.deepcopy(context), list(images), messages))
        if stage == 'select':
            counts = {'latest': 0, 'classic': 0}
            chosen = []
            for paper in context['candidates']:
                category = paper['category']
                if counts[category] >= settings.quotas[category]:
                    continue
                chosen.append({'candidate_id': paper['candidate_id'], 'title_aliases': [],
                               'topic_fit': 'Offline fixture uses configured research interests.',
                               'identity_evidence': 'Fixture publisher DOI and full title agree.',
                               'influence_url': 'https://influence.example/adoption',
                               'influence_quote': 'A later system adopts the recovery protocol as its baseline.'})
                counts[category] += 1
            return {'selected': chosen, 'shortfall_reason': '' if counts == settings.quotas else 'Fixture source coverage leaves slots unfilled.'}
        if stage == 'analyze':
            return analysis_result(context['document'], settings)
        if stage == 'trends':
            return {'labels': {'report_title': 'Daily Paper Report', 'latest': 'Latest', 'classic': 'Classic',
                              'timezone': 'Timezone', 'latest_window': 'Latest window', 'classic_window': 'Classic window',
                              'inclusive': 'inclusive', 'official_publication': 'Official publication',
                              'full_paper': 'Full paper', 'supporting_papers': 'Supporting papers'},
                    'trends': [], 'insufficient_evidence': 'Synthetic fixtures cannot support a scientific trend.',
                    'coverage_note': context.get('selection_shortfall', '')}
        result = review_result()
        if self.reject:
            result.update(approved=False, problems=['Fixture models rejection of unresolved evidence.'])
        return result


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='dailypaper-test-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ('AGENTS.md', 'DAILY_REPORT_PRODUCT_REQUIREMENTS.md', 'config.yaml'):
            shutil.copyfile(REPO / name, self.root / name)
        shutil.copytree(REPO / 'skills', self.root / 'skills')
        (self.root / 'state').mkdir()
        self.original_history = json_bytes({'schema_version': 1, 'papers': [], 'runs': [], 'retained_metadata': {'fixture': True}})
        (self.root / HISTORY_PATH).write_bytes(self.original_history)
        self.settings = load_settings(self.root)
        self.infrastructure = load_infrastructure(self.root)
        self.sources = FixtureSources(self.settings, self.infrastructure)
        self.backend = FixtureBackend(self.root)

    def edit(self, old, new):
        path = self.root / 'DAILY_REPORT_PRODUCT_REQUIREMENTS.md'
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new))
        self.settings = load_settings(self.root)

    def prepare(self, **kwargs):
        return prepare(self.root, day=DAY, sources=self.sources, backend=self.backend, **kwargs)

    def test_prepare_full_papers_and_publish_once(self):
        bundle = self.prepare()
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)
        self.assertFalse((self.root / 'content').exists())
        self.assertEqual([p['category'] for p in bundle['papers']], ['latest'] * 4 + ['classic'])
        analysis_calls = [call for call in self.backend.calls if call[0] == 'analyze']
        self.assertEqual(len(analysis_calls), 5)
        for _, context, images, messages in analysis_calls:
            self.assertEqual(len(images), 2)
            self.assertGreater(len(context['document']['pages'][1]['text']), 2200)
            self.assertIn('TAIL_EVIDENCE_NOT_IN_ABSTRACT', messages[1]['content'])
        result = publish(self.root, bundle)
        self.assertEqual(result['status'], 'archived')
        report = read_report(self.root / f'content/daily/{DAY}.md')
        self.assertEqual(len(report.papers), 5)
        self.assertEqual(report.trends_title, self.settings.trend_heading)
        ledger = load_history(self.root)
        self.assertEqual(len(ledger.data['papers']), 5)
        self.assertTrue(all(p['status'] == 'archived' for p in ledger.data['papers']))
        self.assertEqual(ledger.data['retained_metadata'], {'fixture': True})
        calls = len(self.backend.calls)
        before = {p: p.read_bytes() for folder in ('content', 'state') for p in (self.root / folder).rglob('*') if p.is_file()}
        self.assertTrue(self.prepare()['already_archived'])
        self.assertEqual(publish(self.root, bundle)['status'], 'already_archived')
        self.assertEqual(len(self.backend.calls), calls)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(len(load_history(self.root).data['runs']), 1)

    def test_runtime_change_cannot_reuse_or_replace_prepared_selection(self):
        from codex_runtime import bind_report, RuntimeVerificationError
        resolved = {'model': 'fixture-flagship', 'mode': 'fixture-deepest',
                    'cli_version': 'fixture-cli', 'settings_sha256': self.settings.sha256}
        self.backend.bind_report = lambda stage: bind_report(stage, resolved)
        original_generate = self.backend.generate

        def interrupt_analysis(stage, context, images=()):
            if stage == 'analyze':
                raise RuntimeError('fixture interruption after selection')
            return original_generate(stage, context, images)
        self.backend.generate = interrupt_analysis
        with self.assertRaisesRegex(RuntimeError, 'fixture interruption'):
            self.prepare()
        checkpoint = self.root / '.cache/dailypaper/runs' / DAY.isoformat() / 'selection.json'
        selection = checkpoint.read_bytes()
        calls = len(self.backend.calls)
        self.backend.generate = original_generate
        resolved['mode'] = 'new-deepest'
        with self.assertRaisesRegex(RuntimeVerificationError, 'Mixed configurations'):
            self.prepare()
        self.assertEqual(len(self.backend.calls), calls)
        self.assertEqual(checkpoint.read_bytes(), selection)
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)
        resolved['mode'] = 'fixture-deepest'
        bundle = self.prepare()
        self.assertEqual(bundle['runtime'], resolved)
        self.assertEqual(sum(call[0] == 'select' for call in self.backend.calls), 1)
        self.assertEqual(checkpoint.read_bytes(), selection)
        self.assertFalse((self.root / 'content').exists())
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)

    def test_changing_only_settings_changes_generation_and_rendering(self):
        self.edit('**4** previously', '**1** previously')
        self.edit('**1** previously unrecommended work.', '**0** previously unrecommended work.')
        self.edit('**6 calendar months**', '**1 calendar month**')
        self.edit('**900–1,100 words per paper**', '**1,100–1,150 words per paper**')
        self.edit('**1–2** important', '**1–1** important')
        self.edit("**Clear Research Trends in Today's Papers**", '**Fixture Research Direction**')
        self.edit('GPU systems;', 'Storage research;')
        self.edit('SOSP, OSDI, NSDI', 'PLDI, OSDI, NSDI')
        self.sources = FixtureSources(self.settings, self.infrastructure)
        bundle = self.prepare()
        self.assertEqual(len(bundle['papers']), 1)
        self.assertEqual(bundle['papers'][0]['title'], 'GPU Scheduling Fixture')
        self.assertEqual(len(bundle['assets']), 1)
        self.assertGreaterEqual(bundle['papers'][0]['counts']['summary_words'], 1100)
        self.assertIn('2026-08-08 – 2026-09-08', bundle['report_markdown'])
        self.assertIn('# Fixture Research Direction', bundle['report_markdown'])
        self.assertEqual(self.sources.discovery_settings.venues[0], 'PLDI')
        for _, _, _, messages in self.backend.calls:
            self.assertIn(self.settings.raw, messages[0]['content'])
            self.assertIn('Storage research;', messages[0]['content'])
        publish(self.root, bundle)
        report = read_report(self.root / f'content/daily/{DAY}.md')
        self.assertEqual(report.trends_title, 'Fixture Research Direction')
        self.assertEqual(len(report.papers), 1)

    def test_interrupted_reservation_resumes_same_bundle(self):
        bundle = self.prepare()
        with self.assertRaisesRegex(RuntimeError, 'interrupted'):
            publish(self.root, bundle, before_finalize=lambda: (_ for _ in ()).throw(RuntimeError('interrupted')))
        ledger = load_history(self.root)
        self.assertEqual(ledger.run(bundle['run_id'])['status'], 'reserved')
        calls = len(self.backend.calls)
        recovered = self.prepare()
        self.assertEqual(recovered, bundle)
        self.assertEqual(len(self.backend.calls), calls)
        altered = copy.deepcopy(bundle)
        altered['report_markdown'] += 'Changed draft'
        with self.assertRaises(ValidationError):
            publish(self.root, altered)
        publish(self.root, recovered)
        ledger = load_history(self.root)
        self.assertEqual(ledger.run(bundle['run_id'])['status'], 'archived')
        self.assertEqual(len(ledger.data['papers']), 5)
        self.assertEqual(len(ledger.data['runs']), 1)
        next_day = date(2026, 9, 9)
        with self.assertRaisesRegex(ValidationError, 'No eligible'):
            discovery(self.root, self.settings, next_day, self.sources, ledger)

    def test_edited_settings_cannot_replace_pending_selection(self):
        self.backend.reject = True
        with self.assertRaisesRegex(ValidationError, 'review rejected'):
            self.prepare()
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)
        chosen = (self.root / f'.cache/dailypaper/runs/{DAY}/selection.json').read_bytes()
        self.edit('**4** previously', '**3** previously')
        with self.assertRaisesRegex(ValidationError, 'Settings changed'):
            self.prepare()
        self.assertEqual((self.root / f'.cache/dailypaper/runs/{DAY}/selection.json').read_bytes(), chosen)

    def test_bad_inputs_cannot_publish(self):
        bundle = self.prepare()
        for mutate in (
            lambda b: b['papers'][0]['document']['pages'].pop(),
            lambda b: b['papers'][0]['analysis']['sections'][0].update(text='An abstract.'),
            lambda b: b['papers'][0]['analysis']['visuals'][0].update(caption=''),
            lambda b: b['papers'][0]['analysis']['sections'][3].update(text='```mermaid\ngraph LR\nA-->B\n```'),
            lambda b: b['review'].update(approved=False, problems=['Unverified claim']),
            lambda b: b['papers'][0].update(venue='An unconfigured workshop'),
        ):
            draft = copy.deepcopy(bundle)
            mutate(draft)
            with self.subTest(mutation=mutate):
                with self.assertRaises((ValidationError, jsonschema.ValidationError)):
                    publish(self.root, draft)
                self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)
                self.assertFalse((self.root / 'content').exists())

    def test_existing_report_is_never_overwritten(self):
        bundle = self.prepare()
        report = self.root / f'content/daily/{DAY}.md'
        report.parent.mkdir(parents=True)
        original = '# Existing report\n\n## Latest 1 — Unrelated prior work\n\nPrior evidence.\n'
        report.write_text(original)
        with self.assertRaisesRegex(ValidationError, 'already exists'):
            publish(self.root, bundle)
        self.assertEqual(report.read_text(), original)
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)

    def test_permanent_aliases_and_legacy_evidence_survive_reconciliation(self):
        existing = {'title': 'Original Paper Title', 'title_aliases': ['Renamed Camera Ready Title'],
                    'identifiers': {'arxiv': ['2101.12345v1'], 'doi': ['10.9999/WORK']},
                    'status': 'reserved', 'run_id': 'systems-paper-daily:2021-01-01', 'unknown_field': {'keep': [1, 2]}}
        ledger = json.loads(self.original_history)
        ledger['papers'] = [existing]
        (self.root / HISTORY_PATH).write_bytes(json_bytes(ledger))
        legacy = {'papers': [{'title': 'Legacy Recommended Work', 'paper_id': '2001.99999',
                             'recommended_count': 1, 'last_recommended_date': '2020-01-01',
                             'cooldown_until': '2020-01-02', 'unknown_metadata': 'retain me'}]}
        index = self.root / 'state/paper_index.json'
        index.write_bytes(json_bytes(legacy))
        report = self.root / 'content/daily/2020-01-01.md'
        report.parent.mkdir(parents=True)
        report.write_text('# Old report\n\n## Latest 1 — Archive Only Work\n\n**Metadata.** [PDF](https://arxiv.org/pdf/1912.12345v4)\n\nA prior recommendation.\n')
        snapshot = load_history(self.root)
        for candidate in [{'title': 'Renamed Camera Ready Title'}, {'title': 'Different title', 'doi': '10.9999/work'},
                          {'title': 'Another title', 'url': 'https://arxiv.org/abs/2101.12345v9'},
                          {'title': 'Legacy Recommended Work'}, {'title': 'New name', 'arxiv_id': '1912.12345'}]:
            with self.subTest(candidate=candidate):
                with self.assertRaises(HistoryError):
                    snapshot.assert_new([candidate])
        reconciled = snapshot.reconciled()
        self.assertEqual(reconciled['papers'][0], existing)
        imported = next(p for p in reconciled['papers'] if p['title'] == 'Legacy Recommended Work')
        self.assertEqual(imported['legacy_evidence'][0]['record'], legacy['papers'][0])
        self.assertEqual(index.read_bytes(), json_bytes(legacy))
        self.assertEqual(len(reconciled['papers']), 3)
        write_history(snapshot, reconciled)
        self.assertEqual(load_history(self.root).reconciled(), reconciled)
        # Canonical imported evidence still excludes identifier aliases if a
        # legacy index is later unavailable; no record is omitted from prompts.
        index.unlink()
        current = load_history(self.root)
        with self.assertRaises(HistoryError):
            current.assert_new([{'title': 'A later renamed work', 'arxiv_id': '2001.99999v8'}])
        self.assertEqual(len(current.prompt_records), 3)
        self.assertTrue(any('arxiv:2001.99999' in p['identity_tokens'] for p in current.prompt_records))

    def test_missing_history_and_concurrent_writes_fail_closed(self):
        path = self.root / HISTORY_PATH
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.prepare()
        self.assertEqual(self.backend.calls, [])
        path.write_bytes(self.original_history)
        snapshot = load_history(self.root)
        concurrent = {**snapshot.data, 'external_update': 'preserve'}
        path.write_bytes(json_bytes(concurrent))
        with self.assertRaises(HistoryError):
            write_history(snapshot, snapshot.data)
        with self.assertRaises(HistoryError):
            assert_unchanged(snapshot)
        self.assertEqual(json.loads(path.read_bytes()), concurrent)

    def test_calendar_settings_and_invalid_competing_yaml(self):
        self.assertEqual(calendar_shift(date(2024, 8, 31), months=6), date(2024, 2, 29))
        self.assertEqual(calendar_shift(date(2024, 2, 29), years=5), date(2019, 2, 28))
        self.assertEqual(self.settings.category('2026-03-08', DAY), 'latest')
        self.assertEqual(self.settings.category('2026-03-07', DAY), 'classic')
        self.assertIsNone(self.settings.category('2021-09-07', DAY))
        self.assertIsNone(self.settings.category('2026-09-09', DAY))
        self.assertEqual(self.settings.local_date(datetime(2026, 9, 9, 2, tzinfo=timezone.utc)), DAY)
        self.edit('America/New_York', 'Asia/Tokyo')
        self.assertEqual(self.settings.local_date(datetime(2026, 9, 9, 2, tzinfo=timezone.utc)), date(2026, 9, 9))
        with (self.root / 'config.yaml').open('a') as config:
            config.write('\nresearch_domains:\n  GPU: {priority: 9}\n')
        with self.assertRaisesRegex(SettingsError, 'Competing'):
            load_infrastructure(self.root)

    def test_editor_explains_unfilled_slots_without_publishing_preparation_notes(self):
        self.sources.candidates = self.sources.candidates[:4]
        pool = discovery(self.root, self.settings, DAY, self.sources, load_history(self.root))
        raw = 'No classic was verified. Analysis is pending; screenshot tools returned no pixels.'
        edited = 'No eligible classic paper was verified in this search.'
        generate = self.backend.generate
        def edit_note(stage, context, images=()):
            result = generate(stage, context, images)
            if stage == 'select':
                result['shortfall_reason'] = raw
            if stage == 'trends':
                self.assertEqual(context['selection_shortfall'], raw)
                result['coverage_note'] = edited
            return result
        with patch.object(self.backend, 'generate', side_effect=edit_note):
            bundle = self.prepare(pool=pool)
        self.assertEqual(bundle['shortfall_reason'], raw)
        self.assertIn(edited, bundle['report_markdown'])
        self.assertNotIn('Analysis is pending', bundle['report_markdown'])
        self.assertNotIn('no pixels', bundle['report_markdown'])
        incomplete = {**bundle['trends'], 'coverage_note': ''}
        with self.assertRaisesRegex(ValidationError, 'reader-facing coverage explanation'):
            validate_trends(incomplete, bundle['papers'], self.settings)

    def test_trend_support_and_language_reach_contract_and_renderer(self):
        self.edit('**English**', '**Spanish**')
        messages = build_messages(self.root, self.settings, 'trends', {'papers': []})
        self.assertIn('**Spanish**', messages[0]['content'])
        schema = stage_schema('trends', self.settings)
        self.assertEqual(schema['properties']['trends']['maxItems'], 3)
        self.edit('**3** |', '**1** |')
        self.edit('**2** |', '**3** |')
        self.assertEqual(stage_schema('trends', self.settings)['properties']['trends']['maxItems'], 1)
        papers = [{'title': str(i), 'doi': f'10.9999/{i}', 'category': 'latest'} for i in range(3)]
        trends = self.backend.generate('trends', {'papers': papers, 'selection_shortfall': 'Fixture subset leaves slots unfilled.'})
        trends['trends'] = [{'title': 'Fixture', 'text': 'Shared problem and direction with an unresolved trade-off.',
                             'supporting_work_ids': ['doi:10.9999/0', 'doi:10.9999/1']}]
        with self.assertRaisesRegex(ValidationError, 'latest-paper support'):
            validate_trends(trends, papers, self.settings)
        trends['trends'][0]['supporting_work_ids'].append('doi:10.9999/2')
        validate_trends(trends, papers, self.settings)

    def supplement_fixture(self):
        candidate = copy.deepcopy(self.sources.candidates[0])
        article = 'https://proceedings.mlsys.org/paper_files/paper/2026/hash/fixture.html'
        supplement = 'https://proceedings.mlsys.org/paper_files/paper/2026/file/attachment.pdf'
        candidate.update(doi='', venue='MLSys', source_urls=[article], official_urls=[article])
        self.sources.files[article] = (f'<meta name="citation_title" content="{candidate["title"]}">'
            '<meta name="citation_journal_title" content="Proceedings of Machine Learning and Systems">'
            '<meta name="citation_publication_date" content="2026-05-18">'
            f'<meta name="citation_pdf_url" content="{candidate["pdf_urls"][0]}">'
            f'<a href="{supplement}"><span>Supplemental appendix</span></a>').encode()
        with fitz.open() as extra:
            extra.new_page().insert_text((40, 50), 'APPENDIX_ONLY_EVIDENCE: batch size is 32.')
            self.sources.files[supplement] = extra.tobytes()
        return self.sources.verify_publication(candidate), supplement

    def test_published_supplement_is_read_rendered_and_bound_to_original_sources(self):
        candidate, supplement = self.supplement_fixture()
        self.assertEqual(candidate['supplements'][0]['url'], supplement)
        self.assertNotIn(supplement, candidate['pdf_urls'])
        document = self.sources.full_paper(candidate, self.root / 'complete')
        validate_document(document)
        self.assertEqual(len(document['pages']), 3)
        self.assertIn('APPENDIX_ONLY_EVIDENCE', document['pages'][-1]['text'])
        self.assertEqual(document['pages'][-1]['source_page'], 1)
        self.assertEqual(document['pages'][-1]['source_url'], supplement)
        analysis = analysis_result(document, self.settings)
        validate_analysis(analysis, document, self.settings)
        analysis['visuals'][1]['page'] = 3
        _, blocks = prepare_visuals(candidate, analysis, document, self.root / 'supplement-visuals')
        self.assertIn(f'[PDF page 1]({supplement}#page=1)', blocks[1])
        with self.assertRaisesRegex(ValidationError, 'preserve the selection and revalidate'):
            validate_document({key: value for key, value in document.items() if key != 'source_documents'})
        Path(document['source_documents'][-1]['pdf']).write_bytes(b'changed supplement')
        with self.assertRaisesRegex(ValidationError, 'supplement changed'):
            validate_document(document)

    def author_fixture(self):
        candidate = self.sources.verify_publication(self.sources.candidates[0])
        candidate['source_urls'].append('https://arxiv.org/abs/2601.12345v2')
        url = 'https://arxiv.org/pdf/2601.12345v2'
        raw = self.sources.files[candidate['pdf_urls'][0]]
        with fitz.open(stream=raw, filetype='pdf') as author:
            author.new_page().insert_text((40, 50), 'AUTHOR_APPENDIX_EVIDENCE: compilation can take several minutes.')
            self.sources.files[url] = author.tobytes()
        return candidate, url, raw

    def test_linked_author_appendix_is_retained_without_replacing_publisher_copy(self):
        candidate, url, original = self.author_fixture()
        document = self.sources.full_paper(candidate, self.root / 'author-complete')
        validate_document(document)
        self.assertEqual(len(document['pages']), 5)
        self.assertEqual([d['kind'] for d in document['source_documents']], ['main', 'author-version'])
        self.assertEqual(Path(document['source_documents'][0]['pdf']).read_bytes(), original)
        self.assertEqual(document['pages'][-1]['source_page'], 3)
        self.assertEqual(document['pages'][-1]['source_url'], url)
        self.assertIn('AUTHOR_APPENDIX_EVIDENCE', document['pages'][-1]['text'])

    def test_identical_author_copy_is_not_duplicated_and_wrong_work_is_rejected(self):
        candidate, url, original = self.author_fixture()
        self.sources.files[url] = original
        document = self.sources.full_paper(candidate, self.root / 'identical')
        self.assertEqual(len(document['pages']), 2)
        self.assertEqual(len(document['source_documents']), 1)
        self.sources.files[url] = self.sources.files[self.sources.candidates[1]['pdf_urls'][0]]
        with self.assertRaisesRegex(EvidenceError, 'Author-copy title does not match'):
            self.sources.full_paper(candidate, self.root / 'wrong-author')

    def test_unreadable_linked_author_copy_stops_complete_paper_claim(self):
        candidate, url, original = self.author_fixture()
        get = self.sources.get
        def unavailable(target, *args, **kwargs):
            if target == url:
                raise requests.Timeout('fixture unavailable')
            return get(target, *args, **kwargs)
        with patch.object(self.sources, 'get', side_effect=unavailable):
            with self.assertRaisesRegex(EvidenceError, 'Linked author version could not be verified'):
                self.sources.full_paper(candidate, self.root / 'unavailable-author')

    def test_inaccessible_published_supplement_stops_instead_of_using_main_only(self):
        candidate, supplement = self.supplement_fixture()
        original = self.sources.get
        def get(url, *args, **kwargs):
            if url == supplement:
                raise requests.ConnectionError('fixture unavailable')
            return original(url, *args, **kwargs)
        with patch.object(self.sources, 'get', side_effect=get):
            with self.assertRaisesRegex(EvidenceError, 'Required published supplement unavailable'):
                self.sources.full_paper(candidate, self.root / 'incomplete')
        self.assertFalse((self.root / 'incomplete/paper.pdf').exists())

    def test_combined_paper_limit_and_supplement_text_requirements_are_enforced(self):
        candidate, supplement = self.supplement_fixture()
        self.sources.documents['max_pages'] = 2
        with self.assertRaisesRegex(EvidenceError, 'exceed page limit'):
            self.sources.full_paper(candidate, self.root / 'limited')
        self.sources.documents['max_pages'] = 100
        with fitz.open() as blank:
            blank.new_page()
            self.sources.files[supplement] = blank.tobytes()
        with self.assertRaisesRegex(EvidenceError, 'verified OCR is required'):
            self.sources.full_paper(candidate, self.root / 'scanned')

    def test_source_publication_dates_and_complete_pdf_failures(self):
        candidate = self.sources.candidates[0]
        verified = self.sources.verify_publication(candidate)
        self.assertEqual(verified['publication_date'], '2026-09-01')
        document = self.sources.full_paper(verified, self.root / 'document')
        validate_analysis(analysis_result(document, self.settings), document, self.settings)
        with self.assertRaisesRegex(EvidenceError, 'title could not be matched'):
            self.sources.full_paper({**verified, 'title': 'Wrong research work'}, self.root / 'wrong')
        self.sources.documents['max_pages'] = 1
        with self.assertRaisesRegex(EvidenceError, 'not truncating'):
            self.sources.full_paper(verified, self.root / 'limited')
        crossref_url = next(url for url in self.sources.files if 'crossref.org' in url)
        record = json.loads(self.sources.files[crossref_url])
        record['message']['published-online']['date-parts'] = [[2026]]
        self.sources.files[crossref_url] = json_bytes(record)
        self.sources.files[candidate['source_urls'][0]] = b'<p>Accepted for publication; date unknown.</p>'
        with self.assertRaisesRegex(EvidenceError, 'No exact official'):
            self.sources.verify_publication(candidate)

    def test_classic_influence_is_retrieved_and_missing_evidence_underfills(self):
        original = self.backend.generate
        source = {'url': 'https://influence.example/adoption', 'title': 'Later system',
                  'source_text': 'A later system adopts the recovery protocol as its baseline.', 'source_sha256': 'fixture'}

        def no_known_influence(stage, context, images=()):
            if stage == 'influence':
                self.assertEqual(context['sources'], [source])
                return {'url': source['url'], 'excerpt': source['source_text'], 'reason': 'Explicit adoption as a baseline.'}
            result = original(stage, context, images)
            if stage == 'select':
                for selected in result['selected']:
                    selected.update(influence_url='', influence_quote='')
            return result

        with patch.object(self.backend, 'generate', side_effect=no_known_influence), \
             patch.object(self.sources, 'influence_candidates', return_value=[source]) as retrieve:
            bundle = self.prepare()
        self.assertEqual(retrieve.call_count, 1)
        self.assertEqual(bundle['papers'][-1]['continuing_influence']['excerpt'], source['source_text'])
        with tempfile.TemporaryDirectory(prefix='dailypaper-no-influence-') as stage, \
             patch.object(self.backend, 'generate', side_effect=no_known_influence), \
             patch.object(self.sources, 'influence_candidates', return_value=[]):
            underfilled = self.prepare(stage_dir=Path(stage))
        self.assertEqual(len(underfilled['papers']), 4)
        self.assertIn('No inspectable later-use evidence', underfilled['shortfall_reason'])
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)

    def test_influence_discovery_fetches_later_text_not_just_citation_counts(self):
        candidate = self.sources.verify_publication(self.sources.candidates[-1])
        api = Mock(side_effect=[({'id': 'https://openalex.org/W42', 'title': candidate['title'], 'cited_by_count': 1000}, 'fixture'),
                                ({'results': [{'title': 'Later System', 'locations': [{'landing_page_url': 'https://influence.example/adoption'}]}]}, 'fixture')])
        self.sources.files['https://influence.example/adoption'] = b'<h1>Later System</h1><p>We adopt the recovery protocol as our baseline.</p>'
        with patch.object(self.sources, 'json', side_effect=api):
            evidence = self.sources.influence_candidates(candidate, DAY)
        self.assertEqual(len(evidence), 1)
        self.assertIn('adopt the recovery protocol', evidence[0]['source_text'])
        self.assertIn('cites:W42', api.call_args.args[1]['filter'])
        self.assertIn('to_publication_date:2026-09-08', api.call_args.args[1]['filter'])

    def test_bibliographic_spelling_is_not_a_second_venue_allowlist(self):
        self.assertTrue(label_matches('ACM Trans. Comput. Syst.', 'ACM TOCS'))
        self.assertTrue(label_matches('IEEE Transactions on Parallel and Distributed Systems', 'IEEE TPDS'))
        self.assertTrue(label_matches('SIGMETRICS', 'SIGMETRICS / PERFORMANCE'))
        self.assertFalse(label_matches('SC Workshops', 'SC'))
        self.assertFalse(label_matches('SOSP Companion', 'SOSP'))

    def test_request_budget_visits_configured_venues_and_keeps_classic_years(self):
        sources = Sources({'search': {'max_candidates_per_venue': 12}})
        calls = []

        def dblp(venue, year, limit):
            calls.append((venue, year, limit))
            return [{'candidate_id': f'{venue}:{year}:{i}', 'venue': venue} for i in range(limit)]

        with patch.object(sources, 'dblp', side_effect=dblp), patch.object(sources, 'openalex') as fallback:
            result = sources.discover(self.settings, DAY)
        self.assertFalse(fallback.called)
        self.assertEqual({paper['venue'] for paper in result}, set(self.settings.venues))
        self.assertTrue(any(year == 2021 for _, year, _ in calls))
        self.assertLessEqual(len(result), len(self.settings.venues) * 12)
        self.assertTrue(sources.failures)  # Budget limitations are handed to selection.

    def test_blocked_indexes_stop_repeated_requests_and_redact_credentials(self):
        session = Mock()
        challenge = Mock(status_code=200, url='https://dblp.org/search/publ/api')
        challenge.iter_content.return_value = [b'<html>Making sure you are not a bot</html>']
        limited = Mock(status_code=429)
        session.get.side_effect = [challenge, limited]
        sources = Sources({'search': {'request_interval_seconds': 0, 'retries': 2}}, session)
        with patch.dict(os.environ, {'OPENALEX_API_KEY': 'private-fixture-token'}):
            self.assertEqual(sources.discover(self.settings, DAY), [])
        self.assertEqual(session.get.call_count, 2)
        self.assertEqual(len(sources.failures), 2)
        self.assertIn('non-JSON', sources.failures[0])
        self.assertIn('HTTP 429', sources.failures[1])
        self.assertNotIn('private-fixture-token', str(sources.failures))
        # Repeated access in this run fails locally; a fresh run may retry the service.
        with self.assertRaisesRegex(EvidenceError, 'HTTP 429'):
            sources.json('https://api.openalex.org/works/fixture')
        self.assertEqual(session.get.call_count, 2)
        self.assertEqual(Sources({}).unavailable, {})

    def test_index_timeout_is_not_an_empty_result_or_repeated_per_venue(self):
        session = Mock()
        session.get.side_effect = requests.Timeout('https://api.openalex.org/?api_key=private-fixture-token')
        sources = Sources({'search': {'request_interval_seconds': 0}}, session)
        self.assertEqual(sources.discover(self.settings, DAY), [])
        self.assertEqual(session.get.call_count, 2)
        self.assertTrue(all('Timeout' in item for item in sources.failures))
        self.assertNotIn('private-fixture-token', str(sources.failures))

    def discovery_result(self):
        keys = stage_schema('discover', self.settings)['properties']['candidates']['items']['properties']
        return {'candidates': [{key: copy.deepcopy(paper[key]) for key in keys} for paper in self.sources.candidates],
                'coverage_limits': ['Fixture official search coverage is incomplete.']}

    def test_official_search_fallback_prepares_and_renders_without_history_writes(self):
        original = self.backend.generate
        calls = []
        def fallback(stage, context, images=()):
            if stage == 'discover':
                calls.append(context)
                self.assertEqual(context['date_windows'], self.settings.windows(DAY))
                self.assertEqual(context['prior_recommendation_evidence'], load_history(self.root).prompt_records)
                return self.discovery_result()
            return original(stage, context, images)
        with patch.object(self.sources, 'discover', return_value=[]), \
             patch.object(self.backend, 'generate', side_effect=fallback):
            bundle = self.prepare()
            resumed = self.prepare()
        self.assertEqual(len(calls), 1)  # A retry keeps the existing selection.
        self.assertEqual(bundle['report_markdown'], resumed['report_markdown'])
        self.assertEqual(len(bundle['papers']), 5)
        self.assertEqual(len(bundle['assets']), 5)
        self.assertEqual(bundle['report_markdown'].count('| System | Latency (ms) |'), 5)
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)
        self.assertFalse((self.root / 'content').exists())
        diagnostics = json.loads((self.root / '.cache/dailypaper/runs/2026-09-08/discovery.json').read_text())
        self.assertEqual(len(diagnostics['candidates']), 5)
        self.assertTrue(diagnostics['source_failures'])

    def test_rejected_analysis_is_revised_without_reselecting_or_changing_history(self):
        original = self.backend.generate
        attempts, reviews = [], []
        def revise(stage, context, images=()):
            result = original(stage, context, images)
            if stage == 'analyze' and context['paper']['title'] == self.sources.candidates[0]['title']:
                attempts.append(context)
            if stage == 'review' and context['kind'] == 'paper' and not reviews:
                reviews.append(context)
                result.update(approved=False, problems=['Include the workload conditions for the measured result.'])
            if stage == 'review' and context['kind'] == 'trends':
                self.assertTrue(context['rendering']['offline'])
                self.assertTrue(context['rendering']['chromium_sandbox'])
                self.assertEqual([s['path'] for s in context['rendering']['screenshots']], images)
                self.assertEqual({s['viewport_width'] for s in context['rendering']['screenshots']}, {1440, 390})
                for view in context['rendering']['views']:
                    self.assertEqual(len(view['expanded_figures']), view['images'])
                    for figure in view['expanded_figures']:
                        self.assertEqual(figure['scale'], 1)
                        self.assertEqual(max(t['left'] for t in figure['tiles']), max(0, figure['full_width'] - figure['width']))
                        self.assertEqual(max(t['top'] for t in figure['tiles']), max(0, figure['full_height'] - figure['height']))
            return result
        with patch.object(self.backend, 'generate', side_effect=revise):
            self.prepare()
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]['paper'], attempts[1]['paper'])
        self.assertEqual(attempts[0]['document'], attempts[1]['document'])
        self.assertIn('workload conditions', attempts[1]['revision_feedback'])
        self.assertIn('prior_analysis', attempts[1])
        self.assertEqual(sum(stage == 'select' for stage, *_ in self.backend.calls), 1)
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)

    def test_revision_limit_does_not_bypass_failed_review(self):
        self.backend.reject = True
        with self.assertRaisesRegex(ValidationError, 'review rejected'):
            self.prepare()
        self.assertEqual(sum(stage == 'analyze' for stage, *_ in self.backend.calls), 3)
        self.assertEqual(sum(stage == 'select' for stage, *_ in self.backend.calls), 1)
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)

    def test_browser_blocks_remote_resources_and_binds_screenshots_to_report(self):
        from browser_render import inspect_site
        site = self.root / 'browser-source'
        site.mkdir()
        (site / 'index.html').write_text('<article id="report-body"><img src="https://untrusted.invalid/figure.png"></article>')
        with self.assertRaises(ValidationError):
            inspect_site(site, 'index.html', self.root / 'browser-output', 1, 0)
        bundle = self.prepare()
        from publish_daily import validate_bundle
        del bundle['rendering']
        with self.assertRaisesRegex(ValidationError, 'browser verification'):
            validate_bundle(self.root, bundle, self.settings)

    def test_fallback_rechecks_complete_history_and_publisher_evidence(self):
        data = json.loads(self.original_history)
        data['papers'] = [self.sources.candidates[0]]
        (self.root / HISTORY_PATH).write_bytes(json_bytes(data))
        before = (self.root / HISTORY_PATH).read_bytes()
        result = self.discovery_result()
        invented = copy.deepcopy(result['candidates'][1])
        invented['title'] = 'Invented publisher title'
        result['candidates'].insert(0, invented)
        self.backend.generate = Mock(return_value=result)
        with patch.object(self.sources, 'discover', return_value=[]):
            pool = discovery(self.root, self.settings, DAY, self.sources, load_history(self.root), backend=self.backend)
        self.assertEqual(len(pool['candidates']), 4)
        self.assertEqual(len(pool['rejected']), 2)
        self.assertTrue(any('Previously recommended' in r['reason'] for r in pool['rejected']))
        self.assertTrue(any('DOI title differs' in r['reason'] for r in pool['rejected']))
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), before)

    def test_fallback_uses_updated_settings_and_rejects_unconfigured_venue(self):
        self.edit('SOSP, OSDI, NSDI', 'PLDI, OSDI, NSDI')
        self.edit('**6 calendar months**', '**1 calendar month**')
        messages = build_messages(self.root, self.settings, 'discover', {})
        self.assertIn(self.settings.raw, messages[0]['content'])
        self.assertIn('skills/daily-paper-search/SKILL.md', messages[0]['content'])
        result = self.discovery_result()  # Still contains old SOSP fixture candidates.
        self.backend.generate = Mock(return_value=result)
        with patch.object(self.sources, 'discover', return_value=[]), self.assertRaises(jsonschema.ValidationError):
            discovery(self.root, self.settings, DAY, self.sources, load_history(self.root), backend=self.backend)
        context = self.backend.generate.call_args.args[1]
        self.assertEqual(context['date_windows']['latest']['start'], '2026-08-08')

    def test_empty_discovery_retains_actionable_diagnostics(self):
        self.sources.failures = ['DBLP: HTML challenge', 'OpenAlex: HTTP 429']
        self.backend.generate = Mock(return_value={'candidates': [], 'coverage_limits': ['No exact publisher dates.']})
        diagnostics = self.root / 'isolated-diagnostics.json'
        with patch.object(self.sources, 'discover', return_value=[]), self.assertRaisesRegex(ValidationError, 'HTTP 429'):
            discovery(self.root, self.settings, DAY, self.sources, load_history(self.root), backend=self.backend,
                      diagnostics_path=diagnostics)
        self.assertEqual(json.loads(diagnostics.read_text())['candidates'], [])
        self.assertIn('No exact publisher dates.', json.loads(diagnostics.read_text())['source_failures'])
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)

    def test_doi_digits_do_not_create_false_arxiv_history_collisions(self):
        first = {'title': 'Unrelated first work', 'doi': '10.1145/3600006.3613147'}
        second = {'title': 'Unrelated second work', 'doi': '10.1145/3600006.3613165'}
        for paper in (first, second):
            self.assertEqual(identifier_tokens(paper['doi']), {'doi:' + paper['doi']})
        self.assertIsNone(match_record(first, [second])[0])
        self.assertEqual(match_record(first, [first])[0], first)
        self.assertEqual(identifier_tokens('10.9999/2401.12345'), {'doi:10.9999/2401.12345'})
        self.assertEqual(identifier_tokens('1234567.1234567'), set())

    def test_real_arxiv_aliases_remain_permanently_excluded(self):
        for value in ('arxiv:2309.06180v1', 'https://arxiv.org/pdf/2309.06180v2.pdf',
                      '2309.06180', 'https://doi.org/10.48550/arXiv.2309.06180'):
            self.assertIn('arxiv:2309.06180', identifier_tokens(value))
            self.assertIsNotNone(match_record({'title': 'Renamed work', 'url': value},
                                              [{'title': 'Prior work', 'arxiv_id': '2309.06180v1'}])[0])
        self.assertIn('arxiv:hep-th/9901001', identifier_tokens('https://arxiv.org/abs/hep-th/9901001v2'))
        self.assertEqual((self.root / HISTORY_PATH).read_bytes(), self.original_history)

    def test_web_leads_cannot_self_declare_official_sources_or_venues(self):
        candidate = copy.deepcopy(self.sources.candidates[0])
        crossref_url = next(url for url in self.sources.files if 'crossref.org' in url)
        record = json.loads(self.sources.files[crossref_url])
        record['message']['container-title'] = ['SOSP Companion Workshops']
        self.sources.files[crossref_url] = json_bytes(record)
        with self.assertRaisesRegex(EvidenceError, 'Publisher venue'):
            self.sources.verify_publication(candidate)
        candidate['doi'] = ''  # The author page is listed as official by the untrusted model.
        with self.assertRaisesRegex(EvidenceError, 'No exact official'):
            self.sources.verify_publication(candidate)
        self.assertTrue(publication_venue_matches(["Proceedings ... (ASPLOS '26)"], 'ASPLOS'))
        self.assertFalse(publication_venue_matches(['Proceedings ... (ASPLOS Workshops 2026)'], 'ASPLOS'))

    def test_official_landing_requires_matching_venue_title_and_exact_date(self):
        candidate = {'title': 'Fixture research', 'venue': 'MLSys', 'official_urls': ['https://proceedings.mlsys.org/fixture']}
        prefix = ('<meta name="citation_title" content="Fixture research">'
                  '<meta name="citation_journal_title" content="Proceedings of Machine Learning and Systems">')
        url = candidate['official_urls'][0]
        self.sources.files[url] = (prefix + '<meta name="citation_publication_date" content="2026-05-18">').encode()
        self.assertEqual(self.sources.verify_publication(candidate)['publication_date'], '2026-05-18')
        for untrusted in ('https://people.acm.org/fixture', 'https://proceedings.mlsys.org.example/fixture'):
            self.sources.files[untrusted] = self.sources.files[url]
            with self.assertRaisesRegex(EvidenceError, 'No exact official'):
                self.sources.verify_publication({**candidate, 'official_urls': [untrusted]})
        self.sources.files[url] = (prefix + '<meta name="citation_publication_date" content="2026">').encode()
        with self.assertRaisesRegex(EvidenceError, 'No exact official'):
            self.sources.verify_publication(candidate)
        candidate['venue'] = 'SOSP'
        self.sources.files[url] = (prefix + '<meta name="citation_publication_date" content="2026-05-18">').encode()
        with self.assertRaisesRegex(EvidenceError, 'No exact official'):
            self.sources.verify_publication(candidate)

    def test_pacmpl_conference_issue_is_verified_without_admitting_other_journals(self):
        candidate = copy.deepcopy(self.sources.candidates[0])
        candidate['venue'] = 'PLDI'
        url = next(url for url in self.sources.files if 'crossref.org' in url)
        record = json.loads(self.sources.files[url])
        record['message'].update(type='journal-article', issue='PLDI',
                                 **{'container-title': ['Proceedings of the ACM on Programming Languages']})
        self.sources.files[url] = json_bytes(record)
        self.assertEqual(self.sources.verify_publication(candidate)['venue'], 'PLDI')
        record['message']['container-title'] = ['Unrelated journal']
        self.sources.files[url] = json_bytes(record)
        with self.assertRaisesRegex(EvidenceError, 'Publisher venue'):
            self.sources.verify_publication(candidate)

    def test_later_issue_and_author_pages_cannot_supply_first_publication_date(self):
        candidate = copy.deepcopy(self.sources.candidates[0])
        crossref_url = next(url for url in self.sources.files if 'crossref.org' in url)
        record = json.loads(self.sources.files[crossref_url])
        record['message']['published-online']['date-parts'] = [[2025, 1]]
        record['message']['published-print'] = {'date-parts': [[2026, 9, 1]]}
        self.sources.files[crossref_url] = json_bytes(record)
        self.sources.files[candidate['source_urls'][0]] = b'<p>Issue publication date only.</p>'
        with self.assertRaisesRegex(EvidenceError, 'later print date'):
            self.sources.verify_publication(candidate)
        candidate['doi'], candidate['official_urls'] = '', []
        self.sources.files[candidate['source_urls'][0]] = (f'<meta name="citation_title" content="{candidate["title"]}">'
                         '<meta name="citation_online_date" content="2026-09-01">').encode()
        with self.assertRaisesRegex(EvidenceError, 'No exact official'):
            self.sources.verify_publication(candidate)

    def test_localized_report_labels_and_edited_headings_render(self):
        self.edit('**English**', '**Spanish**')
        self.edit('4. Key figures or tables', '4. Figuras y tablas')
        self.edit("**Clear Research Trends in Today's Papers**", '**Tendencias de investigación**')
        original = self.backend.generate

        def localized(stage, context, images=()):
            result = original(stage, context, images)
            if stage == 'analyze':
                result['visual_labels'] = {'pdf_page': 'Página PDF', 'paraphrased_caption': 'Leyenda parafraseada'}
            if stage == 'trends':
                result['labels'].update(report_title='Informe de artículos', latest='Reciente', classic='Clásico',
                                        timezone='Zona horaria', latest_window='Intervalo reciente', classic_window='Intervalo clásico',
                                        inclusive='inclusivo', official_publication='Publicación oficial', full_paper='Artículo completo',
                                        supporting_papers='Artículos de apoyo')
            return result

        with patch.object(self.backend, 'generate', side_effect=localized):
            bundle = self.prepare()
        self.assertIn('### 4. Figuras y tablas', bundle['report_markdown'])
        self.assertIn('Página PDF', bundle['report_markdown'])
        self.assertIn('## Clásico 1', bundle['report_markdown'])
        publish(self.root, bundle)
        report = read_report(self.root / f'content/daily/{DAY}.md')
        self.assertEqual(report.title, 'Informe de artículos — 2026-09-08')
        self.assertEqual(len(report.papers), 5)
        self.assertEqual(report.papers[-1].category, 'Classic')

    def test_runner_commits_exact_artifacts_and_recovers_failed_push(self):
        import run_local_daily
        shutil.copyfile(REPO / '.gitignore', self.root / '.gitignore')
        # The fixture checkout invokes the real build script through a symlink;
        # all Git state and the remote live inside this temporary directory.
        (self.root / 'scripts').symlink_to(REPO / 'scripts', target_is_directory=True)
        with tempfile.TemporaryDirectory(prefix='dailypaper-remote-') as directory:
            remote = Path(directory) / 'remote.git'

            def git(*args):
                return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

            git('init', '--initial-branch=main')
            git('config', 'user.name', 'Offline Test')
            git('config', 'user.email', 'fixture@example.invalid')
            git('add', '.')
            git('commit', '-m', 'Fixture base')
            git('init', '--bare', '--initial-branch=main', str(remote))
            git('remote', 'add', 'origin', str(remote))
            git('push', '-u', 'origin', 'main')
            base = git('rev-parse', 'HEAD')
            actual_run = run_local_daily.run
            failed = False

            def fail_push_once(cmd, **kwargs):
                nonlocal failed
                if cmd[:2] == ['git', 'push'] and not failed:
                    failed = True
                    raise subprocess.CalledProcessError(1, cmd)
                return actual_run(cmd, **kwargs)

            def fixture_prepare(root, **kwargs):
                return self.prepare()

            with patch.object(run_local_daily, 'prepare', side_effect=fixture_prepare), \
                 patch.object(run_local_daily, 'verify_runtime', return_value=self.backend), \
                 patch.object(run_local_daily, 'run', side_effect=fail_push_once), \
                 patch('report_settings.ReportSettings.local_date', return_value=DAY), \
                 patch.object(sys, 'argv', ['run_local_daily.py', '--repo-root', str(self.root)]):
                with self.assertRaises(subprocess.CalledProcessError):
                    run_local_daily.main()
                self.assertTrue(failed)
                calls = len(self.backend.calls)
                commit = git('rev-parse', 'HEAD')
                self.assertNotEqual(commit, base)
                changed = set(git('diff', '--name-only', base, commit).splitlines())
                self.assertTrue(all(path == HISTORY_PATH or path.startswith('content/') for path in changed))
                self.assertEqual(run_local_daily.main(), 0)
                self.assertEqual(len(self.backend.calls), calls)
                self.assertEqual(git('rev-parse', 'origin/main'), commit)
                self.assertEqual(git('status', '--porcelain'), '')

    def test_codex_receives_full_stage_inputs_and_rejects_invalid_output(self):
        document = self.sources.full_paper(self.sources.candidates[0], self.root / 'transport')
        context = {'document': document}
        result = analysis_result(document, self.settings)
        images = [page['image'] for page in document['pages']]
        captured = {}

        def codex_run(executable, resolution, root, prompt, schema, images, **kwargs):
            captured.update(prompt=prompt, images=images, schema=schema)
            return result, []

        resolution = {'executable': '/fixture/codex', 'model': 'verified-fixture', 'mode': 'ultra', 'settings_sha256': self.settings.sha256}
        backend = CodexBackend(self.root, self.settings, self.infrastructure)
        with patch.object(CodexBackend, 'preflight', return_value=resolution), patch('codex_enrich.execute', side_effect=codex_run):
            self.assertEqual(backend.generate('analyze', context, images), result)
            self.assertIn('TAIL_EVIDENCE_NOT_IN_ABSTRACT', captured['prompt'])
            self.assertIn(self.settings.raw, captured['prompt'])
            self.assertEqual(captured['images'], images)
            self.assertEqual(captured['schema'], stage_schema('analyze', self.settings))
            result = {'partial': 'not a complete analysis'}
            with self.assertRaises(jsonschema.ValidationError):
                backend.generate('analyze', context, images)

    def test_retained_skill_extractor_reads_local_pdf_without_network(self):
        helper = REPO / 'skills/paper-image-extractor/scripts/extract_images.py'
        source = self.root / 'sample.pdf'
        pixels = fitz.Pixmap(fitz.csRGB, (0, 0, 80, 40), False)
        pixels.clear_with(120)
        with fitz.open() as document:
            document.new_page().insert_image(fitz.Rect(20, 20, 180, 100), pixmap=pixels)
            document.save(source)
        output = self.root / 'extracted'
        subprocess.run([sys.executable, str(helper), str(source), str(output), str(output / 'index.md')],
                       check=True, capture_output=True, timeout=30)
        images = list(output.glob('*.png'))
        self.assertEqual(len(images), 1)
        image = fitz.Pixmap(str(images[0]))
        self.assertEqual((image.width, image.height), (80, 40))
        self.assertIn(images[0].name, (output / 'index.md').read_text())


if __name__ == '__main__':
    unittest.main()
