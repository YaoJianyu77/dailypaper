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
summary: 核心点不是再提一种稀疏模式，而是把 6:8 这类更保精度的结构化稀疏真正映射到现有 NVIDIA 2:4 Sparse Tensor Core 执行路径。
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
updated: '2026-03-08'
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- LLM推理系统
- 结构化稀疏
- 2:4 Sparse Tensor Core
- 6:8稀疏
- vLLM
- 量化融合耦合执行路径
reading_priority: high
analysis_priority_rank: 2
selected_for_full_analysis: false
---

# SlideSparse: Fast and Flexible (2N-2):2N Structured Sparsity

## TL;DR
核心点不是再提一种稀疏模式，而是把 6:8 这类更保精度的结构化稀疏真正映射到现有 NVIDIA 2:4 Sparse Tensor Core 执行路径。

## 中文摘要
这篇工作针对 LLM 推理里的一个直接痛点：6:8 这类较温和结构化稀疏更可能保住精度，但现有 NVIDIA Sparse Tensor Core 只原生支持 2:4，所以这类模型通常只能按 dense 跑。作者提出 SlideSparse，用 Sliding Window Decomposition 把任意 (2N-2):2N 权重块重构成 N-1 个重叠的 2:4 窗口，再用 Activation Lifting 把激活重排并入 per-token quantization，试图以很低额外代价复用硬件稀疏加速。摘要声称该方法已接入 vLLM，并在多种 GPU、精度和模型上评测，在 compute-bound 场景下 Qwen2.5-7B 的 6:8 稀疏实测速比达到 1.33x，接近理论上界 4/3；但端到端 serving 条件、额外带宽/显存代价和 baseline 公平性仍需正文核对。

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
- Why this priority: 这篇工作与 LLM inference acceleration 和 serving efficiency 高度对齐，系统点集中在现有 NVIDIA 稀疏硬件路径复用、vLLM 集成和可验证的吞吐收益上，且推荐分数很高。虽然仍需核对硬件前提、端到端条件和 baseline 公平性，但它明显属于今天应优先精读的 systems 主线。

## Research Background And Motivation
在 LLM 推理系统里，结构化稀疏之所以重新重要，是因为它有机会直接换来 matmul 吞吐收益，而不仅仅是参数压缩。问题在于硬件原生支持的 2:4 稀疏过于刚性，50% pruning 可能明显伤害推理精度，而更温和的 6:8 等模式又缺少可直接落地的硬件执行路径。

## Problem Framing
这篇工作的核心问题是：如何在不要求新硬件的前提下，让 (2N-2):2N 这类更保精度的结构化稀疏真正映射到现有 NVIDIA 2:4 Sparse Tensor Core，而不是因为不满足原生约束而退化成 dense 执行。对 LLM serving 来说，这决定了稀疏是否能从离线剪枝结果变成真实的延迟或吞吐收益。

## Method Overview
作者的核心做法是提出 Sliding Window Decomposition，把每个 (2N-2):2N 权重块分解为 N-1 个彼此重叠但各自满足 2:4 约束的窗口表示，从而复用现有 Sparse Tensor Core 的执行路径。为降低激活侧重排成本，论文再提出 Activation Lifting，把对应的 activation rearrangement 融入 per-token quantization 流程，并将整条路径接入 vLLM。

## Experimental Setup And Evidence
摘要给出的证据包括：方法已集成到 vLLM；评测覆盖 A100、H100、B200、RTX 4090、RTX 5080 和 DGX-spark，多种数值精度，以及 Llama、Qwen、BitNet 等模型；在 compute-bound 工作负载下，Qwen2.5-7B 的 6:8 稀疏实测速比为 1.33x，接近理论上界 4/3。摘要还用 Qwen3 从 54% 到 15% 的例子说明严格 2:4 剪枝可能严重伤害推理精度，但摘要没有充分说明端到端延迟、不同 batch 或 sequence length 下的表现、以及 accuracy 评测设置。

## Research Or Engineering Value
如果这些结论成立，这项工作提供了一条非常务实的系统路线：不等新的稀疏硬件支持，也不被迫接受 2:4 带来的精度损失，就能把更温和的结构化稀疏转成现有 NVIDIA GPU 上可部署的推理优化。对工程侧，它可能把稀疏从理论上的压缩手段推进到 vLLM 等 serving 框架里的真实吞吐提升；对研究侧，它展示了一个通过表示重写和运行时融合来扩展硬件原生稀疏能力的思路。

## Reading Checklist
- Sliding Window Decomposition 在 kernel 层到底如何映射到 Sparse Tensor Core 指令路径，额外的 packing、indexing 和 launch 开销有多大？
- Activation Lifting 融入 per-token quantization 后，在不同精度、batch size 和 sequence length 下是否仍接近零成本，还是只在特定 compute-bound 场景成立？
- 与 dense、原生 2:4 sparse 以及其他稀疏实现的比较是否公平，是否把剪枝、校准和精度恢复成本一并算入？

## Core Contributions
- 提出首个面向 (2N-2):2N 结构化稀疏家族、可复用现有 2:4 Sparse Tensor Core 的系统执行方案。
- 提出 Sliding Window Decomposition，把 6:8 等模式重写成 N-1 个重叠的 2:4 合规窗口，并给出理论速度上界 N/(N-1)。
- 提出 Activation Lifting，将激活重排与 per-token quantization 融合，并将整套方法接入 vLLM 进行实际系统评测。

## Why Read It
- 它直接命中 LLM inference systems 的现实问题：更保精度的结构化稀疏如何在现有 GPU 上获得真实加速，而不是停留在剪枝层面。
- 摘要给出的系统机制是具体的，不是泛泛稀疏论文：稀疏模式重写、激活重排融合、vLLM 集成、跨多代 NVIDIA GPU 验证。
- 如果你关心吞吐收益到底来自哪里，这篇文章值得细读，因为它把收益来源明确指向对 2:4 Sparse Tensor Core 路径的复用，而非单纯模型压缩。

## Risks Or Limits
- 从摘要看，方法明显依赖 NVIDIA 的 2:4 Sparse Tensor Core 路径及其软件栈，对非 NVIDIA 硬件或没有对应稀疏单元的后端可迁移性有限。
- 1.33x 的结果是在 compute-bound workload 下给出的；真实线上 serving 若更多受 memory、KV cache、调度或小 batch 影响，端到端收益可能明显缩水。

## Recommended For
- 做 vLLM、serving runtime 或 GPU inference kernel 优化的工程师
- 研究结构化稀疏、量化与 kernel/runtime 协同设计的系统研究者
- 关注 NVIDIA GPU 上 LLM 推理吞吐与精度折中的编译器和低层代码生成研究者

## Keywords
- LLM推理系统
- 结构化稀疏
- 2:4 Sparse Tensor Core
- 6:8稀疏
- vLLM
- 量化融合耦合执行路径

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
