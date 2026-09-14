r"""ADD SHOT CẮT NHẦM KHỐI — gửi giây trục VOICE cho máy chủ cắt trục TIMELINE.

User báo 14/09: *"thêm miếng ở khối này lại bị nhảy sang khối khác thêm miếng"*.

HAI TRỤC THỜI GIAN KHÁC NHAU:
  * trục VOICE    — giây trong file voice, chính là `OF_AUDIO.currentTime`;
  * trục TIMELINE — giây trên dải hình, bị ĐẨY VỀ SAU mỗi lần thêm hình thở
    (`tho_them`). `ofDoiTruoc(i)` = tổng hình thở của các khối ĐỨNG TRƯỚC khối i.

`ofAddShot` lấy thẳng giây trục voice gửi lên `/che-tai`, mà `hinh.che_tai()` so
với `hinh[].t0` — trục TIMELINE. Lệch đúng bằng `ofDoiTruoc`.

ĐO THẬT trên chương user đang làm, SH019 `h-20260911-082055` (16 khối):

    khối có tho_them  0(+5s) · 2(+1s) · 3(+9,7s) · 4 · 6 · 8 · 11 · 12 · 14
    lệch cộng dồn cuối chương            21,7s
    khối bấm E bị cắt nhầm chỗ           14/16
    vạch ở khối 4 (38,5s voice)          cắt lệch 15,7s về trước, rơi ra ngoài khối

Hai chương khác của user (`c9-…`, `e-…`) chưa thêm hình thở lần nào -> lệch 0 ->
bấm E vẫn đúng. Đó là lý do lỗi lúc có lúc không.

Trong code có sẵn `ofThemMieng` làm ĐÚNG phép đổi trục (`const tl = t +
ofDoiTruoc(i)`) nhưng KHÔNG nút nào, KHÔNG phím nào gọi — code chết; còn
`ofAddShot` là hàm chạy thật thì thiếu đúng dòng đó. Máy chủ KHÔNG sai: `che_tai`
làm đúng việc của nó, sai nằm ở chỗ gửi số.

Chạy trong CHROME THẬT (khuôn test_preview_trinh_duyet.py) vì máy không có Node.
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
    """Nguyên văn MỘT dòng bắt đầu bằng `dau` — nạp đúng code đang ship."""
    for d in _h().splitlines():
        if d.strip().startswith(dau):
            return d.strip()
    raise AssertionError(f"không thấy dòng «{dau}»")


# khối của SH019 (đo thật): chỉ cần v0/v1 + tho_them để dựng lại phép đổi trục
KHOI_SH019 = [
    {"v0": 0.0, "v1": 8.4, "tho_them": 5},
    {"v0": 8.4, "v1": 14.0, "tho_them": 0},
    {"v0": 14.0, "v1": 18.2, "tho_them": 1},
    {"v0": 18.2, "v1": 27.0, "tho_them": 9.7},
    {"v0": 27.0, "v1": 50.0, "tho_them": 1},
]

TRANG = """<!doctype html><meta charset="utf-8"><script>
let OF_PID = 'p1', OF_HCHON = -1
const OF_UNDO = []
let OF_HD = {offset: 2.0, hinh: __HINH__}   // `let`: ofAddShot GÁN LẠI OF_HD; để `const` thì lỗi gán bị chính try/catch của hàm nuốt mất
const OF_AUDIO = {currentTime: __NOW__}
const KHOI = __KHOI__
const GUI = []
function ofK() { return KHOI }
function ofChup() { OF_UNDO.push(1) }
function ofVeAll() {}
function toastOf() {}
function ofFmt(x) { return String(x) }
async function api(u, o) {
  GUI.push({u, body: JSON.parse(o.body)})
  return {hop_dong: OF_HD}
}
__DONG__
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


def _trang(chrome, tmp_path, now: float, khoi: list, hinh: list | None = None):
    html = (TRANG.replace("__HAM__", _ham("ofAddShot"))
                 .replace("__DONG__", _dong("const ofDoiTruoc ="))
                 .replace("__KHOI__", json.dumps(khoi))
                 .replace("__HINH__", json.dumps(hinh if hinh is not None else []))
                 .replace("__NOW__", str(now)))
    f = tmp_path / "t.html"
    f.write_text(html, encoding="utf-8")
    pg = chrome.new_page()
    loi: list[str] = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(f.as_uri())
    return pg, loi


def _gui(pg) -> dict:
    pg.evaluate("ofAddShot()")
    pg.wait_for_function("() => GUI.length > 0", timeout=5000)
    return pg.evaluate("GUI[0]")


def test_vach_o_khoi_4_gui_giay_TRUC_TIMELINE(chrome, tmp_path):
    """Vạch 38,5s trục voice, trước nó có 5+1+9,7 = 15,7s hình thở."""
    pg, loi = _trang(chrome, tmp_path, now=38.5 + 2.0, khoi=KHOI_SH019)
    g = _gui(pg)
    assert g["u"].endswith("/che-tai")
    assert g["body"]["tai"] == pytest.approx(38.5 + 15.7, abs=0.01), (
        f"gửi {g['body']['tai']} — đó là giây trục VOICE, máy chủ cắt trục TIMELINE")
    assert loi == [], loi
    pg.close()


def test_chuong_CHUA_them_hinh_tho_thi_khong_doi(chrome, tmp_path):
    """`c9-…` và `e-…` của user: lệch 0 -> con số gửi lên y như cũ."""
    khoi = [dict(k, tho_them=0) for k in KHOI_SH019]
    pg, loi = _trang(chrome, tmp_path, now=38.5 + 2.0, khoi=khoi)
    assert _gui(pg)["body"]["tai"] == pytest.approx(38.5, abs=0.01)
    assert loi == [], loi
    pg.close()


def test_vach_o_khoi_DAU_khong_bi_cong_gi(chrome, tmp_path):
    """Khối 0: không có khối nào đứng trước -> không cộng."""
    pg, loi = _trang(chrome, tmp_path, now=3.0 + 2.0, khoi=KHOI_SH019)
    assert _gui(pg)["body"]["tai"] == pytest.approx(3.0, abs=0.01)
    assert loi == [], loi
    pg.close()


def test_chon_dung_mieng_vua_cat(chrome, tmp_path):
    """`OF_HCHON` tìm miếng theo `t0` — mà `t0` là trục TIMELINE, nên phải dò
    bằng chính con số đã gửi, không phải giây trục voice."""
    hinh = [{"t0": 0.0, "dur": 13.4}, {"t0": 13.4, "dur": 40.8},
            {"t0": 54.2, "dur": 6.0}]
    pg, loi = _trang(chrome, tmp_path, now=38.5 + 2.0, khoi=KHOI_SH019, hinh=hinh)
    pg.evaluate("ofAddShot()")
    pg.wait_for_function("() => GUI.length > 0", timeout=5000)
    assert pg.evaluate("OF_HCHON") == 2, "phải trỏ đúng miếng bắt đầu tại 54,2s"
    assert loi == [], loi
    pg.close()


def test_khong_co_audio_thi_khong_no(chrome, tmp_path):
    html = (TRANG.replace("__HAM__", _ham("ofAddShot"))
                 .replace("__DONG__", _dong("const ofDoiTruoc ="))
                 .replace("__KHOI__", json.dumps(KHOI_SH019))
                 .replace("__HINH__", "[]")
                 .replace("const OF_AUDIO = {currentTime: __NOW__}",
                          "const OF_AUDIO = null"))
    f = tmp_path / "t2.html"
    f.write_text(html, encoding="utf-8")
    pg = chrome.new_page()
    loi: list[str] = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(f.as_uri())
    assert _gui(pg)["body"]["tai"] == pytest.approx(0.0, abs=0.01)
    assert loi == [], loi
    pg.close()


def test_ofThemMieng_van_la_ham_CHET_khong_ai_goi():
    """Ghi lại sự thật, KHÔNG xoá: luật Karpathy #3 của repo — "Don't remove
    pre-existing dead code unless asked". `ofThemMieng` làm đúng phép đổi trục
    nhưng không nút nào, không phím nào gọi. Để lại thì phải biết nó ở đó: hai
    đường cùng làm một việc, sửa đường này mà quên đường kia là sai âm thầm.
    Xoá hay giữ là quyết định của user — test này chỉ canh cho nó đừng SỐNG DẬY
    mà vẫn mang bản cũ."""
    h = _h()
    assert "function ofThemMieng" in h, "đã xoá thì bỏ luôn test này"
    goi = [d for d in h.splitlines()
           if "ofThemMieng" in d and "function ofThemMieng" not in d]
    assert goi == [], f"có chỗ gọi rồi — phải kiểm lại phép đổi trục ở đó: {goi}"
