---
paper_id: 2603.05092v1
title: 'Aura: Universal Multi-dimensional Exogenous Integration for Aviation Time
  Series'
authors:
- Jiafeng Lin
- Mengren Zheng
- Simeng Ye
- Yuxuan Wang
- Huan Zhang
- Yuhui Liu
- Zhongyi Pei
- Jianmin Wang
domain: Large Language Models
slug: 2603-05092v1-aura-universal-multi-dimensional-exogenous-integ
published: '2026-03-05T12:05:15Z'
summary: 把航空时序预测中的异构外源因素按交互模式拆开建模，而不是简单拼接特征。
source_url: https://arxiv.org/abs/2603.05092v1
pdf_url: https://arxiv.org/pdf/2603.05092v1.pdf
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 2.0
  quality: 2.0
  recommendation: 8.67
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 时间序列预测
- 外源信息融合
- 航空维修
- 多模态外生变量
- 工业数据
reading_priority: medium
---

# Aura: Universal Multi-dimensional Exogenous Integration for Aviation Time Series

## TL;DR
把航空时序预测中的异构外源因素按交互模式拆开建模，而不是简单拼接特征。

## 中文摘要
论文围绕航空维修时间序列预测，先归纳出三类影响目标序列的外源因素及其不同交互模式，再提出Aura统一接入框架。Aura通过定制的三分式编码机制，把多维甚至多模态的非顺序上下文嵌入成熟时序模型。摘要称，其在覆盖波音777和空客A320机队的三年工业数据上，相对各类基线都取得了更好的效果。

## Quick Facts
- Paper ID: `2603.05092v1`
- Authors: Jiafeng Lin, Mengren Zheng, Simeng Ye, Yuxuan Wang, Huan Zhang, Yuhui Liu, Zhongyi Pei, Jianmin Wang
- Domain: Large Language Models
- Published: 2026-03-05T12:05:15Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05092v1)
- PDF: [download](https://arxiv.org/pdf/2603.05092v1.pdf)
- Reading priority: medium
- Why this priority: 与给定主题并非最直接相关，但外源多模态融合的建模思想有跨任务借鉴价值。

## Core Contributions
- 归纳航空维修场景中三类外源因素及其不同作用方式。
- 提出三分式编码机制，把异构外部信息显式接入现有时序模型。
- 在大规模工业数据上展示该框架作为通用增强模块的潜力。

## Why Read It
- 外源信息如何接入时序模型是工业预测中的常见难题，这篇给出了结构化解法。
- 它强调按作用机制组织信息，而不是把多源特征直接堆叠。
- 对多模态上下文融入预测任务的研究者有方法层面的借鉴价值。

## Risks Or Limits
- 与LLM主线关联有限。
- 摘要没有充分说明不同模态的数据形式、缺失处理和部署成本。","通用性主要由单一航空场景支撑，跨行业外推仍不明确。

## Recommended For
- 工业时间序列研究者
- 多模态融合研究者
- 航空维修分析团队

## Keywords
- 时间序列预测
- 外源信息融合
- 航空维修
- 多模态外生变量
- 工业数据

## Abstract
Time series forecasting has witnessed an increasing demand across diverse industrial applications, where accurate predictions are pivotal for informed decision-making. Beyond numerical time series data, reliable forecasting in practical scenarios requires integrating diverse exogenous factors. Such exogenous information is often multi-dimensional or even multimodal, introducing heterogeneous interactions that unimodal time series models struggle to capture. In this paper, we delve into an aviation maintenance scenario and identify three distinct types of exogenous factors that influence temporal dynamics through distinct interaction modes. Based on this empirical insight, we propose Aura, a universal framework that explicitly organizes and encodes heterogeneous external information according to its interaction mode with the target time series. Specifically, Aura utilizes a tailored tripartite encoding mechanism to embed heterogeneous features into well-established time series models, ensuring seamless integration of non-sequential context. Extensive experiments on a large-scale, three-year industrial dataset from China Southern Airlines, covering the Boeing 777 and Airbus A320 fleets, demonstrate that Aura consistently achieves state-of-the-art performance across all baselines and exhibits superior adaptability. Our findings highlight Aura's potential as a general-purpose enhancement for aviation safety and reliability.

## Recommendation Signals
- Recommendation score: 8.67
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
