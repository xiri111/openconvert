"""导出器注册与调度。

两条来源合并成一张格式表：内置 JSON 直接注册，第三方通过
``openconvert.exporters`` 入口点发现。插件坏了只跳过并告警，不影响内置格式。
"""

import importlib.metadata
import warnings
from collections.abc import Iterable
from dataclasses import dataclass

from .exporter_api import PLUGIN_API_VERSION, Exporter

ENTRY_POINT_GROUP = "openconvert.exporters"

BUILTIN_SOURCE = "内置"
THIRD_PARTY_SOURCE = "第三方"


@dataclass(frozen=True)
class FormatInfo:
    """``formats`` 命令要展示的一行：名字、显示名、来源、契约版本。"""

    name: str
    display_name: str
    source: str
    api_version: int


class UnknownFormatError(LookupError):
    """``-f`` 指定的格式没有注册；CLI 据此列出可用格式并以退出码 2 结束。"""

    def __init__(self, name: str, available: Iterable[str]) -> None:
        self.name = name
        self.available = tuple(available)
        listed = "、".join(self.available) or "无"
        super().__init__(f"未知格式 '{name}'，可用格式：{listed}")


class ExporterRegistry:
    """按格式名调度导出器。"""

    def __init__(self, *, include_builtin: bool = True) -> None:
        self._exporters: dict[str, Exporter] = {}
        self._formats: dict[str, FormatInfo] = {}
        if include_builtin:
            from .exporters.json import JsonExporter

            self.register(JsonExporter(), source=BUILTIN_SOURCE)

    def register(self, exporter: Exporter, *, source: str = THIRD_PARTY_SOURCE) -> None:
        """登记一个导出器；不符合契约或重名时抛 :class:`ValueError`。"""
        name = getattr(exporter, "format_name", "")
        if not isinstance(name, str):
            raise ValueError(f"format_name 必须是字符串，实际是 {type(name).__name__}")
        name = name.strip()
        if not name:
            raise ValueError("format_name 不能为空")
        if name != name.lower():
            raise ValueError(f"format_name 必须小写：{name!r}")
        if name in self._exporters:
            raise ValueError(f"格式名 '{name}' 已被注册")

        api_version = getattr(exporter, "api_version", None)
        if not isinstance(api_version, int) or api_version != PLUGIN_API_VERSION:
            raise ValueError(
                f"插件契约版本不匹配：需要 {PLUGIN_API_VERSION}，实际 {api_version!r}"
            )
        if not callable(getattr(exporter, "export", None)):
            raise ValueError(f"导出器 '{name}' 没有可调用的 export(table, out)")

        display_name = getattr(exporter, "display_name", "") or name
        self._exporters[name] = exporter
        self._formats[name] = FormatInfo(
            name=name,
            display_name=str(display_name),
            source=source,
            api_version=api_version,
        )

    def get(self, name: str) -> Exporter:
        try:
            return self._exporters[name]
        except KeyError as exc:
            raise UnknownFormatError(name, self.formats) from exc

    @property
    def formats(self) -> tuple[str, ...]:
        return tuple(sorted(self._exporters))

    def describe(self) -> tuple[FormatInfo, ...]:
        return tuple(self._formats[name] for name in self.formats)

    def __contains__(self, name: object) -> bool:
        return name in self._exporters

    def __len__(self) -> int:
        return len(self._exporters)


def discover(
    registry: ExporterRegistry,
    *,
    entry_points: Iterable[importlib.metadata.EntryPoint] | None = None,
) -> ExporterRegistry:
    """把已安装插件登记进 ``registry``；单个插件出错只跳过并告警。"""
    if entry_points is None:
        entry_points = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)

    for entry_point in entry_points:
        try:
            loaded = entry_point.load()
        except Exception as exc:
            warnings.warn(
                f"插件 '{entry_point.name}' 加载失败，已跳过：{exc}",
                UserWarning,
                stacklevel=2,
            )
            continue

        exporter = loaded() if isinstance(loaded, type) else loaded
        if getattr(exporter, "format_name", None) != entry_point.name:
            warnings.warn(
                f"插件 '{entry_point.name}' 的 format_name 是"
                f" {getattr(exporter, 'format_name', None)!r}，与入口点名不一致，已跳过",
                UserWarning,
                stacklevel=2,
            )
            continue

        try:
            registry.register(exporter, source=THIRD_PARTY_SOURCE)
        except ValueError as exc:
            warnings.warn(
                f"插件 '{entry_point.name}' 不符合契约，已跳过：{exc}",
                UserWarning,
                stacklevel=2,
            )

    return registry


def default_registry() -> ExporterRegistry:
    """内置导出器加全部已安装插件。"""
    return discover(ExporterRegistry())
