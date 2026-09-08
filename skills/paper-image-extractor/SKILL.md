---
name: paper-image-extractor
description: Use when preparing DailyPaper visuals or explicitly inspecting, extracting, or rendering paper figures and tables; verify the source pages and make visuals visible and legible. Do not start report generation for image-tool maintenance.
---

# Visual evidence

Read section 5 of `DAILY_REPORT_PRODUCT_REQUIREMENTS.md` for visual limits and presentation requirements. The completion criterion is a visible, legible visual in the rendered daily article, not a file path, PDF link, caption, extraction manifest, or unrendered diagram source.

## Select and inspect

Prioritize the main architecture/workflow/algorithm figure and the strongest end-to-end result, ablation, scalability plot, or explanatory table. Avoid logos, decorative graphics, prose screenshots, and unrelated plots.

Inspect the actual paper page or source image, read its caption, and compare it with surrounding text. Verify axes, units, labels, arrows, legends, baselines, workload/hardware conditions, and the conclusion it supports. Reject a visual whose meaning cannot be verified; do not infer its contents from its caption alone.

## Extract and embed

Prefer a verified original source asset. When necessary, use a source-package PDF figure or a legible crop of the rendered paper page. Retain assets in the existing per-paper image layout under `content/assets/papers/`, as specified by `AGENTS.md`.

Use descriptive filenames such as `figure-3-system-overview.png` or `figure-8-throughput.png`. Embed the actual asset with Markdown image syntax next to its explanation. Use paths compatible with the site builder and deployment base path; a GitHub file-browser page is not an image asset.

The existing helper is `extract-paper-images/scripts/extract_images.py`. Inspect its supported input before calling it; do not assume every publisher URL is accepted. An updated `images/index.md` is only an intermediate extraction result.

## Tables and faithful reconstructions

A verified numerical table can be rendered directly as a Markdown table. Preserve column names, units, baseline names, conditions, and the exact values supporting the conclusion. Identify omitted rows or columns. Do not replace a renderable table with a fenced text block.

When an original item cannot be embedded, a faithful simplified reconstruction may be used. Render it visibly and label it **“Reconstructed from Figure/Table X.”** Mermaid source must be rendered to an image or through a verified diagram renderer. Raw Mermaid code and ASCII text do not satisfy the image requirement.

Preserve the paper's real components, directions, labels, units, and values. Do not interpolate missing measurements, invent labels, or present a reconstruction as the original. If no verified original or reconstruction can be shown, replace the candidate or report the unfilled slot.

## Explain and validate

For each item, provide its original number, a permitted caption quotation or labeled accurate paraphrase, PDF file page and printed page when available, an explanation of relevant visual elements, the supported conclusion, and the main caveat.

Inspect the rendered article for broken paths, unreadable labels, clipping, incorrect table layout, and diagrams shown as source text. Check that committed assets match those inspected. Distinguish local-render verification from verification of the deployed website.

If the user also requests the report in ChatGPT, use supported inline rendering of the same verified visual; do not treat an untested public image URL as proof that the user can see it. A separate ChatGPT copy is not required for website publication.
