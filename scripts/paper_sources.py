"""Venue-index discovery, publisher evidence, and complete PDF acquisition."""

from __future__ import annotations

from datetime import date
import html
from html.parser import HTMLParser
import json
import logging
import math
import os
from pathlib import Path
import re
import time
from urllib.parse import quote, urljoin, urlparse

import fitz
import requests

from recommendation_history import identifier_tokens, normalize_title, sha256, work_id

logger = logging.getLogger(__name__)
INDEX_HOSTS = {'dblp.org', 'api.openalex.org'}


class EvidenceError(ValueError):
    pass


class SourceUnavailable(EvidenceError):
    """An index is unavailable for this invocation, not an empty search result."""


def request_failure(error):
    # Request exception strings can contain query credentials. Log only status/type.
    response = getattr(error, 'response', None)
    return f'HTTP {response.status_code}' if response is not None else type(error).__name__


def listify(value):
    return value if isinstance(value, list) else [] if value is None else [value]


def label_matches(actual, configured):
    actual = normalize_title(re.sub(r'\s*\(\d+\)$', '', actual))
    # Spelling translations only: a key does not make a venue eligible. Eligibility
    # comes exclusively from the configured sources. Avoid substring matches that
    # accidentally admit a similarly named workshop or companion proceedings.
    spellings = {
        'usenix atc': ['USENIX Annual Technical Conference', 'USENIX Conference'],
        'sc': ['Supercomputing', 'International Conference for High Performance Computing Networking Storage and Analysis'],
        'mlsys': ['Machine Learning and Systems', 'Proceedings of Machine Learning and Systems'],
        'acm tocs': ['ACM Trans. Comput. Syst.', 'ACM Transactions on Computer Systems'],
        'acm tos': ['ACM Trans. Storage', 'ACM Transactions on Storage'],
        'ieee tpds': ['IEEE Trans. Parallel Distributed Syst.', 'IEEE Transactions on Parallel and Distributed Systems'],
        'ieee tc': ['IEEE Trans. Computers', 'IEEE Transactions on Computers'],
        'acm taco': ['ACM Trans. Archit. Code Optim.', 'ACM Transactions on Architecture and Code Optimization'],
        'ieee acm ton': ['IEEE ACM Trans. Netw.', 'IEEE ACM Transactions on Networking'],
        'acm pomacs': ['Proc. ACM Meas. Anal. Comput. Syst.', 'Proceedings of the ACM on Measurement and Analysis of Computing Systems'],
    }
    aliases = [normalize_title(a) for a in configured.split(' / ')]
    aliases += [normalize_title(a) for key in list(aliases) for a in spellings.get(key, [])]
    return actual in aliases


def publication_venue_matches(labels, configured, issue=''):
    """Match publisher venue labels, allowing conference years/ordinal prefixes."""
    labels = [str(label) for label in labels if label]
    # Do not let a main-conference acronym admit companion/workshop proceedings.
    if any(re.search(r'\b(workshops?|companion|posters?|demonstrations?|tutorials?|extended abstracts?)\b',
                     label, re.I) for label in labels):
        return False
    # PACMPL publishes conference proceedings as named journal issues (e.g. PLDI).
    # The issue is a venue label only in this specific publisher container.
    if (any(normalize_title(label) == 'proceedings of the acm on programming languages' for label in labels)
            and label_matches(str(issue), configured)):
        return True
    for label in labels:
        if label_matches(label, configured):
            return True
        normalized = normalize_title(label)
        for alias in configured.split(' / '):
            # E.g. "Proceedings ... (ASPLOS '26)". Whole tokens, never substrings.
            if f' {normalize_title(alias)} ' in f' {normalized} ':
                return True
    return False


def official_landing(url, page, venue):
    """Untrusted discovery cannot designate an arbitrary author page as official."""
    host = urlparse(url).hostname or ''
    publishers = {'usenix.org', 'www.usenix.org', 'dl.acm.org', 'ieeexplore.ieee.org', 'proceedings.mlsys.org'}
    if host not in publishers:
        return False
    labels = [page.get('citation_conference_title'), page.get('citation_journal_title')]
    return publication_venue_matches(labels, venue, page.get('citation_issue'))


def author_pdf_urls(candidate):
    """Resolve explicitly linked arXiv copies, including any supplied version."""
    output = []
    for url in [*candidate.get('source_urls', []), *candidate.get('pdf_urls', [])]:
        parsed = urlparse(url)
        if (parsed.hostname not in {'arxiv.org', 'www.arxiv.org', 'export.arxiv.org'}
                or not parsed.path.startswith(('/abs/', '/pdf/', '/html/'))):
            continue
        identifiers = [token[6:] for token in identifier_tokens(url) if token.startswith('arxiv:')]
        if len(identifiers) != 1:
            raise EvidenceError('Linked author copy has an ambiguous arXiv identity')
        version = re.search(r'(v\d+)(?:\.pdf)?$', parsed.path, re.I)
        output.append('https://arxiv.org/pdf/' + identifiers[0] + (version.group(1).lower() if version else ''))
    return list(dict.fromkeys(output))


class PageMetadata(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.meta, self.links, self.text, self.link_labels = {}, [], [], {}
        self.active_link = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = (attrs.get('name') or attrs.get('property') or '').casefold()
            self.meta.setdefault(key, []).append(attrs.get('content', ''))
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
            self.active_link = attrs['href']

    def handle_endtag(self, tag):
        if tag == 'a':
            self.active_link = None

    def handle_data(self, text):
        self.text.append(text)
        if self.active_link:
            self.link_labels[self.active_link] = self.link_labels.get(self.active_link, '') + text

    def get(self, *keys):
        return next((self.meta[k][0] for k in keys if self.meta.get(k)), '')


class Sources:
    def __init__(self, infrastructure, session=None):
        self.options = infrastructure.get('search', {})
        self.documents = infrastructure.get('documents', {})
        self.session = session or requests.Session()
        self.failures = []
        self.unavailable = {}
        self.last_request = 0

    def failure(self, message):
        if message not in self.failures:
            self.failures.append(message)
            logger.warning('Discovery coverage: %s', message)

    def disable_index(self, host, reason):
        message = f'{host}: {reason}; skipping this index for the rest of this run'
        self.unavailable[host] = message
        self.failure(message)
        return SourceUnavailable(message)

    def get(self, url, params=None, *, max_bytes=8_000_000):
        if urlparse(url).scheme not in {'http', 'https'}:
            raise EvidenceError('Evidence must have an HTTP(S) source URL')
        host = urlparse(url).hostname
        if host in self.unavailable:
            raise SourceUnavailable(self.unavailable[host])
        interval = float(self.options.get('request_interval_seconds', 1.5))
        timeout = float(self.options.get('timeout_seconds', 45))
        headers = {'User-Agent': 'DailyPaper/2.0 (research metadata verification)'}
        if urlparse(url).hostname == 'api.openalex.org' and os.environ.get('OPENALEX_API_KEY'):
            params = {**(params or {}), 'api_key': os.environ['OPENALEX_API_KEY']}
        for attempt in range(int(self.options.get('retries', 2)) + 1):
            time.sleep(max(0, interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            response = self.session.get(url, params=params, headers=headers, timeout=timeout, stream=True)
            if host in INDEX_HOSTS and response.status_code in {403, 429}:
                status = response.status_code
                response.close()
                raise self.disable_index(host, f'HTTP {status} access/rate limit')
            if response.status_code in {429, 500, 502, 503, 504} and attempt < int(self.options.get('retries', 2)):
                response.close()
                time.sleep(min(30, 2 ** attempt))
                continue
            chunks, total = [], 0
            try:
                response.raise_for_status()
                for chunk in response.iter_content(65536):
                    total += len(chunk)
                    if total > max_bytes:
                        raise EvidenceError('Source exceeds infrastructure size limit; not truncating')
                    chunks.append(chunk)
                return b''.join(chunks), response.url
            finally:
                response.close()
        raise EvidenceError('Source request failed')

    def json(self, url, params=None):
        host = urlparse(url).hostname
        try:
            raw, final = self.get(url, params)
            try:
                return json.loads(raw), final
            except (ValueError, UnicodeError) as error:
                if host in INDEX_HOSTS:
                    raise self.disable_index(host, 'non-JSON response (possibly an HTML access challenge)') from error
                raise EvidenceError(f'{host}: invalid JSON metadata') from error
        except requests.RequestException as error:
            if host in INDEX_HOSTS and (error.response is None or error.response.status_code >= 500):
                raise self.disable_index(host, request_failure(error)) from error
            raise

    def dblp(self, venue, year, limit):
        payload, url = self.json('https://dblp.org/search/publ/api', {'q': f'{venue} {year}', 'format': 'json', 'h': limit})
        output = []
        for hit in listify(payload.get('result', {}).get('hits', {}).get('hit', [])):
            info = hit['info']
            if str(info.get('year')) != str(year) or not any(label_matches(v, venue) for v in listify(info.get('venue'))):
                continue
            urls = [v.get('text', '') if isinstance(v, dict) else v for v in listify(info.get('ee'))]
            authors = info.get('authors', {})
            authors = authors.get('author', []) if isinstance(authors, dict) else authors
            candidate = {'title': html.unescape(info.get('title', '')).rstrip('.'), 'venue': venue,
                         'authors': [a.get('text', '') if isinstance(a, dict) else a for a in listify(authors)],
                         'doi': info.get('doi', ''), 'dblp_key': info.get('key', ''),
                         'identifiers': {'dblp': [info.get('key', '')]}, 'source_urls': urls,
                         'official_urls': urls,
                         'index_evidence': {'url': url, 'record': info}, 'abstract': ''}
            candidate['candidate_id'] = work_id(candidate)
            output.append(candidate)
        return output

    def openalex(self, venue, start, end, limit):
        payload, _ = self.json('https://api.openalex.org/sources', {'search': venue, 'per-page': 10})
        source = next((s for s in payload.get('results', []) if label_matches(s.get('display_name', ''), venue)
                       or label_matches(venue, s.get('abbreviated_title') or s.get('display_name', ''))), None)
        if not source:
            return []
        payload, url = self.json('https://api.openalex.org/works', {
            'filter': f'primary_location.source.id:{source["id"].split("/")[-1]},from_publication_date:{start},to_publication_date:{end}',
            'per-page': min(200, limit), 'sort': 'publication_date:desc'})
        output = []
        for record in payload.get('results', []):
            locations = record.get('locations', [])
            words = [(position, word) for word, positions in (record.get('abstract_inverted_index') or {}).items() for position in positions]
            candidate = {'title': record.get('title', ''), 'venue': venue, 'doi': record.get('doi') or '',
                         'authors': [a['author']['display_name'] for a in record.get('authorships', [])],
                         'source_urls': [loc['landing_page_url'] for loc in locations if loc.get('landing_page_url')],
                         'official_urls': [record.get('primary_location', {}).get('landing_page_url')],
                         'pdf_urls': [loc['pdf_url'] for loc in locations if loc.get('pdf_url')],
                         'abstract': ' '.join(word for _, word in sorted(words)),
                         'index_evidence': {'url': url, 'record': record}}
            candidate['candidate_id'] = work_id(candidate)
            output.append(candidate)
        return output

    def discover(self, settings, day):
        candidates, seen = [], set()
        windows = [window for category, window in settings.windows(day).items() if settings.quotas[category]]
        earliest = min(date.fromisoformat(window['start']) for window in windows)
        latest = max(date.fromisoformat(window['end']) for window in windows)
        # Spread the per-venue request budget across eligible years; do not hide an
        # unbounded per-year multiplier behind a per-venue infrastructure setting.
        years = latest.year - earliest.year + 1
        limit = int(self.options.get('max_candidates_per_venue', 12))
        per_year = max(1, math.ceil(limit / years))
        used = {venue: 0 for venue in settings.venues}
        for year in range(latest.year, earliest.year - 1, -1):
            for venue in settings.venues:
                if INDEX_HOSTS <= self.unavailable.keys():
                    return candidates
                remaining = limit - used[venue]
                if remaining <= 0:
                    continue
                try:
                    found = []
                    for alias in venue.split(' / ') if 'dblp.org' not in self.unavailable else ():
                        entries = self.dblp(alias, year, min(per_year, remaining))
                        for entry in entries:
                            entry['venue'] = venue
                        found.extend(entries)
                except (requests.RequestException, ValueError, KeyError) as error:
                    if not isinstance(error, SourceUnavailable):
                        self.failure(f'{venue} {year}: DBLP {request_failure(error)}')
                    found = []
                if not found and 'api.openalex.org' not in self.unavailable:
                    try:
                        found = self.openalex(venue, max(earliest, date(year, 1, 1)), min(latest, date(year, 12, 31)), min(per_year, remaining))
                    except (requests.RequestException, ValueError, KeyError) as error:
                        if not isinstance(error, SourceUnavailable):
                            self.failure(f'{venue} {year}: OpenAlex {request_failure(error)}')
                for candidate in found[:min(per_year, remaining)]:
                    if candidate['candidate_id'] not in seen:
                        candidates.append(candidate)
                        seen.add(candidate['candidate_id'])
                        used[venue] += 1
                if len(found) >= min(per_year, remaining):
                    self.failures.append(f'{venue} {year}: discovery may be incomplete at the configured request budget')
        return candidates

    def verify_publication(self, candidate):
        candidate = dict(candidate)
        candidate['pdf_urls'] = list(candidate.get('pdf_urls', []))
        # Rebuild supplement provenance from article pages, never model assertions.
        candidate['supplements'] = []
        candidate['source_urls'] = list(dict.fromkeys(filter(None, [*candidate.get('source_urls', []),
                                                                 *candidate.get('official_urls', [])])))
        doi = next((t[4:] for t in identifier_tokens(candidate.get('doi', '')) if t.startswith('doi:')), '')
        records = []
        incomplete_online_date = []
        if doi:
            try:
                data, url = self.json('https://api.crossref.org/works/' + quote(doi, safe=''))
                record = data['message']
                title = (record.get('title') or [''])[0]
                if normalize_title(title) != normalize_title(candidate['title']):
                    raise EvidenceError('Publisher DOI title differs from the discovered work')
                if record.get('type') not in {'journal-article', 'proceedings-article'}:
                    raise EvidenceError('Publisher record is not a formal research article')
                labels = [*record.get('container-title', []), *record.get('short-container-title', []),
                          record.get('event', {}).get('name', ''), record.get('event', {}).get('acronym', '')]
                if not publication_venue_matches(labels, candidate['venue'], record.get('issue', '')):
                    raise EvidenceError('Publisher venue differs from the configured venue or is excluded')
                online = record.get('published-online', {}).get('date-parts', [[]])[0]
                if online and len(online) < 3:
                    incomplete_online_date = online
                dates = [parts[0] for key in ('published-online', 'published-print')
                         if (parts := record.get(key, {}).get('date-parts')) and len(parts[0]) == 3]
                if dates:
                    published = min(date(*parts) for parts in dates).isoformat()
                    records.append({'url': url, 'kind': 'publisher-deposited-crossref', 'publication_date': published,
                                    'title': title, 'record': record})
                candidate['source_urls'] = list(dict.fromkeys([*candidate.get('source_urls', []), record.get('URL', '')]))
                candidate['pdf_urls'].extend(link['URL'] for link in record.get('link', []) if link.get('content-type') == 'application/pdf')
                candidate['abstract'] = candidate.get('abstract') or ' '.join(PageMetadata(record.get('abstract', '')).text)
            except requests.RequestException:
                pass
        for source_url in candidate.get('source_urls', []):
            host = urlparse(source_url).hostname or ''
            if not source_url or host in {'arxiv.org', 'export.arxiv.org', 'openalex.org', 'dblp.org'}:
                continue
            if source_url.lower().endswith('.pdf'):
                candidate['pdf_urls'].append(source_url)
                continue
            try:
                raw, final = self.get(source_url)
                if raw.startswith(b'%PDF'):
                    candidate['pdf_urls'].append(final)
                    continue
                page = PageMetadata(raw.decode('utf-8', errors='replace'))
                title = page.get('citation_title', 'dc.title')
                if normalize_title(title) != normalize_title(candidate['title']):
                    continue
                official = official_landing(final, page, candidate['venue'])
                for key in ('citation_online_date', 'citation_publication_date') if official else ():
                    value = page.get(key).replace('/', '-')
                    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                        date.fromisoformat(value)
                        records.append({'url': final, 'kind': 'official-landing-page', 'publication_date': value,
                                        'date_field': key, 'title': title, 'metadata': page.meta, 'source_sha256': sha256(raw)})
                pdf = page.get('citation_pdf_url')
                if pdf:
                    candidate['pdf_urls'].insert(0 if official else len(candidate['pdf_urls']), urljoin(final, pdf))
                if official:
                    for link in page.links:
                        if (urlparse(link).path.lower().endswith('.pdf')
                                and re.search(r'supplement|appendi[xc]', link + ' ' + page.link_labels.get(link, ''), re.I)):
                            candidate['supplements'].append({'url': urljoin(final, link), 'article_url': final})
                candidate['pdf_urls'].extend(urljoin(final, link) for link in page.links if link.lower().endswith('.pdf'))
                candidate['abstract'] = candidate.get('abstract') or page.get('citation_abstract', 'dc.description')
                candidate.setdefault('identifiers', {}).setdefault('doi', []).extend(
                    value for value in page.meta.get('citation_doi', []) if value)
            except (requests.RequestException, ValueError):
                continue
        if not records:
            raise EvidenceError('No exact official publication date could be verified')
        if incomplete_online_date:
            exact_online = [record for record in records if record.get('date_field') == 'citation_online_date'
                            and [int(n) for n in record['publication_date'].split('-')][:len(incomplete_online_date)] == incomplete_online_date]
            if not exact_online:
                raise EvidenceError('First online publication date is incomplete; a later print date cannot replace it')
        candidate['publication_date'] = min(record['publication_date'] for record in records)
        candidate['publication_evidence'] = records
        candidate['supplements'] = list({s['url']: s for s in candidate['supplements']}.values())
        supplements = {s['url'] for s in candidate['supplements']}
        candidate['pdf_urls'] = list(dict.fromkeys(candidate['pdf_urls']))
        candidate['pdf_urls'] = [url for url in candidate['pdf_urls'] if url not in supplements]
        if not candidate['pdf_urls'] and doi:
            try:
                data, _ = self.json('https://api.openalex.org/works/https://doi.org/' + quote(doi, safe='/'))
                candidate['pdf_urls'] = [loc['pdf_url'] for loc in data.get('locations', []) if loc.get('pdf_url')]
            except (requests.RequestException, ValueError):
                pass
        candidate['candidate_id'] = work_id(candidate)
        return candidate

    def influence_evidence(self, url, excerpt):
        if not url or not excerpt.strip():
            raise EvidenceError('Classic lacks continuing-influence evidence')
        raw, final = self.get(url)
        if raw.startswith(b'%PDF'):
            with fitz.open(stream=raw, filetype='pdf') as document:
                text = '\n'.join(page.get_text() for page in document)
        else:
            text = ' '.join(PageMetadata(raw.decode('utf-8', errors='replace')).text)
        if normalize_title(excerpt) not in normalize_title(text):
            raise EvidenceError('Classic influence excerpt does not occur in its source')
        return {'url': final, 'excerpt': excerpt, 'source_sha256': sha256(raw), 'source_text': text}

    def influence_candidates(self, candidate, day):
        """Retrieve later citing texts as evidence, never treat citation counts as influence."""
        doi = next((token[4:] for token in identifier_tokens(candidate.get('doi', '')) if token.startswith('doi:')), '')
        if doi:
            record, _ = self.json('https://api.openalex.org/works/https://doi.org/' + quote(doi, safe='/'))
        else:
            data, _ = self.json('https://api.openalex.org/works', {'search': candidate['title'], 'per-page': 5})
            record = next((r for r in data.get('results', []) if normalize_title(r.get('title', '')) == normalize_title(candidate['title'])), {})
        if not record.get('id') or normalize_title(record.get('title', '')) != normalize_title(candidate['title']):
            return []
        data, _ = self.json('https://api.openalex.org/works', {
            'filter': f'cites:{record["id"].split("/")[-1]},from_publication_date:{candidate["publication_date"]},to_publication_date:{day}',
            'sort': 'publication_date:desc', 'per-page': 3})
        output = []
        for citing in data.get('results', []):
            locations = citing.get('locations', [])
            urls = [loc['pdf_url'] for loc in locations if loc.get('pdf_url')]
            urls += [loc['landing_page_url'] for loc in locations if loc.get('landing_page_url')]
            for url in dict.fromkeys(urls):
                try:
                    raw, final = self.get(url, max_bytes=int(self.documents.get('max_pdf_bytes', 50_000_000)))
                    if raw.startswith(b'%PDF'):
                        with fitz.open(stream=raw, filetype='pdf') as document:
                            text = '\n'.join(page.get_text() for page in document)
                    else:
                        text = ' '.join(PageMetadata(raw.decode('utf-8', errors='replace')).text)
                    if normalize_title(citing.get('title', '')) not in normalize_title(text):
                        continue
                    output.append({'url': final, 'title': citing['title'], 'source_text': text, 'source_sha256': sha256(raw)})
                    break
                except (requests.RequestException, ValueError, RuntimeError):
                    continue
        return output

    def full_paper(self, candidate, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        failures = []
        for url in candidate.get('pdf_urls', []):
            try:
                raw, final = self.get(url, max_bytes=int(self.documents.get('max_pdf_bytes', 50_000_000)))
                with fitz.open(stream=raw, filetype='pdf') as document:
                    if document.needs_pass or not 1 <= len(document) <= int(self.documents.get('max_pages', 100)):
                        raise EvidenceError('PDF unreadable or exceeds page limit; not truncating')
                    texts = [page.get_text(sort=True) for page in document]
                    if any(not text.strip() for text in texts):
                        raise EvidenceError('PDF includes pages without extractable text; verified OCR is required')
                    title = normalize_title(candidate['title'])
                    if title not in normalize_title(' '.join(texts[:2])):
                        raise EvidenceError('Full-paper title could not be matched to the verified publication')
                break
            except (requests.RequestException, ValueError, RuntimeError) as error:
                failures.append(f'{url}: {request_failure(error) if isinstance(error, requests.RequestException) else error}')
        else:
            raise EvidenceError('Complete paper unavailable: ' + '; '.join(failures))

        # A supplement is additional evidence, not an alternative main PDF. Fetch
        # it in the existing controller, which already owns bounded PDF retrieval.
        parts = [(raw, final, 'main')]
        for supplement in candidate.get('supplements', []):
            try:
                extra, resolved = self.get(supplement['url'], max_bytes=int(self.documents.get('max_pdf_bytes', 50_000_000)))
                parts.append((extra, resolved, 'supplement'))
            except (requests.RequestException, ValueError, RuntimeError) as error:
                raise EvidenceError('Required published supplement unavailable: ' + supplement['url']) from error
        # A linked author version can contain artifact/appendix evidence omitted
        # from the publisher PDF. Keep distinct copies for explicit comparison;
        # never infer completeness from page count or silently replace a version.
        for author_url in author_pdf_urls(candidate):
            if author_url in {source_url for _, source_url, _ in parts}:
                continue
            try:
                extra, resolved = self.get(author_url, max_bytes=int(self.documents.get('max_pdf_bytes', 50_000_000)))
                if sha256(extra) in {sha256(source) for source, _, _ in parts}:
                    continue
                with fitz.open(stream=extra, filetype='pdf') as author:
                    title_text = ' '.join(author[number].get_text(sort=True) for number in range(min(2, len(author))))
                    if normalize_title(candidate['title']) not in normalize_title(title_text):
                        raise EvidenceError('Author-copy title does not match the verified publication')
                parts.append((extra, resolved, 'author-version'))
            except (requests.RequestException, ValueError, RuntimeError) as error:
                detail = request_failure(error) if isinstance(error, requests.RequestException) else str(error)
                raise EvidenceError('Linked author version could not be verified: ' + author_url + ': ' + detail) from error
        receipts, pages = [], []
        with fitz.open() as combined:
            for index, (source, source_url, kind) in enumerate(parts):
                with fitz.open(stream=source, filetype='pdf') as part:
                    if part.needs_pass or not len(part) or len(combined) + len(part) > int(self.documents.get('max_pages', 100)):
                        raise EvidenceError('Complete paper and supplements unreadable or exceed page limit; not truncating')
                    if any(not page.get_text().strip() for page in part):
                        raise EvidenceError('Paper or supplement includes pages without extractable text; verified OCR is required')
                    source_path = directory / f'source-{index:02}.pdf'
                    source_path.write_bytes(source)
                    receipts.append({'pdf': str(source_path.resolve()), 'url': source_url, 'kind': kind,
                                     'sha256': sha256(source), 'first_page': len(combined) + 1, 'page_count': len(part)})
                    combined.insert_pdf(part)
            complete = combined.tobytes() if len(parts) > 1 else raw
            (directory / 'paper.pdf').write_bytes(complete)
            for number, page in enumerate(combined, 1):
                image = directory / f'page-{number:03}.png'
                page.get_pixmap(dpi=int(self.documents.get('render_dpi', 150)), alpha=False).save(image)
                part = next(p for p in receipts if p['first_page'] <= number < p['first_page'] + p['page_count'])
                pages.append({'page': number, 'text': page.get_text(sort=True), 'image': str(image.resolve()),
                              'image_sha256': sha256(image.read_bytes()), 'source_url': part['url'],
                              'source_page': number - part['first_page'] + 1, 'source_kind': part['kind']})
        logger.info('Complete paper acquired: %s; %s pages across %s documents', candidate['title'], len(pages), len(receipts))
        return {'pdf': str((directory / 'paper.pdf').resolve()), 'url': final,
                'sha256': sha256(complete), 'pages': pages, 'source_documents': receipts}
