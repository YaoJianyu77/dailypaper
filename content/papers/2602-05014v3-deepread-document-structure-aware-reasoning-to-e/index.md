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
summary: 这篇工作试图把文档原生结构变成 Agent 可操作的导航与阅读能力，以减少长文档检索中的碎片化证据读取。
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
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- 大语言模型
- Agentic Search
- RAG
- 文档结构感知
- OCR
- 长文档推理
reading_priority: high
---

# DeepRead: Document Structure-Aware Reasoning to Enhance Agentic Search

## TL;DR
这篇工作试图把文档原生结构变成 Agent 可操作的导航与阅读能力，以减少长文档检索中的碎片化证据读取。

## 中文摘要
论文关注 agentic search 在长文档场景中把内容切成无结构 chunk 后带来的上下文割裂问题。作者提出 DeepRead，用 OCR 保留的版面与层级信息构建段落级、坐标化导航，并提供 `Retrieve` 与 `ReadSection` 两类工具，让模型按“先定位、再连续阅读”的方式推理。摘要称其在四个基准上相对 Search-o1 风格基线平均提升 10.3%，但摘要后半段被截断，行为分析、代价与适用边界没有充分说明。

## Quick Facts
- Paper ID: `2602.05014v3`
- Authors: Zhanli Li, Huiwen Tian, Lvzhou Luo, Yixuan Cao, Ping Luo
- Institutions: Institution information not extracted
- Domain: Large Language Models
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-02-04T20:03:28Z
- arXiv: [abstract](https://arxiv.org/abs/2602.05014v3)
- PDF: [download](https://arxiv.org/pdf/2602.05014v3.pdf)
- Reading priority: high
- Why this priority: 它高度贴合当前对大模型与 Agent 的关注点，且针对长文档检索碎片化这一实际瓶颈提出了较具体的方法机制；同时摘要给出了可观的效果信号。优先级高，但阅读时应重点核对实验设置、效率代价与 OCR 依赖带来的边界。

## Research Background And Motivation
随着大模型工具使用能力增强，RAG 正从一次性检索转向多轮、自主式证据获取。问题在于多数 agentic search 仍把长文档当作扁平 chunk 集合处理，忽略了真实文档的层级结构、顺序逻辑和局部连续阅读需求。

## Problem Framing
这篇论文要解决的是：Agent 在长文档中如何不仅“找到相关片段”，还能够按文档原生结构进行连续、可控的阅读与推理。这个问题重要，因为仅靠扁平 chunk 检索容易打散上下文，导致证据链不完整、跨段推理不稳定，尤其影响复杂问答和文档级任务。

## Method Overview
DeepRead 的核心做法是把文档结构先验显式操作化。作者利用现代 OCR 的结构保真能力建立段落级、带坐标的导航系统，并给 LLM 配置两个互补工具：`Retrieve` 用于扫描式定位相关区域，`ReadSection` 用于在指定层级范围内按顺序连续阅读，从而诱导更接近人类阅读的“定位后细读”推理流程。

## Experimental Setup And Evidence
摘要明确给出的证据有两类：一是跨四个基准、覆盖多种文档类型的评测，声称相对 Search-o1 风格 agentic search 基线平均提升 10.3%；二是细粒度行为分析，声称能证明模型会自主采用更合理的阅读策略。但摘要没有充分说明具体任务设置、基线细节、统计显著性、代价开销，以及行为分析究竟观测到了什么。

## Research Or Engineering Value
如果结论成立，这项工作对研究和工程都有直接价值：研究上，它提供了一个把文档结构先验与 Agent 工具调用结合起来的清晰问题定义与实现路径；工程上，它可能提升企业文档检索、报告问答、表单与论文阅读等场景中的证据完整性和答案可追溯性，尤其适合长文档和层级明显的资料。

## Reading Checklist
- 段落级坐标导航对 OCR 噪声、版面复杂文档和结构识别错误有多敏感，鲁棒性如何评估？
- 性能提升主要来自结构化工具本身，还是来自额外阅读预算、工具设计细节或提示策略，消融是否充分？
- `ReadSection` 带来的上下文质量提升与延迟、token 成本之间如何权衡，在哪些文档类型上收益最明显？

## Core Contributions
- 把长文档 Agent 检索从扁平 chunk 匹配，推进到显式利用层级结构与阅读顺序的文档原生推理框架。
- 提出基于 OCR 结构保真的段落级、坐标化导航表示，为 Agent 提供可执行的文档定位接口。
- 设计 `Retrieve` 与 `ReadSection` 两种互补工具，将“扫描定位”和“连续细读”分离，形成 locate-then-read 的推理范式。

## Why Read It
- 这篇论文切中当前 Agentic RAG 的一个真实痛点：检索命中了，但证据阅读仍是碎片化的。
- 它不是简单换检索器，而是在问题定义层面强调“文档结构即推理资源”，这对长文档问答、浏览式检索和工具型 Agent 都有启发。
- 摘要给出了相对明确的增益信号，而且主题同时贴合大模型与 Agent 两条主线，值得优先核对其方法是否可迁移到实际系统。

## Risks Or Limits
- 摘要后半段被截断，行为分析结论、实验边界和失败案例信息不完整。
- 方法可能高度依赖 OCR 与文档结构解析质量，遇到扫描质量差、非规范版式或跨页复杂布局时效果未明。
- ReadSection` 这类连续阅读工具可能引入额外时延与上下文成本，摘要没有充分说明效率代价。

## Recommended For
- 关注 Agentic RAG、文档问答与长上下文推理的研究者
- 在企业文档搜索、知识库问答、报告阅读系统中做架构设计的工程师
- 想研究“结构化浏览”如何替代纯 chunk 检索范式的 LLM/Agent 从业者

## Keywords
- 大语言模型
- Agentic Search
- RAG
- 文档结构感知
- OCR
- 长文档推理

## Abstract
With the rapid advancement of tool-use capabilities in Large Language Models (LLMs), Retrieval-Augmented Generation (RAG) is shifting from static, one-shot retrieval toward autonomous, multi-turn evidence acquisition. However, existing agentic search frameworks typically treat long documents as flat collections of unstructured chunks, disregarding the native hierarchical organization and sequential logic essential for human comprehension. To bridge this gap, we introduce \textbf{DeepRead}, a structure-aware document reasoning agent designed to operationalize document-native structural priors into actionable reasoning capabilities. Leveraging the structural fidelity of modern OCR, DeepRead constructs a paragraph-level, coordinate-based navigation system and equips the LLM with two synergistic tools: \textsf{Retrieve} for scanning-aware localization, and \textsf{ReadSection} for contiguous, order-preserving reading within specific hierarchical scopes. This design elicits a human-like ``locate-then-read'' reasoning paradigm, effectively mitigating the context fragmentation inherent in traditional retrieval methods. Extensive evaluations across four benchmarks spanning diverse document types demonstrate that DeepRead outperforms Search-o1-style agentic search baselines by an average of 10.3\%. Fine-grained behavioral analysis further confirms that DeepRead autonomously adopts human-aligned reading strategies, validating the critical role of structural awareness in achieving precise document reasoning. Our code is available at https://github.com/Zhanli-Li/DeepRead.

## Recommendation Signals
- Recommendation score: 8.45
- Relevance score: 2.21
- Recency score: 3.0
- Popularity score: 2.4
- Quality score: 2.0
