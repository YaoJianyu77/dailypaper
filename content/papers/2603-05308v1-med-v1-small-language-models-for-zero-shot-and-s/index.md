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
summary: 这篇论文的重点不是更大的模型，而是用3B级小模型把生物医学证据归因做成可扩展流程。
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
- 生物医学
- 证据归因
- 幻觉检测
- 合成数据
reading_priority: medium
---

# Med-V1: Small Language Models for Zero-shot and Scalable Biomedical Evidence Attribution

## TL;DR
这篇论文的重点不是更大的模型，而是用3B级小模型把生物医学证据归因做成可扩展流程。

## 中文摘要
论文面向生物医学场景中的证据归因与幻觉检测，提出一组小语言模型，强调零样本和可扩展部署能力。其现实意义在于把高成本前沿模型才能做好的任务，转向更小模型和高质量合成数据训练的路线。摘要说明了应用背景和模型规模，但没有在给定内容中充分说明数据构造、归因粒度以及跨任务泛化证据。

## Quick Facts
- Paper ID: `2603.05308v1`
- Authors: Qiao Jin, Yin Fang, Lauren He, Yifan Yang, Guangzhi Xiong, Zhizheng Wang, Nicholas Wan, Joey Chan, Donald C. Comeau, Robert Leaman, Charalampos S. Floudas, Aidong Zhang, Michael F. Chiang, Yifan Peng, Zhiyong Lu
- Domain: Large Language Models
- Published: 2026-03-05T15:48:43Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05308v1)
- PDF: [download](https://arxiv.org/pdf/2603.05308v1.pdf)
- Reading priority: medium
- Why this priority: 任务价值高，但更偏垂直领域；是否值得更高优先级取决于其合成数据和零样本证据是否足够强。

## Problem Framing
问题是判断文献是否支持某个断言对幻觉检测和事实核查很关键，但现有高性能方案依赖昂贵的大模型，难以大规模部署。

## Approach Snapshot
方法是训练名为Med-V1的一组约3B参数小语言模型，并使用高质量合成数据来做生物医学证据归因；但摘要没有充分说明标签定义、归因输出形式和训练流程细节。

## Evidence Mentioned In Abstract
摘要提供的证据是任务重要性、现有大模型成本过高，以及作者提出小模型路线和合成数据训练方案；在已给内容中，没有看到零样本结果、扩展性指标或与大模型的差距，摘要没有充分说明。

## Reading Checklist
- 所谓证据归因是句级、段级还是文档级支持判断？
- 高质量合成数据如何构造，是否会把教师模型偏差固化进小模型？
- 零样本能力是在未见任务、未见疾病领域，还是未见文献来源上评估的？

## Core Contributions
- 把生物医学证据归因目标压缩到3B级小模型，强调成本与规模化可行性。
- 使用合成数据作为小模型能力迁移的核心手段。
- 把幻觉检测中的“是否有证据支持”做成更明确的归因任务。

## Why Read It
- 这是小模型在高价值专业任务上的一个直接案例，值得看是否真的能替代昂贵大模型。
- 如果方法扎实，对专业领域RAG、核查和临床文献助手都有参考价值。
- 它也能作为观察合成数据蒸馏效果的一个样本。

## Risks Or Limits
- 领域专用任务强依赖标注定义，摘要未说明归因标准是否稳定。
- 合成数据可能带来教师偏差或过拟合模板的问题。

## Recommended For
- 关注小模型、专业领域LLM与证据归因的研究者
- 在做医学文献核查、专业RAG或高成本受限部署的工程师

## Keywords
- 小语言模型
- 生物医学
- 证据归因
- 幻觉检测
- 合成数据

## Abstract
Assessing whether an article supports an assertion is essential for hallucination detection and claim verification. While large language models (LLMs) have the potential to automate this task, achieving strong performance requires frontier models such as GPT-5 that are prohibitively expensive to deploy at scale. To efficiently perform biomedical evidence attribution, we present Med-V1, a family of small language models with only three billion parameters. Trained on high-quality synthetic data newly developed in this study, Med-V1 substantially outperforms (+27.0% to +71.3%) its base models on five biomedical benchmarks unified into a verification format. Despite its smaller size, Med-V1 performs comparably to frontier LLMs such as GPT-5, along with high-quality explanations for its predictions. We use Med-V1 to conduct a first-of-its-kind use case study that quantifies hallucinations in LLM-generated answers under different citation instructions. Results show that the format instruction strongly affects citation validity and hallucination, with GPT-5 generating more claims but exhibiting hallucination rates similar to GPT-4o. Additionally, we present a second use case showing that Med-V1 can automatically identify high-stakes evidence misattributions in clinical practice guidelines, revealing potentially negative public health impacts that are otherwise challenging to identify at scale. Overall, Med-V1 provides an efficient and accurate lightweight alternative to frontier LLMs for practical and real-world applications in biomedical evidence attribution and verification tasks. Med-V1 is available at https://github.com/ncbi-nlp/Med-V1.

## Recommendation Signals
- Recommendation score: 7.95
- Relevance score: 2.21
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.8
