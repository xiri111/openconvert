# -*- coding: utf-8 -*-
"""生成 DESIGN.docx 的流程图：convert 命令的关键流程（含失败分支）。"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

FONT = "Microsoft YaHei"
plt.rcParams["font.sans-serif"] = [FONT]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "images")

NAVY = "#1F4E79"
BLUE = "#2F6DA3"
TEAL = "#2E7D6F"
RED = "#B03A2E"
GREY = "#5B6672"
FILL_CORE = "#EAF1F8"
FILL_ERR = "#FBEAE8"
FILL_IO = "#F4F6F8"
FILL_OK = "#E8F3EF"


def box(ax, x, y, w, h, text, fc="white", ec=BLUE, lw=1.2, fs=8.4, bold=False,
        tc="#1B1B1B", rad=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rad}",
                                linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            zorder=3, fontweight="bold" if bold else "normal", linespacing=1.55)


def diamond(ax, cx, cy, w, h, text, fs=7.8):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, facecolor="white", edgecolor=BLUE, lw=1.2, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color="#1B1B1B", zorder=3)


def arrow(ax, p1, p2, color=BLUE, lw=1.2, label=None, lfs=7.4, loff=(0, 0), rad=0.0,
          ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=10, lw=lw,
                                 color=color, linestyle=ls, shrinkA=0, shrinkB=0, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        mx, my = (p1[0] + p2[0]) / 2 + loff[0], (p1[1] + p2[1]) / 2 + loff[1]
        ax.text(mx, my, label, fontsize=lfs, color=color, ha="center", va="center", zorder=4,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92))


def flow():
    fig, ax = plt.subplots(figsize=(7.0, 5.94), dpi=320)
    ax.set_xlim(0, 132)
    ax.set_ylim(0, 112)
    ax.axis("off")

    cx, w = 46, 62
    left = cx - w / 2

    box(ax, 10, 99, 72, 7, "openconvert convert -i 学生.csv -f markdown -o 结果.md",
        fc=FILL_IO, ec=NAVY, fs=7.6, bold=True)
    arrow(ax, (cx, 99), (cx, 96), color=NAVY)

    box(ax, left, 85, w, 11, "reader.py\n解码 → 去 BOM → 按 RFC 4180 解析引号与换行\n"
                             "列数不齐补空串 · 表头去重 · 空表头转 column_N",
        fc=FILL_CORE, fs=7.9)
    arrow(ax, (cx, 85), (cx, 82))

    box(ax, left, 73, w, 8.5, "Table（record.py）\n不变式：行长 = 列数、值全为 str、空值为 \"\"",
        fs=7.9)
    arrow(ax, (cx, 73), (cx, 70))

    box(ax, left, 57, w, 12.5, "registry.py\n内置 JSON 导出器 + entry_points 发现的第三方导出器\n"
                               "按 -f 匹配 format_name，并校验 api_version",
        fc=FILL_CORE, fs=7.9)
    arrow(ax, (cx, 57), (cx, 54.5))

    diamond(ax, cx, 50, 34, 9, "命中 -f 的导出器？")

    box(ax, 100, 46, 30, 8, "列出可用格式\n退出码 2", fc=FILL_ERR, ec=RED, fs=7.4)
    arrow(ax, (cx + 17, 50), (100, 50), color=RED, label="否", loff=(0, 1.8))

    arrow(ax, (cx, 45.5), (cx, 43), label="是", loff=(-4.5, 0))

    box(ax, left, 32, w, 11, "writer.py\n打开临时文件 结果.md.tmp（UTF-8、无 BOM）\n"
                             "目标已存在且未加 --overwrite → 退出码 2",
        fs=7.9)
    arrow(ax, (cx, 32), (cx, 29))

    box(ax, left, 17, w, 11, "exporter.export(table, out)\n只写文本流：不碰路径、不打印、不返回统计\n"
                             "格式差异全部收在这一步之后",
        fc="white", ec=TEAL, lw=1.7, fs=7.9)

    box(ax, 100, 24, 30, 9, "删临时文件（不改名）\n退出码 3 / 4", fc=FILL_ERR, ec=RED, fs=7.4)
    arrow(ax, (cx + w / 2, 22.5), (100, 26), color=RED, rad=-0.18, ls=(0, (4, 3)),
          label=None)
    ax.text(94, 15.5, "抛 ExporterError 或 OS 错误", fontsize=7.2, color=RED, ha="center",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.92))

    arrow(ax, (cx, 17), (cx, 14))
    box(ax, left, 3, w, 11, "writer.py 改名 → 结果.md\n打印摘要（条数 / 列数 / 耗时 / 大小）\n"
                             "退出码 0", fc=FILL_OK, ec=TEAL, fs=7.9, bold=False)

    fig.subplots_adjust(0, 0, 1, 1)
    path = os.path.join(OUT, "fig2-flow.png")
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    print("saved", path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    flow()
