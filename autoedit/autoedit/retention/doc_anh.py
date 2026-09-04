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

    Gridline = HÀNG NGANG MẢNH (đường kẻ, không phải diện tích nền) màu xám nhạt,
    trải rộng LIÊN TỤC — khác nền trắng/xám nhạt của cả ảnh chụp (bug 04/09, ảnh
    thật Trịnh Ngọc Hải: nền JPG hơi ngả xám lọt đúng ngưỡng r<=248 cũ, hàng nền
    dưới ảnh bị nhận nhầm là gridline 0%, x_r kéo dài hết chiều rộng ẢNH thay vì
    chiều rộng CHART thật -> tỉ lệ phủ đường xanh bị tính hụt còn 32%).

    Phân biệt bằng ĐỘ DÀY: gridline thật dày 1-3px xen giữa các hàng KHÔNG xám
    (nền trắng thật của ô biểu đồ, hoặc đường cong/chữ) phía trên và dưới nó.
    Hàng xám của cả một VÙNG NỀN thì hàng liền kề cũng xám -> bị loại.
    """
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    xam = ((np.abs(r - g) < 14) & (np.abs(g - b) < 14)
           & (r >= 190) & (r <= 248))
    tyle = xam.mean(axis=1)
    la_hang_xam = tyle > 0.5
    # mảnh: hàng xám mà hàng NGAY TRÊN và NGAY DƯỚI (cách 4px, qua khỏi nét dày
    # nhất 3px của đường kẻ) không xám — tức nó nổi giữa nền không-xám thật.
    n = len(la_hang_xam)
    manh = np.zeros(n, dtype=bool)
    for y in np.where(la_hang_xam)[0]:
        tren = tyle[max(0, y - 4)] <= 0.5
        duoi = tyle[min(n - 1, y + 4)] <= 0.5
        manh[y] = tren or duoi
    hang = np.where(manh)[0]
    if len(hang) < 2:
        raise AnhKhongDoDuoc(
            "không thấy đường kẻ ngang của biểu đồ — chụp đủ khung retention "
            "(cả vạch 100% trên cùng lẫn 0% dưới cùng), không lẫn nền trang")
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
    # bề ngang khung: đoạn LIÊN TỤC dài nhất mà đường 0% thực sự kẻ (tránh lề/
    # chữ số trục hoành cũng lọt ngưỡng xám nằm rời rạc ngoài đoạn kẻ liền mạch).
    cot_xam = np.where(xam[y_bot if y_bot < a.shape[0] else -1])[0]
    if len(cot_xam) == 0:
        raise AnhKhongDoDuoc("đường kẻ 0% quá mờ/đứt đoạn — chụp lại rõ hơn")
    ngat = np.where(np.diff(cot_xam) > 3)[0]
    bien = [0, *(ngat + 1).tolist(), len(cot_xam)]
    doan = max(((bien[i], bien[i + 1]) for i in range(len(bien) - 1)),
              key=lambda ab: cot_xam[ab[1] - 1] - cot_xam[ab[0]])
    x_l, x_r = int(cot_xam[doan[0]]), int(cot_xam[doan[1] - 1])
    return y_top, y_bot, x_l, x_r


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
    # kiểm chân lý: retention chạm 100% Ở ĐÂU ĐÓ rất gần đầu (giây đầu tiên) —
    # KHÔNG đòi cột đầu tiên đo được phải cao (bug 04/09, báo bởi Trịnh Ngọc Hải:
    # video hook yếu tụt thật xuống ~70% chỉ trong vài giây, đây là DỮ LIỆU THẬT
    # chứ không phải ảnh bị cắt — ép ngưỡng 80% từ chối đúng ca cần đo nhất).
    # Ảnh THỰC SỰ cắt mất đầu thì đỉnh cao nhất trong 10% đầu vẫn thấp hẳn dưới
    # mốc chuẩn 95% (YouTube luôn vẽ đúng 100% tại t=0, kể cả khi tụt ngay sau đó).
    dinh_dau = max(p for x, p in ra if x <= 0.10)
    if dinh_dau < 0.90:
        raise AnhKhongDoDuoc(
            f"đỉnh cao nhất trong 10% đầu chỉ {dinh_dau:.0%} — retention luôn "
            "chạm 100% ngay tại 0:00; ảnh có lẽ bị cắt mất đoạn mở đầu hoặc "
            "chụp thiếu góc trên bên trái")
    # resample đều: nội suy tuyến tính trên lưới so_diem điểm
    xs = np.array([p[0] for p in ra])
    ps = np.array([p[1] for p in ra])
    luoi = np.linspace(0.0, 1.0, so_diem)
    return list(zip(luoi.tolist(), np.interp(luoi, xs, ps).tolist()))
