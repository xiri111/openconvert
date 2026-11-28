# -*- coding: utf-8 -*-
"""生成 docs/DESIGN.docx：OpenConvert 系统设计文档。

用法：
    python tools/build_design.py [toc_pages.json]

目录页码由 tools/toc_pages.py 从渲染后的 PDF 反查（与开发计划书同一套机制）。
"""
import json
import os
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import docx_kit as K

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "docs", "DESIGN.docx")
IMG = os.path.join(BASE, "docs", "images")

PAGES = {}
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    with open(sys.argv[1], encoding="utf-8") as f:
        PAGES = json.load(f)

doc = K.init(Document())

_hp = doc.sections[0].header.paragraphs[0]
if _hp.runs:
    _hp.runs[0].text = "OpenConvert（文件转换插件平台）· 系统设计文档"
    for _r in _hp.runs[1:]:
        _r.text = ""

# ----------------------------------------------------------------- 封面
for _ in range(3):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(6)
r = p.add_run("《开源软件生态与开发技术》课程大作业")
K.set_font(r, K.HEI, "Arial", 13, False, RGBColor(0x33, 0x33, 0x33))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(30)
p.paragraph_format.space_after = Pt(2)
r = p.add_run("OpenConvert")
K.set_font(r, K.HEI, "Arial", 30, True, RGBColor(0x1F, 0x4E, 0x79))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(6)
r = p.add_run("系统设计文档")
K.set_font(r, K.HEI, "Arial", 16, False, RGBColor(0x2E, 0x7D, 0x6F))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(30)
r = p.add_run("CSV → JSON / Markdown：一种扩展机制、一个独立扩展、一条可核对的转换链路")
K.set_font(r, K.SONG, K.LATIN, 10.5, False, RGBColor(0x55, 0x55, 0x55))

info = [
    ("文档版本", "v1.0（与发布版本 0.1.0 对齐）"),
    ("对应代码", "0.1.0 发布候选：核心、命令行与 Markdown 扩展全部实现并测试通过"),
    ("文档结构", "需求 → 架构 → 模块 → 扩展契约 → 流程 → 数据 → 测试 → 取舍"),
]
t = doc.add_table(rows=len(info), cols=2)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False
_tblPr = t._tbl.tblPr
_layout = OxmlElement("w:tblLayout")
_layout.set(qn("w:type"), "fixed")
K._insert_ordered(_tblPr, _layout, K.TBLPR_ORDER)
for _gc, _w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), (3.0, 11.0)):
    _gc.set(qn("w:w"), str(int(_w * 567)))
for i, (k, v) in enumerate(info):
    c0, c1 = t.rows[i].cells
    c0.width = Cm(3.0)
    c1.width = Cm(11.0)
    K._write_cell(c0, k, size=9.5, bold=True)
    K._write_cell(c1, v, size=9.5)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(60)
r = p.add_run("2026 年 11 月")
K.set_font(r, K.SONG, K.LATIN, 10.5, False, RGBColor(0x55, 0x55, 0x55))

K.page_break()

# ----------------------------------------------------------------- 目录
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(12)
r = p.add_run("目    录")
K.set_font(r, K.HEI, "Arial", 16, True, RGBColor(0x11, 0x11, 0x11))

toc_anchor = doc.add_paragraph()
toc_anchor.paragraph_format.space_before = Pt(0)
toc_anchor.paragraph_format.space_after = Pt(0)

K.page_break()

# ----------------------------------------------------------------- 1 需求
K.h1("项目概述与需求", 1)

K.h2("目标用户与要解决的问题", "1.1")
K.body("使用者是**需要把同一份表格换几种用法的人**：成绩单要交给程序读（JSON），名单要贴进文档（Markdown 表格）。"
"手工重排既慢又容易漏行，而且每换一种格式就要重做一遍。")
K.body("工具类程序很多能导出，但格式是写死的：想加一种输出就得改主程序、重新发布。"
"本项目要验证的另一件事是：**新增一种输出格式，能不能不改主程序，只装一个插件**。")

K.h2("核心场景与完成条件", "1.2")
K.body("一句话场景：**资料整理者**手里有一份 CSV，用一条命令把它转成需要的格式，并在换格式时不改主程序。")
K.body("核心场景的完成条件（缺一不可）：")
K.bullet("**输入**：一条命令，指定输入 CSV、目标格式与输出路径。")
K.bullet("**处理**：读取并规范化 CSV，交给对应导出器写出文件。")
K.bullet("**可核对的结果**：打印条数、列数、耗时与文件大小；同一输入重复执行，输出字节完全相同。")
K.bullet("**必要的错误反馈**：文件不存在、格式不存在、目标已存在、写入失败，各有明确提示与退出码。")
K.body("在此基础上，独立扩展（Markdown 导出器）增加一种新格式：装上后同一命令可产出 Markdown 表格，"
"卸载后该格式消失且 JSON 转换不受影响。", space_before=4)

K.h2("输入、输出与主要功能", "1.3")
K.table(
    ["命令", "作用", "典型输入", "输出"],
    [
        ["`convert -i <csv> -f <fmt> -o <path>`", "转换并落盘", "CSV、格式名、输出路径", "目标文件 + 摘要行"],
        ["`formats`", "列出可用格式及其来源", "无", "格式名、显示名、来源（内置/第三方）、契约版本"],
        ["`--version`", "显示版本号", "无", "与 Tag 一致的版本号"],
    ],
    widths=[5.6, 3.0, 3.6, 4.8],
    cap="表1  命令与输入输出",
    size=9.0,
)

K.h2("范围边界", "1.4")
K.body("**本次实现**：CSV 输入（UTF-8 与 BOM，可选 `--encoding`）、统一 `Table` 记录、JSON 内置导出、"
"Markdown 独立扩展、插件发现与卸载、原子写与退出码、样例与文档。")
K.body("**本次不做**：")
K.bullet("不做类型推断——所有值保留为字符串，`001` 不会变成 `1`，日期不做格式化。")
K.bullet("不做 Excel / TSV / HTML 输入——只认 CSV，避免范围膨胀。")
K.bullet("不做列宽对齐、合并单元格、样式美化——输出只保证可解析与可读。")
K.bullet("不做在线服务与 GUI——只有命令行，无 HTTP、无数据库、无账号。")
K.bullet("不做流式处理——整表读入内存，大文件属已知限制（见 8.5）。")

# ----------------------------------------------------------------- 2 架构
K.h1("总体架构", 2)

K.h2("分层与依赖方向", "2.1")
K.body("架构的核心约束只有一条：**主程序不认识任何具体格式**。因此格式相关代码只出现在两处——"
"内置 JSON 导出器与独立插件，两者都只依赖契约模块 `exporter_api.py`。")
K.bullet("**依赖方向**：`registry` 依赖契约取导出器；`plugins` 依赖契约实现导出器；`plugins` 不依赖核心其他模块。")
K.bullet("**无格式知识**：核心代码里 grep 不到 `markdown` 字样，这是可机器验证的结论。")
K.bullet("**装配外置**：装哪个插件由 `pip install` 决定，核心不需要配置清单。")

K.h2("总体架构图", "2.2")
K.figure(os.path.join(IMG, "fig1-arch.png"), "图1  模块划分、依赖方向与写入链路", width_cm=14.6)
K.body("自上而下依次是入口层、核心层、契约层、实现层与资源层。三处箭头分别表示：核心使用契约、"
"导出器实现契约、配置在启动时被读取。写入链路的末端是“临时文件 → 改名”，因此任何失败都不会留下半截文件。")

K.h2("模块划分", "2.3")
K.table(
    ["模块", "职责", "允许依赖"],
    [
        ["`exporter_api.py`", "契约：`Exporter`、`Table`、`ExporterError`、`PLUGIN_API_VERSION`", "仅标准库"],
        ["`reader.py`", "CSV 读取与规范化：编码、BOM、引号、空行、列数不齐、表头去重", "`record`"],
        ["`record.py`", "`Table` 数据类与不变式校验", "仅标准库"],
        ["`registry.py`", "内置导出器注册、`entry_points` 发现、版本校验、按格式名取用", "`exporter_api`"],
        ["`exporters/json.py`", "内置 JSON 导出器（基础能力）", "`exporter_api`"],
        ["`writer.py`", "临时文件写入、成功后改名、`--overwrite`、失败清理", "仅标准库"],
        ["`summary.py`", "统计与摘要输出、`--quiet`", "仅标准库"],
        ["`cli.py`", "子命令、参数校验、退出码映射", "以上全部"],
        ["`plugins/openconvert-md/`", "独立扩展：Markdown 导出器（独立发行包）", "`exporter_api`"],
    ],
    widths=[4.4, 8.4, 3.2],
    cap="表2  模块职责与依赖约束",
    size=9.0,
)

K.h2("技术选型", "2.4")
K.table(
    ["关注点", "选择", "理由与代价"],
    [
        ["语言", "Python 3.11", "标准库 `csv` 已实现 RFC 4180 的引号与换行规则；`dataclass` 适合表达契约"],
        ["命令解析", "`argparse`", "三个子命令足够，不引入第三方 CLI 框架"],
        ["插件发现", "`importlib.metadata.entry_points`", "标准机制；装上出现、卸载消失本身就是发现机制的证据"],
        ["测试", "pytest", "参数化与 `tmp_path` 便于构造文件级边界"],
        ["基础检查", "ruff", "一个工具覆盖风格与静态检查，一行配置"],
        ["打包", "setuptools + build", "插件独立产出 wheel，可单独分发"],
    ],
    widths=[2.6, 4.4, 9.0],
    cap="表3  技术选型与取舍",
    size=9.0,
)

# ----------------------------------------------------------------- 3 模块设计
K.h1("模块设计", 3)

K.h2("读取与规范化（reader.py）", "3.1")
K.body("读取层负责把“任意合法的 CSV”变成“满足不变式的 `Table`”，它承担所有脏活：")
K.bullet("**解码**：默认 UTF-8（含 BOM 自动去除）；`--encoding` 可指定其他编码；解码失败报具体文件名与位置。")
K.bullet("**解析**：直接用标准库 `csv.reader`，引号内逗号、引号内换行、`\"\"` 转义由它处理。")
K.bullet("**规范化**：跳过全空行；列数少于表头时补 `\"\"`；多于表头时忽略多余列并记一条警告。")
K.bullet("**表头**：空表头转 `column_N`；重复表头加 `_2`、`_3` 后缀，保证唯一。")
K.body("读取层不判断内容含义：数字、日期、编号一律当字符串，这是 8.1 节的设计取舍。", space_before=4)

K.h2("统一记录（record.py）", "3.2")
K.body("`Table` 是整个系统唯一的数据结构，它的不变式是后续所有模块的契约前提（见 6.1）。"
"构造时校验，不满足直接抛 `ValueError`——保证来自数据结构本身，而不是调用方自觉。")

K.h2("导出器注册与调度（registry.py）", "3.3")
K.body("两条来源合并成一张格式表：**内置 JSON 导出器**直接注册，**第三方导出器**通过 `entry_points` 发现。"
"取用前校验 `api_version`，不一致时跳过并警告，不影响其他格式；`-f` 未命中时抛出携带“可用格式列表”的错误，"
"由 CLI 转成提示与退出码 2。")

K.h2("写盘（writer.py）", "3.4")
K.body("写入遵循“先写临时文件、成功后改名”：")
K.bullet("临时文件建在目标同目录下（保证同一文件系统，改名是原子操作），命名为 `<目标名>.<随机后缀>.tmp`。")
K.bullet("目标已存在且未加 `--overwrite` 时，**在写任何内容之前**返回退出码 2。")
K.bullet("导出器抛出异常时删除临时文件，目标文件保持原样。")
K.bullet("写入与改名统一以 UTF-8、`\\n` 换行，保证同输入同字节。")

K.h2("摘要与命令行（summary.py / cli.py）", "3.5")
K.body("摘要固定四要素：条数、列数、耗时、文件大小；`--quiet` 下只输出错误。"
"CLI 负责参数校验、把 `ExporterError` 与 IO 错误分别映射到退出码 3 / 4，并在 `--version` 输出与 Tag 一致的版本号。")

K.h2("内置 JSON 导出器（exporters/json.py）", "3.6")
K.body("作为基础能力随核心发布，输出为对象数组，键为列名、值为字符串（见 6.2）。"
"它同样实现 `Exporter` 契约，与第三方导出器走同一条调用路径——这样“基础能力”和“扩展”在使用上没有差别，"
"唯一区别是它不需要安装。")

# ----------------------------------------------------------------- 4 扩展机制
K.h1("扩展机制与接口设计", 4)

K.h2("契约内容", "4.1")
K.body("契约模块只有 5 个公开名，全部位于 `exporter_api.py`（清单 1）。插件只允许 import 这一个模块。")
K.code_block([
    "# src/openconvert/exporter_api.py",
    "from dataclasses import dataclass",
    "from typing import Protocol, TextIO",
    "",
    "PLUGIN_API_VERSION = 1",
    "",
    "@dataclass(frozen=True)",
    "class Table:",
    "    columns: tuple[str, ...]           # 已去重；空表头为 column_N",
    "    rows: tuple[tuple[str, ...], ...]  # 每行 len == len(columns)，值全 str，空为 \"\"",
    "    source: str = \"\"",
    "",
    "    def __post_init__(self) -> None:",
    "        \"\"\"校验不变式，不满足抛 ValueError。\"\"\"",
    "",
    "class ExporterError(Exception):",
    "    def __init__(self, code: str, message: str) -> None:",
    "        super().__init__(message)",
    "        self.code, self.message = code, message",
    "",
    "class Exporter(Protocol):",
    "    api_version: int      # 必须等于 PLUGIN_API_VERSION",
    "    format_name: str      # CLI -f 的取值，小写且唯一",
    "    display_name: str     # formats 命令里的显示名",
    "    suffix: str           # 默认扩展名建议，如 \".md\"",
    "    def export(self, table: Table, out: TextIO) -> None: ...",
])
K.body("四个字段的语义与来源约定：`columns` 已去重并规范化；`rows` 保证等长；值全部为 `str`；"
"`source` 仅用于提示，不参与转换。导出器拿到的是**已打开的输出流**，而不是路径。")

K.h2("四条约定", "4.2")
K.bullet("**导出器不碰文件系统**：只往 `out` 流写文本。临时文件、改名、`--overwrite` 由 `writer.py` 统一负责。")
K.bullet("**导出器不做数据清洗**：列补齐、表头去重、空值归一都在读取层完成，插件因此不需要懂 CSV。")
K.bullet("**导出器不打印**：所有提示由 CLI 输出，否则 `--quiet` 会漏、测试也无法断言。")
K.bullet("**失败只抛 ExporterError**：核心据此映射退出码 3，并把 `message` 原样展示给用户。")

K.h2("发现机制", "4.3")
K.body("发现完全依赖标准库，没有注册表文件、没有中心化配置：")
K.bullet("插件在自己的 `pyproject.toml` 里声明入口点组 `openconvert.exporters`，key 为格式名。")
K.bullet("核心启动时调用 `entry_points(group=\"openconvert.exporters\")`，插件包一装上就会出现在结果里。")
K.bullet("加载失败（导入错误、`api_version` 不匹配）时跳过该插件并打印一行警告，不影响内置格式。")
K.bullet("`formats` 命令列出格式名、显示名、来源（内置/第三方）与契约版本，来源信息取自入口点元数据。")

K.h2("版本与兼容策略", "4.4")
K.table(
    ["变更", "示例", "是否兼容", "处理"],
    [
        ["新增 `default` 方法", "`Exporter` 加 `default int priority()`", "兼容", "不升版本"],
        ["新增异常子类", "`ConnectorTimeoutError`", "兼容", "核心按父类捕获"],
        ["`Table` 新增字段", "加 `metadata`", "不兼容", "升 `PLUGIN_API_VERSION`，同步改插件与文档"],
        ["修改 `export` 签名", "改为返回统计对象", "不兼容", "升版本，并在 README 写迁移说明"],
        ["核心内部重构", "拆分 `registry`", "不影响插件", "插件无需改动"],
    ],
    widths=[3.8, 5.6, 2.2, 5.4],
    cap="表4  契约变更与兼容策略",
    size=9.0,
    aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.LEFT],
)

K.h2("独立扩展接入示例", "4.5")
K.body("以本项目的 Markdown 导出器为例，接入共六步，全程不修改核心源码：")
K.code_block([
    "# 1. 建目录（与主程序并列，不混在一起）",
    "plugins/openconvert-md/{pyproject.toml, src/openconvert_md/, tests/}",
    "",
    "# 2. 实现 Exporter：四个属性 + export(table, out)",
    "# 3. 声明入口点",
    "[project.entry-points.\"openconvert.exporters\"]",
    "markdown = \"openconvert_md.exporter:MarkdownExporter\"",
    "",
    "# 4. 独立打包",
    "cd plugins/openconvert-md && python -m build",
    "",
    "# 5. 安装（等价于把 jar 放进 plugins 目录）",
    "python -m pip install dist/openconvert_md-0.1.0-*.whl",
    "",
    "# 6. 验证",
    "openconvert formats          # 出现 markdown",
    "openconvert convert -i 学生.csv -f markdown -o 结果.md",
])
K.body("核验“核心未改”有三条命令：`git status --porcelain` 为空；插件 wheel 里只有 `openconvert_md/`；"
"`grep -rin \"markdown\" src/` 无输出。", space_before=4)

K.h2("错误与退出码", "4.6")
K.table(
    ["场景", "触发方", "系统行为", "退出码"],
    [
        ["输入文件不存在", "CLI 参数校验", "提示路径并退出", "2"],
        ["`-f` 格式不存在", "`registry`", "列出可用格式后退出", "2"],
        ["目标已存在且未加 `--overwrite`", "`writer`", "不写任何内容直接退出", "2"],
        ["CSV 解码失败", "`reader`", "提示文件名与编码", "3"],
        ["导出器抛 `ExporterError`", "导出器", "删临时文件，展示 `message`", "3"],
        ["临时文件写入或改名失败", "`writer`", "删临时文件，目标保持原样", "4"],
        ["成功", "—", "打印摘要", "0"],
    ],
    widths=[4.6, 3.4, 6.2, 1.8],
    cap="表5  错误场景、系统行为与退出码",
    size=9.0,
    aligns=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER],
)

# ----------------------------------------------------------------- 5 流程
K.h1("关键业务流程", 5)

K.h2("convert 主流程", "5.1")
K.body("一条命令从 CSV 走到目标文件，中间经过读取、规范化、选导出器、写临时文件、改名五步（图 2）。"
"流程图两侧是两条失败分支，分别对应“格式不存在”与“转换或写入失败”。")
K.figure(os.path.join(IMG, "fig2-flow.png"), "图2  convert 命令的关键流程（含失败分支）", width_cm=14.0)
K.body("设计上有两个关键点：")
K.bullet("**校验前置**：目标是否存在、格式是否存在都在写任何字节之前判断，避免“写到一半才发现不行”。")
K.bullet("**失败可回滚**：内容先落到临时文件，只有全部成功才改名，因此任何异常都不会破坏已存在的目标文件。")

K.h2("失败分支", "5.2")
K.table(
    ["失败点", "系统行为", "用户看到", "可核对的证据"],
    [
        ["格式未命中", "不创建任何文件", "未知格式：md（可用：json, markdown）", "退出码 2，目录无新文件"],
        ["CSV 解析失败", "不创建临时文件", "第 7 行列数与表头不一致", "退出码 3"],
        ["导出中途抛错", "删除临时文件", "导出失败：<message>", "退出码 3，目录无 `.tmp` 残留"],
        ["改名失败", "删除临时文件，目标不变", "写入失败：目标文件被占用", "退出码 4，目标 mtime 不变"],
        ["成功但 0 条记录", "正常落盘空结果", "已转换：0 条记录，2 列", "退出码 0，JSON 为 `[]`"],
    ],
    widths=[3.2, 4.4, 5.6, 4.4],
    cap="表6  失败分支与可核对证据",
    size=9.0,
)

# ----------------------------------------------------------------- 6 数据与配置
K.h1("数据与配置", 6)

K.h2("Table 的不变式与空值语义", "6.1")
K.body("`Table` 是模块之间唯一的数据结构，四条不变式在构造时校验：")
K.bullet("`len(row) == len(columns)` 恒成立——少一格 Markdown 表格就会塌。")
K.bullet("所有值都是 `str`，任何位置不出现 `None`——`None` 会被写成 `None` 文本。")
K.bullet("空单元格与缺失列都表示为 `\"\"`，二者不做区分——导出器只需要不会错位。")
K.bullet("`columns` 已去重、空表头已规范化——导出器不再处理表头规则。")

K.h2("JSON 输出结构", "6.2")
K.body("内置 JSON 导出器输出对象数组，键为列名、值为字符串，缩进 2 空格、UTF-8 无 BOM、末尾换行：")
K.code_block([
    "[",
    "  {\"姓名\": \"张三\", \"分数\": \"90\"},",
    "  {\"姓名\": \"李四\", \"分数\": \"85\"}",
    "]",
])
K.body("键顺序与列顺序一致；0 条记录输出 `[]`。不做类型转换，是 8.1 节的取舍。")

K.h2("Markdown 输出规则", "6.3")
K.table(
    ["输入", "输出", "依据"],
    [
        ["含竖线 `a|b`", "`a\\|b`", "不转义会破坏列结构"],
        ["含 `\\r\\n` 或 `\\r`", "归一为 `\\n` 后转 `<br>`", "GFM 单元格不支持换行"],
        ["空字符串", "空单元格，保留分隔符", "不能吞列导致错位"],
        ["反引号、`<` `>`", "原样保留", "渲染器会解释，属已知限制"],
        ["0 行数据", "只输出表头与分隔行", "空结果也应可核对"],
    ],
    widths=[4.4, 6.8, 4.8],
    cap="表7  Markdown 导出规则",
    size=9.0,
)

K.h2("命令行参数", "6.4")
K.table(
    ["参数", "含义", "默认值"],
    [
        ["`-i, --input`", "输入 CSV 路径", "必填"],
        ["`-f, --format`", "目标格式（取自 `formats`）", "必填"],
        ["`-o, --output`", "输出文件路径", "必填"],
        ["`--overwrite`", "目标已存在时允许覆盖", "关闭"],
        ["`--encoding`", "输入文件编码", "`utf-8`"],
        ["`--quiet`", "只输出错误", "关闭"],
    ],
    widths=[3.6, 8.4, 3.0],
    cap="表8  命令行参数",
    size=9.0,
)

# ----------------------------------------------------------------- 7 测试
K.h1("测试与质量方案", 7)

K.h2("测试分层与夹具", "7.1")
K.body("测试分三层，各自回答一个问题：契约成立吗（单元）、整条命令成立吗（集成）、失败时说得清吗（失败路径）。"
"核心共 76 条：读取与契约 48 条（`tests/test_reader.py` 16 条、`tests/test_table.py` 8 条、"
"`tests/test_registry.py` 24 条），写盘 8 条（`tests/test_writer.py`），命令行集成 20 条（`tests/test_cli.py`）。"
"插件另有 13 条契约测试（`plugins/openconvert-md/tests/`），未安装插件时整体跳过、不误报失败。")
K.body("夹具统一放在 `samples/`：`学生.csv`（正常，12 行 4 列）、`边界.csv`（引号内逗号、引号内换行、"
"空单元格、列数不齐）、`空表.csv`（只有表头）。`tests/conftest.py` 另有一个 `markdown_plugin` 夹具："
"把插件源码目录放进 `sys.path` 并伪造 `.dist-info`，走 `pip install` 同一套 entry points 发现路径。"
"因此“装上出现、卸载消失”是真实链路验证，而不是往注册表里塞一个假导出器。")

K.h2("用例矩阵", "7.2")
K.table(
    ["编号", "类型", "输入与操作", "断言要点"],
    [
        ["R01", "正常", "`学生.csv` → JSON", "12 条记录、4 列；键顺序与列一致；摘要四要素齐全"],
        ["R02", "边界", "含 BOM 的 CSV", "首列名不含 BOM 字符"],
        ["R03", "边界", "引号内逗号与换行", "字段内容完整，不拆行"],
        ["R04", "边界", "列数不齐", "缺列补空串；多列被忽略并告警，退出码 0"],
        ["R05", "边界", "重复表头", "列名去重为 `name`、`name_2`"],
        ["R06", "边界", "只有表头", "输出 `[]`，退出码 0"],
        ["R07", "失败", "文件不存在", "退出码 2，提示路径，不创建输出文件"],
        ["R08", "失败", "格式不存在", "退出码 2，列出可用格式"],
        ["R09", "失败", "目标已存在且未加 `--overwrite`", "退出码 2，目标内容与时间戳不变"],
        ["R10", "失败", "写入中途失败", "退出码 4，目录无 `.tmp` 残留"],
        ["R11", "失败", "`-o` 与 `-i` 指向同一文件", "退出码 2，源文件字节不变"],
        ["R12", "失败", "导出器抛 `ExporterError`", "退出码 3，展示 message，无 `.tmp` 残留"],
        ["R13", "行为", "`--quiet`", "成功时标准输出与标准错误都为空；失败仍输出错误"],
        ["M01", "扩展", "Markdown 插件契约测试", "13 条，逐字断言输出字符串"],
        ["M02", "扩展", "装上插件后 `formats` 与转换", "出现 `markdown`、来源为第三方，表格逐行匹配"],
        ["M03", "扩展", "卸载插件后", "`markdown` 消失，JSON 转换照常"],
    ],
    widths=[1.4, 1.6, 6.4, 6.6],
    cap="表9  测试用例矩阵",
    size=9.0,
    aligns=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT],
)

K.h2("缺陷注入", "7.3")
K.body("每个成员准备一个可现场演示的注入点，用来证明测试真的能发现错误：")
K.bullet("**写盘**：把 `write_atomic` 改成直接写目标 → `tests/test_writer.py::test_回调失败时目标原样` 与 "
"`tests/test_cli.py::test_写入失败退出码4且无临时文件残留` 同时变红，恢复后变绿。")
K.bullet("**读取层**：把列补齐逻辑改成截断 → R04 变红（行长度与列数不等，`Table` 直接抛 `ValueError`）。")
K.bullet("**导出器**：删掉 `_cell()` 里的竖线转义 → M01 的转义用例立刻变红，恢复后变绿。")
K.bullet("**退出码**：把 `ExporterError` 的映射改成返回 0 → `test_导出器失败退出码3且清理临时文件` 变红。")

K.h2("CI 与发布", "7.4")
K.body("CI 与本地命令完全一致：`pip install -e \".[dev]\"` → `ruff check .` → `pytest -q`，本地过即 CI 过。"
"其后逐步验证扩展链路：`python -m build plugins/openconvert-md` 产出独立 wheel → 安装 → `formats` 出现 "
"`markdown` → 真实转换一次 → 跑插件测试 → 卸载 → `formats` 里消失且 JSON 转换照常。")
K.body("发布流程按版本号串起来：版本同时写在 `pyproject.toml`、`src/openconvert/__init__.py` 与 Git Tag 上，"
"由 `test_版本号与pyproject一致` 防止漂移。发布物为核心 sdist/wheel 与插件 wheel，文件名与 SHA256 记入 "
"`docs/RELEASE.md`；在空目录安装后按 README 的“安装”“用法”各跑一遍，能复现同样的摘要与输出字节，"
"才算交付完成。")

# ----------------------------------------------------------------- 8 取舍
K.h1("设计取舍与局限", 8)

K.h2("不做类型推断", "8.1")
K.body("**选择**：所有值保留为字符串，不做数字/日期/布尔推断。")
K.body("**理由**：推断会破坏数据本身——学号 `001` 变成 `1`、编号 `2024001` 变成浮点、日期格式被改写，"
"都是不可逆的信息损失。转换工具的职责是“换个容器”，不是“解释内容”。")
K.body("**代价**：消费方需要自己转换类型；**缓解**：在 JSON 里保留原始字符串，需要类型的下游自行处理。")

K.h2("整表读入内存", "8.2")
K.body("**选择**：读取时把整个 CSV 读进 `Table`，不做流式处理。")
K.body("**理由**：Markdown 表格需要先知道列数、JSON 数组需要一次性输出，流式并不能省掉这些约束；"
"而整表读入让“列数不齐归一”这类跨行校验变得简单可靠。")
K.body("**代价**：超大文件会占用较多内存。**缓解**：样例规模在万行量级，实测足够；大文件列为已知限制。")

K.h2("entry_points 而非自研类加载", "8.3")
K.body("**选择**：插件发现用标准库 `entry_points`，不做独立类加载或版本隔离。")
K.body("**理由**：标准机制能直接做到“装上出现、卸载消失”，而这正是本项目要证明的结论；自研加载器会增加"
"实现与解释成本，且对本项目（插件零第三方依赖）没有实际收益。")
K.body("**代价**：插件若携带冲突依赖会影响主程序。**缓解**：约定插件不得引入第三方依赖，并在 CI 中检查。")

K.h2("输出不追求美观", "8.4")
K.body("**选择**：不实现列宽对齐、不补空格、不做花哨排版。")
K.body("**理由**：Markdown 表格的对齐是渲染器的事；导出结果必须**同输入同字节**，否则测试无法逐字断言，"
"版本对比也会因为空格变化产生噪声。")

K.h2("已知局限与后续计划", "8.5")
K.table(
    ["局限", "影响", "计划"],
    [
        ["只支持 CSV 输入", "Excel、TSV 需先另存为 CSV", "不解决（范围外）"],
        ["整表读入内存", "百万行级文件占用高", "后续可加分块与临时落盘"],
        ["不做类型推断", "消费方需自行转换", "不解决（有意为之）"],
        ["反引号在 Markdown 中会被解释", "成对反引号渲染为行内代码", "写入 README 已知限制"],
        ["插件无依赖隔离", "冲突依赖需人工排查", "以“插件零第三方依赖”约定规避"],
    ],
    widths=[4.6, 6.4, 5.0],
    cap="表10  已知局限与处理态度",
    size=9.0,
)

# ----------------------------------------------------------------- 附录
K.h1("文档维护", "附录")
K.body("本文档在开发前形成初稿，随接口与实现变化同步修订；提交前与代码、README 逐项核对。"
"未实现的部分明确标注为计划，不写成已完成。")
K.table(
    ["版本", "日期", "修订内容"],
    [
        ["v0.1", "2026-11-23", "初稿：需求、架构、模块、契约、流程、数据、测试、取舍八章；Markdown 扩展已实现，核心读取与 CLI 待实现"],
        ["v0.2", "2026-11-26", "按实现补齐 reader / writer / registry 细节与测试期望值"],
        ["v1.0", "2026-11-26", "与 0.1.0 发布对齐：补测试与发布章、命令行退出码、插件装上/卸载验证与发布校验值"],
    ],
    widths=[1.6, 2.6, 10.8],
    cap="表11  文档修订记录",
    size=9.0,
    aligns=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT],
)

K.insert_toc(toc_anchor, PAGES)
toc_anchor._p.getparent().remove(toc_anchor._p)

with open(os.path.join(BASE, "tools", "_headings.json"), "w", encoding="utf-8") as f:
    json.dump([{"level": l, "num": n, "title": t} for l, n, t in K.HEADINGS], f,
              ensure_ascii=False, indent=1)

doc.save(OUT)
print("saved", OUT, "| headings:", len(K.HEADINGS))
