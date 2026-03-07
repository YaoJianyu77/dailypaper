#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update content/meta/graph_data.json for the static paper site."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from content_store import get_meta_root, get_repo_root, read_json, write_json

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Update graph metadata for a paper')
    parser.add_argument('--paper-id', required=True, help='Paper ID')
    parser.add_argument('--title', required=True, help='Paper title')
    parser.add_argument('--domain', required=True, help='Paper domain')
    parser.add_argument('--score', type=float, default=0.0, help='Quality score')
    parser.add_argument('--related', nargs='*', default=[], help='Related paper IDs')
    parser.add_argument(
        '--related-spec',
        action='append',
        default=[],
        help='Structured related edge as paper_id|edge_type|weight',
    )
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    graph_path = get_meta_root(repo_root) / 'graph_data.json'
    date = datetime.now().strftime('%Y-%m-%d')

    graph = read_json(graph_path, {
        'nodes': [],
        'edges': [],
        'last_updated': date,
    })

    node = {
        'id': args.paper_id,
        'title': args.title,
        'domain': args.domain,
        'quality_score': args.score,
        'updated': date,
    }

    existing_nodes = {item['id']: index for index, item in enumerate(graph['nodes'])}
    if args.paper_id in existing_nodes:
        graph['nodes'][existing_nodes[args.paper_id]].update(node)
    else:
        graph['nodes'].append(node)

    existing_edges = {(edge['source'], edge['target']) for edge in graph['edges']}
    for related in args.related:
        if related and (args.paper_id, related) not in existing_edges:
            graph['edges'].append({
                'source': args.paper_id,
                'target': related,
                'type': 'related',
                'weight': 0.7,
            })
            existing_edges.add((args.paper_id, related))

    for raw_spec in args.related_spec:
        if not raw_spec:
            continue
        parts = raw_spec.split('|')
        if len(parts) != 3:
            continue
        target_id, edge_type, raw_weight = [part.strip() for part in parts]
        if not target_id or (args.paper_id, target_id) in existing_edges:
            continue
        try:
            weight = float(raw_weight)
        except ValueError:
            weight = 0.7
        graph['edges'].append({
            'source': args.paper_id,
            'target': target_id,
            'type': edge_type or 'related',
            'weight': max(0.1, min(1.0, weight)),
        })
        existing_edges.add((args.paper_id, target_id))

    graph['last_updated'] = date
    write_json(graph_path, graph)
    logger.info('Graph updated at %s', graph_path)
    print(graph_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
