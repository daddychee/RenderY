r"""DẢI HÌNH tách khỏi dải VOICE (user chốt 08/09 — "tách như phần mềm dựng").

Trước: 1 khối = voice + hình dính liền, khoảng thở chỉ là đuôi khối trước ->
không thêm được footage thứ 2 vào khoảng thở 8s.
Nay: hai dải độc lập trên CÙNG trục thời gian
  khoi[]  — VOICE, bất biến (v0/v1 + tho/tho_them; server gác luật 422)
  hinh[]  — MIẾNG HÌNH cắt tự do: {t0, dur, uv, chon, khoi_goc, nguoi_sua}
            1 khoảng thở chứa được nhiều miếng; 1 miếng trải qua nhiều khối voice.

Tương thích ngược: hợp đồng cũ (chỉ có khoi[]) đọc lên tự sinh hinh[] 1-1.
Trục thời gian TIMELINE = trục voice + tổng tho_them phía trước (một chỗ duy
nhất tính: `moc_timeline`).
"""

from __future__ import annotations

TOI_THIEU_S = 0.4          # miếng hình ngắn hơn -> vô nghĩa khi dựng


def moc_timeline(khoi: list[dict]) -> list[tuple[float, float, float]]:
    """[(t0_nói, t1_nói, t1_thở)] trên trục TIMELINE (đã cộng tho_them trước đó)."""
    ra, doi = [], 0.0
    for k in khoi:
        t0 = k["v0"] + doi
        t1 = k["v1"] + doi
        nghi = max(0.0, (k.get("tho") or 0) + (k.get("tho_them") or 0))
        ra.append((round(t0, 3), round(t1, 3), round(t1 + nghi, 3)))
        doi += (k.get("tho_them") or 0)
    return ra


def tong_dai(khoi: list[dict]) -> float:
    m = moc_timeline(khoi)
    return round(m[-1][2], 2) if m else 0.0


def sinh_tu_khoi(khoi: list[dict]) -> list[dict]:
    """Hợp đồng cũ -> dải hình 1-1 (mỗi khối 1 miếng phủ trọn nói + thở)."""
    ra = []
    for i, (t0, t1, tt) in enumerate(moc_timeline(khoi)):
        k = khoi[i]
        ra.append({"t0": t0, "dur": round(tt - t0, 3), "khoi_goc": i,
                   "uv": k.get("uv") or [], "chon": k.get("chon", -1),
                   "nguoi_sua": bool(k.get("nguoi_sua"))})
    return ra


def dam_bao(hd: dict) -> list[dict]:
    """Trả hinh[] của hợp đồng, sinh mới nếu chưa có (migration mềm)."""
    if not hd.get("hinh"):
        hd["hinh"] = sinh_tu_khoi(hd.get("khoi") or [])
    return hd["hinh"]


def dong_bo_sau_tho(hd: dict, hinh_cu_moc: list[tuple[float, float, float]]) -> None:
    """+1s/−1s làm mốc voice dịch -> dời các miếng hình theo ĐÚNG khối gốc của
    chúng, giữ nguyên tỉ lệ trong ô (không để hình trôi khỏi lời)."""
    moi = moc_timeline(hd.get("khoi") or [])
    for h in hd.get("hinh") or []:
        i = h.get("khoi_goc")
        if i is None or not (0 <= i < len(moi)) or i >= len(hinh_cu_moc):
            continue
        c0, _, c2 = hinh_cu_moc[i]
        n0, _, n2 = moi[i]
        cu_dai = max(0.001, c2 - c0)
        ty = (h["t0"] - c0) / cu_dai
        ty_dai = h["dur"] / cu_dai
        moi_dai = max(0.001, n2 - n0)
        h["t0"] = round(n0 + ty * moi_dai, 3)
        h["dur"] = round(max(TOI_THIEU_S, ty_dai * moi_dai), 3)
    khit_mep(hd)


def them_mieng(hd: dict, tai_giay: float) -> int:
    """⊞ Thêm hình: chẻ miếng đang phủ `tai_giay` làm đôi. Trả index miếng MỚI."""
    hinh = dam_bao(hd)
    for j, h in enumerate(hinh):
        if h["t0"] <= tai_giay < h["t0"] + h["dur"]:
            trai = max(TOI_THIEU_S, round(tai_giay - h["t0"], 3))
            phai = round(h["dur"] - trai, 3)
            if phai < TOI_THIEU_S:              # quá sát mép -> chia đôi
                trai = round(h["dur"] / 2, 3)
                phai = round(h["dur"] - trai, 3)
            moi = {**h, "t0": round(h["t0"] + trai, 3), "dur": phai,
                   "chon": -1, "nguoi_sua": True}
            h["dur"] = trai
            h["nguoi_sua"] = True
            hinh.insert(j + 1, moi)
            khit_mep(hd)
            return j + 1
    return -1


def bo_mieng(hd: dict, idx: int) -> bool:
    """Bỏ miếng: miếng trước nở ra phủ chỗ trống (không để timeline hở)."""
    hinh = dam_bao(hd)
    if not (0 <= idx < len(hinh)) or len(hinh) <= 1:
        return False
    h = hinh.pop(idx)
    ke = hinh[idx - 1] if idx > 0 else hinh[0]
    if idx > 0:
        ke["dur"] = round(ke["dur"] + h["dur"], 3)
    else:
        ke["t0"] = h["t0"]
        ke["dur"] = round(ke["dur"] + h["dur"], 3)
    ke["nguoi_sua"] = True
    khit_mep(hd)
    return True


def keo_mep(hd: dict, idx: int, dur_moi: float) -> bool:
    """Kéo mép phải miếng idx — miếng kế bù trừ (tổng bất biến). Miếng được
    phép TRẢI QUA nhiều khối voice: không kẹp theo ranh lời."""
    hinh = dam_bao(hd)
    if not (0 <= idx < len(hinh) - 1):
        return False
    a, b = hinh[idx], hinh[idx + 1]
    tong = a["dur"] + b["dur"]
    d = max(TOI_THIEU_S, min(dur_moi, tong - TOI_THIEU_S))
    a["dur"] = round(d, 3)
    b["t0"] = round(a["t0"] + d, 3)
    b["dur"] = round(tong - d, 3)
    a["nguoi_sua"] = b["nguoi_sua"] = True
    khit_mep(hd)
    return True


def khit_mep(hd: dict) -> None:
    """Ép t0 miếng sau = hết miếng trước — dọn lệch làm tròn tích lũy (bug
    SegmentOverlap 08/09). Gọi sau MỌI thao tác dải hình."""
    hinh = dam_bao(hd)
    for i in range(1, len(hinh)):
        hinh[i]["t0"] = round(hinh[i - 1]["t0"] + hinh[i - 1]["dur"], 3)


def kiem(hd: dict) -> list[str]:
    """Rào kiểm dải hình: liền mạch, không chồng, phủ hết timeline."""
    hinh = dam_bao(hd)
    loi = []
    tong = tong_dai(hd.get("khoi") or [])
    for i, h in enumerate(hinh):
        if h["dur"] < TOI_THIEU_S - 0.01:
            loi.append(f"miếng {i + 1}: {h['dur']:.2f}s quá ngắn")
        if i and abs(h["t0"] - (hinh[i - 1]["t0"] + hinh[i - 1]["dur"])) > 0.005:
            loi.append(f"miếng {i + 1}: hở/chồng với miếng trước")
    if hinh and abs((hinh[-1]["t0"] + hinh[-1]["dur"]) - tong) > 0.15:
        loi.append("dải hình không phủ hết timeline voice")
    return loi
