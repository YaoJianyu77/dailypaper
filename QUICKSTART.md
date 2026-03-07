# Quickstart

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Configure

Optional:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to match your research interests.

## 3. Generate today's content

```bash
python start-my-day/scripts/search_arxiv.py \
  --config config.yaml \
  --output state/arxiv_filtered.json

python scripts/ai_enrich.py \
  --config config.yaml \
  --input state/arxiv_filtered.json \
  --output state/arxiv_enriched.json

python scripts/publish_daily.py --input state/arxiv_enriched.json
python scripts/build_site.py --output-dir dist
```

If you did not create `config.yaml`, replace it with `config.example.yaml`.

If you do not set `OPENAI_API_KEY`, the enrichment step will fall back automatically and still produce a report.

## 4. Browse locally

```bash
python -m http.server 8000 -d dist
```

Open `http://localhost:8000`.

## 5. Enable GitHub automation

Push the repository to GitHub and enable GitHub Pages.

The included workflow `.github/workflows/daily.yml` will:

1. fetch papers on a schedule
2. optionally enrich them with AI-generated Chinese summaries
3. update `content/`
4. commit generated content
5. build the site
6. deploy GitHub Pages

For GitHub Pages project sites like `https://YaoJianyu77.github.io/dailypaper/`, the build supports the `/dailypaper` subpath automatically in the included GitHub Actions workflow.

For Netlify or Cloudflare Pages:

- build command: `python3 scripts/build_site.py --output-dir dist`
- output directory: `dist`
- leave `SITE_BASE_URL` empty unless you deploy under a custom subpath

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

## GitHub Secret For AI

To enable the AI layer in GitHub Actions, add this repository secret:

- `OPENAI_API_KEY`

Optional repository variables:

- `OPENAI_MODEL`
- `OPENAI_API_BASE`
