---
name: paper-deep-analysis
description: Use for each selected DailyPaper paper or an explicit request to analyze a paper in depth; read the complete paper and explain its mechanism, experiments, and limitations using the unified settings. Do not generate analyses during unrelated maintenance.
---

# Full-paper technical analysis

Use settings section 5 for every selected paper. Its language, lengths, counts, and headings govern the writing roles below; edited headings take precedence over these role names. Follow `AGENTS.md` for history, runtime, and publication.

## Read and verify

Read the complete paper: main text, important figures/tables, experiments, footnotes, and relevant appendices. Inspect actual figure/table pages rather than inferring their contents from captions. Metadata, abstract text, old repository summaries, and search snippets are screening inputs, not substitutes for reading the paper.

Base technical analysis on the paper. Keep separately verified publication metadata and classic-selection evidence distinct from technical claims. Preserve exact results, hardware/software, models, workloads, baseline comparisons, and conditions. Use the settings page's labels for missing details and interpretation. Cite the relevant page, section, figure, table, or algorithm when possible.

Distinguish a maximum from an average, component performance from end-to-end performance, throughput from latency, and measured behavior from author claims. Never repair missing evidence by inventing an implementation detail. Replace an unreadable candidate or leave the slot unfilled.

## Writing sequence

Develop a causal explanation; avoid mechanically summarizing every source section or repeating the same result.

### 1. Paper in brief

Within the configured brief length, explain the exact problem, inadequacy of prior approaches, central insight, design change, most important quantitative result, and main contribution. This must provide a high-level understanding of the complete work.

### 2. Problem and core insight

Specify input/output, optimization objective, constraints, workload/model/hardware/deployment assumptions, and the actual bottleneck. For each central insight, explain **observation → why it matters → design consequence**. Use the insight-count limit from the settings page and avoid generic motivation.

### 3. How the method works

Start with **input → preprocessing/admission → major computation, scheduling, or communication stages → output**.

Explain what each essential component receives, does, and produces; its connection to the next stage; why it improves the target metric; and its overhead or trade-off. Explain **design change → changed system behavior → performance or quality effect**, not merely module names.

For systems work, cover relevant architecture, task/request lifecycle, control and data paths, scheduling, concurrency, batching/pipelining, synchronization, communication, caches/memory, correctness/consistency, and significant optimizations. For an essential algorithmic or ML component, explain the necessary objectives/equations, training/inference distinction, approximation/sampling, and computational cost. Omit irrelevant categories.

### 4. Key figures or tables

Use `skills/paper-image-extractor/SKILL.md` to choose, verify, render, and explain the core mechanism/evidence visuals.

### 5. Experimental evidence

Briefly give hardware/software, datasets/models/workloads, baselines, metrics, and key conditions. Within the configured finding limit, use **claim → experiment → exact result → baseline → condition → whether the evidence supports the claim**.

Explain the source of gain: reduced work, scheduling, parallelism, communication, locality, caching, approximation, or implementation. If the experiments do not isolate the cause, say so. Do not generalize results beyond evaluated conditions.

### 6. Contributions and limitations

Distinguish contributions in conceptual insight, algorithm, system design, and engineering implementation. Explain assumptions and performance/accuracy/memory/complexity trade-offs, acknowledged limitations, design/evaluation limitations, favorable settings, and settings with little benefit or regression. Label inferred limitations according to the settings.

### 7. Final assessment

Within the configured assessment limit, give one paragraph covering what is convincingly demonstrated, remaining uncertainty, strongest and weakest parts, the main contribution type, and the conditions under which conclusions can be trusted.

## Final editorial check

Define paper-specific terms on first use. Apply the settings' exclusions for unnecessary history, related work, secondary experiments, and reading advice. The daily article must carry the explanation; a separate public paper page is not required. Preserve useful notes and historical reports when editing existing artifacts.
