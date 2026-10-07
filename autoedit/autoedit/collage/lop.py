"""LỚP theo KHUNG người kéo — user chốt 07/10/2026: "máy đề xuất khung, người sửa".

Đo thật 07/10 (ảnh "Những thành phố mơ màng"): bấm điểm cho SAM vớ bậy trên ảnh đồ hoạ nhiều mảnh
(thành phố ăn cả dải hồng tiêu đề + sao trời); KHUNG (box prompt) ra đủ chữ/nhà/cây, SAM tự chấm
0,89–0,98. Lớp bị lớp trước che thì VẼ BÙ phần bị che trong đường bao của chính nó — không bù thì
cụm nhà thủng lỗ hình cây thông lúc cây chưa vào, đỉnh đá khấc hình chân nhà.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

NHO = 0.015                       # lớp < 1,5% khung, không chạm mép = vật lơ lửng (sao, hành tinh)


def khung_px(k, w: int, h: int) -> tuple[int, int, int, int]:
    """Khung tỉ lệ 0..1 (x0, y0, x1, y1) -> pixel, kẹp trong ảnh."""
    x0, y0, x1, y1 = (float(v) for v in k)
    return (int(round(min(max(x0, 0), 1) * w)), int(round(min(max(y0, 0), 1) * h)),
            int(round(min(max(x1, 0), 1) * w)), int(round(min(max(y1, 0), 1) * h)))


def cat_theo_khung(rgb, khung_px_ds, sam) -> list[np.ndarray]:
    """Mỗi khung -> mask SAM (box prompt), KHÔNG tràn ra ngoài khung đã kéo, lấp lỗ."""
    ra = []
    for x0, y0, x1, y1 in khung_px_ds:
        m = np.asarray(sam.tach_khung(rgb, (x0, y0, x1, y1)), bool)
        hop = np.zeros_like(m)
        hop[y0:y1, x0:x1] = True
        ra.append(ndi.binary_fill_holes(m & hop))
    return ra


def cham_mep(m: np.ndarray, le: int = 2) -> dict:
    return {"trai": bool(m[:, :le].any()), "phai": bool(m[:, -le:].any()),
            "tren": bool(m[:le].any()), "duoi": bool(m[-le:].any())}


def la_lo_lung(m: np.ndarray, ds=()) -> bool:
    """Vật lơ lửng (sao, hành tinh) = NHỎ và ĐỨNG TÁCH RIÊNG: không chạm mép ảnh, không dính lớp nào khác
    trong bán kính 3% cạnh ngắn. Đo thật 07/10: cây thông 1,42% khung nằm giữa cụm nhà bị coi là lơ lửng
    -> trôi như hành tinh thay vì trồi lên cùng thành phố."""
    if float(m.mean()) >= NHO or any(cham_mep(m).values()):
        return False
    r = max(1, int(round(0.03 * min(m.shape))))
    gan = ndi.binary_dilation(m, iterations=r)
    return not any((gan & n).any() for n in ds if n is not m)


def chia_vung(masks, zs) -> list[np.ndarray]:
    """Pixel thuộc nhiều lớp -> thuộc lớp GẦN hơn (Z nhỏ)."""
    ra = [np.asarray(m, bool).copy() for m in masks]
    thu_tu = sorted(range(len(ra)), key=lambda i: zs[i])
    da = np.zeros_like(ra[0]) if ra else None
    for i in thu_tu:
        ra[i] &= ~da
        da |= ra[i]
    return ra


def _bao(m: np.ndarray) -> np.ndarray:
    """Đường bao lớp: đóng hình thái học bán kính ~9% cạnh ngắn (lấp khấc/lỗ do lớp trước che,
    KHÔNG lan ra khoảng trời bên ngoài). Làm ở độ phân giải thấp cho nhanh."""
    h, w = m.shape
    f = max(1, min(h, w) // 270)
    nho = m[::f, ::f]
    r = max(1, int(round(0.09 * min(h, w) / f)))
    b = ndi.binary_closing(np.pad(nho, r + 1), iterations=r)[r + 1:-(r + 1), r + 1:-(r + 1)]
    if f > 1:
        b = np.repeat(np.repeat(b, f, 0), f, 1)[:h, :w]
    return b


def ve_bu(rgb, masks, zs, va_nen) -> list[tuple[np.ndarray, np.ndarray]]:
    """(màu, mask) từng lớp sau khi BÙ phần bị lớp gần hơn che, trong đường bao của chính nó."""
    rgb = np.asarray(rgb, np.float32)
    ra = []
    for i, m in enumerate(masks):
        truoc = np.zeros_like(m)
        for j, n in enumerate(masks):
            if j != i and zs[j] < zs[i]:
                truoc |= n
        vung = _bao(m) & ~m & truoc
        if not vung.any():
            ra.append((rgb, m))
            continue
        bu = va_nen(rgb, ndi.binary_dilation(vung, iterations=4))
        mau = rgb.copy()
        mau[vung] = np.asarray(bu, np.float32)[vung]
        ra.append((mau, m | vung))
    return ra


def _mau_vung_sach(rgb, sach: np.ndarray) -> np.ndarray:
    """Màu nền mượt ước từ CHỈ vùng sạch (làm mượt có chuẩn hoá, bán kính tăng dần cho chỗ xa vùng sạch)."""
    h, w = sach.shape
    tron = np.stack([ndi.median_filter(rgb[..., c], 5) for c in range(3)], -1)
    s_ = sach.astype(np.float32)
    ra = np.zeros_like(tron)
    da = np.zeros((h, w), bool)
    for k in (0.06, 0.15, 0.4, 1.0):
        sg = max(2.0, k * min(h, w))
        wgt = ndi.gaussian_filter(s_, sg, mode="nearest")
        m = np.stack([ndi.gaussian_filter(tron[..., c] * s_, sg, mode="nearest") for c in range(3)], -1)
        m /= (wgt[..., None] + 1e-9)
        dung = (wgt > 0.05) & ~da
        ra[dung] = m[dung]
        da |= dung
    ra[~da] = m[~da]
    return ra


def nen_sach(rgb, masks, va_nen) -> np.ndarray:
    """Nền sau khi nhấc mọi lớp ra. LaMa vẽ CHI TIẾT, còn MÀU NỀN (tần số thấp) lấy từ vùng sạch xung
    quanh. Đo thật 07/10: LaMa vá lỗ to giữa trời ra mảng xám sáng hơn trời thật (ảnh thành phố, quả
    cam) — lộ rõ lúc lớp chưa bay vào."""
    rgb = np.asarray(rgb, np.float32)
    hop = np.zeros(rgb.shape[:2], bool)
    for m in masks:
        hop |= m
    if not hop.any():
        return rgb
    # nới 2% cạnh ngắn (>= 10 px): đo thật 07/10 vỏ cam ngoài cùng nằm ngoài mask SAM -> vòng viền nhạt
    lo = ndi.binary_dilation(hop, iterations=max(10, round(0.02 * min(hop.shape))))
    lama = np.asarray(va_nen(rgb, lo), np.float32)
    sg = max(2.0, 0.04 * min(lo.shape))
    thap = np.stack([ndi.gaussian_filter(lama[..., c], sg) for c in range(3)], -1)
    ghep = np.clip(lama - thap + _mau_vung_sach(rgb, ~ndi.binary_dilation(lo, iterations=4)), 0, 1)
    mem = ndi.gaussian_filter(lo.astype(np.float32), 2)[..., None]
    return rgb * (1 - mem) + ghep * mem


def de_xuat_khung(rgb, z, sam, toi_da: int = 4, le: float = 0.015) -> list[list[float]]:
    """Máy ĐỀ XUẤT khung (người sửa): gợi ý theo độ nhô/độ gần -> SAM -> luật lọc của tach.py ->
    hộp bao, tỉ lệ 0..1, nới `le`. Trùng nhau (>50% phần nhỏ) thì bỏ."""
    from autoedit.collage import tach

    v = tach.do_chenh(z)
    h, w = v.shape
    vat = []
    for pts in tach.diem_goi_y(v, toi_da=toi_da):
        ung = [(tach.buoc_mep(m, v), m) for m, sc in ((tach.lam_sach(m), sc) for m, sc in sam.tach(rgb, pts))
               if tach.hop_le(m, sc, v)]
        if not ung:
            continue
        m = max(ung, key=lambda x: x[0])[1]
        if any((m & a).sum() > 0.5 * min(m.sum(), a.sum()) for a in vat):
            continue
        vat.append(m)
        if len(vat) >= toi_da:
            break
    ra = []
    for m in vat:
        ys, xs = np.nonzero(m)
        ra.append([round(max(0.0, xs.min() / w - le), 4), round(max(0.0, ys.min() / h - le), 4),
                   round(min(1.0, (xs.max() + 1) / w + le), 4), round(min(1.0, (ys.max() + 1) / h + le), 4)])
    return ra
