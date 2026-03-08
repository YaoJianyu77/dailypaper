---
paper_id: 2602.06019v1
title: Multi-Token Prediction via Self-Distillation
authors:
- John Kirchenbauer
- Abhimanyu Hans
- Brian Bartoldson
- Micah Goldblum
- Ashwinee Panda
- Tom Goldstein
domain: LLM Inference Systems
slug: 2602-06019v1-multi-token-prediction-via-self-distillation
published: '2026-02-05T18:54:48Z'
summary: 这篇工作试图用在线自蒸馏把现成自回归语言模型直接改造成可一次预测多个 token 的单模型解码器，以换取推理加速而不引入 speculative
  decoding 所需的辅模和验证流水线。
source_url: http://arxiv.org/abs/2602.06019v1
pdf_url: https://arxiv.org/pdf/2602.06019v1
scores:
  relevance: 3.0
  recency: 3.0
  popularity: 2.0
  quality: 1.6
  recommendation: 9.27
tags:
- paper-note
status: generated
updated: '2026-03-08'
venue_or_journal: arXiv preprint
citation_summary: Citation count unavailable
keywords:
- LLM推理系统
- 多token预测
- 在线自蒸馏
- 解码加速
- 自回归语言模型
- speculative decoding替代
reading_priority: high
analysis_priority_rank: 2
selected_for_full_analysis: false
---

# Multi-Token Prediction via Self-Distillation

## TL;DR
这篇工作试图用在线自蒸馏把现成自回归语言模型直接改造成可一次预测多个 token 的单模型解码器，以换取推理加速而不引入 speculative decoding 所需的辅模和验证流水线。

## 中文摘要
论文把推理加速问题从“额外加一个 speculator 和 verifier”改成“直接把原始自回归模型训练成可做多 token 预测的单模型”。核心做法是对预训练 checkpoint 施加简单的在线蒸馏目标，得到一个实现形态不变、可直接部署的 standalone multi-token prediction model。摘要给出的主要结果是在 GSM8K 上平均解码速度超过 3 倍，同时相对单 token 解码的准确率下降小于 5%，但硬件前提、训练开销和与强 baseline 的公平比较摘要没有充分说明。

## Quick Facts
- Paper ID: `2602.06019v1`
- Authors: John Kirchenbauer, Abhimanyu Hans, Brian Bartoldson, Micah Goldblum, Ashwinee Panda, Tom Goldstein
- Institutions: Institution information not extracted
- Domain: LLM Inference Systems
- Venue / Journal: arXiv preprint
- Citations: Citation count unavailable
- Published: 2026-02-05T18:54:48Z
- Source page: [open](http://arxiv.org/abs/2602.06019v1)
- PDF: [download](https://arxiv.org/pdf/2602.06019v1)
- Reading priority: high
- Why this priority: 主题与 LLM Inference Systems 高度吻合，且摘要直接声称在不引入辅模的前提下实现超过 3 倍解码加速，这对 serving efficiency 很值得优先核查。虽然硬件、baseline 公平性和训练成本细节摘要没有充分说明，但它仍是今天应优先读正文的方法型论文。

## Research Background And Motivation
LLM 推理的主要瓶颈仍是逐 token 自回归解码，其延迟和吞吐通常受串行生成过程限制。现有 speculative decoding 虽然能加速，但往往需要额外模型、验证步骤和更复杂的 serving pipeline，因此工程接入和部署成本不低。

## Problem Framing
问题是：能否不引入辅助模型、不改造复杂推理栈，只通过训练把一个现成的单步 next-token 自回归模型转成可直接做多 token 预测的单模型，从而显著降低解码延迟，同时尽量保住任务准确率。这个问题重要，因为它直接关系到 LLM serving 的系统复杂度、部署门槛，以及加速收益能否稳定落地。

## Method Overview
方法是对预训练自回归语言模型施加一个简单的在线自蒸馏目标，把原本“每步预测下一个 token”的模型转成“每步预测多个 token”的 standalone 模型。按摘要描述，最终模型保留与初始 checkpoint 相同的实现形态，部署时不需要额外 verifier、speculator 或专门的推理代码。

## Experimental Setup And Evidence
摘要给出的证据主要是任务级结果：在 GSM8K 上，所述方法相对单 token 解码平均可实现超过 3 倍的解码加速，且准确率下降小于 5%。但摘要没有充分说明模型规模、硬件平台、batch 或上下文长度、训练成本、解码细节，以及与 speculative decoding 或其他强基线的公平比较方式。

## Research Or Engineering Value
如果这些结论在更广泛任务和真实 serving 环境中成立，这项工作有望把解码加速从“复杂多模型推理流水线”收敛为“单模型能力升级”，减少部署和维护负担。对研究上，它提供了把训练目标与推理路径联动设计的方向；对工程上，它可能带来更简单的低延迟推理栈，但实际吞吐收益、显存或带宽影响、以及是否依赖特定 GPU，摘要没有充分说明。

## Reading Checklist
- 在线自蒸馏目标具体如何构造？多 token 预测的监督信号、损失设计和训练稳定性机制是什么？
- 超过 3 倍加速是在什么模型规模、GPU/硬件、batch size、上下文长度和解码设置下测得的？与优化良好的 speculative decoding 基线是否公平？
- 除了 GSM8K，这种多 token 预测模型在开放式生成、长文本和不同领域任务上的准确率、校准和退化模式如何？

## Core Contributions
- 提出一种把预训练自回归语言模型直接转成 standalone 多 token 预测模型的在线自蒸馏思路。
- 把推理加速设计成不依赖辅助 speculator 或 verifier 的单模型部署路径，避免额外专用推理代码。
- 在摘要中报告了 GSM8K 上平均超过 3 倍的解码速度提升，并将准确率损失控制在 5% 以内。

## Why Read It
- 它直接针对 LLM inference acceleration，而不是泛化代码任务；核心价值在于能否用训练替代复杂 decoding pipeline。
- 如果单模型多 token 预测成立，serving 栈会比 speculative decoding 更简单，这对线上部署和维护成本很关键。
- 这篇论文适合和现有 speculative decoding 工作对照阅读，重点核查速度收益到底来自模型能力还是评测设定。

## Risks Or Limits
- 系统信息缺口很大：摘要没有给出硬件前提、吞吐或延迟统计口径、显存或带宽影响。
- 证据目前集中在 GSM8K，这更像特定任务验证；对通用文本生成和真实服务流量的外推风险较高。

## Recommended For
- 关注 LLM 推理解码与 serving 简化的研究者
- 评估 speculative decoding 替代路线的系统工程师
- 研究训练目标与推理路径协同设计的团队

## Keywords
- LLM推理系统
- 多token预测
- 在线自蒸馏
- 解码加速
- 自回归语言模型
- speculative decoding替代

## Abstract
Existing techniques for accelerating language model inference, such as speculative decoding, require training auxiliary speculator models and building and deploying complex inference pipelines. We consider a new approach for converting a pretrained autoregressive language model from a slow single next token prediction model into a fast standalone multi-token prediction model using a simple online distillation objective. The final model retains the exact same implementation as the pretrained initial checkpoint and is deployable without the addition of any auxiliary verifier or other specialized inference code. On GSM8K, our method produces models that can decode more than $3\times$ faster on average at $<5\%$ drop in accuracy relative to single token decoding performance.

## Recommendation Signals
- Recommendation score: 9.27
- Relevance score: 3.0
- Recency score: 3.0
- Popularity score: 2.0
- Quality score: 1.6
- Analysis candidate score: 7.57
- Analysis priority rank: 2
- Analysis signals: speculative decoding, decode
