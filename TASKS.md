# TASKS — llm-file-processor

## Phase 1: 核心原子
> Phase 验收：`pytest` 全绿 + 一行脚本用 FakeProvider 完成 文件→文件

- [x] T-001 包骨架
  - `pyproject.toml`：src layout；运行时依赖 `openai`、`python-dotenv`；dev 依赖 `pytest`
  - `.gitignore`：`.env`、`logs/`、`__pycache__/`、`.pytest_cache/`、`dist/`、`*.egg-info/`
  - `src/llm_processor/__init__.py`：暴露 `LLMFileProcessor`、`ProviderConfig`
  - Done when: `pip install -e .` 成功且 `import llm_processor` 无报错

- [x] T-002 config.py
  - `load_config(path=None) -> ProviderConfig`：默认读当前目录 `.env`；`path` 指定其他 env 文件（如 `configs/qwen.env`）
  - 字段：`base_url`、`api_key`、`model`（必填）；`temperature`、`max_tokens`、`retries`（可选，有默认值）
  - 缺必填字段 → 抛带清晰信息的错误（指出字段名和配置文件名）
  - Done when: 单测覆盖 默认加载 / 自定义配置文件 / 缺必填字段报错

- [x] T-003 templates.py
  - `render(template: str, variables: dict) -> str`：替换 `{{ name }}`
  - 模板里有变量但 variables 没提供 → 抛 `TemplateError`（防止拼写错误被静默漏掉）
  - Done when: 单测覆盖 单变量 / 多变量 / 无变量 / 未知变量报错

- [x] T-004 providers/openai_compatible.py
  - `OpenAICompatibleProvider(config).generate(messages) -> str`（基于 openai SDK，注入 `http_client` 以便 mock）
  - API 错误 / 超时 → 抛 `ProviderError`（重试不在这里，由 processor 层处理）
  - Done when: 单测用 mock transport 验证请求体（model / messages / temperature）与错误抛出路径

- [x] T-005 processor.py
  - `LLMFileProcessor(provider).process(input_path, output_path, prompt_path, variables=None, force=False)`
  - 流程：读输入 → 渲染（内置变量 `content`/`filename`/`stem`/`input_path` + 调用方注入变量）→ `generate` → 原子写（tmp + rename）
  - 输出已存在且 `force=False` → skip（返回可区分状态，供批量层汇总）
  - `ProviderError` → 指数退避重试，超过 `config.retries` 后抛出
  - Done when: FakeProvider 单测覆盖 成功 / skip / force / 渲染失败 / 重试耗尽失败

- [x] T-006 Phase 验收
  - Done when: `pytest` 全绿 + 一行脚本用 FakeProvider 完成一个 txt → md 处理

## Phase 2: CLI
> Phase 验收：真实 API（Qwen）跑通一个真实 transcript，输出可读

- [x] T-007 cli.py 核心（`main(argv, processor)`，零网络）
  - `build_parser()`：`--input`/`--input-dir` 互斥必填；`--output`/`--output-dir`；`--prompt` 必填；`--config`/`--ext`/`--force`/`--log-dir`
  - `main(argv=None, processor=None) -> int`：processor 可注入（测试用 FakeProvider）；退出码 0=成功 / 1=处理失败 / 2=用法或配置错误
  - 单文件：输入不存在 → 2；TemplateError/ProviderError/OSError → 1
  - 批量：非递归扫描 `.txt`/`.md`（排序）；输出名 = stem + `--ext`（默认 md）；空目录 → 2
  - TemplateError 属系统性错误：立即中止整批（返回 1）；ProviderError/OSError：记日志 + 跳过继续
  - 逐文件日志写 `logs/process-<ts>.log`（INFO）；stdout 汇总 `完成: X processed, Y skipped, Z failed` + 失败清单；有失败 → 退出码 1
  - Done when: tests/test_cli.py 覆盖 单文件成功 / 单文件失败退出 1 / skip / 批量混合（退出 1 + 失败清单 + 输出命名）/ 模板错误中止 / 参数错误（退出 2）
- [x] T-008 入口与配置接线
  - `build_processor(config_path=None)`：load_config → OpenAICompatibleProvider → LLMFileProcessor(retries=config.retries)
  - pyproject `[project.scripts] llm-process = "llm_processor.cli:main"`；`scripts/process.py` 薄封装
  - ConfigError → stderr + 退出 2
  - Done when: `llm-process --help` 可跑 + build_processor 单测（真实配置文件 → provider.config 正确）
- [x] T-009 Phase 2 验收（真实 API）
  - 填 `.env`（Qwen 端点），单文件命令跑一个 qwen-bv-tts 真实 transcript
  - Done when: 输出 md 可读 + 批量模式冒烟（2 文件，重跑显示 skipped）

## Phase 3: 真实数据端到端 — 玉成任务
> Phase 验收：≥3 个真实 transcript 处理完，笔记质量可用，重跑自动跳过已完成

- [x] T-010 玉成 study_note prompt + 配置
  - `prompts/yucheng/study_note.md`（ASR 转录 → 结构化学习笔记：核心观点/术语/讲例/原话/存疑）
  - `prompts/examples/summarize.md`、`configs/qwen.env`、`.env.example`、`.env`（本地 vLLM 8001）
  - Done when: 单文件真实 API 跑通，输出为结构化笔记且无思考过程污染（`enable_thinking: false`）
- [x] T-011 全量批量：玉成 89 个 transcript → 学习笔记
  - 输出 `~/Documents/knowledge/yucheng/study_notes/study_note_v1/`（任务名 = Prompt 版本）
  - Done when: 89 个笔记全部生成（失败 <5% 且重跑可补齐），抽检质量可用
- [x] T-012 README + 收尾
  - README（用法/配置/结构/上下游）、重跑验证 skipped、全部提交推送
  - Done when: 重跑批量全部 skipped + 仓库与远程同步

## Phase 3.5: 杨炎国学案例管道
> 验收：杨炎 244 个 transcript → 案例笔记，怪物文件单独处理

- [x] T-013 批量并发 `--workers`（线程池）
  - `--workers N`（默认 1 串行；本地模型可调高）
  - 模板变量预检：worker 启动前试渲染一次，Prompt 坏了不浪费整批调用
  - 汇总/失败清单/退出码与串行一致；日志乱序可接受（有时间戳）
  - Done when: 单测覆盖 并发全部成功 / 并发混合失败（退出 1）/ 并发下模板预检中止（零调用）+ 默认串行行为不变
- [ ] T-014 杨炎 244 批量（32K 上下文，workers=10）
  - 输出 `~/Documents/knowledge/yangyanguoxue/case_notes/case_study_v1/`，config=qwen_case.env
  - Done when: 242/244 生成（2 个 >100K 怪物预期撞上下文墙失败，单独处理）+ 重跑 skipped
