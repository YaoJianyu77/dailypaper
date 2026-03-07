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

## Research Background And Motivation
面向 Agent 的可信性问题，当前事实核验流程大多依赖“检索+LLM 验证”，但这一范式会受检索误差和外部知识可得性制约。随着 LLM 参数知识本身越来越强，直接挖掘其内在事实验证能力成为值得单独研究的问题。

## Problem Framing
核心问题是：在不检索外部证据的前提下，模型能否仅凭自身参数知识，对来自人类文本、网页或模型输出的断言做出稳健核验？这关系到低延迟、低依赖和检索缺失场景下的可信性基础设施。

## Approach Snapshot
作者把“无检索事实核验”定义为独立任务，并设计强调泛化与鲁棒性的统一评测框架。在方法上，INTRA 利用内部表征之间的交互信号，而不是只看输出 logit，试图更好地提取模型内隐知识用于判别。

## Evidence Mentioned In Abstract
摘要给出的证据是跨 9 个数据集、18 种方法和 3 个模型的系统比较，并声称基于内部表征的方法整体优于基于 logit 的方法，INTRA 达到当前最优且泛化更强。具体数据集构成、评价指标、统计显著性和失败样例摘要没有充分说明。

## Research Or Engineering Value
如果结论成立，这项工作会把事实核验从“必须依赖检索”的管线扩展到“可直接调用模型内知识”的新设计空间，适合延迟敏感或检索资源受限的 Agent 与审核系统。它也为研究 LLM 内部表征究竟存了什么、能否可靠用于验证提供了更明确的实验框架。

## Reading Checklist
- INTRA 具体如何建模内部表征交互，额外计算和实现复杂度有多高？
- 在长尾事实和知识过时场景下，无检索核验与检索增强方法相比的失效边界是什么？
- 多语言与长文本设定中的提升，来自真正的知识验证能力，还是来自格式或来源模式识别？

## Core Contributions
- 把无检索事实核验明确为独立研究任务，而不是检索增强方法的弱化版。
- 提出覆盖长尾、来源变化、多语言和长文本生成的泛化评测框架。
- 提出利用内部表征交互的 INTRA，并在摘要声称的广泛比较中取得最优结果。

## Why Read It
- 直接对准 Agent 可信性这个当前高价值问题，且切入点不是常见的检索堆料。
- 方法重点放在内部表征而非 logit，值得看其是否提供了新的可解释分析入口。
- 如果想做低延迟或离线核验系统，这篇论文可能给出新的系统设计基线。

## Risks Or Limits
- 无检索设定天然受模型知识时效性和记忆偏差限制，适用边界可能很窄。
- 摘要未说明与强检索增强基线的成本效果对比，工程价值还需核对。

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
