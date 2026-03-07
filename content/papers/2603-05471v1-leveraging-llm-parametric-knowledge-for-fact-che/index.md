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
summary: 这篇工作把“无检索事实核验”明确成独立问题，并把重心放到如何直接利用 LLM 内部表征而不是外部证据。
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
keywords:
- 无检索事实核验
- 参数知识
- 内部表征
- INTRA
- LLM 可信性
reading_priority: high
image_count: 5
analysis_depth: full
full_analysis_source: arxiv_source
---

# Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval

## TL;DR
这篇工作把“无检索事实核验”明确成独立问题，并把重心放到如何直接利用 LLM 内部表征而不是外部证据。

## 中文摘要
论文关注不依赖外部检索的事实核验，目标是直接利用 LLM 参数知识判断任意自然语言断言的真实性。作者先搭建覆盖长尾知识、来源变化、多语言和长文本生成的评测框架，再提出利用内部表征交互的 INTRA。摘要声称在 9 个数据集、18 种方法和 3 个模型上的比较中，内部表征方法整体优于基于 logit 的方法，但具体任务设置、计算代价与失败案例摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05471v1`
- Authors: Artem Vazhentsev, Maria Marina, Daniil Moskovskiy, Sergey Pletenev, Mikhail Seleznyov, Mikhail Salnikov, Elena Tutubalina, Vasily Konovalov, Irina Nikishina, Alexander Panchenko, Viktor Moskvoretskii
- Domain: Large Language Models
- Published: 2026-03-05T18:42:51Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05471v1)
- PDF: [download](https://arxiv.org/pdf/2603.05471v1.pdf)
- Reading priority: high
- Why this priority: 与 LLM 和 Agent 可信性主线高度贴合，问题定义新，且评测覆盖面看起来广；但需要重点核对无检索设定的现实边界。

## Abstract Translation
可信性是构建在大语言模型之上的 Agentic AI 系统的核心研究挑战。为了提升信任，来自人类文本、网页内容和模型输出等不同来源的自然语言断言，通常通过检索外部知识，再由 LLM 验证断言是否忠实于检索到的证据来完成事实核验。因此，这类方法受制于检索错误和外部数据可得性，同时也没有充分利用模型内在的事实验证能力。本文提出“无检索事实核验”任务，关注对任意自然语言断言的验证，而不依赖其来源。为研究这一设定，作者构建了一个强调泛化的综合评测框架，测试在长尾知识、断言来源变化、多语言和长文本生成上的鲁棒性。在 9 个数据集、18 种方法和 3 个模型上的实验表明，基于 logit 的方法往往不如利用内部表征的方法。基于这一发现，作者提出 INTRA，该方法利用内部表征之间的交互，并在强泛化下取得了当前最优表现。更广泛地说，本文将无检索事实核验建立为一个有前景的研究方向，可作为检索式框架的补充、提升可扩展性，并支持把这类系统用作训练奖励信号或生成过程中的组件。

## Research Background And Motivation
当前面向 LLM 的事实核验主流仍是“claim 拆分 + 外部检索 + 与证据比对”，本质上更偏向验证对外部证据的忠实性。与此同时，LLM 的参数中已经编码了大量百科和常识知识，因此直接挖掘内部信号来判断 claim 真伪，成为低延迟、低外部依赖场景下值得单独研究的问题。

## Problem Framing
论文把问题明确成：给定一个来自任意来源的原子事实断言，只使用 claim 文本以及模型在处理该文本时产生的内部信号，不访问原始提示、上下文或外部知识库，输出一个真实性分数。这个设定的关键难点在于，它既不同于依赖检索证据的事实核验，也不同于只估计模型对自己生成内容置信度的不确定性方法，而是要求系统对跨来源、跨语言、长文本拆出的 claim 和长尾事实都具有泛化能力。

## Method Overview
作者先把现有无检索核验思路分成两类：一类依赖输出概率或不确定性信号，另一类依赖隐藏状态、注意力等内部表征；随后提出 INTRA。INTRA 的核心不是直接读最终 logit，而是从各层 token 级隐藏状态中提取层内真实性线索，先得到每一层的 claim-level truthfulness score，再对更有信息量的中间层分数做标准化融合，形成最终判定。整体设计强调轻量监督和跨数据集泛化，而不是为某个单一 benchmark 堆叠复杂结构。

### Method Figure
![ICLR_scheme_bright-2.drawio_page1](images/ICLR_scheme_bright-2.drawio_page1.png)

*Figure cue:* The task setting of fact-checking without retrieval. Claims from any source (human or LLMs) can be verified without having access to a knowledge base.

## Method Details
- 对每一层的 token 级隐藏状态做可学习的注意力式聚合，生成该层的序列级表示，而不是只取首/尾 token 或简单平均。
- 在每一层的序列表示上训练线性分类器，经 sigmoid 输出该层对 claim 真实性的概率，并用标准交叉熵训练，以控制模型复杂度并减少对特定模式的过拟合。
- 最终判定不是直接选单层最好结果，而是把多个层的 layer-wise truthfulness probabilities 交给额外回归器做跨层融合。
- 跨层融合时只使用中间层，不使用通常较弱的首尾层；提取文本给出的示例是 Llama 3.1-8B-Instruct 使用第 11 到 22 层。
- 为缓解不同层输出分数尺度不一致的问题，作者在跨层回归前对 layer-wise probabilities 做 quantile normalization；训练上还把训练集拆成两部分，分别拟合层内组件和最终融合器。

## Experimental Setup And Evidence
评测围绕作者提出的无检索事实核验 benchmark 展开：共 9 个数据集、18 种方法、3 个模型，主要指标为 ROC-AUC 和 PR-AUC。评测维度覆盖长尾知识、claim 来源变化（人工撰写与模型生成）、多语言、长文本生成以及 cross-model claims；提取文本明确提到的集合包括 AC-PopQA、AC-WH、AVeriTeC、X-Fact、Cities、Companies、CounterFact、UHead、Common Claims，但完整九个数据集的最终列表、样本规模和标注细节，提取文本没有充分说明。监督方法在 PopQA 的训练划分上训练，因此 PopQA 被视为 in-domain，其余数据集视为 out-of-domain；模型层面至少包括 Llama 3.1、Ministral 和 Phi-4。另有一个带检索参照 Verb+RAG，会为每个 claim 检索 top-5 search snippets，但是否存在更强、更完整的 retrieval baseline 组合，提取文本没有充分说明。

### Experiment Figure
![best_vs_mean_per_language_group_roc_auc_fin_v3_page1](images/best_vs_mean_per_language_group_roc_auc_fin_v3_page1.png)

*Figure cue:* ROC-AUC on PopQA, split into five popularity groups. The green arrow shows the percent improvement of the top method (INTRA) over the runner-up.

## Main Results And Claims
作者报告，在无检索设定下，基于内部表征的方法整体上比大多数基于 logit 或不确定性的做法更稳健；除 SP 外，不确定性方法普遍偏弱。INTRA 在平均表现上最稳定：在 Llama 3.1 上，其跨数据集 ROC-AUC 比第二名 retrieval-free 方法 Sheeps 高 2.7%，跨全部模型平均高 1.3%；文中另称在 Llama 3.1 上最高 ROC-AUC 也领先 Sheeps 0.5%。与 Verb+RAG 相比，INTRA 的 ROC-AUC 基本持平，但平均 PR-AUC 高 3%，计算时间约低 20 倍。作者还指出，Verbalized assessment 是最强无监督方法之一，但在非英语输入上拒答率可高达 58%，且计算成本显著更高；某些规则生成数据集则表现出“饱和”或污染迹象。

## Research Or Engineering Value
如果结论稳固，这篇论文的工程价值不在于“取代所有检索式核验”，而在于为事实核验提供了一个低延迟、弱外部依赖的内部 detector 设计空间。它适合离线、隐私受限、检索资源不足，或希望把真实性信号直接接入训练、解码和在线监控流程的场景；同时也为把 factuality detector 作为 reward model、reranker 或 generation-time monitor 提供了更明确的起点。

## Relation To Prior Work
相对常见的 RAG/事实核验流水线，这篇论文不再判断“声明是否被检索证据支持”，而是直接判断“声明本身是否为真”，并且输入只保留 claim 文本。相对传统不确定性估计，它不是评估模型对自己生成内容的信心，而是要求对任意来源的断言给出真实性分数。相对以往只取单层、单 token 或单一 hidden-state probe 的路线，INTRA 采用 token 级隐藏状态聚合形成层内表示，再把多个中间层的层级分数经过标准化后融合，更强调跨层内部信号的组织，而不是只依赖输出 logit、最后一层 embedding 或 retrieval evidence。

## Overall Assessment
这篇论文现在值得读，主要因为它把一个常被混在 hallucination detection 与 RAG 里的问题重新切清楚了：在没有检索时，LLM 内部到底能不能直接完成 claim verification。最值得信的是它的经验层面主结论：在跨 9 个数据集、18 种方法、3 个模型的设置里，内部表征信号普遍比纯 logit 或通用不确定性信号更可靠，而 INTRA 作为相对简单的中间层融合器，确实报告了稳定优势和不错的成本收益。最该怀疑的地方有三点：第一，强结论建立在 PopQA 训练、其余数据 OOD 的设定上，泛化是否足够接近真实部署仍需进一步验证；第二，作者自己承认部分规则数据集可能污染，说明 benchmark 本身并非完全干净；第三，对于知识过时、未知事实和必须检索的边界，现有提取文本没有给出足够细的失效分析。因此，这篇工作更像是为 retrieval-free factuality detector 建立了有价值的研究基线，而不是已经证明无检索核验可以独立承担高风险场景。

## Strengths
- 问题切分清楚：它把“无检索事实核验”从 RAG 式证据比对和一般不确定性估计中明确分离出来。
- 评测覆盖面广：不是只在单一 benchmark 上报分，而是围绕长尾、多语言、来源变化、长文本和 cross-model 泛化做系统比较。
- 经验结论可操作：论文不仅指出内部表征优于纯 logit 信号，还进一步给出中间层更有信息量的分析方向。
- INTRA 结构相对克制：层内聚合、线性判别、跨层融合三步走，目标是用简单监督结构换取更稳的泛化。

## Future Work
- 把“中间层更强”的观察做成可自适应层选择或跨模型共享的训练策略。
- 系统研究无检索 detector 与 retrieval-based verifier 的级联、回退或集成机制，明确什么时候单靠参数知识不够。
- 在多语言、长尾实体和长文本场景下做更细粒度误差分析，区分知识缺失、来源偏置和表面模式匹配。
- 把 claim 位置、生成长度等结构特征与内部表征联合建模，尤其面向 long-form generation。

## Reading Checklist
- 先看 Task Description，确认这个任务的输入边界：只看 claim 文本，不看原始提示、上下文和外部证据。
- 再看 INTRA 的层内聚合与跨层融合公式，重点核对 attention pooling、layer-wise classifier、quantile normalization 和两阶段训练。
- 重点读 layer-wise analysis，确认中间层为何更强，以及这一结论在不同模型上是否一致。
- 按 benchmark 维度读结果，而不是只看平均分：长尾知识、人工 vs 模型生成、多语言、长文本、cross-model 各自有没有明显短板。

## Core Contributions
- 把无检索事实核验明确为独立研究任务，而不是检索增强方法的弱化版。
- 提出覆盖长尾、来源变化、多语言和长文本生成的泛化评测框架。
- 提出利用内部表征交互的 INTRA，并在摘要声称的广泛比较中取得最优结果。

## Why Read It
- 直接对准 Agent 可信性这个当前高价值问题，且切入点不是常见的检索堆料。
- 方法重点放在内部表征而非 logit，值得看其是否提供了新的可解释分析入口。
- 如果想做低延迟或离线核验系统，这篇论文可能给出新的系统设计基线。

## Risks Or Limits
- 核心的“内部表征交互”机制在提取文本里只部分可见，精确公式、特征维度和实现代价提取文本没有充分说明。
- 监督式结果建立在 PopQA 训练划分之上，强泛化结论对训练源选择较敏感；如果换训练数据，结论是否保持，提取文本没有充分说明。
- 作者自己指出部分规则生成数据集可能已“饱和”或存在污染，这会削弱某些 benchmark 上高分对真实泛化能力的说服力。
- 无检索设定天然受参数知识覆盖和时效性限制；论文把它定位为检索框架的补充，但何时必须回退到检索，提取文本没有充分说明。

## Recommended For
- 做 Agent 可信性与事实核验的研究者
- 关注 LLM 内部表征与参数知识利用的研究者
- 设计低延迟审核或离线验证系统的工程师

## Keywords
- 无检索事实核验
- 参数知识
- 内部表征
- INTRA
- LLM 可信性

## Additional Figures

![layer_wise_scores_page1](images/layer_wise_scores_page1.png)

*Figure cue:* ROC-AUC performance of individual layers in the INTRA method.

![heroplot_with_ci_page1](images/heroplot_with_ci_page1.png)

*Figure cue:* ROC-AUC on PopQA, split into five popularity groups. The green arrow shows the percent improvement of the top method (INTRA) over the runner-up.

![wh_auc_relative_short_10bins_page1](images/wh_auc_relative_short_10bins_page1.png)

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
