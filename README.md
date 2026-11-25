# OpenConvert

把 CSV 表格转换成需要的格式：一条命令转 JSON，装一个插件就能转 Markdown。核心不认识任何具体格式，扩展只依赖公开契约。

```text
openconvert convert -i 学生.csv -f json -o 结果.json
已转换：12 条记录，4 列，耗时 0.01 秒，输出到 结果.json（1.3 KB）
```

## 状态

0.1.0 已可用：核心读取、内置 JSON 导出、独立 Markdown 插件、命令行与原子写全部就位，
测试与 CI 齐备。发布内容与校验值见 [docs/RELEASE.md](docs/RELEASE.md)。

## 安装

需要 Python 3.11 及以上。

```bash
git clone <仓库地址>
cd openconvert
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS / Linux：source .venv/bin/activate
python -m pip install -e ".[dev]"     # 只装运行依赖时去掉 [dev]
```

装完验证：

```bash
openconvert --version                 # openconvert 0.1.0
openconvert formats                   # 列出可用格式
```

## 用法

### 转换

```bash
openconvert convert -i 学生.csv -f json -o 结果.json
```

输出四要素固定：条数、列数、耗时、文件大小。

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-i`, `--input` | 输入 CSV 路径 | 必填 |
| `-f`, `--format` | 目标格式，取自 `formats` | 必填 |
| `-o`, `--output` | 输出文件路径 | 必填 |
| `--overwrite` | 目标已存在时允许覆盖 | 关闭 |
| `--encoding` | 输入文件编码 | `utf-8` |
| `--quiet` | 只输出错误，不打印摘要与警告 | 关闭 |

三个常见细节：

- **默认不覆盖**。目标已存在会拒绝并提示，确认要覆盖时加 `--overwrite`：
  ```bash
  openconvert convert -i 学生.csv -f json -o 结果.json --overwrite
  ```
- **不会写半截文件**。内容先写目标同目录下的临时文件，成功后改名；任何步骤失败都清理临时文件，已存在的目标保持原样。
- **不许写回源文件**。`-o` 与 `-i` 指向同一文件时直接拒绝，避免把输入覆盖掉。

### 查看可用格式

```bash
openconvert formats
```

```text
可用格式（2 个）：

  格式      显示名          来源    契约版本
  json      JSON            内置    v1
  markdown  Markdown 表格   第三方  v1
```

只装核心时只有 `json`；装上 Markdown 插件后多出 `markdown`，卸载后消失。

### 版本

```bash
openconvert --version
```

输出与发布 Tag 一致的版本号；也可以 `python -m openconvert ...`，行为相同。

## 退出码

| 退出码 | 含义 | 典型场景 |
|---|---|---|
| 0 | 成功 | 转换完成并打印摘要 |
| 2 | 参数或前置条件不满足 | 输入文件不存在、`-f` 格式不存在、目标已存在、输出与输入相同、少写参数 |
| 3 | 读取或导出失败 | CSV 解码失败、导出器抛 `ExporterError` |
| 4 | 写盘失败 | 临时文件写入或改名失败 |

错误信息全部走标准错误，一行一句人话，例如：

```text
错误：未知格式 'yaml'，可用格式：json、markdown
错误：输入文件不存在：不存在.csv
错误：目标已存在：结果.json（加 --overwrite 才会覆盖）
```

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

契约细节见 [docs/CONTRACT.md](docs/CONTRACT.md)，叙述版见 `docs/DESIGN.docx` 第 4 章。

### 核验“接入时核心源码没改”

```bash
git status --porcelain                     # 安装插件、跑完转换后应为空
grep -rin "markdown" src/ 2>/dev/null      # 核心源码里不应出现该格式名
python -c "import glob,zipfile; print([n for n in zipfile.ZipFile(glob.glob('plugins/*/dist/*.whl')[0]).namelist() if n.startswith('openconvert/')])"
# 期望输出 []：插件 wheel 里不含任何核心文件
```

## 开发与测试

```bash
python -m pytest -q        # 核心单元 + 命令行集成 + 插件测试
ruff check .               # 风格与静态检查
```

- `tests/test_reader.py`、`tests/test_table.py`、`tests/test_registry.py`：读取与契约（成员1）
- `tests/test_writer.py`、`tests/test_cli.py`：写盘与命令行（成员3）
- `plugins/openconvert-md/tests/`：插件契约测试（成员2）

插件测试在未安装插件时整体跳过，不会误报失败；`plugins/openconvert-md/` 下单独跑 `python -m pytest` 也可以。

## 发布

版本号同时出现在 `pyproject.toml`、`src/openconvert/__init__.py` 与 Git Tag 上，三者由测试保证一致（`test_版本号与pyproject一致`）。

```bash
python -m build                                   # 核心 sdist + wheel → dist/
python -m build plugins/openconvert-md --outdir plugins/openconvert-md/dist
```

发布的文件名与 SHA256 记录在 [docs/RELEASE.md](docs/RELEASE.md)；在空目录解压/安装后按本文“安装”“用法”各跑一遍即可复现。

## 已知限制

- 只支持 CSV 输入，Excel / TSV 需先另存为 CSV；
- 整表读入内存，百万行级文件占用较高；
- 不做类型推断，所有值保留为字符串（`001` 不会变成 `1`）；
- Markdown 里成对反引号会被渲染成行内代码，`<` `>` 会被当作 HTML；
- 插件无依赖隔离，约定插件不引入第三方依赖。

## 团队与分工

| 成员 | 负责 | 主要交付 |
|---|---|---|
| 成员1 | 数据怎么进来、插件怎么被找到 | 契约、读取、记录模型、插件发现 |
| 成员2 | 数据怎么写出去 | Markdown 独立扩展、插件测试与打包 |
| 成员3 | 用户看到什么、能否交付 | CLI、原子写、CI、发布 |

详见仓库外的《OpenConvert 开发计划书》。

## 许可证

MIT License，全文见 [LICENSE](LICENSE)。第三方依赖只有标准库与开发期的 pytest、ruff、build，无运行时第三方依赖。
