---
paper_id: '2210.17323'
title: 'GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers'
authors:
- Elias Frantar
- Saleh Ashkboos
- Torsten Hoefler
- Dan Alistarh
domain: LLM Inference Systems
slug: 2210-17323-gptq-accurate-post-training-quantization-for-gen
published: '2022-10-31'
summary: 核心点是把 GPT 类模型做成 3-4 bit 的后训练量化，同时尽量保持精度，以降低大模型在受限硬件上的部署门槛。
source_url: https://arxiv.org/abs/2210.17323
pdf_url: https://arxiv.org/pdf/2210.17323.pdf
scores:
  relevance: 2.9
  recency: 0.0
  popularity: 1.1
  quality: 1.1
  recommendation: 6.83
tags:
- paper-note
status: generated
updated: '2026-03-08'
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- 后训练量化
- GPTQ
- 3-4 bit 权重量化
- GPT 类模型
- 受限硬件部署
reading_priority: high
analysis_priority_rank: 6
selected_for_full_analysis: false
---

# GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers

## TL;DR
核心点是把 GPT 类模型做成 3-4 bit 的后训练量化，同时尽量保持精度，以降低大模型在受限硬件上的部署门槛。

## 中文摘要
这篇工作提出一种面向 GPT 风格模型的可扩展后训练量化方法，目标是在 3-4 bit 权重精度下尽量保持准确性。摘要声称该方法能让更大的模型部署到受限硬件上，因此对大模型推理的存储与部署成本有直接意义。摘要没有充分说明量化误差控制机制、实验设置和系统指标，所以真实收益仍需要通过正文核对。

## Quick Facts
- Paper ID: `2210.17323`
- Authors: Elias Frantar, Saleh Ashkboos, Torsten Hoefler, Dan Alistarh
- Institutions: Institution information not extracted
- Domain: LLM Inference Systems
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2022-10-31
- Source page: [open](https://arxiv.org/abs/2210.17323)
- PDF: [download](https://arxiv.org/pdf/2210.17323.pdf)
- Reading priority: high
- Why this priority: 推荐分为 6.83，且主题与大模型推理部署直接相关；虽然这是 2022-10-31 的经典工作、时效性分数为 0，摘要也缺少系统细节，但它覆盖了 3-4 bit 低比特量化这一基础问题，对当前 LLM inference 读者仍属高优先级补课。

## Research Background And Motivation
大语言模型部署常被权重存储和硬件容量限制，而后训练量化之所以重要，是因为它试图在不重训的前提下降低部署成本。对于生成式 Transformer，如果低比特量化还能保住精度，就会直接影响受限硬件上可部署的模型规模。

## Problem Framing
这篇工作要解决的问题是：能否把 GPT 类模型的权重量化到 3-4 bit，而不显著破坏模型准确性。这个问题重要，因为如果低比特量化带来明显精度退化，资源节省就很难转化成可接受的实际部署方案。

## Method Overview
摘要表明作者提出了一种可扩展的后训练量化方法，直接面向 GPT 风格模型，在训练完成后把权重量化到 3-4 bit，同时把“尽量保持准确性”作为核心目标。摘要没有充分说明其具体误差建模、量化粒度或求解过程。

## Experimental Setup And Evidence
摘要给出的证据是高层结论：在 3-4 bit 权重精度下仍能保持准确性，并让更大的模型可以部署到受限硬件上。摘要没有充分说明实验设置、对比基线、硬件平台，也没有给出延迟、吞吐、显存或带宽等系统指标。

## Research Or Engineering Value
如果这些结论成立，这项工作对研究和工程都有实际价值：它提供了一条不依赖重训的低比特部署路线，可直接降低大模型的存储与部署门槛，并为资源受限环境中的模型落地提供基础方法。对后续量化推理系统而言，它也有潜力成为评估低比特可行性的关键参考点。

## Reading Checklist
- 具体的量化误差是如何建模和补偿的，为什么 3-4 bit 下还能保持 GPT 类模型精度？
- 量化后到底改善了哪些系统指标：显存占用、可部署模型规模、延迟还是吞吐？
- 实验覆盖了哪些模型规模、任务和硬件平台，对比 baseline 是否足够公平？

## Core Contributions
- 提出面向 GPT 类模型的可扩展后训练量化方法。
- 把目标位宽压到 3-4 bit 权重精度，同时强调尽量保持模型准确性。
- 将量化结果直接落到“更大模型可在受限硬件部署”这一实际部署目标上。

## Why Read It
- 后训练量化不要求重新训练，工程进入门槛相对低，直接对应现有模型的部署改造。
- 3-4 bit 是低比特部署的关键区间，若精度真能保住，对模型存储成本和部署可行性影响很大。
- 它聚焦的是“低比特且保精度”这一核心矛盾，适合作为判断量化路线是否值得进入系统实现层的起点。

## Risks Or Limits
- 摘要没有充分说明量化机制，当前还看不出精度保持来自哪些具体设计。
- 摘要没有给出延迟、吞吐、显存或带宽数据，因此系统收益目前主要停留在可部署性陈述。

## Recommended For
- 做大模型推理部署和量化落地的系统工程师。
- 评估低比特后训练量化是否值得进入生产路径的研究者。
- 需要判断受限硬件上可部署模型规模上限的团队。

## Keywords
- 后训练量化
- GPTQ
- 3-4 bit 权重量化
- GPT 类模型
- 受限硬件部署

## Abstract
Introduces a scalable post-training quantization method for GPT-style models that preserves accuracy at 3-4 bit weight precision and makes much larger models deployable on limited hardware.

## Recommendation Signals
- Recommendation score: 6.83
- Relevance score: 2.9
- Recency score: 0.0
- Popularity score: 1.1
- Quality score: 1.1
- Analysis candidate score: 4.88
- Analysis priority rank: 6
