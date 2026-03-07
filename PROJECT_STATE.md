# Project State

## Identity
- Local repo path: `/home/y/dailypaper`
- GitHub repo: `YaoJianyu77/dailypaper`
- Site URL: `https://YaoJianyu77.github.io/dailypaper/`

## Current Primary Workflow
The primary workflow is local generation on your own machine.

Flow:
1. Run `scripts/run_local_daily.py` locally.
2. The script pulls `main` from `dailypaper`.
3. It searches papers with `start-my-day/scripts/search_arxiv.py`.
4. It enriches the ranked papers with local Codex CLI using `scripts/codex_enrich.py`.
5. It publishes markdown into `content/` and builds `dist/`.
6. It commits and pushes updated `content/` and `state/` to GitHub.
7. GitHub Pages updates from the push.

## Main Commands
Run the local pipeline once:

```bash
cd /home/y/dailypaper
uv run --with-requirements requirements.txt python scripts/run_local_daily.py
```

Install the local 7am cron job:

```bash
cd /home/y/dailypaper
./scripts/install_local_cron.sh
```

Watch cron logs:

```bash
tail -f /home/y/dailypaper/state/logs/local_daily.log
```

## Current Automation Setup
- Primary: local `uv` + local `codex`
- GitHub Pages deployment workflow: `.github/workflows/pages.yml`
- GitHub-side generation workflow: `.github/workflows/daily.yml`
  - kept only as a manual fallback
  - not the primary path anymore

## Important Repo Facts
- The repo was renamed locally from `evil-read-arxiv` to `dailypaper`.
- The project title was updated to `DailyPaper`.
- The local remote used by the workflow is `dailypaper`.
- Local SSH push to `git@github.com:YaoJianyu77/dailypaper.git` is configured.
- The local pipeline was repaired after a `codex_enrich.py` prompt-builder signature mismatch.
- Semantic Scholar rate limits are now handled gracefully.
  - If `SEMANTIC_SCHOLAR_API_KEY` is missing and S2 returns `429`, the run continues with arXiv results.

## Optional Secret
Optional GitHub secret for better Semantic Scholar stability:
- `SEMANTIC_SCHOLAR_API_KEY`

## Recent Relevant Commits
- `9a6f87c` `chore: update local daily paper content`
- `5c87822` `fix: align codex enrichment prompt builder`
- `6294489` `chore: rename project to dailypaper`
- `c343f5b` `docs: restore local codex as primary workflow`
- `5d168be` `fix: degrade gracefully on Semantic Scholar rate limits`

## Resume Instructions For A New Agent
Tell the agent to read this file first, then continue from the current repo state.

Suggested opener for a new conversation:

```text
Project path is /home/y/dailypaper. Read PROJECT_STATE.md first. The primary workflow is local uv + local codex via scripts/run_local_daily.py, then push to GitHub and let Pages display the result. Continue with: <your next task>
```

## Skill Usage Status
- The current production workflow does not use the repository's legacy `skill.md` files.
- The old `skill.md` files are legacy documentation from the original repo structure, not the active automation path.
- The active automation path is code-driven through Python scripts.
- In this chat session, no repository `SKILL.md` file was used.
- The only higher-level instructions currently in effect came from `AGENTS.md` and system/developer instructions.
