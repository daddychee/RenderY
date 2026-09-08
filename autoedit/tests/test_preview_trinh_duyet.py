"""Preview đen dù timeline có hình (user báo 08/09) — test TRONG CHROME THẬT.

Máy này không có Node (METHODOLOGY BH3) nên tới nay mọi logic trong
`index.html` đều không test được: mắt user là kênh phát hiện lỗi duy nhất.
Playwright + Chrome thật đã có sẵn trên máy (cài từ R5b) — dùng nó nạp ĐÚNG
đoạn JS đang ship, không chép lại logic sang test.

Bằng chứng thu được trước khi viết test:
  - `/api/sotra/khuc` cho 6/6 miếng của C5 đều ra file khúc, file có thật;
  - prod.log: 121 lượt `/api/sotra/khuc` đều **206** — máy chủ giao video xong,
    trình duyệt đã tải về. Dữ liệu CÓ, chỉ là không được hiện.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1] / "autoedit" / "web" / "static" / "index.html"


def _ham(ten: str) -> str:
    """Lấy nguyên văn một hàm JS trong index.html (khớp ngoặc)."""
    src = GOC.read_text(encoding="utf-8")
    m = re.search(rf"^function\s+{re.escape(ten)}\s*\(", src, re.M)
    assert m, f"không thấy hàm {ten} trong index.html"
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


def _mp4(dich: Path, mau: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"color=c={mau}:s=64x64:d=1", "-pix_fmt", "yuv420p",
                    str(dich)], check=True)


TRANG = """<!doctype html><meta charset="utf-8">
<div id="of-khung">
  <video id="of-video" muted loop playsinline hidden></video>
  <video id="of-video2" muted loop playsinline hidden></video>
  <img id="of-anh" alt="" hidden>
  <div id="of-rong">chưa đổ hình</div>
</div>
<div id="of-nhan"></div>
<script>
/* --- đồ giả tối thiểu cho hai hàm thật bên dưới --- */
let OF_PHA = 2, OF_HCHON = 0
const HINH = [{uv: [{id: 'a', tieu_de: 'A', url_video: 'a.mp4'}], chon: 0},
              {uv: [{id: 'b', tieu_de: 'B', url_video: 'b.mp4'}], chon: 0}]
function ofHinh() { return HINH }
function ofUv(k) { const uv = k && k.uv || []; return uv[k.chon] }
function ofVid(u) { return u.url_video }
function ofAnh(u) { return u.url_anh || '' }   // khuôn hàm thật
function ofDangPhat() { return false }
function esc(s) { return s }
/* --- HAI HÀM THẬT, lấy nguyên văn từ index.html --- */
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
    _mp4(tmp_path / "a.mp4", "red")
    _mp4(tmp_path / "b.mp4", "blue")
    html = TRANG.replace("__HAM__", _ham("ofVeXem") + "\n" + _ham("ofNapKe"))
    (tmp_path / "t.html").write_text(html, encoding="utf-8")
    pg = chrome.new_page()
    pg.goto((tmp_path / "t.html").as_uri())
    yield pg
    pg.close()


def _dang_hien(pg) -> str:
    return pg.evaluate("""() => {
        for (const id of ['of-video', 'of-video2']) {
            const el = document.getElementById(id)
            if (!el.hidden && el.readyState >= 2 && el.videoWidth > 0) return el.currentSrc
        }
        return ''
    }""")


def test_preview_hien_video_o_lan_ve_dau_tien(trang):
    """Mở miếng đầu -> phải thấy clip A."""
    trang.evaluate("ofVeXem()")
    trang.wait_for_function("() => !document.getElementById('of-video').hidden"
                            " || !document.getElementById('of-video2').hidden",
                            timeout=8000)
    assert _dang_hien(trang).endswith("a.mp4")


def test_ve_lai_TRONG_LUC_dang_nap_khong_lam_den_man(trang):
    """LỖI user báo 08/09. `ofVeAll` chạy lại liên tục (playhead, thao tác...).
    Lần vẽ thứ hai rơi vào nhánh «đang hiện đúng clip rồi» -> gọi `ofNapKe`,
    mà `ofNapKe` chọn thẻ video ĐANG ẨN — chính là thẻ đang chờ nạp clip hiện
    tại — rồi ghi đè `src` bằng clip KẾ và **xoá `onloadeddata`**. Callback bật
    hình bị huỷ, cả hai thẻ ở lại `hidden`: màn đen vĩnh viễn dù video đã tải
    xong (prod.log: 121 lượt /khuc đều 206).
    """
    trang.evaluate("ofVeXem(); ofVeXem(); ofVeXem()")   # vẽ lại khi chưa nạp xong
    trang.wait_for_timeout(2500)
    assert _dang_hien(trang).endswith("a.mp4"), "preview ĐEN — không thẻ nào hiện clip A"


def test_doi_mieng_van_hien_dung_clip(trang):
    """Sang miếng 2 phải thấy clip B, không kẹt ở A."""
    trang.evaluate("ofVeXem()")
    trang.wait_for_timeout(1500)
    trang.evaluate("OF_HCHON = 1; ofVeXem()")
    trang.wait_for_timeout(2000)
    assert _dang_hien(trang).endswith("b.mp4")


def test_video_hong_thi_ROI_VE_ANH_chu_khong_de_den(chrome, tmp_path):
    """Đường thứ hai dẫn tới màn đen: clip hỏng/không giải mã được thì
    `onloadeddata` KHÔNG BAO GIỜ bắn, hai thẻ ở lại hidden mãi mãi và không ai
    biết vì sao (BH1: fail-open phải rung chuông). Phải rơi về khung hình tĩnh
    của clip — có còn hơn không."""
    _mp4(tmp_path / "a.mp4", "red")
    (tmp_path / "b.mp4").write_bytes(b"khong phai video")     # hỏng thật
    html = (TRANG.replace("__HAM__", _ham("ofVeXem") + "\n" + _ham("ofNapKe"))
            .replace("url_video: 'b.mp4'", "url_video: 'b.mp4', url_anh: 'khung.jpg'"))
    (tmp_path / "t.html").write_text(html, encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "color=c=green:s=64x64:d=1", "-frames:v", "1",
                    str(tmp_path / "khung.jpg")], check=True)
    pg = chrome.new_page()
    try:
        pg.goto((tmp_path / "t.html").as_uri())
        pg.evaluate("OF_HCHON = 1; ofVeXem()")
        pg.wait_for_timeout(2500)
        hien = pg.evaluate("""() => {
            const a = document.getElementById('of-anh')
            return (!a.hidden && a.naturalWidth > 0) ? a.currentSrc : ''
        }""")
        assert hien.endswith("khung.jpg"), "video hỏng mà preview để đen, không rơi về ảnh"
    finally:
        pg.close()
