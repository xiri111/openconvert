"""OpenConvert 插件契约。

唯一允许插件 import 的模块，公开名只有五个：
``PLUGIN_API_VERSION``、``Table``、``ExporterError``、``Exporter`` 以及本模块本身。

契约内容与 ``docs/DESIGN.docx`` 第 4.1 节保持一致；改动本文件即改动契约，
必须升 ``PLUGIN_API_VERSION`` 并同步插件与文档。
"""

from dataclasses import dataclass
from typing import Protocol, TextIO

PLUGIN_API_VERSION = 1


@dataclass(frozen=True)
class Table:
    """转换过程中的唯一数据结构。

    四条不变式在构造时校验，不满足直接抛 :class:`ValueError`：

    1. 每行长度等于列数——少一格表格就会塌；
    2. 所有值都是 ``str``，任何位置不出现 ``None``；
    3. 空单元格与缺列都表示为 ``""``，二者不做区分；
    4. 列名已去重、空表头已规范化为 ``column_N``。
    """

    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    source: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.columns, tuple):
            raise ValueError("columns 必须是 tuple[str, ...]")

        for index, column in enumerate(self.columns, start=1):
            if not isinstance(column, str) or not column:
                raise ValueError(f"第 {index} 个列名不是非空字符串：{column!r}")
        if len(set(self.columns)) != len(self.columns):
            raise ValueError(f"列名存在重复：{self.columns!r}")

        if not isinstance(self.rows, tuple):
            raise ValueError("rows 必须是 tuple[tuple[str, ...], ...]")

        width = len(self.columns)
        for row_index, row in enumerate(self.rows, start=1):
            if not isinstance(row, tuple):
                raise ValueError(f"第 {row_index} 行不是 tuple：{type(row).__name__}")
            if len(row) != width:
                raise ValueError(
                    f"第 {row_index} 行有 {len(row)} 格，列数是 {width}"
                )
            for cell_index, cell in enumerate(row, start=1):
                if not isinstance(cell, str):
                    raise ValueError(
                        f"第 {row_index} 行第 {cell_index} 格不是 str：{cell!r}"
                    )


class ExporterError(Exception):
    """导出器唯一允许抛出的异常。

    ``code`` 供程序判断（如 ``EMPTY_TABLE``），``message`` 会原样展示给用户，
    因此只写一句人话，不带内部细节。
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Exporter(Protocol):
    """导出器契约：四个属性加一个方法。"""

    api_version: int
    format_name: str
    display_name: str
    suffix: str

    def export(self, table: Table, out: TextIO) -> None:
        """把 ``table`` 写成文本写入 ``out``；不碰文件系统，不打印。"""
