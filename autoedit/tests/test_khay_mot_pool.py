r"""GỘP KHAY VỀ MỘT POOL — phù hợp trước, không phù hợp sau (user chốt 13/09).

User: *"tôi cần sửa UI hiện tại vì tách thành 3 phần ref/envato/PP đang không có
ý nghĩa vì sâu bên trong cũng có nút sorting rồi. Giờ gộp chung 1 pool, video phù
hợp đưa lên trước, không phù hợp cho ra sau."*

Mockup đối chiếu: `scratchpad/ui_mot_pool.html` (khối `SAU` cạnh khối `TRƯỚC`).

VÌ SAO CHIA CỘT LÀ CHIA HAI LẦN — 4 dải dọc hẹp (`of-dai-ref|envato|stock|rec`)
buộc mắt quét 4 chỗ, mà thẻ TỐT NHẤT của miếng có thể nằm ở cột thứ tư; trong khi
popup review đã có nút lọc nguồn (`Tất cả N · Ref · Envato · Pexels · Pixabay`,
việc E 09/09) làm đúng việc đó rồi.

THỨ TỰ KHÔNG SẮP LẠI Ở GIAO DIỆN: `xep_3_tang` (QĐ15) đã trả khay theo
`A + C + B + còn` — A đúng người + đúng vật, C cảnh cận đúng vật, B đúng người
vật chung, "–" máy không lấy. Pool chỉ vẽ NGUYÊN THỨ TỰ ĐÓ; sắp lại ở JS là đặt
luật lần thứ hai ở chỗ không đo được (NT4 + Karpathy #3).

Hai thứ MỚI phải có vì gộp cột:
  1. chip NGUỒN trên từng thẻ — bỏ cột thì thẻ phải tự nói nó từ kho nào;
  2. vạch "máy không tự lấy" trước thẻ B/– đầu tiên — ranh giới tầng B để trống
     (chốt 13/09) phải nhìn thấy được, không thì người dựng tưởng máy đã chọn.

Clip ĐANG DÙNG: bản 4 cột nhấc nó lên đầu khu (06/09 — "bấm footage nào trên
timeline thì thấy ngay nguồn của nó"). Pool KHÔNG nhấc: nhấc là phá thứ tự phù
hợp mà user vừa yêu cầu. Thay bằng CUỘN TỚI nó — vẫn thấy ngay, thứ tự còn nguyên.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1] / "autoedit" / "web" / "static" / "index.html"


def _h() -> str:
    return GOC.read_text(encoding="utf-8")


def _ham(ten: str) -> str:
    """Nguyên văn một hàm JS trong index.html (khớp ngoặc) — khuôn của
    test_preview_trinh_duyet.py: nạp ĐÚNG code đang ship, không chép lại."""
    src = _h()
    m = re.search(rf"^function\s+{re.escape(ten)}\s*\(", src, re.M)
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


# ───────────────────────────── cấu trúc HTML ─────────────────────────────

def test_bon_dai_nguon_DA_GO():
    h = _h()
    for cu in ("of-dai-ref", "of-dai-envato", "of-dai-stock", "of-dai-rec",
               "of-n-ref", "of-n-envato", "of-n-stock", "of-n-rec"):
        assert cu not in h, f"{cu} vẫn còn — khay chưa gộp"


def test_co_MOT_pool_va_dong_dem_tang():
    h = _h()
    assert 'id="of-pool"' in h, "thiếu pool gộp"
    assert h.count('id="of-pool"') == 1, "pool phải là DUY NHẤT"
    assert 'id="of-tally"' in h, "thiếu dòng đếm tầng/nguồn"


def test_pool_la_LUOI_khong_phai_dai_doc():
    """4 cột hẹp thành 1 lưới nhiều thẻ mỗi hàng. Số lấy từ mockup ui_mot_pool.html."""
    h = _h()
    m = re.search(r"#of-pool\{([^}]*)\}", h)
    assert m, "thiếu CSS #of-pool"
    css = m.group(1)
    assert "grid" in css and "auto-fill" in css, css
    assert "minmax(132px" in css, "mockup chốt minmax(132px, 1fr)"


def test_chip_nguon_co_trong_css_va_du_mau():
    h = _h()
    assert ".of-uv .ng{" in h, "thiếu chip nguồn trên thẻ"
    m = re.search(r"OF_MAU_NG\s*=\s*\{([^}]*)\}", h)
    assert m, "thiếu bảng màu nguồn"
    for ng in ("ref", "envato", "pexels", "pixabay", "kho", "aigen"):
        assert ng in m.group(1), f"thiếu màu nguồn {ng}"


# ───────────────────────── chạy thật trong Chrome ─────────────────────────

def _hang_const(ten: str) -> str:
    """Nguyên văn khai báo `const <ten> = {...}` trong index.html.

    Nạp cả nó vào trang thử: bảng màu nguồn nằm NGOÀI hàm, mà thẻ đọc nó lúc vẽ —
    không nạp thì trang thử ném ReferenceError trong khi bản ship vẫn chạy.
    """
    src = _h()
    m = re.search(rf"^const {re.escape(ten)} = \{{.*?\}}$", src, re.M | re.S)
    assert m, f"không thấy const {ten}"
    return m.group(0)


TRANG = """<!doctype html><meta charset="utf-8">
<div id="of-khay"><div id="of-tally"></div><div id="of-pool"></div></div>
<script>
__MAU__
let OF_PHA = 2, OF_HCHON = 0, OF_CHON = 0, OF_TIM_KQ = null, OF_KHOA_SUA = false
const OF_HONG = new Set()
const K = [{uv: __UV__, chon: __CHON__}]
function ofHinh() { return K }
function ofK() { return K }
function ofUvLap() { return false }
function ofAnh(u) { return u.url_anh || '' }
function ofVid(u) { return u.url_video || '' }
function esc(s) { return String(s == null ? '' : s) }
function toastOf() {}
function ofChup() {}
function ofLuu() {}
function ofVeAll() {}
function ofReview() {}
function ofBaoChiXem() {}
__HAM__
</script>"""

UV = [
    {"id": "e1", "nguon": "envato", "tieu_de": "Senior Woman Sleeping", "tang": "A"},
    {"id": "r1", "nguon": "ref", "tieu_de": "elderly couple sleep", "tang": "A"},
    {"id": "p1", "nguon": "pexels", "tieu_de": "close up hands", "tang": "C"},
    {"id": "x1", "nguon": "pixabay", "tieu_de": "bed pillow white", "tang": "B"},
    {"id": "k1", "nguon": "kho", "tieu_de": "cat sleeping", "tang": "-"},
]


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


def _trang(chrome, tmp_path, uv=None, chon=0):
    html = (TRANG.replace("__HAM__", _ham("ofVeKhay"))
                 .replace("__MAU__", _hang_const("OF_MAU_NG"))
                 .replace("__UV__", json.dumps(uv if uv is not None else UV))
                 .replace("__CHON__", str(chon)))
    f = tmp_path / "t.html"
    f.write_text(html, encoding="utf-8")
    pg = chrome.new_page()
    loi: list[str] = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(f.as_uri())
    return pg, loi


def test_pool_ve_DUNG_THU_TU_may_cham(chrome, tmp_path):
    pg, loi = _trang(chrome, tmp_path)
    pg.evaluate("ofVeKhay()")
    tang = pg.eval_on_selector_all("#of-pool .of-uv .tang",
                                   "e => e.map(x => x.textContent)")
    assert tang == ["A", "A", "C", "B", "–"], tang
    assert loi == [], loi
    pg.close()


def test_moi_the_co_chip_NGUON(chrome, tmp_path):
    pg, loi = _trang(chrome, tmp_path)
    pg.evaluate("ofVeKhay()")
    ng = pg.eval_on_selector_all("#of-pool .of-uv .ng",
                                 "e => e.map(x => x.textContent)")
    assert ng == ["envato", "ref", "pexels", "pixabay", "kho"], ng
    assert loi == [], loi
    pg.close()


def test_vach_ranh_truoc_the_MAY_KHONG_TU_LAY(chrome, tmp_path):
    """Tầng B để trống (13/09) — ranh giới phải nhìn thấy."""
    pg, loi = _trang(chrome, tmp_path)
    pg.evaluate("ofVeKhay()")
    n = pg.eval_on_selector_all(
        "#of-pool > *",
        "e => e.map(x => x.classList.contains('moc') ? 'MOC'"
        " : x.querySelector('.tang').textContent)")
    assert n == ["A", "A", "C", "MOC", "B", "–"], n
    assert loi == [], loi
    pg.close()


def test_the_dang_dung_KHONG_bi_nhac_len_dau(chrome, tmp_path):
    """chon=4 (thẻ '–' cuối) — phải vẫn đứng cuối, chỉ được đánh dấu."""
    pg, loi = _trang(chrome, tmp_path, chon=4)
    pg.evaluate("ofVeKhay()")
    kq = pg.evaluate("""() => {
        const t = [...document.querySelectorAll('#of-pool .of-uv')]
        return {thu_tu: t.map(x => x.querySelector('.tang').textContent),
                dang: t.findIndex(x => x.classList.contains('dang'))}
    }""")
    assert kq["thu_tu"] == ["A", "A", "C", "B", "–"], kq
    assert kq["dang"] == 4, "thẻ đang dùng phải ở đúng chỗ, không nhấc lên đầu"
    assert loi == [], loi
    pg.close()


def test_khay_rong_khong_no_JS(chrome, tmp_path):
    pg, loi = _trang(chrome, tmp_path, uv=[])
    pg.evaluate("ofVeKhay()")
    assert pg.eval_on_selector_all("#of-pool .of-uv", "e => e.length") == 0
    assert loi == [], loi
    pg.close()
