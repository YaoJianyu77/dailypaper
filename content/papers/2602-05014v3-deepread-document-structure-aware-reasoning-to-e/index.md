---
paper_id: 2602.05014v3
title: 'DeepRead: Document Structure-Aware Reasoning to Enhance Agentic Search'
authors:
- Zhanli Li
- Huiwen Tian
- Lvzhou Luo
- Yixuan Cao
- Ping Luo
domain: Large Language Models
slug: 2602-05014v3-deepread-document-structure-aware-reasoning-to-e
published: '2026-02-04T20:03:28Z'
summary: 把文档层级结构和版面坐标变成 Agent 可调用的检索与阅读动作，直指长文档 agentic search 的证据碎片化问题。
source_url: https://arxiv.org/abs/2602.05014v3
pdf_url: https://arxiv.org/pdf/2602.05014v3.pdf
scores:
  relevance: 2.21
  recency: 3.0
  popularity: 2.4
  quality: 2.0
  recommendation: 8.45
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- Agentic Search
- RAG
- 长文档推理
- 文档结构感知
- OCR
- 工具使用
reading_priority: high
---

# DeepRead: Document Structure-Aware Reasoning to Enhance Agentic Search

## TL;DR
把文档层级结构和版面坐标变成 Agent 可调用的检索与阅读动作，直指长文档 agentic search 的证据碎片化问题。

## 中文摘要
这篇工作针对长文档 agentic search 把文档当作扁平 chunk 集合处理的问题，引入结构感知的文档推理代理 DeepRead。其核心是基于 OCR 结构保真度构建段落级、坐标驱动的导航系统，并提供 `Retrieve` 与 `ReadSection` 两个协同工具，诱导模型执行“先定位、后细读”的阅读流程。摘要声称在四个覆盖不同文档类型的基准上，相比 Search-o1 风格基线平均提升 10.3%，但实验设置、成本代价、失败案例和行为分析细节摘要没有充分说明。

## Quick Facts
- Paper ID: `2602.05014v3`
- Authors: Zhanli Li, Huiwen Tian, Lvzhou Luo, Yixuan Cao, Ping Luo
- Domain: Large Language Models
- Published: 2026-02-04T20:03:28Z
- arXiv: [abstract](https://arxiv.org/abs/2602.05014v3)
- PDF: [download](https://arxiv.org/pdf/2602.05014v3.pdf)
- Reading priority: high
- Why this priority: 方向与当前大模型/Agent 文档检索高度贴合，方法机制清晰且工程相关性强；摘要还给出跨四个基准的正向结果。尽管成本、鲁棒性和实验细节仍需核对，但作为“结构感知 Agentic Search”范式样本，这篇值得优先读。

## Research Background And Motivation
随着大模型工具使用能力增强，RAG 正从一次性检索转向多轮、自主的证据获取。问题在于现有 agentic search 常把长文档切成无结构碎片，丢掉了层级组织和顺序逻辑，而这些恰恰是人类理解文档时依赖的关键信号。

## Problem Framing
论文要解决的问题是：如何让大模型在长文档中不仅能找到相关内容，还能沿着文档原生结构进行连续、顺序一致的阅读与推理，而不是在碎片化 chunk 之间跳转。这个问题重要，因为许多文档问答与检索错误并非来自模型不会推理，而是证据定位和阅读过程破坏了文档结构。

## Method Overview
方法上，DeepRead把现代 OCR 提供的结构信息转成段落级、带坐标的导航表示，并把这种结构先验暴露为两个工具：`Retrieve` 用于基于扫描/版面信息定位相关区域，`ReadSection` 用于在指定层级范围内执行连续、保序的阅读。整体上，它不是单纯改检索打分，而是把“文档原生结构”嵌入 agent 的行动空间，让模型更像人一样先找位置，再顺着局部上下文读。

## Experimental Setup And Evidence
摘要给出的主要证据是：在四个覆盖不同文档类型的基准上，DeepRead 相比 Search-o1 风格的 agentic search 基线平均提升 10.3%。摘要还提到有细粒度行为分析，称系统会自主采用“先定位再阅读”的策略。但摘要末尾被截断，具体实验任务、统计显著性、计算开销、错误案例以及行为分析细节都没有充分说明。

## Research Or Engineering Value
如果这套思路成立，工程上可直接用于 PDF、报告、企业知识库等长文档场景，提升 Agent/RAG 的证据定位质量和连续阅读能力，减少因切块过细导致的上下文断裂。研究上，它把“文档结构先验如何进入 Agent 推理闭环”变成了一个清晰、可操作的设计方向。

## Reading Checklist
- 段落级坐标导航是如何从 OCR 结果构建的，遇到版面复杂、结构识别错误或扫描质量差的文档时是否稳健？
- `Retrieve` 与 `ReadSection` 的调用策略如何学习或触发，和标准 chunk-based agent 相比会增加多少延迟与 token 成本？
- 四个基准分别覆盖哪些文档类型与任务，10.3% 的平均提升是否稳定存在于各类文档，而不是由少数任务拉高？

## Core Contributions
- 提出一个面向长文档 agentic search 的结构感知推理代理，把文档原生层级与顺序逻辑显式纳入行动空间。
- 构建段落级、坐标驱动的导航表示，并设计 `Retrieve` 与 `ReadSection` 两个互补工具来支持“定位+连续阅读”。
- 摘要报告了跨四个基准的平均性能提升，并用行为分析尝试证明该设计确实改变了代理的阅读策略。

## Why Read It
- 这篇工作切中的不是通用检索调参，而是 Agent 读长文档时最核心的失真来源：结构被扁平化后，证据获取流程本身就错了。
- 方法点足够清楚且工程可落地，尤其适合做文档问答、企业搜索、PDF Agent、结构化 RAG 的团队参考。
- 摘要给出了跨基准的正向结果，说明“把结构先验做成工具”可能比继续堆更细的 chunk 检索更值得关注。

## Risks Or Limits
- 方法效果可能强依赖 OCR 的结构保真度；一旦文档结构抽取不准，后续导航与阅读可能一起失效。
- 摘要只给出平均提升，未充分说明与哪些更强基线比较，也没有交代成本、延迟和长上下文替代方案的对比。

## Recommended For
- 做 Agentic RAG、文档问答、企业搜索系统的研究者和工程师
- 关注长文档推理、工具使用、检索与阅读耦合设计的人
- 想看结构信息如何进入 LLM Agent 行动空间的读者

## Keywords
- Agentic Search
- RAG
- 长文档推理
- 文档结构感知
- OCR
- 工具使用

## Abstract
With the rapid advancement of tool-use capabilities in Large Language Models (LLMs), Retrieval-Augmented Generation (RAG) is shifting from static, one-shot retrieval toward autonomous, multi-turn evidence acquisition. However, existing agentic search frameworks typically treat long documents as flat collections of unstructured chunks, disregarding the native hierarchical organization and sequential logic essential for human comprehension. To bridge this gap, we introduce \textbf{DeepRead}, a structure-aware document reasoning agent designed to operationalize document-native structural priors into actionable reasoning capabilities. Leveraging the structural fidelity of modern OCR, DeepRead constructs a paragraph-level, coordinate-based navigation system and equips the LLM with two synergistic tools: \textsf{Retrieve} for scanning-aware localization, and \textsf{ReadSection} for contiguous, order-preserving reading within specific hierarchical scopes. This design elicits a human-like ``locate-then-read'' reasoning paradigm, effectively mitigating the context fragmentation inherent in traditional retrieval methods. Extensive evaluations across four benchmarks spanning diverse document types demonstrate that DeepRead outperforms Search-o1-style agentic search baselines by an average of 10.3\%. Fine-grained behavioral analysis further confirms that DeepRead autonomously adopts human-aligned reading strategies, validating the critical role of structural awareness in achieving precise document reasoning. Our code is available at https://github.com/Zhanli-Li/DeepRead.

## Recommendation Signals
- Recommendation score: 8.45
- Relevance score: 2.21
- Recency score: 3.0
- Popularity score: 2.4
- Quality score: 2.0
