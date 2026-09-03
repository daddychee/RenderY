r"""Hồ sơ nhịp theo niche — con số từ ĐO THẬT, không phải cảm giác.

Nguồn số (đo 03/09/2026, hai thước độc lập select+scdet HỘI TỤ, xem nhip/do.py):
  Fern ×4 (info/điều tra) + WUFO ×1 (documentary), tách hook/thân:

    Fern hook (info) : trung vị 0,72s · 86% shot ≤2s · đỉnh 54-74 cắt/phút
    Fern thân        : trung vị 2,0-2,2s · ~50% ≤2s · ~20% ≥5s
    Fern điều tra    : hook LEO 3 phút tới đỉnh ~30 (không nổ) · vùng giữa lặng
    WUFO             : hook êm · thân 6,0-6,6s · 5% ≤2s · ~70% ≥5s
    CHU KỲ BÙNG      : 3,1-5,0 phút, trung vị 4,0 — 5/5 video, 3 thể loại, 2 kênh
    BÙNG KẾT         : 4/5 video tăng tốc ở phút chót

  Số ffmpeg là CẬN DƯỚI (hiệu chuẩn trên đáp án 24 cắt: cả 3 thước cùng thấy 12 —
  sót mối nối giữa 2 clip cùng tông màu). Nhịp thật của họ chỉ nhanh hơn.

Vì sao FILE JSON chứ không hằng số: user (15 năm dựng phim) phải chỉnh được bằng
tay khi tai nghề nói khác số đo — hồ sơ là điểm khởi đầu, không phải chân lý.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

THU_MUC_PROFILES = Path(__file__).parent / "profiles"

# Kiểu mở hook — đo được 3 kiểu thật:
#   "no"  : nổ ngay 90s đầu (Fern info: McDonald's đỉnh 71 tại 1:15)
#   "leo" : gây căng dần ~3 phút mới tới đỉnh (Fern điều tra: Hansa 9→19→29)
#   "em"  : không nổ, vào thẳng nền (WUFO)
HOOK_KIEU = ("no", "leo", "em")


@dataclass(frozen=True)
class HoSoNhip:
    """Mục tiêu phân bố độ dài shot cho MỘT niche. Đơn vị: giây."""

    ten: str
    # ---- THÂN (các chương diễn giải) ----
    than_trung_vi: float          # trung vị độ dài shot đích
    than_ty_le_nhanh: float       # tỉ lệ shot ≤2s (0..1)
    than_ty_le_hold: float        # tỉ lệ shot ≥5s (0..1)
    # ---- HOOK (chương H) ----
    hook_kieu: str                # no | leo | em
    hook_trung_vi: float
    hook_ty_le_nhanh: float
    # ---- ĐỢT BÙNG (giữ chân — user chốt: sắp thoát thì tăng nhịp kéo lại) ----
    bung_chu_ky_s: float = 240.0  # ~4 phút — 5/5 video đo được
    bung_he_so: float = 2.0       # mật độ cắt trong đợt bùng = nền × hệ số
    bung_ket: bool = True         # tăng tốc ở phút chót
    # ---- TÁI DÙNG tài sản motif (aigen, Đợt 2 dùng) ----
    gian_cach_tai_dung_s: float = 60.0   # user chốt 03/09

    def kiem(self) -> list[str]:
        """Lỗi cấu hình — trả list rỗng nếu hợp lệ. Người chỉnh JSON bằng tay nên
        phải bắt số vô nghĩa TRƯỚC khi nó chảy vào job 20 phút."""
        loi = []
        if self.hook_kieu not in HOOK_KIEU:
            loi.append(f"hook_kieu '{self.hook_kieu}' — chỉ nhận {'/'.join(HOOK_KIEU)}")
        for ten, v, lo, hi in (
            ("than_trung_vi", self.than_trung_vi, 0.5, 15.0),
            ("hook_trung_vi", self.hook_trung_vi, 0.3, 15.0),
            ("bung_chu_ky_s", self.bung_chu_ky_s, 60.0, 900.0),
            ("bung_he_so", self.bung_he_so, 1.0, 10.0),
        ):
            if not lo <= v <= hi:
                loi.append(f"{ten}={v} ngoài khoảng hợp lý [{lo}, {hi}]")
        for ten, v in (("than_ty_le_nhanh", self.than_ty_le_nhanh),
                       ("than_ty_le_hold", self.than_ty_le_hold),
                       ("hook_ty_le_nhanh", self.hook_ty_le_nhanh)):
            if not 0.0 <= v <= 1.0:
                loi.append(f"{ten}={v} phải trong [0, 1]")
        if self.than_ty_le_nhanh + self.than_ty_le_hold > 1.0:
            loi.append("than_ty_le_nhanh + than_ty_le_hold > 1 — hai nhóm chồng nhau")
        return loi


# Hồ sơ đóng gói sẵn — mỗi niche một file JSON trong profiles/ để user sửa tay.
# Không có file thì rơi về bộ số này (cùng nội dung file lúc đóng gói).
_MAC_DINH: dict[str, dict] = {
    # Life In: du lịch/văn hoá — trường phái documentary NHƯNG nhanh hơn WUFO:
    # video 10-20 phút không có quyền chậm như video 40 phút (user chốt điểm 4),
    # và stock không đẹp tới mức giữ nổi hold 8s như render riêng của WUFO.
    "life-in": dict(than_trung_vi=3.5, than_ty_le_nhanh=0.30, than_ty_le_hold=0.25,
                    hook_kieu="no", hook_trung_vi=1.0, hook_ty_le_nhanh=0.70,
                    bung_he_so=1.8, bung_ket=True),
    # Investigate: theo đúng 2 video điều tra của Fern (Hansa + China Scammer).
    "investigate": dict(than_trung_vi=2.5, than_ty_le_nhanh=0.40, than_ty_le_hold=0.20,
                        hook_kieu="leo", hook_trung_vi=2.0, hook_ty_le_nhanh=0.45,
                        bung_chu_ky_s=270.0, bung_he_so=2.5, bung_ket=True),
    # Mặc định khi niche chưa có hồ sơ: giữa hai cái trên, an toàn cho stock.
    "_mac_dinh": dict(than_trung_vi=3.0, than_ty_le_nhanh=0.35, than_ty_le_hold=0.22,
                      hook_kieu="no", hook_trung_vi=1.2, hook_ty_le_nhanh=0.60,
                      bung_he_so=2.0, bung_ket=True),
}


def nap(niche: str, thu_muc: Path | None = None) -> HoSoNhip:
    """Hồ sơ nhịp cho một niche.

    Thứ tự: file JSON của niche -> bộ đóng gói của niche -> `_mac_dinh`.
    File JSON HỎNG thì báo lỗi RÕ chứ không âm thầm rơi về mặc định — người vừa
    chỉnh tay số mà thấy video ra y như cũ sẽ không hiểu vì sao.
    """
    ten = (niche or "").strip().lower() or "_mac_dinh"
    goc = Path(thu_muc) if thu_muc else THU_MUC_PROFILES
    f = goc / f"{ten}.json"
    if f.is_file():
        try:
            du_lieu = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Hồ sơ nhịp {f.name} hỏng: {exc}") from exc
        hs = HoSoNhip(ten=ten, **{k: v for k, v in du_lieu.items() if k != "ten"})
    elif ten in _MAC_DINH:
        hs = HoSoNhip(ten=ten, **_MAC_DINH[ten])
    else:
        hs = HoSoNhip(ten=ten, **_MAC_DINH["_mac_dinh"])
    loi = hs.kiem()
    if loi:
        raise ValueError(f"Hồ sơ nhịp '{ten}' không hợp lệ: " + "; ".join(loi))
    return hs


def ghi_mau(thu_muc: Path | None = None) -> list[Path]:
    """Xuất bộ hồ sơ đóng gói thành file JSON cho user chỉnh. Không đè file có sẵn."""
    goc = Path(thu_muc) if thu_muc else THU_MUC_PROFILES
    goc.mkdir(parents=True, exist_ok=True)
    ra = []
    for ten, du_lieu in _MAC_DINH.items():
        f = goc / f"{ten}.json"
        if not f.is_file():
            f.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            ra.append(f)
    return ra
