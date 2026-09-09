r"""Việc D — hút stock phải nhận NHIỀU KHOÁ, không gửi nguyên chuỗi có dấu phẩy.

Bug đo thật 09/09/2026 trên production: két V3 phát khoá theo VIỆC, việc
`tim_footage` được cấp **4 khoá** (pexels ×2, pixabay ×2). `ket_v3.nap_env()` đổ
chúng vào biến môi trường dưới dạng NỐI BẰNG DẤU PHẨY:

    PEXELS_API_KEY  = <56 ký tự>,<56 ký tự>     (len 113)
    PIXABAY_API_KEY = <34 ký tự>,<34 ký tự>     (len  69)

`hut.py` lấy `os.getenv(...).strip()` rồi gửi thẳng đi:
  - Pexels  -> header Authorization = cả chuỗi -> **HTTP 401 Unauthorized**
  - Pixabay -> query ?key= cả chuỗi            -> **HTTP 400 Bad Request**

Tách riêng từng khoá thì CẢ 4 ĐỀU SỐNG (mỗi khoá trả 40 clip, 40/40 có
`url_video`). Vậy lỗi không ở khoá mà ở chỗ `hut.py` chưa biết dạng nhiều khoá —
trong khi `sourcer/pexels.py:34` `collect_pexels_keys` và
`sourcer/pixabay.py:133` `collect_pixabay_keys` đã làm đúng việc tách và đang
được dùng ở `web/server.py:499-500`.

Vì sao XOAY VÒNG chứ không chỉ lấy khoá đầu: nhiều khoá tồn tại để NHÂN HẠN MỨC
(Pexels 200 query/giờ/khoá). Dùng mãi khoá đầu là vứt nửa hạn mức, và khi khoá
đầu hết lượt (429) thì hút chết hẳn dù còn khoá sống.
"""

from __future__ import annotations

import urllib.error

import pytest

from autoedit.sotra import hut


class _Bat:
    """Ghi lại URL + headers mà hut.py định gửi — không chạm mạng."""

    def __init__(self, tra: bytes = b'{"videos": [], "hits": []}', loi_lan: int = 0):
        self.goi: list[tuple[str, dict]] = []
        self.tra = tra
        self.loi_lan = loi_lan          # N lượt đầu ném 429

    def __call__(self, url: str, headers: dict | None = None, timeout: float = 45.0) -> bytes:
        self.goi.append((url, dict(headers or {})))
        if len(self.goi) <= self.loi_lan:
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, None)  # type: ignore[arg-type]
        return self.tra


@pytest.fixture
def hai_khoa(monkeypatch):
    """Đúng dạng két V3 phát ra: 2 khoá nối bằng dấu phẩy."""
    monkeypatch.setenv("PEXELS_API_KEY", "PX_MOT,PX_HAI")
    monkeypatch.setenv("PIXABAY_API_KEY", "PB_MOT,PB_HAI")
    for i in range(2, 11):              # dọn biến _2.._10 nếu máy chạy test có
        monkeypatch.delenv(f"PEXELS_API_KEY_{i}", raising=False)
        monkeypatch.delenv(f"PIXABAY_API_KEY_{i}", raising=False)
    monkeypatch.delenv("PEXELS_API_KEYS", raising=False)
    monkeypatch.delenv("PIXABAY_API_KEYS", raising=False)


# ───────────────────────── lỗi đang có ─────────────────────────

def test_pexels_KHONG_gui_ca_chuoi_co_dau_phay(hai_khoa, monkeypatch):
    """Header Authorization phải là MỘT khoá, không phải 'PX_MOT,PX_HAI'."""
    bat = _Bat()
    monkeypatch.setattr(hut, "_get", bat)
    hut.hut_pexels("nui", 1)
    assert bat.goi, "không gọi request nào"
    auth = bat.goi[0][1].get("Authorization", "")
    assert "," not in auth, (
        f"gửi cả chuỗi nhiều khoá làm header -> Pexels trả 401. Đang gửi: {auth!r}")
    assert auth in ("PX_MOT", "PX_HAI"), f"header phải là 1 khoá hợp lệ, đang là {auth!r}"


def test_pixabay_KHONG_gui_ca_chuoi_co_dau_phay(hai_khoa, monkeypatch):
    """`?key=` phải là MỘT khoá — dấu phẩy trong query làm Pixabay trả 400."""
    bat = _Bat()
    monkeypatch.setattr(hut, "_get", bat)
    hut.hut_pixabay("nui", 1)
    assert bat.goi, "không gọi request nào"
    url = bat.goi[0][0]
    assert "PB_MOT,PB_HAI" not in url and "PB_MOT%2CPB_HAI" not in url, (
        f"gửi cả chuỗi nhiều khoá vào ?key= -> Pixabay trả 400. URL: {url}")
    assert ("key=PB_MOT" in url) or ("key=PB_HAI" in url), f"thiếu khoá hợp lệ: {url}"


# ───────────────────────── xoay vòng khi hết lượt ─────────────────────────

def test_pexels_het_luot_thi_XOAY_sang_khoa_ke(hai_khoa, monkeypatch):
    """429 ở khoá đầu KHÔNG được giết lượt hút khi còn khoá khác."""
    bat = _Bat(loi_lan=1)               # lượt 1 (khoá đầu) ném 429
    monkeypatch.setattr(hut, "_get", bat)
    hut.hut_pexels("nui", 1)            # không được ném
    assert len(bat.goi) == 2, f"phải thử khoá thứ 2 sau 429, đã gọi {len(bat.goi)} lượt"
    dung = [g[1].get("Authorization", "") for g in bat.goi]
    assert dung[0] != dung[1], f"xoay vòng phải đổi khoá, cả 2 lượt đều dùng {dung[0]!r}"


def test_pixabay_het_luot_thi_XOAY_sang_khoa_ke(hai_khoa, monkeypatch):
    bat = _Bat(loi_lan=1)
    monkeypatch.setattr(hut, "_get", bat)
    hut.hut_pixabay("nui", 1)
    assert len(bat.goi) == 2, f"phải thử khoá thứ 2 sau 429, đã gọi {len(bat.goi)} lượt"
    assert bat.goi[0][0] != bat.goi[1][0], "xoay vòng phải đổi khoá trong URL"


def test_het_MOI_khoa_thi_van_nem_loi(hai_khoa, monkeypatch):
    """Cạn khoá thì phải báo — nuốt lỗi là phiên hút im lặng không ra gì."""
    bat = _Bat(loi_lan=99)
    monkeypatch.setattr(hut, "_get", bat)
    with pytest.raises(Exception):
        hut.hut_pexels("nui", 1)
    assert len(bat.goi) == 2, "phải thử HẾT các khoá rồi mới bỏ cuộc"


# ───────────────────────── không phá hành vi cũ ─────────────────────────

def test_MOT_khoa_van_chay_nhu_cu(monkeypatch):
    monkeypatch.setenv("PEXELS_API_KEY", "CHI_MOT_KHOA")
    for i in range(2, 11):
        monkeypatch.delenv(f"PEXELS_API_KEY_{i}", raising=False)
    monkeypatch.delenv("PEXELS_API_KEYS", raising=False)
    bat = _Bat()
    monkeypatch.setattr(hut, "_get", bat)
    hut.hut_pexels("nui", 1)
    assert bat.goi[0][1]["Authorization"] == "CHI_MOT_KHOA"


def test_thieu_khoa_van_bao_ro(monkeypatch):
    """Không có khoá thì báo đúng tên biến — đừng để 401 mơ hồ."""
    monkeypatch.setenv("PEXELS_API_KEY", "")
    for i in range(2, 11):
        monkeypatch.delenv(f"PEXELS_API_KEY_{i}", raising=False)
    monkeypatch.delenv("PEXELS_API_KEYS", raising=False)
    with pytest.raises(RuntimeError, match="PEXELS_API_KEY"):
        hut.hut_pexels("nui", 1)


def test_khoang_trang_va_xuong_dong_cung_tach_duoc(monkeypatch):
    """Két/`.env` có thể ngăn bằng khoảng trắng hoặc xuống dòng, không chỉ dấu phẩy."""
    monkeypatch.setenv("PEXELS_API_KEY", "PX_A\nPX_B PX_C")
    for i in range(2, 11):
        monkeypatch.delenv(f"PEXELS_API_KEY_{i}", raising=False)
    monkeypatch.delenv("PEXELS_API_KEYS", raising=False)
    bat = _Bat()
    monkeypatch.setattr(hut, "_get", bat)
    hut.hut_pexels("nui", 1)
    auth = bat.goi[0][1]["Authorization"]
    assert auth in ("PX_A", "PX_B", "PX_C"), f"tách sai: {auth!r}"
