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
summary: Diagnosing hepatic diseases accurately and interpretably is critical, yet
  it remains challenging in real-world clinical settings.
source_url: https://arxiv.org/abs/2603.05129v1
pdf_url: https://arxiv.org/pdf/2603.05129v1.pdf
scores:
  relevance: 2.09
  recency: 3.0
  popularity: 2.0
  quality: 2.0
  recommendation: 7.9
tags:
- paper-note
status: generated
updated: '2026-03-07'
reading_priority: medium
---

# MedCoRAG: Interpretable Hepatology Diagnosis via Hybrid Evidence Retrieval and Multispecialty Consensus

## TL;DR
Diagnosing hepatic diseases accurately and interpretably is critical, yet it remains challenging in real-world clinical settings.

## 中文摘要
Diagnosing hepatic diseases accurately and interpretably is critical, yet it remains challenging in real-world clinical settings.

## Quick Facts
- Paper ID: `2603.05129v1`
- Authors: Zheng Li, Jiayi Xu, Zhikai Hu, Hechang Chen, Lele Cong, Yunyun Wang, Shuchao Pang
- Domain: Agents
- Published: 2026-03-05T12:58:45Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05129v1)
- PDF: [download](https://arxiv.org/pdf/2603.05129v1.pdf)
- Reading priority: medium

## Abstract
Diagnosing hepatic diseases accurately and interpretably is critical, yet it remains challenging in real-world clinical settings. Existing AI approaches for clinical diagnosis often lack transparency, structured reasoning, and deployability. Recent efforts have leveraged large language models (LLMs), retrieval-augmented generation (RAG), and multi-agent collaboration. However, these approaches typically retrieve evidence from a single source and fail to support iterative, role-specialized deliberation grounded in structured clinical data. To address this, we propose MedCoRAG (i.e., Medical Collaborative RAG), an end-to-end framework that generates diagnostic hypotheses from standardized abnormal findings and constructs a patient-specific evidence package by jointly retrieving and pruning UMLS knowledge graph paths and clinical guidelines. It then performs Multi-Agent Collaborative Reasoning: a Router Agent dynamically dispatches Specialist Agents based on case complexity; these agents iteratively reason over the evidence and trigger targeted re-retrievals when needed, while a Generalist Agent synthesizes all deliberations into a traceable consensus diagnosis that emulates multidisciplinary consultation. Experimental results on hepatic disease cases from MIMIC-IV show that MedCoRAG outperforms existing methods and closed-source models in both diagnostic performance and reasoning interpretability.

## Recommendation Signals
- Recommendation score: 7.9
- Relevance score: 2.09
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
