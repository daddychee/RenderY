r"""Cắt video ref thành CẢNH QUAY (không phải câu phụ đề).

Vì sao: ref là phóng sự 52 phút/1GB. Cắt theo phụ đề (bản cũ) cho ra những mẩu
4 giây cắt ngang giữa cú máy — preview giật, kéo vào timeline dính nửa cảnh
trước nửa cảnh sau. Đo 06/09 trên `ref 1.mp4`: 68/516 khúc cắt đúng giữa mạch
nói liền, tức cắt giữa hình.

Ba luật, đều rút từ số đo thật (300s đầu + toàn file):
  1. GỘP MÁY ĐỘNG — mốc cách nhau <= GOP_S là MỘT cảnh. Kiểm bằng mắt cụm
     65-67s: không phải dissolve mà là máy quay gắn trên ô tô đang chạy; chẻ ra
     sẽ được 5 mẩu 0.5s vô dụng. Vùng gộp dài > MAY_DONG_S thì gắn cờ `may_dong`
     (hình chuyển thì tốt, làm hình tĩnh 3-5s thì hỏng).
  2. BỎ CẢNH NGẮN — < TOI_THIEU_S không bao giờ vào timeline (dải dựng 3-5s).
  3. CHẺ CẢNH DÀI — > TOI_DA_S chẻ đôi.

Ngưỡng NGUONG=0.30 chọn theo phân bố: trung vị 2.67s, p25 2.0s, p75 3.83s —
khớp nhịp dựng thật. 0.15 băm nát mọi cú lia (140 cảnh/300s), 0.45 nuốt mất
cắt nhanh trong cao trào (61 cảnh/300s).
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

NGUONG = 0.30           # ngưỡng đổi hình của ffmpeg scene detect
FPS_QUET = 6            # hạ mẫu: quét 52 phút hết 78s thay vì hàng chục phút
RONG_QUET = 160         # thu nhỏ khung — không đổi kết quả, nhanh hơn nhiều
GOP_S = 0.5             # mốc cách nhau <= mức này là cùng MỘT chuyển động
MAY_DONG_S = 0.5        # vùng gộp >= mức này -> máy quay đang động, gắn cờ.
                        # Đo toàn file 06/09: 25 cụm gộp, dài nhất đúng 0.5s —
                        # ngưỡng 1.5s (đặt theo 300s đầu) không bao giờ bật.
TOI_THIEU_S = 2.0       # < mức này: bỏ (user chốt 06/09)
TOI_DA_S = 12.0         # > mức này: chẻ đôi


@dataclass
class Canh:
    t0: float
    t1: float
    may_dong: bool = False

    @property
    def dai(self) -> float:
        return self.t1 - self.t0


def _thoi_luong(video: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(video)],
        capture_output=True, text=True)
    try:
        return float((r.stdout or "0").strip())
    except ValueError:
        return 0.0


def quet_moc(video: Path, nguong: float = NGUONG) -> list[float]:
    """Mốc đổi hình (giây) do ffmpeg scene detect. Hạ mẫu để chạy nhanh."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video),
         "-vf", f"fps={FPS_QUET},scale={RONG_QUET}:-2,"
                f"select='gt(scene,{nguong})',metadata=print:file=-",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stdout or "")]


def gop_may_dong(moc: list[float], gop_s: float = GOP_S) -> list[tuple[float, bool]]:
    """[mốc thô] -> [(mốc, có phải máy đang động)] — cụm mốc sát nhau gộp làm một."""
    if not moc:
        return []
    ra: list[tuple[float, bool]] = []
    dau = last = moc[0]
    for t in moc[1:]:
        if t - last <= gop_s:
            last = t
            continue
        ra.append((dau, last - dau >= MAY_DONG_S))
        dau = last = t
    ra.append((dau, last - dau >= MAY_DONG_S))
    return ra


def cat_canh(video: Path, nguong: float = NGUONG,
             toi_thieu_s: float = TOI_THIEU_S,
             toi_da_s: float = TOI_DA_S) -> list[Canh]:
    """Video -> danh sách CẢNH đã lọc/chẻ, sẵn sàng nạp vào Library."""
    het = _thoi_luong(video)
    if het <= 0:
        return []
    gop = gop_may_dong(quet_moc(video, nguong))
    # ranh cảnh = [0, mốc..., hết]; cờ máy-động của mốc MỞ ĐẦU cảnh đó
    ranh: list[tuple[float, bool]] = [(0.0, False)] + gop + [(het, False)]
    ra: list[Canh] = []
    for i in range(len(ranh) - 1):
        t0, dong = ranh[i]
        t1 = ranh[i + 1][0]
        if t1 - t0 < toi_thieu_s:          # luật 2: bỏ cảnh vụn
            continue
        if t1 - t0 > toi_da_s:             # luật 3: chẻ ĐỀU tới khi vừa khung
            # chẻ đôi MỘT lần không đủ: cảnh 21.4s chẻ đôi vẫn còn 10.7s, mà
            # cảnh 25s thì thành 12.5s — vẫn quá khung (đo 06/09: sót 12 cảnh)
            n = int((t1 - t0) // toi_da_s) + 1
            buoc = (t1 - t0) / n
            for j in range(n):
                ra.append(Canh(t0 + j * buoc, t0 + (j + 1) * buoc, dong))
        else:
            ra.append(Canh(t0, t1, dong))
    return ra
