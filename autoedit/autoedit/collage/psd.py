"""Nhập PSD team đã chia layer — user chốt 08/10/2026: "cách tách cơ học lỗi chồng lỗi", có PSD thì dùng
THẲNG layer người cắt (đúng ý, phần bị che đã vẽ đủ, nền nằm sẵn ở layer dưới) — không máy cắt.

Mỗi layer / nhóm CẤP NGOÀI CÙNG = một khối. Khối chọn chuyển động thành lớp; nền = các layer đang hiện
KHÔNG được chọn, ghép lại. Đo thật trên PSD của team: Pillow đọc được tên layer nhưng KHÔNG lấy được điểm
ảnh từng layer ("cannot load"); psd-tools (MIT) ghép lại khớp Photoshop 54,8 dB, vẽ được hiệu ứng layer
(gói [composite]).
"""

from __future__ import annotations

import io

import numpy as np


def la_psd(b: bytes) -> bool:
    return bytes(b[:4]) == b"8BPS"


def _mo(nguon):
    from psd_tools import PSDImage

    if isinstance(nguon, (bytes, bytearray)):
        return PSDImage.open(io.BytesIO(nguon))
    return PSDImage.open(str(nguon))


def _kin(L, rong: int, cao: int) -> bool:
    """Layer phủ KÍN cả canvas (hiện, đủ khung, không chỗ trong suốt) — mọi thứ dưới nó bị che."""
    if not L.visible or tuple(L.bbox) != (0, 0, rong, cao):
        return False
    im = L.composite()
    return im is not None and (im.mode != "RGBA" or int(np.asarray(im.getchannel("A")).min()) >= 250)


def _la_chu(L) -> bool:
    """Layer chữ (type) hoặc nhóm mà mọi layer đang hiện bên trong đều là chữ."""
    if L.kind == "type":
        return True
    if L.is_group():
        la = [d for d in L.descendants() if not d.is_group() and d.is_visible()]
        return bool(la) and all(d.kind == "type" for d in la)
    return False


def doc(nguon) -> dict:
    """Cỡ canvas + các khối cấp ngoài cùng, thứ tự từ DƯỚI lên (chi_so = vị trí trong danh sách đó)."""
    p = _mo(nguon)
    rong, cao = int(p.width), int(p.height)
    lop = [{"chi_so": i, "ten": L.name, "loai": L.kind, "hien": bool(L.visible),
            "hop": [int(v) for v in L.bbox], "kin": _kin(L, rong, cao), "chu": _la_chu(L)}
           for i, L in enumerate(p)]
    return {"rong": rong, "cao": cao, "lop": lop}


def de_xuat(lop) -> list[int]:
    """Máy tick sẵn (người sửa): mọi khối đang hiện, có điểm ảnh, nằm TRÊN nền. Nền = layer phủ kín cao nhất
    (đo thật PSD PayPal: Background trắng + 'Layer 1' = cả ảnh phẳng) — không có thì khối dưới cùng."""
    hien = [x for x in lop if x["hien"] and x["hop"][2] > x["hop"][0] and x["hop"][3] > x["hop"][1]]
    if not hien:
        return []
    nen = max((x["chi_so"] for x in hien if x.get("kin")), default=hien[0]["chi_so"])
    return [x["chi_so"] for x in hien if x["chi_so"] > nen]


def vung_cat(rong: int, cao: int, W: int, H: int) -> tuple[int, int, int, int]:
    """Cắt GIỮA đúng tỉ lệ khung hình — cùng luật `mau.doc_anh_khung`."""
    if rong / cao > W / H:
        nw = round(cao * W / H)
        return (rong - nw) // 2, 0, (rong - nw) // 2 + nw, cao
    nh = round(rong * H / W)
    return 0, (cao - nh) // 2, rong, (cao - nh) // 2 + nh


def _mang(im, rong_max) -> np.ndarray:
    """PIL RGBA -> mảng 0..1; thu nhỏ trên alpha NHÂN SẴN (không viền tối quanh vật)."""
    from PIL import Image

    im = im.convert("RGBA")
    if rong_max and im.width > rong_max:
        im = im.convert("RGBa").resize((rong_max, round(im.height * rong_max / im.width)), Image.LANCZOS)
        im = im.convert("RGBA")
    return np.asarray(im, np.float32) / 255


def _loc_nen(p, khoi: set):
    """Bộ lọc ghép NỀN: layer đang hiện, không phải khối chọn, không nằm trong nhóm được chọn."""
    def la_nen(L):
        q = L
        while q is not None and q is not p:
            if id(q) in khoi:
                return False
            q = q.parent
        return L.is_visible()
    return la_nen


def tach(nguon, chon, W: int, H: int, rong_max: int | None = None):
    """-> (nền RGBA 0..1 trong khung đã cắt — alpha 0 ở chỗ nền trống, [(chi_so, rgb, alpha)] từ dưới lên).
    Mảng cỡ bằng khung đã cắt (như nhánh JPG), lớp tô đúng chỗ, giữ alpha mềm + hiệu ứng của PSD."""
    p = _mo(nguon)
    ds = list(p)
    chon = sorted({int(c) for c in chon})
    khoi = {id(ds[c]) for c in chon}
    vu = vung_cat(int(p.width), int(p.height), W, H)
    nen = _mang(p.composite(viewport=vu, force=True, layer_filter=_loc_nen(p, khoi)), rong_max)
    lop = []
    for c in chon:
        a = _mang(ds[c].composite(viewport=vu, force=True), rong_max)
        lop.append((c, a[..., :3], a[..., 3]))
    return nen, lop


def khoi_con_trong_nen(nguon, chon, rong_max: int = 512) -> list[int]:
    """Khối chọn mà NỀN vẫn còn bản sao (team chưa xoá khỏi layer nền) -> khối bay đi là lộ 2 bản (đo thật
    PSD PayPal 08/10: 2 ông Elon, 2 nhóm người). User chốt: team xoá trong Photoshop, tool chỉ CẢNH BÁO."""
    p = _mo(nguon)
    ds = list(p)
    la_nen = _loc_nen(p, {id(ds[c]) for c in chon})
    ra = []
    for c in sorted(set(chon)):
        x0, y0, x1, y1 = ds[c].bbox                                # chỉ ghép trong hộp của khối: nhanh
        vu = (max(0, x0), max(0, y0), min(int(p.width), x1), min(int(p.height), y1))
        if vu[2] <= vu[0] or vu[3] <= vu[1]:
            continue
        k = _mang(ds[c].composite(viewport=vu, force=True), rong_max)
        nen = _mang(p.composite(viewport=vu, force=True, layer_filter=la_nen), rong_max)
        mau_, a = k[..., :3], k[..., 3]
        o = a > 0.5
        if o.sum() < 0.002 * o.size or (nen[..., 3][o] > 0.5).mean() < 0.9:
            continue
        if float(np.abs(nen[..., :3][o] - mau_[o]).mean()) < 0.08:
            ra.append(c)
    return ra


def anh_xem(nguon, rong_max: int = 1600):
    """Ảnh ghép cả canvas (PIL RGB) cho trang web — trình duyệt không xem được PSD."""
    im = _mo(nguon).composite().convert("RGB")
    if im.width > rong_max:
        im = im.resize((rong_max, round(im.height * rong_max / im.width)))
    return im


def anh_nho(nguon, canh: int = 160) -> list:
    """Ảnh nhỏ (PIL RGBA) từng khối cấp ngoài cùng, None với khối ẩn / rỗng — cho danh sách tick."""
    ra = []
    for L in _mo(nguon):
        im = L.composite() if L.visible and L.bbox[2] > L.bbox[0] and L.bbox[3] > L.bbox[1] else None
        if im is not None:
            im = im.convert("RGBA")
            im.thumbnail((canh, canh))
        ra.append(im)
    return ra
