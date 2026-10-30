"""Chọn NHÀ gen video khi bấm nút (user 30/10) trong CHROME THẬT: nút Gen video của shot drama và
nút Gen Video / ⇥ Nối của cảnh narration hiện hộp Seedvis / Lightvisual / Gensuite, nhà chưa có
khoá thì mờ kèm lý do, chọn xong gửi kèm nhà; nhớ nhà vừa chọn; Esc huỷ mà không đóng hộp cảnh.
Máy chủ thật + bộ máy giả (không LLM, không nhà video thật, không tốn tiền).

Chụp màn hình hộp chọn: đặt CHUP_CHON_NHA=<đường dẫn .png> khi chạy test."""

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
from test_treatment_drama_api import SinhAssetGia, VeAnhGia, _ve_du_ref
from test_treatment_drama_shot_api import KyThuatBoCuc
from test_treatment_gensuite import VeVideoNha
from test_treatment_tat_ca_chrome import _cho, _mo, _Tiem, chrome  # noqa: F401 — `chrome` là fixture

HOP = "#nenNha.mo"


@pytest.fixture
def may(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    kho = Kho(tmp_path / "k.db")
    vv = VeVideoNha()
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


def _gui(pg):
    """Thân các POST gửi video trang vừa bắn."""
    ds = []
    pg.on("request", lambda r: r.method == "POST" and r.url.endswith("/video") and ds.append(r.post_data_json))
    return ds


def test_shot_drama_chon_nha_mo_nha_thieu_khoa_nho_lan_truoc_esc_huy(chrome, may):
    g, kho, vv = may["goi"], may["kho"], may["vv"]
    for d in ("breakdown", "prompt-drama", "dan-canh", "dan-canh/duyet"):
        g(f"/api/tap/D1/C1/dong/0/{d}", "POST")
    p1 = next(c for c in kho.doc("D1", "C1")["dong"][0]["canh"] if c.get("pm") == "P001")["id"]
    sh = g(f"/api/tap/D1/C1/canh/{p1}/shot")
    s1 = sh[0]["sid"]
    g(f"/api/tap/D1/C1/canh/{p1}/shot/{s1}/anh", "POST")
    g(f"/api/tap/D1/C1/canh/{p1}/shot/{s1}/duyet", "POST")
    nut = f"#theShot button[data-viec='video'][data-sid='{s1}']"

    loi = []
    pg = _mo(chrome.new_context(viewport={"width": 1500, "height": 900}), may, loi)
    gui = _gui(pg)
    pg.click("#mSb")
    pg.evaluate("doiMan_chuong('C1')")
    pg.click(".tc:has(.ma:text-is('P001'))")
    pg.wait_for_selector(nut)
    assert pg.is_enabled(nut)

    # ── bấm: hộp chọn ba nhà, Lightvisual chưa có khoá thì mờ và ghi lý do, chưa gửi gì ──
    pg.click(nut)
    pg.wait_for_selector(HOP)
    nha = pg.locator("#hopNha [data-nha]")
    assert nha.evaluate_all("ds => ds.map(b => b.dataset.nha)") == ["seedvis", "lightvisual", "gensuite"]
    lv = pg.locator("#hopNha [data-nha='lightvisual']")
    assert lv.is_disabled() and "Chưa có khoá Lightvisual — Owner cấp ở General" in lv.inner_text()
    assert pg.locator("#hopNha [data-nha='gensuite']").is_enabled()
    assert "10 giây" in pg.inner_text("#hopNha [data-nha='gensuite']"), "trang nói Gensuite luôn 10 s"
    assert not gui and not vv.goi
    if os.getenv("CHUP_CHON_NHA"):
        pg.screenshot(path=os.environ["CHUP_CHON_NHA"])

    # ── chọn Gensuite: gửi kèm nhà, hộp đóng, máy chủ nhận Gensuite 10 s ──
    pg.click("#hopNha [data-nha='gensuite']")
    assert _cho(lambda: gui, 5, pg=pg)
    assert gui == [{"nha": "gensuite"}]
    assert not pg.is_visible(HOP)
    assert _cho(lambda: vv.goi, 5, pg=pg) and (vv.goi[-1]["nha"], vv.goi[-1]["giay"]) == ("gensuite", 10)
    assert _cho(lambda: pg.inner_text(nut) == "Gen video lại" and pg.is_enabled(nut), 10, pg=pg), pg.inner_text(nut)

    # ── lần sau: nhà vừa chọn đứng sẵn (sáng + có focus); Esc huỷ, hộp cảnh vẫn mở, không gửi ──
    pg.click(nut)
    pg.wait_for_selector(HOP)
    gs = pg.locator("#hopNha [data-nha='gensuite']")
    assert "on" in gs.get_attribute("class") and "lần trước" in gs.inner_text()
    assert pg.evaluate("document.activeElement.dataset.nha") == "gensuite"
    pg.keyboard.press("Escape")
    assert _cho(lambda: not pg.is_visible(HOP), 3, pg=pg)
    pg.wait_for_timeout(300)
    assert len(gui) == 1 and pg.is_visible("#nenCanh.mo"), "Esc chỉ đóng hộp chọn"
    assert pg.is_enabled(nut) and pg.inner_text(nut) == "Gen video lại"

    # ── Enter gửi nhà đang đứng sẵn ──
    pg.click(nut)
    pg.wait_for_selector(HOP)
    pg.keyboard.press("Enter")
    assert _cho(lambda: len(gui) == 2, 5, pg=pg)
    assert gui[-1] == {"nha": "gensuite"}
    assert not loi, loi


def test_canh_narration_gen_video_va_noi_deu_hoi_nha(chrome, may, monkeypatch):
    import autoedit.treatment.app as mapp

    # Video giả không phải MP4 thật: khung cuối cho nút Nối lấy từ đồ giả.
    monkeypatch.setattr(mapp, "khung_cuoi", lambda v, dich: dich.write_bytes(b"KHUNG-CUOI") and dich)
    g, vv = may["goi"], may["vv"]
    g("/api/tap", "POST", {"ma": "SE001", "ten": "K-129"})
    g("/api/tap/SE001/chuong", "POST", {"ma": "H"})
    g("/api/tap/SE001/H", "PUT", {"outline": "", "dong": [{"en": "Voice one.", "vi": "", "het": 0, "canh": [
        {"t": "Tàu lướt đáy biển", "pa": "EN still", "pv": "EN motion", "co": "MS", "goc": "low angle",
         "cd": "slow push in"},
        {"t": "Tàu chìm", "pa": "EN still 2", "pv": "EN motion 2", "co": "MS", "goc": "eye", "cd": "static"}]}]})
    cs = may["kho"].doc("SE001", "H")["dong"][0]["canh"]
    for c in cs:
        g(f"/api/tap/SE001/H/canh/{c['id']}/anh", "POST")
        g(f"/api/tap/SE001/H/canh/{c['id']}/duyet", "POST")
    g(f"/api/tap/SE001/H/canh/{cs[0]['id']}/video", "POST", {"nha": "seedvis"})    # cảnh trước có video
    g(f"/api/tap/SE001/H/canh/{cs[0]['id']}/video-kiem", "POST")

    loi = []
    pg = _mo(chrome.new_context(viewport={"width": 1500, "height": 900}), may, loi)
    gui = _gui(pg)
    pg.evaluate("document.getElementById('dsTap').value = 'SE001'; doiTap('SE001')")
    assert _cho(lambda: pg.evaluate("TAP_MA") == "SE001", 10, pg=pg)
    pg.click("#mSb")
    pg.evaluate("doiMan_chuong('H')")
    assert _cho(lambda: pg.evaluate("canhTrongPham(dungCanhTap()).length") == 2, 10, pg=pg)
    pg.evaluate("moCanh(canhTrongPham(dungCanhTap())[1].ma)")
    noi = "#hopCanh button:has-text('⇥ Nối từ')"
    pg.wait_for_selector(noi)

    pg.click(noi)
    pg.wait_for_selector(HOP)
    pg.click("#hopNha [data-nha='seedvis']")
    assert _cho(lambda: gui, 5, pg=pg)
    assert gui == [{"noi": True, "nha": "seedvis"}]
    assert _cho(lambda: len(vv.goi) == 2, 5, pg=pg) and vv.goi[-1]["nha"] == "seedvis"

    nut = "#hopCanh button:has-text('Gen Video lại')"
    assert _cho(lambda: pg.locator(nut).count() == 1 and pg.is_enabled(nut), 10, pg=pg)
    pg.click(nut)
    pg.wait_for_selector(HOP)
    assert "on" in pg.get_attribute("#hopNha [data-nha='seedvis']", "class"), "nhớ chung mọi nút"
    pg.click("#hopNha [data-nha='gensuite']")
    assert _cho(lambda: len(gui) == 2, 5, pg=pg)
    assert gui[-1] == {"noi": False, "nha": "gensuite"}
    assert _cho(lambda: len(vv.goi) == 3, 5, pg=pg) and (vv.goi[-1]["nha"], vv.goi[-1]["giay"]) == ("gensuite", 10)
    assert not loi, loi
