"""Chất liệu 3 STYLE (user chốt 07/10/2026, duyệt bằng 3 video thử "Những thành phố mơ màng"):
Collage art · Black Grid · Non-Grid. Thông số lấy nguyên từ bản thử đã duyệt.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from autoedit.collage.nhip import nhieu_muot, posterize

KEM = (0.95, 0.94, 0.88)                  # giấy kem (bài mẫu Vox)
NEN_TOI = (0.075, 0.075, 0.082)
TEN = {"collage": "Collage art", "black_grid": "Black Grid", "non_grid": "Non-Grid"}
FPS = {"collage": 30, "black_grid": 12, "non_grid": 12}       # Vox: posterize 12 hình/giây, xuất 24


def nen_luoi(h: int, w: int) -> np.ndarray:
    """Nền tối + lưới mảnh 60 px (theo khung 1920), đậm 10%."""
    s = w / 1920
    buoc, day = max(8, round(60 * s)), max(1, round(2 * s))
    a = np.zeros((h, w), np.float32)
    for x in range(0, w, buoc):
        a[:, x:x + day] = 1
    for y in range(0, h, buoc):
        a[y:y + day] = 1
    return np.float32(NEN_TOI) * (1 - 0.10 * a[..., None]) + 0.10 * a[..., None]


def vien_giay(rgb, a, seed: int = 0, s: float = 1.0):
    """Viền trắng kiểu STICKER ~7 px + bóng đổ lệch (12, 9) mờ 9. User chốt 08/10 (ảnh Non-Grid nhóm CIA):
    viền giấy xé cộng nhiễu ±2,2 px trông nham nhở -> "tròn liền khối": dày ĐỀU, mép ngoài TRÒN TRƠN (làm mượt
    trường khoảng cách), khe hẹp hơn 2 lần viền lấp liền. `s`: px nguồn cho mỗi px xuất; `seed` giữ để tương
    thích lời gọi cũ. Trả (màu alpha THẲNG, alpha)."""
    a = np.asarray(a, np.float32)
    R = 7 * s
    trong = a >= 0.5
    kc = (ndi.distance_transform_edt(~trong) - ndi.distance_transform_edt(trong)).astype(np.float32)  # >0: ngoài vật
    kc = ndi.gaussian_filter(kc, 0.35 * R)                             # bo tròn đường viền, mất bậc thang
    v = np.clip((R - kc) / max(s, 1e-3) + 0.5, 0, 1)                    # mép ngoài mềm ~1 px xuất
    # dịch KHÔNG cuộn vòng: đo thật 07/10 np.roll đẩy bóng tảng đá sát đáy lên tận mép trên -> hộp bao
    # lớp phủ cả khung, camera Black Grid không còn cú nào
    mo, dy, dx = ndi.gaussian_filter(v, 9 * s), round(9 * s), round(12 * s)
    bong = np.zeros_like(mo)
    bong[dy:, dx:] = mo[:mo.shape[0] - dy, :mo.shape[1] - dx] * 0.5
    p_rgb = np.asarray(rgb, np.float32) * a[..., None] + np.float32(KEM) * (v * (1 - a))[..., None]
    p_a = a + v * (1 - a)
    p_a2 = p_a + bong * (1 - p_a)
    return p_rgb / np.maximum(p_a2, 1e-6)[..., None], p_a2


def _hat(h: int, w: int, seed: int, cuong_do: float, tb):
    """Hạt phim: nhiễu chuẩn làm mờ 0,65 px, chuẩn hoá, quanh 0,5 — sinh NGAY trên thiết bị của khung hình."""
    import torch
    import torch.nn.functional as Fn

    g = torch.Generator(device=tb).manual_seed(int(seed))
    n = torch.randn((1, 1, h, w), generator=g, device=tb)
    k = torch.exp(-0.5 * (torch.arange(-3, 4, device=tb, dtype=torch.float32) / 0.65) ** 2)
    k = k / k.sum()
    n = Fn.conv2d(Fn.pad(n, (3, 3, 0, 0), mode="reflect"), k.view(1, 1, 1, -1))
    n = Fn.conv2d(Fn.pad(n, (0, 0, 3, 3), mode="reflect"), k.view(1, 1, -1, 1))[0, 0]
    return (0.5 + 0.11 * cuong_do * n / (n.std() + 1e-6)).clamp(0, 1)[..., None]


def _overlay(nen, lop, dam):
    import torch

    o = torch.where(nen < 0.5, 2 * nen * lop, 1 - 2 * (1 - nen) * (1 - lop))
    return nen + (o - nen) * dam


_TOI_VIEN: dict = {}


def hau_ky(img, i: int, t: float, style: str):
    """Collage art: hạt nhẹ 15%. Black Grid / Non-Grid: nhấp nháy máy chiếu 3,5% (đổi 6 lần/giây)
    + hạt 33%. Cả ba: tối viền 28%. Nhận tensor torch (chạy NGAY trên thiết bị của nó — đo 09/10 GTX 1070 Ti:
    hậu kỳ numpy CPU 504 ms/khung, dựng khung trên card chỉ 17 ms) hoặc mảng numpy; trả cùng kiểu."""
    import torch

    la_np = not isinstance(img, torch.Tensor)
    x = torch.from_numpy(np.ascontiguousarray(img, np.float32)) if la_np else img
    h, w = x.shape[:2]
    tb = x.device
    if (h, w, str(tb)) not in _TOI_VIEN:
        yy, xx = torch.meshgrid(torch.arange(h, device=tb, dtype=torch.float32),
                                torch.arange(w, device=tb, dtype=torch.float32), indexing="ij")
        _TOI_VIEN[(h, w, str(tb))] = (1 - 0.28 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
                                      )[..., None]
    x = x.clamp(0, 1)
    if style == "collage":
        x = _overlay(x, _hat(h, w, i, 0.8, tb), 0.15)
    else:
        x = (x * (1 + 0.035 * nhieu_muot(9, 2, posterize(t, 6)))).clamp(0, 1)
        x = _overlay(x, _hat(h, w, i, 1.2, tb), 0.33)
    x = (x * _TOI_VIEN[(h, w, str(tb))]).clamp(0, 1)
    return x.numpy() if la_np else x
