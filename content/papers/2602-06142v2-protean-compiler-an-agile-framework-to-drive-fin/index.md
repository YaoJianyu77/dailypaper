---
paper_id: 2602.06142v2
title: 'Protean Compiler: An Agile Framework to Drive Fine-grain Phase Ordering'
authors:
- Amir H. Ashouri
- Shayan Shirahmad Gale Bagi
- Kavin Satheeskumar
- Tejas Srikanth
- Jonathan Zhao
- Ibrahim Saidoun
- Ziwen Wang
- Bryan Chan
- Tomasz S. Czajkowski
domain: LLM Code Generation For CUDA Kernels
slug: 2602-06142v2-protean-compiler-an-agile-framework-to-drive-fin
published: '2026-02-05T19:24:05Z'
summary: 这是一篇把细粒度 phase ordering 直接做进 LLVM 的编译器框架论文，亮点是内建特征与可插拔 ML/LLM 接口，但与 LLM inference
  或 CUDA kernel 的直接关联较弱。
source_url: http://arxiv.org/abs/2602.06142v2
pdf_url: https://arxiv.org/pdf/2602.06142v2
scores:
  relevance: 2.33
  recency: 3.0
  popularity: 1.3
  quality: 0.9
  recommendation: 7.22
tags:
- paper-note
status: generated
updated: '2026-03-08'
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- LLVM
- phase ordering
- 编译优化
- 静态特征
- ML for compilers
- Cbench
reading_priority: low
analysis_priority_rank: 3
selected_for_full_analysis: false
---

# Protean Compiler: An Agile Framework to Drive Fine-grain Phase Ordering

## TL;DR
这是一篇把细粒度 phase ordering 直接做进 LLVM 的编译器框架论文，亮点是内建特征与可插拔 ML/LLM 接口，但与 LLM inference 或 CUDA kernel 的直接关联较弱。

## 中文摘要
这篇论文针对经典的 compiler phase ordering 难题，提出一个直接集成到 LLVM 的细粒度优化框架 Protean Compiler。摘要称其内置 140 多种静态特征采集方法，并支持接入第三方 ML 框架和 LLM 做两步优化，相对 LLVM O3 在 Cbench 上取得平均最高 4.1%、个别应用最高 15.7% 的速度提升，代价是额外数秒编译时间。它更像一篇通用编译优化基础设施论文，而不是面向 LLM inference 或 CUDA kernel generation 的 systems paper；硬件前提、模型细节和 baseline 公平性仍需通读正文核对。

## Quick Facts
- Paper ID: `2602.06142v2`
- Authors: Amir H. Ashouri, Shayan Shirahmad Gale Bagi, Kavin Satheeskumar, Tejas Srikanth, Jonathan Zhao, Ibrahim Saidoun, Ziwen Wang, Bryan Chan, Tomasz S. Czajkowski
- Institutions: Institution information not extracted
- Domain: LLM Code Generation For CUDA Kernels
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-02-05T19:24:05Z
- Source page: [open](http://arxiv.org/abs/2602.06142v2)
- PDF: [download](https://arxiv.org/pdf/2602.06142v2)
- Reading priority: low
- Why this priority: 这篇论文在编译器方法上有一定价值，但摘要没有显示其直接面向 LLM inference、CUDA kernel generation、PTX/SASS 或特定 GPU，因此与当前 systems 主线的贴合度偏低，更适合作为外围 LLVM 优化参考。

## Research Background And Motivation
编译器 phase ordering 自上世纪以来一直难解，因为优化空间巨大，而且不同程序、不同代码区域往往需要不同的 pass 顺序。过去的 ML for compilers 工作不少，但很多方法没有无缝进入编译器主干，也难在更细粒度代码段上稳定落地。

## Problem Framing
论文要解决的是：如何把 phase ordering 从手工规则或外置模型，变成 LLVM 内部可用的细粒度能力，并在可接受的编译开销下改进最终代码性能。这个问题重要，因为固定的 O3 式优化流水线难以适配不同程序特征，而 pass 顺序又会直接影响生成代码质量。

## Method Overview
作者提出 Protean Compiler，把 phase-ordering 能力直接内建到 LLVM。核心组成包括一个覆盖不同作用域的 140 多种手工静态特征采集库，以及便于接入第三方 ML 框架和 LLM 的接口；摘要还提到一种两步优化流程，但没有充分说明具体搜索策略、模型形式和与 LLVM pass 管理机制的交互细节。

## Experimental Setup And Evidence
摘要给出的证据主要是 Cbench 上相对 LLVM O3 的性能结果：平均最高 4.1% 加速，部分应用最高 15.7%，代价是额外数秒构建时间；另外在 Susan 和 Jpeg 上，接入第三方 ML/LLM 的两步优化分别报告 10.1% 和 8.5% 提升。摘要没有充分说明硬件平台、统计方式、训练与推理成本、baseline 公平性，也没有说明对 GPU kernel 或 LLM workloads 的适用性。

## Research Or Engineering Value
如果方法成立，它的实际价值在于把 phase ordering 从固定编译级别升级为可学习、可扩展、可插拔的 LLVM 能力，为低层代码生成提供更细粒度的性能调优入口。对研究者，它提供了把模型驱动优化真正嵌入编译器的基础设施；对工程侧，它可能意味着无需重写整条编译链，就能针对特定 workload 增量引入更有针对性的优化决策。

## Reading Checklist
- 细粒度 scope 到底是 function、loop、basic block 还是更小代码段，phase-ordering 决策在 LLVM 流水线中的触发点是什么？
- 相对 O3 的比较是否把特征提取、模型推理、搜索时间都算入编译开销，额外数秒在更大程序或真实工程构建中会如何放大？
- 第三方 ML/LLM 的两步优化具体如何接入，是否需要离线训练或在线推理，能否迁移到 GPU kernel / PTX 级代码生成场景？

## Core Contributions
- 提出 Protean Compiler，把细粒度 phase ordering 作为 LLVM 内建能力而不是外部附加工具。
- 提供覆盖不同作用域的 140 多种手工静态特征采集方法，作为优化决策输入。
- 给出与第三方 ML 框架和 LLM 的接入路径，并报告相对 O3 的初步性能收益。

## Why Read It
- 想看它如何把 phase ordering 真正做进 LLVM 主体，而不是停留在离线模型或研究原型层面。
- 想评估细粒度特征采集和局部优化决策是否能成为后续低层代码生成、自动调优或编译器-模型协同设计的基础设施。
- 想核对摘要中的收益是否来自更好的 pass 顺序本身，而不是 benchmark 选择、范围限制或 baseline 设定。

## Risks Or Limits
- 与当前关注方向的贴合度有限：摘要没有说明 CUDA、PTX/SASS、特定 GPU 或 LLM inference serving 场景。
- 实验证据主要来自 Cbench；对大模型推理、kernel 生成或真实生产编译流水线的外推性不清楚。

## Recommended For
- 做 LLVM pass、phase ordering、ML for compilers 的研究者。
- 关注编译器基础设施如何接入外部模型或 LLM 的工程师。
- 想把通用编译优化思路迁移到低层代码生成系统的人，但不适合只关心 LLM serving 的读者优先阅读。

## Keywords
- LLVM
- phase ordering
- 编译优化
- 静态特征
- ML for compilers
- Cbench

## Abstract
The phase ordering problem has been a long-standing challenge since the late 1970s, yet it remains an open problem due to having a vast optimization space and an unbounded nature, making it an open-ended problem without a finite solution, one can limit the scope by reducing the number and the length of optimizations. Traditionally, such locally optimized decisions are made by hand-coded algorithms tuned for a small number of benchmarks, often requiring significant effort to be retuned when the benchmark suite changes. In the past 20 years, Machine Learning has been employed to construct performance models to improve the selection and ordering of compiler optimizations, however, the approaches are not baked into the compiler seamlessly and never materialized to be leveraged at a fine-grained scope of code segments. This paper presents Protean Compiler: An agile framework to enable LLVM with built-in phase-ordering capabilities at a fine-grained scope. The framework also comprises a complete library of more than 140 handcrafted static feature collection methods at varying scopes, and the experimental results showcase speedup gains of up to 4.1% on average and up to 15.7% on select Cbench applications wrt LLVM's O3 by just incurring a few extra seconds of build time on Cbench. Additionally, Protean compiler allows for an easy integration with third-party ML frameworks and other Large Language Models, and this two-step optimization shows a gain of 10.1% and 8.5% speedup wrt O3 on Cbench's Susan and Jpeg applications. Protean compiler is seamlessly integrated into LLVM and can be used as a new, enhanced, full-fledged compiler. We plan to release the project to the open-source community in the near future.

## Recommendation Signals
- Recommendation score: 7.22
- Relevance score: 2.33
- Recency score: 3.0
- Popularity score: 1.3
- Quality score: 0.9
- Analysis candidate score: 7.18
- Analysis priority rank: 3
- Analysis signals: llvm, benchmark, speedup
