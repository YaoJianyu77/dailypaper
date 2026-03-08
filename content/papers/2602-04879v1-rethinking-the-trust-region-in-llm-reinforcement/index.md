---
paper_id: 2602.04879v1
title: Rethinking the Trust Region in LLM Reinforcement Learning
authors:
- Penghui Qi
- Xiangxin Zhou
- Zichen Liu
- Tianyu Pang
- Chao Du
- Min Lin
- Wee Sun Lee
domain: Large Language Models
slug: 2602-04879v1-rethinking-the-trust-region-in-llm-reinforcement
published: '2026-02-04T18:59:04Z'
summary: 这篇工作把 LLM 强化学习中的 PPO 问题收束到一个更底层的点：现有 trust region 近似可能约束错了对象。
source_url: https://arxiv.org/abs/2602.04879v1
pdf_url: https://arxiv.org/pdf/2602.04879v1.pdf
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 2.0
  quality: 1.6
  recommendation: 8.63
tags:
- paper-note
status: generated
updated: '2026-03-07'
institutions:
- Sea AI Lab, Singapore
- School of Computing, National University of Singapore
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- 大语言模型
- 强化学习微调
- PPO
- trust region
- 策略散度
- KL 散度
reading_priority: high
image_count: 16
analysis_depth: full
full_analysis_source: arxiv_source
---

# Rethinking the Trust Region in LLM Reinforcement Learning

## TL;DR
这篇工作把 LLM 强化学习中的 PPO 问题收束到一个更底层的点：现有 trust region 近似可能约束错了对象。

## 中文摘要
论文认为，PPO 依赖采样 token 概率比值做 clipping，这种单样本近似在超大词表的 LLM 上并不能可靠代表真实策略散度，因此会同时带来低概率 token 过度惩罚和高概率 token 约束不足。作者提出 DPPO，用直接估计的策略散度（如 TV 或 KL）替代启发式 ratio clipping，并用 Binary 与 Top-K 近似把额外开销压低。摘要声称该方法在训练稳定性和效率上优于现有方法，但实验设置、模型规模、任务范围和近似误差细节摘要没有充分说明。

## Quick Facts
- Paper ID: `2602.04879v1`
- Authors: Penghui Qi, Xiangxin Zhou, Zichen Liu, Tianyu Pang, Chao Du, Min Lin, Wee Sun Lee
- Institutions: Sea AI Lab, Singapore, School of Computing, National University of Singapore
- Domain: Large Language Models
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-02-04T18:59:04Z
- arXiv: [abstract](https://arxiv.org/abs/2602.04879v1)
- PDF: [download](https://arxiv.org/pdf/2602.04879v1.pdf)
- Reading priority: high
- Why this priority: 这篇论文高度贴合 Large Language Models 主线，而且切入的是 PPO 在 LLM RL 中的核心约束机制，不是边缘技巧。如果摘要结论成立，它会影响一类主流后训练方法的默认设计；再结合 hot paper 信号与 8.63 的推荐分，值得优先读正文核对实验与近似误差。

## Abstract Translation
强化学习已经成为微调大语言模型的核心范式，而 PPO 是事实标准算法。论文认为，PPO 的核心 ratio clipping 机制在 LLM 的大词表场景下存在结构性不适配：它依据采样 token 的概率比来约束策略更新，而这只是对真实策略散度的噪声化单样本蒙特卡洛估计。结果是，低概率 token 的更新会被过度惩罚，而高概率 token 上潜在的灾难性分布变化又可能约束不足，从而带来训练低效和不稳定。为解决这一问题，作者提出 Divergence Proximal Policy Optimization（DPPO），用直接估计的策略散度（如 TV 或 KL）替代启发式 clipping；同时提出高效的 Binary 和 Top-K 近似，以避免巨大的内存开销。摘要声称，大量实验证明 DPPO 在训练稳定性和效率上优于现有方法，为基于 RL 的 LLM 微调提供了更稳健的基础。

## Research Background And Motivation
LLM 的 RL 后训练目前普遍依赖 PPO/GRPO 一类算法，但这些方法默认把 sampled-token ratio 当作 trust region 的代理，这一近似在大词表、长尾分布上未必成立。随着对齐训练越来越依赖稳定且高效的后训练流程，trust region 到底应该约束什么，已经是核心方法问题，而不是次要实现细节。

## Problem Framing
论文要解决的是一个更底层的问题：在 LLM 的离散大词表策略空间里，怎样定义 trust region 才能真正反映策略分布的安全变化。作者认为现有 PPO ratio clipping 把单个采样 token 的概率比误当成分布散度代理，会同时导致两类偏差：低概率 token 被过度抑制，高概率 token 的大幅概率质量转移又可能漏罚；再叠加 training-inference mismatch，这会直接转化为训练低效和不稳定。

## Method Overview
方法路线是把 PPO 的 ratio-based clipping 重写为 divergence-based trust region。论文先针对有限时域、无折扣、序列级奖励的 LLM 生成设定推导性能差分恒等式与 policy improvement bound，再据此提出 DPPO：仍采用 PPO 风格的一阶优化和动态 mask，但 mask 是否触发不再由单样本 ratio 决定，而是由直接估计的策略散度是否越过阈值决定。为让这一约束在大词表下可行，作者进一步设计了 Binary 与 Top-K 两种近似。

### Method Figure
![sanity_test_page1](images/sanity_test_page1.png)

*Figure cue:* DPPO variants achieve stable training while controlling the training-inference mismatch at a low level. In contrast, methods without a trust region (PG-IS, CISPO) or with a misspecified one (MiniRL) suffer from growing mismatch and eventual collapse.

## Method Details
- 针对 LLM 生成的 finite-horizon、undiscounted 设定，推导了专门的 performance difference identity 和 policy improvement bound，并用 TV/KL 形式给出 trust region 的理论依据。
- 将 PPO 的 clipping 解释为对真实策略散度期望的单样本 Monte Carlo 近似，并指出这种近似对 token 概率量级高度敏感，因此会系统性错判更新是否危险。
- DPPO 用基于散度阈值的动态 mask 替代 ratio clipping；其判断依据是整个策略分布是否已偏离 trust region，而不是某个采样 token 的概率比是否超界。
- Binary 近似把原始词表分布压缩成“采样 token vs 其他 token”的 Bernoulli 分布，在极低额外开销下计算 TV/KL，并更直接反映绝对概率质量变化。
- Top-K 近似保留 behavior policy 下最可能的若干 token，并补入采样 token，再把其余 token 合并为 other 类别，在较低成本下更好捕捉 head distribution 的变化。

## Experimental Setup And Evidence
实验分为稳定性剖析和扩展/缩放验证两层。稳定性部分在 DeepSeek-R1-Distill-Qwen-1.5B 上进行，使用从 MATH 数据集整理出的 1,460 道题做 sanity test，重点回答三个问题：极低学习率下 trust region 是否仍必要；trust region 应锚定 rollout policy 还是 recomputed policy；哪些类型的更新是训练不稳定的主要来源。该部分对比了 PG-IS、PG-TIS/CISPO、GRPO with Clip-Higher、MiniRL、MiniRL-TIS 与 DPPO（binary KL 或 TV 版本）。扩展部分和图注显示，作者还在 Qwen3-30B-A3B-Base、Qwen3-30B-A3B、Qwen3-8B-Base、OctoThinker-3B-Hybrid-Base、Qwen3-1.7B-Base 等模型上评估 AIME24/AIME25、Arc1D、Acre、Sudoku-v0-easy 等任务，并比较 Binary/Top-K 近似及是否使用 rollout router replay（R3）。具体训练步数、重复次数、显存与吞吐配置，提取文本没有充分说明。

### Experiment Figure
![clip_direction_page1](images/clip_direction_page1.png)

*Figure cue:* Analysis of trust region relaxation direction. (Left) Training reward curves. (Right) Policy entropy.

## Datasets And Benchmarks
- MATH（稳定性分析使用其中 1,460 道 curated problems）
- AIME24
- AIME25
- 标准数学推理数据集（OctoThinker-3B-Hybrid-Base 所用，提取文本未明确具体名称）
- Arc1D
- Acre（来自 Gem））? wait invalid JSON? need correct.

## Baselines
- PG-IS
- PG-TIS / CISPO
- GRPO with Clip-Higher
- MiniRL
- MiniRL-TIS
- vanilla ratio-based PPO（在 GRPO 框架下的对照）

## Metrics
- training accuracy
- training rewards / final rewards
- training-inference mismatch
- AIME24 Avg@32
- AIME25 Avg@32
- policy entropy”、“percentage of bad updates

## Ablations And Analysis
- Trust region 在极低学习率下是否仍然必要
- Trust region 的 anchor：rollout policy vs recomputed policy
- 不稳定性的来源：large-divergence bad updates，尤其是 negative samples 上的坏更新
- 对低概率 token 放松 trust region 的影响分析（low-prob sweep）? invalid

## Evaluation Validity And Fairness
- 稳定性部分采用受控 sanity test：若算法稳定，初始模型在已知可解的 1,460 道 MATH 题上应能收敛到接近满分，这对分析 collapse 有较强内部有效性。
- 扩展实验覆盖多个模型和任务，说明论文并非只在单一数学 RL 设置下给出结论。
- 提取文本没有给出重复实验、方差、显著性或置信区间，结果稳健性仍需正文核对。
- 效率与 negligible overhead 的证据主要来自摘要和叙述性文字，缺少吞吐、显存、时延等量化指标。

## Main Results And Claims
提取文本支持的结论是：在基于 MATH 的稳定性 sanity test 中，无 trust region 的 PG-IS/PG-TIS 会出现 training-inference mismatch 持续增长并最终崩溃，而 DPPO 变体能够把 mismatch 维持在较低水平并获得接近完美的最终训练表现。进一步地，使用 recomputed policy 作为 trust region anchor 的做法（如 MiniRL 或 decoupled DPPO-KL）会导致不稳定，作者据此主张 trust region 应锚定 rollout policy。图注和扩展实验文字还表明，DPPO 在 AIME24/AIME25 以及多模型、多任务设置下相对 GRPO 或 ratio-based PPO 具有更好的训练效率，并且有时带来更好的最终或渐近性能。具体提升幅度、统计稳定性和额外系统开销，提取文本没有充分说明。

## Research Or Engineering Value
如果正文结论成立，DPPO 的实用价值在于为 LLM RL 后训练提供一个比 ratio clipping 更合理的默认 trust region 实现：它有望减少训练崩溃和无效 clipping，提高样本效率，并让 PPO/GRPO 类流程更稳定。对做 RLHF、reasoning RL 或大模型对齐基础设施的人，这种改动的价值高于单一 benchmark 的局部提分。

## Relation To Prior Work
相对常见的 PPO/GRPO 路线，这篇论文的差异不在于换奖励函数、换采样策略或简单放宽 clipping 上下界，而是直接质疑“sampled-token ratio 足以代理 trust region”这一默认假设，转而回到 TRPO 风格的分布散度约束。相对 Clip-Higher、CISPO 这类仍在 ratio clipping 周边做启发式修补的方法，它把根因定位为单样本概率比与真实策略散度之间的结构性错位；相对 MiniRL 一类用 recomputed policy 作为锚点的实现，它强调 trust region 必须锚定 rollout policy。核心新意在于重新定义被约束的对象，并用 Binary/Top-K 近似把这一约束压到 LLM 可接受的成本。

## Overall Assessment
从现有材料看，这篇论文最值得信的部分是问题诊断和实验问题分解：它没有把 PPO 的不稳定只当成经验现象，而是把核心矛头指向 sampled-token ratio 与真实分布散度之间的结构性错位，并通过 trust region 必要性、anchor 选择、坏更新来源三个问题把论证拆开，这比单纯报 benchmark 更有说服力。最该保持怀疑的部分是“低开销且普遍更优”的工程结论：提取文本缺少完整数值、误差分析、重复实验和系统开销表，Binary/Top-K 近似在更复杂 RLHF 设置下是否仍可靠，还不能仅凭当前片段下定论。整体上，这是一篇值得优先精读的方法论文，因为它挑战的是 LLM RL 里一个默认但可能不对的核心假设；但在把它当成新默认算法前，必须先核实近似误差、系统代价和泛化范围。

## Technical Route Positioning
这篇论文属于 LLM 后训练中的策略优化/对齐训练路线，具体位于 RLHF、GRPO、PPO 这一链路里的 policy update constraint 设计层，而不是奖励建模、数据配方或推理时搜索。它处理的是：在序列级奖励、超大离散词表和 training-inference mismatch 并存的条件下，如何定义并近似实现一个真正反映分布变化的 trust region。

## Scorecard
- Overall: 7.0/10
- Innovation: 7/10
- Technical Quality: 7/10
- Experimental Rigor: 6/10
- Writing Clarity: 7/10
- Practical Value: 8/10

## Related Paper Comparisons
- [POET-X: Memory-efficient LLM Training by Scaling Orthogonal Transformation](/papers/2603-05500v1-poet-x-memory-efficient-llm-training-by-scaling/) (同属大模型训练稳定性/效率研究，但处于不同训练阶段与技术层): POET-X 关注的是预训练或一般训练中的稳定性与显存效率，技术抓手是可扩展的正交变换；本文则针对 RL 微调里的 trust region 定义失真，改造的是 policy optimization 约束。两者都强调训练效率和稳定性，但本文更靠近 RLHF/GRPO 的后训练核心算法层，问题更窄也更直接。

## Strengths
- 把问题下沉到 trust region 定义本身，而不是继续调 PPO clipping 超参数，问题诊断比较到位。
- 理论部分明确针对 LLM 的 finite-horizon、undiscounted 生成过程重写 performance bound，方法论上较自洽。
- Binary 和 Top-K 近似把“直接约束分布散度”从理论概念推进到可能落地的工程机制。
- 实验不仅展示结果，还系统分析了 trust region 的必要性、anchor 选择和 instability 来源，论证结构较完整。

## Future Work
- 量化 Binary/Top-K 近似与全分布散度之间的误差，并分析它们在长尾 token 或分布急剧变化阶段的失效边界。
- 在更贴近真实 RLHF 的奖励模型、人类偏好数据和噪声奖励场景中验证 DPPO 的稳定性收益。
- 补充吞吐、显存、通信和 wall-clock 开销分析，明确 DPPO 相对 PPO/GRPO 的系统代价。
- 研究 trust region 阈值、anchor 选择与 training-inference mismatch 之间是否能形成更自动化的自适应机制。

## Reading Checklist
- 先核对 LLM 有限时域、无折扣设定下的 performance difference identity 和 policy improvement bound 是否真的支撑后续目标函数。
- 确认 DPPO 的 mask 具体如何定义“朝远离 trust region 的方向移动”，以及它与 PPO 非对称 clipping 的对应关系。
- 查看 Binary 和 Top-K 近似的理论性质：它们为何是 lower bound、K 如何选、误差是否会影响更新判断。
- 重点看 sanity test 中 mismatch 的定义、测量方法，以及为何 rollout policy anchor 比 recomputed policy 更稳。

## Core Contributions
- 指出 PPO 的 ratio clipping 在 LLM 大词表场景下与真实策略散度存在结构性错位，而不只是经验性调参问题。
- 提出 DPPO，用直接估计的策略散度替代 sampled-token ratio clipping 作为 trust region 约束。
- 设计 Binary 与 Top-K 近似，以较低额外代价保留散度估计中的关键信息。

## Why Read It
- 它讨论的是 LLM RL 后训练里最基础的一层优化机制，影响面比单一任务技巧更大。
- 论文的新意不在奖励建模或数据配方，而在重新定义“该约束什么”，这是值得优先核对的方法论问题。
- 如果你在做 RLHF、GRPO/PPO 类后训练或其他策略优化，这篇论文可能直接影响默认算法选择。

## Risks Or Limits
- 提取文本没有充分说明 DPPO 的完整目标函数细节、阈值选择原则和关键超参数。
- 效率、显存和额外开销虽被宣称较低，但缺少明确数字，工程收益目前只能部分相信。
- Binary/Top-K 近似是否会漏掉长尾 token 的重要分布变化，提取文本没有给出充分的误差分析或失败案例。
- 实验数值、重复次数、方差和统计显著性没有在提取片段中展开，严格比较强度仍需核对正文。

## Recommended For
- 关注 LLM 后训练、RLHF 与策略优化的研究者
- 需要提升大模型 RL 微调稳定性和训练效率的工程师
- 正在比较 PPO、KL 约束及其他 policy optimization 方案的人

## Keywords
- 大语言模型
- 强化学习微调
- PPO
- trust region
- 策略散度
- KL 散度

## Additional Figures

![which_trust_region_page1](images/which_trust_region_page1.png)

*Figure cue:* Switching the stable DPPO-KL to a decoupled objective causes the mismatch to grow and performance to collapse, confirming that the trust region must be anchored to the rollout policy.

![rewards_mask_fraction_combined_page1](images/rewards_mask_fraction_combined_page1.png)

*Figure cue:* Isolating the source of instability. The solid curves are training rewards, while the dashed lines are the percentage of bad updates. Starting with the unstable PG-IS, applying a minimal mask that only blocks large-divergence bad updates on negative samples is sufficient to stabilize training, indicating these bad updates are the primary cause of training instability.

![low_prob_sweep_page1](images/low_prob_sweep_page1.png)

*Figure cue:* Analysis of relaxing trust regions for low-probability tokens. (Left) Training reward curves. (Middle) Rollout probability of clipped tokens. (Right) Entropy of clipped tokens.

![main-base_page1](images/main-base_page1.png)

*Figure cue:* Evolution of AIME24 and AIME25 Avg@32 scores during RL training using Qwen3-30B-A3B-Base. 
 
 The first and third panels correspond to the same experiment without rollout router replay (w/o R3), while the second and fourth panels correspond to the same experiment with rollout router replay (w/ R3).

![main-a3b_and_8b_page1](images/main-a3b_and_8b_page1.png)

*Figure cue:* Evolution of AIME24 and AIME25 scores during RL training using Qwen3-30B-A3B (left) and Qwen3-8B-Base (right).

![main-topk_page1](images/main-topk_page1.png)

*Figure cue:* Evolution of AIME24 and AIME25 scores for baselines and DPPO with binary/Top-K (K=20) TV/KL approximation under the same setting as MoE Base w/o R3.

![appendix-base_woR3_page1](images/appendix-base_woR3_page1.png)

*Figure cue:* Evolution of metrics for MoE Base w/o R3 experiment (based on Qwen3-30B-A3B-Base, without rollout router replay).

![appendix-base_wR3_page1](images/appendix-base_wR3_page1.png)

*Figure cue:* Evolution of metrics for MoE Base w/ R3 experiment (based on Qwen3-30B-A3B-Base, with rollout router replay).

![appendix-a3b_page1](images/appendix-a3b_page1.png)

*Figure cue:* Evolution of metrics for MoE Thinking experiment (based on Qwen3-30B-A3B).

![appendix-8b_page1](images/appendix-8b_page1.png)


![appendix-lora_page1](images/appendix-lora_page1.png)


![appendix-topk_page1](images/appendix-topk_page1.png)


![more_settings_page1](images/more_settings_page1.png)


![ppo_vs_dppo_page1](images/ppo_vs_dppo_page1.png)

- Full asset manifest: [images/index.md](images/index.md)

## Abstract
Reinforcement learning (RL) has become a cornerstone for fine-tuning Large Language Models (LLMs), with Proximal Policy Optimization (PPO) serving as the de facto standard algorithm. Despite its ubiquity, we argue that the core ratio clipping mechanism in PPO is structurally ill-suited for the large vocabularies inherent to LLMs. PPO constrains policy updates based on the probability ratio of sampled tokens, which serves as a noisy single-sample Monte Carlo estimate of the true policy divergence. This creates a sub-optimal learning dynamic: updates to low-probability tokens are aggressively over-penalized, while potentially catastrophic shifts in high-probability tokens are under-constrained, leading to training inefficiency and instability. To address this, we propose Divergence Proximal Policy Optimization (DPPO), which substitutes heuristic clipping with a more principled constraint based on a direct estimate of policy divergence (e.g., Total Variation or KL). To avoid huge memory footprint, we introduce the efficient Binary and Top-K approximations to capture the essential divergence with negligible overhead. Extensive empirical evaluations demonstrate that DPPO achieves superior training stability and efficiency compared to existing methods, offering a more robust foundation for RL-based LLM fine-tuning.

## Recommendation Signals
- Recommendation score: 8.63
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 1.6

## Assets
- Extracted assets are stored in the `images/` folder next to this page.
- Browse the image manifest here: [images/index.md](images/index.md)
