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
summary: 这篇论文的核心看点是尝试不用检索，只靠模型参数知识做事实核查。
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
- 大语言模型
- 事实核查
- 参数知识
- 无检索
- 可信性
reading_priority: high
image_count: 5
---

# Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval

## TL;DR
这篇论文的核心看点是尝试不用检索，只靠模型参数知识做事实核查。

## 中文摘要
论文瞄准事实核查中长期依赖“检索加验证”的范式，提出利用LLM参数知识在无检索条件下做核查。这个方向值得现在读，因为Agent系统的可信性越来越受限于检索错误、外部数据可用性和系统复杂度。摘要明确交代了问题动机，但未在给定内容中充分说明具体核查流程、适用事实范围以及与检索式方法的效果差距。

## Quick Facts
- Paper ID: `2603.05471v1`
- Authors: Artem Vazhentsev, Maria Marina, Daniil Moskovskiy, Sergey Pletenev, Mikhail Seleznyov, Mikhail Salnikov, Elena Tutubalina, Vasily Konovalov, Irina Nikishina, Alexander Panchenko, Viktor Moskvoretskii
- Domain: Large Language Models
- Published: 2026-03-05T18:42:51Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05471v1)
- PDF: [download](https://arxiv.org/pdf/2603.05471v1.pdf)
- Reading priority: high
- Why this priority: 它命中LLM与Agent可靠性的核心议题，问题定义有明显新意；优先级高，但需要重点核对无检索条件下的边界和误判成本。

## Problem Framing
问题是现有事实核查通常依赖外部检索，容易受到检索错误、知识覆盖不足和外部数据可用性的限制，从而影响Agent系统可信性。

## Approach Snapshot
方法是利用LLM内部的参数化知识直接进行事实核查，尽量绕开检索步骤；但摘要没有充分说明它如何判断真伪、如何处理知识时效性，以及是否有不确定性估计。

## Evidence Mentioned In Abstract
摘要给出的证据主要是对现有检索式核查局限的论证，以及提出无检索核查这一替代方向；在已提供内容里，没有看到数据集、对比对象、定量结果或失败案例，摘要没有充分说明。

## Reading Checklist
- 无检索核查到底输出什么：真假标签、解释，还是证据归因？
- 对于参数知识中不存在或过时的事实，方法如何避免自信地给出错误判断？
- 与检索增强方法相比，它在时效性强、长尾或专业领域事实上会退化多少？

## Core Contributions
- 把事实核查目标从“依赖外部检索”改写为“直接利用参数知识”。
- 把可信性问题聚焦到检索依赖本身，而不是仅优化验证提示词。
- 为Agent系统中低延迟、低外部依赖的核查路径提供了研究切口。

## Why Read It
- 这是和Agent可信性直接相关的问题，应用价值比单纯提高基准分更高。
- 如果方法成立，会影响事实核查、回答自检和生成后验证三类工作流。
- 它有机会澄清LLM参数知识到底能承担多少验证职责。

## Risks Or Limits
- 参数知识天然有时效性和覆盖边界，无检索方案可能在动态事实下失效。
- 如果没有校准或拒答机制，方法可能把幻觉包装成核查结论。

## Recommended For
- 关注Agent可信性、事实核查与LLM可靠性的研究者
- 在做低延迟验证链路或回答后自检系统的工程师

## Keywords
- 大语言模型
- 事实核查
- 参数知识
- 无检索
- 可信性

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
