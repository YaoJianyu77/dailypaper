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
summary: 把事实核验的重心从外部检索转向模型内部表征，探索“无检索核验”作为独立任务。
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
- 事实核验
- 无检索验证
- 参数知识
- 内部表征
- INTRA
- 泛化评测
reading_priority: high
---

# Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval

## TL;DR
把事实核验的重心从外部检索转向模型内部表征，探索“无检索核验”作为独立任务。

## 中文摘要
论文正式提出“无检索事实核验”任务，目标是在不依赖外部证据检索的前提下验证任意自然语言声明。作者还构建了覆盖长尾知识、来源变化、多语言和长文本生成鲁棒性的综合评测框架。摘要称，基于内部表征的方法普遍优于logit型方法，其提出的INTRA进一步取得了更强的泛化与最优性能。

## Quick Facts
- Paper ID: `2603.05471v1`
- Authors: Artem Vazhentsev, Maria Marina, Daniil Moskovskiy, Sergey Pletenev, Mikhail Seleznyov, Mikhail Salnikov, Elena Tutubalina, Vasily Konovalov, Irina Nikishina, Alexander Panchenko, Viktor Moskvoretskii
- Domain: Large Language Models
- Published: 2026-03-05T18:42:51Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05471v1)
- PDF: [download](https://arxiv.org/pdf/2603.05471v1.pdf)
- Reading priority: high
- Why this priority: 紧扣可信LLM与Agent的核心问题，而且问题设定和评测框架本身就值得优先读。

## Core Contributions
- 把无检索事实核验定义为独立研究任务。
- 构建面向长尾知识、来源变化、多语言和长文本的综合评测框架。
- 提出利用内部表征交互的INTRA方法，并报告更强的泛化表现。

## Why Read It
- 适合判断LLM内部参数知识到底能否承担一部分可信性校验。
- 对Agent系统很关键，因为检索链路并非总是可用且常有误检。
- 论文不只提方法，还把泛化维度本身设计成研究对象。

## Risks Or Limits
- 无检索设定天然受限于参数知识的新鲜度和覆盖范围。
- 摘要没有充分说明在最新事实、冲突事实和高争议陈述上的失败模式。","如果将其作为训练奖励或生成内环组件，误判成本如何控制，摘要没有充分说明。

## Recommended For
- 可信AI研究者
- 事实核验与RAG研究者
- Agent系统设计者

## Keywords
- 事实核验
- 无检索验证
- 参数知识
- 内部表征
- INTRA
- 泛化评测

## Abstract
Trustworthiness is a core research challenge for agentic AI systems built on Large Language Models (LLMs). To enhance trust, natural language claims from diverse sources, including human-written text, web content, and model outputs, are commonly checked for factuality by retrieving external knowledge and using an LLM to verify the faithfulness of claims to the retrieved evidence. As a result, such methods are constrained by retrieval errors and external data availability, while leaving the models intrinsic fact-verification capabilities largely unused. We propose the task of fact-checking without retrieval, focusing on the verification of arbitrary natural language claims, independent of their source. To study this setting, we introduce a comprehensive evaluation framework focused on generalization, testing robustness to (i) long-tail knowledge, (ii) variation in claim sources, (iii) multilinguality, and (iv) long-form generation. Across 9 datasets, 18 methods and 3 models, our experiments indicate that logit-based approaches often underperform compared to those that leverage internal model representations. Building on this finding, we introduce INTRA, a method that exploits interactions between internal representations and achieves state-of-the-art performance with strong generalization. More broadly, our work establishes fact-checking without retrieval as a promising research direction that can complement retrieval-based frameworks, improve scalability, and enable the use of such systems as reward signals during training or as components integrated into the generation process.

## Recommendation Signals
- Recommendation score: 8.4
- Relevance score: 2.8
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
