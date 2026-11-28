"""写盘用例：原子性、覆盖规则、失败清理、换行统一。

对应设计文档 7.3 的注入点「跳过临时文件直接写目标」：
一旦改成直接写目标，``test_回调失败时目标原样`` 与 ``test_写入失败返回退出码4``
会立刻变红——这正是集成测试要证明的那一条。
"""

from pathlib import Path

import pytest

from openconvert.writer import TargetExistsError, WriteError, write_atomic


def _no_leftover(directory: Path) -> list[Path]:
    return [path for path in directory.iterdir() if path.suffix == ".tmp"]


def test_成功写入返回字节数且无临时文件(tmp_path):
    target = tmp_path / "结果.json"
    size = write_atomic(target, lambda stream: stream.write("你好\n"))

    assert target.read_text(encoding="utf-8") == "你好\n"
    assert size == len("你好\n".encode())
    assert _no_leftover(tmp_path) == []


def test_临时文件建在目标同目录(tmp_path):
    target = tmp_path / "sub" / "结果.json"
    target.parent.mkdir()
    inspected: dict[str, Path] = {}

    def write(stream):
        temps = [path for path in target.parent.iterdir() if path.suffix == ".tmp"]
        assert len(temps) == 1
        inspected["temp"] = temps[0]
        stream.write("x")

    write_atomic(target, write)

    temp = inspected["temp"]
    assert temp.parent == target.parent
    assert temp.name.startswith(".结果.json.")
    assert temp.suffix == ".tmp"


def test_换行统一为LF而不是平台换行(tmp_path):
    target = tmp_path / "a.txt"
    write_atomic(target, lambda stream: stream.write("第一行\n第二行\n"))

    assert target.read_bytes() == "第一行\n第二行\n".encode()


def test_目标已存在且未加overwrite时拒绝且原样保留(tmp_path):
    target = tmp_path / "结果.json"
    target.write_text("原内容", encoding="utf-8")

    with pytest.raises(TargetExistsError, match="--overwrite"):
        write_atomic(target, lambda stream: stream.write("新内容"))

    assert target.read_text(encoding="utf-8") == "原内容"
    assert _no_leftover(tmp_path) == []


def test_overwrite允许覆盖(tmp_path):
    target = tmp_path / "结果.json"
    target.write_text("原内容", encoding="utf-8")

    write_atomic(target, lambda stream: stream.write("新内容"), overwrite=True)

    assert target.read_text(encoding="utf-8") == "新内容"


def test_回调失败时目标原样且无残留(tmp_path):
    target = tmp_path / "结果.json"
    target.write_text("原内容", encoding="utf-8")

    def boom(stream):
        stream.write("半截")
        raise RuntimeError("导出器中途失败")

    with pytest.raises(RuntimeError, match="导出器中途失败"):
        write_atomic(target, boom, overwrite=True)

    assert target.read_text(encoding="utf-8") == "原内容"
    assert _no_leftover(tmp_path) == []


def test_目标目录不存在时抛WriteError(tmp_path):
    target = tmp_path / "不存在的目录" / "结果.json"

    with pytest.raises(WriteError, match="写入失败"):
        write_atomic(target, lambda stream: stream.write("x"))


def test_目标是目录时抛WriteError(tmp_path):
    target = tmp_path / "目录"
    target.mkdir()

    with pytest.raises(WriteError, match="是一个目录"):
        write_atomic(target, lambda stream: stream.write("x"), overwrite=True)
