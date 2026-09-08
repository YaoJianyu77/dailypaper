"""One resumable generation chain, shared by local and hosted transports."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import requests

from content_store import get_repo_root
from paper_sources import EvidenceError, Sources
from recommendation_history import atomic_write, json_bytes, load_history, match_record, normalize_title, sha256, work_id
from report_settings import load_infrastructure, load_settings
from report_validation import (prepare_visuals, render_report, require, validate_analysis,
                               validate_review, validate_selection, validate_trends)


def save_checkpoint(path, value):
    atomic_write(path, json_bytes(value), replace=True)


def make_backend(name, root, settings, infrastructure):
    if name == 'codex':
        from codex_enrich import CodexBackend
        return CodexBackend(root, settings, infrastructure)
    raise RuntimeError('The unified settings require the verified strongest Codex model and reasoning setting. Hosted API transports cannot verify this policy; use the local Codex runner. No downgrade selected.')


def discovery(root, settings, day, sources, history):
    verified, rejected = [], []
    for candidate in sources.discover(settings, day):
        previous, reason = match_record(candidate, history.records)
        if previous:
            rejected.append({'title': candidate['title'], 'reason': reason})
            continue
        try:
            paper = sources.verify_publication(candidate)
            category = settings.category(paper['publication_date'], day)
            if not category or not settings.quotas[category]:
                raise EvidenceError('Outside current date windows')
            paper['category'] = category
            previous, reason = match_record(paper, history.records + verified)
            if previous:
                raise EvidenceError(reason)
            verified.append(paper)
        except (EvidenceError, ValueError) as error:
            rejected.append({'title': candidate['title'], 'reason': str(error)})
    require(verified, 'No eligible publication evidence found; generation stopped')
    return {'date': day.isoformat(), 'settings_sha256': settings.sha256,
            'windows': settings.windows(day), 'candidates': verified, 'rejected': rejected,
            'source_failures': list(sources.failures)}


def select(root, settings, day, backend, sources, pool, history):
    require(pool['settings_sha256'] == settings.sha256 and pool['date'] == day.isoformat(),
            'Discovery output uses different settings or date')
    choices = backend.generate('select', {'date': day.isoformat(), 'date_windows': settings.windows(day),
        'candidates': pool['candidates'], 'prior_recommendation_evidence': history.prompt_records,
        'coverage_limits': pool.get('source_failures', [])})
    from pipeline_prompts import stage_schema
    import jsonschema
    jsonschema.validate(choices, stage_schema('select', settings))
    candidates = {paper['candidate_id']: paper for paper in pool['candidates']}
    papers = []
    shortfalls = [choices['shortfall_reason']] if choices['shortfall_reason'] else []
    for choice in choices['selected']:
        require(choice['candidate_id'] in candidates, 'Model selected an unverified candidate')
        paper = copy.deepcopy(candidates[choice['candidate_id']])
        paper.update({key: choice[key] for key in ('topic_fit', 'identity_evidence', 'title_aliases')})
        if paper['category'] == 'classic':
            try:
                if choice['influence_url'] and choice['influence_quote']:
                    paper['continuing_influence'] = sources.influence_evidence(choice['influence_url'], choice['influence_quote'])
                else:
                    evidence = sources.influence_candidates(paper, day)
                    if not evidence:
                        raise EvidenceError('No inspectable later-use evidence was retrieved')
                    decision = backend.generate('influence', {'paper': paper, 'sources': evidence})
                    jsonschema.validate(decision, stage_schema('influence', settings))
                    verified = next((item for item in evidence if item['url'] == decision['url']), None)
                    if not verified or not decision['excerpt'].strip() or not decision['reason'].strip():
                        raise EvidenceError(decision['reason'] or 'Continuing influence was not established')
                    if normalize_title(decision['excerpt']) not in normalize_title(verified['source_text']):
                        raise EvidenceError('Influence excerpt is absent from the retrieved source')
                    paper['continuing_influence'] = {**verified, 'excerpt': decision['excerpt'], 'reason': decision['reason']}
            except (EvidenceError, requests.RequestException) as error:
                shortfalls.append(f'Classic slot unfilled for {paper["title"]}: {error}')
                continue
        papers.append(paper)
    papers.sort(key=lambda paper: paper['category'] != 'latest')
    reason = ' '.join(shortfalls)
    validate_selection(papers, settings, day, history, reason)
    return {'papers': papers, 'shortfall_reason': reason}


def prepare(root, backend_name='codex', *, day=None, sources=None, backend=None, pool=None, stage_dir=None):
    """Prepare and verify artifacts only; publication owns production writes."""
    root = Path(root)
    settings = load_settings(root)
    infrastructure = load_infrastructure(root)
    day = day or settings.local_date()
    run_id = settings.run_id(day)
    history = load_history(root)
    prior_run = history.run(run_id)
    if prior_run and prior_run['status'] in {'archived', 'completed'}:
        from publish_daily import verify_archived_run
        verify_archived_run(root, prior_run)
        return {'already_archived': True, 'run_id': run_id, 'date': day.isoformat()}
    stage = Path(stage_dir) if stage_dir else root / '.cache/dailypaper/runs' / day.isoformat()
    stage.mkdir(parents=True, exist_ok=True)
    sources = sources or Sources(infrastructure)
    backend = backend or make_backend(backend_name, root, settings, infrastructure)
    require(getattr(backend, 'settings', settings).sha256 == settings.sha256,
            'Settings changed after runtime verification; restart preparation with current settings')
    if hasattr(backend, 'preflight'):
        backend.preflight()
    runtime = backend.bind_report(stage) if hasattr(backend, 'bind_report') else None
    if prior_run:
        bundle_path = stage / 'bundle.json'
        require(bundle_path.is_file(), 'Reserved run has no recovery bundle; recover the original artifacts before retrying')
        recovered = json.loads(bundle_path.read_text())
        if runtime is not None:
            from codex_runtime import resolution_identity
            require(resolution_identity(recovered.get('runtime', {})) == resolution_identity(runtime),
                    'Reserved report used a different runtime configuration; generation stopped')
        return recovered
    checkpoint_path = stage / 'selection.json'
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text())
        require(checkpoint['settings_sha256'] == settings.sha256,
                'Settings changed during a pending run; keep its selection and explicitly revalidate before resuming')
        chosen = checkpoint['selection']
    else:
        pool = pool or discovery(root, settings, day, sources, history)
        chosen = select(root, settings, day, backend, sources, pool, history)
        save_checkpoint(checkpoint_path, {'settings_sha256': settings.sha256, 'run_id': run_id, 'selection': chosen})
    validate_selection(chosen['papers'], settings, day, load_history(root), chosen['shortfall_reason'])
    bundle = {'date': day.isoformat(), 'run_id': run_id, 'settings_sha256': settings.sha256,
              'shortfall_reason': chosen['shortfall_reason'], 'papers': [], 'assets': []}
    if runtime is not None:
        bundle['runtime'] = runtime
    for selected in chosen['papers']:
        paper = copy.deepcopy(selected)
        directory = stage / ('paper-' + sha256(work_id(paper).encode())[:20])
        directory.mkdir(parents=True, exist_ok=True)
        cached = directory / 'reviewed.json'
        if cached.exists():
            paper = json.loads(cached.read_text())
            require(paper['settings_sha256'] == settings.sha256, 'Paper checkpoint uses stale settings')
        else:
            document = sources.full_paper(paper, directory)
            context = {'date': day.isoformat(), 'paper': paper, 'document': document,
                       'image_order': [f'PDF page {page["page"]}' for page in document['pages']]}
            images = [page['image'] for page in document['pages']]
            analysis = backend.generate('analyze', context, images)
            counts = validate_analysis(analysis, document, settings)
            assets, blocks = prepare_visuals(paper, analysis, document, directory / 'prepared')
            paper.update(document=document, analysis=analysis, assets=assets, visual_blocks=blocks,
                         counts=counts, settings_sha256=settings.sha256)
            review = backend.generate('review', {'kind': 'paper', 'paper': paper,
                    'prior_recommendation_evidence': history.prompt_records,
                    'date_windows': settings.windows(day),
                    'image_order': context['image_order'] + [asset['path'] for asset in assets]},
                    images + [asset['source'] for asset in assets])
            validate_review(review, settings)
            paper['review'] = review
            paper['reviewed_sha256'] = sha256(json_bytes({key: value for key, value in paper.items() if key not in {'review', 'reviewed_sha256'}}))
            save_checkpoint(cached, paper)
        validate_analysis(paper['analysis'], paper['document'], settings)
        validate_review(paper['review'], settings)
        require(paper['reviewed_sha256'] == sha256(json_bytes({key: value for key, value in paper.items() if key not in {'review', 'reviewed_sha256'}})),
                'Reviewed paper checkpoint was modified')
        bundle['papers'].append(paper)
        bundle['assets'].extend(paper['assets'])
    trends_path = stage / 'trends.json'
    if trends_path.exists():
        trends = json.loads(trends_path.read_text())
    else:
        trends = backend.generate('trends', {'papers': [{'work_id': work_id(p), 'title': p['title'],
                    'category': p['category'], 'analysis': p['analysis']} for p in bundle['papers']]})
        validate_trends(trends, bundle['papers'], settings)
        save_checkpoint(trends_path, trends)
    bundle['trends'] = trends
    validate_trends(trends, bundle['papers'], settings)
    bundle['report_markdown'] = render_report(bundle, settings)
    bundle['review'] = backend.generate('review', {'kind': 'trends', 'report_markdown': bundle['report_markdown'],
        'papers': [{'work_id': work_id(p), 'title': p['title'], 'category': p['category'], 'analysis': p['analysis'],
                    'review': p['review']} for p in bundle['papers']], 'trends': trends})
    validate_review(bundle['review'], settings)
    from publish_daily import validate_bundle, verify_rendered
    validate_bundle(root, bundle, settings)
    verify_rendered(root, bundle, settings)
    save_checkpoint(stage / 'bundle.json', bundle)
    return bundle


def discovery_cli():
    parser = argparse.ArgumentParser(description='Discover papers using the six unified settings')
    parser.add_argument('--repo-root')
    parser.add_argument('--output', required=True)
    parser.add_argument('--config', help='Infrastructure YAML only')
    args = parser.parse_args()
    root = get_repo_root(args.repo_root, __file__)
    settings = load_settings(root)
    result = discovery(root, settings, settings.local_date(), Sources(load_infrastructure(root, args.config)), load_history(root))
    output = Path(args.output)
    save_checkpoint(output if output.is_absolute() else root / output, result)
    return 0


def enrichment_cli(backend_name):
    parser = argparse.ArgumentParser(description='Prepare a complete reviewed report without publishing')
    parser.add_argument('--repo-root')
    parser.add_argument('--input', help='Verified discovery output; omit to discover papers')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = get_repo_root(args.repo_root, __file__)
    pool = json.loads((root / args.input).read_text()) if args.input else None
    result = prepare(root, backend_name, pool=pool)
    output = Path(args.output)
    save_checkpoint(output if output.is_absolute() else root / output, result)
    return 0
