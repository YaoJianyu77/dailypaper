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

## 3. Prepare local Codex automation

```bash
codex --help
git push origin main
```

Requirements for unattended local runs:

- `codex` must be installed and already logged in on this machine
- `git push origin main` must work without prompting
- the machine must be on at 07:00 local time

## 4. Generate today's content locally

Run the full local pipeline:

```bash
uv run --with-requirements requirements.txt python scripts/run_local_daily.py
```

This will:

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

## 5. Install the daily 07:00 cron job

```bash
./scripts/install_local_cron.sh
```

Cron output goes to:

- `state/logs/local_daily.log`

## 6. GitHub Pages deployment model

Push the repository to GitHub and enable GitHub Pages.

With the current setup:

1. your local 07:00 cron job generates and pushes content
2. `.github/workflows/pages.yml` rebuilds the static site on every push to `main`
3. GitHub Pages publishes the updated site

For GitHub Pages project sites like `https://YaoJianyu77.github.io/dailypaper/`, the build supports the `/dailypaper` subpath automatically in the included GitHub Actions workflow.

For Netlify or Cloudflare Pages:

- build command: `python3 scripts/build_site.py --output-dir dist`
- output directory: `dist`
- leave `SITE_BASE_URL` empty unless you deploy under a custom subpath

## 7. Optional GitHub-side generation

If you later want GitHub Actions to generate content without your local machine, use `.github/workflows/daily.yml` manually. That workflow both generates content and deploys Pages directly. Set:

- `OPENAI_API_KEY`
- optional `OPENAI_MODEL`
- optional `OPENAI_API_BASE`

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
