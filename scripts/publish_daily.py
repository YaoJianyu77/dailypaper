#!/usr/bin/env python3
"""Validate, render, and transactionally archive one prepared daily report."""

from __future__ import annotations

import argparse
import copy
from contextlib import nullcontext
from datetime import date, datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlparse

import fitz

from content_store import get_repo_root
from recommendation_history import (HISTORY_PATH, assert_unchanged, atomic_write, history_lock,
                                    identities, json_bytes, load_history, sha256, work_id, write_history)
from report_settings import load_settings
from report_validation import (render_report, require, validate_analysis, validate_review,
                               validate_selection, validate_trends)


def safe_target(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and '..' not in path.parts, 'Unsafe publication path')
    target = (Path(root) / path).resolve()
    require(target.is_relative_to(Path(root).resolve()), 'Publication path escapes repository')
    return target


def validate_bundle(root, bundle, settings, *, allow_run_id=None):
    day = date.fromisoformat(bundle['date'])
    require(bundle['run_id'] == settings.run_id(day), 'Run ID does not match configured local date')
    require(bundle['settings_sha256'] == settings.sha256, 'Prepared report does not use current settings')
    validate_selection(bundle['papers'], settings, day, load_history(root), bundle['shortfall_reason'], allow_run_id)
    expected_assets = []
    for paper in bundle['papers']:
        validate_analysis(paper['analysis'], paper['document'], settings)
        validate_review(paper['review'], settings)
        require(paper['settings_sha256'] == settings.sha256, 'Paper used different settings')
        reviewed = {key: value for key, value in paper.items() if key not in {'review', 'reviewed_sha256'}}
        require(paper['reviewed_sha256'] == sha256(json_bytes(reviewed)), 'Paper changed after review')
        expected_assets.extend(paper['assets'])
    require(bundle['assets'] == expected_assets, 'Asset manifest differs from reviewed papers')
    validate_trends(bundle['trends'], bundle['papers'], settings)
    validate_review(bundle['review'], settings)
    require(bundle['report_markdown'] == render_report(bundle, settings), 'Report changed after assembly')
    rendering = bundle.get('rendering', {})
    require(rendering.get('report_sha256') == sha256(bundle['report_markdown'].encode()),
            'Missing or stale website browser verification')
    require(rendering.get('chromium_sandbox') is True and rendering.get('offline') is True,
            'Website browser safeguards were not verified')
    require(rendering.get('screenshots'), 'Website review has no rendered screenshots')
    for shot in rendering['screenshots']:
        require(sha256(Path(shot['path']).read_bytes()) == shot['sha256'], 'Website screenshot changed after review')
    paths = set()
    for asset in bundle['assets']:
        path = asset['path']
        require(path.startswith('content/assets/papers/') and '/images/' in path and path.endswith('.png'), 'Unexpected asset path')
        safe_target(root, path)
        require(path not in paths, 'Repeated asset path')
        paths.add(path)
        raw = Path(asset['source']).read_bytes()
        require(sha256(raw) == asset['sha256'], 'Visual changed after review')
        pixels = fitz.Pixmap(raw)
        require(pixels.width > 0 and pixels.height > 0, 'Visual cannot be decoded')


def verify_rendered(root, bundle, settings, *, output_dir=None):
    """Build the isolated article and capture actual desktop/mobile browser views."""
    class Visuals(HTMLParser):
        def __init__(self):
            super().__init__()
            self.images, self.tables = [], 0

        def handle_starttag(self, tag, attributes):
            attributes = dict(attributes)
            if tag == 'img' and attributes.get('src'):
                self.images.append(attributes['src'])
            if tag == 'table':
                self.tables += 1

    with (nullcontext(str(output_dir)) if output_dir else tempfile.TemporaryDirectory(prefix='dailypaper-render-')) as directory:
        staged = Path(directory)
        report = staged / 'content/daily' / f'{bundle["date"]}.md'
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(bundle['report_markdown'], encoding='utf-8')
        (staged / 'DAILY_REPORT_PRODUCT_REQUIREMENTS.md').write_text(settings.raw, encoding='utf-8')
        for asset in bundle['assets']:
            target = safe_target(staged, asset['path'])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset['source'], target)
        subprocess.run([sys.executable, str(Path(__file__).parent / 'build_site.py'), '--repo-root', str(staged)],
                       env={**os.environ, 'SITE_BASE_URL': '/dailypaper'}, check=True, capture_output=True, text=True)
        html = (staged / f'dist/daily/{bundle["date"]}/index.html').read_text()
        parsed = Visuals()
        parsed.feed(html)
        require(len(parsed.images) == len(bundle['assets']), 'Not all verified figures rendered in the daily article')
        table_count = sum(v['kind'] == 'table' for paper in bundle['papers'] for v in paper['analysis']['visuals'])
        require(parsed.tables == table_count, 'Verified tables did not render as HTML tables')
        for url in parsed.images:
            require(url.startswith('/dailypaper/assets/papers/'), 'Image URL ignores site base path')
            target = safe_target(staged / 'dist', unquote(urlparse(url).path.removeprefix('/dailypaper/')))
            pixels = fitz.Pixmap(str(target))
            require(pixels.width > 0 and pixels.height > 0, 'Rendered figure is broken')
        from browser_render import inspect_site
        rendering = inspect_site(staged / 'dist', f'daily/{bundle["date"]}/', staged / 'screenshots',
                                 len(bundle['assets']), table_count)
        return {**rendering, 'report_sha256': sha256(bundle['report_markdown'].encode())}


def verify_archived_run(root, run):
    day = run.get('local_date') or run['run_id'].rsplit(':', 1)[-1]
    # Retain historical path evidence while following the existing migrated layout.
    relative = f'content/daily/{day}.md'
    report = safe_target(root, relative)
    require(report.is_file(), 'Archived run report is missing; do not select replacements')
    if run.get('report_sha256'):
        require(sha256(report.read_bytes()) == run['report_sha256'], 'Archived report hash differs from history')
    else:
        require(run.get('report_blob_sha'), 'Archived run lacks verifiable report identity')
        raw = report.read_bytes()
        import hashlib
        blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
        require(blob == run['report_blob_sha'], 'Archived report blob differs from history')
    for asset in run.get('visual_assets', []):
        path = asset.get('path') or asset.get('repo_path')
        require(path and sha256(safe_target(root, path).read_bytes()) == asset['sha256'], 'Archived visual differs from history')
    return relative


def _create_or_verify(path, raw):
    if path.exists():
        require(path.read_bytes() == raw, f'Existing content differs; refusing to overwrite {path}')
    else:
        atomic_write(path, raw)


def publish(root, bundle, *, before_finalize=None):
    root = Path(root)
    settings = load_settings(root)
    run_id = bundle['run_id']
    report_path = f'content/daily/{bundle["date"]}.md'
    with history_lock(root):
        snapshot = load_history(root)
        prior = snapshot.run(run_id)
        if prior and prior['status'] in {'archived', 'completed'}:
            verify_archived_run(root, prior)
            return {'status': 'already_archived', 'paths': [], 'run_id': run_id}
        validate_bundle(root, bundle, settings, allow_run_id=run_id if prior else None)
        verify_rendered(root, bundle, settings)
        raw_report = bundle['report_markdown'].encode()
        manifest = [{'path': asset['path'], 'sha256': asset['sha256']} for asset in bundle['assets']]
        signature = sha256(json_bytes({'report': sha256(raw_report), 'assets': manifest}))
        if prior:
            require(prior['status'] == 'reserved' and prior.get('artifact_sha256') == signature,
                    'Retry differs from the reserved report; recover the original prepared bundle')
        else:
            require(not safe_target(root, report_path).exists(), 'Report already exists; refusing to overwrite it')
            assert_unchanged(snapshot)
            data = snapshot.reconciled()
            now = datetime.now(timezone.utc).isoformat()
            for paper in bundle['papers']:
                tokens = identities(paper)
                data['papers'].append({
                    'work_id': work_id(paper), 'title': paper['title'], 'title_aliases': paper.get('title_aliases', []),
                    'authors': paper['authors'], 'identifiers': {prefix: [v.split(':', 1)[1] for v in sorted(tokens) if v.startswith(prefix + ':')]
                                                               for prefix in ('doi', 'arxiv', 'dblp')},
                    'category': paper['category'], 'venue': paper['venue'], 'publication_date': paper['publication_date'],
                    'publication_date_evidence': paper['publication_evidence'], 'source_urls': paper.get('source_urls', []),
                    'continuing_influence': {k: v for k, v in paper.get('continuing_influence', {}).items() if k != 'source_text'},
                    'full_paper_sha256': paper['document']['sha256'], 'run_id': run_id, 'status': 'reserved',
                    'reserved_at': now, 'report_path': report_path, 'verification': paper['counts']})
            data['runs'].append({'run_id': run_id, 'local_date': bundle['date'], 'timezone': settings.timezone,
                                 'status': 'reserved', 'reserved_at': now, 'settings_sha256': settings.sha256,
                                 'work_ids': [work_id(p) for p in bundle['papers']], 'date_windows': settings.windows(date.fromisoformat(bundle['date'])),
                                 'report_path': report_path, 'report_sha256': sha256(raw_report),
                                 'visual_assets': manifest, 'artifact_sha256': signature})
            write_history(snapshot, data)
        for asset in bundle['assets']:
            _create_or_verify(safe_target(root, asset['path']), Path(asset['source']).read_bytes())
        _create_or_verify(safe_target(root, report_path), raw_report)
        if before_finalize:
            before_finalize()  # Failure injection for isolated transaction tests.
        current = load_history(root)
        old_evidence = {key: value for key, value in snapshot.source_hashes.items() if key not in {HISTORY_PATH, report_path}}
        new_evidence = {key: value for key, value in current.source_hashes.items() if key not in {HISTORY_PATH, report_path}}
        require(old_evidence == new_evidence, 'Other archived evidence changed during publication')
        data = copy.deepcopy(current.data)
        for paper in data['papers']:
            if paper.get('run_id') == run_id:
                paper['status'] = 'archived'
        run = next(r for r in data['runs'] if r['run_id'] == run_id)
        run['status'] = 'archived'
        run['archived_at'] = datetime.now(timezone.utc).isoformat()
        verify_archived_run(root, run)
        write_history(current, data)
        verify_archived_run(root, load_history(root).run(run_id))
    return {'status': 'archived', 'run_id': run_id,
            'paths': [report_path, *[a['path'] for a in bundle['assets']], HISTORY_PATH]}


def main():
    parser = argparse.ArgumentParser(description='Publish a fully reviewed preparation bundle')
    parser.add_argument('--repo-root')
    parser.add_argument('--input', required=True)
    args = parser.parse_args()
    root = get_repo_root(args.repo_root, __file__)
    bundle = json.loads((root / args.input).read_text())
    print(json.dumps(publish(root, bundle)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
