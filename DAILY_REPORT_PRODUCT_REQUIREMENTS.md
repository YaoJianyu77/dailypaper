# Daily Paper Settings

**This is the one page to edit what the daily report should do.** Save changes to `main`; the next agent run must read the latest version. The existing filename is retained so saved task references do not break.

Read the finished report on the existing DailyPaper website. Keep all paper summaries in the same daily article, with their figures and tables inline. Detailed execution rules belong in [AGENTS.md](AGENTS.md) and the [active skills](skills/), not in another user configuration.

The generation pipeline reads this page on each run. Edit the values and prose here; keep the six section names and table labels so the parser can identify them. Unsupported or contradictory values stop generation instead of falling back to old defaults. Verified limitations are tracked in [PROJECT_STATE.md](PROJECT_STATE.md).

## 1. Research areas

| Priority | Current focus |
|---|---|
| Primary | GPU systems; LLM/VLM/VLA inference; CUDA and GPU kernel optimization; inference serving and request scheduling; concurrency, batching, and pipelining; GPU memory and KV-cache management; computation–communication overlap; distributed training and inference; compiler/runtime co-design; PTX, SASS, assembly, and low-level code generation. |
| Also include | Operating systems; distributed systems; networking; storage and file systems; memory management; resource scheduling; cloud systems; HPC; computer architecture with a substantive systems contribution. |
| Exclude | Model-accuracy-only or application-only improvements without a systems idea; prompt-only work; marketing and unsupported opinion pieces. Do not exclude a VLM/VLA systems paper merely because it concerns vision or robotics. |

Do not restrict the entire report to AI. Favor important systems problems and understandable design insights over keyword matches alone.

## 2. Search sources

Search the configured venues first and verify publication identity using official proceedings or publisher records.

| Group | Eligible sources |
|---|---|
| Systems, storage, and networking | SOSP, OSDI, NSDI, EuroSys, USENIX ATC, FAST, SIGCOMM, CoNEXT, SIGMETRICS / PERFORMANCE. |
| Architecture, compilers, parallel computing, and ML systems | ASPLOS, ISCA, MICRO, HPCA, PLDI, CGO, PPoPP, SC, HPDC, MLSys. |
| Journals | ACM TOCS, ACM TOS, IEEE TPDS, IEEE TC, ACM TACO, IEEE/ACM ToN, ACM POMACS. |

Use official venue websites, USENIX, ACM Digital Library, and IEEE Xplore for publication evidence. DBLP, OpenAlex, Semantic Scholar, and Google Scholar can assist discovery. Author pages, institutional sites, and arXiv can supply an accessible copy of the verified work.

Formal publication, including official early access, is required for the date-based pools below. Acceptance alone does not supply a publication date. Exclude standalone preprints, workshops, posters, demonstrations, tutorials, and extended abstracts. An arXiv copy of an eligible published paper is allowed.

## 3. Time windows

| Setting | Current value |
|---|---|
| Date and timezone | Actual execution date in `America/New_York`. |
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

Rank by research fit, problem importance, central insight, evaluation strength, and practical or research value. When quality is comparable, avoid an unnecessarily homogeneous set. A classic needs evidence of continuing influence, adoption, use as a baseline, or an official award; age or citation count alone is insufficient.

Use the complete `state/recommendation_history.json` before selection and verify a safe update before publication. Treat versions, renamed titles, preprints, alternate URLs, and publications with the same core contribution as the same work. Unresolved identity or history checks must not be bypassed. Changing these settings never clears prior history.

## 5. Per-paper content

The reader should understand the paper without opening the original. Explain **problem → bottleneck → insight → method → evidence → limitations**, not merely whether the paper is worth reading.

| Setting | Current value |
|---|---|
| Prompt and report language | **English**, including headings, captions, tables, and trend analysis. |
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

The classic can explain historical development but cannot be the sole evidence of a current trend. Describe signals from today's selected set, not definitive claims about the whole field. State that evidence is insufficient when no shared trend is supported. Do not append a paper-of-the-day ranking, study schedule, or generic closing advice.

---

[Back to the project homepage](README.md) · [Execution details for agents](AGENTS.md) · [Actual implementation status](PROJECT_STATE.md)
