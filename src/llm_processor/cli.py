"""CLI：llm-process 单文件 / 批量处理入口。

用法：
  llm-process --input x.txt --output x.md --prompt prompts/yucheng/study_note.md
  llm-process --input-dir in/ --output-dir out/ --prompt prompts/yucheng/study_note.md
              --config configs/qwen.env --force

退出码：0=成功 / 1=处理失败（或模板错误）/ 2=用法或配置错误
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import ConfigError, load_config
from .processor import LLMFileProcessor, ProcessStatus
from .providers import OpenAICompatibleProvider, ProviderError
from .templates import TemplateError

TEXT_EXTS = {".txt", ".md"}

log = logging.getLogger("llm-process")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="llm-process",
        description="文件 → LLM → 文件：用 Prompt 模板 + 模型处理文本文件",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", help="单输入文件（.txt/.md）")
    src.add_argument("--input-dir", help="批量输入目录（非递归，.txt/.md）")
    p.add_argument("--output", help="输出文件（--input 时必填）")
    p.add_argument("--output-dir", help="输出目录（--input-dir 时必填）")
    p.add_argument("--prompt", required=True, help="Prompt 模板文件")
    p.add_argument("--config", default=None, help="env 配置文件（默认 ./.env）")
    p.add_argument("--ext", default="md", help="批量模式输出扩展名（默认 md）")
    p.add_argument("--force", action="store_true", help="覆盖已有输出")
    p.add_argument("--log-dir", default="logs", help="日志目录（默认 logs）")
    return p


def setup_logging(log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"process-{datetime.now():%Y%m%d-%H%M%S}.log"
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    log.handlers = [fh, sh]  # 重置 handler，避免重复调用时叠加
    return log_file


def build_processor(config_path: Optional[str] = None) -> LLMFileProcessor:
    """--config / .env → Provider（生产路径；测试直接注入 processor）。"""
    config = load_config(config_path)
    provider = OpenAICompatibleProvider(config)
    return LLMFileProcessor(provider, retries=config.retries)


def main(argv: Optional[list[str]] = None, processor: Optional[LLMFileProcessor] = None) -> int:
    args = build_parser().parse_args(argv)
    prompt = Path(args.prompt)
    if not prompt.is_file():
        print(f"错误: Prompt 文件不存在: {prompt}", file=sys.stderr)
        return 2
    if (args.input and not args.output) or (args.input_dir and not args.output_dir):
        print(
            "错误: --input 需配 --output，--input-dir 需配 --output-dir", file=sys.stderr
        )
        return 2

    setup_logging(Path(args.log_dir))

    if processor is None:
        try:
            processor = build_processor(args.config)
        except ConfigError as e:
            print(f"错误: {e}", file=sys.stderr)
            return 2

    if args.input:
        return _run_single(processor, args, prompt)
    return _run_batch(processor, args, prompt)


def _run_single(processor: LLMFileProcessor, args, prompt: Path) -> int:
    inp = Path(args.input)
    if not inp.is_file():
        print(f"错误: 输入文件不存在: {inp}", file=sys.stderr)
        return 2
    out = Path(args.output)
    t0 = time.time()
    try:
        status = processor.process(inp, out, prompt, force=args.force)
    except (TemplateError, ProviderError, OSError) as e:
        log.error("FAILED %s: %s", inp, e)
        print(f"失败: {inp}: {e}", file=sys.stderr)
        return 1
    log.info("%s %s -> %s (%.1fs)", status.value, inp, out, time.time() - t0)
    print(f"{status.value}: {inp} -> {out}")
    return 0


def _run_batch(processor: LLMFileProcessor, args, prompt: Path) -> int:
    in_dir = Path(args.input_dir)
    if not in_dir.is_dir():
        print(f"错误: 输入目录不存在: {in_dir}", file=sys.stderr)
        return 2
    files = sorted(
        p for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() in TEXT_EXTS
    )
    if not files:
        print(f"错误: 输入目录无 .txt/.md 文件: {in_dir}", file=sys.stderr)
        return 2
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = args.ext.lstrip(".")

    processed = skipped = failed = 0
    failures: list[tuple[str, str]] = []
    for f in files:
        out = out_dir / f"{f.stem}.{ext}"
        t0 = time.time()
        try:
            status = processor.process(f, out, prompt, force=args.force)
        except TemplateError as e:
            # 系统性错误（Prompt 本身有问题）：立即中止整批，不浪费后续调用
            log.error("模板错误，中止批量: %s", e)
            print(f"失败: 模板错误，中止批量: {e}", file=sys.stderr)
            return 1
        except (ProviderError, OSError) as e:
            failed += 1
            failures.append((f.name, str(e)))
            log.error("FAILED %s: %s", f, e)
            continue
        if status == ProcessStatus.SKIPPED:
            skipped += 1
        else:
            processed += 1
        log.info("%s %s -> %s (%.1fs)", status.value, f, out.name, time.time() - t0)

    print(f"完成: {processed} processed, {skipped} skipped, {failed} failed")
    for name, err in failures:
        print(f"  - {name}: {err}")
    return 1 if failed else 0
