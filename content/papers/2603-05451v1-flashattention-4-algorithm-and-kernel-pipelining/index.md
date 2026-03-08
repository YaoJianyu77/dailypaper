---
paper_id: 2603.05451v1
title: 'FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric
  Hardware Scaling'
authors:
- Ted Zadouri
- Markus Hoehnerbach
- Jay Shah
- Timmy Liu
- Vijay Thakkar
- Tri Dao
domain: LLM Inference Systems
slug: 2603-05451v1-flashattention-4-algorithm-and-kernel-pipelining
published: '2026-03-05T18:24:49Z'
summary: 这篇工作把注意力优化从面向 H100 的 kernel 调参，推进到面向 Blackwell 非对称硬件扩展的算法与流水线协同设计。
source_url: http://arxiv.org/abs/2603.05451v1
pdf_url: https://arxiv.org/pdf/2603.05451v1
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 1.3
  quality: 1.3
  recommendation: 9.38
tags:
- paper-note
status: generated
updated: '2026-03-08'
institutions:
- Princeton University
- Colfax Research
- NVIDIA
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- FlashAttention
- Blackwell GPU
- B200
- GB200
- attention kernel
- kernel pipelining
reading_priority: high
analysis_priority_rank: 1
selected_for_full_analysis: true
image_count: 10
table_count: 1
analysis_depth: full
full_analysis_source: arxiv_source
---

# FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling

## TL;DR
这篇工作把注意力优化从面向 H100 的 kernel 调参，推进到面向 Blackwell 非对称硬件扩展的算法与流水线协同设计。

## 中文摘要
这篇论文针对 Blackwell GPU 上 tensor core 吞吐增长快于 shared memory 带宽和 exponential 单元的“非对称扩展”问题，重新设计了 attention 的算法与 kernel 流水线。核心做法包括利用全异步 MMA 和更大 tile 的新流水线、用软件模拟 exponential 与条件式 softmax rescaling 减少非 matmul 操作，以及借助 tensor memory 和 2-CTA MMA 降低反向传播中的 shared memory 流量与 atomic add。摘要称其在 B200 的 BF16 设置下相对 cuDNN 9.13 最多提速 1.3 倍、相对 Triton 最多提速 2.7 倍，并达到 1613 TFLOPs/s（71% 利用率）；同时用 CuTe-DSL 实现后，编译时间相对传统 C++ 模板方式快 20-30 倍。摘要没有充分说明不同序列长度、batch/head 配置、端到端 serving 指标和基线公平性。

## Quick Facts
- Paper ID: `2603.05451v1`
- Authors: Ted Zadouri, Markus Hoehnerbach, Jay Shah, Timmy Liu, Vijay Thakkar, Tri Dao
- Institutions: Princeton University, Colfax Research, NVIDIA
- Domain: LLM Inference Systems
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-03-05T18:24:49Z
- Source page: [open](http://arxiv.org/abs/2603.05451v1)
- PDF: [download](https://arxiv.org/pdf/2603.05451v1)
- Reading priority: high
- Why this priority: 这篇论文与当前 Blackwell 代的 LLM inference/attention kernel 优化高度相关，直接命中本项目最关心的硬件假设、kernel 级收益和低层实现路径。摘要已经给出明确的吞吐、利用率和编译时间信号，值得优先读全文核对其实验公平性、数值稳定性和硬件依赖边界。

## Abstract Translation
注意力作为普遍使用的 Transformer 架构中的核心层，是大语言模型和长上下文应用的瓶颈。尽管 FlashAttention-3 通过异步执行和 warp specialization 针对 Hopper GPU 优化了 attention，但它主要面向 H100 架构。AI 行业已经迅速转向部署基于 Blackwell 的系统，例如 B200 和 GB200；由于非对称硬件扩展，这些系统呈现出根本不同的性能特征：tensor core 吞吐翻倍，而 shared memory 带宽和 exponential 单元扩展较慢或基本不变。我们提出了若干技术来应对 Blackwell GPU 上这些转移后的瓶颈：(1) 重新设计流水线，利用完全异步的 MMA 操作和更大的 tile；(2) 用软件模拟 exponential 与条件式 softmax rescaling，减少非 matmul 操作；(3) 利用 tensor memory 和 2-CTA MMA 模式，在反向传播中减少 shared memory 流量和 atomic add。我们表明，FlashAttention-4 在 B200 GPU 的 BF16 设置下，相比 cuDNN 9.13 最多快 1.3 倍、相比 Triton 最多快 2.7 倍，并达到最高 1613 TFLOPs/s（71% 利用率）。除算法创新外，我们还将 FlashAttention-4 完全实现为嵌入 Python 的 CuTe-DSL，在保持完整表达能力的同时，相比传统基于 C++ 模板的方法实现了 20-30 倍更快的编译时间。

## Research Background And Motivation
这篇论文的背景是，attention 仍然是 Transformer 系统里最稳定、最难绕开的高成本算子，而 GPU 代际升级并不会让所有硬件单元同步变快。Blackwell 上 tensor core 吞吐提升明显快于 shared memory、exp 单元和一般 ALU，因此原本围绕 matmul 组织的 attention kernel 设计开始被非 matmul 路径卡住。

## Problem Framing
论文要解决的问题是：在 Blackwell 这类“算得更快、但 shared memory 和 exponential 不够快”的非对称硬件上，如何重写 attention 的前后向 kernel，使真实瓶颈从 shared memory 流量、softmax 相关操作和反向原子归约中释放出来，而不是继续沿用主要为 H100/Hopper 调过参的实现。这个问题直接关系到 B200/GB200 上 dense attention 能否把更高的 tensor core 峰值转成实际 TFLOPs、吞吐和可用 kernel。

## Method Overview
FlashAttention-4 的核心不是单点 kernel trick，而是把 attention 视为一个需要围绕 Blackwell 资源失衡重新设计的算法-流水线协同问题。方法一方面重构前后向的软件流水线，让 fully asynchronous MMA、softmax 计算和数据搬运尽量重叠；另一方面专门削减 Blackwell 上更容易暴露出来的非 matmul 成本，包括 exponential 路径、shared memory 流量、以及 backward 中的 atomic reduction。实现层面则用 CuTe-DSL 取代重模板 C++，把低层控制能力和更快编译周期结合起来。

### Method Figure
![2cta_figure](images/2cta_figure.png)


### Implementation Table
*Table cue:* Compile time for a single kernel: FA3 (C++ templates) and FA4 (CuTe-DSL). Typically FA2 and FA3 require precompiling hundreds of kernels for different attention variants.

```text
Method | Forward pass | Backward pass
55s | 45s
2.5s | 1.4s
Speedup | 22 | 32
```

## Method Details
- 为前向和反向分别重写软件流水线，利用 Blackwell 的 fully asynchronous MMA 和更大 tile，在 tensor core、softmax 计算与内存操作之间做更强重叠。
- 在前向中用基于 FMA 单元的多项式近似来软件模拟 exponential，绕开 MUFU/exponential 单元吞吐不足的问题。
- 引入 conditional softmax rescaling，在不必要时跳过 rescaling，进一步减少 softmax 路径中的非 matmul 操作。
- 利用每个 SM 的 256 KB tensor memory（TMEM）存放更多 tensor core 中间结果，降低 shared memory 流量和寄存器压力，并支撑更大 tile。
- 在反向中利用 2-CTA MMA 模式让 CTA 对协同完成一次 MMA、各自只 staging 一半 operand B，同时重构 dQ 步骤，把全局 atomic reductions 数量减半；文中还配套了面向 Blackwell 资源约束的 CTA 调度、寄存器分配和 deterministic mode。

## Experimental Setup And Evidence
实验主要是 attention 单算子基准，而不是端到端 LLM serving。正文多处写在 B200 GPU 上测试 BF16/FP16 attention；附加实验细节段又写“B100 180GB SXM6 (1000W)”，硬件标注存在不一致，需要回原文核对。基准覆盖 causal/non-causal、head dimension 64、128 和 (192,128)，序列长度从 1k 到 32k，总 token 数固定为 32k，并随序列长度调整 batch size；hidden dimension 设为 2048。forward 和 backward 都报告性能，计时采用 5 次 warmup、10 次重复取平均；此外还包含 deterministic backward 的调度消融，以及 FA3（C++ templates）对比 FA4（CuTe-DSL）的单 kernel 编译时间表。

### Experiment Figure
![fa4_fwd_causalTrue_hdim192128_updated](images/fa4_fwd_causalTrue_hdim192128_updated.png)

*Figure cue:* Forward pass TFLOPS comparison between cuDNN and FA4 on B200 (FP16/BF16) with head dimension (192, 128) for causal attention (typically used in DeepSeek V3 architecture)

## Datasets And Benchmarks
- B200/BF16（正文主述）attention kernel benchmark：sequence length 1k-32k，total tokens 固定 32k，比较 causal 与 non-causal、head dim 64/128/(192,128) 的前向与反向性能。
- Deterministic backward benchmark：B200、head dim 128，下比较不同调度与 swizzle 策略在 causal/non-causal 条件下的性能。
- 单 kernel 编译时间 benchmark：FA3（C++ templates）对比 FA4（CuTe-DSL），分别统计 forward 和 backward 的编译耗时。

## Baselines
- PyTorch 标准 attention 实现
- Triton 实现
- Gluon
- cuDNN 9.13
- cuDNN 9.19.1.2
- FlashAttention-3（仅在编译时间表中作为 C++ templates 基线）

## Metrics
- 平均运行时间（5 次 warmup 后 10 次重复取均值）
- TFLOPs/s
- 相对 cuDNN / Triton 的 speedup
- 理论峰值利用率
- 单 kernel 编译时间
- deterministic backward 相对 nondeterministic backward 的速度比例

## Ablations And Analysis
- Roofline 分析：文中称在 Blackwell 的典型 attention 工作负载中，shared memory traffic 和 exponential operations 的时间开销比 MMA 计算高 25%-60%。
- Deterministic backward 调度消融：比较 SPT、LPT with reverse mblock order、LPT，以及 naive no batch/head swizzle。
- Non-causal deterministic backward 还比较了 batch/head swizzle 与 naive 调度。
- 编译时间表：FA3 前向 55s、反向 45s；FA4 前向 2.5s、反向 1.4s；对应 speedup 为 22x 和 32x。

### Analysis Figure
![causal_bwd_det_FA4](images/causal_bwd_det_FA4.png)

*Figure cue:* Ablations for Deterministic Backward pass on B200 (FP16/BF16) with head dimension 128. Causal attention -- SPT, LPT with reverse mblock order, LPT, and naive with no batch/head swizzle.

## Evaluation Validity And Fairness
- kernel benchmark 的序列长度、head dimension、mask 形态、总 token 数和 FLOPs 计算方式给得较具体，单算子实验设置相对清楚。
- 主要证据集中在 operator-level runtime 与 TFLOPs/s；提取文本没有充分说明端到端 LLM serving latency/throughput、完整训练 step 时间或系统级资源占用。
- 正文主文多次写 B200，但补充实验段写 B100 180GB SXM6，硬件标注不一致，会影响读者对结果平台的判断。
- 对 cuDNN 的领先幅度具有时间敏感性；图注明确写到较新的 cuDNN 已吸收本文许多技巧，性能与 FA4 接近。

## Main Results And Claims
提取文本支持的主要结论是：在 B200 上的 BF16/FP16 attention kernel 基准中，FA4 前向相对 cuDNN 9.13 达到 1.1-1.3x、相对 Triton 达到 2.1-2.7x，最高达到约 1613 TFLOPs/s，约为理论峰值的 71%。正文称在中长序列（4k 及以上）下，FA4 前向在不同 head dimension 和 causal/non-causal 设置中持续优于基线；反向在长序列和 causal masking 下也有一致加速，但提取文本没有给出精确倍数。Deterministic backward 最多达到 nondeterministic 1-CTA backward 约 75% 的速度。表格还显示，单 kernel 编译时间从 FA3 的前向 55s/反向 45s 降到 FA4 的前向 2.5s/反向 1.4s。与此同时，图注也说明更新版 cuDNN 已吸收许多本文技巧，性能与 FA4 接近。

## Research Or Engineering Value
对正在适配 B200/GB200 的工程团队，这篇论文的实际价值很高：它给出了一套相当具体的 dense attention 默认设计范式，解释性能到底来自哪里，尤其是 TMEM、2-CTA、softmax 路径和调度重构如何一起起作用。对编译器和 kernel 开发者，CuTe-DSL 的实现也说明高性能 attention 不一定非得依赖重模板 C++。但若部署栈已经能使用较新的 cuDNN，直接可兑现的额外速度空间可能没有摘要数字看上去那么大。

## Relation To Prior Work
相对早期 FlashAttention/FlashAttention-2 主要围绕 IO-aware tiling、kernel fusion 和序列维并行来减少 HBM 访问、提高 occupancy 的路线，这篇工作把核心矛盾转到了 Blackwell 上更突出的非 MMA 瓶颈。相对面向 Hopper 的 FlashAttention-3，它不只是继续强化异步执行和 warp specialization，而是显式围绕 fully asynchronous MMA、TMEM 和 2-CTA MMA 重写前后向流水线。相对 SageAttention 一类主要依赖低精度量化换吞吐的路线，FA4 仍然聚焦 BF16/FP16 dense attention，本质上是通过 softmax 路径改写、shared memory 流量压缩和原子操作重构来追求速度，而不是靠模型近似或权重量化。

## Overall Assessment
这是一篇很强的算子级 systems 论文候选，最值得信的是它对 Blackwell 非对称硬件扩展导致瓶颈迁移的判断，以及围绕 TMEM、fully asynchronous MMA、2-CTA 和 softmax 非 matmul 路径组织出的整套 kernel 方案；这些内容和给出的 benchmark 设定、编译时间表彼此一致，可信度较高。最该怀疑的是实验外推范围和比较边界：提取文本没有充分说明数值稳定性、模型精度、端到端 serving 收益，也没有充分说明在最新 cuDNN 下还剩多少真实优势，且 B200/B100 的硬件标注不一致需要核对。整体上，我会把它视为一篇对 Blackwell dense attention kernel 设计范式非常有参考价值的论文，但还不是一篇已经把通用系统收益完全坐实的结论性工作。

## Technical Route Positioning
这篇论文属于 LLM 系统里的算子级低层加速路线，更具体地说是 dense attention kernel 的算法-内核-编译器协同优化。它解决的是从 Blackwell 硬件原语到 attention 前后向 kernel 实现这一段链路中的问题：如何把更高的 tensor core 峰值真正转化为可观测吞吐，同时压低 softmax 的非 matmul 开销、shared memory 流量和 backward 原子归约成本。它不是 KV cache、调度器或 serving orchestrator 层面的工作，而是更底层的 operator/kernel 层。

## Scorecard
- Overall: 7.4/10
- Innovation: 7/10
- Technical Quality: 8/10
- Experimental Rigor: 6/10
- Writing Clarity: 8/10
- Practical Value: 8/10

## Related Paper Comparisons
- [SlideSparse: Fast and Flexible (2N-2):2N Structured Sparsity](/papers/2603-05232v1-slidesparse-fast-and-flexible-2n-2-2n-structured/) (同属 LLM inference systems，但技术层级不同): SlideSparse 通过把较温和的结构化稀疏模式重写为硬件可执行的 2:4 稀疏窗口来复用 sparse tensor core，收益来源是模型/算子层的稀疏化；FA4 不改变 attention 的 dense 语义，而是在 Blackwell 上围绕 TMEM、2-CTA MMA 和 softmax 非 matmul 路径做 kernel 共设计。前者更像“改变计算内容”，后者更像“重写计算执行方式”。
- [Oaken: Fast and Efficient LLM Serving with Online-Offline Hybrid KV Cache Quantization.](/papers/dblp-conf-isca-0004hkcl00p25-oaken-fast-and-efficient-llm-serving-with-online/) (同属 serving efficiency，但关注的瓶颈不同): Oaken 处理的是长上下文 serving 中 KV cache 的容量与带宽瓶颈，位于系统级内存管理/量化层；FA4 处理的是 attention 算子内部 compute-SMEM-MUFU 失衡，位于 operator/kernel 层。两者并非替代关系，理论上可以叠加：Oaken 减 cache 压力，FA4 提升 dense attention kernel 本身的执行效率。

## Strengths
- 问题抓得准：不是泛泛讲 attention 快，而是明确识别 Blackwell 上从 MMA 转向 shared memory 和 exponential 单元的瓶颈迁移。
- 方法是成体系的 co-design，而不是只调 kernel 参数；前向、反向、softmax 路径、TMEM/2-CTA 和调度策略之间有一致的硬件逻辑。
- 对 systems 读者价值高：给出了 TMEM、fully asynchronous MMA、2-CTA tensor core 这些 Blackwell 新原语如何改变 attention 设计空间。
- 除了性能，还给出 CuTe-DSL 相对 C++ templates 的编译时间证据，说明实现路径本身也是论文贡献的一部分。

## Future Work
- 在更新版 cuDNN 和更多 Blackwell SKU（如 GB200、后续 B300）上重新评估领先幅度与可迁移性。
- 补上端到端 LLM serving 或训练指标，验证单算子 TFLOPs 提升能否稳定转化为系统级 latency/throughput 收益。
- 系统评估软件模拟 exponential 与 conditional rescaling 的精度、稳定性和适用工作负载边界。
- 探索这些针对非 matmul 瓶颈的设计能否迁移到其他 attention 变体或其他加速器。

## Reading Checklist
- 先核对 roofline 分析到底如何得出 shared memory / exponential 比 MMA 高 25%-60%，以及这个结论覆盖哪些具体 workload。
- 重点看 forward/backward pipeline 图，确认 fully asynchronous MMA 和更大 tile 的 overlap 是如何实现的。
- 仔细读软件模拟 exponential 的多项式近似、conditional rescaling 的触发条件，以及数值稳定性讨论；提取文本没有充分说明这一部分。
- 核对 2-CTA MMA 与 TMEM 的具体数据布局、CTA pairing 约束，以及 dQ atomic reduction 减半是怎样落到 kernel 结构上的。

## Core Contributions
- 把 attention 优化目标从面向 Hopper 的异步执行与 warp specialization，转成面向 Blackwell 非对称硬件扩展的算法-流水线协同设计。
- 提出减少非 matmul 开销的 softmax 路径，包括软件模拟 exponential 与条件式 rescaling，以适配 exp 单元扩展较慢的硬件现实。
- 在 backward 中引入 tensor memory 与 2-CTA MMA 的配合，针对 shared memory 流量和 atomic add 开销做定向优化。

## Why Read It
- 它直接命中当前 B200/GB200 上 attention kernel 的实际瓶颈迁移，和 LLM systems 的硬件代际切换高度相关。
- 摘要同时给出 kernel 性能指标和实现形态变化，既能看吞吐/利用率收益，也能看 CuTe-DSL 对高性能内核开发效率的潜在影响。
- 如果你关注 Blackwell 上的 low-level kernel 设计，这篇论文很可能提供 shared memory、exp 单元与 MMA 管线如何重新平衡的具体范式。

## Risks Or Limits
- 强依赖 Blackwell 特性，尤其是 TMEM、fully asynchronous MMA 和 2-CTA MMA；离开 B200/GB200 后收益边界不清楚。
- 提取文本没有充分说明软件模拟 exponential 和 conditional rescaling 的数值稳定性、误差边界以及模型质量影响。
- 实验主要是单算子 benchmark，提取文本没有充分说明端到端 LLM serving 或训练吞吐/延迟收益。
- 基线公平性存在需要核对的地方：较新的 cuDNN 已接近 FA4，而正文主结果强调的是 cuDNN 9.13。

## Recommended For
- 做 LLM inference 或 serving kernel 优化的工程师
- 关注 Blackwell/Hopper GPU 上 attention 内核迁移的系统研究者
- 研究 CUDA kernel 生成、CuTe/Triton DSL 或低层代码生成的编译器工程师

## Keywords
- FlashAttention
- Blackwell GPU
- B200
- GB200
- attention kernel
- kernel pipelining

## Additional Assets
- 其余提取到的 figures 保存在 `images/` 目录，默认不全部展开，避免让页面被资产列表主导。
- Full asset manifest: [images/index.md](images/index.md)

## Abstract
Attention, as a core layer of the ubiquitous Transformer architecture, is the bottleneck for large language models and long-context applications. While FlashAttention-3 optimized attention for Hopper GPUs through asynchronous execution and warp specialization, it primarily targets the H100 architecture. The AI industry has rapidly transitioned to deploying Blackwell-based systems such as the B200 and GB200, which exhibit fundamentally different performance characteristics due to asymmetric hardware scaling: tensor core throughput doubles while other functional units (shared memory bandwidth, exponential units) scale more slowly or remain unchanged. We develop several techniques to address these shifting bottlenecks on Blackwell GPUs: (1) redesigned pipelines that exploit fully asynchronous MMA operations and larger tile sizes, (2) software-emulated exponential and conditional softmax rescaling that reduces non-matmul operations, and (3) leveraging tensor memory and the 2-CTA MMA mode to reduce shared memory traffic and atomic adds in the backward pass. We demonstrate that our method, FlashAttention-4, achieves up to 1.3$\times$ speedup over cuDNN 9.13 and 2.7$\times$ over Triton on B200 GPUs with BF16, reaching up to 1613 TFLOPs/s (71% utilization). Beyond algorithmic innovations, we implement FlashAttention-4 entirely in CuTe-DSL embedded in Python, achieving 20-30$\times$ faster compile times compared to traditional C++ template-based approaches while maintaining full expressivity.

## Recommendation Signals
- Recommendation score: 9.38
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 1.3
- Quality score: 1.3
- Analysis candidate score: 10.0
- Analysis priority rank: 1
- Analysis signals: flashattention, kernel pipelining, h100, b200, throughput, memory, bandwidth, speedup

## Assets
- Extracted assets are stored in the `images/` folder next to this page.
- Browse the image manifest here: [images/index.md](images/index.md)
