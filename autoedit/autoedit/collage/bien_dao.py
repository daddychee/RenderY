"""MÁY TỰ BIÊN ĐẠO nhịp + camera — user chốt 07/10/2026: bỏ ô camera, "máy tự lên nhịp và camera".

Đầu vào chỉ là hình học các lớp (vị trí, cỡ, độ sâu, chạm mép ảnh). Luật lấy từ bản thử user duyệt
("Những thành phố mơ màng", 3 style) + lỗi đã đo ở đó:
- vai trò theo vị trí: chạm đáy -> trồi lên; đứng trên lớp khác -> trồi từ SAU lớp đó; ở cao -> rơi
  xuống; chạm mép trái/phải -> trượt vào; vật nhỏ lơ lửng -> trôi; còn lại -> bật lên.
- thứ tự: đế trước, vật đứng trên sau, chữ cuối (bản thử: đá -> thành phố -> cây -> tiêu đề).
- lớp chưa tới lượt NẤP HẲN ngoài khung (nóc thành phố từng ló lên trước tảng đá).
- camera GIẢI RÀNG BUỘC bằng số (tính tay lệch 45 px): vật chính trong khung, không cắt đầu; vật bị mép
  ảnh cắt cụt không lộ đường cắt; vật đứng riêng hoặc trọn trong khung hoặc ra hẳn; nền không lộ mép.
- nhịp: cú camera ~1,7 s một lần sau khi các lớp vào xong — không có khoảng chết dài.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from autoedit.collage.nhip import VOT_DAU, lo_xo, nhieu_muot

STYLE = ("collage", "black_grid", "non_grid")
ZOOM_NEN, Z_NEN = 1.15, 40.0
DAI_CU = 0.85                     # cú camera Vox: vọt đỉnh 0,11 s, tắt trong 0,85 s (đo demo Vox)
NGHI = (0.0, 0.0, 0.0, 1.0, 0.0)


@dataclass
class Vat:
    X: float                      # tâm lúc nghỉ, px xuất, gốc giữa khung
    Y: float
    nw: float                     # nửa rộng / nửa cao, px xuất
    nh: float
    Z0: float
    cham: dict                    # chạm mép ẢNH: trai/phai/tren/duoi
    lo_lung: bool = False


@dataclass
class KeHoach:
    anims: list
    cam: object
    gio_vao: list
    nhip: list
    giu: list                     # [(a, b)] đoạn camera đứng giữ


def hop_man(v: Vat, cam, an, W: int, H: int):
    """Hộp bao lớp trên màn hình (x0, y0, x1, y1), gốc góc trái trên — cùng công thức chiếu dung.py."""
    tx, ty, tz, F, px, py = cam
    ox, oy, r, s, dz = (float(x) for x in an)
    d = v.Z0 + dz - tz
    if d < 0.3:
        return (-1e6, -1e6, -1e6 + 1, -1e6 + 1)
    k = F * v.Z0 / d
    cx = F * ((v.X + ox) * v.Z0 - tx) / d + px + W / 2
    cy = F * ((v.Y + oy) * v.Z0 - ty) / d + py + H / 2
    a = math.radians(r)
    hw, hh = v.nw * k * s, v.nh * k * s
    ew, eh = abs(hw * math.cos(a)) + abs(hh * math.sin(a)), abs(hw * math.sin(a)) + abs(hh * math.cos(a))
    return (cx - ew, cy - eh, cx + ew, cy + eh)


def nen_phu_khung(cam, W: int, H: int, zoom: float = ZOOM_NEN, Z: float = Z_NEN) -> bool:
    tx, ty, tz, F, px, py = cam
    d = Z - tz
    x0 = F * (-W * zoom / 2 * Z - tx) / d + px
    x1 = F * (W * zoom / 2 * Z - tx) / d + px
    y0 = F * (-H * zoom / 2 * Z - ty) / d + py
    y1 = F * (H * zoom / 2 * Z - ty) / d + py
    return x0 <= -W / 2 and x1 >= W / 2 and y0 <= -H / 2 and y1 >= H / 2


# ------------------------------------------------------------------ vai trò + thứ tự
def vai_tro(vs: list[Vat], W: int, H: int) -> list[tuple]:
    ra = []
    for i, v in enumerate(vs):
        if v.lo_lung:
            ra.append(("troi", None)); continue
        if v.cham["duoi"]:
            ra.append(("de", None)); continue
        if v.Y < -0.12 * H:
            ra.append(("roi", None)); continue
        day, tot = v.Y + v.nh, None
        for j, u in enumerate(vs):
            if j == i or u.lo_lung or u.Y <= v.Y:
                continue
            tren_u, duoi_u = u.Y - u.nh, u.Y + u.nh
            chong = min(v.X + v.nw, u.X + u.nw) - max(v.X - v.nw, u.X - u.nw)
            if tren_u - 0.05 * H <= day <= duoi_u and chong >= 0.6 * v.nw:
                if tot is None or abs(day - tren_u) < abs(day - (vs[tot].Y - vs[tot].nh)):
                    tot = j
        if tot is not None:
            ra.append(("tren", tot)); continue
        if v.cham["trai"] and not v.cham["phai"]:
            ra.append(("trai", None)); continue
        if v.cham["phai"] and not v.cham["trai"]:
            ra.append(("phai", None)); continue
        if v.cham["tren"]:
            ra.append(("roi", None)); continue
        ra.append(("bat", None))
    return ra


def _muc(vai, i, sau=0):
    r, s = vai[i]
    if r == "de":
        return 0
    if r == "tren" and sau < 8:
        return _muc(vai, s, sau + 1) + 1
    return 9 if r == "roi" else 1


def _lui(vs, vai, i, sau=0) -> float:
    """Lúc trồi lớp lùi SÂU thêm để đi SAU mọi lớp đỡ nó (thành phố trồi từ sau tảng đá)."""
    r, s = vai[i]
    if r != "tren" or sau > 8:
        return 0.0
    can = max(vs[s].Z0 + _lui(vs, vai, s, sau + 1) - vs[i].Z0 + 0.3, 0.6)
    return float(can)


def do_sau_theo_vai(vs: list[Vat], vai) -> list[float]:
    """Z lúc nghỉ theo VAI TRÒ (hình học), không theo model độ sâu — đo thật 07/10: model xếp chữ tiêu đề
    SAU thành phố, tảng đá TRƯỚC nhất trên ảnh đồ hoạ. Luật bản thử user duyệt: đế xa nhất (7,5), mỗi
    tầng đứng trên gần hơn 0,5; chữ ở cao gần nhất (4,5); vật lơ lửng xa 12..24 (trôi chậm)."""
    ra, troi = [], [i for i, (r, _) in enumerate(vai) if r == "troi"]
    for i, (r, _) in enumerate(vai):
        if r == "troi":
            k = troi.index(i)
            ra.append(12.0 + 12.0 * k / max(len(troi) - 1, 1))
        elif r == "roi":
            ra.append(4.5)
        else:
            ra.append(7.5 - 0.5 * min(_muc(vai, i), 3))
    return ra


# ------------------------------------------------------------------ chuyển động lớp
def _anim_vao(v: Vat, vai, t0: float, style: str, W: int, H: int, lui: float, seed: int):
    r, _ = vai
    if style != "collage":                                   # Black Grid / Non-Grid: "đóng dấu"
        lx, goc = lo_xo(0.5, 0.2), (-6 if seed % 2 else 5)

        def dong_dau(t):
            if t < t0:
                return (0.0, 3.0 * H, 0.0, 0.02, 0.0)
            u = lx(t - t0)
            return (0.0, 80 * (1 - u), goc * (1 - u), 0.6 + 0.4 * u, 0.0)
        return dong_dau
    m = 0.04 * H
    k = (v.Z0 + lui) / v.Z0
    ox0 = oy0 = 0.0
    if r in ("de", "tren"):
        oy0 = (H / 2 + m) * k - (v.Y - v.nh)                 # nóc xuống dưới mép khung
    elif r == "roi":
        oy0 = -(H / 2 + m) * k - (v.Y + v.nh)
    elif r == "trai":
        ox0 = -(W / 2 + m) * k - (v.X + v.nw)
    elif r == "phai":
        ox0 = (W / 2 + m) * k - (v.X - v.nw)
    if r == "bat":
        lx = lo_xo(0.55, 0.28)

        def bat(t):
            u = lx(t - t0)
            return (0.0, 0.06 * H * (1 - u), 0.0, max(0.02, u), 0.0)
        return bat
    lx = lo_xo(0.8, 0.5) if r == "de" else lo_xo(0.62, 0.33)

    def vao(t):
        u = lx(t - t0)
        return (ox0 * (1 - u), oy0 * (1 - u), 0.0, 1.0, lui * (1 - min(u, 1.0)))
    return vao


def _anim_troi(seed: int, bien: float = 18):
    def troi(t):
        return (bien * nhieu_muot(seed, 0.15, t), 0.6 * bien * nhieu_muot(seed + 7, 0.12, t),
                4 * nhieu_muot(seed + 3, 0.1, t), 1.0, 0.0)
    return troi


# ------------------------------------------------------------------ camera
def _hop_le(vs, T, cam, W, H, le=0.03) -> bool:
    if not nen_phu_khung(cam, W, H):
        return False
    x0, y0, x1, y1 = hop_man(vs[T], cam, NGHI, W, H)
    if y0 < le * H:                                           # không cắt đầu vật chính
        return False
    w_, h_ = x1 - x0, y1 - y0
    thay = max(0.0, min(x1, W) - max(x0, 0)) * max(0.0, min(y1, H) - max(y0, 0)) / max(w_ * h_, 1e-6)
    if w_ <= (1 - 2 * le) * W and h_ <= (1 - 2 * le) * H:
        if x0 < le * W or x1 > W - le * W or y1 > H - le * H:  # vừa khung thì phải nằm trọn
            return False
    elif thay < 0.6:
        return False
    for i, v in enumerate(vs):
        if i == T or v.lo_lung:
            continue
        b = hop_man(v, cam, NGHI, W, H)
        if v.cham["duoi"] and b[3] < H + 6 or v.cham["tren"] and b[1] > -6:
            return False                                      # lộ đường cắt của vật bị mép ảnh cắt cụt
        if v.cham["trai"] and b[0] > -6 or v.cham["phai"] and b[2] < W + 6:
            return False
        if not any(v.cham.values()):
            trong = b[0] >= 0.02 * W and b[1] >= 0.02 * H and b[2] <= 0.98 * W and b[3] <= 0.98 * H
            ngoai = b[2] <= 0 or b[0] >= W or b[3] <= 0 or b[1] >= H
            if not (trong or ngoai):
                return False                                  # cắt ngang vật đứng riêng (chữ)
    return True


def giai_camera(vs: list[Vat], T: int, W: int, H: int, lap_day: float = 0.72, zoom_max: float = 1.6):
    """Dò lưới (zoom, tâm ngắm) -> camera thoả MỌI ràng buộc, gần độ lấp mong muốn nhất. None nếu không có."""
    v = vs[T]
    nghi = max(2 * v.nh / H, 2 * v.nw / W)
    muon = max(lap_day, min(nghi * 1.25, 1.3))
    tot = None
    for tz in np.arange(0.0, v.Z0 * (1 - 1 / zoom_max) + 1e-9, 0.05):
        d = v.Z0 - tz
        k = v.Z0 / d
        lap = nghi * k
        if lap < nghi * 1.15 - 1e-9 and muon > nghi:          # phải thật sự vào gần
            continue
        for cy in np.linspace(-0.3 * H, 0.3 * H, 25):
            ty = v.Y * v.Z0 - cy * d
            for cx in np.linspace(-0.2 * W, 0.2 * W, 9):
                cam = (v.X * v.Z0 - cx * d, ty, float(tz), 1.0, 0.0, 0.0)
                if not _hop_le(vs, T, cam, W, H):
                    continue
                diem = abs(lap - muon) + 0.3 * (abs(cx) / W + abs(cy) / H)
                if tot is None or diem < tot[0]:
                    tot = (diem, cam)
    return None if tot is None else tot[1]


def _muc_tieu(vs, vai) -> list[int]:
    """Vật chính = lớp lớn nhất KHÔNG chạm mép ảnh; vật phụ = lớp cao nhất khác nó (chữ tiêu đề)."""
    ung = [i for i, v in enumerate(vs) if not v.lo_lung and not any(v.cham.values())]
    if not ung:
        return []
    A = max(ung, key=lambda i: vs[i].nw * vs[i].nh)
    con = [i for i in ung if i != A and vs[i].nw * vs[i].nh >= 0.03 * vs[A].nw * vs[A].nh]
    B = min(con, key=lambda i: vs[i].Y - vs[i].nh) if con else None
    return [A] + ([B] if B is not None else [])


def lap(vs: list[Vat], giay: float, style: str, W: int, H: int) -> KeHoach:
    if style not in STYLE:
        raise ValueError(f"Style lạ: {style}")
    vai = vai_tro(vs, W, H)
    vox = style != "collage"
    # ---- giờ vào
    vao = [i for i, (r, _) in enumerate(vai) if r != "troi"]
    vao.sort(key=lambda i: (_muc(vai, i), -vs[i].Y))
    # vật NHỎ (hộp bao < 3% khung) không chiếm lượt riêng: vào chen 0,3 s sau vật lớn liền trước. Đo thật
    # 07/10: cột tháp (0,8%) + sao băng đuôi dài (2%) chiếm lượt -> tiêu đề vào 3,4 s (bản duyệt 2,05 s),
    # camera đẩy nó đi ngay. Cây thông (4%) vẫn là vật lớn.
    lon = [i for i in vao if 4 * vs[i].nw * vs[i].nh >= 0.03 * W * H]
    t_dau = 0.1 if vox else 0.25
    n = len(lon)
    gap = 0.6 if n <= 1 else min(0.65, max(0.25, (0.42 * giay - t_dau) / (n - 1)))
    if n > 1 and t_dau + gap * (n - 1) > 0.5 * giay:
        gap = max(0.1, (0.5 * giay - t_dau) / (n - 1))
    gio = [0.0] * len(vs)
    t_truoc = t_dau
    k = 0
    for i in vao:
        if i in lon:
            t_truoc = gio[i] = t_dau + k * gap
            k += 1
        else:
            gio[i] = t_truoc + 0.3
    xong = max((gio[i] for i in vao), default=0.0)
    troi_ds = [i for i, (r, _) in enumerate(vai) if r == "troi"]
    for k, i in enumerate(troi_ds):
        gio[i] = (xong + 0.15 + 0.12 * k) if vox else 0.0
    anims = []
    for i, v in enumerate(vs):
        if vai[i][0] == "troi":
            tr = _anim_troi(20 + i)
            if vox:
                dd = _anim_vao(v, vai[i], gio[i], style, W, H, 0.0, i)
                anims.append(lambda t, dd=dd, tr=tr: tuple(np.add(dd(t), tr(t)) - np.array(NGHI)))
            else:
                anims.append(tr)
        else:
            anims.append(_anim_vao(v, vai[i], gio[i], style, W, H, _lui(vs, vai, i), i))
    # ---- camera: khoá (giờ, cam) nối bằng VOT_DAU
    muc = _muc_tieu(vs, vai)
    khoa_cam = {}
    for T in muc:
        c = giai_camera(vs, T, W, H, lap_day=0.78 if vox else 0.72)
        if c is not None:
            khoa_cam[T] = c
    dich = [T for T in muc if T in khoa_cam]
    rong = (0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    chuoi = (dich + ["rong"]) if dich else []
    # cú camera đầu: chỉ sau khi đã GIỮ TOÀN CẢNH >= 1,2 s (người xem kịp thấy cả bố cục); các cú rải
    # đều tới gần cuối, cách nhau 1,45..2,2 s -> không có đoạn chết
    t0_cam = (max(gio) + 1.2) if vao else 0.4                 # tính cả vật lơ lửng 'đóng dấu' sau (Vox)
    t_cuoi = giay - DAI_CU - 0.45
    khoa = []
    if chuoi and t0_cam <= t_cuoi:
        so = 1 + int((t_cuoi - t0_cam) // 1.45)
        buoc = (t_cuoi - t0_cam) / (so - 1) if so > 1 else 0.0
        for k in range(so):
            ten = chuoi[k % len(chuoi)]
            khoa.append((t0_cam + k * buoc, khoa_cam[ten] if ten != "rong" else rong))
    giu = []
    for j, (tk, _) in enumerate(khoa):
        b = khoa[j + 1][0] if j + 1 < len(khoa) else giay
        if tk + DAI_CU < b:
            giu.append((tk + DAI_CU, b))
    troi_x = 0.0 if vox else 260.0

    def cam(t):
        p, u0 = rong, 0.0
        for j, (tk, c) in enumerate(khoa):
            if t >= tk:
                u = VOT_DAU(min((t - tk) / DAI_CU, 1.0))
                p = tuple(a + (b - a) * u for a, b in zip(p, c))
                u0 = u if j == 0 else 1.0
        tx, ty, tz, F, px, py = p
        tz += 0.12 * t / giay                                  # đẩy rất chậm suốt clip
        tx += troi_x * (1 - 2 * t / giay) * (1 - u0)           # trôi ngang (parallax) tới cú camera đầu
        if vox:                                                # rung tay máy 1 Hz (wiggle Vox)
            tx += 40 * nhieu_muot(1, 1.0, t)
            ty += 40 * nhieu_muot(2, 1.0, t)
        return (tx, ty, tz, F, px, py)

    nhip = sorted([gio[i] for i in vao] + [tk for tk, _ in khoa])
    return KeHoach(anims=anims, cam=cam, gio_vao=gio, nhip=nhip, giu=giu)
