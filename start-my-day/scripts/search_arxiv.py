#!/usr/bin/env python3
"""
arXiv + Semantic Scholar 混合架构论文搜索脚本
用于 start-my-day skill，搜索最近一个月和最近一年的极火、极热门、极优质论文
"""

import xml.etree.ElementTree as ET
import json
import re
import os
import sys
import time
import logging
from datetime import datetime, timedelta
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
SEMANTIC_SCHOLAR_FIELDS = "title,abstract,publicationDate,citationCount,influentialCitationCount,url,authors,externalIds"
SEMANTIC_SCHOLAR_QUERY_LIMIT = 60

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

    matched_fields: List[str] = []
    fields = rule.get('fields', [])
    if 'title' in fields and term in title:
        matched_fields.append('title')
    if 'summary' in fields and term in summary:
        matched_fields.append('summary')
    return matched_fields


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
                match = re.search(r'arXiv:(\d+\.\d+)', paper['id'])
                if match:
                    paper['arxiv_id'] = match.group(1)
                else:
                    match = re.search(r'/(\d+\.\d+)$', paper['id'])
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
            for author in entry.findall('atom:author', ARXIV_NS):
                name_elem = author.find('atom:name', ARXIV_NS)
                if name_elem is not None:
                    authors.append(name_elem.text)
            paper['authors'] = authors

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
) -> Tuple[float, Optional[str], List[str], int]:
    """
    计算论文与研究兴趣的相关性评分

    Args:
        paper: 论文信息
        domains: 研究领域配置
        excluded_keywords: 排除关键词

    Returns:
        (相关性评分, 匹配的领域, 匹配的关键词列表)
    """
    title = paper.get('title', '').lower()
    summary = paper.get('summary', '').lower() if 'summary' in paper else paper.get('abstract', '').lower()
    categories = set(paper.get('categories', []))

    # 检查排除关键词
    for rule in normalize_keyword_rules(excluded_keywords):
        if keyword_rule_matches(rule, title, summary):
            return 0, None, [], 0

    max_score = 0
    best_domain = None
    matched_keywords = []
    best_priority = 0

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
        for cat in domain_categories:
            if cat in categories:
                score += category_match_boost
                domain_matched_keywords.append(cat)

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

    return max_score, best_domain, matched_keywords, best_priority


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
        relevance, matched_domain, matched_keywords, domain_priority = calculate_relevance_score(
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
    parser.add_argument('--max-results', type=int, default=200,
                        help='Maximum number of results to fetch from arXiv')
    parser.add_argument('--top-n', type=int, default=10,
                        help='Number of top papers to return')
    parser.add_argument('--target-date', type=str, default=None,
                        help='Target date (YYYY-MM-DD) for filtering')
    parser.add_argument('--categories', type=str,
                        default='cs.AI,cs.LG,cs.CL,cs.CV,cs.MM,cs.MA,cs.RO',
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
    hot_fallback_max_results = get_config_int(search_settings, 'hot_fallback_max_results', max(args.max_results // 2, 80))

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
    categories = args.categories.split(',')

    all_scored_papers = []
    recent_papers = []
    hot_papers = []

    # ========== 第一步：搜索最近30天的论文（arXiv）==========
    logger.info("=" * 70)
    logger.info("Step 1: Searching recent papers (last 30 days) from arXiv")
    logger.info("=" * 70)

    recent_papers = search_arxiv_by_date_range(
        categories=categories,
        start_date=window_30d_start,
        end_date=window_30d_end,
        max_results=args.max_results
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

    # 取前 N 篇
    top_papers = unique_papers[:args.top_n]

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
        'total_recent': len(recent_papers),
        'total_hot': len(hot_papers),
        'total_unique': len(unique_papers),
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

    # 同时输出到 stdout
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))

    return 0


if __name__ == '__main__':
    sys.exit(main())
