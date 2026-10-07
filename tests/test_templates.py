"""T-003: templates.render 单元测试（TDD：先于实现）。"""

import pytest

from llm_processor.templates import TemplateError, render


def test_render_single_variable():
    assert render("hi {{ name }}", {"name": "world"}) == "hi world"


def test_render_multiple_variables():
    assert render("{{ a }}-{{ b }}-{{ c }}", {"a": 1, "b": "x", "c": 3.5}) == "1-x-3.5"


def test_render_no_variables():
    assert render("plain text", {}) == "plain text"


def test_render_repeated_variable():
    assert render("{{ x }} and {{ x }}", {"x": "y"}) == "y and y"


def test_variable_value_not_reexpanded():
    """变量值里的 {{ }} 不再渲染（输入 content 可能含花括号）。"""
    assert render("{{ content }}", {"content": "{{ nested }}"}) == "{{ nested }}"


def test_unknown_variable_raises():
    with pytest.raises(TemplateError) as exc:
        render("hello {{ name }}", {})
    assert "name" in str(exc.value)


def test_multiple_unknown_still_raises():
    with pytest.raises(TemplateError):
        render("{{ a }} {{ b }}", {})
