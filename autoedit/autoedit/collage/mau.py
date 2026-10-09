"""Mẫu "VOX · Chiều sâu": ảnh đã duyệt + giây + mã camera của cảnh -> mp4.

Cả Master Frame thành nền có độ sâu TỪNG PIXEL (Depth Anything V2 SMALL — Apache 2.0;
Base/Large là CC-BY-NC, cấm dùng thương mại). Camera theo bảng mã `cd` của treatment.
Dịch thân máy (truck/track/arc/tilt) mới ra parallax; pan = xoay đều cả khung.

Biên độ camera TỰ CO cho tới khi kiểm lộ mép = 0 (luật bắt buộc của skill) — ảnh nào,
độ sâu nào cũng không lộ mép, ngoài cú lia vút (whip) có phản chiếu mép + motion blur che.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np

from autoedit.collage.dung import Canh, dung_khung, dung_khung_mo, so_mau
from autoedit.collage.nhip import muot

ZOOM = 1.15                       # phóng 15%: mỗi bên dư 7,5% khung cho camera đi
ZN, ZF = 4.0, 40.0                # độ sâu gần nhất (đất) .. xa nhất (trời)
MA_CAMERA = {"static", "push_in", "pull_out", "tilt_up", "tilt_down", "track", "truck_left",
             "truck_right", "pan_left", "pan_right", "whip_pan", "crash_zoom", "arc", "orbit"}
MIEN_LIA = {"whip_pan": (0.7, 1.0)}   # phần clip (tỉ lệ) được phép lộ mép: lia vút cuối clip


def _mot_ma(cd: str, u: float, s: float, mx: float, my: float, zg: float):
    """Camera ở tiến độ u (0..1, đã easing) với biên độ s (0..1) -> (tx, ty, Tz, F, px, py).
    mx, my: phần dư mép (px); zg: độ sâu gần nhất. Dịch tx tại độ sâu Z làm ảnh trượt tx/Z px."""
    tx = ty = tz = px = py = 0.0
    a = 0.85 * s
    if cd == "push_in":
        tz = 0.18 * zg * u * s
    elif cd == "pull_out":
        tz = 0.18 * zg * (1 - u) * s
    elif cd == "truck_left":
        tx = -a * mx * zg * u
    elif cd == "truck_right":
        tx = a * mx * zg * u
    elif cd == "track":
        tx, tz = a * mx * zg * u, 0.08 * zg * u * s
    elif cd in ("arc", "orbit"):
        tx = a * mx * zg * (2 * u - 1)
        tz = (0.10 if cd == "arc" else 0.16) * zg * math.sin(math.pi * u) * s
    elif cd == "pan_left":
        px = a * mx * u
    elif cd == "pan_right":
        px = -a * mx * u
    elif cd in ("tilt_up", "tilt_down"):
        dau = 1 if cd == "tilt_up" else -1                    # tilt up: cảnh trôi XUỐNG
        py = dau * 0.6 * s * my * u
        ty = -dau * 0.25 * s * my * zg * u                    # kèm cẩu nhẹ để có lệch tầng
    elif cd == "crash_zoom":
        tz = zg * (0.06 * min(u / 0.5, 1) + 0.29 * max(0.0, (u - 0.5) / 0.5) ** 3) * s
    elif cd == "whip_pan":
        tz = 0.05 * zg * min(u / 0.7, 1) * s
        px = -max(0.0, (u - 0.7) / 0.3) ** 2.5 * 1.1 * (mx * 2 / 0.15)   # vút qua hết khung
    else:                                                      # static / mã lạ: thở nhẹ
        tz = 0.06 * zg * u * s
    return tx, ty, tz, 1.0, px, py


def lo_mep_toi_da(canh: Canh, cam, giay: float, mien=None, so_mau_kiem: int = 13) -> float:
    """Lộ mép lớn nhất trên `so_mau_kiem` thời điểm, bỏ qua miền lia vút được phép."""
    lo = 0.0
    for i in range(so_mau_kiem):
        t = giay * i / (so_mau_kiem - 1)
        if mien and mien[0] * giay < t <= mien[1] * giay:
            continue
        lo = max(lo, dung_khung(canh, cam(t), t)[1])
    return lo


def ke_hoach(cd: str, giay: float, canh: Canh):
    """-> cam(t). Biên độ bắt đầu 100%, co 20% mỗi lượt tới khi không lộ mép."""
    mx = (canh.PW * canh.S0 - canh.W) / 2
    my = (canh.PH * canh.S0 - canh.H) / 2
    zg = float(canh.z.min())
    cd = cd if cd in MA_CAMERA else "static"
    s = 1.0
    for _ in range(12):
        def cam(t, s=s):
            return _mot_ma(cd, muot(t / giay) if giay > 0 else 0.0, s, mx, my, zg)
        if lo_mep_toi_da(canh, cam, giay, MIEN_LIA.get(cd)) == 0.0:
            return cam
        s *= 0.8
    return lambda t: (0.0, 0.0, 0.0, 1.0, 0.0, 0.0)


_MODEL_DO_SAU = None


def uoc_do_sau(rgb: np.ndarray) -> np.ndarray:
    """Depth Anything V2 Small -> độ sâu Z (gần ZN .. xa ZF). Nạp model 1 lần mỗi tiến trình."""
    global _MODEL_DO_SAU
    import torch
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    from transformers import pipeline

    if _MODEL_DO_SAU is None:
        _MODEL_DO_SAU = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf",
                                 device=0 if torch.cuda.is_available() else -1)
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    d = _MODEL_DO_SAU(im)["predicted_depth"].squeeze().cpu().numpy()       # độ chênh: lớn = gần
    d = np.asarray(Image.fromarray(d.astype(np.float32)).resize(im.size, Image.BICUBIC), np.float32)
    d = gaussian_filter(d, 2, truncate=3.0)
    v = np.clip((d - np.percentile(d, 1)) / (np.percentile(d, 99) - np.percentile(d, 1) + 1e-6), 0, 1)
    return (1 / (v * (1 / ZN - 1 / ZF) + 1 / ZF)).astype(np.float32)


def _dich_chuyen(cam, t: float, dt: float, canh: Canh) -> float:
    """Quãng dịch lớn nhất (px) của các điểm dò giữa t và t+dt -> số mẫu motion blur."""
    a, b = cam(t), cam(t + dt)
    d = 0.0
    for Z in (float(canh.z.min()), float(canh.z.max())):
        for X, Y in ((-canh.W / 2, -canh.H / 2), (canh.W / 2, canh.H / 2), (0, 0)):
            pa = [c[3] * (P * Z - c[k]) / (Z - c[2]) + c[4 + k] for c in (a, b) for k, P in ((0, X), (1, Y))]
            d = max(d, math.hypot(pa[2] - pa[0], pa[3] - pa[1]))
    return d


def bam_anh(anh: Path) -> str:
    """Dấu băm nội dung ảnh — vẽ lại ảnh cảnh thì bản tách cũ tự bỏ."""
    import hashlib

    return hashlib.sha1(Path(anh).read_bytes()).hexdigest()[:20]


def _doc_anh(anh: Path) -> np.ndarray:
    from PIL import Image

    return np.asarray(Image.open(anh).convert("RGB"), np.float32) / 255


def dung_video(anh: Path, giay: float, cd: str, ra: Path, W: int = 1920, H: int = 1080, fps: int = 30,
               uoc_do_sau=None, thiet_bi: str | None = None, ffmpeg: str = "ffmpeg") -> Path:
    """Mẫu "VOX · Chiều sâu": cả ảnh là một nền có độ sâu từng pixel."""
    rgb = _doc_anh(anh)
    canh = Canh(rgb, (uoc_do_sau or globals()["uoc_do_sau"])(rgb), W, H, zoom=ZOOM)
    return _dung_canh(canh, giay, cd, ra, fps, thiet_bi, ffmpeg)


def dung_popup(anh: Path, giay: float, cd: str, ra: Path, nhan: str, kho_tach, diem=None,
               W: int = 1920, H: int = 1080, fps: int = 30, uoc_do_sau=None, tach_lop=None,
               tach_theo_diem=None, thiet_bi: str | None = None, ffmpeg: str = "ffmpeg") -> Path:
    """Mẫu "VOX · Pop-up 2.5D": vật tách khỏi nền bật lên lệch nhịp, camera theo mã `cd`.

    Bản tách lưu THEO CẢNH: có sẵn (cùng ảnh) thì dùng lại; có điểm bấm tay thì tách lại theo
    điểm và ghi đè. Không tách được vật nào -> lùi về Chiều sâu, cờ đã nằm trong kho tách.
    """
    canh = _canh_popup(_doc_anh(anh), bam_anh(anh), nhan, kho_tach, diem, diem, W, H,
                       uoc_do_sau, tach_lop, tach_theo_diem)
    return _dung_canh(canh, giay, cd, ra, fps, thiet_bi, ffmpeg)


def _canh_popup(rgb, bam: str, nhan: str, kho_tach, diem, diem_luu, W: int, H: int,
                uoc_do_sau=None, tach_lop=None, tach_theo_diem=None) -> Canh:
    """Nền + vật bật lên. `diem` theo pixel của `rgb`; `diem_luu` là bản ghi vào kho."""
    from autoedit.collage import tach

    uoc = uoc_do_sau or globals()["uoc_do_sau"]
    if diem:
        kq = (tach_theo_diem or tach.tach_theo_diem)(rgb, uoc(rgb), diem, uoc_do_sau=uoc)
        kho_tach.ghi(nhan, bam, kq, rgb, diem=diem_luu)
    else:
        kq = kho_tach.doc(nhan, bam)
        if kq is None:
            kq = (tach_lop or tach.tach_lop)(rgb, uoc(rgb), uoc_do_sau=uoc)
            kho_tach.ghi(nhan, bam, kq, rgb)
    canh = Canh(kq.nen, kq.z_nen, W, H, zoom=ZOOM)
    if kq.vat:
        from scipy.ndimage import gaussian_filter

        from autoedit.collage.dung import Lop
        from autoedit.collage.nhip import lo_xo

        bat = lo_xo(0.7, 0.35)
        for i, (m, z_vat) in enumerate(kq.vat):
            a = np.dstack([rgb, gaussian_filter(np.asarray(m, np.float32), 1.0)])
            t0 = 0.1 + 0.15 * i                                   # lệch nhịp như mẫu Rockefeller
            # NẢY ngắn (12% khung, phóng 92%->100%), không trồi cả quãng: đo thật 06/10 trồi
            # 0,75 khung làm lộ hết vùng LaMa vá sau lưng vật (mảng xám, bóng ma tháp tàu) —
            # lớp tách tự động không sạch như lớp vẽ riêng của mẫu Rockefeller.
            canh.them(Lop(a, Z0=z_vat, anim=lambda t, t0=t0: (
                0.0, 0.12 * H * (1 - bat(t - t0)), 0.0, 1 - 0.08 * (1 - bat(t - t0)), 0.0)))
    return canh


def _dung_canh(canh: Canh, giay: float, cd: str, ra: Path, fps: int, thiet_bi, ffmpeg: str) -> Path:
    cam = ke_hoach(cd, giay, canh)
    mien = MIEN_LIA.get(cd)

    def cam_cua(t):
        return cam(t), bool(mien and t > mien[0] * giay)

    return _ghi_video([(canh, giay, cam_cua)], ra, fps, thiet_bi, ffmpeg)


def _ghi_video(ds, ra: Path, fps: int, thiet_bi, ffmpeg: str) -> Path:
    """ds = [(canh, giây, cam_cua)] dựng nối tiếp vào MỘT mp4. cam_cua(t) -> (cam, phản_xạ)."""
    W, H = ds[0][0].W, ds[0][0].H
    cua = 0.5 / fps                                            # cửa trập 180°
    ra = Path(ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                          str(ra)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for canh, giay, cam_cua, *ve in ds:
            def cam(t, cam_cua=cam_cua):
                return cam_cua(t)[0]
            for i in range(max(1, round(giay * fps))):
                t = i / fps
                k = so_mau(_dich_chuyen(cam, t, cua, canh))
                if ve:                                         # trung bình k mẫu trong cửa trập
                    img = sum(ve[0](t + (cua * j / (k - 1) if k > 1 else 0.0)) for j in range(k)) / k
                else:
                    img, _ = dung_khung_mo(canh, cam_cua, t, cua, k, thiet_bi=thiet_bi)
                p.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        p.stdin.close()
    except BrokenPipeError:
        pass
    loi = p.stderr.read().decode("utf-8", "replace")
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg hỏng: {loi[-300:]}")
    return ra


# ═══════ CHUỖI 2–3 ảnh -> MỘT video (tool VOX riêng, user chốt 07/10/2026) ══════════
NOI = ("lia_len", "lia_ngang", "cat")
KHUNG = {"16:9": (1920, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920)}   # user chốt 07/10
MAU_ANH = ("chieu_sau", "popup")


def nhan_anh(anh) -> str:
    """Bản tách sống THEO ẢNH (dấu băm): cùng ảnh dựng lại ở việc nào cũng không tách lại."""
    return "anh/" + bam_anh(Path(anh))


def doc_anh_khung(anh, W: int, H: int) -> np.ndarray:
    """Đọc ảnh rồi cắt GIỮA cho đúng tỉ lệ khung — ảnh lệch tỉ lệ thì nền không phủ khung."""
    rgb = _doc_anh(Path(anh))
    h, w = rgb.shape[:2]
    if w / h > W / H:
        nw = round(h * W / H)
        return rgb[:, (w - nw) // 2:(w - nw) // 2 + nw]
    nh = round(w * H / W)
    return rgb[(h - nh) // 2:(h - nh) // 2 + nh]


def diem_pixel(diem, w: int, h: int) -> list[dict]:
    """Điểm bấm lưu theo TỈ LỆ (0..1) của ảnh đã cắt khung -> pixel cho SAM."""
    return [{"x": round(float(d["x"]) * w), "y": round(float(d["y"]) * h), "dau": int(d["dau"])}
            for d in diem or []]


PHONG_LIA = 0.15                  # phóng thêm lúc lia (ca1→ca2 đã duyệt: phóng 15% rồi lùi chậm)


def ke_hoach_chuoi(ds_canh, ds_giay, ds_cd, ds_noi, than=None):
    """-> [cam_cua(t) -> (cam, đang_lia)] theo giờ RIÊNG từng ảnh; ds_noi[i] = cú nối ảnh i -> i+1.

    Cú lia = MỘT cú trượt liền: ảnh trước tăng tốc (bậc 3) đẩy đi, ảnh sau nằm SÁT MÉP nó trượt
    vào rồi hãm (bậc 3) — vận tốc liền qua điểm cắt, phóng 15% lên rồi lùi. Chỗ ảnh này không phủ
    được lấp bằng ẢNH KẾ BÊN (`cam_cua.ghep(t)` -> (j, cam_j, t_j)), không phản chiếu mép: đo thật
    07/10 phản chiếu ra người LỘN NGƯỢC ở chỗ nối, nhoè không xoá được."""
    n = len(ds_canh)
    # `than`: camera riêng từng ảnh do máy biên đạo (bien_dao); không truyền thì theo mã camera cũ
    than = than or [ke_hoach(cd, g, c) for c, g, cd in zip(ds_canh, ds_giay, ds_cd)]
    tv = [min(0.6, 0.35 * g) for g in ds_giay]
    noi = [ds_noi[i] if i < len(ds_noi) else "cat" for i in range(n - 1)]

    def truc(kieu, canh):
        return (5, canh.H) if kieu == "lia_len" else (4, canh.W)

    def lech(i, t):
        """Phần cộng thêm của cú nối cho ảnh i ở giờ t: (trục, px lệch, hệ số phóng, đang_lia)."""
        ra = []
        if i < n - 1 and noi[i] != "cat":                       # đẩy đi
            s = min(1.0, max(0.0, (t - (ds_giay[i] - tv[i])) / tv[i]))
            k, L = truc(noi[i], ds_canh[i])
            ra.append((k, ZOOM * (1 + PHONG_LIA) * L / 2 * s ** 3, PHONG_LIA * s, s > 0))
        if i > 0 and noi[i - 1] != "cat":                       # trượt vào
            u = min(1.0, max(0.0, t / tv[i]))
            k, L = truc(noi[i - 1], ds_canh[i])
            ra.append((k, -ZOOM * (1 + PHONG_LIA) * L / 2 * (1 - u) ** 3, PHONG_LIA * (1 - u), u < 1))
        return ra

    def cam_rieng(i, t):
        c = list(than[i](min(max(t, 0.0), ds_giay[i])))
        lia = False
        for k, o, phong, dang in lech(i, t):
            c[k] += o
            c[3] *= 1 + phong
            lia = lia or dang
        return tuple(c), lia

    def lam(i):
        mien = MIEN_LIA.get(ds_cd[i])

        def cam_cua(t):
            c, lia = cam_rieng(i, t)
            return c, lia or bool(mien and t > mien[0] * ds_giay[i])

        def ghep(t):
            """Ảnh kế bên sát mép: đang đẩy đi -> ảnh sau ở giờ ÂM của nó; đang vào -> ảnh trước
            ở sau giờ cuối. Khoảng cách = nửa bề cao (rộng) hai tấm nền theo phóng hiện tại."""
            c, _ = cam_rieng(i, t)
            if i < n - 1 and noi[i] != "cat" and t > ds_giay[i] - tv[i]:
                j, tj = i + 1, t - ds_giay[i]
            elif i > 0 and noi[i - 1] != "cat" and t < tv[i]:
                j, tj = i - 1, ds_giay[i - 1] + t
            else:
                return None
            cj, _ = cam_rieng(j, tj)
            k, L = truc(noi[min(i, j)], ds_canh[i])
            khoang = ZOOM * L * (c[3] + cj[3]) / 2
            cj = list(cj)
            cj[k] = c[k] - khoang if j > i else c[k] + khoang     # lia lên/ngang: ảnh sau ở TRÊN/TRÁI
            return j, tuple(cj), min(max(tj, 0.0), ds_giay[j])

        cam_cua.ghep = ghep
        return cam_cua

    return [lam(i) for i in range(n)]


def khung_chuoi(ds_canh, cams, i: int, t: float, thiet_bi: str | None = None, tensor: bool = False):
    """MỘT mẫu khung của ảnh i ở giờ t; lúc lia thì lấp chỗ trống bằng ảnh kế bên. `tensor`: giữ trên thiết bị."""
    cam, lia = cams[i](t)
    g = cams[i].ghep(t)
    if g is None:
        return dung_khung(ds_canh[i], cam, t, thiet_bi=thiet_bi, phan_xa=lia, tensor=tensor)[0]
    j, cam_j, tj = g
    a, _, phu = dung_khung(ds_canh[i], cam, t, thiet_bi=thiet_bi, tra_phu=True, tensor=tensor)
    b = dung_khung(ds_canh[j], cam_j, tj, thiet_bi=thiet_bi, phan_xa=True, tensor=tensor)[0]
    if tensor:
        import torch
        return torch.where(phu[..., None], a, b)
    return np.where(phu[..., None], a, b)


def dung_chuoi(ds: list[dict], noi: list[str], ra: Path, kho_tach, W: int = 1920, H: int = 1080,
               fps: int = 30, uoc_do_sau=None, tach_lop=None, tach_theo_diem=None,
               thiet_bi: str | None = None, ffmpeg: str = "ffmpeg") -> Path:
    """ds = [{anh, giay, mau: chieu_sau|popup, cd, diem?}] -> MỘT mp4 nối liền.

    Pop-up: bản tách lưu theo ẢNH (`nhan_anh`), máy gắn ▲ khi không chắc; `diem` (tỉ lệ 0..1)
    có thì tách lại theo điểm bấm và ghi đè."""
    uoc = uoc_do_sau or globals()["uoc_do_sau"]
    ds_canh = []
    for x in ds:
        rgb = doc_anh_khung(x["anh"], W, H)
        if x.get("mau") == "popup":
            d = x.get("diem") or None
            # bản tách làm trên ảnh ĐÃ CẮT KHUNG -> dấu băm kèm khung: đổi khung thì tách lại
            ds_canh.append(_canh_popup(rgb, f"{bam_anh(Path(x['anh']))}@{W}x{H}", nhan_anh(x["anh"]), kho_tach,
                                       diem_pixel(d, rgb.shape[1], rgb.shape[0]) if d else None, d,
                                       W, H, uoc, tach_lop, tach_theo_diem))
        else:
            ds_canh.append(Canh(rgb, uoc(rgb), W, H, zoom=ZOOM))
    giay = [float(x["giay"]) for x in ds]
    cams = ke_hoach_chuoi(ds_canh, giay, [x.get("cd") or "" for x in ds], list(noi))
    ve = [lambda t, i=i: khung_chuoi(ds_canh, cams, i, t, thiet_bi) for i in range(len(ds))]
    return _ghi_video(list(zip(ds_canh, giay, cams, ve)), ra, fps, thiet_bi, ffmpeg)


# ═══════ 3 STYLE: Collage art / Black Grid / Non-Grid (user chốt 07/10/2026) ═══════════════
STYLE = ("collage", "black_grid", "non_grid")


def _the_anh(rgb, ti_le: float = 0.82):
    """Black Grid mà không có lớp: cả ảnh thành MỘT tấm dán giữa lưới (thu nhỏ, chừa lưới quanh)."""
    from PIL import Image

    h, w = rgb.shape[:2]
    nw, nh = int(w * ti_le), int(h * ti_le)
    nho = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS),
                     np.float32) / 255
    out = np.zeros_like(rgb)
    m = np.zeros((h, w), bool)
    y0, x0 = (h - nh) // 2, (w - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = nho
    m[y0:y0 + nh, x0:x0 + nw] = True
    return out, m


def _canh_style(rgb, khung_lop, giay: float, style: str, W: int, H: int, sam, uoc, va_nen, seed: int):
    """Một ảnh -> (Canh có lớp + nền theo style, kế hoạch biên đạo). Lớp từ KHUNG người chốt."""
    from scipy import ndimage as ndi

    from autoedit.collage import phong
    from autoedit.collage import lop as mlop

    PH, PW = rgb.shape[:2]
    z = uoc(rgb)
    hop = [mlop.khung_px(k, PW, PH) for k in khung_lop or []]
    hop = [b for b in hop if b[2] - b[0] >= 4 and b[3] - b[1] >= 4]
    masks = [m for m in (mlop.cat_theo_khung(rgb, hop, sam) if hop else []) if m.any()]
    nguon = rgb
    if not masks and style == "black_grid":
        nguon, m = _the_anh(rgb)
        masks = [m]
    zs, lo_lung = _z_theo_vai(masks, PW, PH, W, H)
    masks = mlop.chia_vung(masks, zs) if masks else []
    if style == "black_grid":
        nen, z_nen = phong.nen_luoi(PH, PW), np.full((PH, PW), 40.0, np.float32)
    elif masks:
        nen, z_nen = mlop.nen_sach(rgb, masks, va_nen), np.full((PH, PW), 40.0, np.float32)
    else:
        nen, z_nen = rgb, z                                      # không lớp: cả ảnh có chiều sâu
    s = PW / (W * ZOOM)                                          # px nguồn cho mỗi px xuất
    lop_mau = [(mau_, ndi.gaussian_filter(ndi.binary_dilation(m, iterations=max(1, round(3 * s))).astype(np.float32),
                                          0.8)) for mau_, m in mlop.ve_bu(nguon, masks, zs, va_nen)]
    return _ghep_canh(nen, z_nen, lop_mau, masks, zs, lo_lung, giay, style, W, H, seed)


def _z_theo_vai(masks, PW: int, PH: int, W: int, H: int):
    """Hình học thô từ mask -> vai trò -> Z (+ cờ vật lơ lửng)."""
    from autoedit.collage import bien_dao
    from autoedit.collage import lop as mlop

    S0 = W / PW * ZOOM
    tam = []
    for m in masks:
        ys, xs = np.nonzero(m)
        tam.append(bien_dao.Vat(((xs.min() + xs.max() + 1) / 2 - PW / 2) * S0, ((ys.min() + ys.max() + 1) / 2 - PH / 2) * S0,
                                (xs.max() + 1 - xs.min()) / 2 * S0, (ys.max() + 1 - ys.min()) / 2 * S0, 6.0,
                                mlop.cham_mep(m), mlop.la_lo_lung(m, masks)))
    zs = bien_dao.do_sau_theo_vai(tam, bien_dao.vai_tro(tam, W, H)) if masks else []
    return zs, [v.lo_lung for v in tam]


def _ghep_canh(nen, z_nen, lop_mau, masks, zs, lo_lung, giay: float, style: str, W: int, H: int, seed: int):
    """Nền + (màu, alpha) từng lớp -> Canh (viền trắng sticker MỌI style — user chốt 08/10: "bản chất collage art
    là sẽ có viền trắng xung quanh element") + kế hoạch biên đạo."""
    from autoedit.collage import bien_dao, phong
    from autoedit.collage import lop as mlop
    from autoedit.collage.dung import Lop

    canh = Canh(nen, z_nen, W, H, zoom=ZOOM)
    s = 1 / canh.S0
    vats = []
    for i, ((mau_, a), zz) in enumerate(zip(lop_mau, zs)):
        mau_, a = phong.vien_giay(mau_, a, seed + i, s)
        L = canh.them(Lop(np.dstack([mau_, a]), zz))
        h_, w_ = L.anh.shape[:2]
        vats.append(bien_dao.Vat(L.X, L.Y, w_ / 2 * L.k, h_ / 2 * L.k, zz, mlop.cham_mep(masks[i]), lo_lung[i]))
    kh = bien_dao.lap(vats, giay, style, W, H)
    for L, an in zip(canh.lop, kh.anims):
        L.anim = an
    return canh, kh


def _dai_giay_chu(mau_, a):
    """Layer CHỮ (mọi style đều có viền trắng): dán lên MỘT dải giấy liền (kiểu Vox) thay vì viền giấy quanh
    TỪNG NÉT — đo thật PSD Toyota 08/10: viền từng nét làm chữ nhỏ nhoè, khó đọc. Giấy theo độ tương phản:
    chữ tối -> giấy kem; chữ SÁNG -> giấy tối (chữ trắng trên giấy kem gần như không đọc được)."""
    from scipy import ndimage as ndi

    from autoedit.collage import phong

    o = a > 0.3
    if not o.any():
        return mau_, a
    lab, _ = ndi.label(o)
    cao = float(np.median([sl[0].stop - sl[0].start for sl in ndi.find_objects(lab)]))  # cao một chữ
    r, le = max(2, round(0.5 * cao)), max(1, round(0.2 * cao))     # lấp khe giữa chữ / lề giấy quanh chữ
    ys, xs = np.nonzero(o)
    pad = r + le + 2
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    k = np.pad(o[y0:y1, x0:x1], pad)
    giay = ndi.binary_dilation(ndi.binary_fill_holes(ndi.binary_closing(k, iterations=r)), iterations=le)
    vung = np.zeros(a.shape, np.float32)
    Y0, X0 = y0 - pad, x0 - pad
    cy0, cx0 = max(0, Y0), max(0, X0)
    cy1, cx1 = min(a.shape[0], Y0 + giay.shape[0]), min(a.shape[1], X0 + giay.shape[1])
    vung[cy0:cy1, cx0:cx1] = giay[cy0 - Y0:cy1 - Y0, cx0 - X0:cx1 - X0]
    al = np.maximum(ndi.gaussian_filter(vung, 0.8), a)
    sang = float((mau_[o] @ np.float32([0.299, 0.587, 0.114])).mean())
    giay_mau = np.float32(phong.KEM) if sang < 0.55 else np.float32([0.07, 0.07, 0.08])
    return giay_mau * (1 - a[..., None]) + mau_ * a[..., None], al


def _lam_muot(mau_, a, f: int, tron: float = 1.0, mem: float = 0.6):
    """Mép lớp TRÒN + FEATHER (như Smooth + Feather của Select and Mask). User báo 08/10: PSD PayPal 1280 px ở
    Collage art viền răng cưa rất nhiều — alpha sắc cạnh bị phóng ~2,8 lần bằng nội suy tuyến tính thành bậc thang;
    user: "tạo feather cho lớp cắt viền để trông tròn gọn và mượt".
    1) kéo màu mép lan vào vùng trong suốt (phóng không ám màu rác) · 2) phóng bicubic f lần ·
    3) SMOOTH: làm mượt hình `tron` px gốc (đường biên tròn đều) rồi kéo alpha lại chỉ còn FEATHER `mem` px gốc.
    Đo mép chéo 08/10: chỉ feather 0,6 px -> bậc thang 0,69 -> 0,41 px và mép nhoè 7 px; smooth 1 + feather 0,6
    -> 0,24 px, mép 5 px (phóng 3 lần)."""
    import torch
    from scipy import ndimage as ndi

    if (a < 0.5).any() and (a >= 0.5).any():
        iy, ix = ndi.distance_transform_edt(a < 0.5, return_distances=False, return_indices=True)
        mau_ = mau_[iy, ix]
    if f > 1:
        t = torch.from_numpy(np.ascontiguousarray(np.dstack([mau_, a]).transpose(2, 0, 1)))[None]
        t = torch.nn.functional.interpolate(t, scale_factor=f, mode="bicubic", align_corners=False)[0]
        mau_, a = t[:3].permute(1, 2, 0).numpy(), t[3].numpy()
    a = ndi.gaussian_filter(np.clip(a, 0, 1).astype(np.float32), tron * f)
    a = (a - 0.5) * (tron / mem) + 0.5                       # đường 0,5 giữ nguyên chỗ, mép thu về độ rộng feather
    return np.ascontiguousarray(np.clip(mau_, 0, 1), np.float32), np.clip(a, 0, 1)


def _canh_psd(duong, chon, giay: float, style: str, W: int, H: int, va_nen, seed: int):
    """Ảnh PSD (user chốt 08/10): lớp = layer NGƯỜI cắt (alpha mềm, phần bị che đã vẽ đủ) — không máy cắt,
    không vẽ bù. Gần/xa theo THỨ TỰ XẾP CHỒNG của PSD (layer trên = gần); luật vai trò chỉ chia các mức Z."""
    from scipy import ndimage as ndi

    from autoedit.collage import phong
    from autoedit.collage import psd as mpsd

    chu = {x["chi_so"]: x.get("chu") for x in mpsd.doc(duong)["lop"]}
    nen4, ds = mpsd.tach(duong, chon, W, H, rong_max=2 * W)
    # PSD nhỏ hơn mức camera phóng tới (1,15 x 1,6) -> làm việc ở f lần (tối đa 3); smooth/feather tính theo px
    # XUẤT (>= 1,6 / 1 px) để PSD to hay nhỏ đều mượt như nhau
    mag = W * ZOOM / nen4.shape[1]
    f = min(3, math.ceil(mag * 1.6)) if mag * 1.6 > 1.2 else 1
    ds = [(c, *_lam_muot(m, a, f, tron=max(1.0, 1.6 / mag), mem=max(0.6, 1.0 / mag)))
          for c, m, a in ds if (a > 0.01).any()]
    ds = [(_dai_giay_chu(m, a) if chu.get(c) else (m, a)) for c, m, a in ds]
    PH, PW = nen4.shape[0] * f, nen4.shape[1] * f
    masks = [a > 0.01 for _, a in ds]
    zs, lo_lung = _z_theo_vai(masks, PW, PH, W, H)
    zs = sorted(zs, reverse=True)                                # dưới cùng xa nhất -> trên cùng gần nhất
    if style == "black_grid":
        nen = phong.nen_luoi(PH, PW)
    else:
        nen = np.ascontiguousarray(nen4[..., :3])
        lo = nen4[..., 3] < 0.5
        if lo.any():  # team chưa vẽ kín nền sau khối -> vá, ở cỡ GỐC (đo 08/10: vá ở cỡ đã phóng 3 lần LaMa đòi 29,7 GB)
            lo = ndi.binary_dilation(lo, iterations=2)
            nen = np.where(lo[..., None], np.asarray(va_nen(nen, lo), np.float32), nen)
        if f > 1:
            import torch
            t = torch.nn.functional.interpolate(torch.from_numpy(np.ascontiguousarray(nen.transpose(2, 0, 1)))[None],
                                                scale_factor=f, mode="bicubic", align_corners=False)[0]
            nen = np.ascontiguousarray(np.clip(t.permute(1, 2, 0).numpy(), 0, 1))
    return _ghep_canh(nen, np.full((PH, PW), 40.0, np.float32), ds, masks, zs, lo_lung, giay, style, W, H, seed)


def _dich_style(canh, cam_cua, t: float, dt: float) -> float:
    """Quãng dịch lớn nhất (px) của nền + từng lớp giữa t và t+dt -> số mẫu nhoè chuyển động."""
    a, b = cam_cua(t)[0], cam_cua(t + dt)[0]
    d = (abs(b[0] - a[0]) + abs(b[1] - a[1])) / 40 + abs(b[4] - a[4]) + abs(b[5] - a[5])
    for L in canh.lop:
        p = []
        for c, tt in ((a, t), (b, t + dt)):
            ox, oy, r, sc, dz = (float(x) for x in L.anim(tt))
            dd = max(L.Z0 + dz - c[2], 0.3)
            kk = c[3] * L.Z0 / dd * L.k * sc * max(L.anh.shape[:2])
            p.append((c[3] * ((L.X + ox) * L.Z0 - c[0]) / dd + c[4],
                      c[3] * ((L.Y + oy) * L.Z0 - c[1]) / dd + c[5], kk, r))
        (x0, y0, k0, r0), (x1, y1, k1, r1) = p
        d = max(d, math.hypot(x1 - x0, y1 - y0) + abs(k1 - k0) / 2 + abs(r1 - r0) * k1 / 115)
    return d


def dung_style(ds: list[dict], ra: Path, W: int = 1920, H: int = 1080, style: str = "collage", sam=None,
               uoc_do_sau=None, va_nen=None, thiet_bi: str | None = None, ffmpeg: str = "ffmpeg") -> Path:
    """ds = [{anh, giay, khung_lop: [[x0,y0,x1,y1] tỉ lệ 0..1] | psd_lop: [chỉ số khối PSD]}] -> MỘT mp4. Máy tự biên đạo nhịp +
    camera (bien_dao), tự chọn cú nối (khung ngang: lia ngang; khung dọc: lia lên)."""
    import torch

    from autoedit.collage import phong, tach

    if style not in STYLE:
        raise ValueError(f"Style lạ: {style}")
    sam = sam or tach.TachSam()
    uoc = uoc_do_sau or globals()["uoc_do_sau"]
    va = va_nen or tach.va_nen_lama
    giay = [float(x["giay"]) for x in ds]
    cap = [_canh_psd(x["anh"], x["psd_lop"], g, style, W, H, va, 10 * i) if x.get("psd_lop") else
           _canh_style(doc_anh_khung(x["anh"], W, H), x.get("khung_lop"), g, style, W, H, sam, uoc, va, 10 * i)
           for i, (x, g) in enumerate(zip(ds, giay))]
    ds_canh = [c for c, _ in cap]
    noi = ["lia_ngang" if W >= H else "lia_len"] * (len(ds) - 1)
    cams = ke_hoach_chuoi(ds_canh, giay, [""] * len(ds), noi, than=[kh.cam for _, kh in cap])
    fps = phong.FPS[style]
    ra = Path(ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-r", "30" if fps == 30 else "24",
                          "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ra)],
                         stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    cua, so = 0.5 / 30, 0
    try:
        for i in range(len(ds)):
            for f in range(max(1, round(giay[i] * fps))):
                t = f / fps
                # khung hình là tensor TRÊN thiết bị suốt dựng -> nhoè -> hậu kỳ; chép về CPU một lần lúc xuất
                if style == "collage":                           # 30 hình/giây + nhoè chuyển động
                    k = so_mau(_dich_style(ds_canh[i], cams[i], t, cua))
                    img = sum(khung_chuoi(ds_canh, cams, i, t + (cua * j / (k - 1) if k > 1 else 0.0), thiet_bi,
                                          tensor=True) for j in range(k)) / k
                else:                                            # Vox: 12 hình/giây, nét
                    img = khung_chuoi(ds_canh, cams, i, t, thiet_bi, tensor=True)
                img = phong.hau_ky(img, so, t, style)
                so += 1
                p.stdin.write((img * 255 + 0.5).to(torch.uint8).cpu().numpy().tobytes())
        p.stdin.close()
    except BrokenPipeError:
        pass
    loi = p.stderr.read().decode("utf-8", "replace")
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg hỏng: {loi[-300:]}")
    return ra
