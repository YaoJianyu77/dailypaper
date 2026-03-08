---
paper_id: 2603.05471v1
title: Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval
authors:
- Artem Vazhentsev
- Maria Marina
- Daniil Moskovskiy
- Sergey Pletenev
- Mikhail Seleznyov
- Mikhail Salnikov
- Elena Tutubalina
- Vasily Konovalov
- Irina Nikishina
- Alexander Panchenko
- Viktor Moskvoretskii
domain: Large Language Models
slug: 2603-05471v1-leveraging-llm-parametric-knowledge-for-fact-che
published: '2026-03-05T18:42:51Z'
summary: 这篇工作试图把事实核查从依赖外部检索，转向直接调用LLM参数知识与内部表征来判断陈述真伪。
source_url: https://arxiv.org/abs/2603.05471v1
pdf_url: https://arxiv.org/pdf/2603.05471v1.pdf
scores:
  relevance: 2.6
  recency: 3.0
  popularity: 2.0
  quality: 2.0
  recommendation: 8.73
tags:
- paper-note
status: generated
updated: '2026-03-07'
institutions:
- Independent Researcher
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- 无检索事实核查
- 大语言模型
- 参数知识
- 内部表征交互
- Agent可信性
- 多语言泛化
reading_priority: high
image_count: 6
analysis_depth: full
full_analysis_source: arxiv_source
---

# Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval

## TL;DR
这篇工作试图把事实核查从依赖外部检索，转向直接调用LLM参数知识与内部表征来判断陈述真伪。

## 中文摘要
论文提出“无检索事实核查”任务，目标是在不依赖外部证据检索的情况下，直接用LLM的参数知识验证任意自然语言陈述。作者构建了一个强调泛化的评测框架，覆盖长尾知识、声明来源变化、多语言和长文本生成四个维度。摘要称在9个数据集、18种方法、3个模型上的实验显示，基于logit的方法通常不如利用内部表征的方法，所提INTRA通过内部表征交互达到SOTA并表现出较强泛化；但摘要没有充分说明具体提升幅度、代价和失败案例。

## Quick Facts
- Paper ID: `2603.05471v1`
- Authors: Artem Vazhentsev, Maria Marina, Daniil Moskovskiy, Sergey Pletenev, Mikhail Seleznyov, Mikhail Salnikov, Elena Tutubalina, Vasily Konovalov, Irina Nikishina, Alexander Panchenko, Viktor Moskvoretskii
- Institutions: Independent Researcher
- Domain: Large Language Models
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-03-05T18:42:51Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05471v1)
- PDF: [download](https://arxiv.org/pdf/2603.05471v1.pdf)
- Reading priority: high
- Why this priority: 这篇论文同时贴合大模型与Agent可信性主线，又试图去掉事实核查里最脆弱、最昂贵的检索环节，问题定义和方法方向都值得优先核对。摘要还给出了较完整的评测广度信号，但关键价值取决于其泛化是否真实、代价是否可接受，因此很适合高优先级阅读。

## Abstract Translation
在以大语言模型为基础的 Agent AI 系统中，可信性是核心研究挑战。为了提升可信度，来自人工文本、网页内容和模型输出的自然语言陈述，通常通过检索外部知识并利用 LLM 判断其是否忠实于检索证据来做事实核查。因此，这类方法受制于检索错误和外部数据可用性，也没有充分利用模型自身的事实验证能力。本文提出“无检索事实核查”任务，关注在不依赖外部检索的情况下验证任意来源的自然语言陈述。为研究这一设定，作者构建了一个强调泛化的综合评测框架，考察其在长尾知识、陈述来源变化、多语言和长文本生成上的鲁棒性。在 9 个数据集、18 种方法和 3 个模型上的实验表明，基于 logit 的方法往往不如利用内部表征的方法。基于这一发现，作者提出 INTRA，通过利用内部表征之间的交互取得了最优表现并展现出较强泛化。更广泛地看，这项工作把无检索事实核查建立为一条有前景的研究方向，可作为检索式框架的补充、提升可扩展性，并支持把这类系统作为训练奖励信号或集成到生成过程中。

## Research Background And Motivation
Agent 系统越来越频繁地消费和生成自然语言陈述，事实核查从“可选组件”变成了可信性基础设施。现有主流路线依赖先检索再验证，但这条链路把性能压在检索质量、知识库覆盖和系统时延上，也弱化了 LLM 参数知识本身的利用。

## Problem Framing
论文研究的问题是：在拿不到外部证据、原始 prompt 或完整生成上下文时，能否仅凭 LLM 的参数知识和内部信号，对任意 atomic claim 给出可靠的真实性分数，而且这种能力能否跨长尾知识、不同 claim 来源、多语言、长文本和 cross-model 设置保持泛化。这件事重要，因为它对应的是 Agent 可信性链路里一个高频、低延迟、可规模化的判别环节。

## Method Overview
论文先把任务定义为仅依赖 claim 文本本身、输出 truthfulness score 的判别问题，然后系统比较概率/不确定性方法、内部表征探针、注意力方法和检索增强方法。在此基础上提出 INTRA：从每层 token hidden states 学习 sequence embedding，先做层内线性真实性判别，再对中间层分数做归一化与回归融合，核心目标不是堆复杂 head，而是在简单结构下提高跨数据集泛化。

### Method Figure
![ICLR_scheme_bright-2.drawio_page1](images/ICLR_scheme_bright-2.drawio_page1.png)

*Figure cue:* The task setting of fact-checking without retrieval. Claims from any source (human or LLMs) can be verified without having access to a knowledge base.

## Method Details
- INTRA 不依赖外部知识、检索结果、原始 prompt 或完整生成，只把单条 atomic claim 作为输入并输出 truthfulness score。
- 方法从 LLM 的各层各 token hidden states 出发，用可学习的 token 权重经 softmax 聚合为每层的 sequence embedding，而不是只取首尾 token 或简单平均。
- 在每一层的 sequence embedding 上训练独立的线性分类器，得到 layer-wise factuality probability；训练目标是标准交叉熵，作者明确避免复杂训练头以减少对特定模式的过拟合。
- 最终融合时不使用全部层，而是只取中间层信息；文中给出的示例是对 Llama 3.1-8B-Instruct 使用第 11 到 22 层。
- 跨层融合前先对各层概率做 quantile normalization，再训练回归器得到最终分数；训练数据被拆成两部分，前一部分用于层内参数，后一部分用于最终回归器。

## Experimental Setup And Evidence
评测围绕 claim-level、无检索 factuality scoring 展开。作者在 9 个数据集、18 种方法和 3 个模型上报告 ROC-AUC 与 PR-AUC；监督方法使用 PopQA 的训练划分，因此 PopQA 被视为 in-domain，其余数据集视为 out-of-domain。数据侧，AC-PopQA 和 AC-WH 由已有 benchmark 派生：答案由 Llama 3.1-8B-Instruct 生成，短答案正确性用 InAccuracy 判定，长答案先拆成 atomic claims，再由 Llama 3.1-70B-Instruct 按类似 FActScore 的流程验证。对照中还包含 Verb+RAG，它使用 Google Serper API 检索 top-5 snippets；其余训练超参、样本规模和统计检验，提取文本没有充分说明。

### Experiment Figure
![best_vs_mean_per_language_group_roc_auc_fin_v3_page1](images/best_vs_mean_per_language_group_roc_auc_fin_v3_page1.png)

*Figure cue:* ROC-AUC on PopQA, split into five popularity groups. The green arrow shows the percent improvement of the top method (INTRA) over the runner-up.

## Datasets And Benchmarks
- AC-PopQA：由 PopQA 派生的 atomic-claim 长尾知识基准，可按实体流行度分组分析。
- AC-WH：由 Wild Hallucinations 派生的 atomic-claim 基准，覆盖长尾事实和长文本生成场景。
- AVeriTeC：人工撰写的真实世界事实 claims。
- X-Fact：覆盖 25 种语言的多语言 crowd-sourced claims。
- Cities：基于 Wikipedia 模板构造的规则生成 claims。
- Companies：基于 Wikipedia 模板构造的规则生成 claims。

## Baselines
- Sequence Probability (SP)
- Perplexity (PPL)
- Mean Token Entropy (MTE)
- Focus
- Claim-Conditioned Probability (CCP)
- RAUQ

## Metrics
- ROC-AUC
- PR-AUC

## Ablations And Analysis
- 层范围消融：文中说明比较了不同 layer range，并报告中间层更有效。
- 单层性能分析：`layer_wise_scores` 图展示了 INTRA 各层的 ROC-AUC。
- 长尾知识分析：PopQA 按实体流行度分成 5 组，比较不同方法在热门到长尾区间的 ROC-AUC。
- 跨数据集泛化分析：MM 在原始 benchmark 上表现强，但在 WH/UHead 等长文本场景失效；UHead 在长文本相关设置领先，但其他设置落后。

## Evaluation Validity And Fairness
- 作者显式把 PopQA 之外的数据集视为 out-of-domain，评测目标瞄准泛化而非单一 benchmark 拟合。
- 监督方法用 PopQA 训练 split 训练，因此总体结果同时混合了 in-domain 与 out-of-domain 表现。
- AC-PopQA 和 AC-WH 的 claim 构造与标注依赖 InAccuracy 和 Llama 3.1-70B-Instruct，可能引入自动标注噪声。
- UHead 只有 Llama 3.1 的公开 checkpoint，跨模型比较并不完全对称。

## Main Results And Claims
提取文本明确支持的结论是：内部表征驱动的方法整体上优于基于 logit 的不确定性信号；大多数监督式方法显著强于无监督的无检索和检索式基线。Verb 是表现最强的无监督路线，但计算更重，而且在非英语输入上拒答严重。INTRA 取得了最高平均表现并显示出更稳健的跨数据集鲁棒性；文本还指出它在 ROC-AUC 上可与 Verb+RAG 持平，在 PR-AUC 上平均高 3%，且计算时间约低 20 倍。关于 INTRA 相对 Sheeps 的 ROC-AUC 提升，提取文本分别给出 0.5% 和 2.7% 两种口径，具体统计口径没有充分说明。

## Research Or Engineering Value
如果正文细节能支撑摘要中的泛化结论，这项工作的工程价值在于提供一个单次前向、无外部检索依赖的 claim verifier，可作为 Agent 输出的首轮事实筛查、长文本拆 claim 后的批量打分器，或检索系统前的 gating 模块。研究上，它也把“参数知识能否直接支撑事实核查”变成了可系统比较的问题，并为 truthfulness reward model 提供了更直接的候选实现；但从现有提取文本看，它更适合作为检索式系统的补充，而不是直接替代。

## Relation To Prior Work
相对主流 retrieval-based fact checking，这篇论文把目标从“判断 claim 是否被检索证据支持”改成“在没有证据时直接判断 claim 是否真实”，因此不再把性能主要押在检索质量、知识库覆盖和延迟上。相对把 hallucination detection 视为自信度估计的路线，它也不是只看输出 logit 或 entropy，更不要求拿到原始 prompt 或完整生成；它把任意 atomic claim 送入模型，利用 hidden states 的 token 聚合、层内判别和跨层融合来抽取 factuality signal。

## Overall Assessment
这篇论文最值得信的部分，是它把无检索事实核查清晰地定义成独立问题，并用较大范围的 benchmark 比较支撑了一个稳定观察：内部表征往往比原始 logit/entropy 更适合做 claim 级 factuality 判断，且 INTRA 在精度与成本的折中上看起来比 Verb+RAG 更实用。最该怀疑的部分，是评测本身的洁净度和外推边界：监督训练锚定 PopQA、部分标签来自其他模型、作者也承认部分规则数据集可能污染，因此“强泛化”和“SOTA”需要结合每个子集与汇总口径细看；同时，提取文本并没有证明这条路线可以替代强检索系统，尤其在时效性事实、超长尾知识和真实开放域部署上仍应保守看待。

## Technical Route Positioning
这篇论文属于 LLM 内部信号驱动的 factuality detection / hallucination detection 路线，解决的是 Agent 可信性链路中“atomic claim 级判别器”这一中间环节：在模型生成之后或训练过程中，直接基于 hidden states、层间分数和少量判别头给 claim 打 truthfulness score，而不是先构建检索器、再做证据对齐。

## Scorecard
- Overall: 7.0/10
- Innovation: 7/10
- Technical Quality: 7/10
- Experimental Rigor: 6/10
- Writing Clarity: 7/10
- Practical Value: 8/10

## Related Paper Comparisons
- [DeepRead: Document Structure-Aware Reasoning to Enhance Agentic Search](/papers/2602-05014v3-deepread-document-structure-aware-reasoning-to-e/) (互补：检索增强系统 vs 无检索事实核查): DeepRead 试图把 agentic search 中“找到并连续阅读外部证据”的过程做得更可靠，核心仍然是强化检索和文档导航；本文则研究在没有外部证据时，LLM 参数知识能否直接完成 claim 级核查。两者不是直接替代关系，而是可形成前后级联：先用无检索判别器做低成本初筛，再把高风险样本交给结构化检索。
- [Rethinking the Trust Region in LLM Reinforcement Learning](/papers/2602-04879v1-rethinking-the-trust-region-in-llm-reinforcement/) (下游衔接：事实性 reward model vs RL 优化器): 本文把无检索事实性判别器定位成可用于训练的 reward signal；DPPO 关注的则是拿到 reward 之后，如何更稳定地优化 LLM 策略。前者解决“truthfulness 奖励如何构造”，后者解决“如何用奖励更新模型”，处在同一训练链路的相邻环节，但并非同一问题。

## Strengths
- 把“事实正确性”与“对检索证据的忠实性”明确区分，问题定义比传统检索式事实核查更贴近无检索和低延迟场景。
- 评测面较宽，覆盖长尾知识、claim 来源变化、多语言、长文本和 cross-model 等泛化压力。
- INTRA 的结构克制而清晰：层内简单判别器加跨层融合，方法论上更像在追求稳健表示而非复杂技巧。
- 结果分析不只给平均分，还涉及层分析、长尾分组、跨数据集失效模式、非英语拒答和计算开销，信息密度较高。

## Future Work
- 围绕中间层表征做更针对性的训练与选择，而不是均匀使用全部层。
- 把 claim 位置、生成长度等结构特征显式纳入长文本 hallucination detection。
- 按语言、实体稀有度或 claim 来源做 detector routing 或 targeted selection。
- 把 retrieval-free factuality signal 直接接入 RL、reward modeling 或 generation-time monitoring。

## Reading Checklist
- 先核对 INTRA 的两阶段训练细节：token 聚合参数、layer-wise classifier、quantile normalization 与最终回归器分别如何拟合。
- 再看 9 个数据集的拆分与标签构造，尤其是 AC-PopQA 和 AC-WH 的 atomic claim 生成与验证流程。
- 重点检查中间层优于首末层的证据是否稳定，以及 layer range ablation 的具体幅度。
- 核对 INTRA 相对 Sheeps 的提升口径，正文摘录里同时出现了 0.5% 和 2.7% 两种说法。

## Core Contributions
- 把“无需外部检索的事实核查”明确提出为独立研究任务，而不是检索式事实核查的附属变体。
- 构建一个强调泛化能力的评测框架，明确覆盖长尾知识、声明来源变化、多语言和长文本生成四个压力维度。
- 提出INTRA，用内部表征交互而非仅靠logit信号进行判断，并在摘要声称的对比实验中取得SOTA。

## Why Read It
- 它直接切中Agent可信性中的一个高成本瓶颈：事实核查是否必须依赖脆弱的检索链路。
- 论文不只给新方法，还给出一个更像“研究基准面”的问题定义和泛化评测框架，后续工作容易在其上比较。
- 如果你关心LLM内部表征究竟能否承载更强的验证能力，这篇论文给出了一个很具体的切入点。

## Risks Or Limits
- 无检索设定天然受参数知识的时效性和覆盖率约束，但提取文本没有充分说明这类失败边界。
- 监督方法以 PopQA 为训练内域，其余数据集为外域；总体平均分数对真实部署可迁移性的解释仍需细看。
- 部分数据构造与标注依赖其他模型和自动流程，标签噪声与评测偏置风险存在。
- 作者自己指出 rule-generated 数据集可能已饱和或受污染，这会抬高某些方法的表观效果。

## Recommended For
- 研究Agent可靠性、事实核查与LLM安全性的研究者
- 关注LLM内部表征、参数知识利用和判别机制的研究者
- 需要设计低延迟、离线或检索不稳定场景校验链路的工程师

## Keywords
- 无检索事实核查
- 大语言模型
- 参数知识
- 内部表征交互
- Agent可信性
- 多语言泛化

## Additional Figures

![layer_wise_scores_page1](images/layer_wise_scores_page1.png)

*Figure cue:* ROC-AUC performance of individual layers in the INTRA method.

![heroplot_with_ci_page1](images/heroplot_with_ci_page1.png)

*Figure cue:* ROC-AUC on PopQA, split into five popularity groups. The green arrow shows the percent improvement of the top method (INTRA) over the runner-up.

![wh_auc_relative_short_10bins_page1](images/wh_auc_relative_short_10bins_page1.png)

*Figure cue:* Short-length claims.

![wh_auc_relative_medium_10bins_page1](images/wh_auc_relative_medium_10bins_page1.png)

*Figure cue:* Short-length claims.
- Full asset manifest: [images/index.md](images/index.md)

## Abstract
Trustworthiness is a core research challenge for agentic AI systems built on Large Language Models (LLMs). To enhance trust, natural language claims from diverse sources, including human-written text, web content, and model outputs, are commonly checked for factuality by retrieving external knowledge and using an LLM to verify the faithfulness of claims to the retrieved evidence. As a result, such methods are constrained by retrieval errors and external data availability, while leaving the models intrinsic fact-verification capabilities largely unused. We propose the task of fact-checking without retrieval, focusing on the verification of arbitrary natural language claims, independent of their source. To study this setting, we introduce a comprehensive evaluation framework focused on generalization, testing robustness to (i) long-tail knowledge, (ii) variation in claim sources, (iii) multilinguality, and (iv) long-form generation. Across 9 datasets, 18 methods and 3 models, our experiments indicate that logit-based approaches often underperform compared to those that leverage internal model representations. Building on this finding, we introduce INTRA, a method that exploits interactions between internal representations and achieves state-of-the-art performance with strong generalization. More broadly, our work establishes fact-checking without retrieval as a promising research direction that can complement retrieval-based frameworks, improve scalability, and enable the use of such systems as reward signals during training or as components integrated into the generation process.

## Recommendation Signals
- Recommendation score: 8.73
- Relevance score: 2.6
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0

## Assets
- Extracted assets are stored in the `images/` folder next to this page.
- Browse the image manifest here: [images/index.md](images/index.md)
