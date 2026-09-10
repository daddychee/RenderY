r"""Xuất timeline VẪN DÍNH preview watermark — hieuvn + haint báo 10/09/2026.

ĐO THẬT trên production 10/09: **5/15 chương gần nhất dính, 17 miếng** mang
watermark. `thay_mau.json` ghi rõ từng miếng:
*"Envato preview WATERMARK — phiên Envato sống rồi bấm Online lại là sạch"*.

NGUYÊN NHÂN (log production `prod.log.old:1535-1551`):

```
online: phiên Envato HẾT HẠN — thử tự đăng nhập lại...
online: deb9c66d LỖI (It looks like you are using Playwright Sync API inside
        the asyncio loo) — giữ preview
online: 1171e0c1 LỖI (Page.goto: Target page, context or browser has been
        closed) — giữ preview
online: 46ca7aab LỖI (...closed) — giữ preview
online: 7ec1b963 LỖI (...closed) — giữ preview
```

`tai_nhieu` mở `sync_playwright()` (tai_sach.py:138), rồi khi thấy phiên hết
hạn lại gọi `phien.dang_nhap()` — mà hàm đó **mở `sync_playwright()` lần nữa**
(phien.py:111). Playwright cấm lồng: nó dựng event loop riêng, gặp loop đang
chạy là ném *"Sync API inside the asyncio loop"*. KHÔNG dính dáng FastAPI —
tái hiện được bằng 3 dòng Python thuần.

Chuỗi hỏng:
  1. phiên hết hạn -> gọi `dang_nhap` BÊN TRONG `sync_playwright` đang mở
  2. Playwright ném lỗi -> `dang_nhap` chết
  3. `ctx.close()` đã gọi ngay trước đó -> context chết theo
  4. `break` thoát vòng -> MỌI clip còn lại giữ preview watermark

Tức là chỉ cần phiên hết hạn ĐÚNG MỘT LẦN là cả chương dính watermark, và tool
báo *"bấm Online lại là sạch"* — nhưng bấm lại vẫn hỏng y hệt vì lỗi nằm ở mã,
không ở phiên.
"""

from __future__ import annotations

import pytest


def test_KHONG_duoc_long_sync_playwright(tmp_path):
    """Bằng chứng gốc: `sync_playwright()` lồng nhau ném đúng lỗi trong log."""
    pw = pytest.importorskip("playwright.sync_api")

    with pytest.raises(Exception) as e:
        with pw.sync_playwright():
            with pw.sync_playwright():
                pass
    assert "asyncio loop" in str(e.value), \
        f"lỗi khác với ca production: {str(e.value)[:120]}"


def test_tai_nhieu_KHONG_goi_dang_nhap_trong_phien(tmp_path):
    """`tai_nhieu` không được gọi `dang_nhap` khi đang mở `sync_playwright`.

    Kiểm bằng mã nguồn vì đây là ràng buộc CẤU TRÚC (hàm nào nằm trong khối
    `with` nào) — chạy thật thì phải có tài khoản Envato và mạng.
    """
    import inspect
    import re

    from autoedit.sourcer import tai_sach

    src = inspect.getsource(tai_sach.tai_nhieu)
    # phần thân nằm trong `with ... sync_playwright() as p:`
    i = src.find("sync_playwright() as p:")
    assert i > 0, "không tìm thấy khối sync_playwright trong tai_nhieu"
    # bỏ dòng chú thích: bản vá GIẢI THÍCH vì sao không được gọi ở đây, chữ
    # `dang_nhap()` trong lời giải thích không phải lời gọi
    trong_khoi = "\n".join(d for d in src[i:].splitlines()
                           if not d.lstrip().startswith("#"))
    assert not re.search(r"\bdang_nhap\s*\(", trong_khoi), (
        "tai_nhieu gọi dang_nhap BÊN TRONG sync_playwright — Playwright cấm "
        "lồng, sẽ ném 'Sync API inside the asyncio loop' và cả chương rơi về "
        "preview watermark (bug hieuvn/haint báo 10/09)")


def test_phien_het_han_thi_BAO_RO_va_KHONG_am_tham_giu_preview(tmp_path, monkeypatch):
    """Phiên hết hạn phải nêu ĐÚNG việc người dùng cần làm, và KHÔNG được lặng
    lẽ xuất bản watermark như không có chuyện gì.

    Trước đây thông điệp là *"phiên Envato sống rồi bấm Online lại là sạch"* —
    người dựng bấm lại, vẫn hỏng y hệt, vì lỗi ở mã chứ không ở phiên.
    """
    from autoedit.sourcer import tai_sach

    ghi: list[str] = []
    monkeypatch.setattr(tai_sach, "co_phien_song", lambda nha: False, raising=False)
    kq = tai_sach.tai_nhieu(None, [], log=ghi.append)
    assert kq == {}
    # không có clip nào cần tải -> không được báo bậy
    assert not any("watermark" in m.lower() for m in ghi), ghi


def test_co_ham_dang_nhap_lai_NGOAI_phien(tmp_path):
    """Phải có đường tự cứu — nhưng đặt NGOÀI `sync_playwright`: thoát ra,
    đăng nhập, rồi chạy lại một lượt. Bỏ hẳn tự cứu là mỗi lần phiên hết hạn
    người dựng phải tự đăng nhập tay."""
    from autoedit.sourcer import tai_sach

    assert hasattr(tai_sach, "tai_nhieu_tu_cuu"), (
        "thiếu đường tự cứu ngoài phiên — phiên hết hạn giữa chừng là cả "
        "chương dính watermark")


def test_soat_truoc_pha_BAT_ca_watermark(tmp_path):
    """Export phải báo TRƯỚC khi dựng nếu miếng đang dùng preview watermark.

    User chốt ở việc B (09/09): *"ấn export timeline, tool check 1 lượt... có
    thì báo đã có video hỏng"*. Watermark cũng là "hỏng" theo nghĩa dùng được
    nhưng KHÔNG giao được — hieuvn/haint chỉ phát hiện khi mở timeline ra xem,
    tức là sau khi đã chờ dựng xong.

    Điều kiện: clip envato mà `path_local` rỗng = chưa có bản sạch = sẽ dùng
    preview watermark (`thay_mau.py` nhánh envato).
    """
    from autoedit.offline.thay_mau import soat_truoc_pha
    from autoedit.sotra import db as sdb

    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "envato:W1", "nguon": "envato", "tieu_de": "Rome dawn",
                      "url_video": "https://cdn/preview.mp4", "path_local": ""})
    c.commit()
    hd = {"khoi": [{"v0": 0.0, "v1": 2.0}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": "envato:W1", "nguon": "envato",
                            "tieu_de": "Rome dawn"}]}]}
    xau = soat_truoc_pha(c, hd)
    c.close()
    assert xau, "không bắt được miếng sắp dùng preview watermark"
    assert xau[0]["mieng"] == 0
    assert "watermark" in (xau[0].get("ly_do") or "").lower(), \
        f"không nói rõ lý do là watermark: {xau[0]}"


def test_envato_DA_co_ban_sach_thi_KHONG_chan(tmp_path):
    """Chặn oan tệ hơn bỏ sót: clip đã tải bản sạch phải cho Export chạy."""
    from autoedit.offline.thay_mau import soat_truoc_pha
    from autoedit.sotra import db as sdb

    sach = tmp_path / "sach.mp4"
    sach.write_bytes(b"\x00" * 200_000)
    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "envato:W2", "nguon": "envato", "tieu_de": "Rome dawn",
                      "url_video": "https://cdn/preview.mp4",
                      "path_local": str(sach)})
    c.commit()
    hd = {"khoi": [{"v0": 0.0, "v1": 2.0}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": "envato:W2", "nguon": "envato",
                            "tieu_de": "Rome dawn"}]}]}
    assert not soat_truoc_pha(c, hd), "chặn oan clip đã có bản sạch"
    c.close()


def test_loi_bao_NOI_DUNG_LY_DO_chu_khong_gop_lam_mot(tmp_path):
    """Hai lý do chặn = hai cách xử lý KHÁC HẲN:

    * clip hỏng/hết hạn -> phải THAY clip khác
    * Envato chưa có bản sạch -> đăng nhập Envato rồi bấm Online, KHÔNG cần thay

    Gộp làm một câu "clip đã hỏng — thay clip khác" là bắt người dựng thay 42
    miếng lành (đo 10/09) trong khi chỉ cần đăng nhập lại một lần. Đúng lỗi
    BH15 vừa rút ra hôm nay: một triệu chứng, hai nguyên nhân, phải hai lời.
    """
    import inspect

    from autoedit.web import server

    src = inspect.getsource(server.api_offline_thay_mau)
    assert "ly_do" in src, (
        "endpoint không dùng `ly_do` từ soát — hộp báo sẽ nói sai cách xử lý")


def test_UI_hien_LY_DO_cua_tung_mieng():
    """Hộp thoại phải in `ly_do` chứ không dán cứng một câu."""
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    i = h.find("OF_HONG = new Set(hong.map")
    assert i > 0, "không tìm thấy nhánh xử lý miếng hỏng trong index.html"
    khoi = h[i:i + 1200]
    assert "ly_do" in khoi, (
        "hộp thoại không in ly_do — người dựng đọc 'clip đã hỏng' rồi đi thay "
        "clip, trong khi thứ cần làm là đăng nhập Envato")


def test_chi_bao_phien_KHONG_duoc_bao_XANH_khi_chua_kiem_that():
    """Chỉ báo phiên trên giao diện dùng `co_phien` — hàm này chỉ kiểm cookie
    CÓ MẶT, không kiểm CÒN HẠN (docstring nói rõ: "kiểm thật sự diễn ra lúc mở
    trang").

    Đo 10/09: `/api/phien` trả `co_phien: true` trong khi mở Chrome thật thì
    trang Envato hiện nút Sign in — phiên CHẾT. Người dựng nhìn chấm xanh
    tưởng ổn, mọi lần Export đều dính watermark mà không ai đi đăng nhập lại.

    Vá: API trả thêm `kiem_luc` (lần cuối tải bản sạch thành công) để giao
    diện phân biệt "có phiên" với "phiên còn sống".
    """
    import inspect

    from autoedit.sourcer import phien as _ph

    d = _ph.trang_thai()
    assert "lan_cuoi_tai" in d["envato"], (
        "API phiên chỉ trả co_phien (cookie có mặt) — chấm xanh dối, người "
        f"dựng không biết phải đăng nhập lại: {d['envato']}")
    assert "lan_cuoi_tai" in inspect.getsource(_ph.trang_thai)


def test_UI_bao_VANG_khi_lau_khong_tai_duoc_ban_sach():
    """Chấm xanh chỉ dựa `co_phien` là DỐI. Giao diện phải đổi màu khi đã lâu
    không tải được bản sạch — dấu hiệu phiên đã chết dù cookie còn nằm đó.

    Đo 10/09: lần tải cuối `2026-09-07 15:07:46`, tức 3 NGÀY trước, đúng lúc
    hieuvn/haint bắt đầu thấy watermark.
    """
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    i = h.find("async function ofVePhien()")
    assert i > 0, "không tìm thấy ofVePhien"
    khoi = h[i:i + 1400]
    assert "lan_cuoi_tai" in khoi, (
        "chỉ báo phiên không dùng lan_cuoi_tai — vẫn hiện xanh khi phiên chết")


# ═════════ CHẶN TRIỆT ĐỂ (user họp team 10/09, chiều) ═════════
# *"ấn export timeline mà có video envato không down được vẫn cho chạy hết
#  timeline. TÔI CẦN FIX TRIỆT ĐỂ VẤN ĐỀ NÀY"*
#
# Soát TRƯỚC (`soat_truoc_pha`) chỉ chặn khi bấm Export. Nhưng ngay sau đó
# `thay_mau` tải bản sạch, và nếu tải HỤT giữa chừng (phiên chết đúng lúc, mạng
# đứt, item bị gỡ) thì nó đi thẳng vào `relocate` — nhánh envato thiếu
# `path_local` rơi về preview watermark, ghi warning, draft VẪN RA ĐỦ.
#
# Tức là có HAI cửa và mới khoá một. Cửa thứ hai là chỗ team gặp.

def _hd_envato(*ids):
    return {"trang_thai": "khoa", "offset": 0.0,
            "khoi": [{"v0": float(i * 2), "v1": float(i * 2 + 2), "tho": 0.0}
                     for i in range(len(ids))],
            "hinh": [{"t0": float(i * 2), "dur": 2.0, "khoi_goc": i, "chon": 0,
                      "uv": [{"id": c, "nguon": "envato", "tieu_de": f"clip {c}"}]}
                     for i, c in enumerate(ids)]}


def test_TAI_HUT_giua_chung_thi_DUNG_khong_dung_draft(tmp_path, monkeypatch):
    """Cửa thứ hai: soát đã qua, nhưng tải bản sạch HỤT -> phải DỪNG.

    Trước đây `thay_mau` nuốt lỗi tải ("dùng preview") rồi dựng tiếp, nên team
    nhận draft đủ 100% miếng mà bên trong có watermark.
    """
    from autoedit.offline import runner as orun
    from autoedit.offline import thay_mau as tm
    from autoedit.sotra import db as sdb

    p = tmp_path / "proj"
    (p / "media").mkdir(parents=True)
    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "envato:X1", "nguon": "envato", "tieu_de": "a",
                      "url_video": "https://cdn/p.mp4", "path_local": ""})
    c.commit()
    hd = _hd_envato("envato:X1")
    orun.luu(p, hd)
    # tải bản sạch KHÔNG lấy được gì (phiên chết giữa chừng)
    monkeypatch.setattr(tm, "relocate",
                        lambda *a, **k: pytest.fail("đã dựng draft dù tải hụt"))
    monkeypatch.setattr("autoedit.sourcer.tai_sach.tai_nhieu_tu_cuu",
                        lambda *a, **k: {})
    with pytest.raises(RuntimeError) as e:
        tm.thay_mau(p, conn=c, log=lambda m: None)
    c.close()
    loi = str(e.value).lower()
    assert "watermark" in loi or "bản sạch" in loi, \
        f"dừng nhưng không nói rõ vì sao: {e.value}"


def test_TAI_DU_thi_chay_binh_thuong(tmp_path, monkeypatch):
    """Chặn oan tệ hơn bỏ sót: tải đủ bản sạch thì Export phải chạy tiếp."""
    from autoedit.offline import runner as orun
    from autoedit.offline import thay_mau as tm
    from autoedit.sotra import db as sdb

    p = tmp_path / "proj"
    (p / "media").mkdir(parents=True)
    sach = tmp_path / "s.mp4"
    sach.write_bytes(bytes(200_000))
    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "envato:X2", "nguon": "envato", "tieu_de": "a",
                      "url_video": "https://cdn/p.mp4", "path_local": str(sach)})
    c.commit()
    hd = _hd_envato("envato:X2")
    orun.luu(p, hd)
    da_dung = []
    monkeypatch.setattr(tm, "relocate",
                        lambda *a, **k: (da_dung.append(1), ({}, {}, []))[1])
    monkeypatch.setattr(tm, "dung_draft", lambda *a, **k: tmp_path / "draft")
    monkeypatch.setattr(tm, "_cat_voice", lambda *a, **k: {})
    monkeypatch.setattr("autoedit.sourcer.tai_sach.tai_nhieu_tu_cuu",
                        lambda *a, **k: {"X2": sach})
    tm.thay_mau(p, profile=object(), conn=c, log=lambda m: None)
    c.close()
    assert da_dung, "clip đã có bản sạch mà vẫn bị chặn"


def test_clip_NON_envato_khong_bi_anh_huong(tmp_path, monkeypatch):
    """pexels/ref/kho không có khái niệm bản sạch — không được chặn nhầm."""
    from autoedit.offline import runner as orun
    from autoedit.offline import thay_mau as tm
    from autoedit.sotra import db as sdb

    p = tmp_path / "proj"
    (p / "media").mkdir(parents=True)
    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "pexels:9", "nguon": "pexels", "tieu_de": "a",
                      "url_video": "https://cdn/p.mp4", "path_local": ""})
    c.commit()
    hd = {"trang_thai": "khoa", "offset": 0.0,
          "khoi": [{"v0": 0.0, "v1": 2.0, "tho": 0.0}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": "pexels:9", "nguon": "pexels", "tieu_de": "a"}]}]}
    orun.luu(p, hd)
    da_dung = []
    monkeypatch.setattr(tm, "relocate",
                        lambda *a, **k: (da_dung.append(1), ({}, {}, []))[1])
    monkeypatch.setattr(tm, "dung_draft", lambda *a, **k: tmp_path / "draft")
    monkeypatch.setattr(tm, "_cat_voice", lambda *a, **k: {})
    tm.thay_mau(p, profile=object(), conn=c, log=lambda m: None)
    c.close()
    assert da_dung, "clip pexels bị chặn oan vì luật bản sạch Envato"


def test_relocate_KHONG_TAI_preview_watermark_nua(tmp_path):
    """Cửa THỨ BA: `relocate` có nhánh tải thẳng preview watermark
    (`thay_mau.py:273`). Ai gọi `relocate` không qua `thay_mau` là lọt.

    User họp team 10/09: FIX TRIỆT ĐỂ. Preview watermark KHÔNG được lên
    timeline nữa — miếng đó phải thử ứng viên DỰ BỊ, hết dự bị thì để ô giữ
    chỗ (việc A). Ô giữ chỗ nói thật là "chưa có clip"; watermark nói dối là
    "có clip rồi" mà giao khách không được.
    """
    from autoedit.offline import thay_mau as tm
    from autoedit.sotra import db as sdb

    p = tmp_path / "proj"
    p.mkdir()
    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "envato:P1", "nguon": "envato", "tieu_de": "a",
                      "url_video": "https://cdn/preview.mp4", "path_local": ""})
    c.commit()
    hd = {"offset": 0.0, "khoi": [{"v0": 0.0, "v1": 2.0, "tho": 0.0}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": "envato:P1", "nguon": "envato", "tieu_de": "a"}]}]}
    da_tai = []
    goc = tm._tai
    tm._tai = lambda url, dich, **k: (da_tai.append(url), goc(url, dich, **k))[1]
    try:
        video, _ids, warns = tm.relocate(p, hd, c, lambda m: None)
    finally:
        tm._tai = goc
    c.close()
    assert not da_tai, f"vẫn tải preview watermark: {da_tai}"
    assert 0 not in video, "preview watermark vẫn lên timeline"
    assert any("bản sạch" in w or "watermark" in w.lower() for w in warns), warns
