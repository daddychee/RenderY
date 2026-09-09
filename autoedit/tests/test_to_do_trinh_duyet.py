r"""Miếng dùng clip hỏng phải TÔ ĐỎ THẬT — kiểm bằng Chrome, không kiểm chuỗi.

User nghiệm thu 09/09: *"CÓ báo 1 khối đang lỗi nhưng không có các viền đỏ, clip
hỏng"*. Server đúng (409 + đúng miếng + tên clip, đã gọi thật trên production),
lỗi nằm ở CSS.

NGUYÊN NHÂN: `index.html` đặt `.of-mieng.hong` TRƯỚC `.of-mieng.tho`. Hai luật
cùng độ ưu tiên (0,2,0) nên luật SAU thắng — `border-color` của `.tho` (miếng
nằm trong khoảng thở) đè lên màu đỏ của `.hong`. Miếng nào trong khoảng thở là
mất viền đỏ, mà đó lại là phần lớn miếng.

VÌ SAO TEST CŨ KHÔNG BẮT: `test_UI_co_ham_to_do_mieng_hong` chỉ kiểm
`".of-mieng.hong" in h` — có chuỗi trong file là xanh, bất kể CSS có ăn hay
không. Đúng loại "test báo xanh vô nghĩa" đã tự phê ở việc `of-noi-xuat`.

CÁCH LÀM ĐÚNG (BH9 + user chốt 09/09): dựng trang thật bằng CSS TRÍCH NGUYÊN VĂN
từ `index.html`, mở bằng Chrome thật, ĐỌC MÀU ĐÃ TÍNH (`getComputedStyle`).
Trích chứ không chép tay: chép tay là test một bản CSS khác với bản đang chạy.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

INDEX = Path("autoedit/web/static/index.html")


def _css() -> str:
    """Toàn bộ <style> của index.html — lấy nguyên văn, giữ đúng THỨ TỰ luật.

    Thứ tự là thứ đang test: đảo hai luật là đổi kết quả.
    """
    h = INDEX.read_text(encoding="utf-8")
    return "\n".join(re.findall(r"<style>(.*?)</style>", h, re.S))


TRANG = """<!doctype html><meta charset="utf-8"><style>__CSS__</style>
<div id="of-dai" style="position:relative;height:60px;width:900px">
  <div class="of-mieng" id="m0" style="left:0;width:120px"></div>
  <div class="of-mieng tho" id="m1" style="left:130px;width:120px"></div>
  <div class="of-mieng hong" id="m2" style="left:260px;width:120px"></div>
  <div class="of-mieng tho hong" id="m3" style="left:390px;width:120px"></div>
  <div class="of-mieng chon hong" id="m4" style="left:520px;width:120px"></div>
</div>"""


@pytest.fixture(scope="module")
def chrome():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception as exc:  # noqa: BLE001 — máy không có Chrome thì bỏ qua
            pytest.skip(f"không mở được Chrome: {str(exc)[:80]}")
        yield b
        b.close()


@pytest.fixture
def trang(chrome, tmp_path):
    (tmp_path / "t.html").write_text(TRANG.replace("__CSS__", _css()), encoding="utf-8")
    pg = chrome.new_page()
    pg.goto((tmp_path / "t.html").as_uri())
    yield pg
    pg.close()


def _mau_vien(pg, mid: str) -> str:
    return pg.evaluate(
        f"() => getComputedStyle(document.getElementById('{mid}')).borderTopColor")


def _do_khong(mau: str) -> bool:
    """Màu này có phải sắc ĐỎ không? (`--bad` = #dc2626 sáng / #ef4444 tối)"""
    m = re.findall(r"[\d.]+", mau)
    if len(m) < 3:
        return False
    r, g, b = (float(x) for x in m[:3])
    return r > 150 and r > g * 2 and r > b * 2


def test_mieng_hong_co_vien_DO(trang):
    assert _do_khong(_mau_vien(trang, "m2")), (
        f"miếng .hong không có viền đỏ — màu đang là {_mau_vien(trang, 'm2')}")


def test_mieng_hong_TRONG_KHOANG_THO_van_do(trang):
    """Ca user gặp thật: `.tho` đứng sau nên đè mất `border-color` của `.hong`."""
    mau = _mau_vien(trang, "m3")
    assert _do_khong(mau), (
        f"miếng vừa .tho vừa .hong MẤT viền đỏ (màu {mau}) — luật .tho đứng sau "
        f"trong CSS nên thắng. Đây đúng lỗi user báo 09/09.")


def test_mieng_hong_DANG_CHON_van_do(trang):
    """`.chon` dùng outline nên không đè border — nhưng phải kiểm, không đoán."""
    assert _do_khong(_mau_vien(trang, "m4")), "miếng .chon + .hong mất viền đỏ"


def test_mieng_thuong_KHONG_do(trang):
    """Không được tô đỏ tràn lan — miếng lành phải giữ nguyên."""
    assert not _do_khong(_mau_vien(trang, "m0")), "miếng lành bị tô đỏ oan"
    assert not _do_khong(_mau_vien(trang, "m1")), "miếng .tho bị tô đỏ oan"


def test_nhan_clip_hong_HIEN_RA(trang):
    """Viền đỏ mỏng dễ lọt mắt — phải có chữ đọc được."""
    for mid in ("m2", "m3"):
        n = trang.evaluate(
            f"""() => {{
                const s = getComputedStyle(document.getElementById('{mid}'), '::after')
                return {{noi_dung: s.content, hien: s.display}}
            }}""")
        assert "hỏng" in n["noi_dung"], f"{mid}: thiếu nhãn 'clip hỏng' ({n})"
        assert n["hien"] != "none", f"{mid}: nhãn bị ẩn"


def test_nhan_KHONG_hien_o_mieng_lanh(trang):
    n = trang.evaluate(
        "() => getComputedStyle(document.getElementById('m0'), '::after').content")
    assert "hỏng" not in n, f"miếng lành cũng hiện nhãn hỏng: {n}"
