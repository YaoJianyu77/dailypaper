---
name: paper-image-extractor
description: Extract paper figures into the repository content store with arXiv source-first fallback behavior.
---

Use this skill for:
- `extract-paper-images/scripts/extract_images.py`
- populating `content/papers/<slug>/images/`
- rebuilding `images/index.md`

Workflow:
1. Prefer the arXiv source package when available.
2. Fall back to source-package PDF figures, then direct PDF extraction.
3. Save results next to the paper page in `content/papers/<slug>/images/`.
4. Keep `images/index.md` updated so the paper page can link to the asset manifest.

Command pattern:
```bash
python extract-paper-images/scripts/extract_images.py \
  <paper_id_or_pdf_path> \
  content/papers/<slug>/images \
  content/papers/<slug>/images/index.md
```

Selection rules:
- Prefer architecture, pipeline, and main-results figures over decorative assets.
- Keep only the images that help browsing the paper page.
