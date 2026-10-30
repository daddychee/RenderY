"""Khối đầu cảnh (hai luật 30/10) trên trang, trong CHROME THẬT: màn Kịch bản hiện cả khối, giữ xuống
dòng; thanh tiêu đề cảnh ở Storyboard chỉ hiện dòng `Có mặt:`."""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.request

import pytest

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho
from test_treatment_chay_chuong import TAM
from test_treatment_cum_canh import KtCum
from test_treatment_drama_api import SinhAssetGia, VeAnhGia, VeVideoGia, _ve_du_ref
from test_treatment_hai_luat import KHOI, VAO
from test_treatment_tat_ca_chrome import _cho, _mo, _Tiem, chrome  # noqa: F401 — `chrome` là fixture

KB = VAO.replace("Có mặt: Tasha, Marcus\n\n### P001", f"Có mặt: Tasha, Marcus\n{KHOI}\n\n### P001")
assert KB != VAO


@pytest.fixture
def may(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    kho = Kho(tmp_path / "k.db")
    app = tao_app(kho, ky_thuat=KtCum(), ve_anh=VeAnhGia(), ve_video=VeVideoGia(), sinh_asset=SinhAssetGia())
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
    goi("/api/tap/D1/drama", "POST", {"text": KB})
    _ve_du_ref(kho, TAM)
    yield {"url": url, "goi": goi, "kho": kho}
    sv.should_exit = True
    th.join(5)


def test_kich_ban_hien_ca_khoi_storyboard_chi_dong_co_mat(chrome, may):
    loi = []
    pg = _mo(chrome.new_context(viewport={"width": 1500, "height": 900}), may, loi)
    pg.evaluate("doiMan_chuong('C1')")
    assert _cho(lambda: pg.locator(".dong .vi").count() >= 2, 10, pg=pg)
    vi = pg.locator(".dong .vi").first.inner_text()
    assert "Có mặt: Tasha, Marcus\nMở cảnh: Tasha trái · Marcus phải\nMáy dàn cảnh:" in vi, vi
    pg.click("#mSb")
    pg.evaluate("doiMan_chuong('C1')")
    assert _cho(lambda: pg.locator(".lo-dau .meta").count() >= 2, 10, pg=pg)
    meta = pg.locator(".lo-dau .meta").first.inner_text()
    assert "Có mặt: Tasha, Marcus" in meta and "Máy dàn cảnh" not in meta, meta
    assert not loi, loi
