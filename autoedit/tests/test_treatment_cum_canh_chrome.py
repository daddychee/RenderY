"""Panel ảnh dàn cảnh của cảnh sau trong cụm cùng phim trường, trong CHROME THẬT: nói rõ vẽ tiếp từ
cảnh nào, cảnh đó chưa duyệt thì khoá nút vẽ; bấm tên cảnh trước mở panel cảnh đó. Fixture Chrome
mượn test Gen toàn bộ asset (có ở cả nhánh deploy lẫn dev)."""

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
from test_treatment_cum_canh import CUM, KtCum
from test_treatment_drama_api import SinhAssetGia, VeAnhGia, VeVideoGia, _ve_du_ref
from test_treatment_tat_ca_chrome import _cho, _mo, _Tiem, chrome  # noqa: F401 — `chrome` là fixture


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
    goi("/api/tap/D1/drama", "POST", {"text": CUM})
    _ve_du_ref(kho, TAM)
    for d in ("breakdown", "prompt-drama"):
        for i in (0, 1):
            goi(f"/api/tap/D1/C1/dong/{i}/{d}", "POST")
    goi("/api/tap/D1/C1/dong/0/dan-canh", "POST")                 # vẽ, CHƯA duyệt
    yield {"url": url, "goi": goi, "kho": kho}
    sv.should_exit = True
    th.join(5)


NUT = "#hopCanh button[data-viec='dan']"


def test_panel_canh_sau_noi_vẽ_tiep_khoa_nut_toi_khi_canh_truoc_duyet(chrome, may):
    loi = []
    pg = _mo(chrome.new_context(viewport={"width": 1500, "height": 900}), may, loi)
    pg.click("#mSb")
    pg.evaluate("doiMan_chuong('C1')")
    pg.evaluate("moDanCanh('C1', 1)")
    assert _cho(lambda: "Cùng phim trường với" in pg.inner_text("#hopCanh"), 10, pg=pg), pg.inner_text("#hopCanh")
    chu = pg.inner_text("#hopCanh")
    assert "C001 · phòng VIP bệnh viện" in chu and "chưa duyệt" in chu
    assert pg.is_disabled(NUT), "cảnh trước chưa duyệt: khoá nút vẽ"
    may["goi"]("/api/tap/D1/C1/dong/0/dan-canh/duyet", "POST")
    pg.evaluate("moDanCanh('C1', 1)")
    assert _cho(lambda: "chưa duyệt — duyệt trước" not in pg.inner_text("#hopCanh")
                and "Cùng phim trường với" in pg.inner_text("#hopCanh"), 10, pg=pg)
    assert _cho(lambda: pg.is_enabled(NUT), 5, pg=pg)
    pg.click("#hopCanh a:has-text('C001')")
    assert _cho(lambda: "Ảnh dàn cảnh · C001" in pg.inner_text("#hopCanh"), 10, pg=pg), pg.inner_text("#hopCanh")
    assert "Cùng phim trường với" not in pg.inner_text("#hopCanh"), "cảnh đầu cụm vẽ như cảnh mới"
    assert not loi, loi
