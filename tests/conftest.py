"""共享夹具：样例目录、命令行调用、真实 Markdown 插件的「伪安装」。

插件为什么不用 monkeypatch 直接塞 registry：那样测的只是核心自己的调度，
测不到「装上出现、卸载消失」。这里把插件源码目录放进 ``sys.path``，
再伪造一份 ``.dist-info``，走的是和 ``pip install`` 完全相同的发现路径。
"""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
MARKDOWN_PLUGIN_SRC = ROOT / "plugins" / "openconvert-md" / "src"


def _install_fake_distribution(site_packages: Path) -> None:
    """写一份只含入口点声明的最小 dist-info。"""
    dist_info = site_packages / "openconvert_md-0.1.0.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: openconvert-md\nVersion: 0.1.0\n",
        encoding="utf-8",
    )
    (dist_info / "entry_points.txt").write_text(
        "[openconvert.exporters]\n"
        "markdown = openconvert_md.exporter:MarkdownExporter\n",
        encoding="utf-8",
    )


@pytest.fixture
def markdown_plugin(tmp_path, monkeypatch):
    """模拟 ``pip install ./plugins/openconvert-md``。"""
    site_packages = tmp_path / "site-packages"
    _install_fake_distribution(site_packages)

    monkeypatch.setattr(
        sys,
        "path",
        [str(site_packages), str(MARKDOWN_PLUGIN_SRC), *sys.path],
    )
    importlib.invalidate_caches()
    try:
        yield
    finally:
        importlib.invalidate_caches()
