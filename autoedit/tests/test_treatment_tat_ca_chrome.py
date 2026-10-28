"""Nút "Gen toàn bộ asset" + nhãn số dư credit (user duyệt 28/10) — test chuỗi và
test trong CHROME THẬT.

KHÔNG import từ test_treatment_bang_chrome: nhánh deploy prod không có Bảng vẽ nên
file đó không tồn tại — fixture Chrome viết ngay trong file này.
"""

from __future__ import annotations

import json
import pathlib
import re
import socket
import threading
import time
import urllib.request

import pytest

from autoedit.treatment import app as mapp
from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho
from test_treatment_drama import KICH_BAN
from test_treatment_drama_api import SinhAssetGia, VeAnhGia, VeVideoGia
from test_treatment_tat_ca import KyThuatDoVat

HTML = pathlib.Path(mapp.__file__).parent / "static" / "treatment.html"


@pytest.fixture(scope="module")
def html():
    return HTML.read_text(encoding="utf-8")


def _than(html, ten):
    i = html.index("function " + ten + "(")
    return html[i:html.index("\nfunction ", i + 1)]


def test_nhan_so_du_nam_tren_thanh_dau_trang_nen_ca_ba_man_deu_thay(html):
    assert 'id="soDu"' in html[html.index("<header>"):html.index("</header>")]


def test_so_du_hoi_moi_60_giay_va_hoi_moi_ngay_sau_moi_lan_gen(html):
    assert "setInterval(napSoDu, 60000)" in html[html.index("(async function khoiDong"):]
    for ham in ("sinhAnh", "sinhRef", "genVideo"):     # ảnh · tấm ref · video
        assert "napSoDu(1)" in _than(html, ham), ham


def test_nut_gen_toan_bo_asset_chi_nguoi_sua_thay(html):
    thanh = html[html.index('<div id="manAs"'):html.index('id="asCanvas"')]
    assert re.search(r'<button class="icon-btn chi-sua" id="nutTatCa"[^>]*onclick="genTatCa\(\)"', thanh)


# ═══════ Chrome thật: máy chủ thật + bộ máy giả (không LLM, không Seedvis, không tốn tiền) ═══════
class _Tiem:
    """Thay vai gateway: request không mang danh tính thì là owner có quyền sửa."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            co = {k for k, _ in scope["headers"]}
            them = [(k, v) for k, v in ((b"x-remote-user", b"owner"), (b"x-remote-actions", b"sua"))
                    if k not in co]
            scope = dict(scope, headers=list(scope["headers"]) + them)
        await self.app(scope, receive, send)


class VeAnhCho(VeAnhGia):
    """Ảnh của nv02 ĐỨNG CHỜ tới khi test mở cổng: trang kịp thấy việc đang chạy mà vài
    asset đã có ảnh. noi02 vẽ hỏng để có một dòng lỗi. Có số dư như Seedvis."""

    credit = 1234

    def __init__(self):
        super().__init__()
        self.cong = threading.Event()

    def gen_anh(self, prompt, dich, **kw):
        if "nv02" in dich.name:
            self.cong.wait(30)
        if "noi02" in dich.name:
            raise RuntimeError("Seedvis 502 <thử>")
        return super().gen_anh(prompt, dich, **kw)


class VeVideoSoDu(VeVideoGia):
    credit = 7888
    # GPT Image 2 đang bảo trì -> trang phải NÓI ra và để người chọn Nano Banana Pro.
    danh_sach = [{"id": "gpt-image-2", "label": "GPT Image 2", "type": "image", "status": "maintenance"},
                 {"id": "GEM_PIX_2", "label": "Nano Banana Pro", "type": "image", "status": "active"}]


@pytest.fixture(scope="module")
def chrome():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception as exc:  # noqa: BLE001 — máy không có Chrome thì bỏ qua
            pytest.skip(f"không mở được Chrome: {str(exc)[:80]}")
        yield b
        b.close()


@pytest.fixture
def may(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    kho = Kho(tmp_path / "k.db")
    va, vv = VeAnhCho(), VeVideoSoDu()
    app = tao_app(kho, ky_thuat=KyThuatDoVat(), ve_anh=va, ve_video=vv, sinh_asset=SinhAssetGia())
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
    goi("/api/tap/D1/drama", "POST", {"text": KICH_BAN})
    yield {"url": url, "goi": goi, "kho": kho, "va": va, "vv": vv}
    va.cong.set()
    sv.should_exit = True
    th.join(5)


def _cho(dk, giay=20.0, pg=None):
    """`pg`: chờ bằng trang, vì Playwright sync chỉ xử lý sự kiện (hộp thoại, request)
    trong lúc gọi nó — `time.sleep` thì hộp confirm treo, danh sách request đứng im."""
    het = time.time() + giay
    while time.time() < het:
        if dk():
            return True
        pg.wait_for_timeout(100) if pg else time.sleep(0.1)
    return False


def _mo(ctx, may, loi):
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(may["url"])
    pg.wait_for_selector("#nutTap", state="attached")
    _cho(lambda: pg.evaluate("TAP_MA") == "D1", 10)
    return pg


# Màu của một biến CSS sau khi trình duyệt tính — không ghi cứng mã màu, đổi nền vẫn đúng.
MAU = ("v => { var d = document.createElement('span'); d.style.color = 'var(' + v + ')';"
       " document.body.appendChild(d); var c = getComputedStyle(d).color; d.remove(); return c; }")


def test_so_du_tren_thanh_dau_trang_mau_theo_so_clip_grok(chrome, may):
    loi = []
    ctx = chrome.new_context(viewport={"width": 1500, "height": 900})
    pg = _mo(ctx, may, loi)
    # Máy chủ thật: ảnh và video khác số -> hai vế.
    assert _cho(lambda: pg.inner_text("#soDu") == "ảnh 1.234 · video 7.888 cr", 5), pg.inner_text("#soDu")
    mau = lambda: pg.evaluate("getComputedStyle(document.getElementById('soDu')).color")  # noqa: E731
    xam = pg.evaluate("getComputedStyle(document.getElementById('aiToi')).color")
    assert mau() == xam
    # Các ca còn lại: chặn route để khỏi đợi bộ nhớ 10 s của máy chủ — đây soát TRANG vẽ.
    tra = {}
    pg.route("**/api/so-du*", lambda r: r.fulfill(json=tra))
    for so, chu, mau_ra, title in [
            ({"anh": 7888, "video": 7888, "chung": True}, "Seedvis · 7.888 cr · ≈ 73 clip Grok", xam, ""),
            ({"anh": 900, "video": 900, "chung": True}, "Seedvis · 900 cr · ≈ 8 clip Grok",
             pg.evaluate(MAU, "--warn"), ""),
            ({"anh": 50, "video": 50, "chung": True}, "Seedvis · 50 cr · ≈ 0 clip Grok",
             pg.evaluate(MAU, "--bad"), "Không đủ 1 clip Grok — báo Owner nạp"),
            ({"anh": 9999, "video": 100, "chung": False}, "ảnh 9.999 · video 100 cr",
             pg.evaluate(MAU, "--bad"), "Không đủ 1 clip Grok — báo Owner nạp"),
            ({"anh": None, "video": 7888, "chung": False}, "video 7.888 cr", xam, ""),
            ({"anh": None, "video": None, "chung": True}, "", xam, "")]:
        tra.clear()
        tra.update(so)
        pg.evaluate("napSoDu(1)")
        assert _cho(lambda: pg.inner_text("#soDu") == chu, 5), (so, pg.inner_text("#soDu"))
        assert mau() == mau_ra and pg.get_attribute("#soDu", "title") == title, (so, mau())
    # Hỏi hỏng thì GIỮ số cũ.
    tra.update({"anh": 7888, "video": 7888, "chung": True})
    pg.evaluate("napSoDu(1)")
    assert _cho(lambda: "7.888" in pg.inner_text("#soDu"), 5)
    pg.unroute("**/api/so-du*")
    pg.route("**/api/so-du*", lambda r: r.fulfill(status=502, body="hong"))
    pg.evaluate("napSoDu(1)")
    pg.wait_for_timeout(400)
    assert "7.888" in pg.inner_text("#soDu")
    for m in ("mSb", "mAs", "mKb"):                       # cả ba màn
        pg.click("#" + m)
        assert pg.is_visible("#soDu"), m
    # Vai chỉ xem: thấy số dư, không thấy nút.
    ctx2 = chrome.new_context(extra_http_headers={"X-Remote-User": "xem", "X-Remote-Actions": ""})
    pg2 = _mo(ctx2, may, loi)
    pg2.click("#mAs")
    assert _cho(lambda: "7.888" in pg2.inner_text("#soDu"), 5) and not pg2.is_visible("#nutTatCa")
    assert not loi, loi


def test_gen_toan_bo_asset_tu_bam_toi_xong(chrome, may):
    g, va = may["goi"], may["va"]
    loi, hop, gui, hoi, moi = [], [], [], [], []
    ctx = chrome.new_context(viewport={"width": 1500, "height": 900})
    tra = {"v": False}

    def tl(d):
        hop.append(d.message)
        d.accept() if tra["v"] else d.dismiss()
    pg = _mo(ctx, may, loi)
    pg.on("dialog", tl)
    pg.on("request", lambda r: "/so/tat-ca" in r.url and (gui if r.method == "POST" else hoi).append(
        (time.time(), r.post_data)))
    pg.on("request", lambda r: "/api/so-du?moi=1" in r.url and moi.append(r.url))
    pg.click("#mAs")
    assert pg.is_visible("#nutTatCa")
    cu = _mo(ctx, may, loi)                 # tab thứ hai mở trước khi chạy, đứng ở màn Kịch bản
    for t in (pg, cu):
        t.evaluate("Promise.all(DS_CHUONG.map(function(c){ return taiLaiChuong(c.ma); }))")
    dung_do01 = "dungCanhTap().filter(function(c){ return (c.ts || []).indexOf('do01') >= 0; }).length"
    assert pg.evaluate(dung_do01) == 0 and cu.evaluate(dung_do01) == 0

    # ── hộp xác nhận nói đủ việc, tiền, giờ, số dư; bảo trì thì NÓI và để người chọn ──
    k = g("/api/tap/D1/so/tat-ca")["ke_hoach"]
    pg.click("#nutTatCa")
    assert _cho(lambda: hop, 5, pg=pg)
    for chu in ("tập D1", "tìm đồ vật", f"viết mô tả {k['mo_ta']} asset",
                f"vẽ {k['anh']} ảnh: người {k['nhan_vat']} · bộ đồ phụ {k['phu']} · nơi {k['noi']} · "
                f"đồ {k['dao_cu']}",
                "GPT Image 2 đang bảo trì — bấm OK là vẽ bằng Nano Banana Pro",
                f"≈ {k['credit_du_phong']} cr · ≈ {k['phut']} phút",
                "Số dư: ảnh 1.234 · video 7.888 cr", "đóng tab không mất"):
        assert chu in hop[-1], (chu, hop[-1])
    assert not gui and pg.is_enabled("#nutTatCa") and pg.inner_text("#nutTatCa") == "Gen toàn bộ asset"

    # ── đồng ý: gửi model dự phòng, tiến độ hiện, tab người khác cũng thấy ──
    tra["v"] = True
    pg.click("#nutTatCa")
    assert _cho(lambda: gui, 5, pg=pg) and json.loads(gui[0][1]) == {"model": "GEM_PIX_2"}
    assert _cho(lambda: "Gen toàn bộ asset ·" in pg.inner_text("#viecTatCa"), 8), pg.inner_text("#viecTatCa")
    ctx2 = chrome.new_context(viewport={"width": 1500, "height": 900},
                              extra_http_headers={"X-Remote-User": "lan", "X-Remote-Actions": "sua"})
    pg2 = _mo(ctx2, may, loi)
    pg2.click("#mAs")
    assert _cho(lambda: "owner bấm" in pg2.inner_text("#viecTatCa"), 8), pg2.inner_text("#viecTatCa")

    # ── asset mới chưa lưu không bị lượt nạp lại nuốt; lưu lúc đang chạy thì GIỮ hộp ──
    pg.click("#manAs button:has-text('+ nhân vật')")
    pg.fill("#hopCanh input[data-so]", "Người mới")
    so_img = "document.querySelectorAll('#asCanvas .tc img').length"
    assert _cho(lambda: pg.evaluate(so_img) >= 1, 15), "ảnh phải hiện dần trong lúc chạy"
    assert "Gen toàn bộ asset ·" in pg.inner_text("#viecTatCa")
    # Máy gán đồ vật vào `ts` của clip: tab phải nạp lại CHƯƠNG ngay khi qua bước tìm đồ vật —
    # DU cũ thì bấm chip asset trong hộp cảnh là PATCH ts cũ, xoá do01 khỏi clip.
    assert pg.evaluate(dung_do01) == 2
    assert "dùng ở 2 cảnh" in pg.locator("#asCanvas .tc", has_text="hộp nhẫn").inner_text()
    assert pg.evaluate("SO.some(function(x){ return x.loai === 'nhan_vat' && !x.ten; })")
    pg.locator("#hopCanh #luuSo").click()
    assert _cho(lambda: "đợi xong rồi lưu" in pg.inner_text("#toast"), 5), pg.inner_text("#toast")
    pg.wait_for_timeout(300)
    assert pg.is_visible("#hopCanh input[data-so]"), "lưu hỏng mà đóng hộp là mất chữ vừa gõ"
    assert pg.input_value("#hopCanh input[data-so]") == "Người mới"
    pg.locator("#hopCanh button", has_text="✕").click()

    # ── vào ra màn Asset không đẻ thêm vòng hỏi (5 s một lượt) ──
    for _ in range(3):
        pg.click("#mSb")
        pg.click("#mAs")
    t0 = time.time()
    pg.wait_for_timeout(10500)
    assert len([t for t, _ in hoi if t >= t0]) <= 3, len([t for t, _ in hoi if t >= t0])

    # ── xong: nạp lại sổ, tóm tắt, lỗi mở sẵn, hỏi lại số dư, thôi hỏi ──
    n_moi = len(moi)
    va.cong.set()
    assert _cho(lambda: "Lần gần nhất: xong" in pg.inner_text("#viecTatCa"), 20), pg.inner_text("#viecTatCa")
    v = g("/api/tap/D1/so/tat-ca")["viec"]
    assert pg.inner_text("#viecTatCa") == f"Lần gần nhất: xong {v['xong']}/{v['tong']} · 1 lỗi"
    assert pg.evaluate("document.querySelector('#ketTatCa details').open")
    assert "noi02 · " in pg.inner_text("#ketTatCa") and ": Seedvis 502 <thử>" in pg.inner_text("#ketTatCa")
    assert f"xong: {v['xong']}/{v['tong']} asset · tìm thêm 1 đồ vật · 1 lỗi" in pg.inner_text("#toast")
    assert _cho(lambda: len(moi) > n_moi, 5, pg=pg), "xong thì hỏi lại số dư"
    co_ref = sum(1 for x in g("/api/tap/D1/so") if x.get("ref"))
    assert pg.evaluate(so_img) == co_ref, (pg.evaluate(so_img), co_ref)
    assert pg.evaluate("SO.some(function(x){ return x.ma === 'do01'; })"), "đồ vật máy vừa thêm phải vào sổ của tab"
    assert "dùng ở 2 cảnh" in pg.locator("#asCanvas .tc", has_text="hộp nhẫn").inner_text()
    # Tab mở TỪ TRƯỚC lượt chạy, không theo dõi: vào màn Asset lúc đã xong cũng phải đồng bộ.
    cu.click("#mAs")
    assert _cho(lambda: "Lần gần nhất: xong" in cu.inner_text("#viecTatCa"), 5)
    assert _cho(lambda: cu.evaluate(dung_do01) == 2, 5, pg=cu), cu.evaluate(dung_do01)
    assert "dùng ở 2 cảnh" in cu.locator("#asCanvas .tc", has_text="hộp nhẫn").inner_text()
    n = len(hoi)
    pg.wait_for_timeout(6000)
    assert len(hoi) == n, "xong thì thôi hỏi"

    # ── mở lại: kết quả lần gần nhất vẫn còn, lỗi GẤP lại ──
    pg3 = _mo(ctx, may, loi)
    pg3.click("#mAs")
    assert _cho(lambda: "Lần gần nhất: xong" in pg3.inner_text("#viecTatCa"), 5)
    assert pg3.evaluate("document.querySelector('#ketTatCa details').open") is False
    pg3.click("#ketTatCa summary")
    assert "Seedvis 502 <thử>" in pg3.inner_text("#ketTatCa")

    # ── vẽ lẻ một tấm ref cũng hỏi lại số dư ──
    n_moi = len(moi)
    pg.evaluate("sinhRef('noi01')")
    assert _cho(lambda: len(moi) > n_moi, 10, pg=pg), "vẽ ref xong phải hỏi lại số dư"
    assert not loi, loi


def test_hop_xac_nhan_theo_model_general_khong_ghi_cung_gpt(chrome, may):
    """User báo 28/10: đổi model ở General mà tool vẫn vẽ GPT2. Tên model, tiền và model
    gửi đi đều theo `model.id` máy chủ trả; bảo trì thì đổi sang `du_phong` — bất kể là ai."""
    g, va, vv = may["goi"], may["va"], may["vv"]
    va.model_ket = "GEM_PIX_2"                                   # General: Nano Banana Pro
    vv.danh_sach = [{"id": "gpt-image-2", "label": "GPT Image 2", "type": "image", "status": "active"},
                    {"id": "GEM_PIX_2", "label": "Nano Banana Pro", "type": "image", "status": "maintenance"}]
    loi, hop, gui = [], [], []
    ctx = chrome.new_context(viewport={"width": 1500, "height": 900})
    pg = _mo(ctx, may, loi)
    pg.on("dialog", lambda d: (hop.append(d.message), d.accept()))
    pg.on("request", lambda r: "/so/tat-ca" in r.url and r.method == "POST" and gui.append(r.post_data))
    r = g("/api/tap/D1/so/tat-ca")
    assert r["model"] == {"id": "GEM_PIX_2", "du_phong": "gpt-image-2", "bao_tri": True}
    pg.click("#mAs")
    pg.click("#nutTatCa")
    assert _cho(lambda: gui, 5, pg=pg), hop
    assert "Nano Banana Pro đang bảo trì — bấm OK là vẽ bằng GPT Image 2" in hop[-1], hop[-1]
    assert f"≈ {r['ke_hoach']['credit_du_phong']} cr" in hop[-1], (r["ke_hoach"], hop[-1])
    assert json.loads(gui[0]) == {"model": "gpt-image-2"}
    va.cong.set()
    assert not loi, loi
