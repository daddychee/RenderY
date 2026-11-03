"""Tick tài khoản gen video theo chương (haint 03/11) trong CHROME THẬT: thanh Storyboard của chương
hiện mọi tài khoản kèm trạng thái (xanh / đỏ), tick lưu theo chương; chương có tick thì bấm Gen video
gửi thẳng không hỏi nhà, máy chủ chọn tài khoản đã tick còn xanh; bỏ hết tick là hộp chọn nhà về như cũ.
Máy chủ thật + bộ máy giả (không nhà video thật, không tốn tiền).

Chụp màn hình thanh: đặt CHUP_TK=<đường dẫn .png> khi chạy test."""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.request

import pytest

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho
from test_treatment_chay_chuong import HAI_CANH, TAM
from test_treatment_chon_nha_chrome import HOP, _gui
from test_treatment_drama_api import SinhAssetGia, VeAnhGia, _ve_du_ref
from test_treatment_drama_shot_api import KyThuatBoCuc
from test_treatment_gensuite import VeVideoNha
from test_treatment_tat_ca_chrome import _cho, _mo, _Tiem, chrome  # noqa: F401 — `chrome` là fixture
from test_treatment_tk_video import VeVideoTk


class VeVideoTkNha(VeVideoTk):
    nha_co_khoa = VeVideoNha.nha_co_khoa


@pytest.fixture
def may(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    kho = Kho(tmp_path / "k.db")
    vv = VeVideoTkNha()
    app = tao_app(kho, ky_thuat=KyThuatBoCuc(), ve_anh=VeAnhGia(), ve_video=vv, sinh_asset=SinhAssetGia())
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
    yield {"url": url, "goi": goi, "kho": kho, "vv": vv}
    sv.should_exit = True
    th.join(5)


def test_tick_tai_khoan_chuong_gui_thang_khong_hoi_nha(chrome, may):
    g, kho, vv = may["goi"], may["kho"], may["vv"]
    for d in ("breakdown", "prompt-drama", "dan-canh", "dan-canh/duyet"):
        g(f"/api/tap/D1/C1/dong/0/{d}", "POST")
    p1 = next(c for c in kho.doc("D1", "C1")["dong"][0]["canh"] if c.get("pm") == "P001")["id"]
    s1 = g(f"/api/tap/D1/C1/canh/{p1}/shot")[0]["sid"]
    g(f"/api/tap/D1/C1/canh/{p1}/shot/{s1}/anh", "POST")
    g(f"/api/tap/D1/C1/canh/{p1}/shot/{s1}/duyet", "POST")
    nut = f"#theShot button[data-viec='video'][data-sid='{s1}']"

    loi = []
    pg = _mo(chrome.new_context(viewport={"width": 1500, "height": 900}), may, loi)
    gui = _gui(pg)
    pg.click("#mSb")
    pg.evaluate("doiMan_chuong('C1')")

    # ── thanh Storyboard: bốn tài khoản, trạng thái từ máy chủ, chưa tick ──
    nhan = "#tkVideo label"
    assert _cho(lambda: pg.locator(nhan).count() == 4, 5, pg=pg)
    the = pg.locator(nhan)
    assert "Lightvisual · a" in the.nth(0).inner_text() and "gói tới 11:30" in the.nth(0).inner_text()
    assert the.nth(0).get_attribute("class") == "xanh" and the.nth(1).get_attribute("class") == "do"
    assert "hết gói" in the.nth(1).inner_text()
    assert not pg.locator("#tkVideo input:checked").count()

    # ── tick a và c: lưu theo chương ──
    pg.check("#tkVideo input[data-tk='a']")
    assert _cho(lambda: kho.tk_video("D1", "C1") == ["a"], 5, pg=pg)
    pg.check("#tkVideo input[data-tk='c']")
    assert _cho(lambda: kho.tk_video("D1", "C1") == ["a", "c"], 5, pg=pg)
    if os.getenv("CHUP_TK"):
        pg.screenshot(path=os.environ["CHUP_TK"])

    # ── Gen video: không hộp chọn nhà, gửi thẳng, máy chủ chọn tài khoản đã tick ──
    pg.click(".tc:has(.ma:text-is('P001'))")
    pg.wait_for_selector(nut)
    pg.click(nut)
    assert _cho(lambda: gui, 5, pg=pg)
    assert gui == [{}] and not pg.is_visible(HOP)
    assert _cho(lambda: vv.goi, 5, pg=pg) and vv.goi[-1]["khoa"] in ("a", "c")
    assert _cho(lambda: pg.inner_text(nut) == "Gen video lại" and pg.is_enabled(nut), 10, pg=pg), pg.inner_text(nut)

    # ── Kiểm lại: máy chủ đọc số dư ngay ──
    pg.evaluate("dongCanh()")
    pg.click("#tkVideo button")
    assert _cho(lambda: vv.kiem == 1, 5, pg=pg)

    # ── bỏ hết tick: hộp chọn nhà về như cũ ──
    pg.uncheck("#tkVideo input[data-tk='a']")
    assert _cho(lambda: kho.tk_video("D1", "C1") == ["c"], 5, pg=pg)
    pg.uncheck("#tkVideo input[data-tk='c']")
    assert _cho(lambda: kho.tk_video("D1", "C1") == [], 5, pg=pg)
    pg.click(".tc:has(.ma:text-is('P001'))")
    pg.wait_for_selector(nut)
    pg.click(nut)
    pg.wait_for_selector(HOP)
    assert len(gui) == 1
    assert not loi, loi
