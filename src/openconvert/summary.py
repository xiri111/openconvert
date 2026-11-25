"""摘要与格式表：命令行上「给人看的文字」都从这里出。

刻意不认识 ``Table``：统计数字由 CLI 传进来，本模块只负责排版，
这样``--quiet`` 的开关也只有 CLI 一个地方管。
"""

import unicodedata
from collections.abc import Iterable
from typing import Protocol


class FormatRow(Protocol):
    """``formats`` 命令需要的最小信息，与 ``registry.FormatInfo`` 结构一致。"""

    name: str
    display_name: str
    source: str
    api_version: int


def format_size(size: int) -> str:
    """把字节数写成 ``512 B`` / ``1.2 KB`` / ``3.4 MB``。"""
    if size < 1024:
        return f"{size} B"
    value = size / 1024
    for unit in ("KB", "MB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def format_summary(
    *,
    rows: int,
    columns: int,
    elapsed: float,
    path: str,
    size: int,
) -> str:
    """成功摘要固定四要素：条数、列数、耗时、文件大小。"""
    return (
        f"已转换：{rows} 条记录，{columns} 列，"
        f"耗时 {elapsed:.2f} 秒，输出到 {path}（{format_size(size)}）"
    )


def _display_width(text: str) -> int:
    """终端显示宽度：中文与全角字符占两格。"""
    return sum(
        2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text
    )


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def format_formats(rows: Iterable[FormatRow]) -> str:
    """``formats`` 的输出：格式名、显示名、来源、契约版本。"""
    items = list(rows)
    if not items:
        return "可用格式：无"

    headers = ("格式", "显示名", "来源", "契约版本")
    body = [[item.name, item.display_name, item.source, f"v{item.api_version}"] for item in items]
    widths = [max(_display_width(row[index]) for row in [headers, *body]) for index in range(3)]

    lines = [f"可用格式（{len(items)} 个）：", ""]
    lines.append(
        "  " + "  ".join(_pad(headers[index], widths[index]) for index in range(3))
        + "  " + headers[3]
    )
    for row in body:
        lines.append(
            "  " + "  ".join(_pad(row[index], widths[index]) for index in range(3))
            + "  " + row[3]
        )
    return "\n".join(lines)
