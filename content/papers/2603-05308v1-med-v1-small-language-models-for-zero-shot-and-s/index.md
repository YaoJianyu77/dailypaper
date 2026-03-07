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
summary: 用3B级小模型做生物医学证据归因，目标是在零样本和规模化部署之间找平衡。
source_url: https://arxiv.org/abs/2603.05308v1
pdf_url: https://arxiv.org/pdf/2603.05308v1.pdf
scores:
  relevance: 2.6
  recency: 3.0
  popularity: 1.8
  quality: 1.8
  recommendation: 7.87
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 生物医学NLP
- 证据归因
- 小语言模型
- 幻觉检测
- 合成数据
- 零样本验证
reading_priority: medium
---

# Med-V1: Small Language Models for Zero-shot and Scalable Biomedical Evidence Attribution

## TL;DR
用3B级小模型做生物医学证据归因，目标是在零样本和规模化部署之间找平衡。

## 中文摘要
Med-V1是一组3B参数的小语言模型，基于本文构建的高质量合成数据训练，用于判断文献是否支持某个断言。摘要称，它在五个统一为验证格式的生物医学基准上显著超过底座模型，并与前沿大模型表现相近。作者还把它用于分析不同引用指令下的幻觉情况，以及发现临床指南中的高风险证据误归因。

## Quick Facts
- Paper ID: `2603.05308v1`
- Authors: Qiao Jin, Yin Fang, Lauren He, Yifan Yang, Guangzhi Xiong, Zhizheng Wang, Nicholas Wan, Joey Chan, Donald C. Comeau, Robert Leaman, Charalampos S. Floudas, Aidong Zhang, Michael F. Chiang, Yifan Peng, Zhiyong Lu
- Domain: Large Language Models
- Published: 2026-03-05T15:48:43Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05308v1)
- PDF: [download](https://arxiv.org/pdf/2603.05308v1.pdf)
- Reading priority: medium
- Why this priority: 垂直领域价值高，但更适合作为可信AI在专业场景中的专题阅读，而非本期首选主线。

## Core Contributions
- 训练面向生物医学证据归因的3B小语言模型家族。
- 将五个生物医学基准统一到验证任务格式，并报告相对底座模型的大幅提升。
- 展示两个实际用例：引用指令下的幻觉分析，以及临床指南中的证据误归因发现。

## Why Read It
- 这是小模型在高价值垂直任务上替代前沿大模型的一个清晰案例。
- 证据归因比一般问答更接近医疗部署中的真实审核需求。
- 如果你关心解释性是否能随模型缩小而保住，这篇值得看。

## Risks Or Limits
- 性能高度依赖合成训练数据质量，摘要没有充分说明其构造偏差与覆盖边界。
- 生物医学领域适配很强，但向通用领域迁移的可行性不明确。","解释质量被强调，但摘要没有充分说明解释如何评测和校验。

## Recommended For
- 医疗NLP研究者
- 事实核验研究者
- 小模型落地团队

## Keywords
- 生物医学NLP
- 证据归因
- 小语言模型
- 幻觉检测
- 合成数据
- 零样本验证

## Abstract
Assessing whether an article supports an assertion is essential for hallucination detection and claim verification. While large language models (LLMs) have the potential to automate this task, achieving strong performance requires frontier models such as GPT-5 that are prohibitively expensive to deploy at scale. To efficiently perform biomedical evidence attribution, we present Med-V1, a family of small language models with only three billion parameters. Trained on high-quality synthetic data newly developed in this study, Med-V1 substantially outperforms (+27.0% to +71.3%) its base models on five biomedical benchmarks unified into a verification format. Despite its smaller size, Med-V1 performs comparably to frontier LLMs such as GPT-5, along with high-quality explanations for its predictions. We use Med-V1 to conduct a first-of-its-kind use case study that quantifies hallucinations in LLM-generated answers under different citation instructions. Results show that the format instruction strongly affects citation validity and hallucination, with GPT-5 generating more claims but exhibiting hallucination rates similar to GPT-4o. Additionally, we present a second use case showing that Med-V1 can automatically identify high-stakes evidence misattributions in clinical practice guidelines, revealing potentially negative public health impacts that are otherwise challenging to identify at scale. Overall, Med-V1 provides an efficient and accurate lightweight alternative to frontier LLMs for practical and real-world applications in biomedical evidence attribution and verification tasks. Med-V1 is available at https://github.com/ncbi-nlp/Med-V1.

## Recommendation Signals
- Recommendation score: 7.87
- Relevance score: 2.6
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.8
