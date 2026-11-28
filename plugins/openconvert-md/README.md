# openconvert-md

OpenConvert 的 **Markdown 表格导出器**，以独立扩展的形式提供：只依赖公开契约 `openconvert.exporter_api`，不 import 核心其他模块，可单独构建、单独安装、可卸载。

## 安装

```bash
pip install ./plugins/openconvert-md        # 发布包上架后改成 pip install openconvert-md
openconvert formats                          # 应出现 markdown
```

## 卸载

```bash
pip uninstall -y openconvert-md
openconvert formats                          # markdown 消失，其他格式不受影响
```

## 输出规则

| 输入 | 输出 | 依据 |
|---|---|---|
| 含竖线 `a|b` | `a\|b` | 不转义会破坏列结构 |
| 含 `\r\n` 或 `\r` | 统一成 `\n` 后转 `<br>` | GFM 单元格不支持换行 |
| 空字符串 | 空单元格，保留分隔符 | 不能吞列导致错位 |
| 反引号、`<` `>` | 原样保留 | 渲染器会解释，属已知限制（见下） |
| 0 行数据 | 仍输出表头与分隔行 | 空结果也应可核对 |

分隔行固定为 `| --- | --- |`，不按内容宽度补空格——**同输入必须同字节**，否则测试无法逐字断言。

## 已知限制

- 成对的反引号在 GFM 中会被渲染成行内代码，本扩展无法转义（Markdown 本身没有反引号转义语法）。
- 含 `<` `>` 的字段会被 Markdown 渲染器当作 HTML 处理。本扩展不负责净化，导出结果仅供人工阅读。

## 开发

```bash
pip install -e ../../dev-stub/openconvert --no-deps   # 契约未就绪时的本地替身（不入库）
pip install -e . --no-deps
python -m pytest -q
```

契约由核心仓库维护；`tests/` 在 `openconvert.exporter_api` 不存在时会整体跳过，不会误报失败。
