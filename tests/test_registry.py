"""注册表与插件发现用例。

覆盖：内置 JSON、按名调度、未知格式带可用列表、契约校验、
装上出现与卸载消失（用假入口点模拟，不依赖真实安装）。
"""

import io
import json
from pathlib import Path

import pytest

from openconvert.exporter_api import PLUGIN_API_VERSION, ExporterError, Table
from openconvert.exporters import JsonExporter
from openconvert.reader import read_csv
from openconvert.registry import (
    ExporterRegistry,
    UnknownFormatError,
    default_registry,
    discover,
)

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class FakeEntryPoint:
    """模拟 importlib.metadata.EntryPoint。"""

    def __init__(self, name, target, error=None):
        self.name = name
        self._target = target
        self._error = error

    def load(self):
        if self._error is not None:
            raise self._error
        return self._target


class MarkdownExporter:
    api_version = PLUGIN_API_VERSION
    format_name = "markdown"
    display_name = "Markdown 表格"
    suffix = ".md"

    def export(self, table, out):
        out.write("| " + " | ".join(table.columns) + " |\n")
        for row in table.rows:
            out.write("| " + " | ".join(row) + " |\n")


def render(exporter, table):
    buffer = io.StringIO()
    exporter.export(table, buffer)
    return buffer.getvalue()


def test_内置json默认已注册():
    registry = ExporterRegistry()
    assert registry.formats == ("json",)
    assert registry.describe()[0].source == "内置"
    assert registry.describe()[0].api_version == PLUGIN_API_VERSION


def test_未知格式错误带可用格式列表():
    with pytest.raises(UnknownFormatError) as info:
        ExporterRegistry().get("docx")
    assert info.value.name == "docx"
    assert info.value.available == ("json",)
    assert "可用格式：json" in str(info.value)


def test_插件可注册并按名调度():
    registry = ExporterRegistry()
    registry.register(MarkdownExporter())
    assert registry.formats == ("json", "markdown")
    assert isinstance(registry.get("markdown"), MarkdownExporter)


def test_格式名重复被拒绝():
    registry = ExporterRegistry()
    registry.register(MarkdownExporter())
    with pytest.raises(ValueError, match="已被注册"):
        registry.register(MarkdownExporter())


def test_契约版本不匹配被拒绝():
    class Old:
        api_version = PLUGIN_API_VERSION + 1
        format_name = "old"
        display_name = "旧插件"
        suffix = ".txt"

        def export(self, table, out):
            return None

    with pytest.raises(ValueError, match="契约版本不匹配"):
        ExporterRegistry().register(Old())


@pytest.mark.parametrize("name", ["", " HTML ", "PDF"])
def test_格式名必须是小写非空(name):
    class Bad:
        api_version = PLUGIN_API_VERSION
        format_name = name
        display_name = ""
        suffix = ""

        def export(self, table, out):
            return None

    with pytest.raises(ValueError, match="format_name"):
        ExporterRegistry().register(Bad())


def test_缺少export方法被拒绝():
    class NoExport:
        api_version = PLUGIN_API_VERSION
        format_name = "noop"
        display_name = ""
        suffix = ""

    with pytest.raises(ValueError, match="没有可调用的 export"):
        ExporterRegistry().register(NoExport())


def test_装上插件后出现在格式表里():
    registry = discover(
        ExporterRegistry(), entry_points=[FakeEntryPoint("markdown", MarkdownExporter)]
    )
    assert "markdown" in registry.formats
    info = next(item for item in registry.describe() if item.name == "markdown")
    assert info.source == "第三方"
    assert info.display_name == "Markdown 表格"


def test_卸载后插件消失内置不受影响():
    registry = discover(ExporterRegistry(), entry_points=[])
    assert registry.formats == ("json",)
    with pytest.raises(UnknownFormatError):
        registry.get("markdown")


def test_插件导入失败只告警不中断():
    with pytest.warns(UserWarning, match="加载失败"):
        registry = discover(
            ExporterRegistry(),
            entry_points=[FakeEntryPoint("broken", None, error=ImportError("缺依赖"))],
        )
    assert registry.formats == ("json",)


def test_插件契约版本不对只告警不中断():
    class Future:
        api_version = PLUGIN_API_VERSION + 1
        format_name = "future"
        display_name = "未来插件"
        suffix = ""

        def export(self, table, out):
            return None

    with pytest.warns(UserWarning, match="不符合契约"):
        registry = discover(
            ExporterRegistry(), entry_points=[FakeEntryPoint("future", Future)]
        )
    assert registry.formats == ("json",)


def test_入口点名与format_name不一致只告警不中断():
    with pytest.warns(UserWarning, match="不一致"):
        registry = discover(
            ExporterRegistry(), entry_points=[FakeEntryPoint("md", MarkdownExporter)]
        )
    assert registry.formats == ("json",)


def test_默认注册表等于内置加已安装插件():
    assert default_registry().formats >= ("json",)


def test_内置json输出对象数组且键顺序等于列顺序():
    table = read_csv(SAMPLES / "学生.csv")
    text = render(JsonExporter(), table)
    payload = json.loads(text)
    assert len(payload) == 12
    assert list(payload[0]) == ["姓名", "学号", "班级", "分数"]
    assert payload[0]["姓名"] == "张三"
    assert text.endswith("\n")


def test_内置json空表输出空数组():
    table = read_csv(SAMPLES / "空表.csv")
    assert render(JsonExporter(), table) == "[]\n"


def test_插件通过输出流写文本不碰文件():
    table = Table(columns=("a", "b"), rows=(("1", "2"),))
    assert render(MarkdownExporter(), table).splitlines() == ["| a | b |", "| 1 | 2 |"]


def test_插件抛ExporterError原样保留code与message():
    err = ExporterError("EMPTY_TABLE", "没有可导出的列")
    assert err.code == "EMPTY_TABLE"
    assert str(err) == "没有可导出的列"
