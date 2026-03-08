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
summary: 核心看点是把基础模型的空间能力拆成主动探索、信念稳定性和信念更新三个可诊断层面。
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
venue_or_journal: ICLR 2026
citation_summary: Citation count unavailable
keywords:
- 空间具身智能
- 主动探索
- 空间信念
- 认知地图
- 部分可观测
- 基础模型/大模型Agent
reading_priority: high
---

# Theory of Space: Can Foundation Models Construct Spatial Beliefs through Active Exploration?

## TL;DR
核心看点是把基础模型的空间能力拆成主动探索、信念稳定性和信念更新三个可诊断层面。

## 中文摘要
这篇工作把空间具身智能中的关键能力定义为“Theory of Space”：智能体需要在部分可观测环境中主动探索，并据此构建、修正和利用空间信念。作者围绕好奇心驱动探索与认知地图构建设计评测，并用“空间信念探针”逐步外显模型的空间表征，以区分感知瓶颈、全局信念不稳定和信念更新失败。摘要声称当前先进模型存在主动-被动落差、探索低效和“Belief Inertia”，但没有给出具体模型、指标和定量结果，而且摘要末尾被截断。

## Quick Facts
- Paper ID: `2602.07055v1`
- Authors: Pingyue Zhang, Zihan Huang, Yue Wang, Jieyu Zhang, Letian Xue, Zihan Wang, Qineng Wang, Keshigeyan Chandrasegaran, Ruohan Zhang, Yejin Choi, Ranjay Krishna, Jiajun Wu, Li Fei-Fei, Manling Li
- Institutions: Institution information not extracted
- Domain: Large Language Models
- Venue / Journal: ICLR 2026
- Citations: Citation count unavailable
- Published: 2026-02-04T19:06:40Z
- arXiv: [abstract](https://arxiv.org/abs/2602.07055v1)
- PDF: [download](https://arxiv.org/pdf/2602.07055v1.pdf)
- Reading priority: high
- Why this priority: 高：它同时命中大模型、Agent和多模态交互这条主线，且问题定义比常见的静态感知评测更接近真实系统短板。虽然摘要没有充分说明实验细节且内容被截断，但其提出的诊断框架和失败模式本身已经足够值得优先核对。

## Research Background And Motivation
多模态基础模型在被动感知上进展很快，但真实Agent任务要求系统在不完整观察下主动决定去哪里看、如何整合新信息。随着大模型和Agent走向具身与交互式环境，能否形成并稳定维护可更新的空间信念，正在成为比单步感知更关键的能力缺口。

## Problem Framing
问题是：基础模型能否在部分可观测环境中通过自主探索，而不是依赖被动输入，形成准确、可更新的空间信念或认知地图？这件事重要，因为如果模型不会主动采样关键信息、也不会用新证据修正旧判断，那么导航、具身交互和长期Agent任务中的状态表示都会系统性失真。

## Method Overview
作者提出“Theory of Space”作为能力定义，并构建一个以好奇心驱动探索和认知地图准确性为目标的benchmark。方法上的关键机制是“spatial belief probing”，即在每一步提示模型显式暴露其当前空间表征；同时结合false belief范式，测试模型是否会用新观察更新已经过时的先验。

## Experimental Setup And Evidence
摘要给出的证据主要是方向性诊断结果：一是主动探索相对被动感知存在明显性能落差，二是模型探索效率低于程序化代理，三是belief probing显示全局空间信念会随时间退化，四是false belief测试指向信念更新迟缓。摘要没有充分说明具体实验设置、模型名单、评价指标和定量结果，且最后一句被截断，因此目前只能确认其问题设定和主要结论方向，不能判断证据强度。

## Research Or Engineering Value
如果这些结论成立，这项工作会为基础模型和Agent研究提供一个更贴近真实交互的空间能力评测框架，把失败原因从“看不懂”进一步拆解为“不会主动找信息”“信念不稳定”“不会更新旧信念”。对工程上做导航、机器人或其他部分可观测Agent系统也有直接价值，因为它提示仅提升感知模块不够，还需要显式优化探索策略、状态维护和belief update机制。

## Reading Checklist
- 空间信念探针到底如何定义和评分，它测到的是模型真实内部表征，还是被提示诱导出来的文本化解释？
- benchmark中的环境类型、动作空间与认知地图准确性指标是什么，是否能公平比较不同模型和不同模态设置？
- Belief Inertia主要来自感知错误、记忆丢失、上下文限制，还是显式信念更新机制本身缺失？

## Core Contributions
- 把空间智能中的关键能力从被动感知扩展为“主动探索下的空间信念构建与更新”这一更完整的问题定义。
- 提出spatial belief probing，用逐步外显的方式诊断模型在探索过程中的空间表征变化。
- 将模型失败模式具体拆分为主动-被动落差、探索低效、全局信念不稳定和Belief Inertia。

## Why Read It
- 当前Agent研究越来越强调交互执行，这篇工作直接检查模型是否真的在形成可更新的世界模型，而不只是做局部感知。
- 它提供的失败模式拆分很有研究价值，因为后续改进可以分别针对探索策略、记忆表示和信念更新，而不是把问题笼统归因于“模型不够强”。
- 摘要还暗示该问题不只存在于具身场景，也出现在文本Agent中，这使它对更广义的部分可观测Agent任务都有参考价值。

## Risks Or Limits
- 摘要没有充分说明benchmark是否区分感知错误、动作决策错误、记忆限制和推理缺陷，失败归因可能混杂。
- belief probing依赖模型显式输出，其可解释性很强，但未必严格等价于模型内部真实状态，存在测量偏差风险。

## Recommended For
- 研究具身Agent、主动探索或导航任务的研究者。
- 关注大模型/多模态系统状态表示、长期记忆和belief tracking问题的读者。
- 需要设计部分可观测环境评测或诊断框架的工程师与研究人员。

## Keywords
- 空间具身智能
- 主动探索
- 空间信念
- 认知地图
- 部分可观测
- 基础模型/大模型Agent

## Abstract
Spatial embodied intelligence requires agents to act to acquire information under partial observability. While multimodal foundation models excel at passive perception, their capacity for active, self-directed exploration remains understudied. We propose Theory of Space, defined as an agent's ability to actively acquire information through self-directed, active exploration and to construct, revise, and exploit a spatial belief from sequential, partial observations. We evaluate this through a benchmark where the goal is curiosity-driven exploration to build an accurate cognitive map. A key innovation is spatial belief probing, which prompts models to reveal their internal spatial representations at each step. Our evaluation of state-of-the-art models reveals several critical bottlenecks. First, we identify an Active-Passive Gap, where performance drops significantly when agents must autonomously gather information. Second, we find high inefficiency, as models explore unsystematically compared to program-based proxies. Through belief probing, we diagnose that while perception is an initial bottleneck, global beliefs suffer from instability that causes spatial knowledge to degrade over time. Finally, using a false belief paradigm, we uncover Belief Inertia, where agents fail to update obsolete priors with new evidence. This issue is present in text-based agents but is particularly severe in vision-based models. Our findings suggest that current foundation models struggle to maintain coherent, revisable spatial beliefs during active exploration.

## Recommendation Signals
- Recommendation score: 8.06
- Relevance score: 2.82
- Recency score: 3.0
- Popularity score: 1.8
- Quality score: 1.4
