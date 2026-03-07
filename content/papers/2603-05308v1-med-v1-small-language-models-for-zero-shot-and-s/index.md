---
paper_id: 2603.05308v1
title: 'Med-V1: Small Language Models for Zero-shot and Scalable Biomedical Evidence
  Attribution'
authors:
- Qiao Jin
- Yin Fang
- Lauren He
- Yifan Yang
- Guangzhi Xiong
- Zhizheng Wang
- Nicholas Wan
- Joey Chan
- Donald C. Comeau
- Robert Leaman
- Charalampos S. Floudas
- Aidong Zhang
- Michael F. Chiang
- Yifan Peng
- Zhiyong Lu
domain: Large Language Models
slug: 2603-05308v1-med-v1-small-language-models-for-zero-shot-and-s
published: '2026-03-05T15:48:43Z'
summary: 这篇工作尝试用小模型承接高价值的证据归因任务，而不是继续依赖昂贵前沿模型。
source_url: https://arxiv.org/abs/2603.05308v1
pdf_url: https://arxiv.org/pdf/2603.05308v1.pdf
scores:
  relevance: 2.21
  recency: 3.0
  popularity: 1.8
  quality: 1.8
  recommendation: 7.95
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 小语言模型
- 证据归因
- 生物医学
- 零样本
- 合成数据
reading_priority: medium
---

# Med-V1: Small Language Models for Zero-shot and Scalable Biomedical Evidence Attribution

## TL;DR
这篇工作尝试用小模型承接高价值的证据归因任务，而不是继续依赖昂贵前沿模型。

## 中文摘要
论文把生物医学证据归因做成可规模化的小模型方案，目标是在零样本设置下替代高成本前沿模型。亮点不是继续堆大模型，而是用高质量合成数据把高价值任务压缩到 30 亿参数级别。摘要没有充分说明合成数据的构造与质量控制、证据归因判定标准，以及跨领域泛化能力。

## Quick Facts
- Paper ID: `2603.05308v1`
- Authors: Qiao Jin, Yin Fang, Lauren He, Yifan Yang, Guangzhi Xiong, Zhizheng Wang, Nicholas Wan, Joey Chan, Donald C. Comeau, Robert Leaman, Charalampos S. Floudas, Aidong Zhang, Michael F. Chiang, Yifan Peng, Zhiyong Lu
- Domain: Large Language Models
- Published: 2026-03-05T15:48:43Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05308v1)
- PDF: [download](https://arxiv.org/pdf/2603.05308v1.pdf)
- Reading priority: medium
- Why this priority: 任务重要且与幻觉检测相关，但场景偏生物医学垂直，更适合作为方法迁移案例阅读。

## Core Contributions
- 把生物医学证据归因压缩到 30 亿参数级别的小语言模型上。
- 结合零样本可用性与可规模化部署来定义任务目标。
- 依赖高质量合成数据而不是继续堆更大的通用模型。

## Why Read It
- 这是小模型在高价值专业任务上替代前沿模型的典型案例。
- 证据归因与幻觉检测直接相关，方法思路可能可迁移到其他垂直领域。
- 对成本敏感的生产环境，任务定制小模型比通用大模型更现实。

## Risks Or Limits
- 摘要没有充分说明合成数据来源、标注噪声控制和评价协议。
- 零样本能力是否依赖生物医学语料分布，外推到其他领域不清楚。','证据归因和简单文本分类的区分边界未说明。

## Recommended For
- 做领域事实核查和证据归因的研究者
- 关注小模型部署的工程师
- 生物医学 NLP 团队

## Keywords
- 小语言模型
- 证据归因
- 生物医学
- 零样本
- 合成数据

## Abstract
Assessing whether an article supports an assertion is essential for hallucination detection and claim verification. While large language models (LLMs) have the potential to automate this task, achieving strong performance requires frontier models such as GPT-5 that are prohibitively expensive to deploy at scale. To efficiently perform biomedical evidence attribution, we present Med-V1, a family of small language models with only three billion parameters. Trained on high-quality synthetic data newly developed in this study, Med-V1 substantially outperforms (+27.0% to +71.3%) its base models on five biomedical benchmarks unified into a verification format. Despite its smaller size, Med-V1 performs comparably to frontier LLMs such as GPT-5, along with high-quality explanations for its predictions. We use Med-V1 to conduct a first-of-its-kind use case study that quantifies hallucinations in LLM-generated answers under different citation instructions. Results show that the format instruction strongly affects citation validity and hallucination, with GPT-5 generating more claims but exhibiting hallucination rates similar to GPT-4o. Additionally, we present a second use case showing that Med-V1 can automatically identify high-stakes evidence misattributions in clinical practice guidelines, revealing potentially negative public health impacts that are otherwise challenging to identify at scale. Overall, Med-V1 provides an efficient and accurate lightweight alternative to frontier LLMs for practical and real-world applications in biomedical evidence attribution and verification tasks. Med-V1 is available at https://github.com/ncbi-nlp/Med-V1.

## Recommendation Signals
- Recommendation score: 7.95
- Relevance score: 2.21
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.8
