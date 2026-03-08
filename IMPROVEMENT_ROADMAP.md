# DailyPaper Improvement Roadmap

## Goal

把当前项目从“通用 AI 论文日报”调整成更适合当前阶段使用的“systems research reading scheduler”。

当前用户画像：

- PhD 初级阶段
- 研究方向以 systems 为主
- 重点关注：
  - LLM inference acceleration
  - LLM code generation for CUDA kernels
  - low-level / PTX / SASS / assembly code generation
- 不是每天都需要固定数量论文
- 更看重筛选质量和阅读价值，而不是生成速度或 token 节省
- 除了新论文，也需要系统补充 3 年以上的重要经典论文

## Current Problems

### 1. Search strategy still follows a single mixed ranking

当前搜索仍然更像“统一候选池 + 统一排序”，这会导致：

- systems 和通用 AI method 使用同一套时间和热度逻辑
- systems 论文供给少时，容易被泛 LLM 论文补位
- 一些真正值得读的 older but important systems papers 无法稳定进入推荐

### 2. Paper count should be treated as an upper bound, not a hard target

当前逻辑容易默认“尽量凑满 6 篇”，但对 systems 方向不合理。

目标应改为：

- 最多 6 篇
- 质量不够时允许只推 4 到 5 篇
- 不为凑数而推泛相关论文

### 3. No persistent memory of recommended / analyzed papers

当前缺少跨天记忆，导致：

- 新旧推送可能重叠
- 无法区分“已经推荐过”与“还没系统读过”
- 无法基于历史阅读状态决定是否再次推荐

### 4. Old important papers are not handled as a first-class source

当前 older papers 仍主要依赖当天搜索临时命中，无法稳定补系统经典。

这对当前阶段不合适，因为：

- 初期需要建立系统研究知识地图
- 很多关键论文发布时间远超 3 年
- old paper 不应该只是新论文不足时的补位

### 5. Quality-first generation is still not strong enough

当前生成链路虽然已经强化，但仍存在这些问题：

- top paper 和普通 paper 的预算差异还不够明显
- enrich 仍有明显的 token 节省倾向
- 重复的指令和 skill 文本占用上下文
- 分析预算没有足够集中到最值得读的一篇论文上

### 6. Full analysis scope is still too wide

当前 top2 full analysis 对当前使用目标并不划算。

更合理的策略：

- 只对 top1 做最精细的 full paper analysis
- 把更多预算用于更好的筛选

## Target Behavior

### Search

- 不强凑论文数量
- systems 论文使用独立策略
- 新论文、已建立论文、经典论文使用不同时间逻辑
- 搜索结果要服务于“今天应该读什么”，而不是“今天最新有什么”

### Recommendation

- 推荐应基于“阅读价值 + 去重记忆 + 当前阶段需要”
- 对已经读过或详细分析过的论文设置冷却期
- 对长期未读但重要的经典论文允许周期性重新激活

### Analysis

- 只做 top1 深度分析
- top1 analysis 质量优先，不节省 token
- 其余论文做高质量但轻量的 systems-style enrich

## Required Changes

## 1. Replace single-pool search with lane-based search

引入 3 条 lane：

- `fresh`
  - 目标：最近 0 到 90 天的新 systems 论文
  - 重点：inference / serving / kernel / runtime / compiler

- `established`
  - 目标：90 天到 3 年之间、已经有一定影响但用户可能还没系统读过的论文

- `classic`
  - 目标：3 年以上的必读论文
  - 不再依赖当天 arXiv 搜索临时召回
  - 作为一条 slow lane 周期性出现，而不是每天硬塞

推荐合并策略：

- 先从 `fresh` 中选 2 到 3 篇
- 再从 `established` 中补 1 到 2 篇
- `classic` 每隔几天自动插入 1 篇
- 总数最多 6 篇，不足则少推

## 2. Systems-specific search signals must be stronger

必须强化真正 systems 论文的正向信号。

高价值强信号示例：

- `speculative decoding`
- `kv cache`
- `paged attention`
- `flashattention`
- `vllm`
- `cuda`
- `triton`
- `ptx`
- `sass`
- `kernel`
- `prefill`
- `decode`
- `runtime`
- `compiler`
- `throughput`
- `latency`
- `bandwidth`
- `H100`
- `B200`
- `GB200`

需要额外 bonus 的条件：

- 明确硬件平台
- 明确 kernel / runtime / compiler 术语
- 明确系统指标（latency / throughput / memory / bandwidth）
- 明确 serving / inference workload

需要额外 penalty 或直接过滤的条件：

- 只有泛 `LLM / transformer / quantization / serving` 命中，没有 systems 强信号
- GNN / molecular / medical / multimodal / generic reasoning / pretraining-only
- 与 kernel / runtime / inference 不强相关的泛 AI 论文

## 3. Introduce a persistent index file

新增持久索引文件：

- `state/paper_index.json`

建议记录字段：

- `paper_id`
- `title`
- `first_seen_date`
- `last_seen_date`
- `last_recommended_date`
- `recommended_count`
- `last_analysis_date`
- `analyzed_count`
- `source_lane`
- `topics`
- `scores_history`
- `reading_status`
- `cooldown_until`
- `priority_class`

`reading_status` 建议：

- `unread`
- `skimmed`
- `read`
- `analyzed`
- `archived`

索引的主要用途：

- 防止重复推送
- 支持冷却期
- 支持重要旧论文重新激活
- 支持后续 classic backlog 的调度

## 4. Add classic backlog as a first-class mechanism

新增 classic backlog 文件，例如：

- `state/classic_backlog.yaml`

或

- `state/classic_backlog.json`

它不应依赖当天搜索临时生成，而应长期维护。

来源包括：

- repo 内置的 systems classics seed pool
- 已推送论文的 upstream / canonical references
- top1 analysis 中提取出的相关工作
- citation graph 中高价值节点
- 后续接入 OpenAlex / DBLP 后自动扩展

字段建议：

- `paper_id`
- `title`
- `venue`
- `year`
- `reason_to_read`
- `topic_tags`
- `priority`
- `status`
- `times_recommended`
- `times_skipped`

调度规则：

- 默认不要求用户手工维护
- 先由 repo 内置一批 systems classics
- 每隔 `N` 天 deterministically 随机取 1 篇
- classic 使用独立 cooldown，避免短时间重复出现

## 5. Add cooldown and reactivation policy

推荐冷却策略：

- 普通推荐论文：45 到 60 天内不重复推荐
- full-analysis 论文：180 到 365 天内默认不重复推荐
- classic 论文如果仍是 `unread`，可以在较长周期后重新出现
- 如果旧论文与当天 top1 强相关，可以提前激活

## 6. Expand sources in a structured way

不建议“盲目加更多源”，而应按角色扩充。

### Primary sources for fresh papers

- arXiv
- OpenReview

### Primary sources for metadata and graph

- OpenAlex
- DBLP

### Primary sources for established / classic systems papers

- official venue pages

建议覆盖的 venue：

- MLSys
- ASPLOS
- ISCA
- MICRO
- HPCA
- SOSP
- OSDI
- NSDI
- USENIX ATC
- EuroSys
- SC
- PPoPP
- CGO
- PLDI

### Metadata fallback only

- Semantic Scholar
- Google Scholar

Google Scholar 不应作为主召回源，只应作为最后的 metadata fallback。

## 7. Separate recommendation score from analysis score

不能直接把 daily rank #1 等同于 full-analysis 对象。

建议新增：

- `recommendation_score`
- `analysis_candidate_score`

`analysis_candidate_score` 更看重：

- 是否强贴合当前研究主线
- 是否有足够方法和实验内容可深读
- 是否具有系统或工程价值
- 是否值得投入较长阅读时间

## 8. Reduce full analysis scope to top1 only

把 full analysis 改为：

- 只分析 top1

这样可以：

- 显著降低分析成本
- 把预算集中到最值得读的一篇
- 把更多资源用于筛选质量

## 9. Make top1 generation quality-first

top1 的生成策略应与普通论文完全区分。

### top1 should get:

- 更长的全文上下文
- 更高的 section budget
- 更高的输出预算
- 更少重复仓库说明
- 更强的 systems-specific analysis instructions

### top1 output must focus on:

- bottleneck 在哪里
- gain 来自哪条硬件 / kernel / memory 路径
- baseline 公平性
- 实验平台与硬件依赖
- 是否能迁移到其他 GPU / runtime
- 是否真的值得读全文

## 10. Keep normal papers lightweight but high-signal

非 top1 论文仍做 enrich，但应控制为：

- 高质量 systems-style note
- 不追求 full memo
- 不浪费分析预算

## 11. Improve current config and script behavior

当前需要修复或调整的行为：

- `search.top_n` 应真正从配置生效，而不需要额外用 CLI 参数覆盖
- daily 数量逻辑应支持“最多 N 篇，而不是必须 N 篇”
- systems lane 应支持独立时间窗口
- old paper lane 不应再依赖 daily arXiv 搜索

## Proposed Implementation Order

### Phase 1: Search architecture

1. 引入 `paper_index.json`
2. 支持 `<= 6` 的推荐上限
3. 改成 `fresh / established / classic` 三条 lane
4. 增加 systems-specific scoring / penalty
5. 让 `search.top_n` 从配置真正生效

### Phase 2: Memory and classics

1. 新增 `classic_backlog`
2. 加冷却期与重新激活规则
3. 把历史推送 / 分析结果写回 `paper_index`

### Phase 3: Source expansion

1. 接 OpenAlex
2. 接 DBLP
3. 接 official systems venue sources
4. 保留 Semantic Scholar / Google Scholar 作为 metadata fallback

### Phase 4: Quality-first generation

1. 把 full analysis 改为 top1 only
2. 增大 top1 上下文和预算
3. 减少普通论文生成开销
4. 给 top1 使用更强的 systems-specific analysis template

## Acceptance Criteria

改造完成后，系统应满足：

- 每天推送数量可以少于 6，但不明显跑偏
- 推送结果更稳定贴合 systems 主线
- 泛 LLM / 非 systems 论文不再经常挤进 top list
- old important papers 能稳定进入阅读流
- 已推荐或已分析论文不会高频重复出现
- top1 analysis 明显更深、更有 systems 价值
- 普通 paper enrich 保持高信号但不过度耗费预算

## Immediate Priority

优先级最高的不是继续改 prompt，而是：

1. `paper_index.json`
2. lane-based search
3. top1-only full analysis
4. classic backlog

只有这些做好后，后续 source expansion 和 prompt 强化才会真正有效。
