"""Markdown 导出器的契约测试。

断言到完整输出字符串，不做 ``is not None`` 之类的弱断言。
"""

import io

import pytest

pytest.importorskip("openconvert.exporter_api", reason="契约尚未就绪，跳过")

from openconvert.exporter_api import PLUGIN_API_VERSION, ExporterError, Table  # noqa: E402
from openconvert_md.exporter import MarkdownExporter  # noqa: E402


def render(columns, rows):
    """把列名与行数据渲染成 Markdown 文本。"""
    table = Table(columns=tuple(columns), rows=tuple(tuple(r) for r in rows))
    buf = io.StringIO()
    MarkdownExporter().export(table, buf)
    return buf.getvalue()


def test_元信息与契约版本一致():
    ex = MarkdownExporter()
    assert ex.api_version == PLUGIN_API_VERSION
    assert ex.format_name == "markdown"
    assert ex.display_name == "Markdown 表格"
    assert ex.suffix == ".md"


def test_基础表格逐行相等():
    out = render(["姓名", "分数"], [["张", "90"], ["李", "85"]])
    assert out.splitlines() == [
        "| 姓名 | 分数 |",
        "| --- | --- |",
        "| 张 | 90 |",
        "| 李 | 85 |",
    ]


def test_竖线被转义():
    out = render(["a|b"], [["c|d"]])
    assert out.splitlines() == ["| a\\|b |", "| --- |", "| c\\|d |"]


def test_换行转成_html_换行():
    out = render(["h"], [["第一行\r\n第二行"]])
    assert out.splitlines()[2] == "| 第一行<br>第二行 |"
    assert "\r" not in out


def test_空单元格保留分隔符():
    out = render(["a", "b"], [["", "x"]])
    assert out.splitlines()[2] == "|  | x |"


def test_零行数据只输出表头与分隔行():
    out = render(["a", "b"], [])
    assert out.splitlines() == ["| a | b |", "| --- | --- |"]


def test_单列表格():
    out = render(["only"], [["v"]])
    assert out.splitlines() == ["| only |", "| --- |", "| v |"]


def test_反引号原样保留():
    out = render(["h"], [["`code`"]])
    assert out.splitlines()[2] == "| `code` |"


def test_无列时抛导出错误():
    with pytest.raises(ExporterError):
        render([], [])
