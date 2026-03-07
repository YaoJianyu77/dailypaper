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

## 3. Enable GitHub-hosted daily generation

```bash
git remote -v
```

The default setup now runs on GitHub, not on your laptop.

What you need in GitHub:

- `Actions` enabled
- `Pages` enabled with `GitHub Actions` as source
- `.github/workflows/daily.yml` enabled
- `.github/workflows/pages.yml` enabled

The generation workflow uses GitHub Models and runs every day at New York `07:00`.

Optional repository variables:

- `AI_MODEL`
- `GITHUB_MODELS_PREFERRED_MODELS`
- `GITHUB_MODELS_API_BASE`

## 4. Trigger a manual run once

Run the generation workflow manually once from the GitHub Actions web UI:

- `Actions`
- `Daily Papers`
- `Run workflow`

This will:

1. search and rank papers
2. call GitHub Models for structured Chinese editorial output
3. publish content into `content/`
4. commit and push updated content back to `main`
5. deploy GitHub Pages directly

## 5. Optional local fallback

If you still want your own machine to do the generation:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py
```

This local path will:

1. pull the latest `main`
2. search and rank papers
3. call local Codex CLI for structured Chinese editorial output
4. publish content into `content/`
5. build `dist/`
6. commit and push updated content back to GitHub

Useful variants:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --skip-push
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --target-date 2026-03-07
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --enricher openai
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --enricher none
uv run --with-requirements requirements.txt python scripts/run_local_daily.py --remote origin
```

## 6. Optional local 07:00 cron job

```bash
./scripts/install_local_cron.sh
```

Cron output goes to:

- `state/logs/local_daily.log`

## 7. GitHub Pages deployment model

Push the repository to GitHub and enable GitHub Pages.

With the current setup:

1. `.github/workflows/daily.yml` generates content every day at New York `07:00` and deploys the site
2. `.github/workflows/pages.yml` rebuilds the static site for local or manual pushes to `main`
3. GitHub Pages publishes the updated site

For GitHub Pages project sites like `https://YaoJianyu77.github.io/dailypaper/`, the build supports the `/dailypaper` subpath automatically in the included GitHub Actions workflow.

For Netlify or Cloudflare Pages:

- build command: `python3 scripts/build_site.py --output-dir dist`
- output directory: `dist`
- leave `SITE_BASE_URL` empty unless you deploy under a custom subpath

The workflow now tries `openai/gpt-5.4` first, then falls back through `openai/gpt-5`, `openai/gpt-4.1`, and `openai/gpt-4o`. You can override that with the `AI_MODEL` repository variable.

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
