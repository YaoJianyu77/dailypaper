---
name: paper-deep-analysis
description: Read a selected paper in full and produce a concise, self-contained 900–1,100-word technical summary with inline key visuals.
---

# Objective

Read the entire selected paper and produce a concise, self-contained technical summary that lets the reader understand the work without reading the original paper.

This is not a reading guide. Do not recommend sections to read, ask the reader to consult the paper, or substitute a list of locations for an explanation. Explain the necessary content directly.

The authoritative user preferences are in `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`. Apply this skill once for every paper selected for the daily report.

## Length and priority

- Target length: 900–1,100 words, excluding figure captions.
- Hard maximum: 1,200 words.
- Include at most two key figures, tables, or faithful reconstructed diagrams.
- Prioritize:
  1. the exact problem and bottleneck;
  2. the paper's central insight;
  3. how the proposed method works end to end;
  4. the strongest experimental evidence;
  5. the most important limitations.
- Omit historical background, broad related-work discussion, minor implementation details, and secondary experiments unless they materially affect the conclusions.

## Full-paper requirement

Read the complete paper, including:

- main text;
- important figures and tables;
- evaluation setup and results;
- relevant footnotes;
- appendices needed to understand the mechanism, correctness, or primary evidence.

Do not write a final deep analysis from only the abstract, metadata, search snippets, or a third-party summary. When the full paper cannot be read and verified, reject the candidate or leave the slot unfilled.

When analyzing a PDF, inspect the actual pages containing every selected figure or table. Do not infer visual content from the caption alone.

## Accuracy requirements

- Base the summary only on the paper and separately verified publication metadata.
- Preserve important quantitative results, experimental conditions, hardware configurations, workloads, models, datasets, metrics, and baseline comparisons.
- Do not invent missing details. Write **“Not specified in the paper.”** when necessary.
- Label any conclusion not explicitly stated by the authors as **“Interpretation.”**
- Add page, section, figure, table, or algorithm references for important claims when possible.
- Distinguish among:
  - what the authors claim;
  - what the experiments demonstrate;
  - what the report infers.
- Do not convert a maximum result into an average result, a component result into an end-to-end result, or a result under one workload into a universal claim.

## Required structure

### 1. Paper in brief

Use 100–150 words to explain:

- the exact problem;
- why existing approaches are insufficient;
- the central insight;
- what the proposed method changes;
- the most important quantitative result;
- the paper's main contribution.

This section must provide an accurate high-level understanding of the complete paper.

### 2. Problem and core insight

Explain the real technical problem, including:

- input and output;
- optimization objective;
- relevant constraints;
- workload, model, hardware, or deployment assumptions;
- the primary bottleneck in previous approaches.

Identify no more than two central insights. Explain each as:

**Observation → why it matters → how it leads to the proposed design.**

Avoid generic motivation and phrases that could describe any systems paper.

### 3. How the method works

Begin with one clear end-to-end flow:

**Input → preprocessing or admission → major computation, scheduling, or communication stages → output.**

Explain only the components required to understand the main mechanism. For each important component, state:

- what it receives;
- what it does;
- what it produces;
- how it interacts with the next component;
- why it improves the target metric;
- what overhead or trade-off it introduces.

For a systems paper, explain the relevant parts of:

- architecture;
- request or task lifecycle;
- control path and data path;
- scheduling;
- concurrency, batching, or pipelining;
- communication and synchronization;
- caching or memory management;
- correctness or consistency;
- important implementation optimizations.

For an algorithm or machine-learning component inside a systems paper, explain the relevant model or algorithm structure, objective functions, optimization, approximation, sampling, and computational cost only when they are necessary to understand the systems mechanism.

Do not merely name modules. Explain the causal mechanism:

**Design change → changed system or algorithm behavior → resulting performance or quality improvement.**

### 4. Key figures or tables

Select at most two items:

1. the main architecture, algorithm, or workflow figure;
2. the strongest experimental result, ablation, or scalability result.

The visual itself must be displayed inline in the daily report and in the final ChatGPT response. A PDF link, page number, repository path, or sentence telling the reader where to find the item is not a displayed visual.

Use the original item when technically possible. Otherwise produce a faithful simplified reconstruction labeled exactly:

> **Reconstructed from Figure/Table X.**

For each item:

- include its original number and caption;
- explain the important axes, labels, arrows, components, curves, and experimental conditions;
- state what conclusion it supports;
- mention the most important caveat.

Do not include decorative, redundant, or weakly connected visuals.

### 5. Experimental evidence

Summarize only the experiments required to judge the primary claims.

Briefly state:

- hardware and software environment;
- datasets, models, or workloads;
- main baselines;
- primary metrics;
- important experimental conditions.

Then present no more than three major findings using:

**Claim → experiment → exact numerical result → baseline → condition → whether the evidence supports the claim.**

Explain what causes the reported gain, such as reduced computation, improved scheduling, greater parallelism, lower communication, better locality, caching, approximation, or stronger implementation. When the experiments do not isolate the cause, state that explicitly.

### 6. Contributions and limitations

State the paper's two or three genuine contributions. Distinguish among:

- conceptual insight;
- algorithmic contribution;
- system design;
- engineering implementation.

Then explain:

- main assumptions;
- performance, accuracy, memory, complexity, or deployment trade-offs;
- limitations acknowledged by the authors;
- important limitations visible from the design or evaluation;
- workloads or environments where the method should work well;
- conditions where it may provide little benefit or perform worse.

Clearly label a limitation inferred by the report as **Interpretation** unless the authors explicitly state it.

### 7. Final assessment

End with one paragraph of no more than 120 words explaining:

- what the paper demonstrates convincingly;
- what remains uncertain;
- the strongest part of the work;
- the weakest part;
- whether the contribution is mainly a new idea, a system design, or an engineering realization;
- the conditions under which the conclusions can reasonably be trusted.

## Writing style

- Write in clear, precise English.
- Define paper-specific terms when they first appear.
- Use exact numerical values when available.
- Do not summarize mechanically section by section.
- Do not include a reading plan, comprehension questions, or recommendations to consult the original paper.
- Avoid empty phrases such as “the authors propose a novel framework.”
- Do not repeat the same point in multiple sections.
- Keep the explanation centered on:

**Problem → bottleneck → insight → method → evidence → limitations.**

The final summary must be compact enough to read quickly but complete enough that the reader understands the paper's main mechanism, evidence, contribution, and limitations without opening the original paper.

## Repository integration

The daily report, not a separate per-paper page, is the default public artifact. Write this complete analysis directly into `content/daily/YYYY-MM-DD.md`.

Reuse verified repository metadata and existing assets when they are correct, but do not inherit an old summary merely because it exists. Preserve useful manual notes only when editing an existing artifact and when they remain consistent with the verified paper.