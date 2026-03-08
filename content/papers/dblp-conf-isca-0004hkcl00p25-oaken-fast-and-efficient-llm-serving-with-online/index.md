---
paper_id: dblp:conf/isca/0004HKCL00P25
title: 'Oaken: Fast and Efficient LLM Serving with Online-Offline Hybrid KV Cache
  Quantization.'
authors:
- Minsu Kim 0004
- Seongmin Hong
- Ryeowook Ko
- Soongyu Choi
- Hunjong Lee
- Junsoo Kim 0002
- Joo-Young Kim 0001
- Jongse Park
domain: LLM Inference Systems
slug: dblp-conf-isca-0004hkcl00p25-oaken-fast-and-efficient-llm-serving-with-online
published: '2025'
summary: 这篇工作把 KV cache 量化中高成本的离群值检测尽量前移到离线阶段，并用专用量化与内存单元把压缩收益转成实际 serving 吞吐。
source_url: https://dl.acm.org/doi/10.1145/3695053.3731019
pdf_url: https://dl.acm.org/doi/pdf/10.1145/3695053.3731019
scores:
  relevance: 3.0
  recency: 0.0
  popularity: 2.0
  quality: 2.0
  recommendation: 7.97
tags:
- paper-note
status: generated
updated: '2026-03-08'
institutions:
- Korea Advanced Institute of Science and Technology
venue_or_journal: ISCA
citation_summary: 4 citations
keywords:
- LLM serving
- KV cache
- 量化
- 离群值检测
- 长上下文推理
- 显存带宽瓶颈
reading_priority: high
analysis_priority_rank: 3
selected_for_full_analysis: false
---

# Oaken: Fast and Efficient LLM Serving with Online-Offline Hybrid KV Cache Quantization.

## TL;DR
这篇工作把 KV cache 量化中高成本的离群值检测尽量前移到离线阶段，并用专用量化与内存单元把压缩收益转成实际 serving 吞吐。

## 中文摘要
这篇工作面向长上下文 LLM serving 中 KV cache 膨胀带来的显存容量与带宽瓶颈，针对现有离群值感知量化在线检测开销过高的问题提出在线-离线混合方案。Oaken先离线设置离群阈值，在线再用这些阈值决定量化尺度，同时配套自定义量化引擎和内存管理单元，把算法与硬件一起设计。摘要声称其在基于 LPU 的实现中，batch size 为 256 时相对 NVIDIA A100 GPU 吞吐最高提升 1.58x，并且相对现有 KV cache 量化技术平均精度损失仅 0.54%；但硬件前提、baseline 公平性与不同工作负载下的稳定性仍需通读正文核对。

## Quick Facts
- Paper ID: `dblp:conf/isca/0004HKCL00P25`
- Authors: Minsu Kim 0004, Seongmin Hong, Ryeowook Ko, Soongyu Choi, Hunjong Lee, Junsoo Kim 0002, Joo-Young Kim 0001, Jongse Park
- Institutions: Korea Advanced Institute of Science and Technology
- Domain: LLM Inference Systems
- Venue / Journal: ISCA
- Citations: 4 citations
- Published: 2025
- Source page: [open](https://dl.acm.org/doi/10.1145/3695053.3731019)
- PDF: [download](https://dl.acm.org/doi/pdf/10.1145/3695053.3731019)
- Reading priority: high
- Why this priority: 这篇论文与当前关注的 LLM inference acceleration 和 serving efficiency 高度贴合，且摘要直接给出 KV cache 量化、吞吐提升、精度代价和硬件协同这几条关键信号。更重要的是，它讨论的是系统层面收益如何兑现，而不是只在算法层面做泛化压缩，因此值得优先读正文核对收益来源、硬件假设和 baseline 公平性。

## Research Background And Motivation
LLM serving 依赖批处理提升吞吐，但 attention 尤其是 KV cache 访问常受显存带宽限制。随着长上下文推理普及，KV cache 容量快速增长，使得高带宽但容量受限的 HBM 配置更容易成为成本和利用率瓶颈。

## Problem Framing
问题是如何在尽量保持模型精度的同时，把 KV cache 压到更低比特，并避免离群值检测本身的在线开销吞掉量化带来的系统收益。这个问题重要，因为如果量化只能在算法上省带宽、却在运行时增加大量额外处理，LLM serving 的真实吞吐和成本就不会改善。

## Method Overview
Oaken采用在线-离线混合 KV cache 量化：先离线确定离群值阈值，再在线利用这些阈值选择量化尺度，从而规避纯在线离群检测的高开销。为把该策略落到系统实现上，作者还设计了可集成到 LLM 加速器中的自定义量化引擎和内存管理单元，并在 LPU 加速器基础上构建实现。

## Experimental Setup And Evidence
摘要给出的证据是一次基于 LPU 的综合评估：在 batch size 为 256 时，Oaken相对 NVIDIA A100 GPU 吞吐最高提升 1.58x，并且相对现有 KV cache 量化技术平均精度损失仅 0.54%。但摘要没有充分说明测试所用模型、上下文长度、延迟指标、功耗或面积开销，也没有展开 baseline 的具体设置与公平性控制。

## Research Or Engineering Value
如果这些结果成立，这项工作对 LLM inference engineering 的价值在于同时缓解 KV cache 的带宽和容量压力，让长上下文 serving 能在较小精度代价下获得更高吞吐。对系统研究而言，它也提示一个关键点：量化是否有价值，不只取决于压缩率，还取决于在线元开销能否通过算法-硬件协同被真正压下去。

## Reading Checklist
- 离线阈值是如何生成和更新的，是否需要按模型、层、头或上下文长度分别校准，迁移到新模型时成本多大？
- 吞吐提升主要来自哪一部分：更低的 KV 传输带宽、更高的有效容量带来的更大 batch，还是专用量化/内存单元减少了在线处理开销？
- 与 A100 和现有 KV cache 量化 baseline 的比较是否在相同模型、batch、上下文长度、精度目标和硬件资源约束下进行，额外硬件面积与功耗代价是多少？

## Core Contributions
- 提出在线-离线混合 KV cache 量化思路，用离线阈值替代高成本的纯在线离群值检测。
- 给出与量化算法配套的自定义量化引擎和内存管理单元，强调算法与加速器协同而非单点压缩技巧。
- 在基于 LPU 的实现上展示吞吐与精度权衡，试图证明 KV cache 量化可以兑现为实际 serving 收益。

## Why Read It
- 直接命中 LLM serving 的 KV cache、带宽和容量瓶颈，属于当前 systems 主线而不是泛泛压缩工作。
- 它关注的是量化元开销会不会抵消系统收益，这比单看压缩精度更接近真实部署问题。
- 摘要同时涉及算法策略和硬件实现，适合核对吞吐提升到底来自数据表示变化还是来自专用数据通路设计。

## Risks Or Limits
- 结果明显依赖专用加速器实现，迁移到通用 GPU 或不同内存层次结构上的收益可能有限。
- 离线阈值若对模型分布、层级特性或工作负载敏感，可能削弱方法在多模型和动态场景中的鲁棒性。

## Recommended For
- 做 LLM serving、KV cache 管理与量化优化的系统研究者和工程师。
- 关注 accelerator/compiler/runtime co-design、尤其是 memory bottleneck 的硬件系统读者。
- 需要评估长上下文推理成本、吞吐与精度权衡的推理基础设施团队。

## Keywords
- LLM serving
- KV cache
- 量化
- 离群值检测
- 长上下文推理
- 显存带宽瓶颈

## Abstract
Modern Large Language Model serving system batches multiple requests to achieve high throughput, while batching attention operations is challenging, rendering memory bandwidth a critical bottleneck. The community relies on high-end GPUs with multiple high-bandwidth memory channels. Unfortunately, HBM's high bandwidth often comes at the expense of limited memory capacity, which reduces core utilization and increases costs. Recent advancements enabling longer contexts for LLMs have substantially increased the key-value cache size, further intensifying the pressures on memory capacity. The literature has explored KV cache quantization techniques, which commonly use low bitwidth for most values, selectively using higher bitwidth for outlier values. While this approach helps achieve high accuracy and low bitwidth simultaneously, it comes with the limitation that cost for online outlier detection is excessively high, negating the advantages. We propose Oaken, an acceleration solution that achieves high accuracy and high performance simultaneously through co-designing algorithm and hardware. To effectively find a sweet spot in the accuracy-performance trade-off space of KV cache quantization, Oaken employs an online-offline hybrid approach, setting outlier thresholds offline, which are then used to determine the quantization scale online. To translate the proposed algorithmic technique into tangible performance gains, Oaken also comes with custom quantization engines and memory management units that can be integrated with any LLM accelerators. We built an Oaken accelerator on top of an LLM accelerator, LPU, and conducted a comprehensive evaluation. Our experiments show that for a batch size of 256, Oaken achieves up to 1.58x throughput improvement over NVIDIA A100 GPU, incurring a minimal accuracy loss of only 0.54\% on average, compared to state-of-the-art KV cache quantization techniques.

## Recommendation Signals
- Recommendation score: 7.97
- Relevance score: 3.0
- Recency score: 0.0
- Popularity score: 2.0
- Quality score: 2.0
- Analysis candidate score: 7.95
- Analysis priority rank: 3
- Analysis signals: kv cache
