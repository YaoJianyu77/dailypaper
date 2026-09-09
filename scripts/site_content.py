"""Read existing report formats without rewriting archived research content."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

from markdown_it import MarkdownIt

from content_store import parse_frontmatter


GROUPS = {'Overview', 'Papers', 'Lead Paper', 'Supporting Reads', 'Classic Revisit', '最新论文', '经典论文'}
TRENDS = {"Clear Research Trends in Today's Papers", '今日论文中的明显研究趋势'}
MODERN_PAPER = re.compile(r'^(Latest\s+\d+|Classic)\s+[—–-]\s+(.+)$')
LEGACY_PAPER = re.compile(r'^(\d+|Lead|Classic)\.\s+(.+)$')


@dataclass
class Paper:
    title: str
    category: str
    body: str
    anchor: str
    excerpt: str

    @property
    def short_title(self):
        if ' — ' in self.title:
            tail = self.title.rsplit(' — ', 1)[1]
            if len(tail) < 36:
                return tail
        prefix = self.title.split(':', 1)[0]
        return prefix if len(prefix) < 48 else self.title


@dataclass
class Report:
    date: date
    title: str
    intro: str
    papers: list[Paper]
    trends: str
    trends_title: str
    source: Path
    source_spans: dict

    @property
    def path(self):
        return f'/reader/?date={self.date.isoformat()}'

    @property
    def month(self):
        return self.date.strftime('%Y-%m')

    @property
    def search_text(self):
        return ' '.join([self.date.isoformat(), self.date.strftime('%B %Y'), self.title,
                         *(paper.title for paper in self.papers)]).lower()


def markdown_parser():
    return MarkdownIt('commonmark', {'html': False}).enable(['table', 'strikethrough'])


def apply_base_url(url, base_url):
    if url.startswith('/') and not url.startswith('//'):
        return base_url + url
    return url


def md_to_html(text, base_url=''):
    md = markdown_parser()
    tokens = md.parse(text)

    def rewrite_links(items):
        for token in items:
            for attr in ('href', 'src'):
                value = token.attrGet(attr)
                if value:
                    token.attrSet(attr, apply_base_url(value, base_url))
            if token.type == 'image':
                token.attrSet('loading', 'lazy')
                token.attrSet('decoding', 'async')
            if token.children:
                rewrite_links(token.children)

    rewrite_links(tokens)
    for index, token in enumerate(tokens[:-2]):
        if token.type != 'paragraph_open':
            continue
        children = tokens[index + 1].children or []
        if len(children) == 1 and children[0].type == 'image':
            token.attrSet('class', 'figure')
            if index + 4 < len(tokens) and tokens[index + 3].type == 'paragraph_open':
                caption = tokens[index + 4].children or []
                if caption and caption[0].type == 'em_open' and caption[-1].type == 'em_close':
                    tokens[index + 3].attrSet('class', 'figure-caption')
    return md.renderer.render(tokens, md.options, {})


def plain_text(text):
    pieces = []
    for token in markdown_parser().parse(text):
        if token.type == 'inline':
            pieces.append(''.join(' ' if t.type == 'softbreak' else t.content for t in token.children or []
                                  if t.type in {'text', 'code_inline', 'softbreak'}))
    return re.sub(r'\s+', ' ', ' '.join(pieces)).strip()


def paper_excerpt(body):
    brief = re.search(r'^###\s+1\.\s+Paper in brief\s*\n+([^#]+)', body, re.MULTILINE)
    quote = re.search(r'^>\s+(.+)$', body, re.MULTILINE)
    text = plain_text(brief.group(1) if brief else quote.group(1) if quote else '')
    if len(text) <= 250:
        return text
    sentence = re.match(r'^(.{60,250}?[.!?])(?:\s|$)', text)
    return sentence.group(1) if sentence else text[:247].rsplit(' ', 1)[0] + '…'


def read_report(path):
    raw = path.read_text(encoding='utf-8')
    metadata, body = parse_frontmatter(raw)
    lines = body.splitlines()
    tokens = markdown_parser().parse(body)
    headings = [(token.tag, tokens[i + 1].content, *token.map)
                for i, token in enumerate(tokens) if token.type == 'heading_open']
    title_heading = next((h for h in headings if h[0] == 'h1'), None)
    title = metadata.get('title') or (title_heading[1] if title_heading else path.stem)
    ignored = set(range(title_heading[2], title_heading[3])) if title_heading else set()
    groups = [h for h in headings if h[0] == 'h2' and h[1] in GROUPS]
    for _, _, start, end in groups:
        ignored.update(range(start, end))
    trend_names = TRENDS | ({metadata['trend_heading']} if metadata.get('trend_heading') else set())
    trend_heading = next((h for h in headings if h[1] in trend_names), None)
    end = trend_heading[2] if trend_heading else len(lines)
    declared = {item['heading']: item for item in metadata.get('paper_headings', [])}
    modern = [h for h in headings if h[0] == 'h2' and MODERN_PAPER.match(h[1])]
    paper_headings = ([h for h in headings if h[0] == 'h2' and h[1] in declared] if declared else
                      modern or [h for h in headings if h[0] == 'h3' and LEGACY_PAPER.match(h[1])])
    paper_headings = [h for h in paper_headings if h[2] < end]

    def content(start, stop):
        value = '\n'.join(line for i, line in enumerate(lines[start:stop], start) if i not in ignored).strip()
        return re.sub(r'(?:\n\s*---\s*)+$', '', value).strip()

    papers, spans = [], []
    for index, (_, heading, start, body_start) in enumerate(paper_headings):
        if declared:
            item = declared[heading]
            paper_title, category = item['title'], item['category'].title()
        else:
            match = (MODERN_PAPER if modern else LEGACY_PAPER).match(heading)
            label, paper_title = match.groups()
            group = next((h[1] for h in reversed(groups) if h[2] < start), '')
            category = 'Classic' if label == 'Classic' or group in {'Classic Revisit', '经典论文'} else 'Latest' if modern else 'Research'
        stop = paper_headings[index + 1][2] if index + 1 < len(paper_headings) else end
        paper_body = content(body_start, stop)
        spans.append([body_start, stop])
        papers.append(Paper(paper_title, category, paper_body, f'paper-{index + 1}', paper_excerpt(paper_body)))
    intro = content(0, paper_headings[0][2] if paper_headings else end)
    return Report(date.fromisoformat(path.stem), str(title), intro, papers,
                  content(trend_heading[3], len(lines)) if trend_heading else '',
                  trend_heading[1] if trend_heading else '', path,
                  {'body_line': raw[:len(raw) - len(body)].count('\n'),
                   'ignored_lines': sorted(ignored),
                   'intro': [0, paper_headings[0][2] if paper_headings else end],
                   'papers': spans,
                   'trends': [trend_heading[3], len(lines)] if trend_heading else [0, 0]})


def read_reports(root):
    return [read_report(path) for path in sorted((root / 'content/daily').glob('*.md'), reverse=True)
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', path.stem)]
