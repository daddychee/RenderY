"""Tool VOX — test TRONG CHROME THẬT (Playwright), máy chủ thật, SAM/độ sâu GIẢ.

Vì sao: bước chọn lớp (kéo khung, máy đề xuất, xoá) + khung hình + style nằm ở JS. Bài học repo:
test chuỗi xanh mà trang chết là chuyện đã xảy ra nhiều lần ("sửa JS phải mở Chrome thật").
"""

from __future__ import annotations

import json
import socket
import threading
import time

import numpy as np
import pytest

from autoedit.collage.hang_doi import HangDoi
from autoedit.vox.app import tao_app


class _Tiem:
    """Thay vai gateway 9000: tiêm danh tính + cờ quyền dựng."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            scope = dict(scope, headers=list(scope["headers"]) + [(b"x-remote-user", b"an"),
                                                                  (b"x-remote-actions", b"vao,dung")])
        await self.app(scope, receive, send)


class _MayLopGia:
    def de_xuat(self, rgb):
        return [[0.1, 0.1, 0.3, 0.4]]

    def cat(self, rgb, khung_lop):
        h, w = rgb.shape[:2]
        ra = []
        for x0, y0, x1, y1 in khung_lop:
            m = np.zeros((h, w), bool)
            m[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = True
            ra.append(m)
        return ra


@pytest.fixture(scope="module")
def chrome():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"không mở được Chrome: {str(exc)[:80]}")
        yield b
        b.close()


@pytest.fixture
def may(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    goc = tmp_path / "collage"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        cong = s.getsockname()[1]
    sv = uvicorn.Server(uvicorn.Config(_Tiem(tao_app(goc, may_lop=_MayLopGia())), host="127.0.0.1", port=cong,
                                       log_level="warning"))
    th = threading.Thread(target=sv.run, daemon=True)
    th.start()
    for _ in range(100):
        if sv.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{cong}/", goc
    sv.should_exit = True
    th.join(5)


def _anh(tmp_path, ten, w, h, mau=(90, 120, 150)):
    from PIL import Image
    p = tmp_path / ten
    Image.new("RGB", (w, h), mau).save(p)
    return p


def _cho(f, lan=100):
    for _ in range(lan):
        v = f()
        if v:
            return v
        time.sleep(0.05)
    return f()


def test_chon_lop_bang_keo_khung_de_xuat_xoa_roi_dung_style(chrome, may, tmp_path):
    url, goc = may
    pg = chrome.new_context(viewport={"width": 1400, "height": 900}).new_page()
    loi = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(url)
    pg.wait_for_selector(".tha")
    assert pg.locator("select").count() == 2, "chỉ còn ô Khung + Style — đã bỏ Mẫu/Camera/Nối"
    with pg.expect_file_chooser() as fc:
        pg.click(".tha >> nth=0")
    fc.value.set_files(str(_anh(tmp_path, "a.png", 320, 180)))
    pg.fill(".anh >> nth=0 >> input[type=number]", "3")

    pg.click(".chon-lop")
    pg.wait_for_selector("#hop.mo")
    pg.wait_for_function("document.getElementById('xemLop').naturalWidth > 0")
    pg.click("#nutDeXuat")                                         # máy đề xuất 1 khung
    pg.wait_for_function("document.querySelectorAll('#dsLop .lop').length === 1")
    pg.wait_for_function("document.getElementById('xemLop').src.startsWith('data:image/jpeg')")
    hop = pg.locator("#xemLop").bounding_box()                     # kéo thêm một khung 50%..90% x 20%..80%
    pg.mouse.move(hop["x"] + hop["width"] * 0.5, hop["y"] + hop["height"] * 0.2)
    pg.mouse.down()
    pg.mouse.move(hop["x"] + hop["width"] * 0.7, hop["y"] + hop["height"] * 0.5, steps=5)
    pg.mouse.move(hop["x"] + hop["width"] * 0.9, hop["y"] + hop["height"] * 0.8, steps=5)
    pg.mouse.up()
    pg.wait_for_function("document.querySelectorAll('#dsLop .lop').length === 2")
    pg.click("#dsLop .lop >> nth=0 >> button")                     # bỏ khung máy đề xuất
    pg.wait_for_function("document.querySelectorAll('#dsLop .lop').length === 1")
    time.sleep(0.4)
    pg.click("#nutXong")
    assert "1 lớp" in pg.inner_text(".anh >> nth=0")

    pg.select_option("#style", "black_grid")
    pg.click("#dung")
    pg.wait_for_selector(".viec")
    v = _cho(lambda: HangDoi(goc / "hang_doi.db").cua("an"))[0]
    ch = json.loads(v["chuoi"])
    assert ch["style"] == "black_grid" and ch["khung"] == "16:9" and ch["anh"][0]["giay"] == 3.0
    (x0, y0, x1, y1), = ch["anh"][0]["khung_lop"]
    assert abs(x0 - 0.5) < 0.02 and abs(y0 - 0.2) < 0.02 and abs(x1 - 0.9) < 0.02 and abs(y1 - 0.8) < 0.02, ch
    assert "Black Grid" in pg.inner_text(".viec .dau")
    assert not loi, loi


def test_khung_tu_theo_anh_dau_chon_tay_thi_giu_doi_khung_thi_xoa_lop(chrome, may, tmp_path):
    url, goc = may
    pg = chrome.new_context(viewport={"width": 1400, "height": 900}).new_page()
    loi = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(url)
    pg.wait_for_selector(".tha")
    assert pg.input_value("#khungVid") == "16:9"
    for (w, h), mong in (((300, 375), "4:5"), ((180, 320), "9:16"), ((320, 180), "16:9")):
        with pg.expect_file_chooser() as fc:
            pg.click(".tha >> nth=0")
        fc.value.set_files(str(_anh(tmp_path, f"a{w}.png", w, h)))
        pg.wait_for_function(f"document.getElementById('khungVid').value === '{mong}'", timeout=5000)
    # có lớp rồi mà đổi khung hình -> lớp bị xoá (khung lớp tính trên ảnh đã cắt khung hình)
    pg.click(".chon-lop")
    pg.wait_for_selector("#hop.mo")
    pg.click("#nutDeXuat")
    pg.wait_for_function("document.querySelectorAll('#dsLop .lop').length === 1")
    pg.click("#nutXong")
    assert "1 lớp" in pg.inner_text(".anh >> nth=0")
    pg.select_option("#khungVid", "4:5")
    assert "chưa chọn" in pg.inner_text(".anh >> nth=0") and "chọn lại lớp" in pg.inner_text("#bao")
    with pg.expect_file_chooser() as fc:                           # chọn tay rồi: đổi ảnh không tự nhảy khung
        pg.click(".tha >> nth=0")
    fc.value.set_files(str(_anh(tmp_path, "b.png", 180, 320)))
    time.sleep(0.5)
    assert pg.input_value("#khungVid") == "4:5"
    assert not loi, loi
