r"""CẢNH BÁO PHẢI CHỈ RA KHỐI NÀO — user báo 18/09: *"Hiện đang mất thông báo
lỗi ở khối nào"*.

Ảnh user gửi: banner đỏ ghi "2 khối vi phạm luật 60s" mà trên timeline KHÔNG có
mảnh nào được đánh dấu. Mổ ra BA lỗi độc lập:

A. **Dấu đỏ trên timeline không tồn tại.** `ofVeTL` gắn class `lap` cho mảnh vi
   phạm, nhưng trong stylesheet **không có luật `.of-mieng.lap`** — chỉ có
   `.of-khoi.lap` của UI đời trước (class `of-khoi` nay không nơi nào sinh ra).
   Mảnh vi phạm trông y hệt mảnh lành.

B. **Tô nhầm đối tượng.** `ofKiemLap()` trả về chỉ số MIẾNG, còn chỗ vẽ lại hỏi
   `lap.has(h.khoi_goc)` — chỉ số KHỐI. Hai trục khác nhau kể từ khi tách dải
   hình khỏi dải voice (08/09).

   ĐO THẬT trên 88 hợp đồng production (18/09): **27 hợp đồng tô SAI CHỖ**.

       c1-20260911-082148   31 miếng/17 khối   vi phạm THẬT [26, 28]  ->  tô 0 mảnh
       c1-20260915-101024   60 miếng/19 khối   vi phạm THẬT [6, 9]    ->  tô 10 mảnh OAN
       c13-20260907-051126  27 miếng/25 khối   [0,1,13,14,17,18]      ->  lệch 4 sót / 4 oan

C. **Câu cảnh báo vứt mất danh sách.** `dung.kiem_lap` trả về ĐÚNG chỉ số các
   khối, `runner.phan_tich` lại chỉ giữ `len()`: "8 khối vi phạm luật 60s".
   52/86 hợp đồng production đang mang câu đó — không câu nào nói khối nào.

Kèm theo: cảnh báo lệch voice khi gộp tập đang báo oan ở sai số làm tròn
(`kim048-tap` thật: "E: file voice ngắn hơn khối 0.01s").
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
    for d in _h().splitlines():
        if d.strip().startswith(dau):
            return d.strip()
    raise AssertionError(f"không thấy dòng «{dau}»")


def _style() -> str:
    return re.search(r"<style>(.*?)</style>", _h(), re.S).group(1)


# ───────────────────── C. câu cảnh báo nói rõ khối nào ─────────────────────

def test_cau_canh_bao_60s_KE_TEN_khoi():
    from autoedit.offline.runner import canh_bao_lap

    cb = canh_bao_lap([2, 5, 9])
    assert cb and "3 khối" in cb[0], cb
    assert "3, 6, 10" in cb[0], f"không kê tên khối (đếm từ 1): {cb[0]}"
    assert "60s" in cb[0]


def test_cau_canh_bao_60s_dai_thi_CAT_BOT_nhung_noi_con_bao_nhieu():
    """Chương thật có tới 8-14 khối vi phạm; kê hết thì banner tràn màn hình."""
    from autoedit.offline.runner import canh_bao_lap

    cb = canh_bao_lap(list(range(20)))[0]
    assert "20 khối" in cb, cb
    assert "1, 2, 3" in cb, cb
    assert "…" in cb or "..." in cb, f"cắt bớt mà không báo còn nữa: {cb}"
    assert len(cb) < 200, f"câu quá dài ({len(cb)} ký tự)"


def test_khong_vi_pham_thi_KHONG_canh_bao():
    from autoedit.offline.runner import canh_bao_lap

    assert canh_bao_lap([]) == []


def test_hop_dong_mang_cau_co_ten_khoi(tmp_path, monkeypatch):
    """Đi trọn đường: phân tích -> hợp đồng ghi câu CÓ SỐ KHỐI, không phải mỗi len()."""
    import subprocess

    from autoedit.offline import dung, runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    d = tmp_path / "projects" / "c9"
    (d / "media").mkdir(parents=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "sine=frequency=200:duration=8", "-ar", "16000",
                    str(d / "media" / "voice_master.wav")], check=True)
    (d / "transcript.json").write_text(json.dumps({"words": [
        {"w": f"tu{i}", "t0": i * 0.5, "t1": i * 0.5 + 0.4} for i in range(16)]}),
        encoding="utf-8")
    # mọi khối cùng MỘT clip -> chắc chắn vi phạm 60s
    mot = [{"id": "ref:x", "nguon": "ref", "tieu_de": "t", "lop": "L1", "diem": 9,
            "url_anh": "", "url_video": "", "geo": "", "dai_s": 30}]
    monkeypatch.setattr(dung, "do_ung_vien", lambda c, k, *a, **kw: [list(mot) for _ in k])
    monkeypatch.setattr(dung, "kiem_lap", lambda *a, **k: [0, 2])

    class _LLM:
        def json(self, *a, **k):
            return {"chu_the_tap": [], "khoi": []}

    hd = runner.phan_tich(d, llm=_LLM())
    cau = [c for c in hd["canh_bao"] if "60s" in c]
    assert cau, hd["canh_bao"]
    assert "1, 3" in cau[0], f"hợp đồng vẫn không nói khối nào: {cau[0]}"


# ──────────── gộp tập: đừng báo oan ở sai số làm tròn (kim048-tap) ────────────

def test_gop_tap_KHONG_bao_oan_lech_vai_phan_tram_giay():
    """`kim048-tap` thật mang cảnh báo "E: file voice ngắn hơn khối 0.01s" — sai
    số làm tròn của ffprobe, không phải hỏng. Báo oan làm người dựng mất lòng
    tin vào banner, rồi bỏ qua cả cảnh báo thật."""
    from autoedit.offline.tap import noi_hop_dong

    def _hd(het: float) -> dict:
        return {"khoi": [{"v0": 0.0, "v1": het - 0.3, "tho": 0.3, "tho_them": 0.0,
                          "loi": "x", "uv": [], "chon": -1}],
                "hinh": [{"t0": 0.0, "dur": het, "khoi_goc": 0, "uv": [], "chon": -1}],
                "canh_bao": []}

    hd = noi_hop_dong([{"ma": "H", "project_id": "h", "hd": _hd(5.0), "dai_voice": 5.0},
                       {"ma": "E", "project_id": "e", "hd": _hd(4.0), "dai_voice": 3.99}])
    assert hd["canh_bao"] == [], f"báo oan sai số làm tròn: {hd['canh_bao']}"


def test_gop_tap_VAN_bao_khi_lech_that():
    """Lệch nửa giây là hỏng thật — vẫn phải kêu."""
    from autoedit.offline.tap import noi_hop_dong

    def _hd(het: float) -> dict:
        return {"khoi": [{"v0": 0.0, "v1": het - 0.3, "tho": 0.3, "tho_them": 0.0,
                          "loi": "x", "uv": [], "chon": -1}],
                "hinh": [{"t0": 0.0, "dur": het, "khoi_goc": 0, "uv": [], "chon": -1}],
                "canh_bao": []}

    hd = noi_hop_dong([{"ma": "H", "project_id": "h", "hd": _hd(5.0), "dai_voice": 5.0},
                       {"ma": "E", "project_id": "e", "hd": _hd(4.0), "dai_voice": 3.4}])
    assert any("ngắn hơn" in c for c in hd["canh_bao"]), hd["canh_bao"]


# ───────────────────── A + B: dấu đỏ trên timeline ─────────────────────

TRANG = """<!doctype html><html><head><meta charset="utf-8"><style>__CSS__</style></head><body>
<div id="of-thuoc"></div><div id="of-dai"><div id="of-ph"></div></div>
<div id="of-dai-au"></div><div id="of-dai-nh"></div>
<div id="of-canh-bao" hidden></div>
<script>
let OF_PID = 'p', OF_PHA = 2, OF_CHON = 0, OF_HCHON = 0, OF_PXS = 14
let OF_HONG = new Set(), OF_AUDIO = null, OF_LANG = null
let OF_HD = __HD__
const NHAY = []
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
  c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]))
function ofAnh() { return '' }
function ofVeAll() { NHAY.push(OF_HCHON) }
function ofDatPh() {} function toastOf() {} function ofBoMieng() {}
function ofReview() {} function ofKeoMep() {}
__DONG__
__HAM__
</script></body></html>"""


def _uv(i: str) -> dict:
    return {"id": f"pexels:{i}", "nguon": "pexels", "tieu_de": i, "url_anh": "", "url_video": ""}


def _hd_lap(chuong: bool = False) -> dict:
    """5 khối · 7 miếng. Miếng 1 và 5 DÙNG CHUNG clip 'a' trong vòng 60s.

    Số miếng khác số khối (đúng cảnh thật) nên lẫn hai trục là lộ ngay.
    """
    khoi, hinh, t = [], [], 0.0
    for i in range(5):
        k = {"v0": round(t, 2), "v1": round(t + 2.0, 2), "tho": 0.4, "tho_them": 0.0,
             "loi": f"cau {i + 1}"}
        if chuong:
            k["chuong"] = "H" if i < 2 else "C1"
        khoi.append(k)
        t = round(t + 2.4, 2)
    moc = 0.0
    for i in range(5):
        n = 2 if i == 0 else 1          # khối 1 chẻ 2 miếng -> hai trục lệch nhau
        for j in range(n):
            uv_id = "a" if len(hinh) in (1, 5) else f"c{len(hinh)}"
            hinh.append({"t0": round(moc, 2), "dur": round(2.4 / n, 2), "khoi_goc": i,
                         "uv": [_uv(uv_id)], "chon": 0, "noi_tiep": j > 0})
            moc = round(moc + 2.4 / n, 2)
    return {"offset": 0, "khoi": khoi, "hinh": hinh,
            "canh_bao": ["2 khối vi phạm luật 60s", "Ngách KHÔNG tới nơi — kiểm ô Niche"],
            **({"la_tap": True} if chuong else {})}


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


def _trang(chrome, tmp_path, chuong: bool = False):
    html = (TRANG.replace("__CSS__", _style())
            .replace("__HD__", json.dumps(_hd_lap(chuong)))
            .replace("__DONG__", "\n".join([_dong("const ofK ="), _dong("const ofDoiTruoc ="),
                                            _dong("const ofHinh ="), _dong("const ofTong ="),
                                            _dong("const ofUv ="), _dong("const ofFmt =")]))
            .replace("__HAM__", "\n".join([_ham("ofMoc"), _ham("ofKiemLap"),
                                           _ham("ofVeTL"), _ham("ofVeCanhBao"),
                                           _ham("ofToiMieng")])))
    f = tmp_path / "t.html"
    f.write_text(html, encoding="utf-8")
    pg = chrome.new_page(viewport={"width": 1100, "height": 500})
    loi: list[str] = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(f.as_uri())
    pg.wait_for_timeout(200)
    return pg, loi


def test_mieng_vi_pham_TRONG_KHAC_mieng_lanh(chrome, tmp_path):
    """Lỗi A: class `lap` được gắn nhưng stylesheet không có luật nào cho nó —
    mảnh vi phạm hiện lên y hệt mảnh lành, người dựng không thấy gì."""
    pg, loi = _trang(chrome, tmp_path)
    pg.evaluate("ofVeTL()")
    assert loi == [], loi
    # CÔ LẬP đúng class `lap`: bật/tắt trên CÙNG MỘT mảnh. So hai mảnh khác nhau
    # là xanh giả — mảnh vi phạm còn mang `tho`/`chon`, khác nhau vì lý do khác.
    kieu = pg.evaluate("""() => {
      const e = document.querySelector('#of-dai .of-mieng')
      if (!e) return null
      const doc = () => { const s = getComputedStyle(e)
        return {vien: s.borderColor, nen: s.backgroundColor,
                outline: s.outlineColor + '|' + s.outlineWidth + '|' + s.outlineStyle,
                bong: s.boxShadow} }
      e.className = 'of-mieng'
      const truoc = doc()
      e.className = 'of-mieng lap'
      return {truoc, sau: doc()}
    }""")
    assert kieu is not None, "không vẽ được mảnh nào"
    assert kieu["truoc"] != kieu["sau"], (
        f"class `lap` KHÔNG đổi gì trên màn hình — thiếu luật CSS .of-mieng.lap: {kieu}")


def test_to_do_DUNG_mieng_vi_pham_khong_lech_truc(chrome, tmp_path):
    """Lỗi B: `ofKiemLap` trả chỉ số MIẾNG, chỗ vẽ lại hỏi `khoi_goc` (chỉ số
    KHỐI). Đo thật: 27/88 hợp đồng production tô sai chỗ."""
    pg, loi = _trang(chrome, tmp_path)
    pg.evaluate("ofVeTL()")
    assert loi == [], loi
    do = pg.evaluate("[...document.querySelectorAll('#of-dai .of-mieng')]"
                     ".map((e, i) => e.classList.contains('lap') ? i : -1).filter(i => i >= 0)")
    assert do == [1, 5], f"tô sai mảnh: {do} (đúng phải là miếng 1 và 5 — cùng clip 'a')"


def test_banner_KE_TEN_mieng_va_bam_duoc(chrome, tmp_path):
    """Điều user cần: banner nói rõ chỗ nào, bấm là nhảy tới đó."""
    pg, loi = _trang(chrome, tmp_path)
    pg.evaluate("ofVeCanhBao()")
    assert loi == [], loi
    chu = pg.eval_on_selector("#of-canh-bao", "e => e.textContent")
    assert "2" in chu and "6" in chu, f"banner không kê số miếng (đếm từ 1): {chu!r}"
    nut = pg.query_selector_all("#of-canh-bao .nhay")
    assert len(nut) == 2, f"không bấm được để nhảy tới: {chu!r}"
    nut[1].click()
    pg.wait_for_timeout(150)
    assert pg.evaluate("OF_HCHON") == 5, "bấm số không nhảy đúng miếng"
    assert pg.evaluate("NHAY.length") > 0, "bấm xong không vẽ lại"


def test_banner_DOI_THEO_hop_dong_dang_sua_khong_giu_cau_cu(chrome, tmp_path):
    """Câu của máy chủ đóng băng lúc phân tích. Người dựng thay clip xong mà
    banner vẫn kêu thì lần sau họ bỏ qua banner."""
    pg, loi = _trang(chrome, tmp_path)
    pg.evaluate("() => { OF_HD.hinh[5].uv = [{id: 'pexels:z', nguon: 'pexels'}] }")
    pg.evaluate("ofVeCanhBao()")
    assert loi == [], loi
    chu = pg.eval_on_selector("#of-canh-bao", "e => e.textContent")
    assert "60s" not in chu, f"đã sửa hết mà banner vẫn kêu lặp: {chu!r}"
    assert "Ngách" in chu, "cảnh báo khác bị mất theo"


def test_banner_hop_dong_TAP_noi_ro_chuong(chrome, tmp_path):
    """Tập 16 chương thì "miếng 148" không giúp ai — phải kèm chương (QĐ17)."""
    pg, loi = _trang(chrome, tmp_path, chuong=True)
    pg.evaluate("ofVeCanhBao()")
    assert loi == [], loi
    chu = pg.eval_on_selector("#of-canh-bao", "e => e.textContent")
    assert "H" in chu and "C1" in chu, f"hợp đồng tập mà banner không nói chương: {chu!r}"
