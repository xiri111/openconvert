# OpenConvert 插件契约（v1）

一页说明，给要写插件的人看。叙述版见 `docs/DESIGN.docx` 第 4 章，两者冲突时以本文件与 `exporter_api.py` 为准。

## 一、只有五个公开名

全部位于 `src/openconvert/exporter_api.py`，**插件只允许 import 这一个模块**。

```python
PLUGIN_API_VERSION = 1

@dataclass(frozen=True)
class Table:
    columns: tuple[str, ...]           # 已去重；空表头为 column_N
    rows: tuple[tuple[str, ...], ...]  # 每行 len == len(columns)，值全 str，空为 ""
    source: str = ""                   # 仅用于提示，不参与转换

class ExporterError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message

class Exporter(Protocol):
    api_version: int      # 必须等于 PLUGIN_API_VERSION
    format_name: str      # CLI -f 的取值，小写且唯一
    display_name: str     # formats 命令里的显示名
    suffix: str           # 默认扩展名建议，如 ".md"（v1 核心未使用：`-o` 必填，
                          # 不会按格式自动补后缀；留给将来的默认文件名）
    def export(self, table: Table, out: TextIO) -> None: ...
```

读取层已经把这些脏活干完了，插件拿到 `Table` 就不要再处理：BOM 已剥离、全空行已跳过、缺列补 `""`、多余列已截断、空表头转 `column_N`、重名加 `_2`/`_3`。

## 二、四条约定

1. **不碰文件系统**：只往 `out` 写文本。临时文件、改名、`--overwrite` 由 `writer.py` 负责。
2. **不做数据清洗**：补齐、去重、空值归一都在读取层完成，插件不必懂 CSV。
3. **不打印**：所有提示由 CLI 输出，否则 `--quiet` 会漏，测试也没法断言。
4. **失败只抛 `ExporterError`**：`code` 供程序判断，`message` 原样展示给用户，只写一句人话。

## 三、发现机制

- 插件在自己的 `pyproject.toml` 里声明入口点组 `openconvert.exporters`，key 就是格式名：

  ```toml
  [project.entry-points."openconvert.exporters"]
  markdown = "openconvert_md.exporter:MarkdownExporter"
  ```

- 核心每次启动调用 `entry_points(group="openconvert.exporters")`，所以**装上就出现在 `formats`，卸载就消失**，主程序一行都不用改。
- 入口点名与 `format_name` 必须一致；不一致、`api_version` 不匹配、import 失败，都只跳过该插件并打印一行警告，不影响内置格式。
- 入口点可以指向类（核心会无参实例化），也可以指向已构造好的实例。

## 四、核心侧的两个错误类型

插件不 import 它们，写在这里是让 CLI 知道怎么映射退出码：

| 异常 | 来源 | 含义 | 退出码 |
| --- | --- | --- | --- |
| `registry.UnknownFormatError` | `registry.py` | `-f` 指定的格式没注册，带 `available` 列表 | 2 |
| `reader.CSVReadError` | `reader.py` | 文件不存在、编码不对、CSV 语法错误，带 `path`/`encoding`/`position` | 3 |
| `exporter_api.ExporterError` | 导出器 | 导出失败，展示 `message` | 3 |
| `ValueError` | `Table.__post_init__`、`register()` | 契约被违反，属编程错误 | 不面向用户 |

## 五、版本策略

| 变更 | 兼容性 | 处理 |
| --- | --- | --- |
| `Exporter` 新增带默认值的方法/属性 | 兼容 | 不升版本 |
| `Table` 新增字段 | 不兼容 | 升 `PLUGIN_API_VERSION`，同步改插件与本文 |
| 修改 `export` 签名 | 不兼容 | 升版本，并在 README 写迁移说明 |
| 核心内部重构（拆 `registry`） | 不影响插件 | 插件无需改动 |

## 六、最小可跑示例

```python
# plugins/<你的包>/src/your_pkg/exporter.py
class YourExporter:
    api_version = 1
    format_name = "yourfmt"
    display_name = "你的格式"
    suffix = ".txt"

    def export(self, table, out):
        out.write(f"{len(table.rows)} 行，{len(table.columns)} 列\n")
```

装完验证：

```bash
pip install -e .
pip install ./plugins/<你的包>
python -c "from openconvert.registry import default_registry; print(default_registry().formats)"
```

## 七、运行期失败的处理

- 插件在 `export()` 里抛 `ExporterError`：核心原样转发 `code` 与 `message`，CLI 显示一行
  `错误：导出失败：<message>`，退出码 3。
- 插件抛其他异常（`RuntimeError`、`TypeError`、`KeyError` 等，即违反第二节第 4 条）：
  核心不让 traceback 漏给用户，统一包成
  `ExporterError("PLUGIN_FAILED", "插件 '<格式名>' 执行失败：<原始消息>")`，
  用户看到的仍是一行提示、退出码 3，临时文件被清理、目标文件保持原样。
  这层兜底只保证“不吓到用户”，插件仍应自己抛 `ExporterError` 并给出准确原因。
- `KeyboardInterrupt`、`SystemExit` 属中断信号，核心不吞，照常向上抛。
