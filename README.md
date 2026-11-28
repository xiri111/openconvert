# OpenConvert

把 CSV 表格转换成需要的格式：一条命令转 JSON，装一个插件就能转 Markdown。核心不认识任何具体格式，扩展只依赖公开契约。

```text
openconvert convert -i 学生.csv -f json -o 结果.json
已转换：12 条记录，4 列，输出到 结果.json
```

## 状态

工程骨架搭建中（对应开发计划书里程碑 M1–M2）。

- 已完成：仓库初始化、Markdown 独立扩展（可直接安装验证发现链路）、系统设计文档初稿 `docs/DESIGN.docx`
- 待完成：契约冻结（`exporter_api.py`）、核心读取与记录、JSON 导出、CLI

## 目录结构（规划）

```text
openconvert/
├── docs/DESIGN.docx          # 系统设计文档（8 章 + 架构图 + 时序图）
├── src/openconvert/
│   ├── exporter_api.py       # 插件契约（唯一允许插件 import 的模块）
│   ├── reader.py  record.py  registry.py
│   ├── writer.py  summary.py cli.py
│   └── exporters/json.py     # 内置 JSON 导出器
├── plugins/openconvert-md/   # 独立扩展：Markdown 导出器（独立打包、可卸载）
├── tests/
├── samples/                  # 学生.csv、边界.csv
└── .github/workflows/ci.yml
```

## 快速开始

待骨架完成后补全（计划书 6.4 要求命令可照抄执行）。

## 核心与扩展

**核心**负责“读进来、规范化、选导出器、写出去”，不认识任何具体格式。**扩展**负责“怎么把这个表写成某种格式”，只依赖契约模块 `src/openconvert/exporter_api.py`。

| 能力 | 来源 | 是否需要安装 |
|---|---|---|
| JSON 导出 | 内置导出器（随核心发布） | 不需要 |
| Markdown 导出 | 独立扩展 `plugins/openconvert-md/` | 需要 |

### 装上与卸载

```bash
# 安装（发布包上架前用本地路径）
python -m pip install ./plugins/openconvert-md

# 看已发现的格式与来源
openconvert formats

# 卸载：格式消失，JSON 导出不受影响
python -m pip uninstall -y openconvert-md
```

格式由标准库 `entry_points(group="openconvert.exporters")` 发现：装上就出现、卸载就消失，**不需要重启配置或修改主程序**。

### 自己写一个导出器

1. 实现 `Exporter`：四个属性（`api_version`、`format_name`、`display_name`、`suffix`）和一个方法 `export(table, out)`；
2. 在 `pyproject.toml` 里声明入口点：

```toml
[project.entry-points."openconvert.exporters"]
csv2sql = "your_pkg.exporter:SqlExporter"
```

3. 打 wheel 安装：`python -m build && pip install dist/*.whl`。

约定（违反会导致行为与文档不一致）：

- **不碰文件系统**：只往 `out` 流写文本，临时文件与改名由核心的 `writer.py` 负责；
- **不做数据清洗**：列补齐、表头去重、空值归一都已在读取层完成；
- **不打印**：所有提示由 CLI 统一输出，否则 `--quiet` 会漏；
- **失败只抛 `ExporterError(code, message)`**：核心据此映射退出码并把 `message` 展示给用户。

### 核验“接入时核心源码没改”

```bash
git status --porcelain                     # 安装插件、跑完转换后应为空
grep -rin "markdown" src/ 2>/dev/null      # 核心源码里不应出现该格式名
python -c "import glob,zipfile; print([n for n in zipfile.ZipFile(glob.glob('plugins/*/dist/*.whl')[0]).namelist() if n.startswith('openconvert/')])"
# 期望输出 []：插件 wheel 里不含任何核心文件
```

## 团队与分工

| 成员 | 负责 | 主要交付 |
|---|---|---|
| 成员1 | 数据怎么进来、插件怎么被找到 | 契约、读取、记录模型、插件发现 |
| 成员2 | 数据怎么写出去 | Markdown 独立扩展、插件测试与打包 |
| 成员3 | 用户看到什么、能否交付 | CLI、原子写、CI、发布 |

详见仓库外的《OpenConvert 开发计划书》。

## 许可证

Apache-2.0（含专利授权条款）。LICENSE 全文待补入仓库；第三方依赖许可声明在 README 定稿时补充。
