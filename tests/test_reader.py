"""读取层用例，编号与设计文档表 10 的用例矩阵对应。"""

from pathlib import Path

import pytest

from openconvert.reader import CSVReadError, read_csv
from openconvert.record import fit_row, normalize_columns

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def test_R01_学生样例十二条四列():
    table = read_csv(SAMPLES / "学生.csv")
    assert table.columns == ("姓名", "学号", "班级", "分数")
    assert len(table.rows) == 12
    assert table.rows[0] == ("张三", "2024001", "高一(1)班", "90")
    assert all(len(row) == 4 for row in table.rows)


def test_R02_带BOM的文件首列名不含BOM(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_text("姓名,分数\n张三,90\n", encoding="utf-8-sig")
    table = read_csv(path)
    assert table.columns == ("姓名", "分数")
    assert table.rows[0] == ("张三", "90")


def test_R03_引号内的逗号与换行不拆列(tmp_path):
    path = tmp_path / "quoted.csv"
    path.write_text('姓名,备注\n张三,"北京,海淀"\n李四,"第一行\n第二行"\n', encoding="utf-8")
    table = read_csv(path)
    assert len(table.rows) == 2
    assert table.rows[0][1] == "北京,海淀"
    assert table.rows[1][1].splitlines() == ["第一行", "第二行"]


def test_R04_缺列补空串多列忽略并告警():
    with pytest.warns(UserWarning, match="超出 4 列"):
        table = read_csv(SAMPLES / "边界.csv")
    assert table.rows[3] == ("赵六", "只有一列", "", "")
    assert table.rows[4] == ("钱七", "备注", "丁", "88")
    assert len(table.rows) == 6


def test_R05_重复表头自动去重(tmp_path):
    path = tmp_path / "dup.csv"
    path.write_text("name,name,名,名\n1,2,3,4\n", encoding="utf-8")
    table = read_csv(path)
    assert table.columns == ("name", "name_2", "名", "名_2")


def test_R06_只有表头时列在行空():
    table = read_csv(SAMPLES / "空表.csv")
    assert table.columns == ("姓名", "学号", "班级", "分数")
    assert table.rows == ()


def test_空表头转column序号(tmp_path):
    path = tmp_path / "blank_header.csv"
    path.write_text("a,,c\n1,2,3\n", encoding="utf-8")
    table = read_csv(path)
    assert table.columns == ("a", "column_2", "c")


def test_跳过全空行(tmp_path):
    path = tmp_path / "blank_lines.csv"
    path.write_text("\n\n姓名,分数\n\n张三,90\n\n\n", encoding="utf-8")
    table = read_csv(path)
    assert table.columns == ("姓名", "分数")
    assert table.rows == (("张三", "90"),)


def test_空文件返回空表(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    table = read_csv(path)
    assert table.columns == ()
    assert table.rows == ()


def test_一万行不丢行不乱码(tmp_path):
    path = tmp_path / "big.csv"
    lines = ["编号,姓名,备注"]
    lines += [f"{index},学生{index},备注{index}，含中文标点。" for index in range(1, 10001)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    table = read_csv(path)
    assert len(table.rows) == 10000
    assert table.rows[-1] == ("10000", "学生10000", "备注10000，含中文标点。")


def test_值保持字符串不做类型推断(tmp_path):
    path = tmp_path / "types.csv"
    path.write_text("编号,分数,日期\n001,90.5,2024-01-02\n", encoding="utf-8")
    table = read_csv(path)
    assert table.rows[0] == ("001", "90.5", "2024-01-02")


def test_非UTF8输入报文件名与编码位置(tmp_path):
    path = tmp_path / "gbk.csv"
    path.write_bytes("姓名,分数\n张三,90\n".encode("gbk"))
    with pytest.raises(CSVReadError) as info:
        read_csv(path)
    assert str(path) in str(info.value)
    assert "utf-8" in str(info.value)


def test_文件不存在报路径(tmp_path):
    with pytest.raises(CSVReadError, match="无法读取输入文件"):
        read_csv(tmp_path / "not-exists.csv")


def test_可指定其他编码(tmp_path):
    path = tmp_path / "gbk.csv"
    path.write_bytes("姓名,分数\n张三,90\n".encode("gbk"))
    table = read_csv(path, encoding="gbk")
    assert table.columns == ("姓名", "分数")


def test_列名去空格且空表头不产生空列名():
    assert normalize_columns([" 姓名 ", "", "姓名"]) == ("姓名", "column_2", "姓名_2")


def test_行对齐补空与截断():
    assert fit_row(["a", "b"], 3) == ("a", "b", "")
    assert fit_row(["a", "b", "c", "d"], 2) == ("a", "b")
