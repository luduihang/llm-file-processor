# VISION — llm-file-processor

## 一句话定位
通用的「文件 → LLM 加工 → 文件」处理工具：**Python Library + CLI + Prompt 模板**。
文件是输入输出边界，Prompt 是业务逻辑，Provider 是模型能力，Processor 只负责把三者连接起来。

## 为谁、解决什么问题
- **客户**：我自己（开发者）。第一个真实应用 = 玉成八字学习笔记；之后是任何「一批文本文件用 LLM 批量加工」的场景（会议记录、课程笔记、论文、小说、代码文档）。
- **问题（我的原话视角）**：
  - 手上一批文本文件（B站 ASR 字幕、会议记录……）
  - 想用「某个 Prompt + 某个模型」统一加工成另一种文本
  - 不想每次手写脚本，业务逻辑不该写死在 Python 里
- **上游关系**：`qwen-bv-tts` 只生产原料（transcripts），本项目只消费**文件路径**，两边代码零依赖。

## v1 范围（最小可用）
1. **原子 Processor**：`processor.process(input_path, output_path, prompt_path, variables=None, force=False)`
   - 读输入 → 读 prompt → 渲染模板 → 调模型 → 写输出
   - 不知道批量、B站、八字、玉成的存在
2. **模板变量**：内置 `{{ content }}` `{{ filename }}` `{{ stem }}` `{{ input_path }}`；调用方可注入任意变量（`variables={"bvid": ...}`）
3. **Provider 层**：v1 只实现 `openai_compatible`（base_url / api_key / model / temperature / max_tokens）
4. **模型配置**：`.env` 或 `--config xxx.env`；Prompt 管"做什么"，配置管"谁来做"，同一 Prompt 可换模型 A/B
5. **CLI（`llm-process`）**：
   - 单文件：`--input x.txt --output x.md --prompt prompts/yucheng/study_note.md`
   - 批量：`--input-dir ... --output-dir ... --prompt ...`
   - 默认跳过已有输出（断点续跑），`--force` 覆盖
6. **Prompt 目录约定**：`prompts/<domain>/<task_vN>.md`；输出目录按任务名组织，改 Prompt 出新版不覆盖旧版
7. **失败处理**：单文件失败指数退避重试；仍失败则记日志 + 跳过，批量继续

## 明确不做（v1 之外）
- HTTP API（FastAPI）——等网页/Agent/其他项目要调用时再套最外层，核心逻辑零改动
- 非 OpenAI 兼容协议（Anthropic 原生等）
- 非文本格式（.json/.csv）、并发、费用统计

## 核心设计原则
1. 文件是输入输出边界
2. Prompt = 业务逻辑（换任务 = 换 Prompt 文件，零代码改动）
3. Provider = 模型能力（换模型 = 换配置，零代码改动）
4. Processor 原子化：单文件进 → 单文件出，批量是外层循环
5. 数据来源与数据加工解耦：文件路径连接

## Domain Glossary
| 术语 | 含义 |
|---|---|
| Processor | `LLMFileProcessor`，原子处理单元：单文件进 → 单文件出 |
| Provider | 模型调用抽象，v1 仅 `openai_compatible` |
| Prompt 模板 | 含 `{{ variable }}` 占位符的 Markdown 文件，承载全部业务逻辑 |
| 内置变量 | `content` / `filename` / `stem` / `input_path`，Processor 自动注入 |
| 注入变量 | 调用方通过 `variables=` 传入的任意键值（如 `bvid`、`title`） |
| 任务名 | 输出目录的组织维度，对应某版 Prompt（如 `study_note_v1`） |
| 原料 | 上游项目（如 `qwen-bv-tts`）产出的原始转录文本，本项目只读 |
| 玉成任务 | 第一个真实应用：八字视频字幕 → 学习笔记，位于 `prompts/yucheng/` |

## 目录骨架（v1）
```
llm-file-processor/
├── README.md
├── pyproject.toml
├── .env.example
├── prompts/
│   ├── examples/summarize.md
│   └── yucheng/study_note.md
├── src/llm_processor/
│   ├── __init__.py
│   ├── processor.py
│   ├── config.py
│   ├── templates.py
│   └── providers/
│       ├── __init__.py
│       └── openai_compatible.py
├── scripts/process.py        # CLI 入口
├── tests/
└── logs/
```
