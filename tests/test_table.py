"""统一记录与不变式用例：不合格的 Table 必须当场拒绝。"""

import pytest

from openconvert.exporter_api import Table
from openconvert.record import make_table


def test_合格表格可直接构造():
    table = Table(columns=("a", "b"), rows=(("1", "2"),))
    assert table.columns == ("a", "b")
    assert table.rows == (("1", "2"),)


def test_行长度与列数不等直接拒绝():
    with pytest.raises(ValueError, match="第 1 行有 1 格"):
        Table(columns=("a", "b"), rows=(("1",),))


def test_出现None直接拒绝():
    with pytest.raises(ValueError, match="不是 str"):
        Table(columns=("a",), rows=((None,),))


def test_列名重复直接拒绝():
    with pytest.raises(ValueError, match="列名存在重复"):
        Table(columns=("a", "a"), rows=())


def test_行必须是对齐后的tuple():
    with pytest.raises(ValueError, match="不是 tuple"):
        Table(columns=("a",), rows=(["1"],))


def test_空表格合法():
    table = Table(columns=(), rows=())
    assert table.rows == ()


def test_缺列与空单元格都表示成空串():
    table = make_table(["a", "b"], [["x"], ["", "y"]])
    assert table.rows == (("x", ""), ("", "y"))


def test_多余列被截掉():
    table = make_table(["a", "b"], [["x", "y", "z"]])
    assert table.rows == (("x", "y"),)
