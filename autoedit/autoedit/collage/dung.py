"""Động cơ dựng 2.5D bằng torch — CPU hôm nay, GPU khi nâng cấp, CÙNG một code.

Một camera pinhole cho mọi thứ (đo thật trên clip user duyệt ca1→ca2):

    xo = F * (X*Z0 - tx) / (Z - Tz) + pan          (toạ độ màn hình, gốc = tâm khung)

- X, Y: toạ độ trên ảnh gốc, đơn vị px XUẤT (ảnh gốc phóng S0 = W/PW*zoom).
- Z0: độ sâu khớp ảnh gốc khi đứng yên (bù scale) -> camera (0,0,0,1,0,0) = ảnh gốc.
- Dịch thân máy (tx, ty, Tz) mới ra parallax; F và pan chỉ phóng/dịch đều.
- Nền có độ sâu TỪNG PIXEL: giải ngược điểm ảnh -> điểm trên ảnh (3 vòng lặp).
- Mảnh `z_test`: nền gần hơn thì nền che mảnh (núi che bưởi).

Toạ độ lấy mẫu theo CHỈ SỐ PIXEL như cv2.remap/warpAffine của bản thử đã duyệt
(`F:\\AutoEdit\\collage_test\\ca_chuyen_dong.py`) — để khung ra khớp mốc vàng.
"""

from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn.functional as Fn


def _thiet_bi(ten: str | None) -> torch.device:
    if ten:
        return torch.device(ten)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Lop:
    """Một mảnh (layer). `anh` RGBA alpha THẲNG, float32 [0,1].

    Không truyền X/Y/k: `anh` cùng cỡ ảnh gốc của cảnh, đặt đúng chỗ -> Canh.them tự cắt
    sát và tính vị trí. Truyền X/Y/k: mảnh đặt tự do (vd vật nối cảnh bay vào).
    `anim(t) -> (lệch_x, lệch_y, góc_độ, phóng, dz)`; lệch theo đơn vị px xuất lúc đứng yên.
    Thứ tự vẽ: xa trước gần sau (theo Z lúc đó); `tang` lớn hơn = ép vẽ sau cùng (vật nối
    cảnh cố ý đè lên mọi thứ dù Z xa hơn).
    """

    def __init__(self, anh, Z0: float, anim=None, z_test: bool = False, X=None, Y=None, k=None,
                 tang: int = 0):
        self.anh = np.asarray(anh, np.float32)
        self.Z0 = float(Z0)
        self.anim = anim or (lambda t: (0.0, 0.0, 0.0, 1.0, 0.0))
        self.z_test = z_test
        self.tang = tang
        self.X, self.Y, self.k = X, Y, k
        self._cache: dict = {}

    def tensor(self, tb: torch.device) -> torch.Tensor:
        """Premultiplied, (4, h, w) — cache theo thiết bị."""
        if tb not in self._cache:
            a = torch.from_numpy(self.anh).to(tb)
            p = torch.cat([a[..., :3] * a[..., 3:], a[..., 3:]], -1)
            self._cache[tb] = p.permute(2, 0, 1).contiguous()
        return self._cache[tb]


class Canh:
    def __init__(self, nen, z, W: int, H: int, zoom: float = 1.0):
        self.nen = np.asarray(nen, np.float32)
        self.PH, self.PW = self.nen.shape[:2]
        self.z = np.asarray(z, np.float32)
        self.W, self.H = int(W), int(H)
        self.S0 = W / self.PW * zoom
        self.phang = float(self.z.max() - self.z.min()) < 1e-6
        self.lop: list[Lop] = []
        self._cache: dict = {}

    def them(self, lop: Lop) -> Lop:
        if lop.X is None:
            ys, xs = np.nonzero(lop.anh[..., 3] > 0.01)
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            lop.X = ((x0 + x1) / 2 - self.PW / 2) * self.S0
            lop.Y = ((y0 + y1) / 2 - self.PH / 2) * self.S0
            lop.k = self.S0
            lop.anh = lop.anh[y0:y1, x0:x1]
        self.lop.append(lop)
        return lop

    def tensor(self, tb: torch.device):
        if tb not in self._cache:
            nen = torch.from_numpy(self.nen).to(tb).permute(2, 0, 1)[None]
            z = torch.from_numpy(self.z).to(tb)[None, None]
            uu = torch.arange(self.W, device=tb, dtype=torch.float32) - self.W / 2
            vv = torch.arange(self.H, device=tb, dtype=torch.float32) - self.H / 2
            vv, uu = torch.meshgrid(vv, uu, indexing="ij")
            self._cache[tb] = (nen, z, uu, vv)
        return self._cache[tb]


def _lay_mau(img: torch.Tensor, mx: torch.Tensor, my: torch.Tensor, phan_xa: bool, h: int, w: int):
    """grid_sample theo CHỈ SỐ PIXEL (align_corners=True) = cv2.remap INTER_LINEAR."""
    gx = 2 * mx / max(w - 1, 1) - 1
    gy = 2 * my / max(h - 1, 1) - 1
    g = torch.stack([gx, gy], -1)[None]
    return Fn.grid_sample(img, g, mode="bilinear", align_corners=True,
                          padding_mode="reflection" if phan_xa else "zeros")


def dung_khung(canh: Canh, cam, t: float, thiet_bi: str | None = None, phan_xa: bool = False,
               tra_phu: bool = False, tensor: bool = False):
    """Dựng 1 khung. cam = (tx, ty, Tz, F, pan_x, pan_y). Trả (ảnh HxWx3 float32, tỉ lệ lộ mép).

    `lo` = phần khung lấy mẫu RA NGOÀI tấm nền (lộ mép) — phải = 0 ngoài lúc lia vút.
    `tra_phu`: trả thêm mặt nạ HxW (bool) chỗ tấm nền PHỦ — để ghép ảnh kế bên vào chỗ trống.
    `tensor`: trả tensor torch NGAY TRÊN thiết bị (không chép về CPU) — dựng bằng card thì nhoè + hậu kỳ chạy
    tiếp trên card, mỗi khung chỉ chép về một lần lúc xuất.
    """
    tb = _thiet_bi(thiet_bi)
    tx, ty, tz, F, px, py = (float(v) for v in cam)
    nen, z, uu, vv = canh.tensor(tb)
    W, H, PW, PH, S0 = canh.W, canh.H, canh.PW, canh.PH, canh.S0
    xo, yo = uu - px, vv - py
    if canh.phang:
        Z = torch.full_like(uu, float(canh.z.flat[0]))
        X, Y = (xo * (Z - tz) / F + tx) / Z, (yo * (Z - tz) / F + ty) / Z
    else:
        X, Y = xo.clone(), yo.clone()
        for _ in range(3):
            Z = _lay_mau(z, X / S0 + PW / 2, Y / S0 + PH / 2, False, PH, PW)[0, 0]
            # cv2 BORDER_REPLICATE: ngoài tấm thì lấy độ sâu mép gần nhất
            Z = torch.where(Z > 0, Z, _lay_mau(z, (X / S0 + PW / 2).clamp(0, PW - 1),
                                               (Y / S0 + PH / 2).clamp(0, PH - 1), False, PH, PW)[0, 0])
            X, Y = (xo * (Z - tz) / F + tx) / Z, (yo * (Z - tz) / F + ty) / Z
    mx, my = X / S0 + PW / 2, Y / S0 + PH / 2
    ngoai = (mx < 0) | (mx > PW - 1) | (my < 0) | (my > PH - 1)
    lo = float(ngoai.float().mean())
    out = _lay_mau(nen, mx, my, phan_xa, PH, PW)[0]                    # (3, H, W)

    # Xa vẽ trước, gần vẽ sau (collage 3 trạm 06/10: vẽ theo thứ tự khai báo -> trăng xa đè người gần)
    trang_thai = [(lop, tuple(float(v) for v in lop.anim(t))) for lop in canh.lop]
    trang_thai.sort(key=lambda x: (x[0].tang, -(x[0].Z0 + x[1][4])))
    for lop, (ox, oy, r, sc_m, dz) in trang_thai:
        Zc = lop.Z0 + dz
        if Zc - tz < 0.3:                                               # đã bay qua ống kính
            continue
        sc = F * lop.Z0 / (Zc - tz)
        cx = F * ((lop.X + ox) * lop.Z0 - tx) / (Zc - tz) + W / 2 + px
        cy = F * ((lop.Y + oy) * lop.Z0 - ty) / (Zc - tz) + H / 2 + py
        g = sc * lop.k * sc_m
        h, w = lop.anh.shape[:2]
        co, si = math.cos(math.radians(r)), math.sin(math.radians(r))
        A = np.array([[g * co, -g * si], [g * si, g * co]], np.float64)
        b = np.array([cx, cy]) - A @ np.array([w / 2, h / 2])
        goc = np.array([[0, 0], [w, 0], [0, h], [w, h]], np.float64) @ A.T + b
        x0, y0 = np.maximum(np.floor(goc.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(goc.max(0)).astype(int), (W, H))
        if x1 <= x0 or y1 <= y0:
            continue
        Ai = np.linalg.inv(A)
        gy_, gx_ = torch.meshgrid(torch.arange(y0, y1, device=tb, dtype=torch.float32),
                                  torch.arange(x0, x1, device=tb, dtype=torch.float32), indexing="ij")
        sx, sy = gx_ - float(b[0]), gy_ - float(b[1])
        mxl = float(Ai[0, 0]) * sx + float(Ai[0, 1]) * sy
        myl = float(Ai[1, 0]) * sx + float(Ai[1, 1]) * sy
        P = _lay_mau(lop.tensor(tb)[None], mxl, myl, False, h, w)[0]   # (4, h', w') premult
        if lop.z_test:                                                  # nền gần hơn -> nền che mảnh
            P = P * ((Z[y0:y1, x0:x1] - Zc) / (0.06 * Zc) + 0.5).clamp(0, 1)[None]
        roi = out[:, y0:y1, x0:x1]
        out[:, y0:y1, x0:x1] = P[:3] + roi * (1 - P[3:4])
    anh = out.permute(1, 2, 0) if tensor else out.permute(1, 2, 0).cpu().numpy()
    if tra_phu:
        return anh, lo, (~ngoai if tensor else (~ngoai).cpu().numpy())
    return anh, lo


def so_mau(quang_dich_px: float, tran: int = 16) -> int:
    """Số mẫu motion blur trong cửa trập theo quãng dịch lớn nhất (đứng yên = 1 mẫu)."""
    return 1 if quang_dich_px < 1 else int(min(tran, math.ceil(quang_dich_px / 4) + 1))


def dung_khung_mo(canh: Canh, cam_cua, t: float, cua_trap: float, k: int, **kw):
    """Motion blur: trung bình k mẫu trong cửa trập. `cam_cua(t)` -> (cam, phan_xa)."""
    if k <= 1:
        cam, px = cam_cua(t)
        return dung_khung(canh, cam, t, phan_xa=px, **kw)
    acc, lo = 0, 0.0
    for j in range(k):
        tj = t + cua_trap * j / (k - 1)
        cam, px = cam_cua(tj)
        img, l = dung_khung(canh, cam, tj, phan_xa=px, **kw)
        acc, lo = acc + img, max(lo, l)
    return acc / k, lo
