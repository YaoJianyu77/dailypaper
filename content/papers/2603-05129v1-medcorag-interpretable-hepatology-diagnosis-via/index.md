---
paper_id: 2603.05129v1
title: 'MedCoRAG: Interpretable Hepatology Diagnosis via Hybrid Evidence Retrieval
  and Multispecialty Consensus'
authors:
- Zheng Li
- Jiayi Xu
- Zhikai Hu
- Hechang Chen
- Lele Cong
- Yunyun Wang
- Shuchao Pang
domain: Agents
slug: 2603-05129v1-medcorag-interpretable-hepatology-diagnosis-via
published: '2026-03-05T12:58:45Z'
summary: 把混合证据检索和多专科协作代理结合到肝病诊断里。
source_url: https://arxiv.org/abs/2603.05129v1
pdf_url: https://arxiv.org/pdf/2603.05129v1.pdf
scores:
  relevance: 2.6
  recency: 3.0
  popularity: 2.0
  quality: 2.0
  recommendation: 8.13
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 医疗Agent
- RAG
- 知识图谱
- 临床指南
- 可解释诊断
reading_priority: medium
---

# MedCoRAG: Interpretable Hepatology Diagnosis via Hybrid Evidence Retrieval and Multispecialty Consensus

## TL;DR
把混合证据检索和多专科协作代理结合到肝病诊断里。

## 中文摘要
MedCoRAG面向肝病可解释诊断，先从标准化异常发现生成诊断假设，再联合检索并裁剪UMLS知识图谱路径与临床指南，形成患者级证据包。随后系统通过Router Agent调度Specialist Agents进行迭代推理与必要的再检索，最后由Generalist Agent综合为可追踪的共识诊断。摘要强调其透明性和结构化协作，但实验结果、诊断范围与错误分析部分被截断，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05129v1`
- Authors: Zheng Li, Jiayi Xu, Zhikai Hu, Hechang Chen, Lele Cong, Yunyun Wang, Shuchao Pang
- Domain: Agents
- Published: 2026-03-05T12:58:45Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05129v1)
- PDF: [download](https://arxiv.org/pdf/2603.05129v1.pdf)
- Reading priority: medium
- Why this priority: Agent结构完整，但应用较垂直，优先级略低于更通用的方法与系统论文。

## Core Contributions
- 把知识图谱路径与临床指南联合纳入证据构建，而非单一来源RAG。
- 设计带Router、Specialist、Generalist分工的多Agent协作诊断流程，并允许推理中触发针对性再检索。
- 把输入规范化为标准化异常发现，提升临床结构化推理的可部署性。

## Why Read It
- 这是Agent系统在高风险医疗场景中的一个相对完整闭环：检索、协作、再检索和共识生成。
- 对需要可追踪推理链和多角色分工的垂直应用有参考意义。

## Risks Or Limits
- 医疗诊断是高风险场景，摘要没有充分说明安全边界、人工审核位置和失败模式。
- 方法局限于肝病还是可迁移到更广泛临床专科，摘要未说明。

## Recommended For
- 医疗Agent研究者
- 临床决策支持团队
- 多Agent RAG设计者

## Keywords
- 医疗Agent
- RAG
- 知识图谱
- 临床指南
- 可解释诊断

## Abstract
Diagnosing hepatic diseases accurately and interpretably is critical, yet it remains challenging in real-world clinical settings. Existing AI approaches for clinical diagnosis often lack transparency, structured reasoning, and deployability. Recent efforts have leveraged large language models (LLMs), retrieval-augmented generation (RAG), and multi-agent collaboration. However, these approaches typically retrieve evidence from a single source and fail to support iterative, role-specialized deliberation grounded in structured clinical data. To address this, we propose MedCoRAG (i.e., Medical Collaborative RAG), an end-to-end framework that generates diagnostic hypotheses from standardized abnormal findings and constructs a patient-specific evidence package by jointly retrieving and pruning UMLS knowledge graph paths and clinical guidelines. It then performs Multi-Agent Collaborative Reasoning: a Router Agent dynamically dispatches Specialist Agents based on case complexity; these agents iteratively reason over the evidence and trigger targeted re-retrievals when needed, while a Generalist Agent synthesizes all deliberations into a traceable consensus diagnosis that emulates multidisciplinary consultation. Experimental results on hepatic disease cases from MIMIC-IV show that MedCoRAG outperforms existing methods and closed-source models in both diagnostic performance and reasoning interpretability.

## Recommendation Signals
- Recommendation score: 8.13
- Relevance score: 2.6
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
