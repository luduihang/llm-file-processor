# DECISIONS — llm-file-processor

> ADR-lite。只记录实现期间做出的非平凡选择（技术栈、模式、架构）。
> 最新在上，不预填。

### [2026-10-07] 思考模型关思考走 LLM_EXTRA_BODY，provider 保持协议无关
- **Context**：Qwen3.8-27B（vLLM 8001）默认输出思考过程，思考文本挤占 max_tokens，笔记写不完且被推理污染
- **Options**：① provider 硬编码 enable_thinking ② prompt 里加 /no_think ③ 配置层 LLM_EXTRA_BODY（JSON 直通请求体）
- **Decision**：③。`LLM_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": false}}`；provider 仅在非空时透传，不知道 vLLM 存在
- **Consequences**：任意 provider 的私有参数都能通过配置接入，代码零改动（好）；JSON 字符串配置可读性一般（可接受）

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
