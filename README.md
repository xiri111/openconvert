# OpenConvert

把 CSV 表格转换成需要的格式：一条命令转 JSON，装一个插件就能转 Markdown。核心不认识任何具体格式，扩展只依赖公开契约。

```text
openconvert convert -i 学生.csv -f json -o 结果.json
已转换：12 条记录，4 列，输出到 结果.json
```

## 状态

工程骨架搭建中（对应开发计划书里程碑 M1–M2）。已完成：仓库初始化。待完成：契约冻结、核心读取与记录、JSON 导出、CLI。

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

## 团队与分工

| 成员 | 负责 | 主要交付 |
|---|---|---|
| 成员1 | 数据怎么进来、插件怎么被找到 | 契约、读取、记录模型、插件发现 |
| 成员2 | 数据怎么写出去 | Markdown 独立扩展、插件测试与打包 |
| 成员3 | 用户看到什么、能否交付 | CLI、原子写、CI、发布 |

详见仓库外的《OpenConvert 开发计划书》。

## 许可证

Apache-2.0（含专利授权条款）。LICENSE 全文待补入仓库；第三方依赖许可声明在 README 定稿时补充。
