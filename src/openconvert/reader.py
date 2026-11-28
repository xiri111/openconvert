"""读取并规范化 CSV。

承担全部脏活：解码、跳过全空行、列数对齐、表头规范化。
判断内容含义不在本层——数字、日期、编号一律当字符串。
"""

import csv
import warnings
from pathlib import Path

from . import record
from .exporter_api import Table

# 纯 UTF-8 时用 utf-8-sig，BOM 会被自动去掉，不会残留在第一个列名里。
_UTF8_NAMES = {"utf-8", "utf8", "u8"}


class CSVReadError(Exception):
    """输入文件读不了或解码失败；CLI 据此给提示并以退出码 3 结束。"""

    def __init__(
        self,
        message: str,
        *,
        path: str = "",
        encoding: str = "",
        position: int | None = None,
    ) -> None:
        super().__init__(message)
        self.path = path
        self.encoding = encoding
        self.position = position


def _is_blank(row: list[str]) -> bool:
    """全空行：整行没有内容，或每个格子都是空白。"""
    return not row or all(not cell.strip() for cell in row)


def _decoder_for(encoding: str) -> str:
    normalized = encoding.strip().lower().replace("_", "-")
    return "utf-8-sig" if normalized in _UTF8_NAMES else encoding


def read_csv(path: str | Path, *, encoding: str = "utf-8") -> Table:
    """读 CSV 并返回 ``Table``。

    空文件返回空表（``columns`` 与 ``rows`` 均为空元组），由导出器自行决定如何表现。
    """
    source = Path(path)
    decoder = _decoder_for(encoding)

    try:
        with source.open("r", encoding=decoder, newline="") as stream:
            reader = csv.reader(stream)

            headers: list[str] | None = None
            for row in reader:
                if _is_blank(row):
                    continue
                headers = row
                break

            if headers is None:
                return Table(columns=(), rows=(), source=str(source))

            columns = record.normalize_columns(headers)
            width = len(columns)

            rows: list[tuple[str, ...]] = []
            truncated_at: int | None = None
            truncated_rows = 0
            for row in reader:
                if _is_blank(row):
                    continue
                if len(row) > width:
                    truncated_at = truncated_at or reader.line_num
                    truncated_rows += 1
                rows.append(record.fit_row(row, width))

            if truncated_rows:
                warnings.warn(
                    f"{source}：第 {truncated_at} 行起共有 {truncated_rows} 行"
                    f"超出 {width} 列，多余列已忽略",
                    UserWarning,
                    stacklevel=2,
                )

            return Table(columns=columns, rows=tuple(rows), source=str(source))

    except UnicodeDecodeError as exc:
        raise CSVReadError(
            f"无法解码输入文件：{source}（编码 {encoding}，第 {exc.start} 字节）",
            path=str(source),
            encoding=encoding,
            position=exc.start,
        ) from exc
    except csv.Error as exc:
        raise CSVReadError(
            f"无法解析 CSV：{source}（第 {reader.line_num} 行，{exc}）",
            path=str(source),
            encoding=encoding,
        ) from exc
    except OSError as exc:
        raise CSVReadError(f"无法读取输入文件：{source}（{exc}）", path=str(source)) from exc
