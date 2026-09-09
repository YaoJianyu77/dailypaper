"""Permanent work identities, legacy evidence, and conditional ledger writes."""

from __future__ import annotations

from contextlib import contextmanager
import copy
from dataclasses import dataclass
from difflib import SequenceMatcher
import fcntl
from functools import cached_property
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.parse import unquote

from site_content import markdown_parser, read_reports

HISTORY_PATH = 'state/recommendation_history.json'


class HistoryError(ValueError):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def normalize_title(value):
    return ' '.join(re.findall(r'[^\W_]+', unicodedata.normalize('NFKC', str(value)).casefold()))


def identifier_tokens(value):
    text = unquote(str(value)).strip()
    found = set()
    arxiv_id = r'(\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?'
    doi_matches = list(re.finditer(r'10\.\d{4,9}/[^\s<>"\]]+', text, re.I))
    for match in doi_matches:
        doi = match.group().rstrip('.,);}').casefold()
        found.add('doi:' + doi)
        # arXiv's own DOI is an explicit alias, unlike arbitrary DOI digits.
        # Format: https://info.arxiv.org/help/doi.html
        arxiv_doi = re.fullmatch(r'10\.48550/arxiv\.' + arxiv_id, doi, re.I)
        if arxiv_doi:
            found.add('arxiv:' + arxiv_doi.group(1).casefold())
    for match in re.finditer(r'(?<![\w])(?:arxiv:|arxiv\.org/(?:abs|pdf)/)?' + arxiv_id + r'(?![\w])', text, re.I):
        if not any(doi.start() <= match.start() < doi.end() for doi in doi_matches):
            found.add('arxiv:' + match.group(1).casefold())
    for match in re.finditer(r'(?:dblp:|dblp\.(?:org|uni-trier\.de)/rec/)((?:conf|journals)/[^\s?#]+)', text, re.I):
        found.add('dblp:' + re.sub(r'\.(?:html|xml|bib)$', '', match.group(1)).rstrip(').'))
    return found


def identities(record):
    result = set()
    for key in ('work_id', 'paper_id', 'arxiv_id', 'doi', 'dblp_key', 'source_url', 'pdf_url', 'url'):
        result.update(identifier_tokens(record.get(key, '')))
    for field, values in record.get('identifiers', {}).items():
        if not isinstance(values, list):
            values = [values]
        for value in values:
            result.update(identifier_tokens(f'{field}:{value}'))
    for url in record.get('source_urls', []):
        result.update(identifier_tokens(url))
    titles = [record.get('title', ''), record.get('normalized_title', ''), *record.get('title_aliases', [])]
    result.update('title:' + normalize_title(t) for t in titles if normalize_title(t))
    for evidence in record.get('legacy_evidence', []):
        if isinstance(evidence.get('record'), dict):
            result.update(identities(evidence['record']))
    return result


def work_id(record):
    tokens = identities(record)
    for prefix in ('doi:', 'arxiv:', 'dblp:'):
        values = sorted(t for t in tokens if t.startswith(prefix))
        if values:
            return values[0]
    title = normalize_title(record.get('title', ''))
    if not title:
        raise HistoryError('Paper has no resolvable work identity')
    return 'title:' + sha256(title.encode())[:24]


def match_record(candidate, records, *, fuzzy=True):
    tokens = identities(candidate)
    if not tokens:
        raise HistoryError('Paper identity is empty')
    for record in records:
        overlap = tokens & identities(record)
        if overlap:
            return record, ', '.join(sorted(overlap))
    if fuzzy:
        title = normalize_title(candidate.get('title', ''))
        for record in records:
            for prior in [record.get('title', ''), *record.get('title_aliases', [])]:
                prior = normalize_title(prior)
                if min(len(title.split()), len(prior.split())) >= 5 and SequenceMatcher(None, title, prior).ratio() >= .9:
                    return record, 'ambiguous similar title; resolve identity before selection'
    return None, ''


def _read_json(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('papers'), list):
        raise HistoryError(f'Invalid complete history: {path}')
    if any(not isinstance(p, dict) or not identities(p) for p in data['papers']):
        raise HistoryError(f'Unresolved history record: {path}')
    return raw, data


@dataclass
class HistorySnapshot:
    root: Path
    data: dict
    digest: str
    source_hashes: dict
    legacy: list

    @property
    def records(self):
        return self.data['papers'] + self.legacy

    @cached_property
    def prompt_records(self):
        # Every work and identity is represented; repeated raw ledger/report
        # evidence stays in the canonical record rather than bloating each prompt.
        return [{'work_id': work_id(p), 'title': p['title'], 'title_aliases': p.get('title_aliases', []),
                 'authors': p.get('authors', []), 'identity_tokens': sorted(identities(p)),
                 'source_urls': p.get('source_urls', []), 'status': p.get('status'), 'run_id': p.get('run_id'),
                 'evidence_paths': sorted(set(filter(None, [p.get('report_path'), *p.get('report_paths', []),
                                         *[e.get('path') for e in p.get('legacy_evidence', [])]])))}
                for p in self.reconciled()['papers']]

    def assert_new(self, papers, run_id=None):
        seen = []
        for paper in papers:
            match, reason = match_record(paper, self.records)
            if match and not (run_id and match.get('run_id') == run_id):
                raise HistoryError(f'Previously recommended or unresolved work: {paper["title"]} ({reason})')
            duplicate, reason = match_record(paper, seen)
            if duplicate:
                raise HistoryError(f'Duplicate work in selection: {paper["title"]} ({reason})')
            seen.append(paper)

    def run(self, run_id):
        matches = [r for r in self.data['runs'] if r.get('run_id') == run_id]
        if len(matches) > 1:
            raise HistoryError('Multiple records for one logical run')
        return matches[0] if matches else None

    def reconciled(self):
        data = copy.deepcopy(self.data)
        for item in self.legacy:
            match, _ = match_record(item, data['papers'], fuzzy=False)
            if match is None:
                data['papers'].append(copy.deepcopy(item))
            else:
                # Keep every original field and the complete additional evidence.
                evidence = match.setdefault('legacy_evidence', [])
                for source in item['legacy_evidence']:
                    if source not in evidence:
                        evidence.append(copy.deepcopy(source))
                if (normalize_title(item['title']) != normalize_title(match['title'])
                        and item['title'] not in match.get('title_aliases', [])):
                    match.setdefault('title_aliases', []).append(item['title'])
                for url in item.get('source_urls', []):
                    if url not in match.get('source_urls', []):
                        match.setdefault('source_urls', []).append(url)
        return data


def load_history(root):
    root = Path(root)
    raw, data = _read_json(root / HISTORY_PATH)
    if not isinstance(data.get('runs'), list) or any(not isinstance(r, dict) for r in data['runs']):
        raise HistoryError('History run ledger is incomplete')
    source_hashes = {HISTORY_PATH: sha256(raw)}
    legacy = []
    index = root / 'state/paper_index.json'
    if index.exists():
        index_raw, index_data = _read_json(index)
        source_hashes['state/paper_index.json'] = sha256(index_raw)
        for item in index_data['papers']:
            if not (item.get('last_recommended_date') or item.get('recommended_count', 0)):
                continue
            legacy.append({**copy.deepcopy(item), 'work_id': work_id(item), 'status': 'imported',
                           'legacy_evidence': [{'path': 'state/paper_index.json', 'record': copy.deepcopy(item)}]})
    for report in read_reports(root):
        relative = report.source.relative_to(root).as_posix()
        source_hashes[relative] = sha256(report.source.read_bytes())
        if not report.papers and report.source.stat().st_size:
            raise HistoryError(f'Cannot resolve recommended works in archived report: {relative}')
        for paper in report.papers:
            # Metadata at the opening and explicit Source/PDF links identify the
            # recommended work; references in its analysis do not become new recommendations.
            intro = paper.body.split('\n\n', 1)[0]
            source_lines = '\n'.join(line for line in paper.body.splitlines() if '**Links:**' in line)
            urls = []
            for token in markdown_parser().parse(intro + '\n\n' + source_lines):
                for child in token.children or []:
                    if child.type == 'link_open' and child.attrGet('href'):
                        urls.append(child.attrGet('href'))
            item = {'title': paper.title, 'source_urls': urls, 'status': 'imported',
                    'report_path': relative, 'legacy_evidence': [{'path': relative, 'title': paper.title,
                                                               'sha256': source_hashes[relative]}]}
            item['work_id'] = work_id(item)
            legacy.append(item)
    return HistorySnapshot(root, data, sha256(raw), source_hashes, legacy)


def assert_unchanged(snapshot):
    current = load_history(snapshot.root)
    if current.source_hashes != snapshot.source_hashes:
        raise HistoryError('History or archived evidence changed concurrently; re-read and revalidate')


@contextmanager
def history_lock(root):
    path = Path(root) / '.cache/dailypaper/history.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def atomic_write(path, data, *, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        if replace:
            os.replace(name, path)
        else:
            os.link(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def write_history(snapshot, data):
    # Call only while holding history_lock. The git publisher also uses a
    # non-forced branch update to reject writes from other clones.
    if sha256((snapshot.root / HISTORY_PATH).read_bytes()) != snapshot.digest:
        raise HistoryError('Conditional history update rejected: ledger changed')
    raw = json_bytes(data)
    atomic_write(snapshot.root / HISTORY_PATH, raw, replace=True)
    if (snapshot.root / HISTORY_PATH).read_bytes() != raw:
        raise HistoryError('History readback failed')
