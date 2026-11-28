"""统一记录：把「任意合法的 CSV 表头与行」规范成满足不变式的 ``Table``。

本模块只做规则，不做 IO、不打印、不告警；报道由 ``reader.py`` 负责。
"""

from collections.abc import Iterable, Sequence

from .exporter_api import Table


def normalize_columns(headers: Sequence[str], *, prefix: str = "column") -> tuple[str, ...]:
    """去空格、空表头转 ``column_N``、重名加 ``_2``/``_3`` 后缀。"""
    used: set[str] = set()
    result: list[str] = []
    for index, raw in enumerate(headers, start=1):
        name = raw.strip() if isinstance(raw, str) else ""
        base = name or f"{prefix}_{index}"
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        result.append(candidate)
    return tuple(result)


def fit_row(values: Sequence[str], width: int) -> tuple[str, ...]:
    """把一行对齐到 ``width``：缺的补空串，多的截掉。"""
    cells = list(values)
    if len(cells) < width:
        cells.extend([""] * (width - len(cells)))
    else:
        del cells[width:]
    return tuple(cells)


def make_table(
    headers: Sequence[str],
    rows: Iterable[Sequence[str]],
    *,
    source: str = "",
) -> Table:
    """按列规范化与行对齐规则组装 ``Table``；不变式由 ``Table`` 自己校验。"""
    columns = normalize_columns(headers)
    return Table(
        columns=columns,
        rows=tuple(fit_row(row, len(columns)) for row in rows),
        source=source,
    )
