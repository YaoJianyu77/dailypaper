# Daily Report Product Requirements

Status: active product requirements agreed on 2026-03-08, updated to remove full-paper-analysis features.

This file is the source of truth for future homepage and daily report behavior. If older code paths or docs assume "generate a paper page for every recommended paper" or any separate full-analysis product, these requirements override that assumption.

## Primary Product Shape

The primary product is the daily recommendation page, not a default collection of per-paper detail pages.

Target information architecture:

- Default output: `content/daily/YYYY-MM-DD.md`
- Default reading experience: one strong daily report that already supports read / skip decisions
- No separate full-analysis output as part of the product

## Confirmed User Preferences

### 1. Homepage / daily report is the main deliverable

The homepage should carry most of the value.

Requirements:

- Each recommended paper should have a relatively detailed mini-analysis on the daily page.
- The daily page should help the user decide whether a paper is worth reading without forcing a click into a separate page.
- More detail is good if it improves judgment quality.
- The problem to avoid is not "too much content", but "content that is too fragmented".

### 2. Daily entries should be detailed but not fragmented

Each paper entry should read like a compact research note, not a pile of fields.

Preferred structure per paper:

- one-sentence judgment
- background and problem
- method and concrete evidence
- why it matters for the user's current research
- what still needs verification
- source / PDF links

Formatting guidance:

- Prefer 1 coherent mini-analysis per paper over many small bullets.
- Compress metadata into one line where possible.
- Keep bullets only for information that is genuinely easier to scan as bullets.
- Avoid repetitive sections that restate the same point in slightly different wording.

### 3. Default workflow should not generate a full paper page for every paper

The user does not want a separate detailed page generated for every recommended paper by default.

Requirements:

- Do not make per-paper detail pages the default publishing output for daily recommendations.
- The daily page should contain the main analysis for all recommended papers.
- If a lightweight internal state artifact is useful for indexing or caching, it may exist, but it should not define the public reading experience.

### 4. No separate full paper analysis product

The product should not include a separate full-paper-analysis workflow or public page type.

Requirements:

- Do not maintain a dedicated full-analysis generation stage in the daily pipeline.
- Do not expose a separate deep-dive or full-analysis page type in the public site.
- The daily report itself should carry the recommendation value.

### 5. Images and tables must serve the analysis

Visual assets are useful only when they improve the reader's understanding of the recommendation.

Requirements:

- Use a figure or table only when it directly supports the text.
- Prefer at most one visual cue per paper on the daily page.
- The visual should illustrate the key mechanism, core result, or most decision-relevant evidence.
- Do not dump extracted assets for their own sake.
- Images, tables, and captions should be integrated into the argument, not appended as raw inventory.

### 6. Homepage ordering must feel correct

The ordering of papers on the homepage should be easy to understand.

Requirements:

- The ranking logic should be visible and defensible.
- If a paper is editorially placed first, the page should make the reason obvious.
- Avoid situations where a lower-scored paper appears first with no explanation.

### 7. Search and recommendation should stay systems-first

The recommendation engine should continue to prioritize the user's current research direction.

Current focus:

- LLM inference acceleration
- LLM code generation for CUDA kernels
- low-level code generation
- PTX / SASS / assembly
- runtime / compiler / kernel optimization

Requirements:

- Systems papers should remain the main target.
- Venue-first retrieval is preferred for systems papers.
- Daily volume is an upper bound, not a quota.
- Fewer but higher-quality papers are preferred over filling the list with weaker matches.

### 8. Classic papers should remain part of the reading program

The user still wants periodic exposure to important older papers.

Requirements:

- A classic paper may appear periodically on the daily page.
- Classics should help build long-term systems background.
- Classics should stay lightweight and recommendation-oriented.

### 9. Quality is more important than time or token saving

Requirements:

- Optimize for judgment quality, not compression for its own sake.
- If richer daily analysis improves reading decisions, prefer the richer version.
- Avoid excessive prompt/token thrift if it harms usefulness.

## Non-Goals

The following are not desired as the default experience:

- generating a public paper page for every recommended paper
- automatic full-paper analysis every day without user intent
- asset-manifest-driven reading flow
- overly terse homepage entries that force the user to click elsewhere
- overly fragmented homepage entries made from too many repeated bullet blocks

## Implementation Direction

Future code changes should move the repo toward this shape:

1. Make the daily report the main public artifact.
2. Expand each daily paper entry into a cohesive mini-analysis.
3. Reduce dependence on default `content/papers/*` publication.
4. Keep images/tables only when they materially improve a daily recommendation.
5. Keep the site navigation centered on daily reports only.
