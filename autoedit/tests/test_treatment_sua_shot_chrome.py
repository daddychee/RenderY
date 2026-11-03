"""Ô "Yêu cầu sửa" trên thẻ shot drama (user haint 31/10: sửa 1/4 shot mà không Breakdown lại cả P) trong
CHROME THẬT: gõ tiếng Việt → Lưu lời sửa → thấy câu tiếng Anh máy dịch; sửa tay câu tiếng Anh rồi bấm thẳng
"Sửa ảnh này" thì câu mới tới máy chủ TRƯỚC lượt sửa ảnh (cú bấm không rơi mất); nút Sửa ảnh này chỉ bật
khi có ảnh và có lời sửa; Quay lại ảnh / video trước hiện khi có bản cũ; chữ gõ dở không mất khi thẻ vẽ
lại; chữ người gõ không thành HTML; xoá lời sửa = lưu rỗng. Máy chủ thật + bộ máy giả (không LLM, không
nhà ảnh/video thật, không tốn tiền).

Chụp thẻ shot: đặt CHUP_SUA_SHOT=<thư mục> khi chạy test."""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.request
from pathlib import Path

import pytest
from PIL import Image

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho
from test_treatment_chay_chuong import HAI_CANH, TAM
from test_treatment_drama_api import SinhAssetGia, VeAnhGia, _ve_du_ref
from test_treatment_sua_shot_api import SUA_EN as DICH, KyThuatSua, VeVideoDem
from test_treatment_tat_ca_chrome import _cho, _mo, _Tiem, chrome  # noqa: F401 — `chrome` là fixture


class VeAnhMau(VeAnhGia):
    """Mỗi lượt vẽ một màu khác: bản hiện tại và bản cũ nhìn khác nhau trên ảnh chụp."""

    def gen_anh(self, prompt, dich, ref=None, model=None, ti_le=None):
        super().gen_anh(prompt, dich, ref=ref, model=model, ti_le=ti_le)
        n = len(self.goi)
        Image.new("RGB", self.CO.get(ti_le, (480, 270)), (60 + 40 * n % 180, 90, 160 - 30 * n % 120)).save(dich)
        return dich


@pytest.fixture
def may(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    kho = Kho(tmp_path / "k.db")
    kt, va, vv = KyThuatSua(), VeAnhMau(), VeVideoDem()
    app = tao_app(kho, ky_thuat=kt, ve_anh=va, ve_video=vv, sinh_asset=SinhAssetGia())
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
    for d in ("breakdown", "prompt-drama", "dan-canh", "dan-canh/duyet"):
        goi(f"/api/tap/D1/C1/dong/0/{d}", "POST")
    p1 = next(c for c in kho.doc("D1", "C1")["dong"][0]["canh"] if c.get("pm") == "P001")["id"]
    sid = [x["sid"] for x in goi(f"/api/tap/D1/C1/canh/{p1}/shot")]
    yield {"url": url, "goi": goi, "kho": kho, "kt": kt, "va": va, "p1": p1, "sid": sid,
           "goc": f"/api/tap/D1/C1/canh/{p1}/shot/"}
    sv.should_exit = True
    th.join(5)


def _sh(may):
    c = next(c for c in may["kho"].doc("D1", "C1")["dong"][0]["canh"] if c.get("id") == may["p1"])
    return json.loads(c["sh"])


def _gui(pg):
    """(cách, đuôi đường, thân) các POST/PATCH trang gửi cho clip — đúng thứ tự."""
    ds = []
    pg.on("request", lambda r: r.method in ("POST", "PATCH") and "/canh/" in r.url and ds.append(
        (r.method, r.url.split("/canh/", 1)[1], r.post_data_json if r.post_data else None)))
    return ds


def _mo_clip(chrome, may, loi):
    pg = _mo(chrome.new_context(viewport={"width": 1500, "height": 1000}), may, loi)
    pg.click("#mSb")
    pg.evaluate("doiMan_chuong('C1')")
    pg.click(".tc:has(.ma:text-is('P001'))")
    pg.wait_for_selector("#theShot textarea[data-sua]")
    assert pg.locator("#theShot .buoc").count() == len(may["sid"]) >= 2
    return pg


def _chup(the, ten):
    thu = os.getenv("CHUP_SUA_SHOT")
    if thu:
        Path(thu).mkdir(parents=True, exist_ok=True)
        the.screenshot(path=str(Path(thu) / ten))


def test_luu_loi_sua_sua_tay_tieng_anh_sua_anh_quay_lai_xoa(chrome, may):
    g, s1 = may["goi"], may["sid"][0]
    g(may["goc"] + s1 + "/anh", "POST")              # shot 1 có ảnh, shot 2 chưa
    loi = []
    pg = _mo_clip(chrome, may, loi)
    gui = _gui(pg)
    the1, the2 = pg.locator("#theShot .buoc").nth(0), pg.locator("#theShot .buoc").nth(1)
    nut1, nut2 = the1.locator("button[data-sua-anh]"), the2.locator("button[data-sua-anh]")

    # ── chưa có lời sửa: Sửa ảnh này tắt, nói vì sao; chưa có ô tiếng Anh ──
    assert nut1.is_disabled() and nut1.get_attribute("title") == "Lưu lời sửa trước"
    assert nut2.is_disabled() and nut2.get_attribute("title") == "Shot chưa có ảnh"
    assert the1.locator("[data-sua-en]").count() == 0 and the1.locator("[data-quay]").count() == 0

    # ── gõ tiếng Việt, Lưu → máy dịch, thấy câu tiếng Anh, nút bật, dòng nhắc hiện ──
    the1.locator("textarea[data-sua]").fill("Nia đang khóc, nước mắt trên má")
    the1.locator("button[data-luu-sua]").click()
    assert _cho(lambda: the1.locator("[data-sua-en]").count() == 1, 10, pg=pg)
    assert the1.locator("[data-sua-en]").inner_text() == DICH
    assert ("POST", f"{may['p1']}/shot/{s1}/sua", {"sua": "Nia đang khóc, nước mắt trên má"}) in gui
    assert len(may["kt"].sua) == 1
    assert (_sh(may)[0]["sua"], _sh(may)[0]["sua_en"]) == ("Nia đang khóc, nước mắt trên má", DICH)
    assert _cho(lambda: nut1.is_enabled(), 5, pg=pg)
    assert "Vẽ lại ảnh / Gen video sẽ dùng lời sửa này" in the1.inner_text()
    assert nut2.is_disabled(), "shot 2 chưa có ảnh"
    _chup(the1, "1_da_luu_loi_sua.png")

    # ── chữ gõ dở ở shot 2 không mất khi thẻ shot vẽ lại (hỏi video 20 s một lần) ──
    the2.locator("textarea[data-sua]").fill("chỉ có Nia")
    pg.evaluate("napShot(canhTheoMa(canhDangMo))")
    pg.wait_for_timeout(500)
    assert the2.locator("textarea[data-sua]").input_value() == "chỉ có Nia"

    # ── sửa tay câu tiếng Anh rồi bấm THẲNG Sửa ảnh này: PATCH câu mới tới trước, cú bấm không rơi ──
    n_ve = len(may["va"].goi)
    the1.locator("[data-sua-en]").click()
    pg.keyboard.press("Control+A")
    pg.keyboard.type("Nia is sobbing quietly.")
    nut1.click()
    assert _cho(lambda: any(d[1].endswith(f"/shot/{s1}/sua-anh") for d in gui), 10, pg=pg), gui
    i_sua = next(i for i, d in enumerate(gui) if d[1].endswith("/sua-anh"))
    i_patch = [i for i, d in enumerate(gui) if d[0] == "PATCH"
               and json.loads(d[2]["truong"]["sh"])[0].get("sua_en") == "Nia is sobbing quietly."]
    assert i_patch and i_patch[0] < i_sua, gui
    assert _sh(may)[0]["sua_en"] == "Nia is sobbing quietly."
    assert _cho(lambda: len(may["va"].goi) == n_ve + 1, 15, pg=pg), "máy chủ vẽ đúng một lượt sửa"

    # ── có bản cũ → Quay lại ảnh trước; bấm thì đổi ảnh trên thẻ ──
    quay = the1.locator("button[data-quay='anh']")
    assert _cho(lambda: quay.count() == 1 and quay.is_enabled(), 15, pg=pg)
    assert the1.locator("button[data-quay='video']").count() == 0, "chưa có video cũ"
    _chup(the1, "2_sau_sua_anh.png")
    # `?v=` của ảnh là giờ sửa file tính theo GIÂY: đổi trong cùng giây với lượt vẽ thì URL chưa đổi và
    # trình duyệt hiện ảnh cũ trong bộ nhớ đệm. Người thật không bấm nhanh vậy (sửa ảnh mất 45–110 s).
    src = the1.locator(".khung-to img").get_attribute("src")
    pg.wait_for_timeout(1100)
    quay.click()
    assert _cho(lambda: ("POST", f"{may['p1']}/shot/{s1}/quay-lai", {"loai": "anh"}) in gui, 5, pg=pg), gui
    assert _cho(lambda: the1.locator(".khung-to img").get_attribute("src") not in (None, src), 10, pg=pg)
    assert _cho(lambda: quay.count() == 1 and quay.is_enabled(), 10, pg=pg), "bấm lần nữa là về lại"
    pg.wait_for_timeout(1100)
    quay.click()
    assert _cho(lambda: sum(d[1].endswith("/quay-lai") for d in gui) == 2, 5, pg=pg), gui
    assert _cho(lambda: the1.locator(".khung-to img").get_attribute("src") != src, 10, pg=pg)

    # ── chữ người gõ không thành HTML (ô tiếng Việt vẽ lại từ kho) ──
    doc = 'Nia khóc </textarea><b id="vo">x</b>'
    the1.locator("textarea[data-sua]").fill(doc)
    the1.locator("button[data-luu-sua]").click()
    assert _cho(lambda: _sh(may)[0].get("sua") == doc, 10, pg=pg)
    pg.evaluate("napShot(canhTheoMa(canhDangMo))")
    assert _cho(lambda: the1.locator("textarea[data-sua]").input_value() == doc, 10, pg=pg)
    assert pg.locator("#vo").count() == 0

    # ── xoá = lưu rỗng: hết câu tiếng Anh, Sửa ảnh này tắt lại ──
    the1.locator("textarea[data-sua]").fill("")
    the1.locator("button[data-luu-sua]").click()
    assert _cho(lambda: the1.locator("[data-sua-en]").count() == 0, 10, pg=pg)
    assert "sua" not in _sh(may)[0] and "sua_en" not in _sh(may)[0]
    assert nut1.is_disabled() and nut1.get_attribute("title") == "Lưu lời sửa trước"
    assert not loi, loi


def test_quay_lai_video_truoc_hien_khi_co_video_cu(chrome, may):
    g, s1 = may["goi"], may["sid"][0]
    goc = may["goc"] + s1
    g(goc + "/anh", "POST")
    g(goc + "/duyet", "POST")
    for _ in range(2):                                # gen video hai lần: bản đầu thành bản cũ
        g(goc + "/video", "POST", {})
        g(goc + "/video-kiem", "POST")
    tt = next(x for x in g(f"/api/tap/D1/C1/canh/{may['p1']}/shot") if x["sid"] == s1)
    assert tt["video_cu"] and not tt["anh_cu"], tt

    loi = []
    pg = _mo_clip(chrome, may, loi)
    gui = _gui(pg)
    the1 = pg.locator("#theShot .buoc").nth(0)
    nut = the1.locator("button[data-quay='video']")
    assert _cho(lambda: nut.count() == 1 and nut.is_enabled(), 10, pg=pg)
    assert the1.locator("button[data-quay='anh']").count() == 0
    nut.click()
    assert _cho(lambda: ("POST", f"{may['p1']}/shot/{s1}/quay-lai", {"loai": "video"}) in gui, 5, pg=pg), gui
    assert _cho(lambda: nut.count() == 1 and nut.is_enabled(), 10, pg=pg), "bấm lần nữa là về lại"
    assert not loi, loi


def test_loi_sua_doi_co_thi_the_shot_doi_theo(chrome, may):
    """haint 03/11: lời sửa đổi cỡ thì nhãn cỡ trên thẻ shot đổi theo, thông báo ghi ô đã đổi."""
    co0 = _sh(may)[0]["co"]
    moi = "ECU" if co0 != "ECU" else "CU"
    may["kt"].doi = {"co": moi, "lap": "Nia's eyes fill the frame"}
    loi = []
    pg = _mo_clip(chrome, may, loi)
    the1 = pg.locator("#theShot .buoc").nth(0)
    nhan = {"ECU": "Extreme close-up", "CU": "Close-up"}[moi]
    assert nhan not in the1.inner_text()
    the1.locator("textarea[data-sua]").fill("đổi thành đặc tả mắt Nia")
    the1.locator("button[data-luu-sua]").click()
    assert _cho(lambda: "Đã đổi: cỡ" in pg.inner_text("#toast"), 10, pg=pg)
    assert f"→ {nhan}" in pg.inner_text("#toast") and "vẽ lại rồi duyệt" in pg.inner_text("#toast")
    assert _sh(may)[0]["co"] == moi
    assert _cho(lambda: nhan in the1.inner_text(), 10, pg=pg), "thẻ shot đổi theo ô mới"
    _chup(the1, "3_doi_co.png")
    assert not loi, loi
