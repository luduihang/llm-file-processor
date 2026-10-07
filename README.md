# llm-file-processor

文件 → LLM → 文件：通用文本文件加工工具（Python Library + CLI + Prompt 模板）。

**文件是输入输出边界，Prompt 是业务逻辑，Provider 是模型能力，Processor 只负责把三者连接起来。**

## 设计

- **原子 Processor**：单文件进 → 单文件出。核心处理器不知道批量、B站、八字的存在。
- **Prompt = 业务逻辑**：换任务 = 换 `prompts/<domain>/<task>.md`，零代码改动。
- **Provider = 模型能力**：换模型 = 换配置（`.env` / `configs/*.env`），零代码改动。v1 只实现 `openai_compatible`（覆盖 OpenAI / DeepSeek / Qwen / 硅基流动 / 火山 / vLLM / Ollama 兼容端点）。
- **批量是外层 for 循环**：指数退避重试 + 跳过已有输出（断点续跑）+ 逐文件日志。
- **输出格式由 Prompt 决定**，不由 Processor 决定（输出 `.md` 就是 Markdown）。

```
                 ┌──────── Prompt A
                 ├──────── Prompt B
                 └──────── Prompt C
                          │
                          ▼
txt / md ──→ LLMFileProcessor ──→ md / txt
                    │
                Provider
           OpenAI Compatible API
```

## 安装

```bash
uv venv .venv
uv pip install -e ".[dev]"
```

## 配置

复制 `.env.example` 为 `.env`（或 `configs/<名字>.env`）：

```ini
LLM_BASE_URL=http://192.168.0.190:8001/v1   # 必填
LLM_API_KEY=EMPTY                            # 必填（vLLM 可随便填）
LLM_MODEL=Qwen3.8-27B-W4A16-AutoRound        # 必填
LLM_TEMPERATURE=0.3                          # 可选，默认 0.7
LLM_MAX_TOKENS=4096                          # 可选，默认 4096
LLM_RETRIES=3                                # 可选，默认 3
LLM_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": false}}  # 可选，JSON 直通请求体
```

`LLM_EXTRA_BODY` 用于协议相关的扩展参数（如 vLLM 思考模型的 `enable_thinking` 开关）。

## 用法

```bash
# 单文件
llm-process --input in.txt --output out.md --prompt prompts/yucheng/study_note.md

# 批量目录（输出名 = 输入 stem + --ext，默认 md）
llm-process --input-dir /path/to/transcripts \
            --output-dir /path/to/study_notes \
            --prompt prompts/yucheng/study_note.md \
            --config configs/qwen.env

# 重跑：已有输出自动跳过（断点续跑）；--force 覆盖
```

退出码：`0` 成功 / `1` 有文件失败（或模板错误）/ `2` 用法或配置错误。
逐文件日志写 `logs/process-<时间戳>.log`。

## Prompt 模板

模板里的 `{{ 变量 }}` 由 Processor 渲染。内置变量：`{{ content }}`（文件内容）、`{{ filename }}`、`{{ stem }}`、`{{ input_path }}`；调用方可注入任意变量（如 `{{ bvid }}`）。引用了未提供的变量会直接报错（防止拼写错误被静默漏掉）。

```markdown
# 任务
把下面的文本整理成学习笔记。

文件名：{{ filename }}

# 转录文本

{{ content }}
```

## 项目结构

```
src/llm_processor/
├── cli.py                  # llm-process 入口（单文件/批量/日志/汇总）
├── config.py               # .env / --config → ProviderConfig
├── processor.py            # LLMFileProcessor：原子处理 + 重试
├── templates.py            # {{ var }} 渲染
└── providers/
    └── openai_compatible.py
prompts/
├── examples/summarize.md
├── yucheng/study_note.md   # 玉成盲派八字：转录 → 学习笔记（知识点型）
└── yangyanguoxue/case_study_v1.md  # 杨炎国学：案例复盘型（老师思路链条 + 先断后验）
configs/
├── qwen.env                # 本地 vLLM Qwen3.8-27B-W4A16（max_tokens 4096）
└── qwen_case.env           # 案例笔记专用（max_tokens 8192，输出需求大）
scripts/process.py          # python scripts/process.py ...（等价 llm-process）
tests/                      # 37 个单元测试，零网络（FakeProvider / MockTransport）
```

## 上下游

上游 `qwen-bv-tts` 生产原料（B站视频 ASR 转录），本项目只消费**文件路径**，代码零依赖。
第一个真实应用：玉成盲派八字视频转录 → 学习笔记（输出到 `~/Documents/knowledge/yucheng/study_notes/`，按 Prompt 版本分目录）。

## 测试

```bash
.venv/bin/pytest    # 37 passed，零网络
```
