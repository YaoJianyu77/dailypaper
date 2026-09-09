---
name: paper-deep-analysis
description: Use for each selected DailyPaper paper or an explicit request to analyze a paper in depth; read the complete paper and explain its mechanism, experiments, and limitations using the unified settings. Do not generate analyses during unrelated maintenance.
---

# Full-paper technical analysis

Use settings section 5 for every selected paper. Its language, lengths, counts, and headings govern the writing roles below; edited headings take precedence over these role names. Follow `AGENTS.md` for history, runtime, and publication.

## Read and verify

Read the complete source material required by settings section 5, inspecting figures/tables in context rather than inferring them from captions. Metadata, old summaries, and search snippets cannot establish technical claims. When linked author versions or supplements differ, compare their appendices and experimental details, attribute version-specific evidence, and do not conflate versions.

Keep publication metadata and classic-selection evidence separate from paper-based technical claims. Use settings section 5 for required experimental detail and missing-detail/interpretation labels. Cite the relevant page, section, figure, table, or algorithm.

Distinguish a maximum from an average, component performance from end-to-end performance, throughput from latency, and measured behavior from author claims. Never repair missing evidence by inventing an implementation detail. Report unreadable or missing evidence to the controller; analysis does not replace the selection.

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

Define paper-specific terms on first use and apply the settings' content exclusions. Use `daily-paper-editor` for article assembly and final review.
