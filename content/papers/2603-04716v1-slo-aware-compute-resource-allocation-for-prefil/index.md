---
paper_id: 2603.04716v1
title: SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM
  Inference
authors:
- Luchang Li
- Dongfang Li
- Bozhao Gong
- Yu Zhang
domain: LLM Inference Systems
slug: 2603-04716v1-slo-aware-compute-resource-allocation-for-prefil
published: '2026-03-05T01:41:09Z'
summary: 把 P/D 解耦服务里的资源配比问题落到 TTFT、TPOT、总吞吐和请求长度共同约束的可计算规划框架上。
source_url: http://arxiv.org/abs/2603.04716v1
pdf_url: https://arxiv.org/pdf/2603.04716v1
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 1.1
  quality: 1.1
  recommendation: 9.22
tags:
- paper-note
status: generated
updated: '2026-03-07'
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- LLM 推理系统
- Prefill-Decode 解耦
- 资源分配
- SLO
- TTFT
- TPOT
reading_priority: high
analysis_priority_rank: 3
selected_for_full_analysis: false
---

# SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM Inference

## TL;DR
把 P/D 解耦服务里的资源配比问题落到 TTFT、TPOT、总吞吐和请求长度共同约束的可计算规划框架上。

## 中文摘要
这篇工作关注 Prefill/Decode 解耦 LLM 推理里一个很实际的问题：在总吞吐和时延 SLO 约束下，prefill 与 decode 侧到底该配多少计算资源。方法上，它把理论资源计算与实测吞吐标定结合起来，用请求输入/输出长度、prefill/decode 吞吐、TTFT 和 TPOT 共同推导资源需求。摘要声称该方法能较准确预测真实场景中的最优 P/D 资源分配，但没有充分说明硬件前提、比较基线和误差范围。

## Quick Facts
- Paper ID: `2603.04716v1`
- Authors: Luchang Li, Dongfang Li, Bozhao Gong, Yu Zhang
- Institutions: Institution information not extracted
- Domain: LLM Inference Systems
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-03-05T01:41:09Z
- arXiv: [abstract](http://arxiv.org/abs/2603.04716v1)
- PDF: [download](https://arxiv.org/pdf/2603.04716v1)
- Reading priority: high
- Why this priority: 给定信息里，这篇与当前关注的 LLM inference acceleration 和 serving efficiency 高度贴合，直接讨论 P/D 解耦部署中的资源配比、TTFT/TPOT 与吞吐关系，且推荐分为 9.22、领域优先级最高。它值得优先读，但是否有通用工程价值仍取决于硬件前提、基线公平性和实验细节是否站得住。

## Research Background And Motivation
随着 Prefill/Decode disaggregation 成为 LLM serving 的常见优化手段，系统瓶颈不再只是单机算力，而是 prefill 与 decode 资源池的配比能否同时满足吞吐和时延目标。由于请求输入/输出长度差异很大，靠经验分配资源很容易造成 TTFT、TPOT 或整体利用率失衡。

## Problem Framing
问题是：给定总吞吐目标、TTFT/TPOT 这类 SLO，以及请求输入/输出长度特征，如何系统地决定 prefill 和 decode 各需要多少硬件资源。这个问题直接影响 LLM inference 服务的容量规划、资源利用率和用户侧时延，但摘要指出目前缺少公认的方法。

## Method Overview
作者提出一个“理论建模 + 经验标定”的混合方法。先基于总吞吐需求、请求输入/输出长度以及 prefill/decode 吞吐建立 P/D 资源数量的理论模型；再用 M/M/1 排队模型把 benchmark 得到的最大 prefill 吞吐与 TTFT 约束联系起来，估计实际可达的 prefill 吞吐；decode 侧则通过寻找满足 TPOT 要求的 batch size，并用实测得到对应 decode 吞吐。

## Experimental Setup And Evidence
摘要给出的证据是“实验结果表明该方法能够较准确地预测真实 LLM inference 场景中的最优 P/D 资源分配”。但摘要没有充分说明实验使用的模型、GPU 或其他硬件条件、请求分布、比较基线、误差指标，以及在不同负载下的稳定性。

## Research Or Engineering Value
如果方法成立，它能把 P/D 解耦部署中的资源规划从经验试错变成可计算、可标定的流程，帮助系统更快确定 GPU 配比并更稳地满足 TTFT、TPOT 和吞吐目标。对推理平台工程而言，这类方法的实际价值在于减少过配和欠配带来的成本与性能损失，并为 autoscaling、capacity planning 和 admission control 提供更明确的依据。

## Reading Checklist
- M/M/1 对 prefill 阶段的建模在真实到达过程、批处理和多 GPU 部署下误差有多大？
- decode 侧满足 TPOT 的 batch size 搜索是否依赖特定模型、KV cache 策略或 GPU，跨硬件是否仍然有效？
- 与经验式配比、启发式 autoscaling 或其他调度方法相比，这个方法的预测精度和实际部署收益分别是多少？

## Core Contributions
- 把 P/D 解耦 LLM inference 的资源配比问题形式化为一个同时受总吞吐、请求长度和 SLO 约束的计算问题。
- 用 M/M/1 排队模型把 prefill 最大吞吐、TTFT 约束与可达 prefill 吞吐联系起来。
- 通过满足 TPOT 的 decode batch size 选择和经验 benchmark，构建一个可落地的 P/D 资源分配流程。

## Why Read It
- 问题贴近真实 serving：P/D disaggregation 已常见，但资源到底怎么配往往仍靠经验。
- 摘要明确把 TTFT、TPOT、吞吐和输入/输出长度放进同一个框架，适合作为容量规划或调度设计的切入点。
- 它是面向 LLM inference serving efficiency 的系统方法论文，而不是泛泛的代码或模型层优化。

## Risks Or Limits
- 核心结论依赖排队模型和 benchmark 标定，若请求到达分布、批处理行为或系统抖动偏离假设，预测可能失真。
- 摘要没有充分说明硬件假设、GPU 类型和模型覆盖范围，方法是否依赖特定部署环境仍需核对。

## Recommended For
- 设计或运营 P/D 解耦 LLM serving 平台的系统工程师
- 关注 TTFT/TPOT、容量规划和 GPU 资源配比的推理基础设施研究者
- 做 LLM inference 调度、autoscaling 或排队建模的读者

## Keywords
- LLM 推理系统
- Prefill-Decode 解耦
- 资源分配
- SLO
- TTFT
- TPOT

## Abstract
Prefill-Decode (P/D) disaggregation has emerged as a widely adopted optimization strategy for Large Language Model (LLM) inference. However, there currently exists no well-established methodology for determining the optimal number of P/D hardware resources, subject to constraints on total throughput, service level objectives (SLOs), and request characteristics - specifically input and output lengths. To address this gap, we propose a hybrid approach that combines theoretical modeling with empirical benchmarking. First, we present a theoretical model for calculating P/D resource counts, which is based on total throughput requirements, request input and output lengths, as well as prefill and decode throughput. Then, to obtain the actual prefill and decode throughput under SLO constraints, we model the prefill process using M/M/1 queuing theory, deriving the achieved prefill throughput from the benchmarked maximum prefill throughput and Time-To-First-Token (TTFT). For the decode phase, we determine the decode batch sizes that meet Time-Per-Output-Token (TPOT) requirements and obtain the corresponding decode throughput through empirical measurements. Our experimental results demonstrate that the proposed method can accurately predict optimal P/D resource allocation in real-world LLM inference scenarios.

## Recommendation Signals
- Recommendation score: 9.22
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.1
- Quality score: 1.1
- Analysis candidate score: 7.89
- Analysis priority rank: 3
- Analysis signals: prefill, decode, throughput
