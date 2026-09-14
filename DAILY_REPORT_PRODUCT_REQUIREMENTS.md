# Daily Paper Settings

**This is the one page to edit what the daily report should do.** Save changes to `main`; the next agent run must read the latest version. The existing filename is retained so saved task references do not break.

Read the finished report on the existing DailyPaper website. Keep all paper summaries in the same daily article, with their figures and tables inline. Detailed execution rules belong in [AGENTS.md](AGENTS.md) and the [active skills](skills/), not in another user configuration.

The generation pipeline reads this page on each run. Edit the values and prose here; keep the six section names and table labels so the parser can identify them. Unsupported or contradictory values stop generation instead of falling back to old defaults. Verified limitations are tracked in [PROJECT_STATE.md](PROJECT_STATE.md).

## 1. Research areas

| Priority | Current focus |
|---|---|
| Primary | Embodied intelligence × systems, especially vision-language-action (VLA) models and world-action models (WAM); inference execution, serving, and deployment of robot policies and world models used for planning or control; real-time closed-loop inference, action chunking, asynchronous execution, replanning, observation freshness, and deadline-aware scheduling; GPU kernels, CUDA Graphs, runtimes, compilers, concurrency, batching, pipelining, memory and cache management, and computation–communication overlap for these workloads; single-robot latency, multi-robot serving, edge/on-device execution, and edge–cloud or distributed deployment. |
| Also include | Transferable LLM/VLM, diffusion/flow, video-model, and GPU systems techniques with a concrete connection to embodied workloads; representative embodied model papers needed to understand architecture, learning objectives, inference dependencies, action representations, or control semantics, subject to the foundation-paper limit in section 4; simulation, data pipelines, distributed training, and evaluation infrastructure with a substantive embodied-systems contribution; operating systems, distributed systems, networking, storage, resource scheduling, HPC, and computer architecture when their mechanisms provide a specific and defensible research connection. |
| Exclude | Accuracy-only or application-only work without a systems contribution, except qualifying embodied foundation papers under section 4; generic model scaling, prompt-only work, unrelated perception/planning/control improvements, and routine applications of existing optimizations without a substantive systems insight or informative workload characterization; marketing, unsupported opinion pieces, and keyword-only matches. Do not exclude work because its title lacks VLA/WAM or because it appears in a robotics or machine-learning venue. |

VLA = vision-language-action model. WAM = world-action model. Follow each paper's actual formulation rather than treating these labels as mutually exclusive architectural classes. Do not assume every WAM jointly generates video and actions or every VLA uses the same action-generation mechanism. World/video models are relevant when their use in action generation, planning, control, or a clearly transferable execution pattern is established.

Keep embodied intelligence × systems as the center of gravity. Judge research relevance through **workload → execution dependencies → hardware/control constraints → measured bottleneck → design opportunity**, not architectural novelty alone. General systems papers remain eligible, but their concrete connection must be explained rather than asserted with “could be applied to robotics.”

## 2. Search sources

Search the configured systems and robotics/ML venues for relevant work; verify publication identity using official proceedings or publisher records. Venue reputation does not replace topic fit or evidence quality.

| Group | Eligible sources |
|---|---|
| Systems, storage, and networking | SOSP, OSDI, NSDI, EuroSys, USENIX ATC, FAST, SIGCOMM, CoNEXT, SIGMETRICS / PERFORMANCE. |
| Architecture, compilers, parallel computing, and ML systems | ASPLOS, ISCA, MICRO, HPCA, PLDI, CGO, PPoPP, SC, HPDC, MLSys. |
| Robotics and embodied intelligence | CoRL / Conference on Robot Learning, RSS / Robotics: Science and Systems, ICRA, IROS. |
| Machine learning and computer vision | NeurIPS / Advances in Neural Information Processing Systems, ICML / International Conference on Machine Learning, ICLR / International Conference on Learning Representations, CVPR, ICCV, ECCV. |
| Journals | ACM TOCS, ACM TOS, IEEE TPDS, IEEE TC, ACM TACO, IEEE/ACM ToN, ACM POMACS, IEEE T-RO / IEEE Transactions on Robotics, IEEE RA-L / IEEE Robotics and Automation Letters, IJRR / The International Journal of Robotics Research. |

Use official venue websites and proceedings, USENIX, ACM Digital Library, IEEE Xplore, PMLR, RSS proceedings, NeurIPS proceedings, official ICLR proceedings on OpenReview, CVF Open Access, and the relevant journal or proceedings publishers for publication evidence. DBLP, OpenAlex, Semantic Scholar, and Google Scholar can assist discovery. Author pages, institutional sites, and arXiv can supply an accessible copy of the verified work.

Formal publication, including official early access, is required for the date-based pools below. Acceptance alone does not supply a publication date. Exclude standalone preprints, workshop papers, poster-only or demonstration-only abstracts, tutorials, and extended abstracts. A full main-conference paper remains eligible when its presentation format is a poster. An arXiv copy of an eligible published paper is allowed; an OpenReview submission alone does not establish official publication.

The same source and publication rules apply to embodied foundation papers. Eligibility here does not establish implementation support: when publication evidence cannot be verified by the current pipeline, report the source-coverage limitation rather than bypass verification or silently replace the research focus.

## 3. Time windows

| Setting | Current value |
|---|---|
| Date and timezone | Actual execution date in `America/New_York`. |
| Daily schedule | **07:00 America/New_York**, one persistent daily job; update that job on reinstall and prevent overlapping runs. |
| Latest-paper pool | The preceding **6 calendar months**, including the execution date. |
| Classic-paper pool | The preceding **5 calendar years**, excluding the latest-paper pool. |
| Date basis | First verified official online publication, not an arXiv revision, code update, or later issue assignment. |

Print the exact inclusive date ranges in each report. Do not substitute fixed 180-day or 1,825-day approximations for calendar arithmetic. If an uncertain date affects eligibility, replace the candidate or leave the slot unfilled rather than invent a date.

## 4. Selection

| Setting | Current value |
|---|---|
| Latest papers per day | **4** previously unrecommended works. |
| Classic papers per day | **1** previously unrecommended work. |
| Shortfall policy | Fewer papers are allowed; explain the missing slots. Never widen the source/date rules or weaken quality to fill them. |
| Non-repetition | **Permanent**, across all imported and subsequent recommendation history; no cooldown or automatic expiration. |

Rank by research fit, problem importance, central insight, evaluation strength, and practical or research value. Apply these three reading roles within the existing latest/classic pools, not as extra slots:

- **Embodied systems:** highest priority. The paper directly studies systems problems in embodied inference, control, deployment, training, simulation, or infrastructure. Prefer a measured bottleneck and an explained mechanism over speedup numbers alone.
- **Transferable systems:** the paper studies a concrete mechanism relevant to embodied execution, such as iterative generation, dependent multimodal stages, temporal reuse, small-batch inference, or deadline-constrained scheduling. Name the shared execution property and the important difference; do not claim the transfer has been validated unless the paper tests it.
- **Embodied foundation:** a representative model or method paper is eligible without a standalone systems contribution when it materially explains a workload, architectural choice, inference dependency, or control mechanism needed for systems research. Limit this role to **at most 1 paper across the entire daily report**; it is optional, not a quota, and cannot be used as filler. State precisely what prerequisite it supplies.

Prefer directly embodied systems work when quality and relevance are comparable. Seek variety in mechanisms and constraints, not unrelated topics merely for diversity. A missing direct-fit paper does not justify relaxing publication, date, history, or quality requirements. A classic can serve any of the roles above, but needs evidence of continuing influence, adoption, use as a baseline, or an official award; age or citation count alone is insufficient.

Value workload characterization, measurement, and benchmark papers when they reveal a consequential systems constraint or invalidate an existing assumption; a new optimization is not mandatory. Prefer reproducible evaluation and accessible artifacts when otherwise comparable, without requiring a physical robot or excluding simulation-only studies. Preserve the distinction between simulation and real-world evidence.

Use the complete `state/recommendation_history.json` before selection and verify a safe update before publication. Treat versions, renamed titles, preprints, alternate URLs, and publications with the same core contribution as the same work. Unresolved identity or history checks must not be bypassed. Changing these settings never clears prior history.

## 5. Per-paper content

The reader should understand the paper without opening the original. Explain **problem → bottleneck → insight → method → evidence → limitations**, not merely whether the paper is worth reading. The purpose is to build enough model understanding and systems judgment to identify and evaluate research opportunities, not to provide a broad course or invent an idea for every paper.

| Setting | Current value |
|---|---|
| Prompt and report language | **English**, including headings, captions, tables, and trend analysis. |
| Production model policy | Before each daily run, read the current [official Codex model recommendations](https://learn.chatgpt.com/docs/models.md) and verify account availability. Use the uniquely identified most capable recommended Codex model for research. Do not guess model names or fall back to a less capable model. |
| Required Codex mode | **Balanced reasoning (`medium`)**, verified against the chosen model's account-visible settings and current [official reasoning guidance](https://learn.chatgpt.com/docs/agent-configuration/subagents.md). Higher reasoning increases token use, while `medium` is the documented balanced default. Apply the exact resolved model and reasoning setting to every generation call, reject substitutions, and keep the configuration consistent throughout a report and its retries. Complete each stage in one agent thread without subagent delegation. Log the selection evidence, model, reasoning setting, Codex version, and per-stage token usage for each run. |
| Model-call budget | Search and selection may each use one model call when needed. Each selected paper receives one complete-paper analysis call. A failed structural validation stops the run rather than automatically spending more model calls; an explicitly resumed invalid checkpoint may receive one targeted correction. One final cross-paper trend synthesis is allowed. Do not run independent paper-review or report-review model passes, or repeat the synthetic installation diagnostic during normal production. |
| Summary length | **900–1,100 words per paper**, excluding figure captions; hard maximum **1,200 words**. |
| Opening brief | **100–150 words**. |
| Final assessment | One paragraph, **at most 120 words**. |
| Central insights | At most **2**. |
| Major experimental findings | At most **3**. |
| Visuals | **1–2** important figures, tables, or faithful rendered reconstructions per paper; no decorative padding. |
| Reading requirement | Complete paper, including important figures, tables, experiments, footnotes, and relevant appendices. |

Use these seven headings in each paper entry:

1. Paper in brief
2. Problem and core insight
3. How the method works
4. Key figures or tables
5. Experimental evidence
6. Contributions and limitations
7. Final assessment

Follow the insight and finding limits above. Preserve hardware/software configurations, workloads, baseline comparisons, exact results, and the conditions under which the results hold. Use paper references for important claims. Write **“Not specified in the paper.”** for missing details and label conclusions not explicitly stated by the authors as **“Interpretation.”**

Assume a reader with a computer-systems background who is still building embodied-model knowledge. Define essential unfamiliar terms inline as **Term = concrete meaning**, then explain their role in this paper; do not assume familiarity with labels such as joint prediction, action chunking, or flow matching. Give only the prerequisites needed for the central mechanism, within the existing word budget. Identify the paper's reading role in “Paper in brief.”

In “How the method works,” explain the actual execution chain: **inputs → major stages → outputs → next inference/control cycle**, using only stages present in the paper. Separate training-only components from inference-time computation. For joint prediction, identify the predicted variables, their conditioning or information exchange, and the generation order; a joint objective does not by itself establish simultaneous GPU execution. When relevant, explain autoregressive dependencies, iterative denoising/flow steps, action horizons, executed chunks, state/cache reuse and invalidation, and opportunities or barriers to overlap. Include equations, tensor dimensions, masks, or pseudocode only when necessary to understand a dependency, bottleneck, or correctness condition. Do not guess a shared backbone, two-head design, cache semantics, or fixed execution pattern from the model family name.

In “Experimental evidence,” preserve the relevant model, hardware count/type, precision, batch/concurrency, input sizes, generation steps, workloads, baselines, and measurement boundaries that the paper reports. Distinguish kernel/model speedup from end-to-end observation-to-action latency; distinguish inference frequency, replanning frequency, and actuator/control frequency. Report latency distributions, throughput, memory, energy, observation age, deadline misses, and closed-loop task outcomes only where relevant and available. Identify whether gains come from the proposed mechanism, extra hardware, reduced work/precision, or a changed quality setting. Never infer a compute-bound or memory-bound bottleneck from architecture or batch size alone, and never infer successful real-time control from inference speed alone.

In “Contributions and limitations” and the existing “Final assessment,” separate the demonstrated contribution, its enabling assumptions, and what remains untested. Explain whether the lesson is a new systems mechanism, a workload-specific adaptation, or an empirical finding. For transferable/foundation papers, state the concrete systems relevance and the unverified gap without inventing systems results. When the paper supports it, include at most one concise **Interpretation** connecting an observed limitation to a testable hypothesis and a minimal discriminating measurement. This is not a novelty claim; “not evaluated” is not proof of failure, and “not discussed” is not evidence that no prior work exists. Do not force a speculative idea into every summary.

Display the actual selected visuals next to their explanation in the website article. Prefer an original method/architecture figure and the strongest experimental plot or table. A PDF link, image path, figure number, unrendered Mermaid code, or ASCII text does not replace a visible figure. A verified numerical table may be rendered directly as a Markdown table.

A faithful reconstruction must be visibly rendered and labeled **“Reconstructed from Figure/Table X.”** Preserve actual components, arrows, labels, units, and values; do not invent measurements. Explain the original item number/caption, important visual elements, supported conclusion, and main caveat. Respect applicable source-use limits when reproducing captions.

Omit unnecessary history, broad related work, secondary experiments, reading plans, comprehension questions, and instructions to consult the original. The detailed writing checklist is in [paper-deep-analysis](skills/paper-deep-analysis/SKILL.md); rendering details are in [paper-image-extractor](skills/paper-image-extractor/SKILL.md).

## 6. Final research trends

| Setting | Current value |
|---|---|
| Final heading | **Clear Research Trends in Today's Papers** |
| Maximum trends | **3** |
| Minimum latest papers per trend | **2** |
| Explanatory chain | **Shared problem → emerging design direction → unresolved trade-off** |
| Evidence | Name the supporting papers; meet the minimum latest-paper support above where supported. |

For an embodied-systems trend, identify the shared execution pattern or deployment/control constraint and explain why the design direction addresses it. Shared use of “VLA,” “WAM,” “Transformer,” or “diffusion” alone is not a trend. Distinguish evidence observed in embodied workloads from a proposed transfer out of general systems work; do not present the latter as established deployment evidence.

The classic can explain historical development but cannot be the sole evidence of a current trend. Describe signals from today's selected set, not definitive claims about the whole field. State that evidence is insufficient when no shared trend is supported. Do not append a paper-of-the-day ranking, study schedule, or generic closing advice.

---

[Back to the project homepage](README.md) · [Execution details for agents](AGENTS.md) · [Actual implementation status](PROJECT_STATE.md)
