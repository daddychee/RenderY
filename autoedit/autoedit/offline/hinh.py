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
SAN_LANG_S = 0.2           # im lặng hiệu dụng tối thiểu giữa 2 câu (cùng sàn với UI)


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


SAN_CHE_S = 0.7            # sàn cứng của máy — miếng ngắn hơn thì dựng vô nghĩa
NGUONG_CHE = 1.6          # khối dài hơn 1,6× chuẩn kênh mới xét chẻ
TRAN_GIU = 2.5            # dài quá mức này thì PHẢI chẻ, dù còn quota "giữ lâu"
LA_GIU = 1.3              # miếng dài hơn 1,3× chuẩn kênh được tính là "giữ lâu"


def _diem_che(k: dict, t0: float, span: float, than: float, n: int) -> list[float]:
    """n miếng đều nhau, NHƯNG né về RANH MỀM có sẵn nếu ở gần.

    Ranh mềm = chỗ người đọc ngắt 0,3-0,5s (khoi.py đã đo). Chẻ ở đó thì mắt
    không thấy gượng; chẻ giữa một câu liền mạch thì thấy ngay.
    """
    doi = t0 - float(k.get("v0") or 0)             # voice -> timeline
    mem = sorted(float(x) + doi for x in (k.get("ranh_mem") or []))
    dung_sai = than * 0.4
    ra: list[float] = []
    for j in range(1, n):
        ly_tuong = t0 + span * j / n
        gan = min((x for x in mem if abs(x - ly_tuong) <= dung_sai),
                  key=lambda x: abs(x - ly_tuong), default=None)
        ra.append(round(gan if gan is not None else ly_tuong, 3))
    return ra


def che_mot_khoi(k: dict, t0: float, tt: float, than: float,
                 cho_giu: bool = False) -> list[tuple[float, float]]:
    """1 khối -> [(t0, dur)] các miếng hình. `than` = 0 thì giữ nguyên 1 miếng.

    Vì sao có hàm này (SEQUENCE PH3): dải hình đang sinh 1-1 với khối, tức nhịp
    video = nhịp THỞ của người đọc voice, không phải nhịp kênh ref. Đo 07/09:
    median khối 2,18s ở tập này nhưng 4,08s ở tập kia — chênh gần 2×, và có
    chương chứa shot 18 giây.
    """
    span = round(tt - t0, 3)
    if than <= 0 or span <= than * NGUONG_CHE:
        return [(t0, span)]
    # còn quota "giữ lâu" và chưa quá trần -> để nguyên, đó là shot giữ
    if cho_giu and span <= than * TRAN_GIU:
        return [(t0, span)]
    n = max(2, round(span / than))
    while n > 2 and span / n < SAN_CHE_S:          # đừng chẻ vụn dưới sàn
        n -= 1
    if span / n < SAN_CHE_S:
        return [(t0, span)]
    moc = [t0] + _diem_che(k, t0, span, than, n) + [tt]
    ra: list[tuple[float, float]] = []
    for a, b in zip(moc, moc[1:]):
        if b - a < SAN_CHE_S and ra:               # né mềm hụt sàn -> nhập lùi
            truoc = ra[-1]
            ra[-1] = (truoc[0], round(b - truoc[0], 3))
        else:
            ra.append((round(a, 3), round(b - a, 3)))
    return ra


def sinh_tu_khoi(khoi: list[dict], than: float = 0.0,
                 hold: float = 0.0) -> list[dict]:
    """Khối -> dải hình. `than`=0 (mặc định) giữ nguyên hành vi cũ: 1 khối 1 miếng.

    `than`/`hold` lấy từ Framing Insight của kênh ref: chẻ khối dài về quanh
    `than`, nhưng chừa `hold` phần shot cố tình để dài (GoDoc: thân 4,73s,
    hold 38% — chẻ đều tất thì mất luôn nhịp giữ của kênh).
    """
    ra: list[dict] = []
    so_giu = 0
    for i, (t0, _t1, tt) in enumerate(moc_timeline(khoi)):
        k = khoi[i]
        cho_giu = than > 0 and hold > 0 and (so_giu + 1) <= hold * (len(ra) + 1)
        mieng = che_mot_khoi(k, t0, tt, than, cho_giu=cho_giu)
        for j, (a, dur) in enumerate(mieng):
            if than > 0 and dur > than * LA_GIU:
                so_giu += 1
            ra.append({"t0": a, "dur": dur, "khoi_goc": i,
                       # ứng viên/lựa chọn của khối gắn vào MIẾNG ĐẦU — miếng
                       # chẻ thêm để trống, người (hoặc phễu) đổ hình sau
                       "uv": (k.get("uv") or []) if j == 0 else [],
                       "chon": k.get("chon", -1) if j == 0 else -1,
                       "nguoi_sua": bool(k.get("nguoi_sua")) if j == 0 else False})
    return ra


def dam_bao(hd: dict) -> list[dict]:
    """Trả hinh[] của hợp đồng, sinh mới nếu chưa có (migration mềm)."""
    if not hd.get("hinh"):
        hd["hinh"] = sinh_tu_khoi(hd.get("khoi") or [])
    return hd["hinh"]


def chua_lech(hd: dict) -> bool:
    """Hợp đồng cũ có khoi_goc lệch (di chứng thao tác trước bản 08/09) -> gán
    lại theo vị trí. Trả True nếu đã phải chữa."""
    moc = moc_timeline(hd.get("khoi") or [])
    hinh = dam_bao(hd)
    lech = False
    for h in hinh:
        i = h.get("khoi_goc")
        if i is None or not (0 <= i < len(moc)):
            lech = True
            break
        n0, _n1, n2 = moc[i]
        giua = h["t0"] + h["dur"] / 2
        if not (n0 - 0.05 <= giua < n2 + 0.05):
            lech = True
            break
    if lech:
        gan_lai_khoi_goc(hd)
    # KHỐI TRỐNG (không miếng nào phủ) -> cấp miếng riêng: mỗi ô voice luôn có
    # ít nhất 1 miếng, nếu không +/-1s sẽ dồn nhầm sang ô khác (LI100 08/09:
    # 15 miếng cho 17 khối, 2 khối trống).
    co = {h.get("khoi_goc") for h in hinh}
    thieu = [i for i in range(len(moc)) if i not in co]
    if thieu:
        for i in thieu:
            n0, _n1, n2 = moc[i]
            hinh.append({"t0": n0, "dur": round(max(TOI_THIEU_S, n2 - n0), 3),
                         "khoi_goc": i, "uv": [], "chon": -1, "nguoi_sua": False})
        hinh.sort(key=lambda h: h["t0"])
        # ô bị miếng CŨ lấn -> cắt lại theo đúng ranh ô của khối gốc
        for i, (n0, _n1, n2) in enumerate(moc):
            ds = [h for h in hinh if h.get("khoi_goc") == i]
            if not ds:
                continue
            t = n0
            for h in ds:
                h["t0"] = round(t, 3)
                h["dur"] = round(max(TOI_THIEU_S, min(h["dur"], n2 - t)), 3)
                t = round(t + h["dur"], 3)
            if abs(n2 - t) > 0.001:
                ds[-1]["dur"] = round(max(TOI_THIEU_S, ds[-1]["dur"] + (n2 - t)), 3)
        khit_mep(hd)
        lech = True
    return lech


def dong_bo_sau_tho(hd: dict, hinh_cu_moc: list[tuple[float, float, float]]) -> None:
    """+1s/−1s: cộng/trừ thời gian VÀO MIẾNG HÌNH NẰM TRONG KHOẢNG THỞ, không
    đụng miếng của khối khác (user chốt 08/09 — "thêm bớt thời gian vào HÌNH
    chứ không phải vào voice; ranh giữa 2 mốc voice không được tràn sang nhau").

    Cách làm: mỗi khối có ô [t0_nói .. t1_thở]. Δ của khối i chỉ được tiêu thụ
    bởi các miếng nằm TRONG vùng thở của khối i (t1_nói..t1_thở); thiếu chỗ thì
    miếng cuối cùng phủ vùng nói cũng nhận phần dư — nhưng KHÔNG BAO GIỜ lấn
    sang ô của khối kế. Các miếng thuộc khối sau chỉ TỊNH TIẾN nguyên khối.
    """
    moi = moc_timeline(hd.get("khoi") or [])
    hinh = dam_bao(hd)
    if not moi or not hinh or len(hinh_cu_moc) < len(moi):
        khit_mep(hd)
        return

    # gom miếng theo khối gốc, giữ nguyên thứ tự
    theo_khoi: dict[int, list[dict]] = {}
    for h in hinh:
        theo_khoi.setdefault(h.get("khoi_goc", 0), []).append(h)

    con_tro = moi[0][0]
    for i, (n0, n1, n2) in enumerate(moi):
        ds = theo_khoi.get(i) or []
        o_moi = round(n2 - n0, 3)                     # ô khối i SAU khi đổi thở
        if not ds:
            con_tro = n2
            continue
        c0, _c1, c2 = hinh_cu_moc[i]
        o_cu = max(0.001, c2 - c0)
        delta = round(o_moi - o_cu, 3)                # + nới / − thu, CHỈ ô này

        # ô nới/thu: dồn hết delta vào MIẾNG CUỐI của ô (miếng nằm trong vùng thở)
        if abs(delta) > 0.001:
            cuoi = ds[-1]
            cuoi["dur"] = round(cuoi["dur"] + delta, 3)
            if cuoi["dur"] < TOI_THIEU_S:             # miếng thở cạn -> lấy tiếp
                thieu = TOI_THIEU_S - cuoi["dur"]
                cuoi["dur"] = TOI_THIEU_S
                for h in reversed(ds[:-1]):
                    lay = min(thieu, max(0.0, h["dur"] - TOI_THIEU_S))
                    h["dur"] = round(h["dur"] - lay, 3)
                    thieu = round(thieu - lay, 3)
                    if thieu <= 0.001:
                        break
                if thieu > 0.001 and len(ds) == 1:    # ô chỉ 1 miếng: ép bằng ô
                    cuoi["dur"] = max(TOI_THIEU_S, o_moi)

        # đặt lại mốc trong ô — miếng thuộc khối SAU chỉ tịnh tiến (không co)
        t = n0
        for h in ds:
            h["t0"] = round(t, 3)
            t = round(t + h["dur"], 3)
        # sai số cộng dồn: ép miếng cuối khớp đúng mép ô (ranh voice bất khả xâm phạm)
        lech = round(n2 - t, 3)
        if abs(lech) > 0.001 and ds:
            ds[-1]["dur"] = round(max(TOI_THIEU_S, ds[-1]["dur"] + lech), 3)
        con_tro = n2
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
            gan_lai_khoi_goc(hd)
            return j + 1
    return -1


def bo_mieng(hd: dict, idx: int) -> tuple[bool, float]:
    """Bỏ miếng. Trả (ok, số giây im lặng đã co).

    Hai luật theo VỊ TRÍ miếng (bug user bắt 06/09):
      - phần miếng trong vùng NÓI: miếng cạnh nở ra phủ — voice bất biến.
      - phần miếng đè KHOẢNG THỞ: khoảng lặng CO LẠI đúng bấy nhiêu (sàn
        SAN_LANG_S), cả cụm voice+hình phía sau trượt lên — dùng lại đúng cơ
        chế ±thở đã nghiệm thu 08/09. Bản cũ chỉ có luật một: xóa ô thở 1.5s
        thì hình phủ kín nhưng tai vẫn nghe 1.5s im lặng — UI đánh lừa.
    """
    hinh = dam_bao(hd)
    if not (0 <= idx < len(hinh)) or len(hinh) <= 1:
        return False, 0.0
    khoi = hd.get("khoi") or []
    moc_cu = moc_timeline(khoi)
    h = hinh[idx]
    a, b = h["t0"], h["t0"] + h["dur"]
    # phần đè lên khoảng thở của khối nào -> co khoảng lặng khối ấy
    tho_co = 0.0
    for i, (_n0, n1, n2) in enumerate(moc_cu):
        chong = round(min(b, n2) - max(a, n1), 3)
        if chong <= 0.001 or n2 - n1 <= 0.001:
            continue
        k = khoi[i]
        tho = float(k.get("tho") or 0.0)
        them = float(k.get("tho_them") or 0.0)
        san = -max(tho - SAN_LANG_S, 0.0)          # im lặng hiệu dụng >= sàn
        moi = max(san, round(them - chong, 3))
        if abs(moi - them) > 0.001:
            k["tho_them"] = moi
            k["nguoi_sua"] = True
            tho_co = round(tho_co + (them - moi), 3)
    # bỏ miếng, miếng cạnh nở phủ TRỌN chỗ trống (vẫn trên trục CŨ)
    hinh.pop(idx)
    ke = hinh[idx - 1] if idx > 0 else hinh[0]
    if idx > 0:
        ke["dur"] = round(ke["dur"] + h["dur"], 3)
    else:
        ke["t0"] = h["t0"]
        ke["dur"] = round(ke["dur"] + h["dur"], 3)
    ke["nguoi_sua"] = True
    if tho_co > 0:
        # trục voice vừa ngắn lại -> hình co theo + cụm sau trượt (một chỗ duy
        # nhất làm việc này: dong_bo_sau_tho, đã nghiệm thu vòng ±thở 08/09)
        dong_bo_sau_tho(hd, moc_cu)
    khit_mep(hd)
    gan_lai_khoi_goc(hd)
    return True, tho_co


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
    gan_lai_khoi_goc(hd)
    return True


def gan_lai_khoi_goc(hd: dict) -> None:
    """Suy khoi_goc theo VỊ TRÍ THẬT (miếng thuộc ô nào thì mang khối đó).

    Bắt buộc sau mọi thao tác chẻ/bỏ/kéo mép: nếu khoi_goc lệch, +/-1s thở sẽ
    co nhầm miếng của khối khác (bắt thật trên LI100 08/09 — miếng 10 mang
    khoi_goc=11 trong khi nằm ở ô khối 9)."""
    moc = moc_timeline(hd.get("khoi") or [])
    if not moc:
        return
    for h in dam_bao(hd):
        giua = h["t0"] + h["dur"] / 2
        i = 0
        for j, (n0, _n1, n2) in enumerate(moc):
            if n0 - 0.01 <= giua < n2 + 0.01:
                i = j
                break
            if giua >= n2:
                i = j
        h["khoi_goc"] = i


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
