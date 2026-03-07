---
paper_id: 2603.05500v1
title: 'POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation'
authors:
- Zeju Qiu
- Lixin Liu
- Adrian Weller
- Han Shi
- Weiyang Liu
domain: Large Language Models
slug: 2603-05500v1-poet-x-memory-efficient-llm-training-by-scaling
published: '2026-03-05T18:59:23Z'
summary: 这篇工作把 POET 的稳定训练路线从“理论上有吸引力”推进到“单卡也可能跑得动”的工程形态。
source_url: https://arxiv.org/abs/2603.05500v1
pdf_url: https://arxiv.org/pdf/2603.05500v1.pdf
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 1.2
  quality: 1.2
  recommendation: 8.2
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- LLM 训练
- 内存效率
- 正交等价变换
- POET-X
- 训练稳定性
reading_priority: high
image_count: 5
analysis_depth: full
full_analysis_source: arxiv_source
---

# POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation

## TL;DR
这篇工作把 POET 的稳定训练路线从“理论上有吸引力”推进到“单卡也可能跑得动”的工程形态。

## 中文摘要
POET-X 是对 POET 的系统级改造版，目标是在保留谱保持和训练稳定性优势的同时，大幅降低内存与计算开销。摘要称它能显著改善吞吐和显存效率，并支持在单张 H100 上预训练十亿参数 LLM，而同设定下 AdamW 会直接爆显存。真正值得核对的是它是否在不同规模和任务上都保住了训练质量，因为这些细节摘要没有充分说明。

## Quick Facts
- Paper ID: `2603.05500v1`
- Authors: Zeju Qiu, Lixin Liu, Adrian Weller, Han Shi, Weiyang Liu
- Domain: Large Language Models
- Published: 2026-03-05T18:59:23Z
- arXiv: [abstract](https://arxiv.org/abs/2603.05500v1)
- PDF: [download](https://arxiv.org/pdf/2603.05500v1.pdf)
- Reading priority: high
- Why this priority: 工程价值直接，且摘要给出明确硬件对比；但仍需核对它是否真正保住了训练质量和可迁移性。

## Abstract Translation
大语言模型的高效且稳定训练仍是现代机器学习系统中的核心挑战。为解决这一问题，已有工作提出了重参数化正交等价训练（POET）：它通过正交等价变换来优化每个权重矩阵，并保持谱性质不变。尽管 POET 具有较强的训练稳定性，但其原始实现因大量矩阵乘法而带来较高的显存占用和计算开销。为克服这些限制，本文提出 POET-X，这是一种可扩展且更省内存的变体，能够以显著更低的计算代价执行正交等价变换。POET-X 在保持 POET 泛化与稳定性优势的同时，显著提升了吞吐和显存效率。实验中，POET-X 据称可以在单张 Nvidia H100 上完成十亿级参数 LLM 的预训练，而相同设置下 AdamW 会因显存不足而失败。

## Research Background And Motivation
LLM 训练一方面需要更高稳定性，另一方面又越来越受限于显存、吞吐和系统成本。POET 这类通过保持谱性质来增强稳定性的路线在理论上有吸引力，但原始实现的矩阵乘法和激活保存成本过高，导致它难以真正用于大规模预训练。

## Problem Framing
论文要解决的不是“再发明一个优化器”，而是如何把 POET 这种基于正交等价变换的稳定训练框架做成真正可扩展的系统：既保留谱保持与训练稳定性，又把显存和计算成本降到足以支撑大模型预训练的水平。这个问题重要，因为很多更稳的训练方法最终都败在系统代价上，无法进入实际训练栈。

## Method Overview
POET-X 延续 POET 的核心参数化思路：用左右两个可训练正交矩阵去变换固定基权重矩阵，从而在保持谱性质的同时学习权重；训练结束后这些变换可以并回原权重，因此没有推理额外开销。它的主要贡献不在新的优化目标，而在把原本昂贵的正交等价变换拆解为一组更省显存、更少数据搬运、更适合 GPU 并行执行的计算过程，并在需要时进一步结合 checkpointing 和量化来压缩训练内存。

### Method Figure
![cnp-crop_page1](images/cnp-crop_page1.png)

*Figure cue:* Illustration of efficient Cayley-Neumann parameterization (batch-wise implementation).

## Method Details
- 将原始的 weight-centric 实现改写为 input-centric 线性映射序列，把“显式构造和保存变换后权重/中间激活”的做法改为围绕输入执行若干矩阵-向量或等价线性操作，以减少反向传播所需保存的激活。
- 建立在 block-stochastic POET 上，利用块对角稀疏正交矩阵与随机置换矩阵的结构，让更新覆盖更均衡；实现时不再显式构造大块对角稀疏矩阵，而是把每个块当作独立小矩阵进行 batch-parallel 乘法。
- 对置换操作做两层优化：一是用自定义 CUDA 索引映射代替显式置换矩阵，二是在内层优化阶段把部分置换预先并入固定权重，减少重复置换次数和访存开销。
- 重新实现 Cayley-Neumann Parameterization：只存 skew-symmetric 矩阵的上三角部分，把参数量、梯度和优化器状态直接减半；同时重排 CNP 计算，使前向和反向都可在 Triton kernel 中做共享内存复用与算子融合。
- 提出两种内存/速度折中版本：一个沿用标准 Autograd 保存额外激活，另一个通过 gradient checkpointing 在反向时重算中间量以进一步省显存；基于这一机制又扩展出只存低比特基模型权重、按需反量化的 POET-XQ。

## Experimental Setup And Evidence
提取文本显示实验分为三层。第一层是单层 profiling，对比原始 POET、POET-X 变体和标准线性层的前后向时延，并分析单卡训练时的显存构成。第二层是大规模预训练：在 C4 上训练 Llama-3B，并与 AdamW、Muon、GaLore、APOLLO 比较；文中说训练预算参考 Chinchilla 比例，使用 60B tokens。第三层是效率与扩展性分析，包括单卡 Llama-8B 的显存分解、基于 GPU hours 的验证困惑度曲线，以及 32 张 H100（4 节点，每节点 8 卡）上的 wall-clock 与吞吐扩展。更细的超参数、block size 取值、学习率和训练配方，提取文本没有充分说明。

### Experiment Figure
![linear_breakdown_page1](images/linear_breakdown_page1.png)

*Figure cue:* Latency breakdown of POET, POET-X, and PyTorch Linear Layers with sequence length 2048 and block size .

## Main Results And Claims
提取文本支持以下结论。相对原始 POET，POET-X 在作者报告中实现了约 3 倍 GPU 显存下降和 8 倍运行速度提升。单层 profiling 中，原始 POET 的一次前后向总时延从 10.59ms 降到 POET-X 两个变体的 1.38ms 和 1.89ms，且其反向延迟已接近标准线性层。显存分解显示，原始 POET 因保存变换后权重等激活而可能比 AdamW 更耗内存，而 POET-X 两个变体呈现出更接近 PEFT 方法的显存结构。多节点 Llama-3B 预训练中，POET-X 的验证困惑度优于 AdamW 和其他内存友好方法，略逊于 Muon，但使用更低 GPU 内存；同时文中声称其 wall-clock 效率也优于 AdamW。摘要和引言还声称在单张 H100 上可进行十亿级甚至最高到 13B 规模模型的预训练，但对应配置与完整证据在提取文本中没有充分展开。

## Research Or Engineering Value
如果论文结论成立，POET-X 的价值主要在两点。第一，它把原本更像研究型想法的 POET 推进成接近可落地的大模型训练方案，使“更稳的训练参数化”不再天然意味着巨额显存和吞吐损失。第二，它为资源受限环境提供了更有吸引力的预训练选项：不是单纯省一点优化器状态，而是通过重写整个正交变换计算链条，把单卡或小规模集群能尝试的模型规模继续往上推。对研究者而言，这也意味着正交约束、谱保持和稀疏训练之间的结合开始具备系统可行性。

## Relation To Prior Work
相对常见的 AdamW、Muon 这类“直接在稠密权重或梯度空间改更新规则”的路线，POET-X 走的是重参数化路线：它不直接改写基础权重的更新，而是通过左右正交变换来学习权重，从而显式保留谱性质。相对 LoRA、GaLore、APOLLO 这类主要从低秩、梯度压缩或内存友好优化器角度降成本的方法，POET-X 的差异在于它把“结构化正交变换”作为训练主对象，并试图让这种参数效率真正转化为系统显存效率。相对原始 POET，本文不是再强调稳定性理论，而是把重点转向 OET 的可扩展实现，核心增量是 input-centric 重写、置换/块计算优化和高效 CNP，而不是新的训练目标。

## Overall Assessment
这篇论文现在值得读，原因不是它又提出了一个训练算法名词，而是它试图把“谱保持/正交变换带来稳定性”这条路线从理论上可取推进到系统上可跑。最值得信的部分，是它对原始 POET 瓶颈的拆解相当具体，input-centric 重写、置换规约、块并行和高效 CNP 之间的逻辑链条完整，而且单层 profiling 与显存分解也和这个故事一致。最该怀疑的部分，是质量与泛化是否在更大规模、更长训练和更多任务上稳定保留；提取文本虽然给出优于 AdamW 的结论和略逊 Muon 的定位，但完整数字、设置公平性、硬件依赖和 13B 单卡主张的细节都没有充分展开。因此，我会把它看成一篇很强的系统化训练工程论文，但在把它当成“普适替代 AdamW 的新范式”之前，还需要更仔细核对实验边界。

## Strengths
- 问题定义清晰：不是泛泛谈训练稳定性，而是直接瞄准“稳定方法为何在系统层面跑不起来”这一瓶颈。
- 方法是成体系的工程改造，而非单一技巧，覆盖计算重写、稀疏结构利用、置换优化、参数化压缩、kernel fusion、checkpointing 和量化支持。
- 保留了 POET 的核心结构优势：谱保持、稀疏训练动机，以及训练后可并回权重、无推理额外开销。
- 实验设计至少覆盖了算子级、单卡显存级和多节点预训练级三个层次，能较完整地支撑“系统可扩展性”叙事。

## Future Work
- 补齐跨规模质量验证，尤其是从 3B、8B 到文中宣称的更大规模时，训练稳定性、最终困惑度和 wall-clock 成本是否仍保持优势。
- 分析不同 block size、置换策略、checkpointing 选择和量化设置对收敛质量与效率的联合影响，而不只给总吞吐或总显存。
- 验证自定义 CUDA/Triton 实现对硬件代际、互联方式和软件栈版本的敏感性，确认方法不是仅在特定 H100 环境下成立。
- 更系统地研究 CNP 近似误差与正交性偏差在长程预训练中的累积效应。

## Reading Checklist
- 先确认 POET 的基础参数化到底固定了什么、学习了什么，以及“谱保持”为什么能带来训练稳定性。
- 重点看 input-centric 实现的推导，核对它究竟省掉了哪些中间激活，哪些张量在反向中仍必须访问。
- 检查置换加速与 permutation reduction 的具体执行顺序，确认它们是否只是工程常数优化，还是也改变了实际内存峰值。
- 细读高效 CNP 部分，尤其是上三角存储、kernel fusion 和前后向共享内存复用各自贡献了多少。提取文本对分项贡献有方向性描述，但完整拆分仍需看正文表格。

## Core Contributions
- 提出 POET 的可扩展变体 POET-X，专门解决原方法的高显存和高计算瓶颈。
- 在不改变核心稳定训练动机的前提下，重新设计正交等价变换的执行方式。
- 给出单张 H100 预训练十亿参数 LLM 的可行性主张，并以 AdamW 显存不足作为对照。

## Why Read It
- 训练效率论文里少见同时抓稳定性和显存，切入点比常规优化器微调更有结构性。
- 单卡十亿参数的主张很硬，值得核对实现细节和真实边界。
- 如果你关心更稳的预训练，这篇论文提供了一个不同于 AdamW 路线的选择。

## Risks Or Limits
- 许多关键实验细节在提取文本里不完整，尤其是具体超参数、block size 选择、训练步数和完整最终质量数字，因此结果可复现性目前难判断。
- “保留 POET 的泛化和稳定性优势”是核心卖点，但提取文本对稳定性指标、不同模型规模和不同任务上的一致性说明不足。
- 收益高度依赖自定义 CUDA/Triton kernel 与特定 GPU 执行路径，跨硬件平台或跨软件栈迁移后的效果存在不确定性。
- CNP 本身是近似正交化，论文称轻微偏离正交性不影响性能，但提取文本没有充分说明这种近似在更长训练、更大模型下是否会累积风险。

## Recommended For
- 做大模型预训练系统与优化器研究的读者
- 资源受限但想跑更大模型的工程师
- 关注训练稳定性与参数化方法的研究者

## Keywords
- LLM 训练
- 内存效率
- 正交等价变换
- POET-X
- 训练稳定性

## Additional Figures

![matrix_coverage_new_page1](images/matrix_coverage_new_page1.png)

*Figure cue:* Fully-stochastic POET (with ) vs. block-stochastic POET (with ) for the weight matrix update coverage. In the toy experiment, we use a weight matrix and run both POET variants for 100-step update, so 200 are the largest possible update steps (multiplication by and counts as two updates). Block-stochastic POET ensures balanced update for the weight matrix while fully-stocahstic POET does not.

![memory_breakdown_page1](images/memory_breakdown_page1.png)

*Figure cue:* Memory breakdown for training Llama-8B on a single GPU across different methods with batch size 1, sequence lengths 1024 and block size . Since POET~ runs OOM under this setting, we estimate its memory footprint by profiling memory usage across different numbers of decoder layers (i.e., parameter sizes) and applying scaling.

![val_ppl_256_page1](images/val_ppl_256_page1.png)

*Figure cue:* Validation perplexity dynamics with respect to GPU hours for training Llama-8B with (5B tokens) and (10B tokens), respectively.
- Full asset manifest: [images/index.md](images/index.md)

## Abstract
Efficient and stable training of large language models (LLMs) remains a core challenge in modern machine learning systems. To address this challenge, Reparameterized Orthogonal Equivalence Training (POET), a spectrum-preserving framework that optimizes each weight matrix through orthogonal equivalence transformation, has been proposed. Although POET provides strong training stability, its original implementation incurs high memory consumption and computational overhead due to intensive matrix multiplications. To overcome these limitations, we introduce POET-X, a scalable and memory-efficient variant that performs orthogonal equivalence transformations with significantly reduced computational cost. POET-X maintains the generalization and stability benefits of POET while achieving substantial improvements in throughput and memory efficiency. In our experiments, POET-X enables the pretraining of billion-parameter LLMs on a single Nvidia H100 GPU, and in contrast, standard optimizers such as AdamW run out of memory under the same settings.

## Recommendation Signals
- Recommendation score: 8.2
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.2
- Quality score: 1.2

## Assets
- Extracted assets are stored in the `images/` folder next to this page.
- Browse the image manifest here: [images/index.md](images/index.md)
