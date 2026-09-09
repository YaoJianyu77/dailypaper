"""Validate evidence and render only complete, reviewed report artifacts."""

from datetime import date
from pathlib import Path
import re

import fitz
import jsonschema

from content_store import dump_markdown
from pipeline_prompts import stage_schema
from recommendation_history import sha256, work_id
from site_content import markdown_parser, plain_text


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def word_count(text):
    return len(re.findall(r'[\u4e00-\u9fff]|[^\W_]+(?:[’\x27-][^\W_]+)*', plain_text(text)))


def validate_document(document):
    require(document.get('source_documents'),
            'Missing complete-paper source receipts; preserve the selection and revalidate its original documents')
    raw = Path(document['pdf']).read_bytes()
    require(sha256(raw) == document['sha256'], 'PDF changed after acquisition')
    with fitz.open(stream=raw, filetype='pdf') as pdf:
        require(len(document['pages']) == len(pdf), 'Incomplete full-paper input')
        require([p['page'] for p in document['pages']] == list(range(1, len(pdf) + 1)), 'Missing or reordered PDF pages')
        for page, info in zip(pdf, document['pages']):
            require(info['text'] == page.get_text(sort=True), 'Full-paper text was altered or truncated')
            require(sha256(Path(info['image']).read_bytes()) == info['image_sha256'], 'PDF page image changed')
        offset = 0
        for source in document['source_documents']:
            source_raw = Path(source['pdf']).read_bytes()
            require(sha256(source_raw) == source['sha256'], 'Original paper or supplement changed')
            with fitz.open(stream=source_raw, filetype='pdf') as part:
                require(source['first_page'] == offset + 1 and source['page_count'] == len(part), 'Source page mapping changed')
                for page in part:
                    require(offset < len(pdf) and page.get_text(sort=True) == pdf[offset].get_text(sort=True),
                            'Paper or supplement omitted or changed during assembly')
                    offset += 1
        require(offset == len(pdf), 'Incomplete paper and supplement source receipt')


def validate_analysis(analysis, document, settings):
    jsonschema.validate(analysis, stage_schema('analyze', settings))
    validate_document(document)
    require(analysis['document_sha256'] == document['sha256'], 'Analysis used a different paper')
    require(sorted(analysis['read_pages']) == [p['page'] for p in document['pages']], 'Full-paper reading receipt incomplete')
    require([s['heading'] for s in analysis['sections']] == list(settings.headings), 'Summary headings or order differ from settings')
    sections = analysis['sections']
    for section in sections:
        require(section['text'].strip(), f'Empty summary section: {section["heading"]}')
        tokens = markdown_parser().parse(section['text'])
        require(not any(token.type in {'heading_open', 'html_block', 'table_open', 'fence'} for token in tokens),
                'Summary section contains an extra heading, unrendered block, or undeclared table')
        require(not any(child.type == 'image' for token in tokens for child in token.children or []),
                'Visuals must be declared and verified before embedding')
    brief = word_count(sections[0]['text'])
    assessment = word_count(sections[-1]['text'])
    require(settings.brief_min <= brief <= settings.brief_max, f'Opening brief has {brief} words')
    require(assessment <= settings.assessment_max, f'Final assessment has {assessment} words')
    require(len(re.split(r'\n\s*\n', sections[-1]['text'].strip())) == 1, 'Final assessment must be one paragraph')
    count = sum(word_count(section['text']) for section in sections)
    count += sum(word_count(v['explanation']) + word_count(v['caveat']) for v in analysis['visuals'])
    require(settings.summary_min <= count <= min(settings.summary_max, settings.hard_max), f'Summary has {count} words excluding captions')
    for item in [*analysis['insights'], *analysis['findings'], *analysis['visuals']]:
        require(1 <= item['page'] <= len(document['pages']), 'Evidence refers to a missing PDF page')
    for visual in analysis['visuals']:
        require(all(visual[k].strip() for k in ('label', 'caption', 'explanation', 'caveat')), 'Visual evidence is incomplete')
        if visual['kind'] == 'crop':
            left, top, right, bottom = visual['bbox']
            require(left < right and top < bottom, 'Figure crop has invalid bounds')
        else:
            require(visual['headers'] and visual['rows'], 'Table has no renderable cells')
            require(all(len(row) == len(visual['headers']) for row in visual['rows']), 'Table columns do not align')
    return {'summary_words': count, 'brief_words': brief, 'assessment_words': assessment,
            'pages': len(document['pages']), 'visuals': len(analysis['visuals'])}


def validate_review(review, settings):
    jsonschema.validate(review, stage_schema('review', settings))
    require(review['approved'] and not review['problems'], 'Final review rejected the draft: ' + '; '.join(review['problems']))
    for key, value in review.items():
        if isinstance(value, dict):
            require(value['passed'] and value['evidence'].strip(), f'Unverified review check: {key}')


def validate_selection(papers, settings, day, history, shortfall_reason='', run_id=None):
    require(bool(papers), 'No verified papers selected; no empty completed report will be published')
    history.assert_new(papers, run_id=run_id)
    counts = {key: 0 for key in settings.quotas}
    for paper in papers:
        require(paper['venue'] in settings.venues, 'Paper venue is no longer configured')
        require(paper.get('publication_evidence'), 'Missing verified official publication evidence')
        category = settings.category(paper['publication_date'], day)
        require(category is not None and category == paper['category'], 'Paper outside its configured date window')
        require(paper.get('topic_fit') and paper.get('identity_evidence'), 'Topic or identity check missing')
        if category == 'classic':
            require(paper.get('continuing_influence'), 'Classic influence evidence missing')
        counts[category] += 1
    require(all(counts[key] <= quota for key, quota in settings.quotas.items()), 'Selection exceeds configured quotas')
    if counts != settings.quotas:
        require(settings.allow_underfill and bool(shortfall_reason.strip()), 'Unfilled slots need the configured shortfall policy and explanation')
    return counts


def validate_trends(trends, papers, settings):
    jsonschema.validate(trends, stage_schema('trends', settings))
    if any(sum(p['category'] == category for p in papers) < quota for category, quota in settings.quotas.items()):
        require(trends['coverage_note'].strip(), 'Unfilled slots need a reader-facing coverage explanation')
    by_id = {work_id(p): p for p in papers}
    for trend in trends['trends']:
        supporting = set(trend['supporting_work_ids'])
        require(supporting <= by_id.keys(), 'Trend cites a paper outside this report')
        require(sum(by_id[key]['category'] == 'latest' for key in supporting) >= settings.trend_min_latest,
                'Trend lacks the configured latest-paper support')
        require(trend['title'].strip() and trend['text'].strip(), 'Empty research trend')
    require(trends['trends'] or trends['insufficient_evidence'].strip(), 'Missing trends or evidence-shortfall explanation')


def table_markdown(visual):
    def cell(value):
        return str(value).replace('\\', '\\\\').replace('|', '\\|').replace('\n', ' ')
    rows = [visual['headers'], ['---'] * len(visual['headers']), *visual['rows']]
    return '\n'.join('| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows)


def prepare_visuals(paper, analysis, document, directory, dpi=200):
    directory = Path(directory)
    assets, blocks = [], []
    key = 'work-' + sha256(work_id(paper).encode())[:20]
    with fitz.open(document['pdf']) as pdf:
        for index, visual in enumerate(analysis['visuals'], 1):
            if visual['kind'] == 'crop':
                page = pdf[visual['page'] - 1]
                x0, y0, x1, y1 = visual['bbox']
                clip = fitz.Rect(x0 * page.rect.width, y0 * page.rect.height, x1 * page.rect.width, y1 * page.rect.height)
                relative = f'content/assets/papers/{key}/images/figure-{index}.png'
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                page.get_pixmap(clip=clip, dpi=dpi, alpha=False).save(path)
                assets.append({'path': relative, 'source': str(path.resolve()), 'sha256': sha256(path.read_bytes())})
                label = visual['label'].replace('[', '\\[').replace(']', '\\]')
                rendered = f'![{label}](/{relative.removeprefix("content/")})'
            else:
                rendered = table_markdown(visual)
            labels = analysis['visual_labels']
            source = document['pages'][visual['page'] - 1]
            source_page = source['source_page']
            source_url = source['source_url'].split('#')[0] + f'#page={source_page}'
            reference = f'[{labels["pdf_page"]} {source_page}]({source_url})'
            blocks.append(f'{rendered}\n\n*{visual["label"]}, {reference}. {labels["paraphrased_caption"]}: {visual["caption"]}*\n\n'
                          f'{visual["explanation"]}\n\n{visual["caveat"]}')
    return assets, blocks


def render_report(bundle, settings):
    day = date.fromisoformat(bundle['date'])
    windows = settings.windows(day)
    labels = bundle['trends']['labels']
    lines = [f'# {labels["report_title"]} — {day}', '',
             f'**{labels["timezone"]}:** {settings.timezone}', '',
             f'**{labels["latest_window"]}:** {windows["latest"]["start"]} – {windows["latest"]["end"]} ({labels["inclusive"]}). '
             f'**{labels["classic_window"]}:** {windows["classic"]["start"]} – {windows["classic"]["end"]} ({labels["inclusive"]}).', '']
    if bundle['trends']['coverage_note']:
        lines.extend([bundle['trends']['coverage_note'], ''])
    numbers = {'latest': 0, 'classic': 0}
    paper_headings = []
    for paper in bundle['papers']:
        category = paper['category']
        numbers[category] += 1
        label = f'{labels[category]} {numbers[category]}'
        title = paper['title'].replace('\n', ' ')
        heading = f'{label} — {title}'
        paper_headings.append({'heading': heading, 'title': title, 'category': category})
        evidence_url = paper['publication_evidence'][0]['url']
        documents = paper['document']['source_documents']
        source_links = ' · '.join(f'[{labels["full_paper"]}'
            + (f' ({index}/{len(documents)})' if len(documents) > 1 else '') + f']({document["url"]})'
            for index, document in enumerate(documents, 1))
        lines.extend([f'## {heading}', '',
                      f'**{paper["venue"]} · {paper["publication_date"]} · {", ".join(paper["authors"])}.** '
                      f'[{labels["official_publication"]}]({evidence_url}) · {source_links}', ''])
        for index, section in enumerate(paper['analysis']['sections'], 1):
            lines.extend([f'### {index}. {section["heading"]}', '', section['text'], ''])
            if section['heading'] == paper['analysis']['visual_section']:
                lines.extend(['\n\n'.join(paper['visual_blocks']), ''])
    lines.extend([f'# {settings.trend_heading}', ''])
    by_id = {work_id(p): p['title'] for p in bundle['papers']}
    for trend in bundle['trends']['trends']:
        lines.extend([f'## {trend["title"]}', '', trend['text'], '',
                      labels['supporting_papers'] + ': ' + '; '.join(by_id[key] for key in trend['supporting_work_ids']) + '.', ''])
    if bundle['trends']['insufficient_evidence']:
        lines.extend([bundle['trends']['insufficient_evidence'], ''])
    return dump_markdown({'title': f'{labels["report_title"]} — {day}', 'date': day.isoformat(),
                          'trend_heading': settings.trend_heading, 'settings_sha256': settings.sha256,
                          'run_id': bundle['run_id'], 'paper_headings': paper_headings,
                          'paper_count': len(bundle['papers'])}, '\n'.join(lines))
