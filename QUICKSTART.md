# Quickstart

## 1. Install

```bash
uv --version
```

## 2. Configure

Optional:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to match your research interests.

## 3. Prepare local AI generation

```bash
codex --help
git push dailypaper main
```

The default setup now runs on your own machine, not in GitHub Actions.

What you need locally:

- `codex` installed and already logged in
- `git push dailypaper main` working without prompts
- the machine powered on at 07:00 local time

Optional repository secret:

- `SEMANTIC_SCHOLAR_API_KEY`

If this secret is absent and Semantic Scholar rate-limits the run, the hot-paper pass degrades gracefully and continues with arXiv results.

## 4. Run the local pipeline once

Run:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py
```

This will:

1. search and rank papers
2. call local Codex CLI for structured Chinese editorial output
3. publish content into `content/`
4. commit and push updated content back to `main`
5. trigger `.github/workflows/pages.yml`
6. refresh GitHub Pages

Useful variants:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --skip-push
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --target-date 2026-03-07
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --enricher openai
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --enricher none
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --remote dailypaper
```

## 5. Install the local 07:00 cron job

```bash
./scripts/install_local_cron.sh
```

Cron output goes to:

- `state/logs/local_daily.log`

## 6. GitHub Pages deployment model

Push the repository to GitHub and enable GitHub Pages.

With the current setup:

1. your local 07:00 job generates and pushes content
2. `.github/workflows/pages.yml` rebuilds the static site for pushes to `main`
3. GitHub Pages publishes the updated site

For GitHub Pages project sites like `https://YaoJianyu77.github.io/dailypaper/`, the build supports the `/dailypaper` subpath automatically in the included GitHub Actions workflow.

For Netlify or Cloudflare Pages:

- build command: `python3 scripts/build_site.py --output-dir dist`
- output directory: `dist`
- leave `SITE_BASE_URL` empty unless you deploy under a custom subpath

`.github/workflows/daily.yml` remains available as a manual GitHub-side fallback, but it is no longer the primary path.

## Output layout

```text
content/
  daily/
  papers/
  meta/
state/
dist/
```

## Images

Store extracted images next to each paper page:

```text
content/papers/<slug>/images/
```

Generate them with:

```bash
python extract-paper-images/scripts/extract_images.py \
  <paper-id> \
  content/papers/<slug>/images \
  content/papers/<slug>/images/index.md
```

## Optional local preview

If you still want to inspect the generated site before pushing:

```bash
uv run --with-requirements requirements.txt python -m http.server 8000 -d dist
```
