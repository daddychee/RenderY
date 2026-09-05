r"""Đo NHỊP DỰNG của video bất kỳ — tính năng "học nhịp từ video input".

Hai thước ĐỘC LẬP, giữ vì đã kiểm chứng hội tụ (03/09, video Fern 28'):
  select gt(scene,0.3): 472 cắt · scdet: 526 cắt — lệch <12%, trung vị trùng.
Thước thứ ba (YDIF ngưỡng thích nghi) đã thử và LOẠI: đồ hoạ chuyển động đánh
lừa nó đếm 1552 cắt (trung vị 0,24s — vô lý).

⚠ SỐ LÀ CẬN DƯỚI. Hiệu chuẩn trên video đáp-án-đã-biết (24 mối cắt): cả hai
thước cùng thấy 12 — sót mối nối giữa hai clip CÙNG TÔNG MÀU. So sánh tương đối
giữa các video vẫn đúng (cùng thước); tuyệt đối thì nhịp thật nhanh hơn số đo.

Bài học đắt từ BAN_GIAO_M4 (21/07): "3 lần script báo đúng, 3 lần user mở CapCut
bác lại" — số đo không thay được tai/mắt người. Module này chỉ MÔ TẢ, kết luận
đạt/không giao cho cổng mắt của user.
"""

from __future__ import annotations

import re
import statistics
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

NGUONG_SELECT = 0.30
HOOK_S = 90.0        # cửa sổ hook để tách thống kê (quy ước, khớp phép đo gốc)
NHANH_S = 2.0        # shot "chớp"
HOLD_S = 5.0         # cú hold (cùng mốc dna.py)
CUA_SO_CONG = 60.0   # đường cong nhịp: cửa sổ trượt 60s
BUOC_CONG = 15.0


class DoNhipError(RuntimeError):
    """Không đo được video — file hỏng/ffmpeg thiếu."""


# ------------------------------------------------------------- dò điểm cắt
def _ffmpeg(args: list[str]) -> str:
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner"] + args,
                           capture_output=True, text=True, errors="replace")
    except OSError as exc:
        raise DoNhipError(f"không chạy được ffmpeg: {exc}") from exc
    return r.stderr


def diem_cat_select(video: Path, nguong: float = NGUONG_SELECT) -> list[float]:
    err = _ffmpeg(["-i", str(video),
                   "-filter:v", f"select='gt(scene,{nguong})',showinfo",
                   "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", err)]


def diem_cat_scdet(video: Path) -> list[float]:
    err = _ffmpeg(["-i", str(video), "-filter:v", "scdet=threshold=10",
                   "-f", "null", "-"])
    return [float(m) for m in re.findall(r"lavfi\.scd\.time:\s*([0-9.]+)", err)]


def do_dai_video(video: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video)], capture_output=True, text=True)
        return float(r.stdout.strip())
    except (OSError, ValueError) as exc:
        raise DoNhipError(f"không đọc được độ dài {Path(video).name}: {exc}") from exc


# --------------------------------------------------------------- thống kê
@dataclass
class ThongKeDoan:
    """Số đặc trưng của một ĐOẠN (hook hoặc thân)."""

    so_shot: int
    trung_vi: float
    cat_moi_phut: float
    ty_le_nhanh: float      # shot ≤ NHANH_S
    ty_le_hold: float       # shot ≥ HOLD_S
    dai_dong: float         # p90/p10


def thong_ke_doan(cat: list[float], t0: float, t1: float) -> ThongKeDoan | None:
    """Thống kê shot trong cửa sổ [t0, t1). None nếu quá ít dữ liệu."""
    moc = [t0] + sorted(c for c in cat if t0 < c < t1) + [t1]
    shot = [moc[i + 1] - moc[i] for i in range(len(moc) - 1) if moc[i + 1] > moc[i]]
    if len(shot) < 3:
        return None
    s, n = sorted(shot), len(shot)
    return ThongKeDoan(
        so_shot=n,
        trung_vi=round(statistics.median(shot), 2),
        cat_moi_phut=round(n / ((t1 - t0) / 60), 1),
        ty_le_nhanh=round(sum(1 for d in shot if d <= NHANH_S) / n, 2),
        ty_le_hold=round(sum(1 for d in shot if d >= HOLD_S) / n, 2),
        dai_dong=round(s[int(n * .9)] / max(s[int(n * .1)], .01), 1),
    )


def duong_cong(cat: list[float], tong: float,
               cua_so: float = CUA_SO_CONG, buoc: float = BUOC_CONG,
               ) -> list[tuple[float, float]]:
    """[(mốc giữa cửa sổ, cắt/phút)] — nhịp biến thiên theo thời gian."""
    ra, t = [], 0.0
    while t + cua_so <= tong:
        n = sum(1 for c in cat if t <= c < t + cua_so)
        ra.append((t + cua_so / 2, n / (cua_so / 60)))
        t += buoc
    return ra


def dinh_bung(cong: list[tuple[float, float]], he_so: float = 1.5,
              gian_cach_s: float = 90.0) -> list[tuple[float, float]]:
    """Đỉnh cục bộ vượt trung vị `he_so` lần — các đợt bùng (re-hook).

    Đo 5 video: chu kỳ 3,1-5,0 phút, trung vị 4,0 — cơ sở của bung_chu_ky_s
    trong hồ sơ nhịp.
    """
    if len(cong) < 5:
        return []
    nen = statistics.median(v for _, v in cong)
    ra: list[tuple[float, float]] = []
    for i in range(2, len(cong) - 2):
        t, v = cong[i]
        if v >= nen * he_so and v == max(x[1] for x in cong[i - 2:i + 3]):
            if not ra or t - ra[-1][0] >= gian_cach_s:
                ra.append((t, v))
    return ra


@dataclass
class KetQuaDo:
    """Kết quả đo trọn một video — hai thước + hook/thân + đường cong."""

    video: str
    tong_s: float
    hook: dict[str, ThongKeDoan | None] = field(default_factory=dict)   # theo thước
    than: dict[str, ThongKeDoan | None] = field(default_factory=dict)
    bung: list[tuple[float, float]] = field(default_factory=list)
    chu_ky_bung_s: float | None = None
    cong: list[tuple[float, float]] = field(default_factory=list)  # [(t, cắt/phút)] — đồ thị nhịp

    def hoi_tu(self, lech_toi_da: float = 0.25) -> bool:
        """Hai thước có hội tụ không (trung vị thân lệch ≤25%)? Không hội tụ thì
        video này đánh lừa được thước (đồ hoạ nhấp nháy...) — số không đáng tin."""
        a, b = self.than.get("select"), self.than.get("scdet")
        if a is None or b is None:
            return False
        return abs(a.trung_vi - b.trung_vi) / max(a.trung_vi, b.trung_vi) <= lech_toi_da


def do_video(video: Path) -> KetQuaDo:
    """Đo trọn: 2 thước, tách hook/thân, đường cong + đợt bùng (theo thước select)."""
    video = Path(video)
    if not video.is_file():
        raise DoNhipError(f"không thấy file {video}")
    tong = do_dai_video(video)
    kq = KetQuaDo(video=video.name, tong_s=tong)
    cat_sel = diem_cat_select(video)
    for ten, cat in (("select", cat_sel), ("scdet", diem_cat_scdet(video))):
        kq.hook[ten] = thong_ke_doan(cat, 0.0, min(HOOK_S, tong))
        kq.than[ten] = thong_ke_doan(cat, min(HOOK_S, tong), tong)
    kq.cong = duong_cong(cat_sel, tong)
    kq.bung = dinh_bung(kq.cong)
    if len(kq.bung) >= 2:
        khoang = [kq.bung[i + 1][0] - kq.bung[i][0] for i in range(len(kq.bung) - 1)]
        kq.chu_ky_bung_s = round(statistics.median(khoang), 0)
    return kq
