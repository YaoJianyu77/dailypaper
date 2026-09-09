"""Parse the one user settings page; YAML contains infrastructure only."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path
import re
from zoneinfo import ZoneInfo

import yaml

from site_content import markdown_parser, plain_text

SETTINGS_FILE = 'DAILY_REPORT_PRODUCT_REQUIREMENTS.md'


class SettingsError(ValueError):
    pass


def sections_and_rows(text):
    tokens = markdown_parser().parse(text)
    lines = text.splitlines()
    headings = [(i, token) for i, token in enumerate(tokens)
                if token.type == 'heading_open' and token.tag == 'h2']
    sections, tables = {}, {}
    for number, (index, token) in enumerate(headings):
        name = re.sub(r'^\d+\.\s*', '', tokens[index + 1].content).strip().casefold()
        if name in sections:
            raise SettingsError(f'Duplicate settings section: {name}')
        stop = headings[number + 1][1].map[0] if number + 1 < len(headings) else len(lines)
        sections[name] = '\n'.join(lines[token.map[1]:stop]).strip()
        rows, cells = {}, []
        for item in markdown_parser().parse(sections[name]):
            if item.type == 'tr_open':
                cells = []
            elif item.type == 'inline' and item.level >= 2:
                cells.append(plain_text(item.content))
            elif item.type == 'tr_close' and len(cells) == 2:
                key = cells[0].casefold()
                if key in rows:
                    raise SettingsError(f'Duplicate setting: {cells[0]}')
                rows[key] = cells[1]
        tables[name] = rows
    return sections, tables


def research_topics(root):
    path = Path(root) / SETTINGS_FILE
    if not path.is_file():
        return []
    _, tables = sections_and_rows(path.read_text(encoding='utf-8'))
    rows = tables.get('research areas', {})
    items = [item.strip().removesuffix('.') for label in ('primary', 'also include')
             for item in rows.get(label, '').split(';') if item.strip()]
    unique = {}
    for item in items:
        unique.setdefault(item.casefold(), item)
    return list(unique.values())


def calendar_shift(day, *, months=0, years=0):
    total = day.year * 12 + day.month - 1 - months - years * 12
    year, month = divmod(total, 12)
    month += 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


@dataclass(frozen=True)
class ReportSettings:
    raw: str
    sections: dict
    tables: dict
    sha256: str
    timezone: str
    latest_months: int
    classic_years: int
    latest_count: int
    classic_count: int
    allow_underfill: bool
    language: str
    summary_min: int
    summary_max: int
    hard_max: int
    brief_min: int
    brief_max: int
    assessment_max: int
    visual_min: int
    visual_max: int
    insight_max: int
    finding_max: int
    headings: tuple
    trend_heading: str
    trend_max: int
    trend_min_latest: int
    venues: tuple

    def local_date(self, now=None):
        return (now or datetime.now(ZoneInfo(self.timezone))).astimezone(ZoneInfo(self.timezone)).date()

    def run_id(self, day):
        return f'systems-paper-daily:{day.isoformat()}'

    def windows(self, day):
        start = calendar_shift(day, months=self.latest_months)
        return {'latest': {'start': start.isoformat(), 'end': day.isoformat()},
                'classic': {'start': calendar_shift(day, years=self.classic_years).isoformat(),
                            'end': (start - timedelta(days=1)).isoformat()}}

    def category(self, publication_date, day):
        value = date.fromisoformat(publication_date)
        for category, window in self.windows(day).items():
            if date.fromisoformat(window['start']) <= value <= date.fromisoformat(window['end']):
                return category
        return None

    @property
    def quotas(self):
        return {'latest': self.latest_count, 'classic': self.classic_count}


def load_settings(root):
    path = Path(root) / SETTINGS_FILE
    raw = path.read_text(encoding='utf-8')
    sections, tables = sections_and_rows(raw)
    required = ('research areas', 'search sources', 'time windows', 'selection',
                'per-paper content', 'final research trends')
    if set(sections) != set(required):
        raise SettingsError(f'{SETTINGS_FILE} must contain the six named settings sections')

    def value(section, key):
        try:
            result = tables[section][key.casefold()]
        except KeyError as exc:
            raise SettingsError(f'Missing setting: {section} / {key}') from exc
        if not result.strip():
            raise SettingsError(f'Empty setting: {key}')
        return result

    def numbers(section, key, count=1):
        result = tuple(int(n.replace(',', '')) for n in re.findall(r'\d[\d,]*', value(section, key)))
        if len(result) != count:
            raise SettingsError(f'{key} must specify {count} numeric value(s)')
        return result

    timezone = re.search(r'\b[A-Za-z_]+/[A-Za-z_/]+\b', value('time windows', 'Date and timezone'))
    if not timezone:
        raise SettingsError('Date and timezone must name an IANA timezone')
    timezone = timezone.group()
    ZoneInfo(timezone)
    if not re.search(r'calendar months?', value('time windows', 'Latest-paper pool'), re.I):
        raise SettingsError('Latest-paper pool must use calendar months')
    if not re.search(r'calendar years?', value('time windows', 'Classic-paper pool'), re.I):
        raise SettingsError('Classic-paper pool must use calendar years')
    if not value('selection', 'Non-repetition').casefold().startswith('permanent'):
        raise SettingsError('Permanent history cannot be expired or reset by a settings change')
    shortfall = value('selection', 'Shortfall policy').casefold()
    if shortfall.startswith('fewer papers are allowed'):
        underfill = True
    elif shortfall.startswith('fewer papers are not allowed'):
        underfill = False
    else:
        raise SettingsError('Shortfall policy must begin with "Fewer papers are allowed" or "Fewer papers are not allowed"')
    headings = tuple(plain_text(m) for m in re.findall(r'^\d+\.\s+(.+)$', sections['per-paper content'], re.M))
    if len(headings) < 2 or len(set(headings)) != len(headings):
        raise SettingsError('Per-paper content needs distinct, ordered summary headings')
    sources = tables['search sources']
    venues = tuple(dict.fromkeys(item.strip().removesuffix('.')
                   for key, row in sources.items() if key != 'group'
                   for item in row.split(',') if item.strip()))
    if not venues or not research_topics(root):
        raise SettingsError('At least one eligible venue and positive research area are required')
    summary_min, summary_max, hard_max = numbers('per-paper content', 'Summary length', 3)
    brief_min, brief_max = numbers('per-paper content', 'Opening brief', 2)
    visual_min, visual_max = numbers('per-paper content', 'Visuals', 2)
    result = ReportSettings(
        raw, sections, tables, hashlib.sha256(raw.encode()).hexdigest(), timezone,
        *numbers('time windows', 'Latest-paper pool'), *numbers('time windows', 'Classic-paper pool'),
        *numbers('selection', 'Latest papers per day'), *numbers('selection', 'Classic papers per day'),
        underfill, value('per-paper content', 'Prompt and report language').split(',')[0].strip().removesuffix('.'),
        summary_min, summary_max, hard_max, brief_min, brief_max,
        *numbers('per-paper content', 'Final assessment'), visual_min, visual_max,
        *numbers('per-paper content', 'Central insights'), *numbers('per-paper content', 'Major experimental findings'),
        headings, value('final research trends', 'Final heading'),
        *numbers('final research trends', 'Maximum trends'),
        *numbers('final research trends', 'Minimum latest papers per trend'), venues)
    if not (0 < summary_min <= summary_max <= hard_max and 0 < brief_min <= brief_max <= summary_max
            and 0 < visual_min <= visual_max and result.assessment_max > 0
            and result.latest_months > 0 and result.classic_years * 12 > result.latest_months
            and min(result.quotas.values()) >= 0 and sum(result.quotas.values()) > 0
            and min(result.insight_max, result.finding_max, result.trend_max, result.trend_min_latest) > 0):
        raise SettingsError('Settings contain contradictory or non-positive limits')
    return result


def load_infrastructure(root):
    root = Path(root)
    path = root / 'config.yaml'
    data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    allowed = {
        'site': {'title', 'base_url'},
        'ai': {'codex_timeout_seconds'},
        'search': {'max_candidates_per_venue', 'request_interval_seconds', 'timeout_seconds', 'retries'},
        'documents': {'max_pdf_bytes', 'max_pages', 'render_dpi'},
    }
    for group, values in data.items():
        if group not in allowed or not isinstance(values, dict) or set(values) - allowed[group]:
            raise SettingsError(f'Competing or unsupported YAML settings in {group}; preferences belong in {SETTINGS_FILE}')
    return data
