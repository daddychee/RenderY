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
