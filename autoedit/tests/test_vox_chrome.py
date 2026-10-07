"""Tool VOX — test TRONG CHROME THẬT (Playwright), máy chủ thật, thợ GIẢ.

Vì sao: luồng chọn ảnh / gửi / bấm điểm tách lại nằm ở JS. Bài học repo: test chuỗi xanh mà
trang chết là chuyện đã xảy ra nhiều lần ("sửa JS phải mở Chrome thật").
"""

from __future__ import annotations

import json
import socket
import threading
import time

import numpy as np
import pytest

from autoedit.collage.hang_doi import HangDoi
from autoedit.collage.kho_tach import KhoTach
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
    sv = uvicorn.Server(uvicorn.Config(_Tiem(tao_app(goc)), host="127.0.0.1", port=cong, log_level="warning"))
    th = threading.Thread(target=sv.run, daemon=True)
    th.start()
    for _ in range(100):
        if sv.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{cong}/", goc
    sv.should_exit = True
    th.join(5)


def _anh(tmp_path, ten, mau):
    from PIL import Image
    p = tmp_path / ten
    Image.new("RGB", (320, 180), mau).save(p)
    return p


def _cho(f, lan=100):
    for _ in range(lan):
        v = f()
        if v:
            return v
        time.sleep(0.05)
    return f()


def test_chon_hai_anh_nhap_giay_gui_roi_xem_video_va_tach_lai(chrome, may, tmp_path):
    url, goc = may
    pg = chrome.new_context(viewport={"width": 1400, "height": 900}).new_page()
    loi = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(url)
    pg.wait_for_selector(".tha")
    assert "an" in pg.inner_text("#ai")

    # ảnh 1: Pop-up 2,5 s
    with pg.expect_file_chooser() as fc:
        pg.click(".tha >> nth=0")
    fc.value.set_files(str(_anh(tmp_path, "a.png", (200, 60, 60))))
    pg.fill(".anh >> nth=0 >> input[type=number]", "2.5")
    pg.select_option(".anh >> nth=0 >> select >> nth=0", "popup")
    # ảnh 2: Chiều sâu 3 s, nối cắt thẳng
    pg.click("#them")
    with pg.expect_file_chooser() as fc:
        pg.click(".tha >> nth=1")
    fc.value.set_files(str(_anh(tmp_path, "b.png", (60, 60, 200))))
    pg.fill(".anh >> nth=1 >> input[type=number]", "3")
    pg.select_option(".noi select", "cat")
    assert "tổng 5,5 giây" in pg.inner_text("#tong")
    pg.click("#dung")
    pg.wait_for_selector(".viec")
    assert "chờ · thứ 1" in pg.inner_text(".viec")

    hd = HangDoi(goc / "hang_doi.db")
    v = hd.cua("an")[0]
    ch = json.loads(v["chuoi"])
    assert [x["giay"] for x in ch["anh"]] == [2.5, 3.0] and ch["noi"] == ["cat"]
    assert [x["mau"] for x in ch["anh"]] == ["popup", "chieu_sau"]

    # thợ giả: dựng xong + máy gắn ▲ cho ảnh Pop-up
    from autoedit.collage import tach
    m = np.zeros((180, 320), bool)
    m[40:, 100:200] = True
    KhoTach(goc).ghi(ch["anh"][0]["nhan"], "x", tach.KetQuaTach(
        [(m, 5.0)], np.zeros((180, 320, 3), np.float32), np.zeros((180, 320), np.float32), ["diem_sam_thap"]),
        np.full((180, 320, 3), 0.5, np.float32))
    hd.lay_tiep()
    ra = tmp_path / "ra.mp4"
    ra.write_bytes(b"\x00")
    hd.xong(v["id"], str(ra))
    pg.evaluate("napViec()")
    pg.wait_for_selector(".viec video")
    assert pg.locator(".viec .co").count() == 1 and "xong" in pg.inner_text(".viec .tt")

    # bấm ảnh có ▲ -> hộp tách: trái vào vật, phải vào nền -> Tách lại = việc mới mang điểm
    pg.click(".nho .o.bam")
    pg.wait_for_selector("#hop.mo")
    assert "không chắc" in pg.inner_text("#coTach")
    pg.wait_for_function("document.getElementById('hopAnh').naturalWidth > 0")
    hop = pg.locator("#hopAnh").bounding_box()
    pg.mouse.click(hop["x"] + hop["width"] * 0.5, hop["y"] + hop["height"] * 0.6)
    pg.mouse.click(hop["x"] + hop["width"] * 0.05, hop["y"] + hop["height"] * 0.1, button="right")
    assert pg.locator(".diem").count() == 2
    pg.click("#nutTach")
    moi = _cho(lambda: [x for x in hd.cua("an") if x["id"] != v["id"]])
    d = json.loads(moi[0]["chuoi"])["anh"][0]["diem"]
    assert [x["dau"] for x in d] == [1, 0]
    assert abs(d[0]["x"] - 0.5) < 0.02 and abs(d[0]["y"] - 0.6) < 0.02, d
    assert not loi, loi
