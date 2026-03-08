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
summary: 这篇工作把高成本前沿模型才能做好的生物医学证据归因任务，下放到3B级小模型上，并把它直接用于量化引用失真与高风险误归因。
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
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- 小语言模型
- 生物医学证据归因
- 幻觉检测
- 声明验证
- 合成数据训练
- 零样本验证
reading_priority: medium
---

# Med-V1: Small Language Models for Zero-shot and Scalable Biomedical Evidence Attribution

## TL;DR
这篇工作把高成本前沿模型才能做好的生物医学证据归因任务，下放到3B级小模型上，并把它直接用于量化引用失真与高风险误归因。

## 中文摘要
论文关注生物医学场景中的证据归因，即判断文章是否真正支持某个断言，这对幻觉检测和声明验证很关键。作者提出一组3B参数的小语言模型 Med-V1，使用本文新构建的高质量合成数据训练，声称在五个统一为验证格式的生物医学基准上显著优于底座模型，并可比肩 GPT-5 这类前沿模型。工作还把模型用于两个应用案例：分析不同引用指令下 LLM 回答的幻觉与引用有效性，以及识别临床实践指南中的高风险证据误归因；但摘要没有充分说明数据构造、解释质量评测和泛化边界。

## Quick Facts
- Paper ID: `2603.05308v1`
- Authors: Qiao Jin, Yin Fang, Lauren He, Yifan Yang, Guangzhi Xiong, Zhizheng Wang, Nicholas Wan, Joey Chan, Donald C. Comeau, Robert Leaman, Charalampos S. Floudas, Aidong Zhang, Michael F. Chiang, Yifan Peng, Zhiyong Lu
- Institutions: Institution information not extracted
- Domain: Large Language Models
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-03-05T15:48:43Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05308v1)
- PDF: [download](https://arxiv.org/pdf/2603.05308v1.pdf)
- Reading priority: medium
- Why this priority: 这篇论文与大模型可靠性和低成本部署高度相关，问题定义也很实用；但应用场景强烈偏向生物医学，且摘要对数据构造、评测协议和泛化边界交代不足。对关注 LLM 审计、引用验证和小模型高价值任务的人值得优先读摘要与实验部分，但未必是当天最先通读的通用方法论文。

## Research Background And Motivation
随着大模型被用于医疗问答、文献综述和临床知识服务，系统是否真的能把结论对应到可靠证据，已经成为比“能否生成答案”更核心的问题。现有高性能方案往往依赖昂贵前沿模型，因此一个可扩展、低成本、零样本可用的证据归因器有明显现实需求。

## Problem Framing
这篇论文要解决的问题是：能否用小语言模型在生物医学领域准确判断“给定文献是否支持某个断言”，从而支撑幻觉检测、引用有效性分析和高风险误归因发现。这个问题重要，因为医疗与生物医学场景对证据链要求高，而前沿大模型的成本使大规模部署与持续审计不现实。

## Method Overview
作者提出 Med-V1，一组仅约 3B 参数的小语言模型，核心做法是用本文新开发的高质量合成数据进行训练，并把五个生物医学基准统一改写为验证任务格式。模型输出不仅包含支持/不支持类判断，还强调给出解释；在应用层面，作者将其用于评估 LLM 在不同引用指令下的回答质量，以及扫描临床指南中的证据误归因。

## Experimental Setup And Evidence
摘要给出的证据主要有三类：第一，Med-V1 相对其底座模型在五个生物医学基准上有较大提升；第二，尽管模型更小，其表现据称可与 GPT-5 级别模型相当；第三，两个应用案例表明它可用于量化 LLM 回答中的幻觉/引用有效性，并发现临床指南中的高风险误归因。不过摘要没有充分说明五个基准的具体构成、比较设置、解释质量如何评估，以及两个案例中的误报漏报情况。

## Research Or Engineering Value
如果这些结论成立，这项工作对研究和工程都有直接价值：研究上，它把“证据归因”从依赖超大模型的昂贵能力，转成可系统评测和扩展的小模型能力；工程上，它可作为医疗问答、RAG、文献助手和临床知识系统中的审计模块，用更低成本持续检查引用是否有效、输出是否存在高风险幻觉。

## Reading Checklist
- 合成训练数据是如何生成、过滤和标注的？是否存在把教师模型偏差蒸馏进学生模型的问题？
- 五个生物医学基准被统一为验证格式后，任务定义是否发生变化，从而影响与既有结果的可比性？
- 两个真实应用案例中，模型发现的误归因有多少经过人工核验，误报与漏报在高风险场景下是否可接受？

## Core Contributions
- 提出面向生物医学证据归因的 3B 级小语言模型家族，目标是以更低成本替代前沿大模型完成高价值验证任务。
- 构建并使用高质量合成数据训练该模型，使其在统一后的五个生物医学验证基准上显著强于底座模型。
- 将证据归因模型落到两个具体使用场景：分析 LLM 在不同引用指令下的幻觉与引用有效性，以及识别临床实践指南中的高风险证据误归因。

## Why Read It
- 它切中的不是通用生成能力，而是更接近真实部署痛点的“证据是否站得住”问题，这对医疗 RAG、引用式问答和事实核查都很实用。
- 小模型接近前沿模型性能这一主张，如果成立，意味着高频审计与批量验证可以从昂贵 API 转向可部署模型。
- 论文不仅做 benchmark，还给出面向 LLM 输出审计和临床指南核查的应用案例，便于判断它是否有工程落地潜力。

## Risks Or Limits
- 领域偏重生物医学，方法能否迁移到通用 LLM、Agent 或多模态证据归因，摘要没有充分说明。
- 核心增益依赖合成数据质量，但摘要没有充分说明数据来源、覆盖范围和潜在标注噪声。

## Recommended For
- 做医疗/科研文献问答、事实核查或引用审计系统的工程师
- 关注小模型蒸馏、合成数据训练和高价值判别任务的 LLM 研究者
- 需要评估 RAG 或回答系统中“引用是否真的支撑结论”的团队

## Keywords
- 小语言模型
- 生物医学证据归因
- 幻觉检测
- 声明验证
- 合成数据训练
- 零样本验证

## Abstract
Assessing whether an article supports an assertion is essential for hallucination detection and claim verification. While large language models (LLMs) have the potential to automate this task, achieving strong performance requires frontier models such as GPT-5 that are prohibitively expensive to deploy at scale. To efficiently perform biomedical evidence attribution, we present Med-V1, a family of small language models with only three billion parameters. Trained on high-quality synthetic data newly developed in this study, Med-V1 substantially outperforms (+27.0% to +71.3%) its base models on five biomedical benchmarks unified into a verification format. Despite its smaller size, Med-V1 performs comparably to frontier LLMs such as GPT-5, along with high-quality explanations for its predictions. We use Med-V1 to conduct a first-of-its-kind use case study that quantifies hallucinations in LLM-generated answers under different citation instructions. Results show that the format instruction strongly affects citation validity and hallucination, with GPT-5 generating more claims but exhibiting hallucination rates similar to GPT-4o. Additionally, we present a second use case showing that Med-V1 can automatically identify high-stakes evidence misattributions in clinical practice guidelines, revealing potentially negative public health impacts that are otherwise challenging to identify at scale. Overall, Med-V1 provides an efficient and accurate lightweight alternative to frontier LLMs for practical and real-world applications in biomedical evidence attribution and verification tasks. Med-V1 is available at https://github.com/ncbi-nlp/Med-V1.

## Recommendation Signals
- Recommendation score: 7.95
- Relevance score: 2.21
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.8
