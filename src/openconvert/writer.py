"""写盘：先写目标同目录下的临时文件，成功后改名。

为什么要绕这一圈：任何时刻失败都不留下半截文件，也不会破坏已存在的目标。
临时文件放在目标同目录，保证同一文件系统，改名才是原子操作；
跨目录或跨卷的改名可能退化成复制，失败时目标就毁了。

本模块只依赖标准库：导出器由调用方以「写回调」形式传入，
``writer`` 不需要认识 ``Table`` 或 ``Exporter``。
"""

import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

# 临时文件命名：.结果.json.8f3a1c.tmp，放在目标同目录。
_TEMP_SUFFIX = ".tmp"


class TargetExistsError(Exception):
    """目标已存在且没有 --overwrite；CLI 据此退出码 2，且不写任何字节。"""


class WriteError(Exception):
    """临时文件写入或改名失败；CLI 据此退出码 4，并保证目标保持原样。"""


def write_atomic(
    target: str | Path,
    write: Callable[[TextIO], None],
    *,
    overwrite: bool = False,
) -> int:
    """把 ``write`` 的输出写进 ``target``，返回写入字节数。

    步骤：检查目标是否存在 → 建临时文件 → 调 ``write`` → 落盘改名。
    失败时删除临时文件并抛 :class:`WriteError`，原目标不受影响。
    回调自身抛出的异常（如导出器的 ``ExporterError``）会先清理临时文件，
    再原样传播给调用方，好让 CLI 映射成对应的退出码。
    """
    destination = Path(target)

    if destination.exists() and destination.is_dir():
        raise WriteError(f"无法写入：{destination} 是一个目录")
    if destination.exists() and not overwrite:
        raise TargetExistsError(
            f"目标已存在：{destination}（加 --overwrite 才会覆盖）"
        )

    file_descriptor = -1
    temp_path: Path | None = None
    try:
        file_descriptor, temp_name = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=_TEMP_SUFFIX,
        )
        temp_path = Path(temp_name)

        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as stream:
            file_descriptor = -1
            write(stream)
            stream.flush()
            os.fsync(stream.fileno())

        size = temp_path.stat().st_size
        os.replace(temp_path, destination)
        temp_path = None

    except OSError as exc:
        raise WriteError(f"写入失败：{destination}（{exc}）") from exc

    else:
        return size

    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
