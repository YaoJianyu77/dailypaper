# evil-read-arxiv

A GitHub-hosted daily paper pipeline.

The repository is now structured as a content store plus a static website:

- `start-my-day/scripts/search_arxiv.py` fetches and ranks papers from arXiv and Semantic Scholar.
- `scripts/publish_daily.py` converts search output into versioned markdown under `content/`.
- `scripts/build_site.py` compiles that markdown into a static site under `dist/`.
- `.github/workflows/daily.yml` runs the pipeline on a schedule, commits fresh content, and deploys GitHub Pages.

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
pip install -r requirements.txt
```

Search papers:

```bash
python start-my-day/scripts/search_arxiv.py \
  --config config.example.yaml \
  --output state/arxiv_filtered.json
```

Publish the daily report into `content/`:

```bash
python scripts/publish_daily.py --input state/arxiv_filtered.json
```

Build the static site:

```bash
python scripts/build_site.py --output-dir dist
```

Serve it locally:

```bash
python -m http.server 8000 -d dist
```

Then open `http://localhost:8000`.

## Automation Model

The scheduled GitHub Actions workflow does this end to end:

1. Run the paper search.
2. Optionally enrich the top papers with AI-generated Chinese summaries and recommendations.
3. Generate or update daily markdown and paper pages.
4. Commit `content/` and `state/` changes back into the repository.
5. Build the static site.
6. Deploy the static site to GitHub Pages.

That gives you:

- a homepage that shows the latest daily report
- an archive page for older reports
- one page per paper
- git history for every generated artifact
- a site you can browse on GitHub Pages or locally after `git clone`

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

The included workflow lives at:

- `.github/workflows/daily.yml`

It runs on a cron schedule and also supports manual dispatch.

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

When `OPENAI_API_KEY` is present, the script calls the OpenAI Responses API and adds:

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

When `OPENAI_API_KEY` is missing, the script degrades safely and passes the ranked papers through without failing the workflow.

### GitHub Secrets

To enable unattended AI enrichment in GitHub Actions:

1. Open `Settings -> Secrets and variables -> Actions`
2. Add repository secret:
   - `OPENAI_API_KEY`
3. Optional repository variables:
   - `OPENAI_MODEL`
   - `OPENAI_API_BASE`

Default model in config:

```yaml
ai:
  model: "gpt-4.1-mini"
```

You can also run it locally:

```bash
export OPENAI_API_KEY=\"your-key\"
python scripts/ai_enrich.py \
  --config config.yaml \
  --input state/arxiv_filtered.json \
  --output state/arxiv_enriched.json
python scripts/publish_daily.py --input state/arxiv_enriched.json
```

## Notes on Legacy Files

The repository still contains `skill.md` files and some original helper scripts from the Claude skill version. They are now legacy references. The active path is the repository content workflow described above.

## Minimal Local Flow

```bash
pip install -r requirements.txt
python start-my-day/scripts/search_arxiv.py --config config.example.yaml --output state/arxiv_filtered.json
python scripts/publish_daily.py --input state/arxiv_filtered.json
python scripts/build_site.py --output-dir dist
python -m http.server 8000 -d dist
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
