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
summary: 这篇工作说明在高风险证据归因任务上，3B 级小模型有机会替代昂贵前沿模型，但前提是数据构造和评测设计站得住。
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
- 生物医学证据归因
- 小语言模型
- 合成数据
- 幻觉检测
- 断言验证
reading_priority: medium
---

# Med-V1: Small Language Models for Zero-shot and Scalable Biomedical Evidence Attribution

## TL;DR
这篇工作说明在高风险证据归因任务上，3B 级小模型有机会替代昂贵前沿模型，但前提是数据构造和评测设计站得住。

## 中文摘要
论文面向生物医学证据归因，试图用 30 亿参数级小模型替代高成本前沿模型做断言与证据支持判断。作者基于新构建的高质量合成数据训练 Med-V1，并把 5 个生物医学基准统一为验证格式；摘要声称相对基座提升 27.0% 到 71.3%，且表现可比 GPT-5 这类前沿模型。它还展示了两个应用：量化不同引用指令下的幻觉与引用有效性，以及识别临床实践指南中的高风险证据误归因。合成数据质量、解释可信度和跨机构泛化边界摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05308v1`
- Authors: Qiao Jin, Yin Fang, Lauren He, Yifan Yang, Guangzhi Xiong, Zhizheng Wang, Nicholas Wan, Joey Chan, Donald C. Comeau, Robert Leaman, Charalampos S. Floudas, Aidong Zhang, Michael F. Chiang, Yifan Peng, Zhiyong Lu
- Domain: Large Language Models
- Published: 2026-03-05T15:48:43Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05308v1)
- PDF: [download](https://arxiv.org/pdf/2603.05308v1.pdf)
- Reading priority: medium
- Why this priority: 问题很重要，也有明确应用价值，但领域较垂直，且最关键的数据与泛化细节还需要通读正文核对。

## Research Background And Motivation
证据归因是生物医学场景里幻觉检测和断言核验的基础能力，但强性能往往依赖昂贵前沿模型。高风险领域需要更便宜、更可扩展且能解释的替代方案。

## Problem Framing
核心问题是能否用小模型在零样本和可扩展设定下完成“文献是否支持断言”的判断，并给出可用解释。这个问题重要，因为生物医学场景既高风险又高成本，不能长期依赖最贵模型。

## Method Overview
作者训练 3B 级 Med-V1 系列小模型，监督信号来自本研究新构建的高质量合成数据，并把多个基准统一为验证格式以做归因判断。随后将模型用于两个真实用例：分析引用指令对幻觉的影响，以及筛查临床指南中的证据误归因。

## Experimental Setup And Evidence
摘要给出两类证据：在 5 个生物医学基准上，相对基座提升 27.0% 到 71.3%，并声称可比肩 GPT-5；同时给出两个应用案例展示可扩展性和潜在公共卫生价值。具体数据构造细节、标注质量控制、解释评价方法和外部泛化摘要没有充分说明。

## Research Or Engineering Value
如果结论成立，这项工作会把高成本的生物医学证据核验压缩到更可部署的小模型上，适合大规模文献审阅、临床问答监控和高风险内容审核。它也提示“专域小模型加高质量任务化数据”仍然是替代前沿通用模型的现实路线。

## Reading Checklist
- 合成训练数据是如何构造和质控的，是否会把数据偏差直接灌进模型？
- 所谓零样本具体指什么设置，是否真的没有目标基准上的任务适配？
- 解释质量如何评估，解释是否真实对应模型的证据归因过程？

## Core Contributions
- 提出面向生物医学证据归因的 3B 级小模型家族，而不是继续依赖最贵的通用模型。
- 用新构建的高质量合成数据训练模型，并把 5 个基准统一到验证格式下比较。
- 展示两个高价值应用场景：量化引用指令下的幻觉，以及发现临床指南中的证据误归因。

## Why Read It
- 它不是单纯做领域微调，而是把专域小模型如何接近前沿模型的路径写得很具体。
- 生物医学虽然是垂直场景，但证据归因与幻觉检测的方法问题具有可迁移价值。
- 如果你关心高风险场景里的可扩展审核系统，这篇论文的应用价值很直接。

## Risks Or Limits
- 合成数据可能带来分布偏差，导致看起来强但真实外部泛化不足。
- 摘要对解释质量的描述偏结论式，缺少足够细节支撑。

## Recommended For
- 做医学 NLP、证据归因与幻觉检测的研究者
- 关注小模型在高风险领域替代前沿模型的工程师
- 研究专域数据构造与模型对齐的读者

## Keywords
- 生物医学证据归因
- 小语言模型
- 合成数据
- 幻觉检测
- 断言验证

## Abstract
Assessing whether an article supports an assertion is essential for hallucination detection and claim verification. While large language models (LLMs) have the potential to automate this task, achieving strong performance requires frontier models such as GPT-5 that are prohibitively expensive to deploy at scale. To efficiently perform biomedical evidence attribution, we present Med-V1, a family of small language models with only three billion parameters. Trained on high-quality synthetic data newly developed in this study, Med-V1 substantially outperforms (+27.0% to +71.3%) its base models on five biomedical benchmarks unified into a verification format. Despite its smaller size, Med-V1 performs comparably to frontier LLMs such as GPT-5, along with high-quality explanations for its predictions. We use Med-V1 to conduct a first-of-its-kind use case study that quantifies hallucinations in LLM-generated answers under different citation instructions. Results show that the format instruction strongly affects citation validity and hallucination, with GPT-5 generating more claims but exhibiting hallucination rates similar to GPT-4o. Additionally, we present a second use case showing that Med-V1 can automatically identify high-stakes evidence misattributions in clinical practice guidelines, revealing potentially negative public health impacts that are otherwise challenging to identify at scale. Overall, Med-V1 provides an efficient and accurate lightweight alternative to frontier LLMs for practical and real-world applications in biomedical evidence attribution and verification tasks. Med-V1 is available at https://github.com/ncbi-nlp/Med-V1.

## Recommendation Signals
- Recommendation score: 7.95
- Relevance score: 2.21
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.8
