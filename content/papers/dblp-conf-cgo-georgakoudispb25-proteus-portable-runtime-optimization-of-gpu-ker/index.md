---
paper_id: dblp:conf/cgo/GeorgakoudisPB25
title: 'Proteus: Portable Runtime Optimization of GPU Kernel Execution with Just-in-Time
  Compilation.'
authors:
- Giorgis Georgakoudis
- Konstantinos Parasyris
- David Beckingsale
domain: LLM Code Generation For CUDA Kernels
slug: dblp-conf-cgo-georgakoudispb25-proteus-portable-runtime-optimization-of-gpu-ker
published: '2025'
summary: 用语言无关 LLVM IR 做 GPU kernel 运行时特化，目标是在 AMD 和 NVIDIA 上以较低 JIT 开销换取比 AOT 更好的端到端性能。
source_url: https://dl.acm.org/doi/10.1145/3696443.3708939
pdf_url: ''
scores:
  relevance: 1.63
  recency: 0.0
  popularity: 2.0
  quality: 2.0
  recommendation: 5.46
tags:
- paper-note
status: generated
updated: '2026-03-08'
institutions:
- Lawrence Livermore National Laboratory
venue_or_journal: CGO
citation_summary: 2 citations
keywords:
- GPU kernel JIT
- LLVM IR
- 运行时特化
- 跨厂商 GPU
- AOT 与 JIT 比较
reading_priority: medium
analysis_priority_rank: 5
selected_for_full_analysis: false
---

# Proteus: Portable Runtime Optimization of GPU Kernel Execution with Just-in-Time Compilation.

## TL;DR
用语言无关 LLVM IR 做 GPU kernel 运行时特化，目标是在 AMD 和 NVIDIA 上以较低 JIT 开销换取比 AOT 更好的端到端性能。

## 中文摘要
Proteus 试图把 GPU kernel 的运行时特化做成一个轻量、可移植的 JIT 流程：动态提取语言无关 LLVM IR，再按输入参数和 launch 参数重新编译优化。摘要声称它在 AMD 和 NVIDIA GPU 上都能相对 AOT 获得端到端加速，并平均优于 CUDA 专用的 Jitify，说明作者把重点放在降低 JIT 开销同时生成更合适的目标代码。对 systems 读者，这篇的看点是跨厂商 GPU 的 runtime/compiler 协同设计；但收益到底来自哪些 kernel、哪些运行时信息、以及 baseline 是否公平，摘要没有充分说明。

## Quick Facts
- Paper ID: `dblp:conf/cgo/GeorgakoudisPB25`
- Authors: Giorgis Georgakoudis, Konstantinos Parasyris, David Beckingsale
- Institutions: Lawrence Livermore National Laboratory
- Domain: LLM Code Generation For CUDA Kernels
- Venue / Journal: CGO
- Citations: 2 citations
- Published: 2025
- Source page: [open](https://dl.acm.org/doi/10.1145/3696443.3708939)
- PDF: not found from current source metadata
- Reading priority: medium
- Why this priority: 这篇与 GPU kernel runtime specialization、LLVM IR 级可移植 JIT、以及跨 AMD/NVIDIA 的低层优化直接相关，和当前关注的 kernel 生成与系统优化方向有交集；但它并非面向 LLM inference/serving 的专门工作，收益来源、硬件前提和 baseline 公平性仍需通读确认。

## Research Background And Motivation
GPU/HPC 程序通常依赖 AOT 编译，而 AOT 在编译时拿不到真实输入、launch 参数和运行环境，因此会错过很多只在运行时才成立的优化机会。随着异构 GPU 与多语言生态并存，研究者希望用更可移植的运行时编译框架补上这部分信息缺口。

## Problem Framing
这篇工作要解决的问题是：能否在不过度侵入现有代码、也不绑定单一语言或单一 GPU 厂商工具链的前提下，在运行时利用输入参数和 launch 参数对 GPU kernel 做特化，并把 JIT 开销压到足以换回端到端收益。这个问题重要，因为很多 kernel 的最佳代码形态依赖运行时信息，而过重或过于厂商绑定的 JIT 会直接限制工程可用性。

## Method Overview
Proteus 的核心做法是动态提取语言无关的 LLVM IR，只在运行时对相关 GPU kernel 重新编译和优化，并通过最小侵入的注解接口把输入参数与 launch 参数暴露给特化流程。相比语言或平台专用方案，它把可移植性放在 LLVM IR 层，同时试图通过降低编译对象和编译流程开销来控制 JIT 成本。

## Experimental Setup And Evidence
摘要给出的证据是：在一组多样化程序上、覆盖 AMD 和 NVIDIA GPU，Proteus 相对 AOT 获得最高 2.8×（AMD）和 1.78×（NVIDIA）的端到端加速，并相对 CUDA 专用 Jitify 达到平均 1.23× 提升。摘要将收益归因于更低的编译开销以及在某些情况下更快的二进制代码，但 benchmark 构成、GPU 型号、开销拆分、baseline 配置和受益 kernel 分布，摘要没有充分说明。

## Research Or Engineering Value
如果结论成立，这项工作说明 GPU kernel 的 runtime specialization 可以在不强绑定单一语言或单一 GPU 生态的情况下带来实用收益，对跨厂商加速库、编译器与运行时协同设计，以及未来面向 LLM inference kernel 的动态代码生成都有直接工程启发。它的实际价值在于把“何时值得 JIT”和“如何可移植地 JIT”结合成一个可落地框架。

## Reading Checklist
- 端到端加速里，编译开销下降、kernel 执行时间下降、以及 launch 参数特化三者各自贡献了多少？
- Proteus 需要开发者添加哪些注解；这些注解在不同语言、编程模型或框架边界上会不会削弱其“语言无关”主张？
- AMD 与 NVIDIA 上使用了哪些硬件和编译后端，和 AOT/Jitify 的对比是否在缓存、预热和测量口径上保持公平？

## Core Contributions
- 提出一个面向 GPU kernel 的轻量 JIT 框架，可在运行时提取并利用语言无关 LLVM IR。
- 通过最小侵入的注解接口，让 kernel 能按输入参数和 launch 参数进行运行时特化。
- 在 AMD 和 NVIDIA GPU 上对比 AOT 与 CUDA 专用 Jitify，主张其兼顾可移植性、较低开销与性能收益。

## Why Read It
- 它直接回答一个 systems 核心问题：runtime specialization 的收益能否覆盖 JIT 成本。
- 跨 AMD/NVIDIA 的设计比只讨论 CUDA 工具链更有参考价值，适合评估可移植 GPU 编译/runtime 路线。
- 如果你关心 LLM inference kernel 或低层代码生成，这篇可以作为通用 GPU JIT 框架的对照，帮助判断哪些机制值得迁移到 serving 场景。

## Risks Or Limits
- 论文场景来自通用 HPC 程序，不是 LLM inference/serving；任务形态迁移性需要谨慎判断。
- 收益可能集中在少数特定输入分布、launch 参数或 kernel 类型上，摘要没有充分说明覆盖面。

## Recommended For
- GPU 编译器与运行时研究者
- 做 CUDA/HIP/LLVM kernel 优化的工程师
- 评估 LLM inference kernel 动态特化可行性的系统研究者

## Keywords
- GPU kernel JIT
- LLVM IR
- 运行时特化
- 跨厂商 GPU
- AOT 与 JIT 比较

## Abstract
In High-performance computing (HPC) fast application execution is the primary objective. HPC software is written in high-performance languages (C/C++, Fortran) and is statically compiled Ahead-of-Time (AOT) using optimizing compilers to generate fast code. AOT compilation optimizes source code with only limited information available at compile time, which precludes possible optimization leveraging runtime information. We propose Proteus, an easy-to-use, portable, and lightweight Just-In-Time (JIT) compilation approach to optimize GPU kernels at runtime. Proteus dynamically extracts, compiles, and optimizes language-agnostic LLVM IR to reduce compilation overhead while enhancing portability and versatility compared to language-specific solutions. Using a minimally intrusive annotation-based interface, Proteus specializes GPU kernels for input arguments and launch parameters. Evaluation on a diverse set of programs on AMD and NVIDIA GPUs shows that Proteus achieves significant end-to-end speedup, up to 2.8× for AMD and 1.78× on NVIDIA, over AOT optimization, while outperforming CUDA-specific Jitify with an average 1.23× speedp, thanks to reduced overhead and faster binary code in certain cases.

## Recommendation Signals
- Recommendation score: 5.46
- Relevance score: 1.63
- Recency score: 0.0
- Popularity score: 2.0
- Quality score: 2.0
- Analysis candidate score: 5.43
- Analysis priority rank: 5
- Analysis signals: gpu kernel
