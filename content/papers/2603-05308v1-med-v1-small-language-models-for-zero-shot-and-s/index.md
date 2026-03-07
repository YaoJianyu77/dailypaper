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
summary: 用3B级小模型做生物医学证据归因，并把它用于幻觉测量。
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
- 小语言模型
- 证据归因
- 合成数据
- 幻觉检测
reading_priority: medium
---

# Med-V1: Small Language Models for Zero-shot and Scalable Biomedical Evidence Attribution

## TL;DR
用3B级小模型做生物医学证据归因，并把它用于幻觉测量。

## 中文摘要
Med-V1是一组3B参数的小语言模型，目标是在生物医学场景中判断文献是否支持某个断言。作者基于新构建的高质量合成数据训练模型，使其在五个统一为验证格式的生物医学基准上相对基座模型提升27.0%到71.3%，并宣称表现可比前沿大模型。论文还把Med-V1用于分析不同引用指令下的幻觉与引文有效性，但第二个应用案例的细节在摘要中被截断，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05308v1`
- Authors: Qiao Jin, Yin Fang, Lauren He, Yifan Yang, Guangzhi Xiong, Zhizheng Wang, Nicholas Wan, Joey Chan, Donald C. Comeau, Robert Leaman, Charalampos S. Floudas, Aidong Zhang, Michael F. Chiang, Yifan Peng, Zhiyong Lu
- Domain: Large Language Models
- Published: 2026-03-05T15:48:43Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05308v1)
- PDF: [download](https://arxiv.org/pdf/2603.05308v1.pdf)
- Reading priority: medium
- Why this priority: 证据归因方向重要，但场景较垂直，且主贡献更多落在生物医学验证而非通用LLM系统。

## Core Contributions
- 提出面向生物医学证据归因的3B级小模型族，强调可扩展部署而非单纯追求大模型能力。
- 构建高质量合成训练数据，并在五个统一化验证基准上显示显著优于基座模型。
- 将模型用于实际分析场景，考察引用指令对LLM幻觉和证据有效性的影响。

## Why Read It
- 这是小模型在高价值专业验证任务中替代前沿闭源模型的一个具体案例。
- 如果你关心evidence attribution而不仅是生成质量，这篇工作很对路。
- 它把模型能力评估进一步连接到了“如何测量幻觉”这一实际问题。

## Risks Or Limits
- 性能高度依赖合成数据质量与分布，摘要未说明数据构造偏差如何控制。
- 医学证据归因的结论未必能外推到开放领域或非英文环境。

## Recommended For
- 生物医学NLP研究者
- 小语言模型研究者
- 引用与幻觉分析团队

## Keywords
- 生物医学NLP
- 小语言模型
- 证据归因
- 合成数据
- 幻觉检测

## Abstract
Assessing whether an article supports an assertion is essential for hallucination detection and claim verification. While large language models (LLMs) have the potential to automate this task, achieving strong performance requires frontier models such as GPT-5 that are prohibitively expensive to deploy at scale. To efficiently perform biomedical evidence attribution, we present Med-V1, a family of small language models with only three billion parameters. Trained on high-quality synthetic data newly developed in this study, Med-V1 substantially outperforms (+27.0% to +71.3%) its base models on five biomedical benchmarks unified into a verification format. Despite its smaller size, Med-V1 performs comparably to frontier LLMs such as GPT-5, along with high-quality explanations for its predictions. We use Med-V1 to conduct a first-of-its-kind use case study that quantifies hallucinations in LLM-generated answers under different citation instructions. Results show that the format instruction strongly affects citation validity and hallucination, with GPT-5 generating more claims but exhibiting hallucination rates similar to GPT-4o. Additionally, we present a second use case showing that Med-V1 can automatically identify high-stakes evidence misattributions in clinical practice guidelines, revealing potentially negative public health impacts that are otherwise challenging to identify at scale. Overall, Med-V1 provides an efficient and accurate lightweight alternative to frontier LLMs for practical and real-world applications in biomedical evidence attribution and verification tasks. Med-V1 is available at https://github.com/ncbi-nlp/Med-V1.

## Recommendation Signals
- Recommendation score: 7.87
- Relevance score: 2.6
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.8
