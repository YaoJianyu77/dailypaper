---
paper_id: 2603.05232v1
title: 'SlideSparse: Fast and Flexible (2N-2):2N Structured Sparsity'
authors:
- Hanyong Shao
- Yingbo Hao
- Ting Song
- Yan Xia
- Di Zhang
- Shaohan Huang
- Xun Wu
- Songchen Xu
- Le Xu
- Li Dong
- Zewen Chi
- Yi Zou
- Furu Wei
domain: LLM Inference Systems
slug: 2603-05232v1-slidesparse-fast-and-flexible-2n-2-2n-structured
published: '2026-03-05T14:49:16Z'
summary: 这篇工作试图把 6:8 一类温和结构化稀疏，映射到现有 NVIDIA 2:4 Sparse Tensor Core 执行路径，从而在不走专用硬件的前提下拿到接近理论上限的
  LLM 推理加速。
source_url: http://arxiv.org/abs/2603.05232v1
pdf_url: https://arxiv.org/pdf/2603.05232v1
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 1.5
  quality: 1.5
  recommendation: 9.55
tags:
- paper-note
status: generated
updated: '2026-03-07'
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- LLM推理系统
- 结构化稀疏
- 2:4 Sparse Tensor Core
- 6:8稀疏
- vLLM
- GPU推理加速
reading_priority: high
analysis_priority_rank: 2
selected_for_full_analysis: false
---

# SlideSparse: Fast and Flexible (2N-2):2N Structured Sparsity

## TL;DR
这篇工作试图把 6:8 一类温和结构化稀疏，映射到现有 NVIDIA 2:4 Sparse Tensor Core 执行路径，从而在不走专用硬件的前提下拿到接近理论上限的 LLM 推理加速。

## 中文摘要
论文针对 2:4 稀疏硬件约束过强、会显著伤害 LLM 精度的问题，提出把更温和的 $(2N-2):2N$ 稀疏模式重写为可落到现有 Sparse Tensor Core 的执行形式。核心做法是用 Sliding Window Decomposition 把权重块分解成多个重叠的 2:4 合规窗口，再用 Activation Lifting 把激活重排并入每 token 量化流程。摘要声称该方法已集成到 vLLM，并在多种 GPU、精度和模型家族上验证；在 compute-bound 场景下，6:8 稀疏的 Qwen2.5-7B 达到 1.33x 加速，接近理论上限 4/3。摘要没有充分说明端到端延迟、带宽瓶颈、额外 kernel 开销和 baseline 公平性细节。

## Quick Facts
- Paper ID: `2603.05232v1`
- Authors: Hanyong Shao, Yingbo Hao, Ting Song, Yan Xia, Di Zhang, Shaohan Huang, Xun Wu, Songchen Xu, Le Xu, Li Dong, Zewen Chi, Yi Zou, Furu Wei
- Institutions: Institution information not extracted
- Domain: LLM Inference Systems
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-03-05T14:49:16Z
- Source page: [open](http://arxiv.org/abs/2603.05232v1)
- PDF: [download](https://arxiv.org/pdf/2603.05232v1)
- Reading priority: high
- Why this priority: 这篇论文与当前关注的 LLM inference acceleration 高度对齐，而且不是泛泛代码任务：核心问题就是如何在现有 NVIDIA 稀疏硬件约束下，把更保精度的结构化稀疏转成真实执行收益。摘要还明确给出 vLLM 集成、多 GPU/多精度评测和接近理论上限的加速结果，系统相关性和即时阅读价值都很高。

## Research Background And Motivation
LLM 推理系统希望用结构化稀疏换取更高吞吐和更低算力成本，但现有 NVIDIA 2:4 Sparse Tensor Core 只支持严格 50% 剪枝，实际常会带来明显精度退化。于是系统问题变成：能否在不等待新硬件指令支持的情况下，让更温和、对精度更友好的稀疏模式也真正获得硬件加速。

## Problem Framing
论文要解决的问题是，像 6:8 这样的 $(2N-2):2N$ 结构化稀疏虽然更可能保住 LLM 精度，但现有 commodity GPU 没有对应硬件支持，部署时只能退回 dense 执行，导致“有稀疏、无收益”。这对 LLM serving 很关键，因为如果稀疏模式不能映射到现有 Tensor Core 路径，就无法转化为真实的延迟或吞吐收益。

## Method Overview
作者提出 SlideSparse，把任意 $(2N-2):2N$ 权重块重构为 $N-1$ 个重叠的 2:4 合规窗口，从而复用现有 Sparse Tensor Core。对应的激活重排通过 Activation Lifting 融合进每 token 量化流程，摘要称其额外代价接近于零。整体上这是一个编排层与 kernel/执行路径协同的映射方案，而不是重新定义新硬件稀疏格式。

## Experimental Setup And Evidence
摘要给出的证据包括：方法已集成到 vLLM；评测覆盖多种 GPU（A100、H100、B200、RTX 4090、RTX 5080、DGX-spark）、多种精度（FP4、INT8、FP8、BF16、FP16）和多类模型（Llama、Qwen、BitNet）；在 compute-bound 工作负载上，Qwen2.5-7B 的 6:8 稀疏达到 1.33x 加速，接近理论上限 $4/3$。此外，摘要以 Qwen3 从 54% 到 15% 的例子说明严格 2:4 剪枝可能严重伤害推理精度。摘要没有充分说明实验任务、精度评测协议、端到端 serving 指标、kernel 级开销拆分和对比基线设置。

## Research Or Engineering Value
如果结论成立，这项工作给 LLM inference 一个很实际的路径：用现有 GPU 和现有 Sparse Tensor Core，就能把更温和的结构化稀疏转成真实加速，而不必在精度和吞吐之间二选一。对工程上，它可能降低部署稀疏 LLM 的改造门槛；对研究上，它提示编译/运行时映射可以先于硬件原生支持，扩展稀疏设计空间。

## Reading Checklist
- Sliding Window Decomposition 具体如何保证任意 $(2N-2):2N$ 块都能无损映射到重叠 2:4 窗口，额外的存储、索引和 kernel 调度开销是多少？
- Activation Lifting 融入每 token 量化后，对 decode 场景的端到端 latency、memory bandwidth 和 batch-size 敏感性到底有什么影响？
- 1.33x 加速是在哪些 compute-bound 条件下得到的；与 dense、原生 2:4 稀疏和其他稀疏执行方案相比，baseline 是否公平且可复现？

## Core Contributions
- 提出首个面向 $(2N-2):2N$ 稀疏家族、可复用现有 NVIDIA 2:4 Sparse Tensor Core 的执行系统。
- 设计 Sliding Window Decomposition，把温和结构化稀疏重写为多个重叠的 2:4 合规窗口。
- 提出 Activation Lifting，把激活侧重排并入量化流程，试图把额外运行时成本压到很低。

## Why Read It
- 它直接命中 LLM serving 的系统主线：如何在 commodity GPU 上把“更保精度的稀疏”变成真实吞吐收益。
- 摘要同时给出硬件范围、精度范围和 vLLM 集成信息，值得核对其是否真有跨平台与实际部署价值。
- 如果方法成立，它比单纯提出新稀疏模式更有系统含量，因为关键在于对现有 Tensor Core 执行路径的映射。

## Risks Or Limits
- 收益上限受理论比值 $N/(N-1)$ 约束，6:8 的上限本身只有 4/3，实际工程收益空间未必足够大。
- 摘要强调 compute-bound 场景，说明在 memory-bound 或小 batch decode 下，收益可能明显缩水。

## Recommended For
- 做 LLM inference/serving 优化、尤其关注 vLLM 内核路径和 decode 吞吐的人。
- 研究结构化稀疏、量化与运行时协同映射的人。
- 关心 CUDA kernel 生成、编译器/runtime co-design 与特定 GPU 稀疏硬件约束的人。

## Keywords
- LLM推理系统
- 结构化稀疏
- 2:4 Sparse Tensor Core
- 6:8稀疏
- vLLM
- GPU推理加速

## Abstract
NVIDIA's 2:4 Sparse Tensor Cores deliver 2x throughput but demand strict 50% pruning -- a ratio that collapses LLM reasoning accuracy (Qwen3: 54% to 15%). Milder $(2N-2):2N$ patterns (e.g., 6:8, 25% pruning) preserve accuracy yet receive no hardware support, falling back to dense execution without any benefit from sparsity. We present SlideSparse, the first system to unlock Sparse Tensor Core acceleration for the $(2N-2):2N$ model family on commodity GPUs. Our Sliding Window Decomposition reconstructs any $(2N-2):2N$ weight block into $N-1$ overlapping 2:4-compliant windows without any accuracy loss; Activation Lifting fuses the corresponding activation rearrangement into per-token quantization at near-zero cost. Integrated into vLLM, SlideSparse is evaluated across various GPUs (A100, H100, B200, RTX 4090, RTX 5080, DGX-spark), precisions (FP4, INT8, FP8, BF16, FP16), and model families (Llama, Qwen, BitNet). On compute-bound workloads, the measured speedup ratio (1.33x) approaches the theoretical upper-bound $N/(N-1)=4/3$ at 6:8 weight sparsity in Qwen2.5-7B, establishing $(2N-2):2N$ as a practical path to accuracy-preserving LLM acceleration. Code available at https://github.com/bcacdwk/vllmbench.

## Recommendation Signals
- Recommendation score: 9.55
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.5
- Quality score: 1.5
- Analysis candidate score: 9.88
- Analysis priority rank: 2
- Analysis signals: vllm, h100, a100, b200, throughput, speedup
