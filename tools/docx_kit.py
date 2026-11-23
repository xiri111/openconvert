# -*- coding: utf-8 -*-
"""生成 docs/DESIGN.docx：课程资料检索平台（RAG Connector Platform）系统设计文档。

用法：
    python tools/build_design_docx.py

依赖：python-docx（样式与域代码均用 python-docx + 原始 XML 实现）。
"""
import os
import re
import sys
import json

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "unused.docx")
IMG = os.path.join(BASE, "images")

# 目录页码：由 tools/toc_pages.py 从渲染后的 PDF 反查得到，作为可选参数传入
PAGES = {}
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    with open(sys.argv[1], encoding="utf-8") as f:
        PAGES = json.load(f)

SONG = "宋体"
HEI = "黑体"
CODE = "Consolas"
LATIN = "Times New Roman"
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
GREY = RGBColor(0x59, 0x59, 0x59)

PPR_ORDER = [
    "w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
    "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd", "w:tabs",
    "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct",
    "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd", "w:snapToGrid",
    "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap",
    "w:jc", "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
]

TBLPR_ORDER = [
    "w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual", "w:tblStyleRowBandSize",
    "w:tblStyleColBandSize", "w:tblW", "w:jc", "w:tblCellSpacing", "w:tblInd",
    "w:tblBorders", "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook", "w:tblCaption",
    "w:tblDescription",
]

TCPR_ORDER = [
    "w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders", "w:shd",
    "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark",
]


def _insert_ordered(parent, child, order):
    tag = child.tag.split("}")[-1]
    tag = "w:" + tag
    idx = order.index(tag)
    for existing in parent:
        etag = "w:" + existing.tag.split("}")[-1]
        if etag in order and order.index(etag) > idx:
            existing.addprevious(child)
            return child
    parent.append(child)
    return child


def set_font(run, cn=SONG, latin=LATIN, size=12, bold=False, color=None, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    run.font.name = latin
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), latin)
    rFonts.set(qn("w:hAnsi"), latin)
    rFonts.set(qn("w:eastAsia"), cn)
    rFonts.set(qn("w:cs"), latin)


def shade(el_parent, parent_order, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    _insert_ordered(el_parent, shd, parent_order)


def para_border(p, edges=("top", "bottom", "left", "right"), sz=6, color="D0D7DE", space=4):
    pPr = p._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        _insert_ordered(pPr, pBdr, PPR_ORDER)
    for edge in edges:
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), str(space))
        el.set(qn("w:color"), color)
        pBdr.append(el)


INLINE = re.compile(r"(\*\*.+?\*\*|`.+?`)")


def rich(p, text, size=12, cn=SONG, latin=LATIN, color=None, bold_all=False):
    """支持 **加粗** 与 `行内代码` 的简易行内标记。"""
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**"):
            r = p.add_run(piece[2:-2])
            set_font(r, cn, latin, size, True, color)
        elif piece.startswith("`") and piece.endswith("`"):
            r = p.add_run(piece[1:-1])
            set_font(r, SONG, CODE, size - 1, bold_all, RGBColor(0x1B, 0x1B, 0x1B))
        else:
            r = p.add_run(piece)
            set_font(r, cn, latin, size, bold_all, color)
    return p


def body(text, size=12, indent=True, space_after=0, align=WD_ALIGN_PARAGRAPH.LEFT,
         space_before=0, keep_with_next=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.alignment = align
    pf.first_line_indent = Pt(24) if indent else Pt(0)
    pf.keep_with_next = keep_with_next
    rich(p, text, size=size)
    return p


def bullet(text, size=12, level=0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.left_indent = Cm(1.05 + 0.6 * level)
    pf.first_line_indent = Cm(-0.33)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    mark = "▪ " if level else "· "
    rich(p, mark + text, size=size)
    return p


HEADINGS = []


def h1(text, num=None):
    HEADINGS.append((1, str(num) if num else "", text))
    p = doc.add_paragraph(style="Heading 1")
    pf = p.paragraph_format
    pf.space_before = Pt(18)
    pf.space_after = Pt(10)
    pf.first_line_indent = Pt(0)
    pf.keep_with_next = True
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run((f"{num}  " if num else "") + text)
    set_font(r, HEI, "Arial", 16, True, RGBColor(0x11, 0x11, 0x11))
    return p


def h2(text, num=None):
    HEADINGS.append((2, str(num) if num else "", text))
    p = doc.add_paragraph(style="Heading 2")
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    pf.first_line_indent = Pt(0)
    pf.keep_with_next = True
    r = p.add_run((f"{num}  " if num else "") + text)
    set_font(r, HEI, "Arial", 13.5, True, RGBColor(0x1F, 0x3B, 0x57))
    return p


def h3(text, num=None):
    p = doc.add_paragraph(style="Heading 3")
    pf = p.paragraph_format
    pf.space_before = Pt(8)
    pf.space_after = Pt(4)
    pf.first_line_indent = Pt(0)
    pf.keep_with_next = True
    r = p.add_run((f"{num}  " if num else "") + text)
    set_font(r, HEI, "Arial", 12, True, RGBColor(0x1B, 0x1B, 0x1B))
    return p


def code_block(lines, size=8.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = Pt(size + 4)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    pf.left_indent = Cm(0.3)
    pf.right_indent = Cm(0.2)
    pf.first_line_indent = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # 短代码块保持整块不跨页；长清单允许跨页，避免整页留白
    pf.keep_together = len(lines) <= 14
    shade(p._p.get_or_add_pPr(), PPR_ORDER, "F6F7F9")
    para_border(p, sz=4, color="DDE2E8", space=3)
    for i, line in enumerate(lines):
        r = p.add_run(line if line else " ")
        set_font(r, SONG, CODE, size, False, RGBColor(0x1A, 0x1A, 0x1A))
        if i < len(lines) - 1:
            r.add_break()
    return p


def caption(text, kind="图"):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(4)
    pf.space_after = Pt(10)
    pf.first_line_indent = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    r = p.add_run(text)
    set_font(r, SONG, LATIN, 10, False, RGBColor(0x33, 0x33, 0x33))
    return p


def figure(path, cap, width_cm=14.4):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(8)
    pf.space_after = Pt(2)
    pf.first_line_indent = Pt(0)
    pf.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width_cm))
    caption(cap)


def _tbl_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", 14), ("left", 0), ("bottom", 14), ("right", 0),
                     ("insideH", 0), ("insideV", 0)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single" if sz else "none")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "808080" if sz else "auto")
        borders.append(el)
    _insert_ordered(tblPr, borders, TBLPR_ORDER)

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    _insert_ordered(tblPr, layout, TBLPR_ORDER)


def _cell_bottom_border(cell, sz=6):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    el = OxmlElement("w:bottom")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "808080")
    tcBorders.append(el)
    _insert_ordered(tcPr, tcBorders, TCPR_ORDER)


def _cell_margins(table):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for edge, w in (("top", 40), ("left", 90), ("bottom", 40), ("right", 90)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(w))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    _insert_ordered(tblPr, mar, TBLPR_ORDER)


def _write_cell(cell, text, size=10, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    pf = p.paragraph_format
    pf.space_before = Pt(1.5)
    pf.space_after = Pt(1.5)
    pf.first_line_indent = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.alignment = align
    rich(p, text, size=size, color=color, bold_all=bold)


def table(headers, rows, widths, cap=None, size=10, header_align=WD_ALIGN_PARAGRAPH.CENTER,
          aligns=None, keep=None):
    total_w = 15.0
    scale = total_w / sum(widths)
    widths = [w * scale for w in widths]

    if cap:
        cp = doc.add_paragraph()
        pf = cp.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.space_before = Pt(8)
        pf.space_after = Pt(4)
        pf.first_line_indent = Pt(0)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        pf.keep_with_next = True
        r = cp.add_run(cap)
        set_font(r, SONG, LATIN, 10, False, RGBColor(0x33, 0x33, 0x33))

    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _tbl_borders(t)
    _cell_margins(t)

    # 固定布局下，列宽由 tblGrid 决定，必须与单元格宽度一致
    tblPr = t._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        _insert_ordered(tblPr, tblW, TBLPR_ORDER)
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(total_w * 567)))

    grid_cols = t._tbl.tblGrid.findall(qn("w:gridCol"))
    for i, gc in enumerate(grid_cols):
        gc.set(qn("w:w"), str(int(widths[i] * 567)))

    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)

    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    trPr.append(th)

    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]
        c.width = Cm(widths[j])
        _write_cell(c, h, size=size, bold=True, align=header_align)
        _cell_bottom_border(c)

    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            c = t.rows[i].cells[j]
            c.width = Cm(widths[j])
            al = (aligns or [WD_ALIGN_PARAGRAPH.LEFT] * len(headers))[j]
            _write_cell(c, val, size=size, align=al)

    # 小表尽量整体落在同一页；大表允许跨页（表头已设为重复行）
    if keep is None:
        keep = len(rows) <= 8
    if keep:
        for row in t.rows[:-1]:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True

    tail = doc.add_paragraph()
    tail.paragraph_format.space_before = Pt(0)
    tail.paragraph_format.space_after = Pt(4)
    tail.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    tail.add_run("").font.size = Pt(4)
    return t


def add_field(paragraph, instr, placeholder=""):
    r1 = paragraph.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "begin")
    r1._r.append(fld)

    r2 = paragraph.add_run()
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    r2._r.append(instr_el)

    r3 = paragraph.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "separate")
    r3._r.append(fld)

    r4 = paragraph.add_run(placeholder)
    set_font(r4, SONG, LATIN, 10, False, RGBColor(0x40, 0x40, 0x40))

    r5 = paragraph.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "end")
    r5._r.append(fld)


def page_break():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)


def _field_char(p, kind):
    r = p.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), kind)
    r._r.append(fld)


def _field_instr(p, text):
    r = p.add_run()
    el = OxmlElement("w:instrText")
    el.set(qn("xml:space"), "preserve")
    el.text = text
    r._r.append(el)


def insert_toc(anchor, pages):
    """在 anchor 之前插入目录。

    目录是带缓存结果的 TOC 域：打开即显示完整条目与页码；若在 Word 中更新域，
    会按 TOC 1 / TOC 2 样式重新生成。页码由渲染后的 PDF 反查得到（见 tools/toc_pages.py）。
    """
    entries = [(lvl, num, title) for (lvl, num, title) in HEADINGS]
    if not entries:
        return
    created = []
    for idx, (lvl, num, title) in enumerate(entries):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(3 if lvl == 1 else 0)
        pf.space_after = Pt(0)
        pf.line_spacing = Pt(16 if lvl == 1 else 13.5)
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.left_indent = Cm(0)
        pf.first_line_indent = Cm(0 if lvl == 1 else 0.78)
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.tab_stops.add_tab_stop(Cm(15.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)

        if idx == 0:
            _field_char(p, "begin")
            _field_instr(p, r' TOC \o "1-2" \h \z \u ')
            _field_char(p, "separate")

        size = 11.5 if lvl == 1 else 11
        r = p.add_run(f"{num}  {title}" if num else title)
        set_font(r, SONG, LATIN, size, lvl == 1, RGBColor(0x1B, 0x1B, 0x1B))

        r = p.add_run()
        r.add_tab()

        page = pages.get(num, "")
        r = p.add_run(str(page) if page else "")
        set_font(r, SONG, LATIN, size, lvl == 1, RGBColor(0x1B, 0x1B, 0x1B))

        if idx == len(entries) - 1:
            _field_char(p, "end")

        created.append(p)

    for p in created:
        anchor._p.addprevious(p._p)


def setup_styles():
    st = doc.styles["Normal"]
    st.font.name = LATIN
    st.font.size = Pt(12)
    rPr = st.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), LATIN)
    rFonts.set(qn("w:hAnsi"), LATIN)
    rFonts.set(qn("w:eastAsia"), SONG)

    for name, size in (("Heading 1", 16), ("Heading 2", 13.5), ("Heading 3", 12)):
        s = doc.styles[name]
        s.font.name = "Arial"
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        rPr = s.element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            rPr.insert(0, rFonts)
        rFonts.set(qn("w:ascii"), "Arial")
        rFonts.set(qn("w:hAnsi"), "Arial")
        rFonts.set(qn("w:eastAsia"), HEI)


def setup_section():
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.0)
    sec.right_margin = Cm(3.0)
    sec.header_distance = Cm(1.5)
    sec.footer_distance = Cm(1.6)
    sec.different_first_page_header_footer = True

    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.paragraph_format.space_after = Pt(2)
    r = hp.add_run("《开源软件生态与开发技术》大作业 · 课程资料检索平台（RAG Connector Platform）· 系统设计文档")
    set_font(r, SONG, LATIN, 8.5, False, RGBColor(0x55, 0x55, 0x55))
    para_border(hp, edges=("bottom",), sz=4, color="BFBFBF", space=2)

    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("— ")
    set_font(r, SONG, LATIN, 9, False, RGBColor(0x55, 0x55, 0x55))
    add_field(fp, " PAGE ", "1")
    r = fp.add_run(" —")
    set_font(r, SONG, LATIN, 9, False, RGBColor(0x55, 0x55, 0x55))

    fp1 = sec.first_page_footer.paragraphs[0]
    fp1.alignment = WD_ALIGN_PARAGRAPH.CENTER

def init(document):
    """绑定目标文档并应用基础样式与页面设置。"""
    global doc
    doc = document
    setup_styles()
    setup_section()
    return doc
