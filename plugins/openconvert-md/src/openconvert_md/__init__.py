"""OpenConvert 的 Markdown 导出器。

只依赖公开契约 ``openconvert.exporter_api``，不 import 核心其他模块。
"""

from .exporter import MarkdownExporter

__all__ = ["MarkdownExporter"]
__version__ = "0.1.0"
