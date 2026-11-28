"""命令行集成用例（设计文档表 9 的 R06–R10 与 M02）。

每个用例都走 ``cli.main``，断言三样东西：退出码、用户看到的文字、磁盘结果。
不 mock registry、不 mock writer：坏掉的是真实链路才有意义。
"""

import importlib.metadata
import json
import sys
import tomllib
from pathlib import Path

import pytest

import openconvert
from openconvert import cli, writer

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def run(argv: list[str], capsys) -> tuple[int, str, str]:
    code = cli.main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def convert(*args: str) -> list[str]:
    """``convert`` 子命令的参数表。"""
    return ["convert", *args]


def test_正常转换输出文件与四要素摘要(tmp_path, capsys):
    target = tmp_path / "结果.json"

    code, out, _ = run(
        convert("-i", str(SAMPLES / "学生.csv"), "-f", "json", "-o", str(target)),
        capsys,
    )

    assert code == 0
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert len(payload) == 12
    assert list(payload[0]) == ["姓名", "学号", "班级", "分数"]
    assert "已转换：12 条记录，4 列，耗时" in out
    assert f"输出到 {target}" in out
    assert " KB）" in out


def test_空表正常落盘且摘要为零条(tmp_path, capsys):
    target = tmp_path / "结果.json"

    code, out, _ = run(
        convert("-i", str(SAMPLES / "空表.csv"), "-f", "json", "-o", str(target)),
        capsys,
    )

    assert code == 0
    assert target.read_text(encoding="utf-8") == "[]\n"
    assert "已转换：0 条记录，4 列" in out


def test_quiet成功时没有任何输出(tmp_path, capsys):
    target = tmp_path / "结果.json"

    code, out, err = run(
        convert(
            "-i", str(SAMPLES / "学生.csv"), "-f", "json", "-o", str(target), "--quiet"
        ),
        capsys,
    )

    assert code == 0
    assert (out, err) == ("", "")


def test_输入文件不存在退出码2并提示路径(tmp_path, capsys):
    missing = tmp_path / "没有这个.csv"
    target = tmp_path / "结果.json"

    code, _, err = run(
        convert("-i", str(missing), "-f", "json", "-o", str(target)),
        capsys,
    )

    assert code == cli.EXIT_USAGE
    assert "输入文件不存在" in err
    assert str(missing) in err
    assert not target.exists()


def test_格式不存在退出码2并列出可用格式(tmp_path, capsys):
    target = tmp_path / "结果.yaml"

    code, _, err = run(
        convert(
            "-i",
            str(SAMPLES / "学生.csv"),
            "-f",
            "yaml",
            "-o",
            str(target),
        ),
        capsys,
    )

    assert code == cli.EXIT_USAGE
    assert "未知格式 'yaml'" in err
    assert "可用格式：json" in err
    assert not target.exists()


def test_目标已存在未加overwrite时退出码2且原文件不变(tmp_path, capsys):
    target = tmp_path / "结果.json"
    target.write_text("旧内容", encoding="utf-8")

    code, _, err = run(
        convert("-i", str(SAMPLES / "学生.csv"), "-f", "json", "-o", str(target)),
        capsys,
    )

    assert code == cli.EXIT_USAGE
    assert "目标已存在" in err
    assert "--overwrite" in err
    assert target.read_text(encoding="utf-8") == "旧内容"


def test_加overwrite后覆盖成功(tmp_path, capsys):
    target = tmp_path / "结果.json"
    target.write_text("旧内容", encoding="utf-8")

    code, _, _ = run(
        convert(
            "-i",
            str(SAMPLES / "学生.csv"),
            "-f",
            "json",
            "-o",
            str(target),
            "--overwrite",
        ),
        capsys,
    )

    assert code == 0
    assert "旧内容" not in target.read_text(encoding="utf-8")


def test_输出路径与输入相同时退出码2且源文件不变(tmp_path, capsys):
    source = tmp_path / "学生.csv"
    source.write_text("姓名,分数\n张三,90\n", encoding="utf-8")
    before = source.read_bytes()

    code, _, err = run(
        convert("-i", str(source), "-f", "json", "-o", str(source)),
        capsys,
    )

    assert code == cli.EXIT_USAGE
    assert "不能与输入文件相同" in err
    assert source.read_bytes() == before


def test_写入失败退出码4且无临时文件残留(tmp_path, capsys, monkeypatch):
    target = tmp_path / "结果.json"

    def boom(*_args, **_kwargs):
        raise PermissionError(13, "目标文件被占用")

    monkeypatch.setattr(writer.os, "replace", boom)

    code, _, err = run(
        convert("-i", str(SAMPLES / "学生.csv"), "-f", "json", "-o", str(target)),
        capsys,
    )

    assert code == cli.EXIT_WRITE
    assert "写入失败" in err
    assert not target.exists()
    assert [path for path in tmp_path.iterdir() if path.suffix == ".tmp"] == []


def test_导出器失败退出码3且清理临时文件(tmp_path, capsys, markdown_plugin):
    empty = tmp_path / "空文件.csv"
    empty.write_text("", encoding="utf-8")
    target = tmp_path / "结果.md"

    code, _, err = run(
        convert("-i", str(empty), "-f", "markdown", "-o", str(target)),
        capsys,
    )

    assert code == cli.EXIT_CONVERT
    assert "导出失败：没有可导出的列" in err
    assert not target.exists()
    assert [path for path in tmp_path.iterdir() if path.suffix == ".tmp"] == []


def test_列数不齐给警告但退出码为0(tmp_path, capsys):
    target = tmp_path / "结果.json"

    code, _, err = run(
        convert("-i", str(SAMPLES / "边界.csv"), "-f", "json", "-o", str(target)),
        capsys,
    )

    assert code == 0
    assert "警告：" in err
    assert "超出 4 列" in err
    assert target.exists()


def test_quiet连警告也不输出(tmp_path, capsys):
    target = tmp_path / "结果.json"

    code, out, err = run(
        convert(
            "-i",
            str(SAMPLES / "边界.csv"),
            "-f",
            "json",
            "-o",
            str(target),
            "--quiet",
        ),
        capsys,
    )

    assert code == 0
    assert (out, err) == ("", "")


def test_可指定其他编码(tmp_path, capsys):
    source = tmp_path / "gbk.csv"
    source.write_bytes("姓名,分数\n张三,90\n".encode("gbk"))
    target = tmp_path / "结果.json"

    code, _, _ = run(
        convert(
            "-i",
            str(source),
            "-f",
            "json",
            "-o",
            str(target),
            "--encoding",
            "gbk",
        ),
        capsys,
    )

    assert code == 0
    assert json.loads(target.read_text(encoding="utf-8"))[0]["姓名"] == "张三"


def test_formats列出内置格式与来源(capsys):
    code, out, _ = run(["formats"], capsys)

    assert code == 0
    assert "可用格式（1 个）" in out
    assert "json" in out
    assert "内置" in out
    assert "v1" in out


def test_版本号与pyproject一致(capsys):
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    assert project["project"]["version"] == openconvert.__version__

    with pytest.raises(SystemExit) as info:
        cli.main(["--version"])
    assert info.value.code == 0
    assert capsys.readouterr().out.strip() == f"openconvert {openconvert.__version__}"


def test_help能看懂三个命令(capsys):
    with pytest.raises(SystemExit) as info:
        cli.main(["--help"])
    assert info.value.code == 0
    assert "convert" in capsys.readouterr().out

    with pytest.raises(SystemExit) as info:
        cli.main(["convert", "--help"])
    assert info.value.code == 0
    text = capsys.readouterr().out
    for option in ("--input", "--format", "--output", "--overwrite", "--encoding", "--quiet"):
        assert option in text


def test_少写参数退出码2并打印用法(capsys):
    with pytest.raises(SystemExit) as info:
        cli.main(["convert", "-i", "学生.csv"])

    assert info.value.code == cli.EXIT_USAGE
    assert "usage:" in capsys.readouterr().err


def test_装上插件后formats出现且能转换(markdown_plugin, tmp_path, capsys):
    code, out, _ = run(["formats"], capsys)
    assert code == 0
    assert "markdown" in out
    assert "第三方" in out

    target = tmp_path / "结果.md"
    code, _, _ = run(
        convert("-i", str(SAMPLES / "学生.csv"), "-f", "markdown", "-o", str(target)),
        capsys,
    )

    assert code == 0
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "| 姓名 | 学号 | 班级 | 分数 |"
    assert lines[1] == "| --- | --- | --- | --- |"
    assert len(lines) == 14


def _markdown_installed() -> bool:
    for entry_point in importlib.metadata.entry_points(group="openconvert.exporters"):
        if entry_point.name == "markdown":
            return True
    return False


@pytest.mark.skipif(
    _markdown_installed(), reason="本机真实安装了 markdown 插件，卸载后才能验证消失"
)
def test_卸载插件后格式消失(capsys):
    code, out, _ = run(["formats"], capsys)

    assert code == 0
    assert "markdown" not in out
    assert "json" in out


def test_模块入口可执行():
    """``python -m openconvert`` 与脚本入口等价。"""
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "openconvert", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == f"openconvert {openconvert.__version__}"
