"""内置 JSON 导出器。

按设计文档 6.2：对象数组、键为列名、值为字符串、缩进 2 空格、
UTF-8 无 BOM、末尾换行、0 条记录输出 ``[]``。

交付位置属于成员2（分工第（二）条第 1 项）；本文件当前为占位实现，
接口与输出已按契约写死，成员2 可直接替换本文件而不动核心。
"""

import json
from typing import TextIO

from ..exporter_api import PLUGIN_API_VERSION, Table


class JsonExporter:
    api_version = PLUGIN_API_VERSION
    format_name = "json"
    display_name = "JSON"
    suffix = ".json"

    def export(self, table: Table, out: TextIO) -> None:
        records = [dict(zip(table.columns, row, strict=True)) for row in table.rows]
        out.write(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
