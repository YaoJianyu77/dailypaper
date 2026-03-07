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
summary: 这篇工作把事实核查从依赖外部检索的流水线，推进到直接调用 LLM 参数知识的设定。
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
- 事实核查
- 参数知识
- 无检索
- LLM
- 可信性
reading_priority: high
---

# Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval

## TL;DR
这篇工作把事实核查从依赖外部检索的流水线，推进到直接调用 LLM 参数知识的设定。

## 中文摘要
论文关注不依赖外部检索的事实核查，核心方向是直接利用 LLM 的参数知识判断自然语言陈述的真实性。这个问题对 agent 系统很现实，因为检索错误、外部数据缺失和额外链路复杂度本身就是脆弱点。摘要没有充分说明具体验证框架、置信度校准方式，以及对时效性知识和长尾事实的处理。

## Quick Facts
- Paper ID: `2603.05471v1`
- Authors: Artem Vazhentsev, Maria Marina, Daniil Moskovskiy, Sergey Pletenev, Mikhail Seleznyov, Mikhail Salnikov, Elena Tutubalina, Vasily Konovalov, Irina Nikishina, Alexander Panchenko, Viktor Moskvoretskii
- Domain: Large Language Models
- Published: 2026-03-05T18:42:51Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05471v1)
- PDF: [download](https://arxiv.org/pdf/2603.05471v1.pdf)
- Reading priority: high
- Why this priority: 直接命中 agent 可信性瓶颈，问题设定对当前 LLM 系统很重要，即使摘要细节不足也值得优先读。

## Core Contributions
- 把事实核查重新定义为参数知识利用问题，而不是默认检索先行。
- 把 agent 可信性中的检索误差与外部数据可用性限制直接纳入问题定义。
- 面向来自人类文本、网页内容和模型输出的陈述统一讨论核查场景。

## Why Read It
- 很多 agent 流水线把检索视为必需组件，这篇工作直接挑战这一前提。
- 如果无检索方案可用，就有机会减少外部依赖和检索误差传播。
- 它对事实核查、输出校验和可信性评测都有直接相关性。

## Risks Or Limits
- 参数知识会过时，摘要没有充分说明时间敏感事实如何处理。
- 对长尾、专业或争议性陈述的覆盖边界未说明。','摘要没有充分说明如何做置信度校准与错误分析。

## Recommended For
- 做 agent 可信性和校验链路的研究者
- 事实核查与幻觉检测方向的工程师
- 关注检索增强替代路径的团队

## Keywords
- 事实核查
- 参数知识
- 无检索
- LLM
- 可信性

## Abstract
Trustworthiness is a core research challenge for agentic AI systems built on Large Language Models (LLMs). To enhance trust, natural language claims from diverse sources, including human-written text, web content, and model outputs, are commonly checked for factuality by retrieving external knowledge and using an LLM to verify the faithfulness of claims to the retrieved evidence. As a result, such methods are constrained by retrieval errors and external data availability, while leaving the models intrinsic fact-verification capabilities largely unused. We propose the task of fact-checking without retrieval, focusing on the verification of arbitrary natural language claims, independent of their source. To study this setting, we introduce a comprehensive evaluation framework focused on generalization, testing robustness to (i) long-tail knowledge, (ii) variation in claim sources, (iii) multilinguality, and (iv) long-form generation. Across 9 datasets, 18 methods and 3 models, our experiments indicate that logit-based approaches often underperform compared to those that leverage internal model representations. Building on this finding, we introduce INTRA, a method that exploits interactions between internal representations and achieves state-of-the-art performance with strong generalization. More broadly, our work establishes fact-checking without retrieval as a promising research direction that can complement retrieval-based frameworks, improve scalability, and enable the use of such systems as reward signals during training or as components integrated into the generation process.

## Recommendation Signals
- Recommendation score: 8.73
- Relevance score: 2.6
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
