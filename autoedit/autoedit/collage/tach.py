"""Tách layer TỰ ĐỘNG từ một ảnh cảnh — không ai bấm điểm, không thêm thư viện.

Đo 06/10/2026 trên 5 cảnh thật SE001: mảng gần theo độ sâu -> điểm gợi ý (distance transform)
-> SAM 2.1 small (3 phương án) -> giữ phương án có MÉP GÃY ĐỘ SÂU rõ nhất -> LaMa vá nền.
Tách đúng: người họp báo, tháp tàu ngầm, vai người tiền cảnh. Mặt biển/mặt đất "gần" nhưng
độ sâu chuyển dần + chạm cả hai mép khung -> loại. Không vật nào -> cờ để lùi về "Chiều sâu".

Giấy phép: SAM 2.1 Apache 2.0 · LaMa (big-lama) Apache 2.0 · Depth Anything V2 Small Apache 2.0.
Bộ xử lý ảnh SAM 2 của transformers đòi torchvision (venv không có, cài vào có thể kéo thay cả
torch +cpu) -> tiền xử lý làm tay ĐÚNG thông số gốc (1024², ImageNet, điểm x*1024/W).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

SAM_ID = "facebook/sam2.1-hiera-small"
LAMA_URL = "https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt"
BUOC_MEP_TOI_THIEU = 0.08          # bước nhảy độ chênh tại mép (0 xa .. 1 gần) để coi là vật nổi


@dataclass
class KetQuaTach:
    vat: list = field(default_factory=list)       # [(mask bool HxW, Z trung vị của vật)]
    nen: np.ndarray | None = None                 # ảnh nền đã vá chỗ vật nhấc ra
    z_nen: np.ndarray | None = None
    co: list = field(default_factory=list)        # cờ "không chắc" để review có trọng điểm


def otsu(v: np.ndarray) -> float:
    h, b = np.histogram(v, 64, (0, 1))
    p = h / max(h.sum(), 1)
    w = np.cumsum(p)
    m = np.cumsum(p * (b[:-1] + b[1:]) / 2)
    s = (m[-1] * w - m) ** 2 / (w * (1 - w) + 1e-9)
    return float(b[np.argmax(s) + 1])


def lam_sach(m: np.ndarray) -> np.ndarray:
    """Lấp lỗ + giữ mảng liền lớn nhất (mask SAM lấm tấm ở vùng cùng màu)."""
    m = ndi.binary_fill_holes(m)
    nh, n = ndi.label(m)
    if n > 1:
        m = nh == 1 + int(np.argmax(ndi.sum(m, nh, range(1, n + 1))))
    return m


def buoc_mep(m: np.ndarray, v: np.ndarray) -> float:
    """Bước nhảy độ chênh NGAY TẠI MÉP mask (bỏ phần mép trùng khung ảnh)."""
    trong = m & ~ndi.binary_erosion(m, iterations=4)
    ngoai = ndi.binary_dilation(m, iterations=8) & ~ndi.binary_dilation(m, iterations=3)
    khung = np.zeros_like(m)
    khung[6:-6, 6:-6] = True
    trong, ngoai = trong & khung, ngoai & khung
    if trong.sum() < 20 or ngoai.sum() < 20:
        return 0.0
    return float(np.median(v[trong]) - np.median(v[ngoai]))


def cham_bien(m: np.ndarray, le: int = 2) -> dict:
    return {"trai": bool(m[:, :le].any()), "phai": bool(m[:, -le:].any()),
            "tren": bool(m[:le].any()), "duoi": bool(m[-le:].any())}


def hop_le(m: np.ndarray, diem_sam: float, v: np.ndarray) -> bool:
    phu = float(m.mean())
    b = cham_bien(m)
    if not (0.01 < phu < 0.6) or diem_sam <= 0.5:
        return False
    if (b["trai"] and b["phai"]) or (b["tren"] and b["duoi"]):      # mặt phẳng nền trải ngang/dọc khung
        return False
    return buoc_mep(m, v) > BUOC_MEP_TOI_THIEU


def diem_goi_y(v: np.ndarray, so_diem: int = 6, toi_da: int = 3) -> list[list[list[int]]]:
    """Mảng GẦN theo độ sâu (Otsu) -> mỗi mảng `so_diem` điểm nằm sâu bên trong."""
    if float(v.max() - v.min()) < 1e-6:
        return []
    h, w = v.shape
    k = max(1, int(min(h, w) * 0.004))
    gan = ndi.binary_closing(ndi.binary_opening(v > otsu(v), iterations=k), iterations=int(k * 1.6) + 1)
    nhan, n = ndi.label(gan)
    if not n:
        return []
    dt = ndi.sum(np.ones_like(v), nhan, range(1, n + 1))
    ra = []
    for i in np.argsort(-dt)[:toi_da]:
        if dt[i] < 0.015 * v.size:
            continue
        d = ndi.distance_transform_edt(nhan == i + 1)
        ys, xs = np.nonzero(d > 0.5 * d.max())
        idx = np.linspace(0, len(xs) - 1, so_diem).astype(int)
        ra.append([[int(xs[j]), int(ys[j])] for j in idx])
    return ra


def do_chenh(z: np.ndarray) -> np.ndarray:
    """Độ sâu Z -> độ chênh 0 (xa) .. 1 (gần)."""
    d = 1.0 / np.asarray(z, np.float32)
    return (d - d.min()) / max(float(d.max() - d.min()), 1e-9)


DIEM_SAM_CHAC = 0.75               # SAM tự chấm dưới mức này -> cờ ⚠
MEP_CHAC = 0.15                    # bước mép dưới mức này -> cờ ⚠ (vật lẫn vào nền)


def tach_lop(rgb, z, sam=None, va_nen=None, uoc_do_sau=None, toi_da: int = 3) -> KetQuaTach:
    sam = sam or TachSam()
    v = do_chenh(z)
    vat, co = [], []
    for pts in diem_goi_y(v, toi_da=toi_da):
        ung = [(buoc_mep(m, v), sc, m) for m, sc in ((lam_sach(m), sc) for m, sc in sam.tach(rgb, pts))
               if hop_le(m, sc, v)]
        if not ung:
            continue
        b, sc, m = max(ung, key=lambda x: x[0])
        if any((m & a).sum() > 0.5 * min(m.sum(), a.sum()) for a, _ in vat):
            continue                                              # trùng vật đã có
        vat.append((m, float(np.median(z[m]))))
        co += [c for c, xau in (("diem_sam_thap", sc < DIEM_SAM_CHAC), ("mep_yeu", b < MEP_CHAC))
               if xau and c not in co]
    if not vat:
        return KetQuaTach([], rgb, z, ["khong_tach_duoc_vat"])
    return _va(rgb, z, vat, co, va_nen, uoc_do_sau)


def tach_theo_diem(rgb, z, diem, sam=None, va_nen=None, uoc_do_sau=None) -> KetQuaTach:
    """Editor bấm lên ảnh: dau=1 là VẬT, dau=0 là KHÔNG phải vật. Người đã chỉ rõ thì lấy
    phương án SAM tự chấm cao nhất (không dò mép như lúc tự động) và KHÔNG gắn cờ: đo thật
    06/10 cảnh tàu trên biển — bấm 3 điểm ra đúng cả thân + tháp mà SAM vẫn tự chấm < 0,6,
    gắn ▲ là báo động giả ngay sau lúc người vừa sửa."""
    if not any(int(d.get("dau", 1)) == 1 for d in diem):
        raise ValueError("Cần ít nhất một điểm bấm VÀO vật.")
    sam = sam or TachSam()
    ds = sam.tach(rgb, [[int(d["x"]), int(d["y"])] for d in diem], [int(d.get("dau", 1)) for d in diem])
    m, _ = max(ds, key=lambda x: x[1])
    m = lam_sach(m)
    return _va(rgb, z, [(m, float(np.median(z[m])))], [], va_nen, uoc_do_sau)


def _va(rgb, z, vat, co, va_nen, uoc_do_sau) -> KetQuaTach:
    hop = np.zeros(np.asarray(z).shape, bool)
    for m, _ in vat:
        hop |= m
    nen = (va_nen or va_nen_lama)(rgb, ndi.binary_dilation(hop, iterations=12))
    return KetQuaTach(vat, nen, uoc_do_sau(nen) if uoc_do_sau else z, co)


# ------------------------------------------------------------------ model thật (nạp lười)
class TachSam:
    """SAM 2.1 small qua transformers, tiền xử lý làm tay (không cần torchvision)."""
    _model = None

    def tach(self, rgb: np.ndarray, pts, nhan=None) -> list:
        import torch
        from PIL import Image
        from transformers import Sam2Model

        if TachSam._model is None:
            TachSam._model = Sam2Model.from_pretrained(SAM_ID).eval()
        H, W = rgb.shape[:2]
        im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR)
        x = (np.asarray(im, np.float32) / 255 - np.float32([0.485, 0.456, 0.406])) / np.float32([0.229, 0.224, 0.225])
        p = torch.tensor([[[[px * 1024 / W, py * 1024 / H] for px, py in pts]]], dtype=torch.float32)
        with torch.no_grad():
            nh = torch.tensor([[list(nhan) if nhan else [1] * len(pts)]], dtype=torch.long)
            o = TachSam._model(pixel_values=torch.from_numpy(x).permute(2, 0, 1)[None], input_points=p,
                               input_labels=nh, multimask_output=True)
        m = torch.nn.functional.interpolate(o.pred_masks[0].float(), (H, W), mode="bilinear",
                                            align_corners=False)[0].numpy() > 0
        sc = o.iou_scores[0, 0].numpy()
        return [(m[i], float(sc[i])) for i in range(len(m))]


_LAMA = None


def va_nen_lama(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """LaMa (big-lama TorchScript, Apache 2.0) vá chỗ `mask`. Tải 1 lần vào cache torch hub."""
    global _LAMA
    import torch

    if _LAMA is None:
        p = Path(torch.hub.get_dir()) / "checkpoints" / "big-lama.pt"
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            torch.hub.download_url_to_file(LAMA_URL, str(p))
        _LAMA = torch.jit.load(str(p), map_location="cpu").eval()
    h, w = mask.shape
    H, W = (h + 7) // 8 * 8, (w + 7) // 8 * 8
    a = np.zeros((H, W, 3), np.float32)
    a[:h, :w] = rgb
    b = np.zeros((H, W), np.float32)
    b[:h, :w] = mask
    with torch.no_grad():
        o = _LAMA(torch.from_numpy(a).permute(2, 0, 1)[None], torch.from_numpy(b)[None, None])[0]
    return np.clip(o.permute(1, 2, 0).numpy()[:h, :w], 0, 1)
