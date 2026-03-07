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
summary: 把RAG、知识图谱和多Agent会诊流程揉在一起，追求可追踪的肝病诊断共识。
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
- 多专科协作
- 可解释诊断
- MIMIC-IV
reading_priority: medium
---

# MedCoRAG: Interpretable Hepatology Diagnosis via Hybrid Evidence Retrieval and Multispecialty Consensus

## TL;DR
把RAG、知识图谱和多Agent会诊流程揉在一起，追求可追踪的肝病诊断共识。

## 中文摘要
MedCoRAG先从标准化异常发现生成诊断假设，再联合检索并裁剪UMLS知识图谱路径与临床指南，形成患者特定证据包。之后由Router Agent按病例复杂度调度专科Agent开展多轮协作推理，必要时触发定向再检索，最后由Generalist Agent汇总为可追踪共识诊断。摘要称，其在MIMIC-IV肝病病例上同时提升了诊断表现与推理可解释性。

## Quick Facts
- Paper ID: `2603.05129v1`
- Authors: Zheng Li, Jiayi Xu, Zhikai Hu, Hechang Chen, Lele Cong, Yunyun Wang, Shuchao Pang
- Domain: Agents
- Published: 2026-03-05T12:58:45Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05129v1)
- PDF: [download](https://arxiv.org/pdf/2603.05129v1.pdf)
- Reading priority: medium
- Why this priority: Agent工作流设计有参考价值，但应用场景较窄，摘要也未充分展开安全与部署细节。

## Core Contributions
- 提出结合知识图谱路径与临床指南的混合证据检索方案。
- 设计Router、Specialist、Generalist协作的多Agent诊断流程，并允许定向再检索。
- 把诊断输出组织为可追踪的共识结果，强调可解释性。

## Why Read It
- 这篇展示了Agent在高风险医疗场景里如何围绕证据而不是围绕聊天来组织。
- 多专科协作和再检索机制，比单轮RAG更接近真实会诊。
- 适合参考如何把结构化知识、指南和Agent工作流连接起来。

## Risks Or Limits
- 摘要没有充分说明各Agent的责任边界、失败回退机制和成本。
- 效果验证集中在肝病场景，跨专科迁移能力仍不明确。","医疗场景对安全性要求极高，但摘要没有充分说明人工审核或审计流程。

## Recommended For
- 医疗Agent研究者
- RAG系统设计者
- 临床决策支持团队

## Keywords
- 医疗Agent
- RAG
- 知识图谱
- 多专科协作
- 可解释诊断
- MIMIC-IV

## Abstract
Diagnosing hepatic diseases accurately and interpretably is critical, yet it remains challenging in real-world clinical settings. Existing AI approaches for clinical diagnosis often lack transparency, structured reasoning, and deployability. Recent efforts have leveraged large language models (LLMs), retrieval-augmented generation (RAG), and multi-agent collaboration. However, these approaches typically retrieve evidence from a single source and fail to support iterative, role-specialized deliberation grounded in structured clinical data. To address this, we propose MedCoRAG (i.e., Medical Collaborative RAG), an end-to-end framework that generates diagnostic hypotheses from standardized abnormal findings and constructs a patient-specific evidence package by jointly retrieving and pruning UMLS knowledge graph paths and clinical guidelines. It then performs Multi-Agent Collaborative Reasoning: a Router Agent dynamically dispatches Specialist Agents based on case complexity; these agents iteratively reason over the evidence and trigger targeted re-retrievals when needed, while a Generalist Agent synthesizes all deliberations into a traceable consensus diagnosis that emulates multidisciplinary consultation. Experimental results on hepatic disease cases from MIMIC-IV show that MedCoRAG outperforms existing methods and closed-source models in both diagnostic performance and reasoning interpretability.

## Recommendation Signals
- Recommendation score: 8.13
- Relevance score: 2.6
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
