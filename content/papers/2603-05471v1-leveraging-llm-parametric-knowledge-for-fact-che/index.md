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
可信性是基于大语言模型构建的 Agent 系统中的核心研究挑战。为了提升可信性，来自人类文本、网页内容和模型输出等不同来源的自然语言断言，通常会先检索外部知识，再用大语言模型验证这些断言是否忠实于检索到的证据。因此，这类方法会受限于检索错误和外部数据可得性，同时模型自身内在的事实核验能力并没有被充分利用。本文提出“无检索事实核验”任务，目标是在不依赖外部检索的情况下验证任意自然语言断言。为研究这一设定，作者构建了一个强调泛化能力的综合评测框架，重点测试四类鲁棒性：(i) 长尾知识，(ii) 断言来源变化，(iii) 多语言，(iv) 长文本生成。基于 9 个数据集、18 种方法和 3 个模型的实验表明，基于 logit 的方法通常不如利用模型内部表征的方法。基于这一发现，作者提出 INTRA，通过利用内部表征之间的交互来达到最优性能并展现较强泛化。更广泛地说，这项工作把无检索事实核验确立为一个有前景的研究方向，它可与检索式框架互补、提升可扩展性，并支持将此类系统作为训练奖励信号或集成到生成过程中。

## Research Background And Motivation
当前事实核验和幻觉检测主流仍是“检索外部证据，再判断是否一致”的流水线，但这种路线会引入额外延迟、受检索质量影响，并且默认外部证据比模型参数知识更可靠。随着大模型在参数中已经编码了大量百科和常识知识，直接评估并利用其内在事实判断能力，成为面向 Agent 可信性的一个自然下一步。

## Problem Framing
论文要回答的是：在完全不访问外部证据、也不依赖原始提示词和完整生成上下文的前提下，能否仅根据一个原子事实断言的文本本身，以及模型处理该断言时产生的内部信号，估计其真实性？这个问题重要，因为它对应低延迟、弱外部依赖、甚至训练期可内嵌的事实性判别能力，而不只是传统 RAG 验证链路的简化版。

## Method Overview
方法上，论文先把现有无检索核验方法分成基于输出概率/logit 的不确定性方法与基于内部表征的监督方法，再提出 INTRA 作为统一的内部表征路线。INTRA 不直接依赖某一层、某一 token 或单一不确定性分数，而是先在每一层对整条 claim 聚合出序列表征，分别得到层级真实性分数，再对中间层的层级分数做归一化与回归融合，从而利用“层间+表征交互”提升泛化。

## Method Details
- INTRA 先对每一层的 token hidden states 做可学习加权聚合，形成 sequence-level embedding；权重通过 softmax 归一化，因此不是简单平均或只取首尾 token。
- 在每一层上，模型单独训练一个线性分类器输出该层的 truthfulness probability，并使用标准交叉熵训练，刻意保持头部简单以减少对特定模式的过拟合。
- 最终判别不直接使用某一层，而是只取模型中间层的层级概率做融合；文中明确认为首层和末层通常较弱，因此使用从前 1/3 到后 2/3 之间的中间层区间。
- 为避免不同层输出概率分布不一致影响融合效果，INTRA 在回归前先对层级概率做 quantile normalization，再训练回归器得到最终 truthfulness score。
- 训练被拆成两段：先用一部分训练数据拟合各层聚合与分类参数，再用另一部分训练回归融合器；这种两阶段设计旨在降低层间融合对训练分布的耦合。

## Experimental Setup And Evidence
实验围绕作者定义的“无检索事实核验”设定展开：输入是任意来源的原子事实断言，模型只能基于 claim 文本本身及其内部信号打分，不能访问外部知识。评测覆盖 9 个数据集、18 种方法和 3 个模型，重点考察长尾知识、人工与模型生成来源差异、多语言、长文本生成以及跨模型 claim 等泛化维度。文中把 PopQA 视为有监督训练的 in-domain 数据，其余数据集视为 out-of-domain；主要指标是 ROC-AUC 和 PR-AUC。提取文本还说明了一个检索增强对照 `Verb + RAG`，以及 UHead 只对 Llama 3.1 提供了预训练开源检查点。

## Main Results And Claims
提取文本支持的主要结论是：1）总体上，利用内部表征的方法比基于 logit/不确定性的办法更稳健，后者除 SP 外普遍偏弱；2）INTRA 在跨 9 个数据集的平均表现上达到最优，并表现出更一致的泛化，而不是只在单一基准上强；3）在 Llama 3.1 上，INTRA 的 ROC-AUC 比第二名 Sheeps 高 0.5%，跨数据集平均 ROC-AUC 相对第二名 retrieval-free 方法 Sheeps 高 2.7%，跨全部模型平均高 1.3%；4）INTRA 的 ROC-AUC 与 Verb+RAG 持平，但平均 PR-AUC 高 3%，且计算时间约少 20 倍；5）Verb 是最强的无监督方法之一，但计算成本显著更高，并且在非英语输入上有很高拒答率，最高可到 58%；6）一些方法在特定数据集上强，但跨场景泛化差，文中还指出规则生成数据集可能已接近饱和，存在污染或针对性过拟合迹象。

## Research Or Engineering Value
如果这个方向站得住，它对工程上最直接的价值是提供一种低外部依赖、低延迟的 claim verifier，可作为 RAG 核验链路的补充，或用于没有稳定检索条件的场景。对研究上，它也有两个清晰用途：一是把“大模型内部到底有没有可稳定提取的真实性信号”变成可系统评测的问题；二是为 truthfulness-oriented reward model 或生成过程中的在线监控模块提供候选技术路线。

## Relation To Prior Work
相对常见的 RAG 式事实核验，这篇论文不再验证“claim 是否被检索证据支持”，而是直接判定 claim 本身是否为真，且完全不依赖外部检索。相对传统不确定性估计，它也不是评估模型对自己生成内容的信心，而是评估任意来源断言的真实性。相对已有 probe/hidden-state 方法，INTRA 的差异不在于再找一个“最佳单层”或“最佳 token”，而是在保持判别头简单的前提下，用可学习序列聚合、分层打分、中间层选择和归一化后的层间回归，把多层内部信号整合起来，重点追求跨数据集泛化而不是单任务适配。

## Overall Assessment
这篇论文最值得信的是它把“无检索事实核验”定义成了一个独立且现实的问题，并且从实验叙述看，作者没有只追求单一基准分数，而是在泛化维度上做了较系统的比较；“内部表征优于纯 logit 信号”这个结论也与方法设计和结果描述相互呼应。最该怀疑的地方有两点：第一，这条路线受参数知识时效性和覆盖度的硬约束，能否替代检索很可疑，更像补充模块；第二，提取文本虽然给出平均优势和效率收益，但对失败模式、训练成本、数据污染影响和与强检索系统的真实工程对比说明仍不充分，因此应把它视为一个方向性很强的研究起点，而不是已定型的通用解决方案。

## Strengths
- 问题定义清楚，把“无检索事实核验”从传统检索式 faithful verification 和常见 uncertainty estimation 中分离出来，研究对象更明确。
- 评测设计强调泛化而非单基准最优，覆盖长尾、多语言、长文本、来源变化和跨模型 claim，比较接近真实部署中的失配场景。
- 方法本身相对克制，没有引入很重的架构修改，而是围绕层级表征聚合、分层判别和中间层融合做设计，便于分析内部知识信号。
- 实验结论不只说 INTRA 更强，也给出一个更广泛的经验判断：内部表征路线通常优于直接看 logit/概率的不确定性信号。

## Future Work
- 核查在知识过时、真实世界新近事件和极长尾实体上的失效边界，明确无检索路线与检索增强路线各自适用范围。
- 进一步分析中间层为何最有效，以及不同层在不同语言、不同 claim 类型上的分工是否稳定。
- 把 claim 位置、生成长度等结构信息更系统地纳入长文本场景中的真实性检测。
- 研究如何将无检索判别器与检索式核验组合，而不是二选一，以兼顾速度、时效性和可解释性。

## Reading Checklist
- 先看任务定义：作者如何严格限制输入，只允许 claim 文本和内部信号，而不允许提示词、完整生成或外部证据。
- 重点看 INTRA 的具体实现：序列聚合用的参数化形式、层级分类器输入、quantile normalization 的细节，以及两阶段训练如何避免信息泄漏。
- 检查 9 个数据集的构成与拆分，尤其是 PopQA 训练、其余数据集 OOD 的设置是否足够公平。
- 对照 Verb、Verb+RAG、Sheeps、UHead 等强基线，确认 INTRA 的优势到底来自表征质量、训练目标，还是 benchmark 偏好。

## Core Contributions
- 把无检索事实核验明确为独立研究任务，而不是检索增强方法的弱化版。
- 提出覆盖长尾、来源变化、多语言和长文本生成的泛化评测框架。
- 提出利用内部表征交互的 INTRA，并在摘要声称的广泛比较中取得最优结果。

## Why Read It
- 直接对准 Agent 可信性这个当前高价值问题，且切入点不是常见的检索堆料。
- 方法重点放在内部表征而非 logit，值得看其是否提供了新的可解释分析入口。
- 如果想做低延迟或离线核验系统，这篇论文可能给出新的系统设计基线。

## Risks Or Limits
- 该设定天然受模型参数知识的时效性、覆盖面和记忆偏差限制；遇到知识过时或模型从未见过的事实时，上限可能明显受约束。
- INTRA 依然是有监督方法，并以 PopQA 训练后再测试其他数据集；虽然论文强调 OOD 泛化，但训练分布对结果的影响仍需仔细看正文和附录。
- 提取文本没有充分说明 INTRA 的额外训练成本、特征维度、部署内存开销，以及与更强检索系统的完整成本收益比较。
- 作者自己指出部分规则生成数据集可能存在污染或过拟合风险，这意味着某些 benchmark 上的高分未必能直接转化为真实世界稳健性。

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

## Figures
![ICLR_scheme_bright-2.drawio_page1](images/ICLR_scheme_bright-2.drawio_page1.png)

![best_vs_mean_per_language_group_roc_auc_fin_v3_page1](images/best_vs_mean_per_language_group_roc_auc_fin_v3_page1.png)

![heroplot_with_ci_page1](images/heroplot_with_ci_page1.png)

![layer_wise_scores_page1](images/layer_wise_scores_page1.png)

![wh_auc_relative_medium_10bins_page1](images/wh_auc_relative_medium_10bins_page1.png)

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
