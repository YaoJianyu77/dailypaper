---
paper_id: 2602.07055v1
title: 'Theory of Space: Can Foundation Models Construct Spatial Beliefs through Active
  Exploration?'
authors:
- Pingyue Zhang
- Zihan Huang
- Yue Wang
- Jieyu Zhang
- Letian Xue
- Zihan Wang
- Qineng Wang
- Keshigeyan Chandrasegaran
- Ruohan Zhang
- Yejin Choi
- Ranjay Krishna
- Jiajun Wu
- Li Fei-Fei
- Manling Li
domain: Large Language Models
slug: 2602-07055v1-theory-of-space-can-foundation-models-construct
published: '2026-02-04T19:06:40Z'
summary: 这篇工作值得读的点不在于又做了一个空间任务，而在于它把基础模型在主动探索中“如何形成、维护和更新空间信念”单独拎出来做了问题定义与诊断。
source_url: https://arxiv.org/abs/2602.07055v1
pdf_url: https://arxiv.org/pdf/2602.07055v1.pdf
scores:
  relevance: 2.82
  recency: 3.0
  popularity: 1.8
  quality: 1.4
  recommendation: 8.06
tags:
- paper-note
status: generated
updated: '2026-03-07'
keywords:
- 基础模型
- 主动探索
- 空间信念
- 认知地图
- 部分可观测
- 具身智能
reading_priority: high
---

# Theory of Space: Can Foundation Models Construct Spatial Beliefs through Active Exploration?

## TL;DR
这篇工作值得读的点不在于又做了一个空间任务，而在于它把基础模型在主动探索中“如何形成、维护和更新空间信念”单独拎出来做了问题定义与诊断。

## 中文摘要
论文提出“Theory of Space”，将基础模型在部分可观测环境中通过主动探索获取信息、构建并更新空间信念的能力作为核心研究对象。作者基于一个以好奇心驱动探索和认知地图构建为目标的基准进行评测，并引入空间信念探测来观察模型在每一步暴露出的内部空间表征。摘要声称当前最先进模型存在主动-被动能力落差、探索低效、全局空间信念不稳定以及信念更新迟滞等问题。摘要没有充分说明实验设置、评价指标和结果幅度，而且摘要末尾被截断，若要判断结论强度仍需读正文核对。

## Quick Facts
- Paper ID: `2602.07055v1`
- Authors: Pingyue Zhang, Zihan Huang, Yue Wang, Jieyu Zhang, Letian Xue, Zihan Wang, Qineng Wang, Keshigeyan Chandrasegaran, Ruohan Zhang, Yejin Choi, Ranjay Krishna, Jiajun Wu, Li Fei-Fei, Manling Li
- Domain: Large Language Models
- Published: 2026-02-04T19:06:40Z
- arXiv: [abstract](https://arxiv.org/abs/2602.07055v1)
- PDF: [download](https://arxiv.org/pdf/2602.07055v1.pdf)
- Reading priority: high
- Why this priority: 这篇论文同时贴合大模型、Agent 和多模态方向，而且不是泛泛讨论空间任务，而是直接切入“主动探索下的内部信念构建与更新”这一更基础的能力缺口。摘要虽然缺少实验细节，但问题定义、诊断工具和暴露出的失败模式都很有研究价值，适合作为近期重点阅读对象。

## Research Background And Motivation
多模态基础模型在被动感知上进步很快，但具身智能里的关键难点其实是部分可观测条件下的主动信息获取与持续状态维护。随着大模型开始进入代理和具身场景，模型是否能形成可靠的空间信念而不只是看懂单帧输入，成为一个更基础也更现实的问题。

## Problem Framing
论文要回答的问题是：基础模型在主动探索场景中，能否像合格代理一样从连续、局部观测中构建、修正并利用空间信念。这个问题重要，因为如果模型只能做被动识别而不能稳定更新内部世界模型，就很难支撑长期规划、导航和具身决策。

## Method Overview
作者先把这一能力定义为“Theory of Space”，再设计一个以探索并构建准确认知地图为目标的评测基准。方法上的核心动作是加入“空间信念探测”，在每一步提示模型显式暴露其当前空间表征，用它来区分感知错误、全局信念退化和信念更新失败等不同瓶颈；同时还用错误信念范式检查模型是否会坚持过时先验。

## Experimental Setup And Evidence
摘要给出的证据是：在对当前最先进模型的评测中，作者观察到主动-被动差距、探索效率低、全局信念不稳定，以及面对新证据时存在“Belief Inertia”。但摘要没有给出具体实验协议、比较对象、评价指标、误差类型分布或定量结果，且最后一句被截断，因此目前只能确认作者提出了这些诊断性结论，不能仅凭摘要判断结论有多普适或多强。

## Research Or Engineering Value
如果这些结论成立，这项工作会给大模型代理与具身系统提供一个更可操作的问题框架：不仅看感知或任务成败，还直接检查模型内部空间信念是否稳定、是否能被新证据纠正。对研究上，它有助于把“主动探索失败”拆解成更细的能力瓶颈；对工程上，它可能帮助设计更稳健的记忆、地图构建和信念更新机制。

## Reading Checklist
- 空间信念探测具体如何设计，探测到的表征与模型真实内部状态之间有多强的一致性？
- 基准中的任务、环境和评价指标是什么，所谓主动-被动差距与信念不稳定是如何被量化的？
- Belief Inertia 在哪些模型和输入模态上最明显，加入外部记忆、地图模块或程序化规划后是否能显著缓解？

## Core Contributions
- 把基础模型在主动探索中构建和更新空间信念的能力明确表述为“Theory of Space”问题。
- 提出一个围绕好奇心驱动探索与认知地图构建的评测基准，用来测试主动信息获取而非被动感知。
- 引入空间信念探测这一诊断视角，用逐步暴露的空间表征来定位感知瓶颈、全局信念退化和更新迟滞。

## Why Read It
- 它切中的是真正影响代理落地的短板：模型会看不等于会主动找信息，也不等于会维护世界模型。
- 论文的价值更像问题定义和诊断框架，而不是单一任务刷分，这对大模型代理研究更耐读。
- 如果你关心具身智能、空间推理或长期交互中的记忆更新，这篇论文给出了一个值得复用的分析坐标系。

## Risks Or Limits
- 摘要没有充分说明基准设置、比较方法和定量收益，当前无法判断问题定义之外的实验说服力。
- 空间信念探测依赖提示模型显式报告其表征，这种报告是否真实反映内部状态需要谨慎核对。

## Recommended For
- 关注大模型代理、具身智能和主动探索问题定义的研究者。
- 在做多模态导航、空间推理、记忆更新或世界模型诊断的工程师。
- 想判断当前基础模型离可用的长期交互式空间代理还有多远的读者。

## Keywords
- 基础模型
- 主动探索
- 空间信念
- 认知地图
- 部分可观测
- 具身智能

## Abstract
Spatial embodied intelligence requires agents to act to acquire information under partial observability. While multimodal foundation models excel at passive perception, their capacity for active, self-directed exploration remains understudied. We propose Theory of Space, defined as an agent's ability to actively acquire information through self-directed, active exploration and to construct, revise, and exploit a spatial belief from sequential, partial observations. We evaluate this through a benchmark where the goal is curiosity-driven exploration to build an accurate cognitive map. A key innovation is spatial belief probing, which prompts models to reveal their internal spatial representations at each step. Our evaluation of state-of-the-art models reveals several critical bottlenecks. First, we identify an Active-Passive Gap, where performance drops significantly when agents must autonomously gather information. Second, we find high inefficiency, as models explore unsystematically compared to program-based proxies. Through belief probing, we diagnose that while perception is an initial bottleneck, global beliefs suffer from instability that causes spatial knowledge to degrade over time. Finally, using a false belief paradigm, we uncover Belief Inertia, where agents fail to update obsolete priors with new evidence. This issue is present in text-based agents but is particularly severe in vision-based models. Our findings suggest that current foundation models struggle to maintain coherent, revisable spatial beliefs during active exploration.

## Recommendation Signals
- Recommendation score: 8.06
- Relevance score: 2.82
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.4
