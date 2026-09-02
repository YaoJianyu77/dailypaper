---
name: paper-image-extractor
description: Inspect paper visuals, select the two most informative items, and render them inline in the daily report.
---

# Completion criterion

A paper entry is not complete merely because it names a figure, gives a PDF page, links to a file, or records an asset path. The selected visual content must be visibly rendered inline in:

1. `content/daily/YYYY-MM-DD.md`; and
2. the final ChatGPT task response.

Every paper entry must contain at least one visible visual element and no more than two, following `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`.

## Visual selection

Prefer, in order:

1. the main architecture, workflow, request lifecycle, algorithm, or system-design figure;
2. the strongest end-to-end result, scalability result, ablation, or decision-relevant table;
3. a faithful reconstruction when the original cannot be embedded reliably.

Do not choose decorative figures, logos, screenshots of prose, generic model diagrams, or plots unrelated to the paper's primary claim.

## Inspection requirement

For every candidate visual:

1. inspect the actual PDF page or extracted source image;
2. read the original caption;
3. verify axes, units, legends, labels, arrows, components, workloads, baselines, and experimental conditions;
4. compare the visual against the surrounding paper text;
5. reject the item if its meaning cannot be verified.

Never infer the contents of a figure or table from its caption alone.

## Original-image workflow

Prefer the arXiv source package when available. Fall back to source-package PDF figures, then a crop from the rendered PDF page.

Store retained assets under:

`content/assets/papers/<stable-paper-key>/images/`

Use stable descriptive names such as:

- `figure-3-system-overview.png`
- `figure-8-end-to-end-throughput.png`
- `table-2-ablation.png`

Embed the asset in the daily report with a site-valid absolute path:

```markdown
![Figure 3: system overview](/assets/papers/<stable-paper-key>/images/figure-3-system-overview.png)
```

Immediately below it, include the original number and caption, followed by a concise explanation of what the reader should notice and the most important caveat.

Do not use a repository browser URL as an image source. Do not write only:

- “Figure 3 is on page 7”;
- “see the PDF”;
- “image saved at …”;
- a bare link to the asset.

## Table workflow

When the selected item is a table and the values can be read reliably, render the relevant rows directly as a Markdown table in the report. Preserve:

- column names;
- units;
- baseline names;
- workload/model/hardware conditions;
- values necessary to support the stated conclusion.

Label it with the original table number and caption. State when rows or columns were omitted for compactness.

Do not render a usable table only as a fenced text block. A fenced block is a fallback for layout that cannot be represented as Markdown, not the default.

## Reconstruction fallback

When the original item cannot be embedded because the runtime cannot save binary assets, the source format is unusable, or the visual is too dense, render a faithful simplified reconstruction inline.

Label it exactly:

> **Reconstructed from Figure/Table X.**

Allowed forms:

- Mermaid flowchart for architecture or control/data flow;
- compact ASCII diagram for a sequential pipeline;
- Markdown table for numerical evidence;
- a simple chart only when every plotted value is explicitly available and verified in the paper.

A reconstruction must preserve actual components, directionality, labels, units, and reported numbers. Do not add inferred components or interpolate missing data. Do not use image generation to imitate an original research figure.

A location-only fallback is not allowed. If neither an original item nor a faithful reconstruction can be displayed, replace the paper or leave the slot unfilled.

## Explanation attached to every visual

For each displayed visual, provide:

- original Figure/Table number;
- original caption, quoted or accurately paraphrased within reasonable length;
- PDF file page and paper page when available;
- axes, units, arrows, labels, or columns that matter;
- the exact conclusion it supports;
- the strongest caveat or limitation.

## Existing repository extractor

For the local repository workflow, the existing command remains:

```bash
python extract-paper-images/scripts/extract_images.py \
  <paper_id_or_pdf_path> \
  content/assets/papers/<stable-paper-key>/images \
  content/assets/papers/<stable-paper-key>/images/index.md
```

Extraction is only an intermediate step. After extraction, explicitly select and embed the useful item in the daily report. An updated `images/index.md` does not satisfy the final display requirement by itself.