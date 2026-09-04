r"""Đọc ĐƯỜNG CONG retention từ ẢNH CHỤP biểu đồ YouTube Studio.

User 04/09: "Không thể xuất CSV retention, chỉ có ảnh" — nên đo thẳng trên ảnh
bằng pixel (Python đo, không nhờ LLM đoán số):

  1. Tìm các ĐƯỜNG KẺ NGANG xám nhạt (gridline) — YouTube kẻ đều 0/33/66/100%:
     đường trên cùng = 100%, dưới cùng = 0% -> thước đo trục tung.
  2. Tách đường màu XANH NGỌC ("Video này") khỏi nền: xanh dương trội hẳn đỏ và
     bão hoà đủ cao — loại được dải xám "thông thường", nền hồng nhạt vùng bôi,
     vạch đỏ 0:00 và chấm legend (legend nằm NGOÀI khung gridline nên bị cắt).
  3. Mỗi cột x lấy median y của pixel xanh -> (x_frac 0..1, retention 0..1).

Trục hoành ảnh không tự đọc được (nhãn 28:25 là chữ) — thời lượng tập cũ do
editor nhập khi nộp job; x_frac × thời lượng = giây thật.

Ảnh không đo được (thiếu gridline, thiếu đường xanh) thì NỔ AnhKhongDoDuoc với
lý do rõ — thà bắt nộp lại ảnh còn hơn im lặng chỉnh nhịp theo số rác.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class AnhKhongDoDuoc(ValueError):
    """Ảnh chụp không đo được — thông điệp tiếng Việt, in thẳng cho editor."""


def _gridlines(a: np.ndarray) -> tuple[int, int, int, int]:
    """Tìm khung gridline: (y_top, y_bottom, x_left, x_right).

    Gridline = hàng có nhiều pixel xám nhạt (kênh gần bằng nhau, sáng) trải rộng.
    """
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    xam = ((np.abs(r - g) < 14) & (np.abs(g - b) < 14)
           & (r >= 190) & (r <= 248))
    tyle = xam.mean(axis=1)
    hang = np.where(tyle > 0.5)[0]
    if len(hang) < 2:
        raise AnhKhongDoDuoc(
            "không thấy đường kẻ ngang của biểu đồ — chụp đủ khung retention "
            "(cả vạch 100% trên cùng lẫn 0% dưới cùng)")
    # gom hàng liền kề thành từng đường
    duong = [int(hang[0])]
    for y in hang[1:]:
        if y - duong[-1] > 3:
            duong.append(int(y))
        else:
            duong[-1] = int(y)          # lấy mép dưới của vệt
    if len(duong) < 2:
        raise AnhKhongDoDuoc("chỉ thấy 1 đường kẻ ngang — ảnh cắt mất khung")
    y_top, y_bot = duong[0], duong[-1]
    # bề ngang khung: đoạn x mà đường 0% thực sự kẻ (tránh lề trắng 2 bên)
    cot = np.where(xam[y_bot if y_bot < a.shape[0] else -1])[0]
    return y_top, y_bot, int(cot.min()), int(cot.max())


def doc_duong_cong(anh: Path, so_diem: int = 200) -> list[tuple[float, float]]:
    """Ảnh chụp -> [(x_frac 0..1, retention 0..1)] đã resample đều so_diem điểm."""
    from PIL import Image

    a = np.asarray(Image.open(anh).convert("RGB"))
    y_top, y_bot, x_l, x_r = _gridlines(a)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    xanh = ((b - r > 30) & (g - r > 15) & (b > 90)
            & ((np.maximum(np.maximum(r, g), b)
                - np.minimum(np.minimum(r, g), b)) > 55))
    xanh[: y_top - 2] = False           # cắt legend/chữ phía trên khung
    xanh[y_bot + 3:] = False
    xanh[:, :x_l] = False
    xanh[:, x_r + 1:] = False

    cot_co = np.where(xanh.any(axis=0))[0]
    if len(cot_co) < (x_r - x_l) * 0.35:
        raise AnhKhongDoDuoc(
            f"đường retention màu xanh chỉ phủ {len(cot_co)} cột "
            f"({100 * len(cot_co) // max(1, x_r - x_l)}% bề ngang) — cần ảnh rõ "
            "hơn, không che khuất đường 'Video này'")
    x0, x1 = int(cot_co.min()), int(cot_co.max())
    ys = np.arange(a.shape[0])
    ra: list[tuple[float, float]] = []
    for x in cot_co:
        yy = ys[xanh[:, x]]
        y_mid = float(np.median(yy))
        pct = (y_bot - y_mid) / max(1.0, (y_bot - y_top))
        ra.append(((x - x0) / max(1, x1 - x0), min(1.0, max(0.0, pct))))
    # kiểm chân lý: retention LUÔN bắt đầu ~100%
    if ra[0][1] < 0.80:
        raise AnhKhongDoDuoc(
            f"điểm đầu đường cong chỉ {ra[0][1]:.0%} — retention phải bắt đầu "
            "100%; ảnh có lẽ bị cắt mất đoạn mở đầu")
    # resample đều: nội suy tuyến tính trên lưới so_diem điểm
    xs = np.array([p[0] for p in ra])
    ps = np.array([p[1] for p in ra])
    luoi = np.linspace(0.0, 1.0, so_diem)
    return list(zip(luoi.tolist(), np.interp(luoi, xs, ps).tolist()))
