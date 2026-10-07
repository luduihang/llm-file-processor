# PLAN — llm-file-processor (v1)

原则：每个 phase 小而端到端有用；只规划 v1。

## Phase 1: 核心原子（纯 Python，零真实 API 调用）
目标：`processor.process()` 可从 Python 直接调用，单元测试全绿。
- 包骨架：`pyproject.toml`（src layout + pytest）、`.gitignore`
- `config.py`：加载 `.env` / `--config` 文件 → `ProviderConfig`（base_url / api_key / model / temperature / max_tokens / retries）
- `providers/openai_compatible.py`：`generate(messages) -> str`
- `templates.py`：`{{ var }}` 替换；内置变量 `content`/`filename`/`stem`/`input_path` + 注入变量
- `processor.py`：`LLMFileProcessor.process()` 原子（读 → 渲染 → 调用 → 原子写 tmp+rename）
- tests：FakeProvider（无网络），覆盖模板渲染、原子流程、skip/force 语义
**验收**：`pytest` 全绿 + 一行脚本用 FakeProvider 完成 文件→文件

## Phase 2: CLI（接真实 API）
目标：`llm-process` 单文件 + 批量目录在 shell 可用。
- `scripts/process.py` + `llm-process` 入口
- 单文件模式 / 批量模式（`--input-dir` / `--output-dir`，输出名 = 输入 stem + `--ext`（默认 md））
- 重试（指数退避）+ 跳过已有输出 + `--force` + 日志写 `logs/`
- 批量结束输出汇总：成功 / 跳过 / 失败清单
**验收**：真实 API（Qwen）跑通一个真实 transcript，输出可读

## Phase 3: 真实数据端到端 — 玉成任务
目标：玉成 transcripts → 学习笔记的批量管道可用。
- `prompts/yucheng/study_note.md`（学习笔记 prompt，基于之前对话的设计稿；若设计稿不全则重新定稿）
- `prompts/examples/summarize.md`（通用示例）
- `configs/*.env`（如 qwen.env）+ `.env.example`
- 批量跑 `qwen-bv-tts/data/3706946339212259 玉成一盲派一事业/transcripts/` → 输出目录（任务名 `study_note_v1`）
- README（用法 + 设计原则）
**验收**：≥3 个真实 transcript 处理完，笔记质量可用，重跑自动跳过已完成

## 明确不做
见 VISION.md「明确不做」（HTTP API / 其他协议 / 非文本 / 并发）。
