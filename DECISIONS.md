# DECISIONS — llm-file-processor

> ADR-lite。只记录实现期间做出的非平凡选择（技术栈、模式、架构）。
> 最新在上，不预填。

### [2026-10-07] 重试归属 processor 层，openai SDK max_retries=0
- **Context**：模型调用可能瞬时失败（超时 / 5xx），SDK 与 processor 双层重试会叠加，退避行为不可预测
- **Options**：① 用 SDK 内置重试 ② 只在 processor 层重试 ③ 双层重试
- **Decision**：②。`OpenAICompatibleProvider` 建 client 时 `max_retries=0`；`LLMFileProcessor._generate_with_retry` 做指数退避（base * 2^n），次数由 `retries` 控制（Phase 2 起接 `config.retries`）
- **Consequences**：Python API 用户默认也获得重试（好）；重试策略不能按 provider 单独配置（可接受——v1 只有一个 provider）

## 条目模板
### [YYYY-MM-DD] <一句话决策>
- **Context**：为什么需要这个决策
- **Options**：考虑过什么
- **Decision**：选了什么
- **Consequences**：带来什么（包括代价）
