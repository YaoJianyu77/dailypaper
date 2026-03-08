#!/usr/bin/env python3
"""
arXiv + Semantic Scholar + Google Scholar 混合架构论文搜索脚本
用于 start-my-day skill，搜索最近一个月和最近一年的极火、极热门、极优质论文
"""

import xml.etree.ElementTree as ET
import json
import re
import html
import os
import sys
import time
import logging
import hashlib
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, List, Dict, Set, Optional, Tuple
from pathlib import Path
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logger.warning("requests library not found, using urllib for Semantic Scholar API")

# ---------------------------------------------------------------------------
# API 配置
# ---------------------------------------------------------------------------
ARXIV_NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom'
}

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_BATCH_API_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
SEMANTIC_SCHOLAR_FIELDS = "title,abstract,publicationDate,citationCount,influentialCitationCount,url,authors,externalIds"
SEMANTIC_SCHOLAR_BATCH_FIELDS = "citationCount,influentialCitationCount,venue,journal"
SEMANTIC_SCHOLAR_QUERY_LIMIT = 60
DBLP_PUBL_SEARCH_API_URL = "https://dblp.org/search/publ/api"
OPENALEX_SOURCES_API_URL = "https://api.openalex.org/sources"
OPENALEX_WORKS_API_URL = "https://api.openalex.org/works"
GOOGLE_SCHOLAR_SEARCH_URL = "https://scholar.google.com/scholar"
GOOGLE_SCHOLAR_REQUEST_INTERVAL = 4.0
GOOGLE_SCHOLAR_MIN_TITLE_SIMILARITY = 0.72
VENUE_PAGE_TIMEOUT_SECONDS = 30
VENUE_PAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
DEFAULT_LANE_SETTINGS = {
    'fresh': {'max_age_days': 90, 'quota': 3},
    'established': {'max_age_days': 1095, 'quota': 2},
    'classic': {'quota': 1},
    'fill_order': ['fresh', 'established', 'classic'],
    'allow_underfill': True,
}
DEFAULT_HISTORY_SETTINGS = {
    'index_path': 'state/paper_index.json',
    'classic_backlog_path': 'state/classic_backlog.json',
    'recommended_cooldown_days': 60,
    'classic_recommended_cooldown_days': 21,
    'analyzed_cooldown_days': 365,
}
DEFAULT_CLASSIC_SETTINGS = {
    'enabled': True,
    'cadence_days': 3,
    'anchor_date': '2026-03-07',
    'random_seed': 'systems-classics-v1',
    'allow_full_analysis': False,
}
DEFAULT_VENUE_SOURCE_SETTINGS = {
    'enabled': True,
    'provider': 'dblp',
    'max_hits_per_query': 12,
    'max_candidates': 80,
    'request_interval_seconds': 1.0,
    'recent_years': 5,
    'prefer_open_access_pdf': True,
    'venues': [],
    'query_groups': [],
}

ARXIV_CATEGORY_KEYWORDS = {
    "cs.AI": "artificial intelligence",
    "cs.LG": "machine learning",
    "cs.CL": "computational linguistics natural language processing",
    "cs.CV": "computer vision",
    "cs.MM": "multimedia",
    "cs.MA": "multi-agent systems",
    "cs.RO": "robotics"
}

# ---------------------------------------------------------------------------
# 评分常量  —— 修改权重时只需编辑这里
# ---------------------------------------------------------------------------

# 各维度原始评分的满分值（归一化基准）
SCORE_MAX = 3.0

# 相关性评分：关键词在标题 / 摘要中匹配的加分
RELEVANCE_TITLE_KEYWORD_BOOST = 0.5
RELEVANCE_SUMMARY_KEYWORD_BOOST = 0.3
RELEVANCE_CATEGORY_MATCH_BOOST = 1.0

# 新近性阈值（天） -> 对应评分
RECENCY_THRESHOLDS = [
    (30, 3.0),
    (90, 2.0),
    (180, 1.0),
]
RECENCY_DEFAULT = 0.0

# 热门度：高影响力引用数归一化到 0-SCORE_MAX
# 含义：达到此引用数时视为满分
POPULARITY_INFLUENTIAL_CITATION_FULL_SCORE = 100

# 综合推荐评分权重（普通论文）
WEIGHTS_NORMAL = {
    'relevance': 0.40,
    'recency': 0.20,
    'popularity': 0.30,
    'quality': 0.10,
}
# 综合推荐评分权重（高影响力论文：提高热门度，降低新近性）
WEIGHTS_HOT = {
    'relevance': 0.35,
    'recency': 0.10,
    'popularity': 0.45,
    'quality': 0.10,
}

# Semantic Scholar 速率限制等待时间（秒）
S2_RATE_LIMIT_WAIT = 30
S2_CATEGORY_REQUEST_INTERVAL = 3


class SemanticScholarRateLimitError(RuntimeError):
    """Raised when Semantic Scholar rate limits and the caller should degrade gracefully."""


def load_research_config(config_path: str) -> Dict:
    """
    从 YAML 文件加载研究兴趣配置

    Args:
        config_path: 配置文件路径

    Returns:
        研究配置字典
    """
    import yaml

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error("Error loading config: %s", e)
        # 返回默认配置
        return {
            "research_domains": {
                "大模型": {
                    "keywords": [
                        "pre-training", "foundation model", "model architecture",
                        "large language model", "LLM", "transformer"
                    ],
                    "arxiv_categories": ["cs.AI", "cs.LG", "cs.CL"],
                    "priority": 5
                }
            },
            "excluded_keywords": ["3D", "review", "workshop", "survey"]
        }


def get_search_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    search_settings = config.get('search', {})
    if isinstance(search_settings, dict):
        return search_settings
    return {}


def get_search_scoring_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    scoring_settings = get_search_settings(config).get('scoring', {})
    if isinstance(scoring_settings, dict):
        return scoring_settings
    return {}


def get_config_float(config: Dict[str, Any], key: str, default: float) -> float:
    try:
        return float(config.get(key, default))
    except (TypeError, ValueError, AttributeError):
        return default


def get_config_int(config: Dict[str, Any], key: str, default: int) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError, AttributeError):
        return default


def get_config_bool(config: Dict[str, Any], key: str, default: bool) -> bool:
    value = config.get(key, default) if isinstance(config, dict) else default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {'1', 'true', 'yes', 'on'}:
            return True
        if lowered in {'0', 'false', 'no', 'off'}:
            return False
    return bool(value)


def get_metadata_fallback_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = get_search_settings(config).get('metadata_fallbacks', {})
    if not isinstance(raw, dict):
        raw = {}
    return {
        'google_scholar_enabled': get_config_bool(raw, 'google_scholar_enabled', True),
        'google_scholar_request_interval_seconds': get_config_float(
            raw,
            'google_scholar_request_interval_seconds',
            GOOGLE_SCHOLAR_REQUEST_INTERVAL,
        ),
        'google_scholar_min_title_similarity': get_config_float(
            raw,
            'google_scholar_min_title_similarity',
            GOOGLE_SCHOLAR_MIN_TITLE_SIMILARITY,
        ),
    }


def get_lane_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = get_search_settings(config).get('lanes', {})
    if not isinstance(raw, dict):
        raw = {}

    result = {
        'fresh': {
            'max_age_days': get_config_int(raw.get('fresh', {}), 'max_age_days', DEFAULT_LANE_SETTINGS['fresh']['max_age_days']),
            'quota': get_config_int(raw.get('fresh', {}), 'quota', DEFAULT_LANE_SETTINGS['fresh']['quota']),
        },
        'established': {
            'max_age_days': get_config_int(raw.get('established', {}), 'max_age_days', DEFAULT_LANE_SETTINGS['established']['max_age_days']),
            'quota': get_config_int(raw.get('established', {}), 'quota', DEFAULT_LANE_SETTINGS['established']['quota']),
        },
        'classic': {
            'quota': get_config_int(raw.get('classic', {}), 'quota', DEFAULT_LANE_SETTINGS['classic']['quota']),
        },
        'allow_underfill': get_config_bool(raw, 'allow_underfill', DEFAULT_LANE_SETTINGS['allow_underfill']),
    }

    fill_order = raw.get('fill_order', DEFAULT_LANE_SETTINGS['fill_order'])
    if isinstance(fill_order, list):
        normalized = [str(item).strip().lower() for item in fill_order if str(item).strip()]
        result['fill_order'] = [item for item in normalized if item in {'fresh', 'established', 'classic'}] or list(DEFAULT_LANE_SETTINGS['fill_order'])
    else:
        result['fill_order'] = list(DEFAULT_LANE_SETTINGS['fill_order'])
    return result


def get_history_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = get_search_settings(config).get('history', {})
    if not isinstance(raw, dict):
        raw = {}
    return {
        'index_path': str(raw.get('index_path') or DEFAULT_HISTORY_SETTINGS['index_path']).strip() or DEFAULT_HISTORY_SETTINGS['index_path'],
        'classic_backlog_path': str(raw.get('classic_backlog_path') or DEFAULT_HISTORY_SETTINGS['classic_backlog_path']).strip() or DEFAULT_HISTORY_SETTINGS['classic_backlog_path'],
        'recommended_cooldown_days': get_config_int(raw, 'recommended_cooldown_days', DEFAULT_HISTORY_SETTINGS['recommended_cooldown_days']),
        'classic_recommended_cooldown_days': get_config_int(raw, 'classic_recommended_cooldown_days', DEFAULT_HISTORY_SETTINGS['classic_recommended_cooldown_days']),
        'analyzed_cooldown_days': get_config_int(raw, 'analyzed_cooldown_days', DEFAULT_HISTORY_SETTINGS['analyzed_cooldown_days']),
    }


def get_classic_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = get_search_settings(config).get('classics', {})
    if not isinstance(raw, dict):
        raw = {}
    return {
        'enabled': get_config_bool(raw, 'enabled', DEFAULT_CLASSIC_SETTINGS['enabled']),
        'cadence_days': max(1, get_config_int(raw, 'cadence_days', DEFAULT_CLASSIC_SETTINGS['cadence_days'])),
        'anchor_date': str(raw.get('anchor_date') or DEFAULT_CLASSIC_SETTINGS['anchor_date']).strip() or DEFAULT_CLASSIC_SETTINGS['anchor_date'],
        'random_seed': str(raw.get('random_seed') or DEFAULT_CLASSIC_SETTINGS['random_seed']).strip() or DEFAULT_CLASSIC_SETTINGS['random_seed'],
        'allow_full_analysis': get_config_bool(raw, 'allow_full_analysis', DEFAULT_CLASSIC_SETTINGS['allow_full_analysis']),
    }


def get_venue_source_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = get_search_settings(config).get('venue_sources', {})
    if not isinstance(raw, dict):
        raw = {}

    venues = raw.get('venues', DEFAULT_VENUE_SOURCE_SETTINGS['venues'])
    query_groups = raw.get('query_groups', DEFAULT_VENUE_SOURCE_SETTINGS['query_groups'])
    if not isinstance(venues, list):
        venues = []
    if not isinstance(query_groups, list):
        query_groups = []

    normalized_venues: List[Dict[str, Any]] = []
    for item in venues:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name') or '').strip()
        if not name:
            continue
        aliases = item.get('aliases', [])
        if isinstance(aliases, str):
            aliases = [aliases]
        elif not isinstance(aliases, list):
            aliases = []
        query_aliases = item.get('query_aliases', [])
        if isinstance(query_aliases, str):
            query_aliases = [query_aliases]
        elif not isinstance(query_aliases, list):
            query_aliases = []
        normalized_aliases = [str(alias).strip() for alias in aliases if str(alias).strip()]
        normalized_query_aliases = [str(alias).strip() for alias in query_aliases if str(alias).strip()]
        normalized_venues.append({
            'name': name,
            'aliases': normalized_aliases or [name],
            'query_aliases': normalized_query_aliases,
            'priority': get_config_int(item, 'priority', 3),
        })

    normalized_groups: List[str] = []
    for item in query_groups:
        text = str(item or '').strip()
        if text:
            normalized_groups.append(text)

    return {
        'enabled': get_config_bool(raw, 'enabled', DEFAULT_VENUE_SOURCE_SETTINGS['enabled']),
        'provider': str(raw.get('provider') or DEFAULT_VENUE_SOURCE_SETTINGS['provider']).strip().lower() or DEFAULT_VENUE_SOURCE_SETTINGS['provider'],
        'max_hits_per_query': max(1, get_config_int(raw, 'max_hits_per_query', DEFAULT_VENUE_SOURCE_SETTINGS['max_hits_per_query'])),
        'max_candidates': max(1, get_config_int(raw, 'max_candidates', DEFAULT_VENUE_SOURCE_SETTINGS['max_candidates'])),
        'request_interval_seconds': max(0.0, get_config_float(raw, 'request_interval_seconds', DEFAULT_VENUE_SOURCE_SETTINGS['request_interval_seconds'])),
        'recent_years': max(1, get_config_int(raw, 'recent_years', DEFAULT_VENUE_SOURCE_SETTINGS['recent_years'])),
        'prefer_open_access_pdf': get_config_bool(raw, 'prefer_open_access_pdf', DEFAULT_VENUE_SOURCE_SETTINGS['prefer_open_access_pdf']),
        'venues': normalized_venues,
        'query_groups': normalized_groups,
    }


def resolve_repo_path(repo_root: Path, path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root / path
    return path


def normalize_title_key(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', str(title or '').lower()).strip()


def paper_index_key(paper: Dict[str, Any]) -> str:
    arxiv_id = str(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('paper_id') or '').strip()
    if arxiv_id:
        return arxiv_id
    return normalize_title_key(str(paper.get('title') or ''))


def parse_date_flexible(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    text = str(value or '').strip()
    if not text:
        return None
    for parser in (
        lambda raw: datetime.fromisoformat(raw.replace('Z', '+00:00')),
        lambda raw: datetime.strptime(raw, '%Y-%m-%d'),
    ):
        try:
            return parser(text)
        except ValueError:
            continue
    return None


def coarse_publication_datetime(year: int, reference_date: Optional[datetime] = None) -> Optional[datetime]:
    if year <= 0:
        return None
    anchor = datetime(year, 7, 1)
    if reference_date and year == reference_date.year and anchor > reference_date:
        return reference_date
    return anchor


def looks_like_arxiv_id(value: str) -> bool:
    text = str(value or '').strip()
    return bool(re.fullmatch(r'\d{4}\.\d+(?:v\d+)?', text))


def normalize_year(value: Any) -> Optional[int]:
    try:
        year = int(str(value or '').strip())
    except (TypeError, ValueError):
        return None
    if year < 1900 or year > 2100:
        return None
    return year


def first_non_empty_url(*values: Any) -> str:
    for value in values:
        text = str(value or '').strip()
        if text.startswith('http://') or text.startswith('https://'):
            return text
    return ''


def flatten_dblp_author_names(value: Any) -> List[str]:
    authors: List[str] = []
    if isinstance(value, list):
        items = value
    elif value is None:
        items = []
    else:
        items = [value]

    for item in items:
        if isinstance(item, dict):
            text = str(item.get('text') or item.get('@text') or item.get('author') or '').strip()
        else:
            text = str(item or '').strip()
        if text and text not in authors:
            authors.append(text)
    return authors


def dblp_info_authors(info: Dict[str, Any]) -> List[str]:
    authors_value = info.get('authors')
    if isinstance(authors_value, dict):
        author_items = authors_value.get('author')
        return flatten_dblp_author_names(author_items)
    return flatten_dblp_author_names(authors_value)


def normalize_dblp_hits(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    result = payload.get('result', {})
    if not isinstance(result, dict):
        return []
    hits = result.get('hits', {})
    if not isinstance(hits, dict):
        return []
    raw = hits.get('hit', [])
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def normalize_dblp_ee_list(value: Any) -> List[str]:
    urls: List[str] = []
    if isinstance(value, list):
        items = value
    elif value is None:
        items = []
    else:
        items = [value]
    for item in items:
        if isinstance(item, dict):
            text = str(item.get('text') or item.get('@text') or '').strip()
        else:
            text = str(item or '').strip()
        if text.startswith('http://') or text.startswith('https://'):
            urls.append(text)
    return urls


def looks_like_pdf_url(url: str) -> bool:
    low = str(url or '').strip().lower()
    if not low:
        return False
    return (
        low.endswith('.pdf')
        or '.pdf?' in low
        or '/pdf/' in low
        or low.startswith('https://arxiv.org/pdf/')
    )


def derive_pdf_from_source_url(source_url: str) -> str:
    url = str(source_url or '').strip()
    low = url.lower()
    if not url:
        return ''
    if 'proceedings.mlsys.org/paper_files/paper/' in low and low.endswith('-abstract-conference.html'):
        return re.sub(r'-Abstract-Conference\.html$', '-Paper-Conference.pdf', url, flags=re.IGNORECASE)
    return ''


def prefer_dblp_pdf_url(candidates: List[str], prefer_open_access_pdf: bool) -> str:
    if not candidates:
        return ''
    lowered = [(url, url.lower()) for url in candidates]
    for url, low in lowered:
        if looks_like_pdf_url(low):
            return url
    if prefer_open_access_pdf:
        for url, low in lowered:
            if any(token in low for token in ['/pdf', 'openaccess']) and 'doi.org' not in low:
                return url
    return ''


def openalex_inverted_index_to_text(value: Any, max_chars: int = 3000) -> str:
    if not isinstance(value, dict):
        return ''
    positions: List[Tuple[int, str]] = []
    for token, indexes in value.items():
        if not isinstance(indexes, list):
            continue
        for index in indexes:
            try:
                positions.append((int(index), str(token)))
            except (TypeError, ValueError):
                continue
    if not positions:
        return ''
    positions.sort(key=lambda item: item[0])
    words = [token for _, token in positions]
    text = ' '.join(words)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


def openalex_source_display_names(source: Dict[str, Any]) -> List[str]:
    names = [str(source.get('display_name') or '').strip()]
    for host in source.get('host_organization_lineage_names', []) if isinstance(source.get('host_organization_lineage_names'), list) else []:
        text = str(host or '').strip()
        if text:
            names.append(text)
    seen: set[str] = set()
    result: List[str] = []
    for name in names:
        lowered = name.lower()
        if not name or lowered in seen:
            continue
        seen.add(lowered)
        result.append(name)
    return result


def search_openalex_source(venue_alias: str) -> Optional[Dict[str, Any]]:
    params = {
        'search': venue_alias,
        'per-page': '5',
        'filter': 'type:conference',
    }
    url = f"{OPENALEX_SOURCES_API_URL}?{urllib.parse.urlencode(params)}"
    payload = fetch_json_url(url, timeout_seconds=45)
    results = payload.get('results', []) if isinstance(payload, dict) else []
    if not isinstance(results, list):
        return None

    best_source = None
    best_score = -1.0
    target = venue_alias.lower()
    for source in results:
        if not isinstance(source, dict):
            continue
        names = openalex_source_display_names(source)
        if not names:
            continue
        score = max(SequenceMatcher(None, target, name.lower()).ratio() for name in names)
        if score > best_score:
            best_score = score
            best_source = source
    return best_source if best_score >= 0.55 else None


def search_openalex_work_by_doi_or_title(*, doi: str = '', title: str = '') -> Optional[Dict[str, Any]]:
    doi = str(doi or '').strip()
    title = str(title or '').strip()
    urls: List[str] = []
    if doi:
        doi_value = doi if doi.startswith('http') else f'https://doi.org/{doi}'
        urls.append(f"{OPENALEX_WORKS_API_URL}?{urllib.parse.urlencode({'filter': f'doi:{doi_value}', 'per-page': '1'})}")
    if title:
        urls.append(f"{OPENALEX_WORKS_API_URL}?{urllib.parse.urlencode({'search': title, 'per-page': '5'})}")

    for url in urls:
        try:
            payload = fetch_json_url(url, timeout_seconds=45)
        except Exception as exc:
            logger.warning("OpenAlex work lookup failed for %s: %s", title or doi or url, exc)
            continue
        results = payload.get('results', []) if isinstance(payload, dict) else []
        if not isinstance(results, list) or not results:
            continue
        if doi:
            return results[0] if isinstance(results[0], dict) else None
        ranked = [
            (
                SequenceMatcher(
                    None,
                    str(item.get('display_name') or '').lower(),
                    title.lower(),
                ).ratio(),
                item,
            )
            for item in results
            if isinstance(item, dict)
        ]
        ranked = [item for item in ranked if item[0] >= 0.72]
        if ranked:
            ranked.sort(key=lambda pair: pair[0], reverse=True)
            return ranked[0][1]
    return None


def openalex_work_to_candidate(
    work: Dict[str, Any],
    *,
    venue_name: str,
    venue_alias: str,
    reference_date: datetime,
) -> Optional[Dict[str, Any]]:
    title = str(work.get('display_name') or work.get('title') or '').strip()
    if not title:
        return None

    paper_id = str(work.get('id') or '').strip()
    if not paper_id:
        return None

    publication_year = normalize_year(work.get('publication_year'))
    publication_date = str(work.get('publication_date') or publication_year or '').strip()
    published_dt = parse_date_flexible(publication_date) or coarse_publication_datetime(publication_year or 0, reference_date)
    abstract = openalex_inverted_index_to_text(work.get('abstract_inverted_index'))

    primary_location = work.get('primary_location', {}) if isinstance(work.get('primary_location'), dict) else {}
    best_oa_location = work.get('best_oa_location', {}) if isinstance(work.get('best_oa_location'), dict) else {}
    source = primary_location.get('source', {}) if isinstance(primary_location.get('source'), dict) else {}
    openalex_venue = str(source.get('display_name') or venue_name or '').strip()

    source_url = first_non_empty_url(
        primary_location.get('landing_page_url'),
        best_oa_location.get('landing_page_url'),
        work.get('primary_location', {}).get('pdf_url') if isinstance(work.get('primary_location'), dict) else '',
        work.get('id'),
    )
    pdf_url = first_non_empty_url(
        primary_location.get('pdf_url'),
        best_oa_location.get('pdf_url'),
    )

    authorships = work.get('authorships', [])
    authors: List[str] = []
    institutions: List[str] = []
    if isinstance(authorships, list):
        for authorship in authorships[:12]:
            if not isinstance(authorship, dict):
                continue
            author = authorship.get('author', {})
            if isinstance(author, dict):
                name = str(author.get('display_name') or '').strip()
                if name and name not in authors:
                    authors.append(name)
            institutions_data = authorship.get('institutions', [])
            if isinstance(institutions_data, list):
                for inst in institutions_data:
                    if not isinstance(inst, dict):
                        continue
                    name = str(inst.get('display_name') or '').strip()
                    if name and name not in institutions:
                        institutions.append(name)

    candidate = {
        'id': paper_id,
        'paper_id': paper_id,
        'title': title,
        'summary': abstract,
        'abstract': abstract,
        'authors': authors,
        'institutions': institutions,
        'published': publication_date,
        'published_date': published_dt,
        'publicationDate': publication_date,
        'categories': [],
        'source': 'openalex_venue',
        'source_provider': 'openalex',
        'source_url': source_url,
        'url': source_url,
        'pdf_url': pdf_url,
        'venue': openalex_venue,
        'citationCount': work.get('cited_by_count'),
        'venue_source_name': venue_name,
        'venue_source_alias': venue_alias,
        'openalex_id': paper_id,
        'doi': str(work.get('doi') or '').strip(),
        'selection_signals': {
            'source': 'openalex_venue',
            'venue': venue_name,
            'venue_alias': venue_alias,
        },
    }
    return candidate


def hydrate_papers_with_venue_metadata(papers: List[Dict[str, Any]]) -> None:
    for paper in papers:
        source = str(paper.get('source') or '').strip().lower()
        if source not in {'dblp_venue', 'openalex_venue'}:
            continue

        official = fetch_official_venue_metadata(str(paper.get('source_url') or paper.get('url') or '').strip())
        abstract = str(official.get('abstract') or '').strip()
        pdf_url = str(official.get('pdf_url') or '').strip()
        landing_page_url = str(official.get('landing_page_url') or paper.get('source_url') or paper.get('url') or '').strip()

        openalex_work: Optional[Dict[str, Any]] = None
        needs_openalex = (
            not abstract
            or not pdf_url
            or paper.get('citationCount') is None
            or not str(paper.get('venue') or paper.get('journal_ref') or '').strip()
        )
        if needs_openalex:
            openalex_work = search_openalex_work_by_doi_or_title(
                doi=str(paper.get('doi') or '').strip(),
                title=str(paper.get('title') or '').strip(),
            )

        if openalex_work:
            if not abstract:
                abstract = openalex_inverted_index_to_text(openalex_work.get('abstract_inverted_index'))
            primary_location = openalex_work.get('primary_location', {}) if isinstance(openalex_work.get('primary_location'), dict) else {}
            best_oa_location = openalex_work.get('best_oa_location', {}) if isinstance(openalex_work.get('best_oa_location'), dict) else {}
            if not landing_page_url:
                landing_page_url = first_non_empty_url(
                    primary_location.get('landing_page_url'),
                    best_oa_location.get('landing_page_url'),
                    openalex_work.get('id'),
                )
            if not pdf_url:
                pdf_url = first_non_empty_url(
                    primary_location.get('pdf_url'),
                    best_oa_location.get('pdf_url'),
                )
            source_info = primary_location.get('source', {}) if isinstance(primary_location.get('source'), dict) else {}
            openalex_venue = str(source_info.get('display_name') or '').strip()
            if openalex_venue and not str(paper.get('venue') or paper.get('journal_ref') or '').strip():
                paper['venue'] = openalex_venue
            cited_by = openalex_work.get('cited_by_count')
            if cited_by is not None and paper.get('citationCount') is None:
                paper['citationCount'] = cited_by
            authorships = openalex_work.get('authorships', [])
            if isinstance(authorships, list) and not paper.get('institutions'):
                institutions: List[str] = []
                for authorship in authorships:
                    if not isinstance(authorship, dict):
                        continue
                    for inst in authorship.get('institutions', []) if isinstance(authorship.get('institutions'), list) else []:
                        if not isinstance(inst, dict):
                            continue
                        name = str(inst.get('display_name') or '').strip()
                        if name and name not in institutions:
                            institutions.append(name)
                if institutions:
                    paper['institutions'] = institutions[:8]

        current_summary = str(paper.get('summary') or paper.get('abstract') or '').strip()
        if abstract and (not current_summary or len(abstract) > len(current_summary) + 80):
            paper['summary'] = abstract
            paper['abstract'] = abstract
        if pdf_url and not str(paper.get('pdf_url') or '').strip():
            paper['pdf_url'] = pdf_url
        if landing_page_url:
            paper['source_url'] = landing_page_url
            paper['url'] = landing_page_url
        if official or openalex_work:
            paper['venue_metadata'] = {
                'official_page_blocked': bool(official.get('blocked')),
                'official_page_url': landing_page_url,
                'abstract_source': 'official_page' if official.get('abstract') else ('openalex' if openalex_work else ''),
                'pdf_source': 'official_page' if official.get('pdf_url') else ('openalex' if openalex_work and pdf_url else ''),
            }


def refresh_selected_paper_scores(
    papers: List[Dict[str, Any]],
    config: Dict[str, Any],
    *,
    target_date: Optional[datetime] = None,
) -> None:
    scoring_settings = get_search_scoring_settings(config)
    weights_normal = get_recommendation_weights(scoring_settings, 'weights_normal', WEIGHTS_NORMAL)
    weights_hot = get_recommendation_weights(scoring_settings, 'weights_hot', WEIGHTS_HOT)
    recency_thresholds = get_recency_thresholds(config)
    for paper in papers:
        summary = str(paper.get('summary') or paper.get('abstract') or '').strip()
        current_scores = paper.get('scores', {})
        if not summary or not isinstance(current_scores, dict):
            continue

        quality = min(calculate_quality_score(summary), SCORE_MAX)
        relevance = min(float(current_scores.get('relevance', 0) or 0), SCORE_MAX)
        recency = float(current_scores.get('recency', 0) or 0)
        if recency <= 0:
            published_date = parse_date_flexible(paper.get('published_date') or paper.get('publicationDate') or paper.get('published'))
            recency = calculate_recency_score(
                published_date,
                reference_date=target_date,
                thresholds=recency_thresholds,
            )
        popularity = float(current_scores.get('popularity', 0) or 0)
        if not paper.get('is_hot_paper'):
            popularity = quality
        recommendation_score = calculate_recommendation_score(
            relevance,
            min(recency, SCORE_MAX),
            min(popularity, SCORE_MAX),
            quality,
            bool(paper.get('is_hot_paper')),
            priority_bonus=float(paper.get('domain_preference_bonus', 0) or 0),
            weights_normal=weights_normal,
            weights_hot=weights_hot,
        )
        current_scores['quality'] = round(quality, 2)
        current_scores['popularity'] = round(min(popularity, SCORE_MAX), 2)
        current_scores['recommendation'] = recommendation_score
        paper['scores'] = current_scores

        match_details = paper.get('match_details', {}) if isinstance(paper.get('match_details'), dict) else {}
        analysis_candidate_score, analysis_components = calculate_analysis_candidate_score(paper, match_details)
        paper['analysis_candidate_score'] = analysis_candidate_score
        paper['analysis_signals'] = analysis_components.get('analysis_signals', [])
        paper['analysis_components'] = {
            key: value
            for key, value in analysis_components.items()
            if key != 'analysis_signals'
        }


def load_paper_index_entries(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {}

    if isinstance(payload, dict):
        items = payload.get('papers', [])
    elif isinstance(payload, list):
        items = payload
    else:
        items = []

    result: Dict[str, Dict[str, Any]] = {}
    if not isinstance(items, list):
        return result
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get('paper_id') or '').strip() or normalize_title_key(item.get('title') or '')
        if not key:
            continue
        result[key] = item
    return result


def load_classic_backlog(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return []

    if isinstance(payload, dict):
        items = payload.get('papers', [])
    elif isinstance(payload, list):
        items = payload
    else:
        items = []
    return [item for item in items if isinstance(item, dict)]


def venue_query_groups(config: Dict[str, Any], venue_settings: Dict[str, Any]) -> List[str]:
    configured = [str(item).strip() for item in venue_settings.get('query_groups', []) if str(item).strip()]
    if configured:
        return configured

    systems_domain = config.get('research_domains', {}).get('LLM Inference Systems', {})
    if not isinstance(systems_domain, dict):
        systems_domain = {}

    required_terms = [
        str(item.get('term') or '').strip()
        for item in normalize_keyword_rules(systems_domain.get('required_signal_keywords', []))
        if str(item.get('term') or '').strip()
    ]
    bonus_terms = [
        str(item.get('term') or '').strip()
        for item in normalize_keyword_rules(systems_domain.get('bonus_keywords', []))
        if str(item.get('term') or '').strip()
    ]

    groups: List[List[str]] = []
    inference_terms = [term for term in required_terms if term in {'llm inference', 'llm serving', 'speculative decoding', 'kv cache', 'prefill', 'decode', 'vllm', 'runtime', 'serving system'}]
    kernel_terms = [term for term in required_terms if term in {'flashattention', 'attention kernel', 'kernel pipelining', 'compiler', 'h100', 'a100', 'b200'}]
    low_level_terms = [
        term for term in (required_terms + bonus_terms)
        if term in {'cuda', 'triton', 'ptx', 'sass', 'kernel', 'latency', 'throughput', 'bandwidth', 'memory', 'quantization'}
    ]

    if inference_terms:
        groups.append(inference_terms)
    if kernel_terms:
        groups.append(kernel_terms)
    if low_level_terms:
        groups.append(low_level_terms)

    result: List[str] = []
    for group in groups:
        unique_group = []
        seen: set[str] = set()
        for term in group:
            lowered = term.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            unique_group.append(term)
        if unique_group:
            result.append('|'.join(unique_group[:8]))
    return result[:4]


def build_dblp_query(venue_alias: str, group: str) -> str:
    raw_terms = [term.strip() for term in str(group or '').split('|') if term.strip()]
    if not raw_terms:
        raw_terms = [str(group or '').strip()]
    selected_terms: List[str] = []
    seen: set[str] = set()
    for term in raw_terms:
        lowered = term.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        selected_terms.append(term)
        if len(selected_terms) >= 3:
            break
    compact_group = ' '.join(selected_terms)
    parts = [compact_group, str(venue_alias or '').strip()]
    return ' '.join(part for part in parts if part)


def venue_query_aliases(venue: Dict[str, Any]) -> List[str]:
    raw_query_aliases = venue.get('query_aliases', [])
    if isinstance(raw_query_aliases, str):
        raw_query_aliases = [raw_query_aliases]
    elif not isinstance(raw_query_aliases, list):
        raw_query_aliases = []

    query_aliases = [str(alias).strip() for alias in raw_query_aliases if str(alias).strip()]
    if query_aliases:
        return unique_terms_preserve_order(query_aliases)

    aliases = venue.get('aliases', [])
    if isinstance(aliases, str):
        aliases = [aliases]
    elif not isinstance(aliases, list):
        aliases = []

    normalized_aliases = [str(alias).strip() for alias in aliases if str(alias).strip()]
    if not normalized_aliases:
        normalized_aliases = [str(venue.get('name') or '').strip()]

    def alias_rank(alias: str) -> Tuple[int, int]:
        letters_only = re.sub(r'[^A-Za-z]', '', alias)
        short_acronym_penalty = 1 if len(letters_only) <= 2 else 0
        return (-short_acronym_penalty, len(alias))

    ranked = sorted(unique_terms_preserve_order(normalized_aliases), key=alias_rank, reverse=True)
    return ranked[:2]


def build_dblp_year_query(venue_alias: str, year: int) -> str:
    parts = [str(venue_alias or '').strip(), str(year)]
    return ' '.join(part for part in parts if part)


def dblp_hit_is_main_paper(info: Dict[str, Any]) -> bool:
    title = html.unescape(str(info.get('title') or '').strip())
    if not title:
        return False

    title_lower = re.sub(r'\s+', ' ', title).strip().lower()
    venue_text = str(info.get('venue') or '').strip().lower()
    publication_type = str(info.get('type') or '').strip().lower()

    if publication_type in {'editorship', 'books and theses', 'parts in books or collections'}:
        return False

    skip_prefixes = (
        'proceedings of ',
        'joint proceedings of ',
        'companion publication of ',
        'introduction to the special section',
    )
    if any(title_lower.startswith(prefix) for prefix in skip_prefixes):
        return False

    if '@' in venue_text:
        return False
    if 'workshop' in venue_text or 'companion' in venue_text:
        return False
    return True


def dblp_candidate_has_systems_signal(candidate: Dict[str, Any], config: Dict[str, Any]) -> bool:
    domains = config.get('research_domains', {})
    excluded_keywords = config.get('excluded_keywords', [])
    scoring_settings = get_search_scoring_settings(config)
    relevance, matched_domain, _, _, _ = calculate_relevance_score(
        candidate,
        domains,
        excluded_keywords,
        scoring_settings,
    )
    return bool(matched_domain) and relevance > 0


def dblp_record_urls(info: Dict[str, Any], prefer_open_access_pdf: bool) -> Tuple[str, str]:
    urls = normalize_dblp_ee_list(info.get('ee'))
    doi = str(info.get('doi') or '').strip()
    if doi and not doi.startswith('http'):
        urls.append(f'https://doi.org/{doi}')

    source_url = first_non_empty_url(*urls)
    pdf_url = prefer_dblp_pdf_url(urls, prefer_open_access_pdf)
    if not pdf_url:
        pdf_url = derive_pdf_from_source_url(source_url)

    key = str(info.get('key') or '').strip()
    if key:
        dblp_record = f'https://dblp.org/rec/{key}.html'
        if not source_url:
            source_url = dblp_record
        elif source_url != dblp_record:
            source_url = source_url
    return source_url, pdf_url


def fetch_json_url(url: str, *, timeout_seconds: int = 45) -> Dict[str, Any]:
    if HAS_REQUESTS:
        response = requests.get(url, timeout=timeout_seconds, headers={'User-Agent': 'DailyPaper/1.0'})
        if response.status_code == 429:
            raise SemanticScholarRateLimitError('dblp-rate-limit')
        response.raise_for_status()
        return response.json()

    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise SemanticScholarRateLimitError('dblp-rate-limit') from exc
        raise


def fetch_text_url(
    url: str,
    *,
    timeout_seconds: int = VENUE_PAGE_TIMEOUT_SECONDS,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[str, str, int]:
    request_headers = headers or VENUE_PAGE_HEADERS
    if HAS_REQUESTS:
        response = requests.get(url, timeout=timeout_seconds, headers=request_headers, allow_redirects=True)
        if response.status_code == 429:
            raise SemanticScholarRateLimitError('venue-page-rate-limit')
        return response.text, response.url, int(response.status_code)

    req = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            return (
                response.read().decode('utf-8', errors='ignore'),
                response.geturl(),
                int(getattr(response, 'status', 200) or 200),
            )
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise SemanticScholarRateLimitError('venue-page-rate-limit') from exc
        return exc.read().decode('utf-8', errors='ignore'), exc.geturl() or url, int(exc.code)


def _clean_html_fragment(raw: str) -> str:
    text = re.sub(r'(?is)<(?:script|style)[^>]*>.*?</(?:script|style)>', ' ', raw or '')
    text = re.sub(r'(?is)<br\s*/?>', ' ', text)
    text = re.sub(r'(?is)</p>', ' ', text)
    text = re.sub(r'(?is)<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def html_meta_content(html_text: str, *keys: str) -> str:
    for key in keys:
        escaped = re.escape(str(key or ''))
        patterns = [
            rf'<meta[^>]+name=["\']{escaped}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+property=["\']{escaped}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{escaped}["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{escaped}["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html_text, flags=re.IGNORECASE)
            if match:
                return _clean_html_fragment(match.group(1))
    return ''


def looks_like_bot_wall(html_text: str, status_code: int) -> bool:
    lowered = str(html_text or '').lower()
    if status_code in {401, 403}:
        return True
    blockers = [
        'just a moment',
        'cf-browser-verification',
        'enable javascript and cookies',
        'captcha',
        'access denied',
    ]
    return any(token in lowered for token in blockers)


def extract_abstract_from_html(html_text: str) -> str:
    meta_abstract = html_meta_content(
        html_text,
        'citation_abstract',
        'dc.description',
        'description',
        'og:description',
        'twitter:description',
    )
    if len(meta_abstract) >= 80:
        return meta_abstract

    patterns = [
        r'(?is)<section[^>]*class=["\'][^"\']*paper-section[^"\']*["\'][^>]*>.*?<h[1-6][^>]*>\s*Abstract\s*</h[1-6]>.*?<p[^>]*class=["\'][^"\']*paper-abstract[^"\']*["\'][^>]*>(.*?)</p>',
        r'(?is)<p[^>]*class=["\'][^"\']*(?:paper-abstract|abstractInFull|abstract|article__abstract)[^"\']*["\'][^>]*>(.*?)</p>',
        r'(?is)<section[^>]*id=["\']abstract["\'][^>]*>(.*?)</section>',
        r'(?is)<div[^>]*id=["\']abstract["\'][^>]*>(.*?)</div>',
        r'(?is)<section[^>]*>.*?<h[1-6][^>]*>\s*Abstract\s*</h[1-6]>(.*?)</section>',
        r'(?is)<div[^>]*class=["\'][^"\']*abstract[^"\']*["\'][^>]*>(.*?)</div>',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text)
        if not match:
            continue
        text = _clean_html_fragment(match.group(1))
        if len(text) >= 80:
            return text
    return ''


def extract_pdf_url_from_html(html_text: str, page_url: str) -> str:
    meta_pdf = html_meta_content(html_text, 'citation_pdf_url', 'pdf_url')
    if meta_pdf:
        return urllib.parse.urljoin(page_url, meta_pdf)

    patterns = [
        r'(?is)<a[^>]+href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
        r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*(?:paper|pdf|download pdf|full text pdf)\s*</a>',
        r'(?is)<iframe[^>]+src=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text)
        if not match:
            continue
        url = urllib.parse.urljoin(page_url, str(match.group(1) or '').strip())
        if looks_like_pdf_url(url):
            return url
    return ''


def fetch_official_venue_metadata(source_url: str) -> Dict[str, Any]:
    url = str(source_url or '').strip()
    if not url:
        return {}
    try:
        html_text, final_url, status_code = fetch_text_url(url, timeout_seconds=VENUE_PAGE_TIMEOUT_SECONDS)
    except Exception as exc:
        logger.warning("Official venue fetch failed for %s: %s", url, exc)
        return {}

    if looks_like_bot_wall(html_text, status_code):
        return {'blocked': True, 'landing_page_url': final_url or url}

    abstract = extract_abstract_from_html(html_text)
    pdf_url = extract_pdf_url_from_html(html_text, final_url or url)
    result = {
        'landing_page_url': final_url or url,
        'blocked': False,
    }
    if abstract:
        result['abstract'] = abstract
    if pdf_url:
        result['pdf_url'] = pdf_url
    return result


def dblp_hit_to_candidate(
    hit: Dict[str, Any],
    *,
    venue_name: str,
    venue_alias: str,
    reference_date: datetime,
    prefer_open_access_pdf: bool,
) -> Optional[Dict[str, Any]]:
    info = hit.get('info')
    if not isinstance(info, dict):
        return None

    title = html.unescape(str(info.get('title') or '').strip())
    if not title:
        return None

    year = normalize_year(info.get('year'))
    if year is None:
        return None

    published_date = coarse_publication_datetime(year, reference_date)
    source_url, pdf_url = dblp_record_urls(info, prefer_open_access_pdf)
    record_key = str(info.get('key') or '').strip()
    paper_id = f'dblp:{record_key}' if record_key else normalize_title_key(title)

    candidate = {
        'id': paper_id,
        'paper_id': paper_id,
        'title': title,
        'summary': '',
        'abstract': '',
        'authors': dblp_info_authors(info),
        'published': str(year),
        'published_date': published_date,
        'publicationDate': str(year),
        'categories': [],
        'source': 'dblp_venue',
        'source_provider': 'dblp',
        'source_url': source_url,
        'url': source_url,
        'pdf_url': pdf_url,
        'venue': str(info.get('venue') or venue_name or '').strip(),
        'venue_source_name': venue_name,
        'venue_source_alias': venue_alias,
        'dblp_key': record_key,
        'doi': str(info.get('doi') or '').strip(),
        'dblp_type': str(info.get('type') or '').strip(),
        'access': str(info.get('access') or '').strip(),
        'selection_signals': {
            'source': 'dblp_venue',
            'venue': venue_name,
            'venue_alias': venue_alias,
        },
    }
    return candidate


def search_dblp_venue_papers(
    config: Dict[str, Any],
    venue_settings: Dict[str, Any],
    *,
    reference_date: datetime,
) -> List[Dict[str, Any]]:
    if not venue_settings.get('enabled', True):
        return []

    venues = venue_settings.get('venues', [])
    if not venues:
        return []

    session = requests.Session() if HAS_REQUESTS else None
    results: List[Dict[str, Any]] = []
    seen_keys: set[str] = set()
    min_year = reference_date.year - max(0, int(venue_settings.get('recent_years', 3) or 3)) + 1
    max_hits = max(1, int(venue_settings.get('max_hits_per_query', 10) or 10))
    max_candidates = max(1, int(venue_settings.get('max_candidates', 80) or 80))
    request_interval = max(0.0, float(venue_settings.get('request_interval_seconds', 1.0) or 0.0))
    prefer_open_access_pdf = bool(venue_settings.get('prefer_open_access_pdf', True))
    venue_search_disabled = False

    current_year = reference_date.year
    search_years = list(range(current_year, min_year - 1, -1))

    for venue in sorted(venues, key=lambda item: get_config_int(item, 'priority', 0), reverse=True):
        if venue_search_disabled:
            break
        venue_name = str(venue.get('name') or '').strip()
        priority = get_config_int(venue, 'priority', 3)
        query_aliases = venue_query_aliases(venue)
        if not query_aliases:
            continue
        for year in search_years:
            if venue_search_disabled:
                break
            for alias in query_aliases:
                query = build_dblp_year_query(alias, year)
                params = {
                    'q': query,
                    'format': 'json',
                    'h': str(max_hits),
                }
                url = f"{DBLP_PUBL_SEARCH_API_URL}?{urllib.parse.urlencode(params)}"
                try:
                    payload = fetch_json_url(url, timeout_seconds=45)
                except SemanticScholarRateLimitError:
                    logger.warning("DBLP rate limited venue search; backing off and stopping remaining venue queries")
                    if request_interval:
                        time.sleep(max(request_interval, 10.0))
                    venue_search_disabled = True
                    break
                except Exception as exc:
                    logger.warning("DBLP venue query failed for %s (%s): %s", venue_name, query, exc)
                    continue

                hits = normalize_dblp_hits(payload)
                for hit in hits:
                    info = hit.get('info')
                    if not isinstance(info, dict) or not dblp_hit_is_main_paper(info):
                        continue
                    candidate = dblp_hit_to_candidate(
                        hit,
                        venue_name=venue_name,
                        venue_alias=alias,
                        reference_date=reference_date,
                        prefer_open_access_pdf=prefer_open_access_pdf,
                    )
                    if not candidate:
                        continue
                    candidate_year = normalize_year(candidate.get('publicationDate'))
                    if candidate_year is None or candidate_year < min_year or candidate_year > current_year:
                        continue
                    if candidate_year != year:
                        continue
                    if not dblp_candidate_has_systems_signal(candidate, config):
                        continue
                    key = str(candidate.get('dblp_key') or normalize_title_key(candidate.get('title') or ''))
                    if not key or key in seen_keys:
                        continue
                    seen_keys.add(key)
                    candidate['venue_source_priority'] = priority
                    candidate['venue_query_year'] = year
                    results.append(candidate)
                    if len(results) >= max_candidates:
                        return results
                if request_interval:
                    time.sleep(request_interval)
    return results


def search_openalex_venue_papers(
    config: Dict[str, Any],
    venue_settings: Dict[str, Any],
    *,
    reference_date: datetime,
) -> List[Dict[str, Any]]:
    venues = venue_settings.get('venues', [])
    if not venues:
        return []

    results: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    source_cache: Dict[str, Optional[Dict[str, Any]]] = {}
    min_year = reference_date.year - max(0, int(venue_settings.get('recent_years', 3) or 3)) + 1
    max_hits = max(1, int(venue_settings.get('max_hits_per_query', 10) or 10))
    max_candidates = max(1, int(venue_settings.get('max_candidates', 80) or 80))
    request_interval = max(0.0, float(venue_settings.get('request_interval_seconds', 1.0) or 0.0))

    for venue in sorted(venues, key=lambda item: get_config_int(item, 'priority', 0), reverse=True):
        aliases = venue.get('aliases', []) if isinstance(venue.get('aliases'), list) else []
        if not aliases:
            continue
        venue_name = str(venue.get('name') or aliases[0]).strip()
        primary_alias = sorted(aliases, key=lambda value: (len(value), value.lower()))[0]
        if primary_alias not in source_cache:
            try:
                source_cache[primary_alias] = search_openalex_source(primary_alias)
            except Exception as exc:
                logger.warning("OpenAlex source lookup failed for %s: %s", primary_alias, exc)
                source_cache[primary_alias] = None
            if request_interval:
                time.sleep(request_interval)
        source = source_cache.get(primary_alias)
        if not source:
            continue
        source_id = str(source.get('id') or '').strip().split('/')[-1]
        if not source_id:
            continue

        params = {
            'filter': f'primary_location.source.id:{source_id},from_publication_date:{min_year}-01-01',
            'per-page': str(max_hits),
            'sort': 'publication_date:desc',
        }
        url = f"{OPENALEX_WORKS_API_URL}?{urllib.parse.urlencode(params)}"
        try:
            payload = fetch_json_url(url, timeout_seconds=45)
        except Exception as exc:
            logger.warning("OpenAlex venue query failed for %s: %s", venue_name, exc)
            continue

        works = payload.get('results', []) if isinstance(payload, dict) else []
        if not isinstance(works, list):
            works = []
        for work in works:
            if not isinstance(work, dict):
                continue
            candidate = openalex_work_to_candidate(
                work,
                venue_name=venue_name,
                venue_alias=primary_alias,
                reference_date=reference_date,
            )
            if not candidate:
                continue
            year = normalize_year(candidate.get('publicationDate')[:4] if isinstance(candidate.get('publicationDate'), str) else candidate.get('publicationDate'))
            if year is None or year < min_year:
                continue
            paper_id = str(candidate.get('paper_id') or '')
            if not paper_id or paper_id in seen_ids:
                continue
            seen_ids.add(paper_id)
            candidate['venue_source_priority'] = get_config_int(venue, 'priority', 3)
            results.append(candidate)
            if len(results) >= max_candidates:
                return results
        if request_interval:
            time.sleep(request_interval)
    return results


def search_venue_papers(
    config: Dict[str, Any],
    venue_settings: Dict[str, Any],
    *,
    reference_date: datetime,
) -> List[Dict[str, Any]]:
    provider = str(venue_settings.get('provider') or DEFAULT_VENUE_SOURCE_SETTINGS['provider']).strip().lower()
    if provider == 'dblp':
        return search_dblp_venue_papers(config, venue_settings, reference_date=reference_date)
    if provider == 'openalex':
        return search_openalex_venue_papers(config, venue_settings, reference_date=reference_date)
    logger.info("Skipping venue search because provider=%s is not implemented", provider)
    return []


def paper_in_cooldown(
    paper: Dict[str, Any],
    index_entries: Dict[str, Dict[str, Any]],
    history_settings: Dict[str, Any],
    reference_date: datetime,
) -> bool:
    key = paper_index_key(paper)
    if not key or key not in index_entries:
        return False

    entry = index_entries[key]
    reference = reference_date.date()
    last_analysis = parse_date_flexible(entry.get('last_analysis_date'))
    last_recommended = parse_date_flexible(entry.get('last_recommended_date'))
    if (last_analysis and last_analysis.date() == reference) or (last_recommended and last_recommended.date() == reference):
        return False

    cooldown_until = parse_date_flexible(entry.get('cooldown_until'))
    if cooldown_until and cooldown_until.date() >= reference:
        return True

    if last_analysis and (reference - last_analysis.date()).days < max(0, history_settings['analyzed_cooldown_days']):
        return True

    recommended_cooldown_days = history_settings['recommended_cooldown_days']
    paper_lane = str(paper.get('selection_lane') or paper.get('source_lane') or '').strip().lower()
    entry_lane = str(entry.get('source_lane') or '').strip().lower()
    if paper_lane == 'classic' or entry_lane == 'classic':
        recommended_cooldown_days = history_settings.get('classic_recommended_cooldown_days', recommended_cooldown_days)

    if last_recommended and (reference - last_recommended.date()).days < max(0, recommended_cooldown_days):
        return True

    return False


def should_activate_classic_slot(reference_date: datetime, classic_settings: Dict[str, Any]) -> bool:
    if not classic_settings.get('enabled', True):
        return False
    anchor_date = parse_date_flexible(classic_settings.get('anchor_date'))
    if anchor_date is None:
        anchor_date = reference_date
    cadence_days = max(1, int(classic_settings.get('cadence_days', 3) or 3))
    delta_days = abs((reference_date.date() - anchor_date.date()).days)
    return (delta_days % cadence_days) == 0


def classic_rotation_score(
    paper: Dict[str, Any],
    reference_date: datetime,
    classic_settings: Dict[str, Any],
) -> float:
    seed = str(classic_settings.get('random_seed') or DEFAULT_CLASSIC_SETTINGS['random_seed'])
    key = paper_index_key(paper) or normalize_title_key(paper.get('title', ''))
    digest = hashlib.sha256(f'{seed}|{reference_date.date().isoformat()}|{key}'.encode('utf-8')).hexdigest()
    random_unit = int(digest[:8], 16) / 0xFFFFFFFF
    base = float(paper.get('scores', {}).get('recommendation', 0) or 0)
    return round(base + random_unit * 1.5, 4)


def backlog_paper_to_candidate(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    title = str(item.get('title') or '').strip()
    if not title:
        return None
    paper_id = str(item.get('paper_id') or '').strip()
    priority = max(1, min(5, get_config_int(item, 'priority', 3)))
    recommendation = float(item.get('recommendation_score', round(7.2 + priority * 0.45, 2)))
    published = str(item.get('published') or '').strip()
    if not published and item.get('year'):
        published = f"{int(item['year'])}-01-01"
    candidate = {
        'paper_id': paper_id,
        'arxiv_id': paper_id,
        'title': title,
        'summary': str(item.get('summary') or item.get('reason_to_read') or '').strip(),
        'authors': item.get('authors', []),
        'published': published,
        'published_date': parse_date_flexible(published),
        'categories': item.get('categories', []),
        'source': 'classic_backlog',
        'matched_domain': str(item.get('matched_domain') or item.get('domain') or 'Classic Systems').strip(),
        'matched_keywords': item.get('topic_tags', []),
        'matched_domain_priority': priority,
        'domain_preference_bonus': round(max(priority - 1, 0) * 0.15, 2),
        'selection_lane': 'classic',
        'is_hot_paper': False,
        'source_url': str(item.get('source_url') or item.get('url') or '').strip(),
        'pdf_url': str(item.get('pdf_url') or '').strip(),
        'scores': {
            'relevance': round(min(1.4 + priority * 0.3, SCORE_MAX), 2),
            'recency': 0.0,
            'popularity': round(min(1.0 + priority * 0.25, SCORE_MAX), 2),
            'quality': round(min(1.4 + priority * 0.25, SCORE_MAX), 2),
            'recommendation': recommendation,
        },
        'analysis_candidate_score': round(min(recommendation * 0.92 + priority * 0.25, 10.0), 2),
        'analysis_signals': unique_terms_preserve_order(item.get('topic_tags', []))[:10],
        'analysis_components': {
            'signal_strength': round(min(6.0 + priority * 0.7, 10.0), 2),
            'implementation_depth': round(min(5.5 + priority * 0.6, 10.0), 2),
            'evidence_strength': round(min(5.0 + priority * 0.5, 10.0), 2),
        },
    }
    return candidate


def assign_selection_lane(paper: Dict[str, Any], reference_date: datetime, lane_settings: Dict[str, Any]) -> str:
    if str(paper.get('selection_lane') or '').strip().lower() == 'classic' or paper.get('source') == 'classic_backlog':
        return 'classic'

    published_date = parse_date_flexible(
        paper.get('published_date')
        or paper.get('published')
        or paper.get('publicationDate')
    )
    if not published_date:
        return 'established'
    if published_date.tzinfo and reference_date.tzinfo is None:
        comparison_date = reference_date.replace(tzinfo=published_date.tzinfo)
    elif published_date.tzinfo is None and reference_date.tzinfo:
        comparison_date = reference_date.replace(tzinfo=None)
    else:
        comparison_date = reference_date
    age_days = max(0, (comparison_date - published_date).days)
    if age_days <= lane_settings['fresh']['max_age_days']:
        return 'fresh'
    if age_days <= lane_settings['established']['max_age_days']:
        return 'established'
    return 'classic'


def select_papers_by_lanes(
    candidates: List[Dict[str, Any]],
    top_n: int,
    lane_settings: Dict[str, Any],
    classic_settings: Dict[str, Any],
    history_settings: Dict[str, Any],
    index_entries: Dict[str, Dict[str, Any]],
    reference_date: datetime,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    buckets: Dict[str, List[Dict[str, Any]]] = {'fresh': [], 'established': [], 'classic': []}
    cooled_buckets: Dict[str, List[Dict[str, Any]]] = {'fresh': [], 'established': [], 'classic': []}
    history_filtered = 0
    history_relaxed = 0
    classic_slot_active = should_activate_classic_slot(reference_date, classic_settings)

    for paper in candidates:
        lane = assign_selection_lane(paper, reference_date, lane_settings)
        paper['selection_lane'] = lane
        if lane == 'classic' and not classic_slot_active:
            continue
        if paper_in_cooldown(paper, index_entries, history_settings, reference_date):
            history_filtered += 1
            cooled_buckets.setdefault(lane, []).append(paper)
            continue
        buckets.setdefault(lane, []).append(paper)

    for lane_name, items in buckets.items():
        if lane_name == 'classic':
            for item in items:
                item['classic_rotation_score'] = classic_rotation_score(item, reference_date, classic_settings)
            items.sort(
                key=lambda item: (
                    float(item.get('classic_rotation_score', 0) or 0),
                    float(item.get('scores', {}).get('recommendation', 0) or 0),
                ),
                reverse=True,
            )
        else:
            items.sort(key=lambda item: float(item.get('scores', {}).get('recommendation', 0) or 0), reverse=True)

    selected: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def maybe_add(paper: Dict[str, Any]) -> None:
        key = paper_index_key(paper)
        if not key or key in seen:
            return
        selected.append(paper)
        seen.add(key)

    for lane_name in ['fresh', 'established', 'classic']:
        quota = max(0, int(lane_settings.get(lane_name, {}).get('quota', 0)))
        if lane_name == 'classic' and not classic_slot_active:
            quota = 0
        for paper in buckets.get(lane_name, [])[:quota]:
            if len(selected) >= top_n:
                break
            maybe_add(paper)

    if len(selected) < top_n:
        for lane_name in lane_settings.get('fill_order', DEFAULT_LANE_SETTINGS['fill_order']):
            if lane_name == 'classic':
                if not classic_slot_active:
                    continue
                if sum(1 for paper in selected if paper.get('selection_lane') == 'classic') >= max(0, int(lane_settings.get('classic', {}).get('quota', 0))):
                    continue
            for paper in buckets.get(lane_name, []):
                if len(selected) >= top_n:
                    break
                maybe_add(paper)

    needs_relaxation = (
        top_n > 0
        and sum(1 for paper in selected if paper.get('selection_lane') in {'fresh', 'established'}) == 0
        and any(cooled_buckets.get(name) for name in ['fresh', 'established'])
    )
    if needs_relaxation:
        for lane_name in ['fresh', 'established']:
            cooled_buckets[lane_name].sort(
                key=lambda item: float(item.get('scores', {}).get('recommendation', 0) or 0),
                reverse=True,
            )
        for lane_name in lane_settings.get('fill_order', DEFAULT_LANE_SETTINGS['fill_order']):
            if lane_name == 'classic':
                continue
            for paper in cooled_buckets.get(lane_name, []):
                if len(selected) >= top_n:
                    break
                before = len(selected)
                maybe_add(paper)
                if len(selected) > before:
                    paper['history_relaxed'] = True
                    history_relaxed += 1

    lane_counts = {
        'fresh': sum(1 for paper in selected if paper.get('selection_lane') == 'fresh'),
        'established': sum(1 for paper in selected if paper.get('selection_lane') == 'established'),
        'classic': sum(1 for paper in selected if paper.get('selection_lane') == 'classic'),
        'history_filtered': history_filtered,
        'history_relaxed': history_relaxed,
        'classic_slot_active': int(classic_slot_active),
    }
    return selected, lane_counts


def normalize_keyword_rules(raw_rules: Any) -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    if not isinstance(raw_rules, list):
        return rules

    for raw_rule in raw_rules:
        if isinstance(raw_rule, str):
            term = raw_rule.strip()
            if not term:
                continue
            rules.append({
                'term': term,
                'fields': ['title', 'summary'],
                'weight': 1.0,
            })
            continue

        if not isinstance(raw_rule, dict):
            continue

        term = str(raw_rule.get('term') or raw_rule.get('keyword') or raw_rule.get('phrase') or '').strip()
        if not term:
            continue

        raw_fields = raw_rule.get('fields', ['title', 'summary'])
        if isinstance(raw_fields, str):
            fields = [part.strip().lower() for part in raw_fields.split(',') if part.strip()]
        elif isinstance(raw_fields, list):
            fields = [str(part).strip().lower() for part in raw_fields if str(part).strip()]
        else:
            fields = ['title', 'summary']

        if not fields:
            fields = ['title', 'summary']

        rules.append({
            'term': term,
            'fields': fields,
            'weight': get_config_float(raw_rule, 'weight', 1.0),
        })

    return rules


def keyword_rule_matches(rule: Dict[str, Any], title: str, summary: str) -> List[str]:
    term = str(rule.get('term') or '').strip().lower()
    if not term:
        return []

    def contains_term(text: str) -> bool:
        normalized = str(text or '').lower()
        tokens = re.findall(r'[a-z0-9]+', term)
        if not tokens:
            return term in normalized
        pattern = r'(?<![a-z0-9])' + r'[\s\-_:/\\]*'.join(re.escape(token) for token in tokens) + r'(?![a-z0-9])'
        return re.search(pattern, normalized) is not None

    matched_fields: List[str] = []
    fields = rule.get('fields', [])
    if 'title' in fields and contains_term(title):
        matched_fields.append('title')
    if 'summary' in fields and contains_term(summary):
        matched_fields.append('summary')
    return matched_fields


def unique_terms_preserve_order(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for item in items:
        text = str(item or '').strip()
        lowered = text.lower()
        if not text or lowered in seen:
            continue
        seen.add(lowered)
        result.append(text)
    return result


def evaluate_keyword_rules(raw_rules: Any, title: str, summary: str) -> Dict[str, Any]:
    matched_terms: List[str] = []
    title_terms: List[str] = []
    summary_terms: List[str] = []

    for rule in normalize_keyword_rules(raw_rules):
        matched_fields = keyword_rule_matches(rule, title, summary)
        if not matched_fields:
            continue
        term = str(rule.get('term') or '').strip()
        if not term:
            continue
        matched_terms.append(term)
        if 'title' in matched_fields:
            title_terms.append(term)
        if 'summary' in matched_fields:
            summary_terms.append(term)

    matched_terms = unique_terms_preserve_order(matched_terms)
    title_terms = unique_terms_preserve_order(title_terms)
    summary_terms = unique_terms_preserve_order(summary_terms)
    return {
        'terms': matched_terms,
        'title_terms': title_terms,
        'summary_terms': summary_terms,
        'match_count': len(matched_terms),
        'title_match_count': len(title_terms),
        'summary_match_count': len(summary_terms),
    }


def get_recency_thresholds(config: Dict[str, Any]) -> List[Tuple[int, float]]:
    raw_thresholds = get_search_scoring_settings(config).get('recency_thresholds')
    thresholds: List[Tuple[int, float]] = []

    if isinstance(raw_thresholds, list):
        for item in raw_thresholds:
            if not isinstance(item, dict):
                continue
            try:
                thresholds.append((int(item['days']), float(item['score'])))
            except (KeyError, TypeError, ValueError):
                continue

    return thresholds or RECENCY_THRESHOLDS


def get_recommendation_weights(
    scoring_settings: Dict[str, Any],
    key: str,
    defaults: Dict[str, float],
) -> Dict[str, float]:
    raw_weights = scoring_settings.get(key, {})
    if not isinstance(raw_weights, dict):
        return defaults

    weights: Dict[str, float] = {}
    for metric, default_value in defaults.items():
        weights[metric] = get_config_float(raw_weights, metric, default_value)
    return weights


def calculate_date_windows(
    target_date: Optional[datetime] = None,
    *,
    recent_window_days: int = 30,
    hot_window_days: int = 365,
    hot_exclude_recent_days: Optional[int] = None,
) -> Tuple[datetime, datetime, datetime, datetime]:
    """
    计算两个时间窗口：最近30天和过去一年（除去最近30天）

    Args:
        target_date: 基准日期，如果为 None 则使用当前日期

    Returns:
        (window_30d_start, window_30d_end, window_1y_start, window_1y_end)
        - window_30d_start: 30天窗口开始日期
        - window_30d_end: 30天窗口结束日期（即 target_date）
        - window_1y_start: 一年窗口开始日期
        - window_1y_end: 一年窗口结束日期（即 31天前）
    """
    if target_date is None:
        target_date = datetime.now()

    if hot_exclude_recent_days is None:
        hot_exclude_recent_days = recent_window_days

    # 最近窗口: [target_date - recent_window_days, target_date]
    window_30d_start = target_date - timedelta(days=recent_window_days)
    window_30d_end = target_date

    # 热门窗口（除去最近窗口）: [target_date - hot_window_days, target_date - hot_exclude_recent_days - 1 days]
    window_1y_start = target_date - timedelta(days=hot_window_days)
    window_1y_end = target_date - timedelta(days=hot_exclude_recent_days + 1)

    return window_30d_start, window_30d_end, window_1y_start, window_1y_end


def search_arxiv_by_date_range(
    categories: List[str],
    start_date: datetime,
    end_date: datetime,
    max_results: int = 200,
    max_retries: int = 3
) -> List[Dict]:
    """
    使用 arXiv API 搜索指定日期范围内的论文

    Args:
        categories: arXiv 分类列表
        start_date: 开始日期
        end_date: 结束日期
        max_results: 最大结果数
        max_retries: 最大重试次数

    Returns:
        论文列表
    """
    # 构建分类查询
    category_query = "+OR+".join([f"cat:{cat}" for cat in categories])

    # 构建日期范围查询 (arXiv 使用 YYYYMMDD 格式)
    date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000+TO+{end_date.strftime('%Y%m%d')}2359]"

    # 组合查询
    full_query = f"({category_query})+AND+{date_query}"

    # 构建 URL
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={full_query}&"
        f"max_results={max_results}&"
        f"sortBy=submittedDate&"
        f"sortOrder=descending"
    )

    logger.info("[arXiv] Searching papers from %s to %s", start_date.date(), end_date.date())
    logger.debug("[arXiv] URL: %s...", url[:120])

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                xml_content = response.read().decode('utf-8')
                papers = parse_arxiv_xml(xml_content)
                logger.info("[arXiv] Found %d papers", len(papers))
                return papers
        except Exception as e:
            logger.warning("[arXiv] Error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                logger.info("[arXiv] Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
            else:
                logger.error("[arXiv] Failed after %d attempts", max_retries)
                return []

    return []


def search_semantic_scholar_hot_papers(
    query: str,
    start_date: datetime,
    end_date: datetime,
    top_k: int = 20,
    max_retries: int = 3
) -> List[Dict]:
    """
    使用 Semantic Scholar API 搜索指定时间范围内的高影响力论文

    Args:
        query: 搜索关键词
        start_date: 开始日期
        end_date: 结束日期
        top_k: 返回前 K 篇高影响力论文
        max_retries: 最大重试次数

    Returns:
        按高影响力引用数排序的论文列表
    """
    # 构建日期范围 (Semantic Scholar 使用 YYYY-MM-DD:YYYY-MM-DD 格式)
    date_range = f"{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"

    # 构建请求参数
    params = {
        "query": query,
        "publicationDateOrYear": date_range,
        "limit": SEMANTIC_SCHOLAR_QUERY_LIMIT,
        "fields": SEMANTIC_SCHOLAR_FIELDS
    }

    headers = {
        "User-Agent": "StartMyDay-PaperFetcher/1.0"
    }
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key

    logger.info("[S2] Searching hot papers from %s to %s", start_date.date(), end_date.date())
    logger.info("[S2] Query: '%s'", query)

    for attempt in range(max_retries):
        try:
            if HAS_REQUESTS:
                response = requests.get(
                    SEMANTIC_SCHOLAR_API_URL,
                    params=params,
                    headers=headers,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
            else:
                # 使用 urllib
                query_string = urllib.parse.urlencode(params)
                url = f"{SEMANTIC_SCHOLAR_API_URL}?{query_string}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))

            papers = data.get("data", [])
            if not papers:
                logger.info("[S2] No papers found")
                return []

            # 本地二次过滤与排序
            valid_papers = []
            for p in papers:
                # 过滤掉没有标题或摘要的无效条目
                if not p.get("title") or not p.get("abstract"):
                    continue

                # 处理可能的 None 值
                inf_cit = p.get("influentialCitationCount") or 0
                cit = p.get("citationCount") or 0

                p["influentialCitationCount"] = inf_cit
                p["citationCount"] = cit

                # 标记来源
                p["source"] = "semantic_scholar"
                p["hot_score"] = inf_cit  # 使用高影响力引用数作为热度分数

                valid_papers.append(p)

            # 按高影响力引用数倒序排列
            sorted_papers = sorted(
                valid_papers,
                key=lambda x: x["influentialCitationCount"],
                reverse=True
            )

            logger.info("[S2] Found %d valid papers, returning top %d", len(sorted_papers), top_k)
            return sorted_papers[:top_k]

        except Exception as e:
            error_msg = str(e)
            logger.warning("[S2] Error (attempt %d/%d): %s", attempt + 1, max_retries, e)

            # 检查是否是 429 错误（Too Many Requests）
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            retry_after = getattr(getattr(e, "response", None), "headers", {}).get("Retry-After")
            is_rate_limit = status_code == 429 or "429" in error_msg or "Too Many Requests" in error_msg

            if attempt < max_retries - 1:
                # 对于 429 错误，使用更长的等待时间
                if is_rate_limit:
                    if not api_key:
                        raise SemanticScholarRateLimitError(
                            "Semantic Scholar rate limited unauthenticated requests"
                        ) from e
                    wait_time = int(retry_after) if retry_after and str(retry_after).isdigit() else S2_RATE_LIMIT_WAIT
                    logger.warning("[S2] Rate limit hit. Waiting %d seconds...", wait_time)
                else:
                    wait_time = (2 ** attempt) * 2
                    logger.info("[S2] Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
            else:
                if is_rate_limit and not api_key:
                    raise SemanticScholarRateLimitError(
                        "Semantic Scholar rate limited unauthenticated requests"
                    ) from e
                logger.error("[S2] Failed after %d attempts", max_retries)
                return []

    return []


def search_hot_papers_from_categories(
    categories: List[str],
    start_date: datetime,
    end_date: datetime,
    top_k_per_category: int = 5
) -> List[Dict]:
    """
    为多个 arXiv 分类搜索高影响力论文

    Args:
        categories: arXiv 分类列表
        start_date: 开始日期
        end_date: 结束日期
        top_k_per_category: 每个分类返回的论文数

    Returns:
        合并后的高影响力论文列表
    """
    all_hot_papers = []
    seen_arxiv_ids = set()

    for category in categories:
        # 获取对应的关键词
        query = ARXIV_CATEGORY_KEYWORDS.get(category, category)

        try:
            papers = search_semantic_scholar_hot_papers(
                query=query,
                start_date=start_date,
                end_date=end_date,
                top_k=top_k_per_category
            )
        except SemanticScholarRateLimitError:
            logger.warning(
                "[S2] Rate limit encountered without API key. Stopping hot-paper search early and continuing with current results."
            )
            break

        # 去重（基于 arXiv ID）
        for p in papers:
            # 安全地从 externalIds 字典中提取 ArXiv 编号
            arxiv_id = p.get("externalIds", {}).get("ArXiv") if p.get("externalIds") else None

            # 统一写入 arxiv_id 字段，方便最后 Step 3 的全局去重
            p["arxiv_id"] = arxiv_id

            if arxiv_id and arxiv_id not in seen_arxiv_ids:
                seen_arxiv_ids.add(arxiv_id)
                all_hot_papers.append(p)
            elif not arxiv_id:
                # 没有 arXiv ID 的也保留（可能是其他来源的论文）
                all_hot_papers.append(p)

        time.sleep(S2_CATEGORY_REQUEST_INTERVAL)

    # 最终按影响力引用数排序
    all_hot_papers.sort(key=lambda x: x.get("influentialCitationCount", 0), reverse=True)

    return all_hot_papers


def search_hot_papers_from_arxiv_fallback(
    categories: List[str],
    start_date: datetime,
    end_date: datetime,
    max_results: int = 120,
) -> List[Dict]:
    """
    当 Semantic Scholar 不可用或没有结果时，使用 arXiv 一年窗口回退搜索。

    这里无法得到真实引用数，因此只提供“过去一年但不在最近窗口内”的候选集合，
    后续仍由相关性、质量和较弱的热门度启发式排序。
    """
    papers = search_arxiv_by_date_range(
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        max_results=max_results,
    )
    for paper in papers:
        paper['source'] = 'arxiv_hot_fallback'
        paper['hot_score'] = 0
    logger.info("[arXiv fallback] Found %d hot-window papers", len(papers))
    return papers


def _semantic_scholar_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": "StartMyDay-PaperFetcher/1.0",
        "Content-Type": "application/json",
    }
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def _normalize_semantic_scholar_journal(raw: Any) -> str:
    if isinstance(raw, dict):
        for key in ['name', 'title', 'venue']:
            value = str(raw.get(key) or '').strip()
            if value:
                return value
        return ''
    return str(raw or '').strip()


def _google_scholar_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }


def _strip_html_text(raw: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', raw or '')
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _normalize_title_for_match(text: str) -> str:
    lowered = _strip_html_text(text).lower()
    return re.sub(r'[^a-z0-9]+', ' ', lowered).strip()


def _title_similarity(left: str, right: str) -> float:
    normalized_left = _normalize_title_for_match(left)
    normalized_right = _normalize_title_for_match(right)
    if not normalized_left or not normalized_right:
        return 0.0
    return SequenceMatcher(None, normalized_left, normalized_right).ratio()


def _normalize_google_scholar_venue(meta_line: str) -> str:
    text = _strip_html_text(meta_line)
    if not text:
        return ''

    parts = [part.strip() for part in text.split(' - ') if part.strip()]
    candidate = parts[1] if len(parts) >= 2 else text
    candidate = re.sub(
        r'arxiv(?: preprint)?\s*arxiv:\s*\d+\.\d+(?:v\d+)?',
        'arXiv preprint',
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(r'\b\d{4}\b', '', candidate)
    candidate = re.sub(r'\s+', ' ', candidate).strip(' ,;-')
    return candidate


def search_google_scholar_metadata_by_title(
    title: str,
    *,
    min_title_similarity: float = GOOGLE_SCHOLAR_MIN_TITLE_SIMILARITY,
) -> Optional[Dict[str, Any]]:
    clean_title = str(title or '').strip()
    if not clean_title:
        return None

    params = {
        'hl': 'en',
        'q': f'"{clean_title}"',
        'num': 1,
        'as_vis': 1,
    }

    if HAS_REQUESTS:
        response = requests.get(
            GOOGLE_SCHOLAR_SEARCH_URL,
            params=params,
            headers=_google_scholar_headers(),
            timeout=20,
        )
        response.raise_for_status()
        content = response.text
    else:
        query_string = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{GOOGLE_SCHOLAR_SEARCH_URL}?{query_string}",
            headers=_google_scholar_headers(),
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8', errors='ignore')

    lowered_content = content.lower()
    if 'unusual traffic' in lowered_content or 'please show you\'re not a robot' in lowered_content:
        raise RuntimeError('Google Scholar blocked the request')

    block_match = re.search(
        r'(<div class="gs_r gs_or gs_scl[^"]*".*?)(?=<div class="gs_r gs_or gs_scl|<div id="gs_ccl_bottom"|$)',
        content,
        flags=re.DOTALL,
    )
    if not block_match:
        return None

    block = block_match.group(1)
    title_match = re.search(r'<h3 class="gs_rt[^"]*".*?>(.*?)</h3>', block, flags=re.DOTALL)
    if not title_match:
        return None

    result_title = _strip_html_text(title_match.group(1))
    if _title_similarity(clean_title, result_title) < min_title_similarity:
        return None

    meta_match = re.search(r'<div class="gs_a">(.*?)</div>', block, flags=re.DOTALL)
    meta_line = meta_match.group(1) if meta_match else ''
    citation_match = re.search(r'Cited by\s+([\d,]+)', _strip_html_text(block), flags=re.IGNORECASE)
    citation_count = None
    if citation_match:
        try:
            citation_count = int(citation_match.group(1).replace(',', ''))
        except ValueError:
            citation_count = None

    venue = _normalize_google_scholar_venue(meta_line)
    result: Dict[str, Any] = {
        'title': result_title,
        'venue': venue,
    }
    if citation_count is not None:
        result['citationCount'] = citation_count
    return result


def hydrate_papers_with_google_scholar_metadata(
    papers: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> None:
    settings = get_metadata_fallback_settings(config)
    if not settings['google_scholar_enabled']:
        return

    interval_seconds = max(0.0, float(settings['google_scholar_request_interval_seconds']))
    min_title_similarity = max(0.5, min(0.95, float(settings['google_scholar_min_title_similarity'])))
    last_request_at = 0.0

    for paper in papers:
        needs_citation = paper.get('citationCount') is None
        needs_venue = not str(paper.get('venue') or paper.get('journal_ref') or '').strip()
        if not needs_citation and not needs_venue:
            continue

        title = str(paper.get('title') or '').strip()
        if not title:
            continue

        wait_seconds = interval_seconds - (time.time() - last_request_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        try:
            metadata = search_google_scholar_metadata_by_title(
                title,
                min_title_similarity=min_title_similarity,
            )
            last_request_at = time.time()
        except Exception as exc:
            logger.warning("[Google Scholar] Metadata hydration failed for '%s': %s", title, exc)
            if 'blocked' in str(exc).lower() or 'robot' in str(exc).lower():
                break
            continue

        if not metadata:
            continue

        citation_count = metadata.get('citationCount')
        venue = str(metadata.get('venue') or '').strip()
        if needs_citation and citation_count is not None:
            paper['citationCount'] = citation_count
        if needs_venue and venue:
            if 'journal' in venue.lower() or 'transactions' in venue.lower() or 'review' in venue.lower():
                paper['journal_ref'] = venue
            else:
                paper['venue'] = venue


def hydrate_papers_with_semantic_scholar_metadata(
    papers: List[Dict[str, Any]],
    *,
    max_retries: int = 2,
) -> None:
    """
    对最终入选论文做轻量 metadata 补充，尽量填充 citation / venue 信息。
    失败时静默降级，不影响主流程。
    """
    ids: List[str] = []
    indexed_papers: List[Dict[str, Any]] = []

    for paper in papers:
        arxiv_id = str(paper.get('arxiv_id') or paper.get('arxivId') or '').strip()
        if not arxiv_id:
            continue
        ids.append(f'ARXIV:{arxiv_id}')
        indexed_papers.append(paper)

    if not ids:
        return

    params = {
        'fields': SEMANTIC_SCHOLAR_BATCH_FIELDS,
    }
    headers = _semantic_scholar_headers()
    payload = json.dumps({'ids': ids}).encode('utf-8')

    for attempt in range(max_retries):
        try:
            if HAS_REQUESTS:
                response = requests.post(
                    SEMANTIC_SCHOLAR_BATCH_API_URL,
                    params=params,
                    headers=headers,
                    data=payload,
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
            else:
                query_string = urllib.parse.urlencode(params)
                req = urllib.request.Request(
                    f"{SEMANTIC_SCHOLAR_BATCH_API_URL}?{query_string}",
                    headers=headers,
                    data=payload,
                    method='POST',
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    data = json.loads(response.read().decode('utf-8'))

            if not isinstance(data, list):
                return

            for paper, record in zip(indexed_papers, data):
                if not isinstance(record, dict):
                    continue
                citation_count = record.get('citationCount')
                influential_count = record.get('influentialCitationCount')
                venue = str(record.get('venue') or '').strip()
                journal = _normalize_semantic_scholar_journal(record.get('journal'))

                if citation_count is not None:
                    paper['citationCount'] = citation_count
                if influential_count is not None:
                    paper['influentialCitationCount'] = influential_count
                if venue and not paper.get('venue'):
                    paper['venue'] = venue
                if journal and not paper.get('journal_ref'):
                    paper['journal_ref'] = journal
            return
        except Exception as exc:
            logger.warning("[S2 batch] Metadata hydration failed (attempt %d/%d): %s", attempt + 1, max_retries, exc)
            if attempt < max_retries - 1:
                time.sleep(3)


def parse_arxiv_xml(xml_content: str) -> List[Dict]:
    """
    解析 arXiv XML 结果

    Args:
        xml_content: XML 内容

    Returns:
        论文列表，每篇论文包含 ID、标题、作者、摘要等信息
    """
    papers = []

    try:
        root = ET.fromstring(xml_content)

        # 查找所有 entry 元素
        for entry in root.findall('atom:entry', ARXIV_NS):
            paper = {}

            # 提取 ID
            id_elem = entry.find('atom:id', ARXIV_NS)
            if id_elem is not None:
                paper['id'] = id_elem.text
                # 提取 arXiv ID（从 URL 中提取）
                match = re.search(r'arXiv:(\d+\.\d+(?:v\d+)?)', paper['id'])
                if match:
                    paper['arxiv_id'] = match.group(1)
                else:
                    match = re.search(r'/(\d+\.\d+(?:v\d+)?)$', paper['id'])
                    if match:
                        paper['arxiv_id'] = match.group(1)

            # 提取标题
            title_elem = entry.find('atom:title', ARXIV_NS)
            if title_elem is not None:
                paper['title'] = title_elem.text.strip()

            # 提取摘要
            summary_elem = entry.find('atom:summary', ARXIV_NS)
            if summary_elem is not None:
                paper['summary'] = summary_elem.text.strip()

            # 提取作者
            authors = []
            author_details = []
            institutions: List[str] = []
            for author in entry.findall('atom:author', ARXIV_NS):
                name_elem = author.find('atom:name', ARXIV_NS)
                author_name = ''
                if name_elem is not None:
                    author_name = str(name_elem.text or '').strip()
                    if author_name:
                        authors.append(author_name)
                author_detail: Dict[str, Any] = {}
                if author_name:
                    author_detail['name'] = author_name
                affiliation_elem = author.find('arxiv:affiliation', ARXIV_NS)
                affiliation = str(affiliation_elem.text or '').strip() if affiliation_elem is not None else ''
                if affiliation:
                    author_detail['affiliation'] = affiliation
                    if affiliation not in institutions:
                        institutions.append(affiliation)
                if author_detail:
                    author_details.append(author_detail)
            paper['authors'] = authors
            if author_details:
                paper['author_details'] = author_details
            if institutions:
                paper['institutions'] = institutions

            # 提取发布日期
            published_elem = entry.find('atom:published', ARXIV_NS)
            if published_elem is not None:
                paper['published'] = published_elem.text
                # 解析日期
                try:
                    paper['published_date'] = datetime.fromisoformat(
                        paper['published'].replace('Z', '+00:00')
                    )
                except (ValueError, TypeError):
                    paper['published_date'] = None

            # 提取更新日期
            updated_elem = entry.find('atom:updated', ARXIV_NS)
            if updated_elem is not None:
                paper['updated'] = updated_elem.text

            # 提取 arXiv 元数据
            comment_elem = entry.find('arxiv:comment', ARXIV_NS)
            if comment_elem is not None and str(comment_elem.text or '').strip():
                paper['comments'] = str(comment_elem.text or '').strip()

            journal_ref_elem = entry.find('arxiv:journal_ref', ARXIV_NS)
            if journal_ref_elem is not None and str(journal_ref_elem.text or '').strip():
                paper['journal_ref'] = str(journal_ref_elem.text or '').strip()

            doi_elem = entry.find('arxiv:doi', ARXIV_NS)
            if doi_elem is not None and str(doi_elem.text or '').strip():
                paper['doi'] = str(doi_elem.text or '').strip()

            primary_category_elem = entry.find('arxiv:primary_category', ARXIV_NS)
            if primary_category_elem is not None and primary_category_elem.get('term'):
                paper['primary_category'] = primary_category_elem.get('term')

            # 提取分类
            categories = []
            for category in entry.findall('atom:category', ARXIV_NS):
                term = category.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories

            # 提取 PDF 链接
            for link in entry.findall('atom:link', ARXIV_NS):
                if link.get('title') == 'pdf':
                    paper['pdf_url'] = link.get('href')
                    break

            # 提取主页面链接
            if 'id' in paper:
                paper['url'] = paper['id']

            # 标记来源
            paper['source'] = 'arxiv'

            papers.append(paper)

    except ET.ParseError as e:
        logger.error("Error parsing XML: %s", e)
        raise

    return papers


def calculate_relevance_score(
    paper: Dict,
    domains: Dict,
    excluded_keywords: List[str],
    scoring_settings: Dict[str, Any],
) -> Tuple[float, Optional[str], List[str], int, Dict[str, Any]]:
    """
    计算论文与研究兴趣的相关性评分

    Args:
        paper: 论文信息
        domains: 研究领域配置
        excluded_keywords: 排除关键词

    Returns:
        (相关性评分, 匹配的领域, 匹配的关键词列表, 领域优先级, 匹配细节)
    """
    title = paper.get('title', '').lower()
    summary = paper.get('summary', '').lower() if 'summary' in paper else paper.get('abstract', '').lower()
    categories = set(paper.get('categories', []))

    # 检查排除关键词
    for rule in normalize_keyword_rules(excluded_keywords):
        if keyword_rule_matches(rule, title, summary):
            return 0, None, [], 0, {}

    max_score = 0
    best_domain = None
    matched_keywords = []
    best_priority = 0
    best_match_details: Dict[str, Any] = {}

    title_keyword_boost = get_config_float(
        scoring_settings,
        'relevance_title_keyword_boost',
        RELEVANCE_TITLE_KEYWORD_BOOST,
    )
    summary_keyword_boost = get_config_float(
        scoring_settings,
        'relevance_summary_keyword_boost',
        RELEVANCE_SUMMARY_KEYWORD_BOOST,
    )
    category_match_boost = get_config_float(
        scoring_settings,
        'relevance_category_match_boost',
        RELEVANCE_CATEGORY_MATCH_BOOST,
    )

    # 遍历所有领域
    for domain_name, domain_config in domains.items():
        score = 0
        domain_matched_keywords = []
        text_match_count = 0

        # 关键词匹配
        keywords = normalize_keyword_rules(domain_config.get('keywords', []))
        negative_keywords = normalize_keyword_rules(domain_config.get('negative_keywords', []))

        if any(keyword_rule_matches(rule, title, summary) for rule in negative_keywords):
            continue

        for rule in keywords:
            matched_fields = keyword_rule_matches(rule, title, summary)
            if not matched_fields:
                continue
            text_match_count += 1
            domain_matched_keywords.append(rule['term'])
            weight = get_config_float(rule, 'weight', 1.0)
            if 'title' in matched_fields:
                score += title_keyword_boost * weight
            else:
                score += summary_keyword_boost * weight

        # 类别匹配
        domain_categories = domain_config.get('arxiv_categories', [])
        matched_categories: List[str] = []
        for cat in domain_categories:
            if cat in categories:
                score += category_match_boost
                domain_matched_keywords.append(cat)
                matched_categories.append(cat)

        required_signal_matches = evaluate_keyword_rules(
            domain_config.get('required_signal_keywords', []),
            title,
            summary,
        )
        min_required_signal_matches = get_config_int(
            domain_config,
            'min_required_signal_matches',
            1 if normalize_keyword_rules(domain_config.get('required_signal_keywords', [])) else 0,
        )
        if min_required_signal_matches and required_signal_matches['match_count'] < min_required_signal_matches:
            continue

        signal_bonus = min(
            required_signal_matches['match_count'] * get_config_float(domain_config, 'required_signal_bonus_per_match', 0.35),
            get_config_float(domain_config, 'max_required_signal_bonus', 0.9),
        )
        score += signal_bonus
        domain_matched_keywords.extend(required_signal_matches['terms'])

        bonus_keyword_matches = evaluate_keyword_rules(
            domain_config.get('bonus_keywords', []),
            title,
            summary,
        )
        bonus_keyword_bonus = min(
            bonus_keyword_matches['match_count'] * get_config_float(domain_config, 'bonus_keyword_bonus_per_match', 0.2),
            get_config_float(domain_config, 'max_bonus_keyword_bonus', 0.5),
        )
        score += bonus_keyword_bonus
        domain_matched_keywords.extend(bonus_keyword_matches['terms'])

        analysis_keyword_matches = evaluate_keyword_rules(
            domain_config.get('analysis_keywords', []),
            title,
            summary,
        )
        domain_matched_keywords.extend(analysis_keyword_matches['terms'])
        domain_matched_keywords = unique_terms_preserve_order(domain_matched_keywords)

        require_text_match = bool(domain_config.get('require_text_match', False))
        min_keyword_matches = get_config_int(domain_config, 'min_keyword_matches', 0)
        min_score = get_config_float(domain_config, 'min_score', 0.0)
        domain_priority = get_config_int(domain_config, 'priority', 0)

        if require_text_match and text_match_count == 0:
            continue
        if min_keyword_matches and text_match_count < min_keyword_matches:
            continue
        if score < min_score:
            continue

        if score > max_score or (score == max_score and domain_priority > best_priority):
            max_score = score
            best_domain = domain_name
            matched_keywords = domain_matched_keywords
            best_priority = domain_priority
            best_match_details = {
                'domain': domain_name,
                'text_match_count': text_match_count,
                'matched_categories': matched_categories,
                'required_signal_matches': required_signal_matches['terms'],
                'required_signal_match_count': required_signal_matches['match_count'],
                'bonus_keyword_matches': bonus_keyword_matches['terms'],
                'bonus_keyword_match_count': bonus_keyword_matches['match_count'],
                'analysis_keyword_matches': analysis_keyword_matches['terms'],
                'analysis_keyword_match_count': analysis_keyword_matches['match_count'],
                'signal_bonus': round(signal_bonus, 2),
                'bonus_keyword_bonus': round(bonus_keyword_bonus, 2),
            }

    return max_score, best_domain, matched_keywords, best_priority, best_match_details


def calculate_recency_score(
    published_date: Optional[datetime],
    *,
    reference_date: Optional[datetime] = None,
    thresholds: Optional[List[Tuple[int, float]]] = None,
) -> float:
    """
    根据发布日期计算新近性评分

    Args:
        published_date: 发布日期

    Returns:
        新近性评分 (0-3)
    """
    if published_date is None:
        return 0

    if thresholds is None:
        thresholds = RECENCY_THRESHOLDS

    if reference_date is None:
        reference_date = datetime.now(published_date.tzinfo) if published_date.tzinfo else datetime.now()
    elif published_date.tzinfo and reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=published_date.tzinfo)
    elif published_date.tzinfo is None and reference_date.tzinfo:
        reference_date = reference_date.replace(tzinfo=None)

    days_diff = (reference_date - published_date).days

    for max_days, score in thresholds:
        if days_diff <= max_days:
            return score
    return RECENCY_DEFAULT


def calculate_quality_score(summary: str) -> float:
    """
    从摘要推断质量评分

    采用更细粒度的指标：强创新词权重高于弱创新词，
    量化结果和对比实验也加分。

    Args:
        summary: 论文摘要

    Returns:
        质量评分 (0-3)
    """
    score = 0.0
    summary_lower = summary.lower()

    strong_innovation = [
        'state-of-the-art', 'sota', 'breakthrough', 'first',
        'surpass', 'outperform', 'pioneering'
    ]
    weak_innovation = [
        'novel', 'propose', 'introduce', 'new approach',
        'new method', 'innovative'
    ]
    method_indicators = [
        'framework', 'architecture', 'algorithm', 'mechanism',
        'pipeline', 'end-to-end'
    ]
    quantitative_indicators = [
        'outperforms', 'improves by', 'achieves', 'accuracy',
        'f1', 'bleu', 'rouge', 'beats', 'surpasses'
    ]
    experiment_indicators = [
        'experiment', 'evaluation', 'benchmark', 'ablation',
        'baseline', 'comparison'
    ]

    strong_count = sum(1 for ind in strong_innovation if ind in summary_lower)
    if strong_count >= 2:
        score += 1.0
    elif strong_count == 1:
        score += 0.7
    else:
        weak_count = sum(1 for ind in weak_innovation if ind in summary_lower)
        if weak_count > 0:
            score += 0.3

    if any(ind in summary_lower for ind in method_indicators):
        score += 0.5

    if any(ind in summary_lower for ind in quantitative_indicators):
        score += 0.8
    elif any(ind in summary_lower for ind in experiment_indicators):
        score += 0.4

    return min(score, SCORE_MAX)


def calculate_recommendation_score(
    relevance_score: float,
    recency_score: float,
    popularity_score: float,
    quality_score: float,
    is_hot_paper: bool = False,
    *,
    priority_bonus: float = 0.0,
    weights_normal: Optional[Dict[str, float]] = None,
    weights_hot: Optional[Dict[str, float]] = None,
) -> float:
    """
    计算综合推荐评分

    权重定义在模块顶部常量 WEIGHTS_NORMAL / WEIGHTS_HOT 中。
    对于高影响力论文（来自 Semantic Scholar），使用 WEIGHTS_HOT 提高热门度权重。

    Args:
        relevance_score: 相关性评分 (0-SCORE_MAX)
        recency_score: 新近性评分 (0-SCORE_MAX)
        popularity_score: 热门度评分 (0-SCORE_MAX)
        quality_score: 质量评分 (0-SCORE_MAX)
        is_hot_paper: 是否是高影响力论文

    Returns:
        综合推荐评分 (0-10)
    """
    scores = {
        'relevance': relevance_score,
        'recency': recency_score,
        'popularity': popularity_score,
        'quality': quality_score,
    }
    # 归一化到 0-10 分
    normalized = {k: (min(max(v, 0.0), SCORE_MAX) / SCORE_MAX) * 10 for k, v in scores.items()}

    weights = weights_hot if is_hot_paper else weights_normal
    if not weights:
        weights = WEIGHTS_HOT if is_hot_paper else WEIGHTS_NORMAL

    final_score = sum(normalized[k] * weights[k] for k in weights) + max(priority_bonus, 0.0)

    return round(min(final_score, 10.0), 2)


ANALYSIS_EVIDENCE_INDICATORS = [
    'benchmark', 'benchmarks', 'baseline', 'baselines', 'evaluation', 'experiment',
    'experiments', 'ablation', 'ablation study', 'compare', 'compared', 'comparison',
]
ANALYSIS_METRIC_INDICATORS = [
    'latency', 'throughput', 'memory', 'bandwidth', 'speedup', 'tokens/s', 'token/s',
    'ms', 'seconds', 'gb', 'gb/s', 'tflops', 'occupancy',
]
ANALYSIS_IMPLEMENTATION_INDICATORS = [
    'kernel', 'runtime', 'compiler', 'cuda', 'triton', 'ptx', 'sass', 'warp',
    'tensor core', 'prefill', 'decode', 'kv cache', 'h100', 'a100', 'b200',
]


def normalized_score_10(value: float) -> float:
    return (min(max(value, 0.0), SCORE_MAX) / SCORE_MAX) * 10


def count_indicator_hits(text: str, indicators: List[str]) -> int:
    lowered = str(text or '').lower()
    return sum(1 for indicator in indicators if indicator in lowered)


def calculate_analysis_candidate_score(
    paper: Dict[str, Any],
    match_details: Dict[str, Any],
) -> Tuple[float, Dict[str, Any]]:
    title = str(paper.get('title') or '').lower()
    summary = str(paper.get('summary') or paper.get('abstract') or '').lower()
    combined_text = f'{title}\n{summary}'

    required_signal_count = int(match_details.get('required_signal_match_count', 0) or 0)
    bonus_keyword_count = int(match_details.get('bonus_keyword_match_count', 0) or 0)
    analysis_keyword_count = int(match_details.get('analysis_keyword_match_count', 0) or 0)
    evidence_hits = count_indicator_hits(combined_text, ANALYSIS_EVIDENCE_INDICATORS)
    metric_hits = count_indicator_hits(combined_text, ANALYSIS_METRIC_INDICATORS)
    implementation_hits = count_indicator_hits(combined_text, ANALYSIS_IMPLEMENTATION_INDICATORS)
    has_quantitative_claim = bool(
        re.search(r'\b\d+(\.\d+)?x\b', combined_text)
        or re.search(r'\b\d+(\.\d+)?%\b', combined_text)
    )
    paper_id = str(paper.get('arxiv_id') or paper.get('arxivId') or paper.get('paper_id') or paper.get('id') or '').strip()
    pdf_url = str(paper.get('pdf_url') or '').strip()
    source_url = str(paper.get('source_url') or paper.get('url') or '').strip()
    has_readable_pdf = (
        looks_like_pdf_url(pdf_url)
        or looks_like_pdf_url(source_url)
        or looks_like_arxiv_id(paper_id)
    )
    has_source_page = bool(source_url)

    signal_strength = min(
        required_signal_count * 0.9 + bonus_keyword_count * 0.45 + analysis_keyword_count * 0.35,
        SCORE_MAX,
    )
    implementation_depth = min(
        required_signal_count * 0.55 + implementation_hits * 0.28,
        SCORE_MAX,
    )
    evidence_strength = min(
        evidence_hits * 0.4 + metric_hits * 0.32 + (0.6 if has_quantitative_claim else 0.0),
        SCORE_MAX,
    )

    recommendation = float(paper.get('scores', {}).get('recommendation', 0) or 0)
    relevance = float(paper.get('scores', {}).get('relevance', 0) or 0)
    final_score = (
        recommendation * 0.30
        + normalized_score_10(relevance) * 0.20
        + normalized_score_10(signal_strength) * 0.20
        + normalized_score_10(implementation_depth) * 0.15
        + normalized_score_10(evidence_strength) * 0.15
        + (0.35 if has_source_page else 0.0)
        + (0.55 if has_readable_pdf else 0.0)
    )
    analysis_signals = unique_terms_preserve_order(
        list(match_details.get('required_signal_matches', []))
        + list(match_details.get('bonus_keyword_matches', []))
        + list(match_details.get('analysis_keyword_matches', []))
    )
    components = {
        'signal_strength': round(normalized_score_10(signal_strength), 2),
        'implementation_depth': round(normalized_score_10(implementation_depth), 2),
        'evidence_strength': round(normalized_score_10(evidence_strength), 2),
        'has_source_page': has_source_page,
        'has_readable_pdf': has_readable_pdf,
        'analysis_signals': analysis_signals[:10],
    }
    return round(min(final_score, 10.0), 2), components


def annotate_analysis_priority(
    papers: List[Dict[str, Any]],
    analysis_top_n: int,
    classic_settings: Optional[Dict[str, Any]] = None,
) -> None:
    allow_classic_full_analysis = bool((classic_settings or {}).get('allow_full_analysis', False))
    eligible = [
        paper for paper in papers
        if allow_classic_full_analysis or str(paper.get('selection_lane') or '').strip().lower() != 'classic'
    ]
    ranked_pool = eligible or papers
    ranked = sorted(
        ranked_pool,
        key=lambda item: (
            float(item.get('analysis_candidate_score', 0) or 0),
            float(item.get('scores', {}).get('recommendation', 0) or 0),
        ),
        reverse=True,
    )
    id_to_rank: Dict[int, int] = {id(paper): index for index, paper in enumerate(ranked, start=1)}
    eligible_ids = {id(candidate) for candidate in ranked_pool}
    for paper in papers:
        rank = id_to_rank.get(id(paper), 0)
        paper['analysis_priority_rank'] = rank
        paper['analysis_eligible'] = id(paper) in eligible_ids
        paper['selected_for_full_analysis'] = bool(rank and rank <= max(0, analysis_top_n))


def filter_and_score_papers(
    papers: List[Dict],
    config: Dict,
    target_date: Optional[datetime] = None,
    is_hot_paper_batch: bool = False
) -> List[Dict]:
    """
    筛选和评分论文

    Args:
        papers: 论文列表
        config: 研究配置
        target_date: 目标日期（用于计算新近性）
        is_hot_paper_batch: 是否是高影响力论文批次

    Returns:
        筛选和评分后的论文列表
    """
    domains = config.get('research_domains', {})
    excluded_keywords = config.get('excluded_keywords', [])
    scoring_settings = get_search_scoring_settings(config)
    recency_thresholds = get_recency_thresholds(config)
    weights_normal = get_recommendation_weights(scoring_settings, 'weights_normal', WEIGHTS_NORMAL)
    weights_hot = get_recommendation_weights(scoring_settings, 'weights_hot', WEIGHTS_HOT)
    influential_citation_full_score = get_config_float(
        scoring_settings,
        'popularity_influential_citation_full_score',
        POPULARITY_INFLUENTIAL_CITATION_FULL_SCORE,
    )
    priority_bonus_per_level = get_config_float(scoring_settings, 'priority_bonus_per_level', 0.15)
    max_priority_bonus = get_config_float(scoring_settings, 'max_priority_bonus', 0.6)

    scored_papers = []

    for paper in papers:
        # 计算相关性
        relevance, matched_domain, matched_keywords, domain_priority, match_details = calculate_relevance_score(
            paper, domains, excluded_keywords, scoring_settings
        )

        # 如果相关性为0，跳过
        if relevance == 0:
            continue

        # 计算新近性
        if 'published_date' in paper:
            published_date = paper.get('published_date')
            if isinstance(published_date, str):
                try:
                    published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                except ValueError:
                    published_date = None
            recency = calculate_recency_score(
                published_date,
                reference_date=target_date,
                thresholds=recency_thresholds,
            )
        else:
            # 对于 Semantic Scholar 的论文，使用 publicationDate
            pub_date_str = paper.get('publicationDate')
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                    recency = calculate_recency_score(
                        pub_date,
                        reference_date=target_date,
                        thresholds=recency_thresholds,
                    )
                except (ValueError, TypeError):
                    recency = 0
            else:
                recency = 0

        # 计算热门度
        if is_hot_paper_batch:
            # 高影响力论文：使用 influentialCitationCount
            inf_cit = paper.get('influentialCitationCount', 0) or 0
            if inf_cit > 0:
                popularity = min(
                    inf_cit / (influential_citation_full_score / SCORE_MAX),
                    SCORE_MAX,
                )
            else:
                # Semantic Scholar 不可用时回退到较保守的摘要启发式，避免 hot window 直接失真为 0。
                summary = paper.get('summary', '') if 'summary' in paper else paper.get('abstract', '')
                popularity = min(calculate_quality_score(summary) + 0.4, SCORE_MAX)
        else:
            # 普通论文：基于摘要推断
            summary = paper.get('summary', '') if 'summary' in paper else paper.get('abstract', '')
            popularity = calculate_quality_score(summary)  # 临时使用质量评分作为热门度

        # 计算质量
        summary = paper.get('summary', '') if 'summary' in paper else paper.get('abstract', '')
        quality = calculate_quality_score(summary)
        relevance = min(relevance, SCORE_MAX)
        recency = min(recency, SCORE_MAX)
        popularity = min(popularity, SCORE_MAX)
        quality = min(quality, SCORE_MAX)
        priority_bonus = min(max(domain_priority - 1, 0) * priority_bonus_per_level, max_priority_bonus)

        # 计算综合推荐评分
        recommendation_score = calculate_recommendation_score(
            relevance,
            recency,
            popularity,
            quality,
            is_hot_paper_batch,
            priority_bonus=priority_bonus,
            weights_normal=weights_normal,
            weights_hot=weights_hot,
        )

        # 添加评分信息
        paper['scores'] = {
            'relevance': round(relevance, 2),
            'recency': round(recency, 2),
            'popularity': round(popularity, 2),
            'quality': round(quality, 2),
            'recommendation': recommendation_score
        }
        paper['matched_domain'] = matched_domain
        paper['matched_keywords'] = matched_keywords
        paper['matched_domain_priority'] = domain_priority
        paper['domain_preference_bonus'] = round(priority_bonus, 2)
        paper['is_hot_paper'] = is_hot_paper_batch
        paper['match_details'] = match_details
        analysis_candidate_score, analysis_components = calculate_analysis_candidate_score(paper, match_details)
        paper['analysis_candidate_score'] = analysis_candidate_score
        paper['analysis_signals'] = analysis_components.get('analysis_signals', [])
        paper['analysis_components'] = {
            key: value
            for key, value in analysis_components.items()
            if key != 'analysis_signals'
        }

        scored_papers.append(paper)

    # 按推荐评分排序
    scored_papers.sort(key=lambda x: x['scores']['recommendation'], reverse=True)

    return scored_papers


def main():
    """主函数"""
    import argparse

    repo_root = Path(__file__).resolve().parents[2]
    default_config = os.environ.get('PAPER_SITE_CONFIG', '')
    if not default_config:
        config_yaml = repo_root / 'config.yaml'
        default_config = str(config_yaml if config_yaml.exists() else repo_root / 'config.example.yaml')

    parser = argparse.ArgumentParser(description='Search and filter arXiv papers with Semantic Scholar integration')
    parser.add_argument('--config', type=str,
                        default=default_config or None,
                        help='Path to research interests config file (or set PAPER_SITE_CONFIG env var)')
    parser.add_argument('--output', type=str, default='arxiv_filtered.json',
                        help='Output JSON file path')
    parser.add_argument('--max-results', type=int, default=None,
                        help='Maximum number of results to fetch from arXiv')
    parser.add_argument('--top-n', type=int, default=None,
                        help='Maximum number of top papers to return')
    parser.add_argument('--target-date', type=str, default=None,
                        help='Target date (YYYY-MM-DD) for filtering')
    parser.add_argument('--categories', type=str,
                        default=None,
                        help='Comma-separated list of arXiv categories')
    parser.add_argument('--skip-hot-papers', action='store_true',
                        help='Skip searching hot papers from Semantic Scholar')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    if not args.config:
        logger.error("未指定配置文件路径。请通过 --config 参数或 PAPER_SITE_CONFIG 环境变量设置。")
        return 1

    logger.info("Loading config from: %s", args.config)
    config = load_research_config(args.config)
    search_settings = get_search_settings(config)
    lane_settings = get_lane_settings(config)
    classic_settings = get_classic_settings(config)
    venue_settings = get_venue_source_settings(config)
    history_settings = get_history_settings(config)
    analysis_settings = config.get('analysis', {}) if isinstance(config, dict) else {}

    max_results = args.max_results if args.max_results is not None else get_config_int(search_settings, 'max_results', 200)
    top_n = args.top_n if args.top_n is not None else get_config_int(search_settings, 'top_n', 10)
    analysis_top_n = get_config_int(analysis_settings, 'top_n', 1)

    # 解析目标日期
    target_date = None
    if args.target_date:
        try:
            target_date = datetime.strptime(args.target_date, '%Y-%m-%d')
            logger.info("Target date: %s", args.target_date)
        except ValueError:
            logger.error("Invalid target date format: %s", args.target_date)
            return 1
    else:
        target_date = datetime.now()
        logger.info("Using current date: %s", target_date.strftime('%Y-%m-%d'))

    recent_window_days = get_config_int(search_settings, 'recent_window_days', 30)
    hot_window_days = get_config_int(search_settings, 'hot_window_days', 365)
    hot_exclude_recent_days = get_config_int(search_settings, 'hot_exclude_recent_days', recent_window_days)
    hot_top_k_per_category = get_config_int(search_settings, 'hot_top_k_per_category', 5)
    hot_fallback_max_results = get_config_int(search_settings, 'hot_fallback_max_results', max(max_results // 2, 80))

    window_30d_start, window_30d_end, window_1y_start, window_1y_end = calculate_date_windows(
        target_date,
        recent_window_days=recent_window_days,
        hot_window_days=hot_window_days,
        hot_exclude_recent_days=hot_exclude_recent_days,
    )
    logger.info("Date windows:")
    logger.info("  Recent window (%d days): %s to %s", recent_window_days, window_30d_start.date(), window_30d_end.date())
    logger.info(
        "  Hot window (%d days, excluding last %d days): %s to %s",
        hot_window_days,
        hot_exclude_recent_days,
        window_1y_start.date(),
        window_1y_end.date(),
    )

    # 解析分类
    if args.categories:
        categories = [part.strip() for part in args.categories.split(',') if part.strip()]
    else:
        config_categories = search_settings.get('categories', [])
        if isinstance(config_categories, list):
            categories = [str(part).strip() for part in config_categories if str(part).strip()]
        else:
            categories = []
    if not categories:
        categories = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.MM', 'cs.MA', 'cs.RO']

    all_scored_papers = []
    recent_papers = []
    hot_papers = []
    venue_papers = []

    # ========== 第一步：搜索最近30天的论文（arXiv）==========
    logger.info("=" * 70)
    logger.info("Step 1: Searching recent papers (last 30 days) from arXiv")
    logger.info("=" * 70)

    recent_papers = search_arxiv_by_date_range(
        categories=categories,
        start_date=window_30d_start,
        end_date=window_30d_end,
        max_results=max_results
    )

    if recent_papers:
        scored_recent = filter_and_score_papers(
            papers=recent_papers,
            config=config,
            target_date=target_date,
            is_hot_paper_batch=False
        )
        logger.info("Scored %d recent papers", len(scored_recent))
        all_scored_papers.extend(scored_recent)
    else:
        logger.warning("No recent papers found")

    # ========== 第 1.5 步：搜索 systems venue 论文（DBLP）==========
    logger.info("=" * 70)
    logger.info("Step 1.5: Searching systems venue papers from configured venue index")
    logger.info("=" * 70)

    venue_papers = search_venue_papers(
        config=config,
        venue_settings=venue_settings,
        reference_date=target_date,
    )
    if venue_papers:
        scored_venue = filter_and_score_papers(
            papers=venue_papers,
            config=config,
            target_date=target_date,
            is_hot_paper_batch=False,
        )
        logger.info("Scored %d venue papers", len(scored_venue))
        all_scored_papers.extend(scored_venue)
    else:
        logger.info("No venue papers found from configured venue index")

    # ========== 第二步：搜索过去一年的高影响力论文（Semantic Scholar）==========
    if not args.skip_hot_papers:
        logger.info("=" * 70)
        logger.info("Step 2: Searching hot papers (past year) from Semantic Scholar")
        logger.info("=" * 70)

        hot_papers = search_hot_papers_from_categories(
            categories=categories,
            start_date=window_1y_start,
            end_date=window_1y_end,
            top_k_per_category=hot_top_k_per_category
        )

        if hot_papers:
            scored_hot = filter_and_score_papers(
                papers=hot_papers,
                config=config,
                target_date=target_date,
                is_hot_paper_batch=True
            )
            logger.info("Scored %d hot papers", len(scored_hot))
            all_scored_papers.extend(scored_hot)
        else:
            logger.warning("No hot papers found from Semantic Scholar, falling back to arXiv hot window")
            hot_papers = search_hot_papers_from_arxiv_fallback(
                categories=categories,
                start_date=window_1y_start,
                end_date=window_1y_end,
                max_results=hot_fallback_max_results,
            )
            if hot_papers:
                scored_hot = filter_and_score_papers(
                    papers=hot_papers,
                    config=config,
                    target_date=target_date,
                    is_hot_paper_batch=True,
                )
                logger.info("Scored %d fallback hot papers", len(scored_hot))
                all_scored_papers.extend(scored_hot)
            else:
                logger.warning("No hot papers found from fallback arXiv search either")
    else:
        logger.info("Skipping hot paper search (disabled by user)")

    # ========== 第三步：合并结果并排序 ==========
    logger.info("=" * 70)
    logger.info("Step 3: Merging and ranking results")
    logger.info("=" * 70)

    # 按推荐评分排序
    all_scored_papers.sort(key=lambda x: x['scores']['recommendation'], reverse=True)

    # 去重（基于 arXiv ID）
    seen_ids = set()
    unique_papers = []
    for p in all_scored_papers:
        arxiv_id = p.get('arxiv_id') or p.get('arxivId')
        if arxiv_id:
            if arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                unique_papers.append(p)
        else:
            # 没有 arXiv ID 的，使用标题去重
            title = p.get('title', '')
            if title not in seen_ids:
                seen_ids.add(title)
                unique_papers.append(p)

    logger.info("Total unique papers after deduplication: %d", len(unique_papers))

    if len(unique_papers) == 0:
        logger.warning("No papers matched the criteria!")
        return 1

    repo_history_root = repo_root
    index_entries = load_paper_index_entries(resolve_repo_path(repo_history_root, history_settings['index_path']))
    classic_candidates = [
        paper for item in load_classic_backlog(resolve_repo_path(repo_history_root, history_settings['classic_backlog_path']))
        if (paper := backlog_paper_to_candidate(item))
    ]
    selection_candidates = [*unique_papers, *classic_candidates]
    top_papers, lane_counts = select_papers_by_lanes(
        selection_candidates,
        top_n=max(0, top_n),
        lane_settings=lane_settings,
        classic_settings=classic_settings,
        history_settings=history_settings,
        index_entries=index_entries,
        reference_date=target_date,
    )
    hydrate_papers_with_venue_metadata(top_papers)
    refresh_selected_paper_scores(top_papers, config, target_date=target_date)
    hydrate_papers_with_semantic_scholar_metadata(top_papers)
    hydrate_papers_with_google_scholar_metadata(top_papers, config)
    annotate_analysis_priority(top_papers, analysis_top_n, classic_settings)

    # 准备输出
    output = {
        'target_date': args.target_date or target_date.strftime('%Y-%m-%d'),
        'date_windows': {
            'recent_window': {
                'days': recent_window_days,
                'start': window_30d_start.strftime('%Y-%m-%d'),
                'end': window_30d_end.strftime('%Y-%m-%d')
            },
            'hot_window': {
                'days': hot_window_days,
                'exclude_recent_days': hot_exclude_recent_days,
                'start': window_1y_start.strftime('%Y-%m-%d'),
                'end': window_1y_end.strftime('%Y-%m-%d')
            }
        },
        'total_found': len(recent_papers) + len(hot_papers) + len(venue_papers),
        'total_venue': len(venue_papers),
        'total_filtered': len(all_scored_papers),
        'total_recent': len(recent_papers),
        'total_hot': len(hot_papers),
        'total_unique': len(unique_papers),
        'total_classic_backlog_candidates': len(classic_candidates),
        'selection': {
            'max_recommendations': top_n,
            'analysis_top_n': analysis_top_n,
            'selected_count': len(top_papers),
            'lane_counts': lane_counts,
            'classic_policy': {
                'enabled': classic_settings['enabled'],
                'cadence_days': classic_settings['cadence_days'],
                'anchor_date': classic_settings['anchor_date'],
                'allow_full_analysis': classic_settings['allow_full_analysis'],
                'slot_active_today': bool(lane_counts.get('classic_slot_active')),
            },
        },
        'top_papers': top_papers
    }

    # 保存结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    logger.info("Results saved to: %s", args.output)
    logger.info("Top %d papers:", len(top_papers))
    for i, p in enumerate(top_papers, 1):
        hot_marker = " [HOT]" if p.get('is_hot_paper') else ""
        logger.info("  %d. %s... (Score: %s)%s", i, p.get('title', 'N/A')[:60], p['scores']['recommendation'], hot_marker)
    deep_dive = next((paper for paper in top_papers if paper.get('selected_for_full_analysis')), None)
    if deep_dive:
        logger.info(
            "Deep-dive candidate: %s (analysis score: %s)",
            deep_dive.get('title', 'N/A')[:80],
            deep_dive.get('analysis_candidate_score', 'N/A'),
        )

    # 同时输出到 stdout
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))

    return 0


if __name__ == '__main__':
    sys.exit(main())
