---
name: paper-deep-analysis
description: Use for each selected DailyPaper paper or an explicit request to analyze a paper in depth; read the complete paper and explain its mechanism, experiments, and limitations using the unified settings. Do not generate analyses during unrelated maintenance.
---

# Full-paper technical analysis

Read `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`, especially section 5, before writing. Language, length, brief/assessment limits, visual count, and output structure come from that page; do not maintain competing numeric defaults here. Use this skill for every selected paper, not just the highest-ranked one.

## Read and verify

Read the complete paper: main text, important figures/tables, experiments, footnotes, and relevant appendices. Inspect actual figure/table pages rather than inferring their contents from captions. Metadata, abstract text, old repository summaries, and search snippets are screening inputs, not substitutes for reading the paper.

Base technical analysis on the paper. Keep separately verified publication metadata and classic-selection evidence distinct from technical claims. Preserve exact results, hardware/software, models, workloads, baseline comparisons, and conditions. Use the settings page's labels for missing details and interpretation. Cite the relevant page, section, figure, table, or algorithm when possible.

Distinguish a maximum from an average, component performance from end-to-end performance, throughput from latency, and measured behavior from author claims. Never repair missing evidence by inventing an implementation detail. Replace an unreadable candidate or leave the slot unfilled.

## Writing sequence

Use the narrative and ordered headings from section 5 of the settings. The roles below explain how to write those sections; they do not override edited headings. Do not mechanically summarize every paper section, repeat the same result across sections, or substitute generic praise for a causal explanation.

### 1. Paper in brief

Within the configured brief length, explain the exact problem, inadequacy of prior approaches, central insight, design change, most important quantitative result, and main contribution. This must provide a high-level understanding of the complete work.

### 2. Problem and core insight

Specify input/output, optimization objective, constraints, workload/model/hardware/deployment assumptions, and the actual bottleneck. For each central insight, explain **observation → why it matters → design consequence**. Use the insight-count limit from the settings page and avoid generic motivation.

### 3. How the method works

Start with **input → preprocessing/admission → major computation, scheduling, or communication stages → output**.

Explain what each essential component receives, does, and produces; its connection to the next stage; why it improves the target metric; and its overhead or trade-off. Explain **design change → changed system behavior → performance or quality effect**, not merely module names.

For systems work, cover relevant architecture, task/request lifecycle, control and data paths, scheduling, concurrency, batching/pipelining, synchronization, communication, caches/memory, correctness/consistency, and significant optimizations. For an essential algorithmic or ML component, explain the necessary objectives/equations, training/inference distinction, approximation/sampling, and computational cost. Omit irrelevant categories.

### 4. Key figures or tables

Use `skills/paper-image-extractor/SKILL.md`. Choose the mechanism and evidence visuals that explain the core contribution, within the settings limit. Show them directly inside the daily article. For each, identify the original item and caption, explain relevant axes/labels/arrows/conditions, state the supported conclusion, and identify the main caveat. Reproduced captions must respect source-use limits; accurate paraphrases must be labeled as such.

A path or figure location is not a displayed figure. A reconstruction must be faithful, visibly rendered, and labeled with its original Figure/Table number. Do not fabricate measurements or add decorative graphics.

### 5. Experimental evidence

Briefly give hardware/software, datasets/models/workloads, baselines, metrics, and key conditions. Within the configured finding limit, use **claim → experiment → exact result → baseline → condition → whether the evidence supports the claim**.

Explain the source of gain: reduced work, scheduling, parallelism, communication, locality, caching, approximation, or implementation. If the experiments do not isolate the cause, say so. Do not generalize results beyond evaluated conditions.

### 6. Contributions and limitations

Distinguish contributions in conceptual insight, algorithm, system design, and engineering implementation. Explain assumptions and performance/accuracy/memory/complexity trade-offs, acknowledged limitations, design/evaluation limitations, favorable settings, and settings with little benefit or regression. Label inferred limitations according to the settings.

### 7. Final assessment

Within the configured assessment limit, give one paragraph covering what is convincingly demonstrated, remaining uncertainty, strongest and weakest parts, the main contribution type, and the conditions under which conclusions can be trusted.

## Final editorial check

Use precise language and define paper-specific terms on first use. Omit nonessential history, broad related work, minor implementation details, and secondary experiments. No reading guide, comprehension questions, study plan, or request to consult the original is allowed. The daily article itself must carry the complete explanation; a separate per-paper public page is not required.

Follow `AGENTS.md` for archive paths and publication. Preserve useful manual notes when an existing artifact is explicitly being edited; do not rewrite historical reports just because the template changed.
