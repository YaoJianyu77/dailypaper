# Systems Paper Daily — Product Requirements

Status: active source of truth.

This file contains every preference the user is expected to edit directly. Operational details belong in `AGENTS.md` and the active skills under `skills/`. The scheduled task, local Codex workflow, and GitHub-hosted workflow must treat this file as authoritative when older code, prompts, or documentation disagree.

## Scheduled Task Entry Point

Use the following as the complete instruction saved in ChatGPT Scheduled Tasks:

> Open the GitHub repository `YaoJianyu77/dailypaper` on branch `main`. Read `PROJECT_STATE.md`, `AGENTS.md`, and `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`, then load the active skills required by `AGENTS.md`. Execute the complete **Systems Paper Daily** workflow for the current date in `America/New_York`. Read the persistent recommendation history before selecting papers, permanently exclude every previously recommended research work, read every selected paper in full, display the selected figures or tables inline, write the final report to the repository's existing `content/` structure, update and verify the history only after the report is complete, and return the complete report—not merely links or file locations. Fail closed if a required read, write, full-text verification, visual rendering, or history verification step cannot be completed.

The schedule itself is maintained in ChatGPT Scheduled Tasks. Editing this repository does not change the saved execution time.

---

# User-editable configuration

Only the sections marked **USER-EDITABLE** are intended for routine preference changes. Editing them must never erase recommendation history.

## 1. Output language and reading goal — USER-EDITABLE

- The prompt, report, headings, captions, explanations, and trend analysis must be written in clear, precise **English**.
- Preserve original paper titles and paper-specific technical terms.
- Define a paper-specific term when it first appears.
- The report must be self-contained: the reader should understand each paper's main idea, mechanism, evidence, and limitations without opening the original paper.
- This is not a reading guide. Do not tell the reader which section to read, ask the reader to consult the paper, or provide comprehension questions.

## 2. Research areas — USER-EDITABLE

### Primary focus

- GPU systems
- AI inference systems
- LLM, VLM, and VLA inference
- CUDA and GPU kernel optimization
- inference serving and request scheduling
- concurrency, batching, pipelining, and overlap
- GPU memory and KV-cache management
- computation–communication overlap
- distributed training and inference
- compiler/runtime co-design for foundation models
- PTX, SASS, assembly-level optimization, and low-level code generation

### Secondary focus

- operating systems
- distributed systems
- networking systems
- storage and file systems
- memory management
- resource scheduling
- cloud systems
- high-performance computing
- computer architecture when the systems contribution is central

### Default exclusions

Exclude papers whose main contribution is only model accuracy, application quality, prompt design, dataset construction, or domain adaptation without a substantive systems idea. Also exclude workshop papers, posters, tutorials, extended abstracts, opinion pieces, and marketing material unless this section is explicitly changed.

## 3. Search sources — USER-EDITABLE

Search venue-first. A paper is eligible only when it is formally published, accepted, or available as an official early-access article in one of the configured top-tier systems venues below. arXiv may provide the readable full text, but arXiv presence alone is not evidence of publication.

### Operating systems, distributed systems, storage, and networking

- SOSP
- OSDI
- NSDI
- EuroSys
- USENIX ATC
- FAST
- SIGCOMM
- CoNEXT
- SIGMETRICS / PERFORMANCE

### Architecture, compilers, parallel systems, and HPC

- ASPLOS
- ISCA
- MICRO
- HPCA
- PLDI
- CGO
- PPoPP
- SC
- HPDC

### Machine-learning systems

- MLSys

### Journals

- ACM Transactions on Computer Systems (TOCS)
- ACM Transactions on Storage (TOS)
- IEEE Transactions on Parallel and Distributed Systems (TPDS)
- IEEE Transactions on Computers (TC)
- ACM Transactions on Architecture and Code Optimization (TACO)
- IEEE/ACM Transactions on Networking (ToN)
- ACM Proceedings on Measurement and Analysis of Computing Systems (POMACS)

Use official conference proceedings, publisher pages, USENIX, ACM Digital Library, IEEE Xplore, and official journal pages as primary publication evidence. DBLP, OpenAlex, Semantic Scholar, and Google Scholar may assist discovery and cross-checking, but they do not replace the official record. Use an author page, institutional page, or arXiv only to obtain an accessible copy after publication identity has been verified.

## 4. Time windows — USER-EDITABLE

Calculate both windows from the execution date in `America/New_York` and print the exact inclusive date range at the top of the report.

- **Latest-paper pool:** papers first formally published online during the preceding **6 calendar months**, including the execution date.
- **Classic-paper pool:** papers first formally published during the preceding **5 years**, excluding the latest-paper window so that the two pools never overlap.

Use the first official online-publication date when available. A later journal issue assignment, arXiv revision, code release, or web-page update does not make an old research work new. When only a year is verifiable and that ambiguity affects eligibility, do not invent a date; replace the candidate or report that the slot could not be filled.

## 5. Selection and permanent non-repetition — USER-EDITABLE

Daily target:

- **4 previously unrecommended latest papers**
- **1 previously unrecommended classic paper**

Quality is a constraint, not a quota. Return fewer papers when enough eligible, non-duplicate, full-text-readable papers cannot be verified. Never fill a slot by weakening the venue list, widening the time window, using an abstract-only paper, or repeating a prior research work.

Rank latest papers by:

1. fit with the configured research areas;
2. importance of the systems problem;
3. originality and causal clarity of the central idea;
4. strength and relevance of the evaluation;
5. practical or research value for systems work.

A classic paper must have verifiable continuing influence, such as repeated use as a baseline, adoption of its abstraction or design, recognized deployment, an official award, or clear influence on later systems. Citation count alone is insufficient.

### Permanent duplicate rule

The persistent history is:

- `state/recommendation_history.json`

A research work becomes permanently ineligible once it appears in that history with an imported, reserved, archived, or otherwise completed recommendation status. There is no cooldown and no automatic expiration.

Identify the same research work using, in priority order:

1. normalized DOI;
2. arXiv identifier without the version suffix;
3. DBLP key or another stable publication identifier;
4. normalized title plus author overlap;
5. explicit evidence that a preprint, renamed paper, conference version, journal extension, or revised title represents the same core contribution.

Different URLs, arXiv versions, title changes, or publication venues do not make the same work eligible again. A substantially extended paper is still a duplicate unless its primary technical contribution and evaluation are demonstrably different.

The task must read the complete history before candidate selection, re-read the current history immediately before committing, detect concurrent changes, and verify the final written history after committing. If history cannot be completely read or safely updated, do not publish recommendations.

## 6. Per-paper summary — USER-EDITABLE

Read the complete paper, including important figures, tables, experiments, footnotes, and relevant appendices. Base the summary only on the paper and verified publication metadata.

### Length and priority

- Target length: **900–1,100 words per paper**, excluding figure captions.
- Hard maximum: **1,200 words per paper**.
- Include at most **two** key figures, tables, or faithful reconstructed diagrams per paper.
- Prioritize:
  1. the exact problem and bottleneck;
  2. the paper's central insight;
  3. how the proposed method works end to end;
  4. the strongest experimental evidence;
  5. the most important limitations.
- Omit historical background, broad related-work discussion, minor implementation details, and secondary experiments unless they materially affect the conclusions.

### Accuracy requirements

- Preserve important quantitative results, experimental conditions, hardware configurations, workloads, and baseline comparisons.
- Do not invent missing details. Write **“Not specified in the paper.”** when necessary.
- Label any conclusion not explicitly stated by the authors as **“Interpretation.”**
- Add page, section, figure, table, or algorithm references for important claims when possible.
- Distinguish the authors' claim, the evidence actually presented, and the report's interpretation.

### Required structure for every paper

#### 1. Paper in brief

In 100–150 words, explain the exact problem, why existing approaches are insufficient, the central insight, what the proposed method changes, the most important quantitative result, and the main contribution.

#### 2. Problem and core insight

Explain the input and output, optimization objective, constraints, workload/model/hardware/deployment assumptions, and the primary bottleneck in previous approaches. Identify no more than two central insights, each using:

**Observation → why it matters → how it leads to the design.**

#### 3. How the method works

Begin with one explicit end-to-end chain:

**Input → admission or preprocessing → computation/scheduling/communication stages → output.**

For every essential component, explain what it receives, what it does, what it produces, how it interacts with the next component, why it improves the target metric, and what overhead or trade-off it introduces. Explain control path and data path, scheduling, concurrency, batching, pipelining, communication, synchronization, caching, memory management, correctness, consistency, and implementation optimizations only when they are relevant.

Use the causal form:

**Design change → changed system behavior → resulting performance or quality effect.**

#### 4. Key figures or tables

Select at most two items:

1. the main architecture, algorithm, or workflow figure;
2. the strongest experimental result, ablation, or scalability result.

The visual itself must appear **inline in the report**. A sentence such as “see Figure 4 on page 7,” a link to the PDF, or a file location does not satisfy this requirement.

For every item, include its original number and caption, explain the important axes, labels, arrows, components, curves, and experimental conditions, state the conclusion it supports, and state its most important caveat.

#### 5. Experimental evidence

Briefly state the hardware/software environment, datasets/models/workloads, baselines, metrics, and important conditions. Include no more than three major findings, each using:

**Claim → experiment → exact result → baseline → condition → whether the evidence supports the claim.**

Explain what actually causes the gain. When the evaluation does not isolate the cause, say so explicitly.

#### 6. Contributions and limitations

State two or three genuine contributions and classify them as conceptual insight, algorithmic contribution, system design, or engineering implementation. Explain assumptions, performance/accuracy/memory/complexity trade-offs, author-acknowledged limitations, important limitations visible from the design or evaluation, favorable workloads, and cases where the method may offer little benefit or perform worse.

#### 7. Final assessment

End with one paragraph of at most 120 words explaining what the paper demonstrates convincingly, what remains uncertain, the strongest and weakest parts, whether the main contribution is an idea, system design, or engineering realization, and the conditions under which the conclusions can reasonably be trusted.

## 7. Visual display policy — USER-EDITABLE

Every paper entry must contain at least one visible visual element and no more than two.

Preferred order:

1. an original architecture/workflow figure;
2. an original strongest-results plot or table;
3. a faithful simplified reconstruction when the original cannot be embedded reliably.

For repository archives, store extracted or cropped assets under:

- `content/assets/papers/<stable-paper-key>/images/`

Embed them in `content/daily/YYYY-MM-DD.md` using rendered Markdown image syntax and a site-valid path, for example:

```markdown
![Figure 4: MPK compilation and runtime flow](/assets/papers/<stable-paper-key>/images/figure-4.png)
```

For a table, render the relevant rows directly as a Markdown table whenever possible. Do not place a table only in a code block and do not provide only a link or location.

When an original visual cannot be stored or displayed, include a faithful Mermaid diagram, ASCII pipeline, or Markdown table in the report and label it exactly:

> **Reconstructed from Figure/Table X.**

A reconstruction must preserve the paper's actual components, directions, labels, units, and values. It must never introduce inferred measurements or appear to be an original figure.

The final ChatGPT task response must display the same visual material inline. Returning only the GitHub report path is incomplete.

## 8. Final daily trend section — USER-EDITABLE

End the complete report with:

# Clear Research Trends in Today's Papers

Include at most three trends. Each trend must follow:

**Shared problem → emerging design direction → unresolved trade-off.**

Support each trend with at least two of the day's latest papers whenever possible and name those papers. The classic paper may explain historical evolution but cannot be the sole evidence for a current trend. Present these as signals from the selected set, not definitive claims about the entire field. If the selected papers do not support a meaningful common trend, state that the evidence is insufficient rather than inventing one.

Do not add a reading plan, “paper of the day,” study schedule, or generic closing advice.

---

# Operational contract

The implementation details below are not routine user-editable settings.

## Required repository paths

- Product configuration: `DAILY_REPORT_PRODUCT_REQUIREMENTS.md`
- Agent entry point: `AGENTS.md`
- Project state: `PROJECT_STATE.md`
- Persistent scheduled-task history: `state/recommendation_history.json`
- Existing local-pipeline index: `state/paper_index.json`
- Daily reports: `content/daily/YYYY-MM-DD.md`
- Shared visual assets: `content/assets/papers/<stable-paper-key>/images/`
- Active skills: `skills/*/SKILL.md`

Do not create a parallel `chatgpt_daily/` directory. Do not write daily reports or configuration outside the repository's existing `content/`, `state/`, and `skills/` structure.

## Transaction order

Use this exact order:

**Read configuration and skills → read complete history → search and verify candidates → resolve research-work identity → select papers → read every paper and inspect visuals → draft the complete report with inline visuals → re-read history → reserve selected works → archive and verify the report → mark reservations archived → verify history → return the complete report.**

Use one stable run ID per local calendar date, such as `systems-paper-daily:2026-09-02`. A retry for the same date must resume or verify the existing transaction rather than create a second recommendation set.

If a required step fails, leave an explicit failed or recoverable transaction record when possible, but do not publish an unverified report and do not claim success.