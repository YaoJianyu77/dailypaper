#!/usr/bin/env python3
"""Run the local daily-paper pipeline and push results to GitHub."""

from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from content_store import get_repo_root

logger = logging.getLogger(__name__)


def load_local_env(repo_root: Path) -> None:
    for env_name in ('.env.local', '.env'):
        env_path = repo_root / env_name
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[len('export '):].strip()
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value


def load_config(repo_root: Path) -> tuple[Path, Dict[str, Any]]:
    config_path = repo_root / 'config.yaml'
    if not config_path.exists():
        config_path = repo_root / 'config.example.yaml'
    config = yaml.safe_load(config_path.read_text(encoding='utf-8')) or {}
    return config_path, config

def run(cmd: List[str], *, cwd: Path, env: Dict[str, str] | None = None) -> None:
    logger.info('Running: %s', ' '.join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True, env=env)


def capture(cmd: List[str], *, cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=True)
    return result.stdout.strip()


def is_git_clean(repo_root: Path) -> bool:
    return not capture(['git', 'status', '--porcelain'], cwd=repo_root)


def pick_remote(repo_root: Path, preferred: str | None) -> str:
    remotes = [line.strip() for line in capture(['git', 'remote'], cwd=repo_root).splitlines() if line.strip()]
    if preferred:
        if preferred not in remotes:
            raise SystemExit(f'Remote {preferred!r} not found. Available remotes: {", ".join(remotes) or "(none)"}')
        return preferred

    try:
        upstream = capture(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}'], cwd=repo_root)
        upstream_remote = upstream.split('/', 1)[0]
        if upstream_remote in remotes:
            return upstream_remote
    except subprocess.CalledProcessError:
        pass

    for candidate in ['origin', 'dailypaper']:
        if candidate in remotes:
            return candidate

    if remotes:
        return remotes[0]

    raise SystemExit('No git remote configured. Add a GitHub remote before running the local pipeline.')


def infer_site_base_url(repo_root: Path, remote_name: str, config: Dict[str, Any]) -> str:
    site_settings = config.get('site', {}) if isinstance(config, dict) else {}
    configured = str(site_settings.get('base_url') or '').strip()
    if configured:
        return configured

    try:
        remote_url = capture(['git', 'remote', 'get-url', remote_name], cwd=repo_root)
    except subprocess.CalledProcessError:
        return ''

    match = re.search(r'[:/]([^/:]+)/([^/]+?)(?:\.git)?$', remote_url)
    if not match:
        return ''

    owner, repo_name = match.groups()
    if repo_name == f'{owner}.github.io':
        return ''
    return f'/{repo_name}'


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(description='Run local daily paper generation and push results')
    parser.add_argument('--repo-root', default=None, help='Repository root path')
    parser.add_argument('--target-date', default=None, help='Override report date (YYYY-MM-DD)')
    parser.add_argument('--skip-push', action='store_true', help='Generate locally without pushing')
    parser.add_argument('--skip-build', action='store_true', help='Skip local static site build')
    parser.add_argument('--enricher', choices=['codex', 'openai', 'none'], default='codex', help='Enrichment backend to use locally')
    parser.add_argument('--remote', default=None, help='Git remote to pull from and push to (auto-detected by default)')
    args = parser.parse_args()

    repo_root = get_repo_root(args.repo_root, __file__)
    load_local_env(repo_root)
    config_path, config = load_config(repo_root)
    search_cfg = config.get('search', {}) if isinstance(config, dict) else {}
    remote_name = pick_remote(repo_root, args.remote)

    if not is_git_clean(repo_root):
        logger.error('Repository is not clean. Commit or stash local changes before running the scheduled job.')
        return 1

    run(['git', 'pull', '--rebase', remote_name, 'main'], cwd=repo_root)

    search_cmd = [
        sys.executable,
        str(repo_root / 'start-my-day' / 'scripts' / 'search_arxiv.py'),
        '--config', str(config_path),
        '--output', 'state/arxiv_filtered.json',
        '--max-results', str(search_cfg.get('max_results', 200)),
        '--top-n', str(search_cfg.get('top_n', 10)),
        '--categories', ','.join(search_cfg.get('categories', ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.MM', 'cs.MA', 'cs.RO'])),
    ]
    if args.target_date:
        search_cmd.extend(['--target-date', args.target_date])
    if search_cfg.get('skip_hot_papers', False):
        search_cmd.append('--skip-hot-papers')
    run(search_cmd, cwd=repo_root)

    enriched_file = 'state/arxiv_enriched.json'
    if args.enricher == 'codex':
        run([
            sys.executable,
            str(repo_root / 'scripts' / 'codex_enrich.py'),
            '--config', str(config_path),
            '--input', 'state/arxiv_filtered.json',
            '--output', enriched_file,
            '--strict',
        ], cwd=repo_root, env={**os.environ, 'PATH': f"{Path.home() / '.npm-global' / 'bin'}:{os.environ.get('PATH', '')}"})
    elif args.enricher == 'openai':
        run([
            sys.executable,
            str(repo_root / 'scripts' / 'ai_enrich.py'),
            '--config', str(config_path),
            '--input', 'state/arxiv_filtered.json',
            '--output', enriched_file,
            '--strict',
        ], cwd=repo_root)
    else:
        enriched_file = 'state/arxiv_filtered.json'

    run([
        sys.executable,
        str(repo_root / 'scripts' / 'publish_daily.py'),
        '--config', str(config_path),
        '--input', enriched_file,
    ], cwd=repo_root)

    if not args.skip_build:
        env = dict(os.environ)
        if 'SITE_BASE_URL' not in env:
            env['SITE_BASE_URL'] = infer_site_base_url(repo_root, remote_name, config)
        run([
            sys.executable,
            str(repo_root / 'scripts' / 'build_site.py'),
            '--output-dir', 'dist',
        ], cwd=repo_root, env=env)

    subprocess.run(['git', 'add', 'content', 'state'], cwd=str(repo_root), check=True)
    diff = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=str(repo_root))
    if diff.returncode == 0:
        logger.info('No content changes detected. Nothing to commit.')
        return 0

    commit_msg = 'chore: update local daily paper content'
    if args.target_date:
        commit_msg = f'chore: update daily paper content for {args.target_date}'
    run(['git', 'commit', '-m', commit_msg], cwd=repo_root)

    if not args.skip_push:
        run(['git', 'push', remote_name, 'main'], cwd=repo_root)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
