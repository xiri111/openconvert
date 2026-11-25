# OpenConvert 0.1.0 发布记录

- **版本**：0.1.0（Tag 建议 `v0.1.0`，与 `pyproject.toml`、`src/openconvert/__init__.py` 一致）
- **日期**：2026-11-26
- **Python**：3.11 及以上（CI 覆盖 3.11、3.12）

## 发布内容

| 交付物 | 说明 |
|---|---|
| `openconvert` 核心 | CSV 读取与规范化、统一 `Table`、导出器注册与发现、JSON 内置导出、命令行、原子写、摘要 |
| `openconvert-md` 独立扩展 | Markdown 表格导出器，单独打包、单独安装、可卸载，只依赖 `openconvert.exporter_api` |

本版实现的功能：

- 三个命令：`convert`、`formats`、`--version`，`--help` 可直接看清用法；
- 参数前置校验：输入不存在、格式不存在、目标已存在、输出与输入相同，一律退出码 2 且不写任何字节；
- 原子写：先写目标同目录临时文件，成功后改名；失败清理临时文件，已存在目标保持原样；
- 摘要四要素：条数、列数、耗时、文件大小；`--quiet` 只输出错误；
- 退出码 0 / 2 / 3 / 4，与 `docs/DESIGN.docx` 4.6 节一致；
- 插件装上出现、卸载消失，核心源码不变。

## 产物与校验值

可在仓库根目录重新构建（见 README “发布”一节），用下面的 SHA256 核对：

| 文件 | SHA256 |
|---|---|
| `dist/openconvert-0.1.0-py3-none-any.whl` | `93c094aad24f3d04fd2362a195638b8ac23db9d94150465b1748c825eedda372` |
| `dist/openconvert-0.1.0.tar.gz` | `3d508983a791e62a8a50eb3c3a4201d9ac3be41c6e30c5f9cbf8e5a3caa493b8` |
| `plugins/openconvert-md/dist/openconvert_md-0.1.0-py3-none-any.whl` | `527cee640451854436fe82b6225080243ed2697e78deee5ee134626a6df8db32` |
| `plugins/openconvert-md/dist/openconvert_md-0.1.0.tar.gz` | `b8d5c5a36cb5599f78a4e33f6864eda1e1d9b4d4f4bde02fc1fb90b2c355faf8` |

> 校验值随构建时间与打包工具版本变化；发布时以实际构建产物为准，更新本表。
> 构建脚本不提交 `dist/`，只提交本记录与源码。

## 发布验证（0.1.0 实测）

在全新虚拟环境中按 README 操作，逐步结果：

1. 安装核心 wheel：`openconvert --version` → `openconvert 0.1.0`；
2. `openconvert formats` → 只有 `json`（内置，契约 v1）；
3. `openconvert convert -i samples/学生.csv -f json -o 结果.json` → 退出码 0，摘要为
   `已转换：12 条记录，4 列，耗时 0.05 秒，输出到 结果.json（1.3 KB）`，文件为 12 条对象数组；
4. 安装插件 wheel：`openconvert formats` → 多出 `markdown`（第三方，契约 v1）；
5. `openconvert convert -i samples/学生.csv -f markdown -o 结果.md` → 退出码 0，14 行 GFM 表格；
6. 卸载插件：`openconvert formats` → `markdown` 消失，只剩 `json`，JSON 转换照常。

测试与检查：

- `ruff check .` 通过；
- `pytest -q` 71 条核心用例全部通过；
- 安装插件后 `pytest plugins/openconvert-md/tests -q` 13 条全部通过；
- 缺陷注入演示：删掉 `writer.py` 中清理临时文件的一行，
  `tests/test_writer.py::test_回调失败时目标原样` 与
  `tests/test_cli.py::test_写入失败退出码4且无临时文件残留` 同时变红，恢复后变绿。

## 兼容性说明

- 插件契约 `PLUGIN_API_VERSION = 1`，本版未变更；
- 0.1.0 起 `openconvert` 脚本与 `python -m openconvert` 等价；
- 后续若修改 `Table` 字段或 `export` 签名，必须升 `PLUGIN_API_VERSION` 并同步插件与
  `docs/CONTRACT.md`。

## 已知限制

- 只支持 CSV 输入；
- 整表读入内存；
- 不做类型推断，所有值为字符串；
- Markdown 成对反引号、`<` `>` 由渲染器解释；
- 插件无依赖隔离，约定插件不引入第三方依赖。
