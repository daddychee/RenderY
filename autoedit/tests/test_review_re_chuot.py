r"""POPUP REVIEW: rê chuột ra ngoài vùng trim thì bị GIẬT VỀ ĐẦU (user báo 17/09).

User: *"Click double vào video thì video chạy tự động, không thể pause được,
Không thể rê chuột để xem được"*.

ĐO THẬT trên chương `c9-20260911-082606` (SH019) trong Chrome thật, 17/09:

    mở popup                     -> play@0.00 ngay (v.play() ở ofReview)
    CHƯA kéo tay trim            -> pause GIỮ, seek tới 7,55s/9,44s GIỮ  ✔
    kéo tay B về 3,8s rồi seek   -> currentTime nhảy về **0**, kể cả đang PAUSE  ✘

Thủ phạm là chốt lặp khúc trong `ofReview`:

    v.ontimeupdate = () => { … if (v.currentTime > OF_RV_T1) v.currentTime = OF_RV_T0 }

`timeupdate` bắn ở MỌI lần đổi thời điểm — kể cả khi người dùng tự kéo thanh, kể cả
khi đang dừng. Nên vừa rê ra ngoài vùng trim là bị kéo về đầu; đang phát thì lặp
liên tục nên cảm giác "không pause được".

LUẬT ĐÚNG: lặp khúc là để XEM THỬ đoạn đã chọn — nó chỉ được áp khi VIDEO TỰ CHẠY
tới cuối vùng, không được áp khi NGƯỜI dựng chủ động rê đi chỗ khác. Rê ra ngoài =
người dựng muốn xem phần khác của clip gốc (đúng việc họ cần khi chọn lại khúc).
Bấm ▶ Play (xem thử khúc) là quay lại chế độ lặp.
"""

from __future__ import annotations

import re
import subprocess
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


def _mp4(dich: Path, giay: int = 10) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"testsrc=size=160x90:rate=15:duration={giay}",
                    "-pix_fmt", "yuv420p", str(dich)], check=True)


TRANG = """<!doctype html><meta charset="utf-8">
<div id="of-trim-cs"><div id="of-rv-ten"></div>
  <video id="of-rv-video" muted loop playsinline controls></video>
  <img id="of-rv-anh" hidden>
  <div id="of-trim"><div id="of-trim-thanh">
    <div id="of-trim-vung"></div><div class="tay" id="of-tay-a"></div>
    <div class="tay" id="of-tay-b"></div><div id="of-trim-ph"></div>
  </div></div>
  <div id="of-trim-so"></div>
  <div id="of-rv-meta"></div>
</div>
<script>
__DONG__
function ofNoiTrim() {}
function ofRvMeta() {}
function ofTimVe() {}
function ofVid(u) { return u.url_video || '' }
function ofAnh(u) { return u.url_anh || '' }
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
    _mp4(tmp_path / "v.mp4", 10)
    html = (TRANG.replace("__HAM__", "\n".join(
                    [_ham("ofReview"), _ham("ofVeTrim"), _ham("ofTrimPhat")]))
                 .replace("__DONG__", "\n".join([_dong("let OF_RV = null"),
                                                 _dong("let OF_RV_TU_DO")])))
    (tmp_path / "t.html").write_text(html, encoding="utf-8")
    pg = chrome.new_page()
    loi: list[str] = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto((tmp_path / "t.html").as_uri())
    pg.evaluate("ofReview({id: 'pexels:1', tieu_de: 'thu', url_video: 'v.mp4'})")
    pg.wait_for_function("() => document.getElementById('of-rv-video').duration > 1",
                         timeout=8000)
    yield pg, loi
    pg.close()


def _now(pg) -> float:
    return pg.evaluate("+document.getElementById('of-rv-video').currentTime.toFixed(2)")


def test_re_ra_ngoai_vung_trim_thi_GIU_NGUYEN(trang):
    """Lỗi user báo: kéo tay trim còn 0–4s rồi rê tới 8s -> bị giật về 0."""
    pg, loi = trang
    pg.evaluate("() => { OF_RV_T0 = 0; OF_RV_T1 = 4; ofVeTrim() }")
    pg.evaluate("document.getElementById('of-rv-video').pause()")
    pg.evaluate("document.getElementById('of-rv-video').currentTime = 8")
    pg.wait_for_timeout(1500)
    assert _now(pg) == pytest.approx(8, abs=0.3), "bị kéo về đầu — không xem được clip gốc"
    assert loi == [], loi


def test_dang_PHAT_ma_re_ra_ngoai_cung_GIU(trang):
    pg, loi = trang
    pg.evaluate("() => { OF_RV_T0 = 0; OF_RV_T1 = 4; ofVeTrim() }")
    pg.evaluate("document.getElementById('of-rv-video').play()")
    pg.wait_for_timeout(600)
    pg.evaluate("document.getElementById('of-rv-video').currentTime = 8")
    pg.wait_for_timeout(1200)
    assert _now(pg) > 7.5, "đang phát mà rê ra ngoài vẫn bị giật về đầu"
    assert loi == [], loi


def test_PAUSE_van_giu_nguyen_sau_khi_re(trang):
    pg, loi = trang
    pg.evaluate("() => { OF_RV_T0 = 0; OF_RV_T1 = 4; ofVeTrim() }")
    pg.evaluate("document.getElementById('of-rv-video').pause()")
    pg.evaluate("document.getElementById('of-rv-video').currentTime = 8")
    pg.wait_for_timeout(1500)
    assert pg.evaluate("document.getElementById('of-rv-video').paused") is True
    assert loi == [], loi


def test_PHAT_TU_NHIEN_qua_moc_cuoi_thi_VAN_lap_khuc(trang):
    """Giữ nguyên tính năng: xem thử khúc đã chọn thì phải lặp trong khúc."""
    pg, loi = trang
    pg.evaluate("() => { OF_RV_T0 = 0; OF_RV_T1 = 2; ofVeTrim() }")
    pg.evaluate("() => { const v = document.getElementById('of-rv-video')"
                "; v.currentTime = 1.6; v.play() }")
    pg.wait_for_timeout(2500)
    assert _now(pg) < 2.2, "chạy quá mốc cuối mà không quay lại đầu khúc"
    assert loi == [], loi


def test_nut_PLAY_khuc_bat_lai_che_do_lap(trang):
    """Rê ra ngoài rồi bấm ▶ Play — phải về đầu khúc và lặp lại như cũ."""
    pg, loi = trang
    pg.evaluate("() => { OF_RV_T0 = 0; OF_RV_T1 = 2; ofVeTrim() }")
    pg.evaluate("document.getElementById('of-rv-video').currentTime = 8")
    pg.wait_for_timeout(800)
    pg.evaluate("ofTrimPhat()")
    pg.wait_for_timeout(2500)
    assert _now(pg) < 2.2, "bấm Play khúc xong vẫn chạy ra ngoài khúc"
    assert loi == [], loi
