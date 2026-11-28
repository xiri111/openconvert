"""命令行入口：三个命令、参数校验、退出码映射。

对外只有 ``main``：``openconvert`` 脚本与 ``python -m openconvert`` 都走这里。
退出码约定（见设计文档 4.6 节）：

====  ================================================
0     成功
2     参数或前置条件不满足（文件不存在、格式不存在、目标已存在）
3     读取失败或导出失败（CSV 解码错误、导出器抛 ExporterError；
      插件抛其他异常时由 registry.export 归一成 ExporterError）
4     写盘失败（临时文件写入或改名失败）
====  ================================================
"""

import argparse
import os
import sys
import time
import warnings
from pathlib import Path

from . import __version__
from .exporter_api import ExporterError
from .reader import CSVReadError, read_csv
from .registry import UnknownFormatError, default_registry
from .summary import format_formats, format_summary
from .writer import TargetExistsError, WriteError, write_atomic

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CONVERT = 3
EXIT_WRITE = 4


def build_parser() -> argparse.ArgumentParser:
    """三个命令的完整帮助文本；``--help`` 的内容就是使用说明。"""
    parser = argparse.ArgumentParser(
        prog="openconvert",
        description="把 CSV 表格转成需要的格式：主程序不认识任何具体格式，装一个插件就能加一种。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"openconvert {__version__}",
        help="显示版本号",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="{convert,formats}")

    convert = subparsers.add_parser(
        "convert",
        help="把 CSV 转换成目标格式",
        description="读取 CSV，交给对应导出器写出文件；先写临时文件，成功后才改名。",
    )
    convert.add_argument("-i", "--input", required=True, metavar="CSV", help="输入 CSV 文件")
    convert.add_argument(
        "-f",
        "--format",
        required=True,
        metavar="FORMAT",
        help="目标格式，取值见 formats 命令",
    )
    convert.add_argument("-o", "--output", required=True, metavar="PATH", help="输出文件路径")
    convert.add_argument(
        "--overwrite",
        action="store_true",
        help="目标已存在时允许覆盖（默认拒绝）",
    )
    convert.add_argument(
        "--encoding",
        default="utf-8",
        metavar="NAME",
        help="输入文件编码（默认 utf-8）",
    )
    convert.add_argument(
        "--quiet",
        action="store_true",
        help="只输出错误，不打印摘要与警告",
    )

    subparsers.add_parser(
        "formats",
        help="列出可用格式及其来源",
        description="列出内置格式与已安装插件提供的格式，以及各自遵循的契约版本。",
    )
    return parser


def _fail(code: int, message: str) -> int:
    print(f"错误：{message}", file=sys.stderr)
    return code


def _same_file(source: Path, target: Path) -> bool:
    """输出不许写回输入：Windows 下路径大小写不敏感，按 normcase 比较。"""
    try:
        left = os.path.normcase(str(source.resolve()))
        right = os.path.normcase(str(target.resolve()))
    except OSError:
        return False
    return left == right


def _convert(args: argparse.Namespace) -> int:
    source = Path(args.input)
    target = Path(args.output)
    started = time.perf_counter()

    # 校验前置：文件在不在、格式认不认识、目标能不能写，全在写任何字节之前判断。
    if not source.is_file():
        return _fail(EXIT_USAGE, f"输入文件不存在：{source}")

    registry = default_registry()
    try:
        registry.get(args.format)
    except UnknownFormatError as exc:
        return _fail(EXIT_USAGE, str(exc))

    if _same_file(source, target):
        return _fail(EXIT_USAGE, f"输出路径不能与输入文件相同：{target}")

    if target.exists() and not args.overwrite:
        return _fail(EXIT_USAGE, f"目标已存在：{target}（加 --overwrite 才会覆盖）")

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            table = read_csv(source, encoding=args.encoding)
    except CSVReadError as exc:
        return _fail(EXIT_CONVERT, str(exc))

    if not args.quiet:
        for item in caught:
            print(f"警告：{item.message}", file=sys.stderr)

    try:
        size = write_atomic(
            target,
            lambda stream: registry.export(args.format, table, stream),
            overwrite=args.overwrite,
        )
    except TargetExistsError as exc:
        return _fail(EXIT_USAGE, str(exc))
    except ExporterError as exc:
        return _fail(EXIT_CONVERT, f"导出失败：{exc.message}")
    except WriteError as exc:
        return _fail(EXIT_WRITE, str(exc))

    if not args.quiet:
        print(
            format_summary(
                rows=len(table.rows),
                columns=len(table.columns),
                elapsed=time.perf_counter() - started,
                path=str(target),
                size=size,
            )
        )
    return EXIT_OK


def _list_formats() -> int:
    print(format_formats(default_registry().describe()))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """解析参数并执行；返回退出码。"""
    args = build_parser().parse_args(argv)
    if args.command == "formats":
        return _list_formats()
    return _convert(args)


if __name__ == "__main__":
    sys.exit(main())
