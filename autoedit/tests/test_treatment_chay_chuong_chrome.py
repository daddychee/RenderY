"""Nút "Chạy tới duyệt ảnh" trong CHROME THẬT (user chốt 29/10): máy chủ thật + bộ máy giả
(không LLM, không Seedvis, không tốn tiền). Fixture Chrome mượn của test Gen toàn bộ asset —
file đó có ở cả nhánh deploy lẫn dev."""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.request

import pytest

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho
from test_treatment_chay_chuong import HAI_CANH, TAM
from test_treatment_drama_api import SinhAssetGia, VeAnhGia, _ve_du_ref
from test_treatment_drama_shot_api import KyThuatBoCuc, VeVideoI2v
from test_treatment_tat_ca_chrome import _cho, _mo, _Tiem, chrome  # noqa: F401 — `chrome` là fixture


class VeAnhCho(VeAnhGia):
    """Ảnh dàn cảnh vẽ ngay; ảnh SHOT đứng chờ tới khi test mở cổng — trang kịp thấy việc
    đang chạy ở bước vẽ ảnh shot."""

    credit = 1234

    def __init__(self):
        super().__init__()
        self.cong = threading.Event()

    def gen_anh(self, prompt, dich, **kw):
        if not dich.stem.startswith("td_"):
            self.cong.wait(30)
        return super().gen_anh(prompt, dich, **kw)


@pytest.fixture
def may(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    kho = Kho(tmp_path / "k.db")
    va, vv = VeAnhCho(), VeVideoI2v()
    app = tao_app(kho, ky_thuat=KyThuatBoCuc(), ve_anh=va, ve_video=vv, sinh_asset=SinhAssetGia())
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        cong = s.getsockname()[1]
    sv = uvicorn.Server(uvicorn.Config(_Tiem(app), host="127.0.0.1", port=cong, log_level="warning"))
    th = threading.Thread(target=sv.run, daemon=True)
    th.start()
    for _ in range(100):
        if sv.started:
            break
        time.sleep(0.05)
    url = f"http://127.0.0.1:{cong}"

    def goi(duong, cach="GET", than=None):
        rq = urllib.request.Request(url + duong, method=cach,
                                    data=None if than is None else json.dumps(than).encode(),
                                    headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(rq).read() or b"null")

    goi("/api/tap", "POST", {"ma": "D1", "ten": "Hộp nhẫn", "loai": "drama"})
    goi("/api/tap/D1/drama", "POST", {"text": HAI_CANH})
    _ve_du_ref(kho, TAM)
    yield {"url": url, "goi": goi, "kho": kho, "va": va, "vv": vv}
    va.cong.set()
    sv.should_exit = True
    th.join(5)


def test_chay_chuong_tu_bam_toi_duyet_anh_shot(chrome, may):
    g, va, vv = may["goi"], may["va"], may["vv"]
    loi, hop, gui = [], [], []
    tra = {"v": False}

    def tl(d):
        hop.append(d.message)
        d.accept() if tra["v"] else d.dismiss()
    ctx = chrome.new_context(viewport={"width": 1500, "height": 900})
    pg = _mo(ctx, may, loi)
    pg.on("dialog", tl)
    pg.on("request", lambda r: r.method == "POST" and r.url.endswith("/C1/chay") and gui.append(r.url))
    pg.click("#mSb")
    assert _cho(lambda: pg.is_visible("#nutChuong"), 5, pg=pg), "chương drama: người sửa thấy nút"
    pg.evaluate("doiMan_chuong('TONG')")
    assert _cho(lambda: not pg.is_visible("#nutChuong"), 5, pg=pg), "Toàn bộ: không có nút chạy chương"
    pg.evaluate("doiMan_chuong('C1')")
    assert _cho(lambda: pg.is_visible("#nutChuong"), 5, pg=pg)

    # ── hộp xác nhận: số máy chủ đếm, cảnh 3 người, không duyệt shot / không video ──
    k = g("/api/tap/D1/C1/chay")["ke_hoach"]
    pg.click("#nutChuong")
    assert _cho(lambda: hop, 5, pg=pg)
    for chu in ("Chạy chương C1 tới duyệt ảnh (2 cảnh · 3 clip)", "Breakdown 3 clip", "viết prompt 3 clip",
                "vẽ 2 ảnh dàn cảnh", "MÁY TỰ DUYỆT 2 ảnh dàn cảnh", "vẽ ≈ 5 ảnh khung đầu shot",
                f"≈ {k['credit']} cr (7 ảnh · ", f"≈ {k['phut']} phút", "Số dư: ",
                "C002 · bếp nhà Tasha · trưa · N02 (3 người)", "Máy KHÔNG duyệt ảnh shot, KHÔNG gọi video"):
        assert chu in hop[-1], (chu, hop[-1])
    assert not gui and pg.is_enabled("#nutChuong") and pg.inner_text("#nutChuong") == "Chạy tới duyệt ảnh"

    # ── đồng ý: tiến độ hiện, F5 giữa chừng vẫn thấy, người chỉ xem không có nút ──
    tra["v"] = True
    pg.click("#nutChuong")
    assert _cho(lambda: gui, 5, pg=pg)
    assert _cho(lambda: "Chạy chương C1 · vẽ ảnh shot" in pg.inner_text("#viecChuong"), 15, pg=pg), \
        pg.inner_text("#viecChuong")
    pg.reload()
    pg.wait_for_selector("#nutTap", state="attached")
    _cho(lambda: pg.evaluate("TAP_MA") == "D1", 10, pg=pg)
    pg.click("#mSb")
    assert _cho(lambda: "Chạy chương C1 · vẽ ảnh shot" in pg.inner_text("#viecChuong"), 10, pg=pg)
    assert "owner bấm" in pg.inner_text("#viecChuong")
    ctx2 = chrome.new_context(viewport={"width": 1500, "height": 900},
                              extra_http_headers={"X-Remote-User": "lan", "X-Remote-Actions": "xem"})
    pg2 = _mo(ctx2, may, loi)
    pg2.click("#mSb")
    assert _cho(lambda: "Chạy chương C1 ·" in pg2.inner_text("#viecChuong"), 10, pg=pg2)
    assert not pg2.is_visible("#nutChuong"), "người chỉ xem không thấy nút"

    # ── xong: tóm tắt, danh sách dàn cảnh MÁY duyệt (cảnh 3 người đánh dấu) ──
    va.cong.set()
    assert _cho(lambda: "Lần chạy chương C1 gần nhất: xong · 0 lỗi" in pg.inner_text("#viecChuong"), 20, pg=pg), \
        pg.inner_text("#viecChuong")
    ket = pg.inner_text("#ketChuong")
    assert "2 ảnh dàn cảnh do MÁY tự duyệt" in ket and "3 người — khung cắt mặc định chưa tin" in ket, ket
    assert "Chạy chương C1 xong: 2 ảnh dàn cảnh máy duyệt · 0 lỗi" in pg.inner_text("#toast")
    assert not vv.goi, "không gọi video"

    # ── bấm tên cảnh: panel dàn cảnh nói máy tự duyệt; xác nhận thì cảnh rời danh sách ──
    pg.click("#ketChuong a:has-text('C002')")
    assert _cho(lambda: "máy tự duyệt" in pg.inner_text("#hopCanh"), 5, pg=pg), pg.inner_text("#hopCanh")
    assert "3 người" in pg.inner_text("#hopCanh")
    pg.click("#hopCanh button:has-text('Máy đã duyệt · bấm xác nhận')")
    assert _cho(lambda: "✓ đã duyệt" in pg.inner_text("#hopCanh"), 5, pg=pg)
    assert _cho(lambda: "1 ảnh dàn cảnh do MÁY tự duyệt" in pg.inner_text("#ketChuong"), 5, pg=pg), \
        pg.inner_text("#ketChuong")
    assert "máy tự duyệt" not in pg.inner_text("#hopCanh")
    assert not loi, loi
