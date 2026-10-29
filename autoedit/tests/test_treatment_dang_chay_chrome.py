"""Thanh "Đang chạy" trong CHROME THẬT (user chốt 29/10): hai người, hai tab — người này bấm,
người kia thấy thanh, nhãn trên thẻ clip, nút khoá kèm tên; xong thì tự mở và thẻ có ảnh mới.
Máy chủ thật + bộ máy giả (không LLM, không Seedvis). Fixture mượn test Generate All — file đó
có ở cả nhánh deploy lẫn dev."""

from __future__ import annotations

import threading

from test_treatment_chay_chuong_chrome import may  # noqa: F401 — fixture
from test_treatment_tat_ca_chrome import _cho, _mo, chrome  # noqa: F401 — `chrome` là fixture

THE = ".tc:has(.ma:text-is('{}'))"
NUT = "#theShot button[data-viec='anh'][data-sid='{}']"


def _lan(chrome, may, loi):
    ctx = chrome.new_context(viewport={"width": 1500, "height": 900},
                             extra_http_headers={"X-Remote-User": "lan", "X-Remote-Actions": "sua"})
    return _mo(ctx, may, loi)


def _sb(pg):
    pg.click("#mSb")
    pg.evaluate("doiMan_chuong('C1')")
    pg.wait_for_selector(THE.format("P001"))


def _nen(g, duong):
    t = threading.Thread(target=lambda: g(duong, "POST"), daemon=True)
    t.start()
    return t


def test_nguoi_khac_ve_anh_shot_thay_thanh_nhan_the_nut_khoa_xong_thi_mo_va_co_anh(chrome, may):
    g, va, kho = may["goi"], may["va"], may["kho"]
    for d in ("breakdown", "prompt-drama", "dan-canh", "dan-canh/duyet"):    # dàn cảnh vẽ ngay (td_)
        g(f"/api/tap/D1/C1/dong/0/{d}", "POST")
    p1 = next(c for c in kho.doc("D1", "C1")["dong"][0]["canh"] if c.get("pm") == "P001")["id"]
    s1, s2 = [x["sid"] for x in g(f"/api/tap/D1/C1/canh/{p1}/shot")]
    loi = []
    pg = _mo(chrome.new_context(viewport={"width": 1500, "height": 900}), may, loi)    # owner
    _sb(pg)
    pg2 = _lan(chrome, may, loi)
    _sb(pg2)
    pg2.click(THE.format("P001"))
    pg2.wait_for_selector(NUT.format(s1))
    assert pg2.is_hidden("#dangChay"), "rảnh thì không có thanh"

    # ── owner vẽ ảnh shot 1 (đứng ở cổng): lan thấy thanh, nhãn thẻ, nút shot 1 khoá kèm tên ──
    t = _nen(g, f"/api/tap/D1/C1/canh/{p1}/shot/{s1}/anh")
    assert _cho(lambda: "owner · vẽ ảnh · C1 · P001 · shot 1" in pg2.inner_text("#dangChay"), 20, pg=pg2), \
        pg2.inner_text("#dangChay")
    assert "Đang chạy" in pg2.inner_text("#dangChay")
    assert _cho(lambda: pg2.inner_text(NUT.format(s1)) == "⟳ owner đang làm…", 5, pg=pg2)
    assert pg2.is_disabled(NUT.format(s1)) and "owner đang vẽ ảnh" in pg2.get_attribute(NUT.format(s1), "title")
    assert pg2.inner_text(NUT.format(s2)) == "Vẽ ảnh" and pg2.is_enabled(NUT.format(s2)), "shot khác không dính"
    # Hộp clip phủ kín màn hình: thanh vẫn phải NHÌN THẤY được (nổi trên lớp phủ), không bị che.
    tren = pg2.evaluate("""() => { var r = document.getElementById('dangChay').getBoundingClientRect();
        var e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return !!e && !!e.closest('#dangChay'); }""")
    assert tren, "hộp clip đang mở che mất thanh Đang chạy"
    assert "owner · vẽ ảnh" in pg2.inner_text(THE.format("P001") + " .dang-lam")
    assert pg2.locator(THE.format("P002") + " .dang-lam").count() == 0
    # chính người bấm: thanh ghi "Bạn"
    assert _cho(lambda: "Bạn · vẽ ảnh" in pg.inner_text("#dangChay"), 20, pg=pg), pg.inner_text("#dangChay")

    # ── xong: thanh tắt, nút trả lại, thẻ có ảnh mới mà lan không phải F5 ──
    va.cong.set()
    t.join(10)
    assert _cho(lambda: pg2.is_hidden("#dangChay"), 10, pg=pg2), pg2.inner_text("#dangChay")
    assert pg2.inner_text(NUT.format(s1)) == "Vẽ ảnh" and pg2.is_enabled(NUT.format(s1))
    assert pg2.locator(THE.format("P001") + " .dang-lam").count() == 0
    assert _cho(lambda: pg2.locator(THE.format("P001") + " .hinh img").count() == 1, 5, pg=pg2)

    # ── lan tự bấm shot 2: thanh hiện ngay (không đợi vòng 15 giây), nút là chữ của banRon ──
    va.cong.clear()
    pg2.click(NUT.format(s2))
    assert _cho(lambda: "Bạn · vẽ ảnh" in pg2.inner_text("#dangChay"), 3, pg=pg2), pg2.inner_text("#dangChay")
    assert pg2.inner_text(NUT.format(s2)) == "Đang vẽ ảnh…"
    assert _cho(lambda: "lan · vẽ ảnh · C1 · P001 · shot 2" in pg.inner_text("#dangChay"), 20, pg=pg)
    va.cong.set()
    assert _cho(lambda: pg2.is_hidden("#dangChay"), 10, pg=pg2)
    assert _cho(lambda: pg2.inner_text(NUT.format(s2)) == "Vẽ lại ảnh", 5, pg=pg2)
    assert not loi, loi


def test_generate_all_nguoi_khac_bam_thi_nut_khoa_co_tien_do_xong_thi_mo(chrome, may):
    g, va = may["goi"], may["va"]
    loi = []
    pg2 = _lan(chrome, may, loi)
    _sb(pg2)
    assert pg2.inner_text("#nutChuong") == "Generate All" and pg2.is_enabled("#nutChuong")
    g("/api/tap/D1/C1/chay", "POST")                       # owner; ảnh shot đứng ở cổng
    assert _cho(lambda: pg2.inner_text("#nutChuong").startswith("⟳ Đang chạy"), 20, pg=pg2), \
        pg2.inner_text("#nutChuong")
    assert pg2.is_disabled("#nutChuong")
    thanh = pg2.inner_text("#dangChay")
    assert "owner · Generate All chương C1 · vẽ ảnh shot" in thanh, thanh
    assert pg2.locator("#dangChay .thanh-td").count() == 1
    va.cong.set()
    assert _cho(lambda: pg2.inner_text("#nutChuong") == "Generate All", 30, pg=pg2), pg2.inner_text("#nutChuong")
    assert pg2.is_enabled("#nutChuong") and pg2.is_hidden("#dangChay")
    assert not loi, loi
