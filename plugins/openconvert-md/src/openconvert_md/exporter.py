r"""Markdown 表格导出器。

转换规则（与设计文档“Markdown 导出规则”表一致）：

- 竖线 ``|`` → ``\|``：不转义会破坏列结构
- ``\r\n`` / ``\r`` 先归一为 ``\n``，再替换为 ``<br>``：GFM 单元格不支持换行
- 空字符串 → 空单元格，保留分隔符：不能吞列导致错位
- 反引号与 ``<`` ``>`` 原样保留：渲染器会解释，属已知限制

分隔行固定写 ``| --- | --- |``，不按内容宽度补空格：保证同输入同字节。
"""

from __future__ import annotations

from typing import TextIO

from openconvert.exporter_api import PLUGIN_API_VERSION, ExporterError, Table


def _cell(value: str) -> str:
    """把单元格内容转成 GFM 表格里安全的文本。"""
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("|", "\\|").replace("\n", "<br>")


class MarkdownExporter:
    """把 ``Table`` 写成 GFM 表格。"""

    api_version = PLUGIN_API_VERSION
    format_name = "markdown"
    display_name = "Markdown 表格"
    suffix = ".md"

    def export(self, table: Table, out: TextIO) -> None:
        """把 ``table`` 写入已打开的输出流；不碰文件系统，不打印。"""
        columns = table.columns
        if not columns:
            raise ExporterError("EMPTY_TABLE", "没有可导出的列")

        out.write("| " + " | ".join(_cell(c) for c in columns) + " |\n")
        out.write("|" + "|".join([" --- "] * len(columns)) + "|\n")
        for row in table.rows:
            out.write("| " + " | ".join(_cell(v) for v in row) + " |\n")
