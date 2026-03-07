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
summary: 把事实核查从“检索后判定”转向直接利用LLM内部知识与表征。
source_url: https://arxiv.org/abs/2603.05471v1
pdf_url: https://arxiv.org/pdf/2603.05471v1.pdf
scores:
  relevance: 2.8
  recency: 3.0
  popularity: 2.0
  quality: 2.0
  recommendation: 8.4
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 事实核查
- 无检索验证
- 参数知识
- 内部表征
- 鲁棒性评测
reading_priority: high
---

# Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval

## TL;DR
把事实核查从“检索后判定”转向直接利用LLM内部知识与表征。

## 中文摘要
作者提出“无检索事实核查”任务，目标是不依赖外部证据，直接验证任意自然语言声明。论文同时构建了一个强调泛化能力的评测框架，覆盖长尾知识、声明来源变化、多语言和长文本生成等压力场景，并在9个数据集、18种方法、3个模型上比较方法。实验结论指向：仅看logit的做法通常不如利用内部表征的方法，进而提出INTRA作为新的表征型方案；但INTRA的具体机制在摘要中被截断，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05471v1`
- Authors: Artem Vazhentsev, Maria Marina, Daniil Moskovskiy, Sergey Pletenev, Mikhail Seleznyov, Mikhail Salnikov, Elena Tutubalina, Vasily Konovalov, Irina Nikishina, Alexander Panchenko, Viktor Moskvoretskii
- Domain: Large Language Models
- Published: 2026-03-05T18:42:51Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05471v1)
- PDF: [download](https://arxiv.org/pdf/2603.05471v1.pdf)
- Reading priority: high
- Why this priority: 问题定义新、评测框架完整，且直接关联Agent可信性与LLM内生知识利用。

## Core Contributions
- 把事实核查明确重述为无需检索的设置，强调模型内生知识的可验证性。
- 提出覆盖四类鲁棒性维度的综合评测框架，而不是只看单一核查数据集。
- 通过大规模比较指出logit-based方法的局限，并引出INTRA这一内部表征方法。

## Why Read It
- 这是Agent可信性问题中很关键的一条路线，因为它讨论模型在没有检索支撑时到底能否自证。
- 如果你在做hallucination检测或模型校准，这里的评测设计值得直接借鉴。
- 对“参数知识能否被提取为判别信号”这一问题给出了明确实验入口。

## Risks Or Limits
- 无检索设定天然受模型知识时效性和长尾覆盖限制。
- 摘要没有充分说明INTRA的实现、推理成本以及是否支持置信度校准或拒答。

## Recommended For
- 可信性研究者
- 幻觉检测研究者
- Agent评测设计者

## Keywords
- 事实核查
- 无检索验证
- 参数知识
- 内部表征
- 鲁棒性评测

## Abstract
Trustworthiness is a core research challenge for agentic AI systems built on Large Language Models (LLMs). To enhance trust, natural language claims from diverse sources, including human-written text, web content, and model outputs, are commonly checked for factuality by retrieving external knowledge and using an LLM to verify the faithfulness of claims to the retrieved evidence. As a result, such methods are constrained by retrieval errors and external data availability, while leaving the models intrinsic fact-verification capabilities largely unused. We propose the task of fact-checking without retrieval, focusing on the verification of arbitrary natural language claims, independent of their source. To study this setting, we introduce a comprehensive evaluation framework focused on generalization, testing robustness to (i) long-tail knowledge, (ii) variation in claim sources, (iii) multilinguality, and (iv) long-form generation. Across 9 datasets, 18 methods and 3 models, our experiments indicate that logit-based approaches often underperform compared to those that leverage internal model representations. Building on this finding, we introduce INTRA, a method that exploits interactions between internal representations and achieves state-of-the-art performance with strong generalization. More broadly, our work establishes fact-checking without retrieval as a promising research direction that can complement retrieval-based frameworks, improve scalability, and enable the use of such systems as reward signals during training or as components integrated into the generation process.

## Recommendation Signals
- Recommendation score: 8.4
- Relevance score: 2.8
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
