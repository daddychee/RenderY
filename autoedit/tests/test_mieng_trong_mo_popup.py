r"""MIẾNG CHƯA CÓ HÌNH: double-click không mở được popup (user báo 17/09).

User: *"Đối với khối chưa được đổ footage thì không thể click đúp vào khối đó để
hút thêm source phù hợp"*.

`ofVeTL` gắn dblclick cho từng miếng, nhưng chặn ngay ở cửa:

    const u = ofUv(h)
    if (!u) { toastOf('Shot chưa có hình — chọn từ khay trước'); return }

Trớ trêu: popup ĐÓ CHÍNH LÀ chỗ có ô tra Library và nút ⛏ Hút thêm (việc E,
09/09 — user chốt khay tra cứu "phải nằm trong phần popup mở ra click đúp vào
video"). Miếng trống là lúc cần hút NHẤT thì lại không vào được.

Lưới trong popup đã sẵn sàng cho ca này: `ofTimVe` có nhánh "Miếng này chưa có ứng
viên nào — gõ từ khoá để tra Library hoặc bấm ⛏ Hút thêm". Chỉ `ofReview` là chưa
chịu mở khi không có clip (đọc thẳng `u.tieu_de`, `ofVid(u)`).

Kèm theo: ô trống giữa màn còn ghi "chọn từ 4 khu bên phải" — sót từ hôm gộp khay
về MỘT pool (13/09), nay chỉ còn một khay.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1] / "autoedit" / "web" / "static" / "index.html"


def _h() -> str:
    return GOC.read_text(encoding="utf-8")


def _ham(ten: str) -> str:
    src = _h()
    m = re.search(rf"^(?:async )?function\s+{re.escape(ten)}\s*\(", src, re.M)
    assert m, f"không thấy hàm {ten}"
    i = src.index("{", m.end() - 1)
    sau, muc = i, 0
    while sau < len(src):
        if src[sau] == "{":
            muc += 1
        elif src[sau] == "}":
            muc -= 1
            if muc == 0:
                break
        sau += 1
    return src[m.start():sau + 1]


def _dong(dau: str) -> str:
    for d in _h().splitlines():
        if d.strip().startswith(dau):
            return d.strip()
    raise AssertionError(f"không thấy dòng «{dau}»")


# ───────────────────────── đọc mã nguồn ─────────────────────────

def test_dblclick_mieng_TRONG_khong_con_bi_chan():
    h = _ham("ofVeTL")
    assert "Shot chưa có hình — chọn từ khay trước" not in h, \
        "vẫn chặn miếng trống bằng toast"
    assert "ofReview(" in h, "dblclick không còn mở popup nữa"


def test_o_trong_khong_con_ghi_4_khu():
    """Gộp khay về một pool (13/09) rồi thì không còn '4 khu'."""
    assert "4 khu bên phải" not in _h(), "chữ cũ sót lại sau khi gộp pool"


# ───────────────────── chạy thật trong Chrome ─────────────────────

TRANG = """<!doctype html><meta charset="utf-8">
<div id="of-trim-cs"><div id="of-rv-ten"></div>
  <video id="of-rv-video" muted loop playsinline controls></video>
  <img id="of-rv-anh" hidden>
  <div id="of-trim"><div id="of-trim-thanh"><div id="of-trim-vung"></div>
    <div class="tay" id="of-tay-a"></div><div class="tay" id="of-tay-b"></div>
    <div id="of-trim-ph"></div></div></div>
  <div id="of-trim-so"></div><div id="of-rv-meta"></div>
  <div id="of-tim-luoi"></div><div id="of-tim-nhan"></div><div id="of-tim-loc"></div>
</div>
<script>
__DONG__
let OF_HCHON = 0, OF_TIM_KQ = null, OF_TIM_DEM = {}, OF_TIM_TRANG = 0, OF_TIM_HET = true
let OF_TIM_Q = ''
const OF_TIM_LOC = {ng: '', neo: false, dai: false, chua: false}
const OF_TIM_MAU = {ref: '#8fd0a8', envato: '#7fb2e8', pexels: '#e8b97f', pixabay: '#c9a3e0'}
const HINH = [{uv: [], chon: -1}]
function ofHinh() { return HINH }
function ofNoiTrim() {}
function ofVid(u) { return (u && u.url_video) || '' }
function ofAnh(u) { return (u && u.url_anh) || '' }
function esc(s) { return String(s == null ? '' : s) }
function ofTimDatNg() {}
function ofTimBat() {}
function ofTimSang() {}
__HAM__
</script>"""


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
def trang(chrome, tmp_path):
    html = (TRANG.replace("__HAM__", "\n".join(
                    [_ham("ofReview"), _ham("ofVeTrim"), _ham("ofRvMeta"),
                     _ham("ofTimThe"), _ham("ofTimVe")]))
                 .replace("__DONG__", "\n".join([_dong("let OF_RV = null"),
                                                 _dong("let OF_RV_TU_DO")])))
    (tmp_path / "t.html").write_text(html, encoding="utf-8")
    pg = chrome.new_page()
    loi: list[str] = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto((tmp_path / "t.html").as_uri())
    yield pg, loi
    pg.close()


def test_mo_popup_KHONG_CO_CLIP_van_chay(trang):
    pg, loi = trang
    pg.evaluate("ofReview(null)")
    pg.wait_for_timeout(500)
    assert loi == [], loi
    assert pg.evaluate("document.getElementById('of-trim-cs').classList.contains('mo')")


def test_popup_trong_AN_video_va_thanh_trim(trang):
    """Không có clip thì không được hiện khung video đen + thanh trim vô nghĩa."""
    pg, loi = trang
    pg.evaluate("ofReview(null)")
    pg.wait_for_timeout(400)
    assert pg.evaluate("document.getElementById('of-rv-video').hidden") is True
    assert pg.evaluate("document.getElementById('of-trim').hidden") is True
    assert loi == [], loi


def test_popup_trong_MOI_go_tu_khoa_hoac_hut(trang):
    """Đúng thứ người dựng cần thấy: lời mời tra Library / ⛏ Hút thêm."""
    pg, loi = trang
    pg.evaluate("ofReview(null)")
    pg.wait_for_timeout(400)
    chu = pg.eval_on_selector("#of-tim-luoi", "e => e.textContent")
    assert "Hút thêm" in chu, chu
    assert loi == [], loi


def test_van_mo_binh_thuong_khi_CO_clip(trang):
    """Không được làm hỏng đường cũ: có clip thì vẫn hiện video + thanh trim."""
    pg, loi = trang
    pg.evaluate("ofReview({id: 'pexels:1', tieu_de: 'co clip', url_video: 'v.mp4'})")
    pg.wait_for_timeout(400)
    assert pg.evaluate("document.getElementById('of-rv-video').hidden") is False
    assert pg.evaluate("document.getElementById('of-rv-ten').textContent") == "co clip"
    assert loi == [], loi
