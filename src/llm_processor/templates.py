"""Prompt 模板渲染：{{ variable }} 替换。

Python = 执行能力，Prompt = 业务逻辑。模板承载业务，代码只做替换。
"""

import re

_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}}")


class TemplateError(ValueError):
    """模板变量缺失。"""


def render(template: str, variables: dict) -> str:
    """把 template 中的 {{ name }} 替换为 variables 对应值。

    - 变量值不再递归渲染（content 可能含 {{ }} 字符）
    - 模板引用了 variables 未提供的变量 → TemplateError（防止拼写错误被静默漏掉）
    """

    def _sub(match: re.Match) -> str:
        name = match.group(1)
        if name not in variables:
            raise TemplateError(
                f"模板变量缺失: {name} (已提供: {sorted(variables)})"
            )
        return str(variables[name])

    return _VAR_RE.sub(_sub, template)
