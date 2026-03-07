# evil-read-arxiv

A repository-backed daily paper pipeline with two operating modes:

- GitHub-hosted generation with GitHub Models and GitHub Actions
- local `uv` + Codex CLI generation as a fallback

The repository is now structured as a content store plus a static website:

- `start-my-day/scripts/search_arxiv.py` fetches and ranks papers from arXiv and Semantic Scholar.
- `scripts/publish_daily.py` converts search output into versioned markdown under `content/`.
- `scripts/build_site.py` compiles that markdown into a static site under `dist/`.
- `.github/workflows/daily.yml` generates fresh content on a schedule or on manual dispatch.
- `.github/workflows/pages.yml` deploys GitHub Pages whenever `main` changes.

## What Changed

This project no longer depends on Obsidian or an Obsidian Vault.

Content now lives directly in the repository:

```text
content/
  daily/
    2026-03-07.md
  papers/
    2602-12345-some-paper-title/
      index.md
      images/
        index.md
        fig1.png
  meta/
    latest.json
    daily-index.json
    graph_data.json
state/
  arxiv_filtered.json
  existing_notes_index.json
dist/
  ... generated static site, not committed
```

## Core Commands

Install dependencies:

```bash
uv --version
```

Search papers:

```bash
uv run --with-requirements requirements.txt python start-my-day/scripts/search_arxiv.py \
  --config config.example.yaml \
  --output state/arxiv_filtered.json
```

Publish the daily report into `content/`:

```bash
uv run --with-requirements requirements.txt python scripts/publish_daily.py --input state/arxiv_filtered.json
```

Build the static site:

```bash
uv run --with-requirements requirements.txt python scripts/build_site.py --output-dir dist
```

Serve it locally:

```bash
uv run --with-requirements requirements.txt python -m http.server 8000 -d dist
```

Then open `http://localhost:8000`.

## GitHub Automation Model

The GitHub-hosted path is now the default:

1. `.github/workflows/daily.yml` runs every day at New York `07:00`.
2. The workflow searches papers, calls GitHub Models for Chinese editorial enrichment, and commits fresh `content/` and `state/`.
3. `.github/workflows/pages.yml` sees the push to `main` and redeploys GitHub Pages.

The schedule uses two UTC cron entries plus a timezone guard so it stays aligned to New York `07:00` across daylight saving changes.

Recommended repository setup:

- keep GitHub Pages enabled with `GitHub Actions` as the source
- leave `.github/workflows/pages.yml` enabled
- leave `.github/workflows/daily.yml` enabled for daily generation
- optionally set repository variable `AI_MODEL` if you want to force a specific GitHub Models model id

The generation workflow does this:

1. Run the paper search.
2. Enrich the top papers with GitHub Models.
3. Generate or update daily markdown and paper pages.
4. Commit `content/` and `state/` changes back into the repository.

That gives you:

- a homepage that shows the latest daily report
- an archive page for older reports
- one page per paper
- git history for every generated artifact
- a site you can browse on GitHub Pages or locally after `git clone`

## Local Fallback

If you still want agent generation on your own machine, the local flow is still supported:

1. `scripts/run_local_daily.py` pulls `main`, searches papers, runs local Codex CLI enrichment, publishes markdown, builds the site, commits `content/` and `state/`, and pushes back to GitHub.
2. `scripts/install_local_cron.sh` installs a local cron job for `07:00` every day.
3. `.github/workflows/pages.yml` sees the new push on `main` and redeploys GitHub Pages.

Prerequisites on the machine that will run at 7am:

- `codex` must already be installed and logged in
- `git push` must already work non-interactively, preferably with SSH keys or a credential helper
- the machine must be powered on at the scheduled time

Install the local cron job:

```bash
./scripts/install_local_cron.sh
```

Run the full local pipeline immediately:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py
```

Useful variants:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --target-date 2026-03-07
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --skip-push
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --enricher openai
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --enricher none
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --remote origin
```

By default the script auto-detects the active Git remote. Use `--remote` only if your clone does not track the correct remote.

Cron logs are written to:

- `state/logs/local_daily.log`

## Content and Asset Management

Recommended policy:

- Keep markdown, metadata, and compressed web-ready images in the repository.
- Do not store every raw PDF or very large source asset in git.
- For each paper, keep only the few images you actually want to browse on the website.
- Use `extract-paper-images/scripts/extract_images.py` to populate `content/papers/<slug>/images/`.

Example:

```bash
python extract-paper-images/scripts/extract_images.py \
  2602.12345 \
  content/papers/2602-12345-some-paper-title/images \
  content/papers/2602-12345-some-paper-title/images/index.md
```

## Configuration

Copy the example config if you want repository-local settings:

```bash
cp config.example.yaml config.yaml
```

The search script reads:

- `config.yaml` if it exists
- otherwise `config.example.yaml`
- or a path passed explicitly with `--config`

## GitHub Pages

Enable GitHub Pages for the repository and let GitHub Actions deploy it.

The included workflows live at:

- `.github/workflows/daily.yml`
- `.github/workflows/pages.yml`

Recommended setup:

- `.github/workflows/daily.yml` should stay enabled for the 7am generation job
- `.github/workflows/pages.yml` should stay enabled for deployment on push to `main`
- local `scripts/run_local_daily.py` is optional fallback, not the primary path

For a project site such as `https://YaoJianyu77.github.io/dailypaper/`, the build now supports a subpath base URL.

- In GitHub Actions, `SITE_BASE_URL` is derived automatically from the repository name.
- For the `dailypaper` repository, that becomes `/dailypaper`.
- For a user site such as `username.github.io`, the base URL stays empty.

## Netlify And Cloudflare Pages

The static output is also compatible with Netlify and Cloudflare Pages.

Included platform config:

- [netlify.toml](/home/y/evil-read-arxiv/netlify.toml)
- [wrangler.toml](/home/y/evil-read-arxiv/wrangler.toml)

Recommended settings:

- Netlify
  - Build command: `python3 scripts/build_site.py --output-dir dist`
  - Publish directory: `dist`
  - `SITE_BASE_URL=""`
- Cloudflare Pages
  - Build command: `python3 scripts/build_site.py --output-dir dist`
  - Output directory: `dist`
  - `SITE_BASE_URL=""`

If you ever deploy behind a subpath on another platform, set:

```bash
SITE_BASE_URL="/your-subpath"
```

## AI Enrichment

The pipeline now includes an optional `search -> enrich -> publish` layer.

New script:

- `scripts/ai_enrich.py`

Input:

- `state/arxiv_filtered.json`

Output:

- `state/arxiv_enriched.json`

By default the script calls GitHub Models and prefers the strongest available OpenAI model from the repository's visible model catalog. The default preference order is:

- `openai/gpt-5.4`
- `openai/gpt-5`
- `openai/gpt-4.1`
- `openai/gpt-4o`

You can force a specific model with the repository variable `AI_MODEL` or the config key `ai.model`.

The enrichment layer adds:

- `daily_brief.overview_zh`
- `daily_brief.top_themes`
- `daily_brief.reading_strategy`
- per-paper AI fields such as:
  - `one_liner_zh`
  - `summary_zh`
  - `core_contributions`
  - `why_read`
  - `risks`
  - `recommended_for`
  - `keywords`
  - `reading_priority`

If GitHub Models is unavailable or disabled, the script degrades safely and passes the ranked papers through without failing the workflow.

### GitHub Variables

For the GitHub-hosted path, the default config is:

```yaml
ai:
  provider: "github_models"
  model: "auto"
```

Optional repository variables for GitHub Actions:

- `AI_MODEL`
- `GITHUB_MODELS_PREFERRED_MODELS`
- `GITHUB_MODELS_API_BASE`

You can still run OpenAI directly if you want:

```bash
export OPENAI_API_KEY=\"your-key\"
uv run --with-requirements requirements.txt python scripts/ai_enrich.py \
  --config config.yaml \
  --input state/arxiv_filtered.json \
  --output state/arxiv_enriched.json
uv run --with-requirements requirements.txt python scripts/publish_daily.py --input state/arxiv_enriched.json
```

## Notes on Legacy Files

The repository still contains `skill.md` files and some original helper scripts from the Claude skill version. They are now legacy references. The active path is the repository content workflow described above.

## Minimal Local Flow

```bash
uv run --with-requirements requirements.txt python start-my-day/scripts/search_arxiv.py --config config.example.yaml --output state/arxiv_filtered.json
uv run --with-requirements requirements.txt python scripts/publish_daily.py --input state/arxiv_filtered.json
uv run --with-requirements requirements.txt python scripts/build_site.py --output-dir dist
```

For the local Codex CLI fallback, replace the middle steps with:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --skip-push
```

## Main Files

- `scripts/content_store.py`: shared repo path and markdown helpers
- `scripts/ai_enrich.py`: AI-generated Chinese summaries and daily overview
- `scripts/publish_daily.py`: generate `content/daily/` and `content/papers/`
- `scripts/build_site.py`: static site compiler
- `start-my-day/scripts/search_arxiv.py`: search and ranking
- `start-my-day/scripts/scan_existing_notes.py`: build keyword index from `content/papers/`
- `start-my-day/scripts/link_keywords.py`: replace keywords with standard markdown links
- `paper-analyze/scripts/generate_note.py`: generate a repository paper page
- `paper-analyze/scripts/update_graph.py`: update `content/meta/graph_data.json`
