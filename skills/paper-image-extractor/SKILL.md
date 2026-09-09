---
name: paper-image-extractor
description: Use when preparing DailyPaper visuals or explicitly inspecting, extracting, or rendering paper figures and tables; verify the source pages and make visuals visible and legible. Do not start report generation for image-tool maintenance.
---

# Paper visuals

Use settings section 5 for counts and presentation requirements, and `AGENTS.md` for retained asset paths and publication checks.

## Inspect and extract

Choose visuals that explain the mechanism and strongest experimental evidence. Inspect original pages and surrounding text: verify axes, units, arrows, legends, baselines, workload/hardware conditions, and supported conclusions. Captions alone cannot establish visual meaning.

Prefer original source assets, source-package PDF figures, or legible page crops. The manual helper `skills/paper-image-extractor/scripts/extract_images.py` accepts an arXiv ID or local PDF, output directory, and index path. Its inventory is an intermediate artifact; check selected images yourself. Production uses the verified document pages and crop/table contracts in `scripts/report_validation.py`.

Use descriptive image filenames and embed assets next to their explanation with deployment-compatible paths. A GitHub file-browser URL is not an image URL.

## Tables and reconstructions

Render verified numerical tables directly as Markdown tables, preserving headers, units, baselines, conditions, exact values, and any indicated omissions. Do not substitute fenced text.

If reconstruction is needed, retain actual components, arrows, labels, axes, units, and measurements. Render it visibly and identify the original Figure/Table number with the reconstruction label from settings. Mermaid source and ASCII diagrams do not substitute for a rendered visual. If no faithful visual is possible, report the evidence gap rather than inventing it.

## Explain and validate

Identify each original item, PDF/printed page when available, and a source-use-compliant quotation or labeled caption paraphrase. Explain meaningful visual elements, the supported conclusion, and its main caveat.

Inspect the final rendered article for broken paths, clipping, unreadable labels, and incorrect tables. Use original-size/zoom views for wide figures and check all details. Verify retained assets match inspected ones; distinguish local rendering from live-site verification.
