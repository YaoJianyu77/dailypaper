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
summary: 把多类外生因素按交互模式拆解后接入航空时间序列预测。
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
- 外生变量
- 航空维修
- 异构特征融合
- 工业数据
reading_priority: low
---

# Aura: Universal Multi-dimensional Exogenous Integration for Aviation Time Series

## TL;DR
把多类外生因素按交互模式拆解后接入航空时间序列预测。

## 中文摘要
这篇论文面向航空维修场景，讨论时间序列预测中多维乃至多模态外生因素的整合问题。作者根据场景经验区分三类外生因素及其不同交互模式，并提出Aura，用三分式编码机制把异构外部信息嵌入现有时间序列模型。摘要提到其基于中国南方航空三年工业数据展开实验，但具体结果与模型细节被截断，摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05092v1`
- Authors: Jiafeng Lin, Mengren Zheng, Simeng Ye, Yuxuan Wang, Huan Zhang, Yuhui Liu, Zhongyi Pei, Jianmin Wang
- Domain: Large Language Models
- Published: 2026-03-05T12:05:15Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05092v1)
- PDF: [download](https://arxiv.org/pdf/2603.05092v1.pdf)
- Reading priority: low
- Why this priority: 推荐分不低，但与本日报的LLM、多模态和Agent主线关联较弱。

## Core Contributions
- 把航空维护预测中的外生信息显式分为三类交互模式，而不是统一拼接处理。
- 提出可插入既有时间序列模型的tripartite encoding机制，用于整合非序列上下文。
- 提供来自真实航空工业场景的大规模长期数据验证背景。

## Why Read It
- 如果你关心结构化外生信息如何进入时序模型，这篇工作有明确的建模切分思路。
- 它展示了行业数据里“多源上下文”比单一数值序列更重要的设定。

## Risks Or Limits
- 与LLM、多模态Agent主线关联较弱，阅读收益更偏行业方法论。
- 摘要没有充分说明实验指标、基线范围和不同外生类型各自的增益。

## Recommended For
- 工业预测研究者
- 航空维修分析团队
- 多源外生信息建模人员

## Keywords
- 时间序列预测
- 外生变量
- 航空维修
- 异构特征融合
- 工业数据

## Abstract
Time series forecasting has witnessed an increasing demand across diverse industrial applications, where accurate predictions are pivotal for informed decision-making. Beyond numerical time series data, reliable forecasting in practical scenarios requires integrating diverse exogenous factors. Such exogenous information is often multi-dimensional or even multimodal, introducing heterogeneous interactions that unimodal time series models struggle to capture. In this paper, we delve into an aviation maintenance scenario and identify three distinct types of exogenous factors that influence temporal dynamics through distinct interaction modes. Based on this empirical insight, we propose Aura, a universal framework that explicitly organizes and encodes heterogeneous external information according to its interaction mode with the target time series. Specifically, Aura utilizes a tailored tripartite encoding mechanism to embed heterogeneous features into well-established time series models, ensuring seamless integration of non-sequential context. Extensive experiments on a large-scale, three-year industrial dataset from China Southern Airlines, covering the Boeing 777 and Airbus A320 fleets, demonstrate that Aura consistently achieves state-of-the-art performance across all baselines and exhibits superior adaptability. Our findings highlight Aura's potential as a general-purpose enhancement for aviation safety and reliability.

## Recommendation Signals
- Recommendation score: 8.67
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 2.0
