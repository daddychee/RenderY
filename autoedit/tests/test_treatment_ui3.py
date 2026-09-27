"""Hộp cảnh v3 — Owner duyệt mockup ui3 ngày 27/09: toàn màn hình, bốn bước
theo đúng thứ tự tay làm (References → Camera angle → Shot size → Camera
movement), nhãn là thuật ngữ chuyên môn tiếng Anh, KHÔNG có ô "chưa đo" (Owner:
bỏ hẳn cho gọn), KHÔNG có gợi ý LLM (Owner: thôi không cần làm).
"""

from __future__ import annotations

import pathlib
import re

import pytest

from autoedit.treatment import app as mapp

HTML = pathlib.Path(mapp.__file__).parent / "static" / "treatment.html"


@pytest.fixture(scope="module")
def html():
    return HTML.read_text(encoding="utf-8")


def _than(html, ten):
    i = html.index("function " + ten + "(")
    return html[i:html.index("\nfunction ", i + 1)]


def _bang_js(html, ten):
    i = html.index("var " + ten + " = {")
    khoi = html[i:html.index("};", i)]
    return dict(re.findall(r"(\w+): \"([^\"]*)\"", khoi))


def test_hop_canh_TOAN_MAN_HINH_va_cac_phieu_khac_thi_khong(html):
    assert "#hopCanh.toan{width:100vw" in html and "height:100vh" in html[html.index("#hopCanh.toan{"):][:200]
    assert "hopToan(true)" in _than(html, "moCanh")
    assert "hopToan(false)" in _than(html, "dongCanh")
    # Tone · Model · Asset · gợi ý asset vẽ vào cùng #hopCanh -> phải hạ cờ
    assert html.count("hopToan(false);\n  document.getElementById(\"hopCanh\").innerHTML = h") == 4


def test_bon_buoc_dung_thu_tu_Ref_Angle_Size_Movement(html):
    m = _than(html, "moCanh")
    assert m.index("References") < m.index("veKhungCanh(x)") < m.index("veMayCanh(x)")
    kh = _than(html, "veKhungCanh")
    assert kh.index('"Camera angle"') < kh.index('"Shot size"'), "góc máy (2) trước cỡ cảnh (3) — Owner chốt"
    assert kh.index('nutMa("goc"') < kh.index('nutMa("co"')
    assert '"Camera movement"' in _than(html, "veMayCanh")
    # số bước
    assert re.search(r"buocDau\(2, \"Camera angle\"", kh) and re.search(r"buocDau\(3, \"Shot size\"", kh)
    assert 'buocDau(4, "Camera movement"' in _than(html, "veMayCanh")


def test_nhan_la_thuat_ngu_chuyen_mon_tieng_Anh(html):
    assert set(_bang_js(html, "NHAN_GOC").values()) == {
        "Eye level", "Low angle", "High angle", "Bird's-eye view", "Top shot", "Over-the-shoulder", "POV"}
    assert set(_bang_js(html, "NHAN_CO").values()) == {
        "Extreme wide shot", "Wide shot", "Medium shot", "Medium close-up", "Close-up",
        "Extreme close-up", "Aerial shot"}
    assert set(_bang_js(html, "NHAN_CD").values()) == {
        "Static", "Push in", "Pull out", "Crash zoom", "Pan left", "Pan right", "Whip pan",
        "Tilt up", "Tilt down", "Tracking", "Truck left", "Truck right", "Arc shot", "360 orbit"}
    # mỗi nhãn có chú thích Việt đi kèm
    for bang, goi in (("NHAN_GOC", "GOI_GOC"), ("NHAN_CO", "GOI_CO"), ("NHAN_CD", "GOI_CD")):
        assert set(_bang_js(html, bang)) == set(_bang_js(html, goi)), bang


def test_ba_nhom_chuyen_dong_phu_dung_moi_ma_cua_CD_CHU_mot_lan(html):
    i = html.index("var NHOM_CD = [")
    khoi = html[i:html.index("]];", i)]
    ma = re.findall(r'"(\w+)"', khoi)
    ma = [m for m in ma if m in mapp.CD_CHU or m.islower()]
    ma = [m for m in ma if m in mapp.CD_CHU]
    assert sorted(ma) == sorted(mapp.CD_CHU), "nhóm phải phủ đúng bảng đã đo, không thừa không thiếu"
    assert len(ma) == len(set(ma))


def test_KHONG_co_o_chua_do_va_KHONG_goi_y_LLM(html):
    for chu in ("Dutch", "Handheld", "Boom", "Dolly zoom", "Full shot", "Medium wide", "chưa đo"):
        assert chu not in html, chu
    # `goiYTaiSan` (đọc kịch bản gợi asset) là việc khác, vẫn còn — chỉ cấm gợi ý KHUNG/MÁY
    for chu in ("LLM gợi ý", "batGoiY", "dungGoiY", "goiYKhung", "goiYMay"):
        assert chu not in html, chu


def test_o_chon_la_the_co_nhan_lon_va_chu_thich_nho(html):
    n = _than(html, "nutMa")
    assert "class=\"o" in n and "<b>' + nhan[m] + '</b>" in n and "<small>" in n
    assert "luoi" in n
    # chữ tự do cũ của LLM vẫn được bày để thay
    assert "chipCu(" in _than(html, "veKhungCanh") and "chipCu(" in _than(html, "veMayCanh")


def test_buoc_1_dem_anh_se_gui_va_giu_cac_khoi_cu(html):
    m = _than(html, "moCanh")
    assert "gui.length + ' / 4" in m
    for f in ("veTruongDoanCanh(x)", "veTaiSanCanh(x)", "veAnhSeGui(x)", "veTongCanh(x)",
              "veMoHinhCanh(x)", 'hopPrompt("Prompt ảnh"', 'hopPrompt("Prompt video"'):
        assert f in m, f
    assert 'id="oCanh"' in m and "luuNoiCanh(" in m, "nội dung/hành động vẫn sửa được ngay trên đầu"
