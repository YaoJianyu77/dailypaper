"""The resumable DailyPaper preparation chain used by the production runner."""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path

import requests

from codex_enrich import CodexBackend
from paper_sources import EvidenceError, Sources, request_failure
from recommendation_history import atomic_write, json_bytes, load_history, match_record, normalize_title, sha256, work_id
from report_settings import load_infrastructure, load_settings
from report_validation import (ValidationError, prepare_visuals, render_report, require, validate_analysis,
                               validate_review, validate_selection, validate_trends)

logger = logging.getLogger(__name__)


def save_checkpoint(path, value):
    atomic_write(path, json_bytes(value), replace=True)


def discovery(root, settings, day, sources, history, *, backend=None, diagnostics_path=None):
    verified, rejected = [], []
    def verify(candidates):
        for candidate in candidates:
            try:
                require(candidate['venue'] in settings.venues, 'Venue is not configured')
                previous, reason = match_record(candidate, history.records + verified)
                if previous:
                    raise EvidenceError('Previously recommended or duplicate work: ' + reason)
                paper = sources.verify_publication(candidate)
                category = settings.category(paper['publication_date'], day)
                if not category or not settings.quotas[category]:
                    raise EvidenceError('Outside current date windows')
                paper['category'] = category
                previous, reason = match_record(paper, history.records + verified)
                if previous:
                    raise EvidenceError('Previously recommended or duplicate work: ' + reason)
                verified.append(paper)
                logger.info('Publication verified: %s (%s, %s)', paper['title'], paper['venue'], paper['publication_date'])
            except (ValueError, requests.RequestException) as error:
                reason = request_failure(error) if isinstance(error, requests.RequestException) else str(error)
                rejected.append({'title': candidate['title'], 'reason': reason})
                logger.info('Candidate excluded: %s: %s', candidate['title'], reason)

    logger.info('Discovering configured venues; complete history contains %s source records', len(history.records))
    verify(sources.discover(settings, day))
    counts = {category: sum(p['category'] == category for p in verified) for category in settings.quotas}
    if backend is not None and any(counts[key] < quota for key, quota in settings.quotas.items()):
        logger.info('Index coverage insufficient (%s); searching official sources with verified Codex runtime', counts)
        from pipeline_prompts import stage_schema
        import jsonschema
        result = backend.generate('discover', {'date': day.isoformat(), 'date_windows': settings.windows(day),
            'prior_recommendation_evidence': history.prompt_records, 'existing_verified_candidates': verified,
            'source_failures': list(sources.failures),
            'max_candidates_per_venue': int(sources.options.get('max_candidates_per_venue', 12))})
        jsonschema.validate(result, stage_schema('discover', settings))
        for limitation in result['coverage_limits']:
            sources.failure(limitation)
        used = {}
        candidates = []
        for candidate in result['candidates']:
            venue = candidate['venue']
            used[venue] = used.get(venue, 0) + 1
            if used[venue] > int(sources.options.get('max_candidates_per_venue', 12)):
                sources.failure(f'{venue}: web discovery exceeded the configured candidate budget; extra leads excluded')
                continue
            candidate['candidate_id'] = work_id(candidate)
            candidates.append(candidate)
        verify(candidates)
    result = {'date': day.isoformat(), 'settings_sha256': settings.sha256,
            'windows': settings.windows(day), 'candidates': verified, 'rejected': rejected,
            'source_failures': list(sources.failures)}
    if diagnostics_path:
        save_checkpoint(diagnostics_path, result)
    logger.info('Discovery finished: %s verified, %s excluded, %s coverage limits',
                len(verified), len(rejected), len(sources.failures))
    details = '; '.join([*sources.failures, *[f'{r["title"]}: {r["reason"]}' for r in rejected[:5]]])
    require(verified, 'No eligible publication evidence found; generation stopped. ' + details)
    return result


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


def prepare(root, *, day=None, sources=None, backend=None, pool=None, stage_dir=None):
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
    backend = backend or CodexBackend(root, settings, infrastructure)
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
        pool = pool or discovery(root, settings, day, sources, history, backend=backend,
                                 diagnostics_path=stage / 'discovery.json')
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
            for attempt in range(3):
                analysis = backend.generate('analyze', context, images)
                try:
                    counts = validate_analysis(analysis, document, settings)
                    assets, blocks = prepare_visuals(paper, analysis, document, directory / 'prepared')
                    paper = {**copy.deepcopy(selected), 'document': document, 'analysis': analysis,
                             'assets': assets, 'visual_blocks': blocks, 'counts': counts, 'settings_sha256': settings.sha256}
                    review = backend.generate('review', {'kind': 'paper', 'paper': paper,
                            'prior_recommendation_evidence': history.prompt_records,
                            'date_windows': settings.windows(day),
                            'image_order': context['image_order'] + [asset['path'] for asset in assets]},
                            images + [asset['source'] for asset in assets])
                    validate_review(review, settings)
                    break
                except ValidationError as error:
                    if attempt == 2:
                        raise
                    logger.warning('Revising the same paper after validation: %s: %s', selected['title'], error)
                    context = {**context, 'prior_analysis': analysis, 'revision_feedback': str(error)}
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
        trends = backend.generate('trends', {'date': day.isoformat(), 'selection_shortfall': chosen['shortfall_reason'],
                    'papers': [{'work_id': work_id(p), 'title': p['title'],
                    'category': p['category'], 'analysis': p['analysis']} for p in bundle['papers']]})
        validate_trends(trends, bundle['papers'], settings)
        save_checkpoint(trends_path, trends)
    bundle['trends'] = trends
    validate_trends(trends, bundle['papers'], settings)
    bundle['report_markdown'] = render_report(bundle, settings)
    from publish_daily import validate_bundle, verify_rendered
    bundle['rendering'] = verify_rendered(root, bundle, settings, output_dir=stage / 'website')
    screenshots = bundle['rendering']['screenshots']
    bundle['review'] = backend.generate('review', {'kind': 'trends', 'report_markdown': bundle['report_markdown'],
        'papers': [{'work_id': work_id(p), 'title': p['title'], 'category': p['category'], 'analysis': p['analysis'],
                    'review': p['review']} for p in bundle['papers']], 'trends': trends,
        'selection_shortfall': bundle['shortfall_reason'],
        'rendering': bundle['rendering'], 'image_order': [f'{s["viewport_width"]}px {s["item"]}' for s in screenshots]},
        [s['path'] for s in screenshots])
    validate_review(bundle['review'], settings)
    validate_bundle(root, bundle, settings)
    save_checkpoint(stage / 'bundle.json', bundle)
    return bundle
