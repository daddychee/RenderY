# Chép NGUYÊN từ Padoma GEN VIDEO app/kiem_drama.py (27/10/2026), giao ước khuôn với skill /bien-kich-grok trong skill-bien-kich/. Không sửa tay: luật treatment riêng viết ở drama.py.
"""Kiểm và tách kịch bản drama thoại hai tầng cảnh và clip (Spec 44 B, C, D, E). **Khuôn là giao ước giữa hai repo** như `kiem_kich_ban.py`:
đổi khuôn thì đổi cả skill `/bien-kich-drama`, file này và web.

Hàm thuần, không import gì của app (bản chép `skill bien kich/cong-cu/kiem_drama.py` chạy độc lập ở máy editor), hằng số viết trong file.
- `tach(van_ban)`: phim (tên, loại, mức Seedance, thể loại), phần `# Phần n · tên · 10 phút`, cảnh `## Cxxx · nơi · lúc · Nxx` (+ `Có mặt:`),
  clip `### Pxxx · tên` với Máy, Khung, Hình, Thoại, Lời nghĩ, mục `## Ghi chú nối`, khối `## Thiết kế trận T1: tên · cỡ chính · P045–P052`
  (Spec 71 L.3, phan["tran"]: khoảng P, mã ở cột Cảnh của bảng); mọi mục kèm số dòng (từ 1).
- Chế độ Grok (Spec 69 E): văn bản có clip `Máy: Grok 10s|15s` thì mọi clip phải Grok (Veo, Seedance là LỖI), không mức Seedance
  (phim["grok"] True, phim["seedance"] None), trần từ như Seedance; NHẮC cú máy Grok không làm được, hành động nặng, `Khung:` quá 4 người,
  ô trong nhà, đám đông có mặt rõ.
- `kiem(van_ban, ca_phim=True, muc=None)`: trả (lỗi, nhắc, phim). Lỗi và nhắc là cặp (số dòng hoặc None, câu có mã clip). ca_phim=False: file một phần
  không có phần đầu phim, bỏ luật dòng `Loại phim:`. Mức chọn máy (mục C): dòng `Seedance: 100%|75%|30s` ở phần đầu phim; không có thì `muc`
  (dòng lệnh lấy từ `phan-01.md` cùng thư mục), không có nữa thì 100. phim["seedance"] là mức đã dùng (`30s` là số 30).
  Clip `Seedance 30s` (Spec 71 B, chạy Mango): mọi shot ghi `shot n (X giây)`, cộng đủ 30; thiếu là LỖI. Phần đa số clip 30 giây tính 2 clip/phút.
  Mức `30s` (Spec 71 K.1, mọi clip Seedance 30s): clip Veo là LỖI, clip Seedance 10 đến 25 giây là NHẮC (giữ được khi có lý do).
- `tom_tat(phan, muc)`: một dòng mức Seedance (phần Grok: Grok, gói ngày), số clip theo loại, tổng giây, % Seedance (theo giây), clip/phút, số lời nghĩ, ước credit gen.
- `gop(van_ban_cac_phan)`: phần đầu phim của file đầu + từ `# Phần` trở đi của mọi file, ra `kich-ban.md`.

Chạy: py -3 kiem_drama.py <file phần> [...]                  kiểm từng file, in tóm tắt, LỖI, NHẮC; thoát 1 khi có lỗi
            (file không có phần đầu phim lấy mức Seedance ở phan-01.md cùng thư mục)
      py -3 kiem_drama.py gop <thư mục | file phần ...> [-o kich-ban.md]
            gộp `phan-*.md` (theo số) rồi kiểm bản gộp (mã clip liền qua các phần); có lỗi thì không ghi. Mặc định ghi kich-ban.md cạnh các phần."""
import re
import sys
from pathlib import Path

LOAI = "drama_thoai"
GIAY_VEO = 8
GIAY_SEEDANCE = (10, 15, 20, 25, 30)          # Spec 29 H: 20 đến 30 chỉ khi editor yêu cầu; file chép sang skill nên không import gia_credit
TRAN_TU_VEO = 18
TU_MOT_GIAY_SEEDANCE = 3                      # thoại + lời nghĩ clip Seedance (chốt 01/10, gv3): 15 giây 45 từ, 10 giây 30 từ
MUC_30 = 30                                   # dòng `Seedance: 30s` (Spec 71 K.1): mọi clip Seedance 30s chạy Mango, chỉ nhân viên
MUC_SEEDANCE = (100, 75, MUC_30)              # dòng `Seedance:` (chốt 01/10 sau gv3); thiếu dòng tính 100
MUC_MAC_DINH = 100
GROK = "grok"
GIAY_GROK = (10, 15)                          # Spec 69 D.1: Grok tối đa 15 giây, kịch bản chỉ 10s, 15s
TRAN_KHUNG_GROK = 4                           # Spec 69 D.3: mỗi clip nhiều nhất 4 người rõ mặt (anh/chị nâng từ 3, 25/10)
TRAN_KHUNG_VEO = 1                            # mức 75%: Veo chỉ clip 1 người, 1 câu, không lời nghĩ
TRAN_LUOT_VEO = 1
SEEDANCE_THAP, SEEDANCE_CAO = 0.65, 0.85      # mức 75%: tỉ lệ giây Seedance của phần
# Spec 71 B: clip Seedance 30 giây (Mango, chỉ nhân viên). Giá một clip chép từ gia_credit (test so), file chạy độc lập
GIAY_30, CLIP_PHUT_30, CREDIT_CLIP_30 = 30, 2, 325
CLIP_PHUT = {100: 5, 75: 5.5, MUC_30: CLIP_PHUT_30}
LECH_CLIP_PHUT = 0.20
RE_SHOT_GIAY = re.compile(r"\bshot\s+(\d+)\s*\((\d+(?:[.,]\d+)?)\s*(?:giây|s)\)", re.I)
RE_SHOT_SO = re.compile(r"\bshot\s+(\d+)\b", re.I)
TRAN_LOI_NGHI = 0.10                          # tỉ lệ clip có lời nghĩ trong phần (02/10: lời nghĩ là công cụ chính, từ 0,05)
# Ước credit (Spec 44 D): Seedance theo giây (10, 15 giây chạy 2.0 fast, Spec 59; giá 18/10 10 giây 55, 15 giây 75), gen dư khoảng 10%
# vì editor cắt đầu đuôi; Veo theo clip; máy nghe 1 credit mỗi clip có tiếng nói
CREDIT_GIAY_SEEDANCE, DU_SEEDANCE, CREDIT_CLIP_VEO, CREDIT_NGHE = 5.5, 1.10, 6, 1
# NHẮC 1, chữ ở `Hình:` hay cách nói clip Veo. Cú máy chậm (đẩy, lùi, lia chậm) không nhắc nên không có "đẩy".
TU_HANH_DONG = ("đánh", "đấm", "tát", "chạy", "lao tới", "lao vào", "ngã", "té", "ôm chầm", "đập", "xô", "vật lộn", "giằng co", "nhảy",
                "đuổi", "máy cầm tay", "rung", "máy chạy theo")
TU_CAM_XUC = ("khóc", "nức nở", "nghẹn", "run", "sững", "giận", "gào", "hét", "rưng rưng", "nước mắt", "ngấn nước", "sụp đổ", "tuyệt vọng")
TU_DO_VAT = ("cầm", "đưa", "mở", "đeo", "giơ", "nắm", "rút ra", "lấy ra", "đặt xuống")
# NHẮC 5 (chốt 03/10, phim 191: 46/52 clip "Máy đứng yên"): clip Seedance có ít nhất một cú máy hay góc có ý đồ ở `Hình:` (drama-thoai.md mục 8).
# Qua vai, cận, trung là cỡ cảnh thường, không tính.
TU_THU_PHAP = ("đẩy vào", "lùi ra", "máy lùi", "lia", "trượt ngang", "máy ngước", "máy cúi", "chuyển nét", "vòng quanh", "nửa vòng", "vòng từ",
               "bám lưng", "bám theo", "góc thấp", "góc cao", "từ trên xuống", "sát đất", "khung trong khung", "qua khung cửa", "qua cửa kính",
               "qua ô cửa", "trong gương", "qua gương", "dolly zoom", "zoom nhanh", "máy nâng", "nâng lên", "máy hạ", "máy cầm tay", "rõ nét tiền cảnh",
               "tiền cảnh mờ", "ngược sáng", "nghiêng khung", "góc nhìn của")
RE_TP = re.compile(r"\bTP\d{1,3}\b")
# NHẮC Grok (Spec 69 E), tìm ở `Hình:` (chữ thường). Chạm nhẹ một động tác (tát, nắm cổ tay, giật tờ giấy) không nhắc.
RE_CU_GROK = re.compile(r"dolly zoom|\b360\b|vòng tròn quanh|vòng trọn|trượt ngang theo")
RE_NANG_GROK = re.compile(r"\b(xô(?! (nước|đá|rác|đựng|nhựa))|đẩy ngã|lôi đi|lôi xềnh xệch|lôi ra khỏi|lôi tuột|kéo lê|kéo lôi|vật lộn|giằng co|đấm|đá vào|đá văng|đá mạnh|đá tung|"
                          r"đạp(?! xe)|ngã xuống|ngã nhào|ngã vật|ngã ra|té ngã|té xuống|nhảy ra khỏi|"
                          r"đánh(?! (rơi|dấu|thức|răng|máy|mắt|son|phấn|giá|cược|bạc|vần|lừa|thuế|đổ)))\b")
RE_DONG_NGUOI = re.compile(r"\b(đám đông|khách khứa|khách mời|quan khách|người xem|người qua đường|đông người|hàng người|cả sảnh|cả phòng)\b")
RE_DONG_MO = re.compile(r"\b(mờ|lưng|bóng)\b")
RE_DONG_CAN = re.compile(r"\b(cận|đặc tả|mặt|gương mặt)\s+(từng\s+|của\s+)?(đám đông|khách|người xem|người qua đường|quan khách)")
RE_O = re.compile(r"\b(chiếc ô|cây ô|cái ô|ô đen|ô màu|che ô|cầm ô|mở ô|gập ô|bật ô|tán ô|cụp ô|cây dù|chiếc dù|cái dù|cầm dù|che dù|mở dù|"
                  r"gập dù|umbrella)\b")
RE_O_GAP = re.compile(r"\b(gấp|gập|cụp|xếp|đã đóng)\b")       # ô gập, xếp ở cửa là đúng cách (grok-drama.md mục 3)
RE_TRONG_NHA = re.compile(r"\b(trong nhà|bên trong|sảnh|phòng|bếp|hành lang|quán|nhà hàng|cửa hàng|siêu thị|thang máy|bệnh viện|nhà thờ|lobby|"
                          r"room|kitchen|hall|office|restaurant|diner|café|cafe|store|shop|apartment|hospital|church|inside|interior)\b")
TRAN_TINH = 0.30                              # tỉ lệ clip Seedance không thủ pháp tối đa trong phần

RE_PHAN = re.compile(r"^# Phần\s+(\d+)\b(.*)$")
RE_CANH = re.compile(r"^## (C\d{2,4})\b(.*)$")
RE_CLIP = re.compile(r"^### (P\d{2,4})\b(.*)$")
# Spec 71 L.3: khối trận đúng định dạng phim thường (skill bien kich/kien-thuc/tran-danh.md), ngay trên `## Cxxx` của cảnh mở trận
RE_TRAN = re.compile(r"^## Thiết kế trận\s+T(\d+)\s*:\s*(.*?)\s*·\s*cỡ\s+(xô xát|chính|cuối)\s*·\s*(P\d{2,4})\s*[–-]\s*(P\d{2,4})\s*$", re.I)
DAU_TRAN = "## thiết kế trận"
SHOT_TRAN_30 = (10, 16)                       # clip Seedance 30s trong khối trận: số shot (Spec 71 J.3, như dem_phan_canh)
RE_MAY = re.compile(r"^(veo|seedance|grok)\s+(\d+)\s*s$", re.I)
RE_PHUT = re.compile(r"(\d+(?:[.,]\d+)?)\s*phút")
RE_NHIP = re.compile(r"\bN\d{2,3}\b")
RE_LUOT = re.compile(r"^(.+?)\s*(?:\(([^)]*)\))?\s*:\s*(.*)$")
RE_NGOAC = re.compile(r"\"([^\"]*)\"|“([^”]*)”")
RE_TU = re.compile(r"\w[\w'’-]*")
RE_SEEDANCE = re.compile(r"^(\d+)\s*(%|s)$", re.I)
NHAC_VEO = [(re.compile(r"\b(" + "|".join(re.escape(t) for t in tu) + r")\b", re.I), loai)
            for tu, loai in ((TU_HANH_DONG, "hành động lớn"), (TU_CAM_XUC, "cảm xúc rõ"), (TU_DO_VAT, "đồ vật trong tay"))]
KHOA_CLIP = {"máy": "may", "khung": "khung", "hình": "hinh", "thoại": "thoai", "lời nghĩ": "loi_nghi"}

Loi = tuple[int | None, str]


def _ten(s: str) -> list[str]:
    return [t.strip() for t in s.split(",") if t.strip()]


def _cham(s: str) -> list[str]:
    """Phần sau mã trong tiêu đề `Cxxx · a · b` thành [a, b]."""
    return [x.strip() for x in s.split("·") if x.strip()]


def so_tu(cau: str) -> int:
    """Số từ trong ngoặc kép (thẳng hay cong) của một dòng thoại."""
    return sum(len(RE_TU.findall(a or b)) for a, b in RE_NGOAC.findall(cau))


def luot(noi_dung: str, dong: int) -> dict:
    """`Tên (cách nói): "câu"` → {ten, cach, cau, dong}. Lời nghĩ `Tên: "câu"` dùng chung."""
    m = RE_LUOT.match(noi_dung)
    if not m or '"' in m.group(1) or "“" in m.group(1):
        return {"ten": "", "cach": "", "cau": noi_dung, "dong": dong}
    return {"ten": m.group(1).strip(), "cach": (m.group(2) or "").strip(), "cau": m.group(3).strip(), "dong": dong}


def _clip(ma: str, tieu_de: str, dong: int) -> dict:
    return {"ma": ma, "ten": " · ".join(_cham(tieu_de)), "dong": dong, "may": None, "may_goc": None, "giay": None, "may_dong": None,
            "khung": None, "khung_dong": None, "hinh": None, "thoai": [], "loi_nghi": None}


def _dong_clip(c: dict, khoa: str, gia_tri: str, i: int) -> None:
    if khoa == "may":
        c["may_goc"], c["may_dong"] = gia_tri, i
        m = RE_MAY.match(gia_tri)
        if m:
            c["may"], c["giay"] = m.group(1).lower(), int(m.group(2))
    elif khoa == "khung":
        c["khung"], c["khung_dong"] = _ten(gia_tri), i
    elif khoa == "hinh":
        c["hinh"] = gia_tri
    elif khoa == "thoai":
        c["thoai"].append(luot(gia_tri, i))
    else:
        c["loi_nghi"] = luot(gia_tri, i)


def tach(van_ban: str) -> dict:
    """Tách khuôn mục B. Clip nằm ngoài cảnh (trước `## C…` đầu phần, hay sau `## Ghi chú nối`) vào phan["clip_ngoai"]."""
    phim = {"ten": "", "loai": None, "loai_dong": None, "seedance_goc": None, "seedance_dong": None, "the_loai": "", "dau": [], "phan": [],
            "tran_ngoai": []}
    phan = canh = clip = tran = None
    muc = None                                  # None | "canh" | "ghi_chu" | "tran"
    for i, d in enumerate(van_ban.splitlines(), 1):
        s = d.strip()
        if m := RE_PHAN.match(s):
            t = _cham(m.group(2))
            phut = RE_PHUT.search(m.group(2))
            phut = float(phut.group(1).replace(",", ".")) if phut else None      # "8,5 phút"
            phan = {"so": int(m.group(1)), "ten": t[0] if t and not RE_PHUT.fullmatch(t[0]) else "",
                    "phut": int(phut) if phut is not None and phut.is_integer() else phut,
                    "dong": i, "canh": [], "clip_ngoai": [], "ghi_chu_noi": "", "tran": []}
            phim["phan"].append(phan)
            canh = clip = muc = None
            continue
        if phan is None:
            if s.lower().startswith(DAU_TRAN):
                phim["tran_ngoai"].append(i)
            phim["dau"].append(d)
            if s.startswith("# ") and not phim["ten"]:
                phim["ten"] = s[2:].strip()
            elif s.lower().startswith("loại phim:"):
                phim["loai"], phim["loai_dong"] = s.split(":", 1)[1].strip(), i
            elif s.lower().startswith("seedance:"):
                phim["seedance_goc"], phim["seedance_dong"] = s.split(":", 1)[1].strip(), i
            elif s.lower().startswith("thể loại:"):
                phim["the_loai"] = _cham(s.split(":", 1)[1])[0] if _cham(s.split(":", 1)[1]) else ""
            continue
        if m := RE_CANH.match(s):
            t = _cham(m.group(2))
            nhip = [x for x in t if RE_NHIP.fullmatch(x)]
            t = [x for x in t if not RE_NHIP.fullmatch(x)]
            canh = {"ma": m.group(1), "noi": t[0] if t else "", "luc": t[1] if len(t) > 1 else "", "nhip": nhip[0] if nhip else "",
                    "dong": i, "co_mat": None, "clip": []}
            phan["canh"].append(canh)
            clip, muc = None, "canh"
            continue
        if s.lower().startswith(DAU_TRAN):
            m = RE_TRAN.match(s)
            tran = {"so": f"T{m.group(1)}", "tu": m.group(4), "toi": m.group(5), "dong": i, "hang": []} if m else {"sai": True, "dong": i, "hang": []}
            phan["tran"].append(tran)
            canh = clip = None
            muc = "tran"
            continue
        if s.startswith("## "):
            canh = clip = None
            muc = "ghi_chu" if s[3:].strip().lower().startswith("ghi chú nối") else None
            continue
        if m := RE_CLIP.match(s):
            clip = _clip(m.group(1), m.group(2), i)
            (canh["clip"] if canh is not None else phan["clip_ngoai"]).append(clip)
            continue
        if muc == "ghi_chu":
            phan["ghi_chu_noi"] = (phan["ghi_chu_noi"] + "\n" + s).strip()
            continue
        if muc == "tran":
            if s.startswith("|") and (m := re.match(r"(P\d{2,4})\b", s.strip("|").split("|")[0].strip())):
                tran["hang"].append(m.group(1))       # cảnh 30s hai dòng `P045 0–17`, `P045 17–30`
            continue
        if not s:
            continue
        khoa, _, gia_tri = s.partition(":")
        khoa = KHOA_CLIP.get(khoa.strip().lower())
        if clip is not None and khoa:
            _dong_clip(clip, khoa, gia_tri.strip(), i)
        elif clip is not None and clip["hinh"] is not None and not clip["thoai"] and not clip["loi_nghi"]:
            clip["hinh"] += " " + s                 # Hình viết tràn nhiều dòng
        elif canh is not None and clip is None and s.lower().startswith("có mặt:"):
            canh["co_mat"] = _ten(s.split(":", 1)[1])
    phim["grok"] = any(c["may"] == GROK for p in phim["phan"] for c in p["clip_ngoai"] + cac_clip(p))     # Spec 69 E
    phim["seedance"] = None if phim["grok"] else muc_seedance(phim["seedance_goc"])
    return phim


def muc_seedance(goc: str | None) -> int | None:
    """Giá trị dòng `Seedance:` → 100, 75 (`100%`, `75%`) hay 30 (`30s`); không có dòng hay sai dạng thì None (kiem tính 100, sai dạng là LỖI)."""
    m = RE_SEEDANCE.match((goc or "").strip())
    if not m:
        return None
    so, s = int(m.group(1)), m.group(2).lower() == "s"
    return so if so in MUC_SEEDANCE and s == (so == MUC_30) else None


def ten_muc(muc: int | None) -> str:
    """Mức Seedance để in: `30s` hay `100%`, `75%`."""
    return f"{muc}s" if muc == MUC_30 else f"{muc}%"


def cac_clip(phan: dict) -> list[dict]:
    return [c for canh in phan["canh"] for c in canh["clip"]]


def so_do(phan: dict) -> dict:
    """Số đo một phần: số clip (cả theo loại máy, giây), tổng giây, % giây Seedance, clip/phút, số clip có lời nghĩ, ước credit gen một lần."""
    clip = cac_clip(phan)
    giay = {"veo": 0, "seedance": 0, GROK: 0}
    loai: dict[tuple[str, int], int] = {}
    for c in clip:
        if c["may"] in giay and c["giay"]:
            giay[c["may"]] += c["giay"]
            loai[(c["may"], c["giay"])] = loai.get((c["may"], c["giay"]), 0) + 1
    tong = sum(giay.values())
    n30 = loai.get(("seedance", GIAY_30), 0)          # Mango tính theo clip, không gen dư
    credit = ((giay["seedance"] - n30 * GIAY_30) * DU_SEEDANCE * CREDIT_GIAY_SEEDANCE + n30 * CREDIT_CLIP_30
              + loai.get(("veo", GIAY_VEO), 0) * CREDIT_CLIP_VEO + sum(1 for c in clip if c["thoai"] or c["loi_nghi"]) * CREDIT_NGHE)
    sd = [c for c in clip if c["may"] in ("seedance", GROK)]      # clip nhiều shot (Grok viết như Seedance, Spec 69 D.4)
    return {"clip": len(clip), "loai": loai, "giay": tong, "ty_seedance": giay["seedance"] / tong if tong else 0.0,
            "clip_phut": len(clip) / phan["phut"] if phan["phut"] else None, "loi_nghi": sum(1 for c in clip if c["loi_nghi"]),
            "credit": round(credit), "seedance": len(sd), "tinh": [c["ma"] for c in sd if not co_thu_phap(c["hinh"])]}


def co_thu_phap(hinh: str | None) -> bool:
    """`Hình:` có cú máy hay góc có ý đồ (TU_THU_PHAP) hay mã TP của kho thủ pháp."""
    h = (hinh or "").lower()
    return any(t in h for t in TU_THU_PHAP) or bool(RE_TP.search(hinh or ""))


def tom_tat(phan: dict, muc: int | None = MUC_MAC_DINH) -> str:
    s = so_do(phan)
    cp = f"{s['clip_phut']:.1f}".replace(".", ",") if s["clip_phut"] is not None else "?"
    if any(k[0] == GROK for k in s["loai"]):        # Spec 69: Grok gói ngày, không ước credit
        loai = ", ".join(f"{s['loai'][k]} Grok {k[1]}s" for k in ((GROK, 10), (GROK, 15)) if s["loai"].get(k))
        return (f"Phần {phan['so']} · Grok: {s['clip']} clip ({loai}) · {s['giay']} giây · {cp} clip/phút · {s['loi_nghi']} lời nghĩ · "
                f"{s['seedance'] - len(s['tinh'])}/{s['seedance']} clip có thủ pháp · Grok gói ngày, 0đ")
    loai = ", ".join(f"{s['loai'][k]} {k[0].capitalize()} {k[1]}s" for k in (("seedance", 10), ("seedance", 15), ("seedance", GIAY_30), ("veo", GIAY_VEO))
                     if s["loai"].get(k))
    credit = f"{s['credit']:,}".replace(",", ".")
    return (f"Phần {phan['so']} · mức Seedance {ten_muc(muc)}: {s['clip']} clip" + (f" ({loai})" if loai else "") + f" · {s['giay']} giây · "
            f"Seedance {round(s['ty_seedance'] * 100)}% giây · {cp} clip/phút · {s['loi_nghi']} lời nghĩ · "
            f"{s['seedance'] - len(s['tinh'])}/{s['seedance']} clip Seedance có thủ pháp · ước {credit} credit")


def _kiem_clip(c: dict, co_mat: list[str] | None, loi: list[Loi], nhac: list[Loi], muc: int, grok: bool = False) -> None:
    ma = c["ma"]
    dang = "Grok 10s, Grok 15s" if grok else "Veo 8s, Seedance 10s, Seedance 15s"
    if c["may_goc"] is None:
        loi.append((c["dong"], f"{ma}: thiếu dòng Máy: ({dang})"))
    elif c["may"] is None:
        loi.append((c["may_dong"], f"{ma}: dòng Máy: '{c['may_goc']}' sai dạng ({dang})"))
    elif grok and c["may"] != GROK:
        loi.append((c["may_dong"], f"{ma}: kịch bản Grok (có clip Máy: Grok) mà clip là {c['may_goc']}: mọi clip Grok 10s hay Grok 15s"))
    elif c["may"] == GROK and c["giay"] not in GIAY_GROK:
        loi.append((c["may_dong"], f"{ma}: clip Grok {c['giay']} giây, chỉ Grok 10s hay Grok 15s"))
    elif c["may"] == "veo" and c["giay"] != GIAY_VEO:
        loi.append((c["may_dong"], f"{ma}: clip Veo {c['giay']} giây, Veo luôn {GIAY_VEO} giây"))
    elif c["may"] == "seedance" and c["giay"] not in GIAY_SEEDANCE:
        loi.append((c["may_dong"], f"{ma}: clip Seedance {c['giay']} giây, chỉ {'/'.join(map(str, GIAY_SEEDANCE))} giây"))
    if c["khung"] is None:
        loi.append((c["dong"], f"{ma}: thiếu dòng Khung:"))
    if c["hinh"] is None:
        loi.append((c["dong"], f"{ma}: thiếu dòng Hình:"))
    khung = [t.lower() for t in c["khung"] or []]
    if co_mat is not None:
        cm = {t.lower() for t in co_mat}
        for t in c["khung"] or []:
            if t.lower() not in cm:
                loi.append((c["khung_dong"], f"{ma}: '{t}' ở Khung: không có ở Có mặt: của cảnh"))
    for lt in c["thoai"]:
        if not lt["ten"]:
            loi.append((lt["dong"], f'{ma}: dòng Thoại: sai dạng (Tên (cách nói): "câu tiếng Anh")'))
    if (c["may"] == "seedance" and c["giay"] in GIAY_SEEDANCE) or (c["may"] == GROK and c["giay"] in GIAY_GROK):
        tu = sum(so_tu(lt["cau"]) for lt in c["thoai"]) + (so_tu(c["loi_nghi"]["cau"]) if c["loi_nghi"] else 0)
        if tu > TU_MOT_GIAY_SEEDANCE * c["giay"]:
            dong = c["thoai"][0]["dong"] if c["thoai"] else c["loi_nghi"]["dong"]
            loi.append((dong, f"{ma}: clip {'Grok' if c['may'] == GROK else 'Seedance'} {c['giay']} giây {tu} từ thoại và lời nghĩ, tối đa {TU_MOT_GIAY_SEEDANCE * c['giay']}: "
                              f"bớt chữ hay chia clip"))
    if c["may"] == "seedance" and c["giay"] == GIAY_30:
        _kiem_30(c, loi)
    elif c["may"] == "seedance" and muc == MUC_30 and c["giay"] in GIAY_SEEDANCE:
        nhac.append((c["may_dong"], f"{ma}: kịch bản mức Seedance 30s mà clip là {c['may_goc']}: gộp thành Seedance 30s, hay giữ khi có lý do (ghi báo cáo)"))
    if grok:
        _nhac_grok(c, nhac)
    if grok or c["may"] != "veo":
        return
    if muc == 100:
        loi.append((c["may_dong"], f"{ma}: kịch bản mức Seedance 100% mà clip là Veo: đổi sang Seedance 10s hay 15s (hoặc ghi Seedance: 75%)"))
        return
    if muc == MUC_30:
        loi.append((c["may_dong"], f"{ma}: kịch bản mức Seedance 30s mà clip là Veo: gộp vào clip Seedance 30s"))
        return
    tu = sum(so_tu(lt["cau"]) for lt in c["thoai"])
    if tu > TRAN_TU_VEO:
        loi.append((c["thoai"][0]["dong"], f"{ma}: clip Veo {tu} từ thoại, tối đa {TRAN_TU_VEO}: chia clip hay sang Seedance"))
    if len(khung) > TRAN_KHUNG_VEO:
        loi.append((c["khung_dong"], f"{ma}: clip Veo {len(khung)} người ở Khung:, Veo chỉ {TRAN_KHUNG_VEO} người: sang Seedance"))
    if len(c["thoai"]) > TRAN_LUOT_VEO:
        loi.append((c["thoai"][0]["dong"], f"{ma}: clip Veo {len(c['thoai'])} lượt thoại, Veo chỉ {TRAN_LUOT_VEO} lượt: sang Seedance"))
    if c["loi_nghi"]:
        loi.append((c["loi_nghi"]["dong"], f"{ma}: clip Veo có Lời nghĩ:, lời nghĩ luôn Seedance"))
    for lt in c["thoai"]:
        if lt["ten"] and c["khung"] is not None and lt["ten"].lower() not in khung:
            loi.append((lt["dong"], f"{ma}: người nói '{lt['ten']}' không có tên ở Khung: (Veo chỉ cho người trong khung nói)"))
    chu = " ".join([c["hinh"] or ""] + [lt["cach"] for lt in c["thoai"]])
    for re_, loai in NHAC_VEO:
        if m := re_.search(chu.replace("máy cầm tay", "") if loai == "đồ vật trong tay" else chu):
            nhac.append((c["dong"], f"{ma}: clip Veo có '{m.group(1)}' ({loai}), nên sang Seedance"))
            break


def _g(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def shot_giay(hinh: str | None) -> tuple[list[tuple[int, float]], list[int]]:
    """`Hình:` → ([(số shot, giây)], số các shot nhắc tới mà chưa ghi `(X giây)`)."""
    shot = [(int(n), float(g.replace(",", "."))) for n, g in RE_SHOT_GIAY.findall(hinh or "")]
    return shot, sorted({int(n) for n in RE_SHOT_SO.findall(hinh or "")} - {s for s, _ in shot})


def _kiem_30(c: dict, loi: list[Loi]) -> None:
    """Spec 71 B: clip Seedance 30 giây: mọi shot ghi số giây, cộng đủ 30 (drama-thoai.md mục 3). Chỗ cắt, số shot do người viết chọn."""
    ma = c["ma"]
    shot, thieu = shot_giay(c["hinh"])
    if thieu or not shot:
        loi.append((c["dong"], f"{ma}: clip Seedance 30 giây, " + (f"shot {', '.join(map(str, thieu))} chưa ghi số giây" if thieu else
                                                                  "Hình: chưa chia shot có số giây") + ": ghi `shot n (X giây)` ở mọi shot"))
        return
    tong = sum(g for _, g in shot)
    if abs(tong - GIAY_30) > 0.01:
        loi.append((c["dong"], f"{ma}: clip Seedance 30 giây, giây các shot cộng {_g(tong)}, phải đủ 30: sửa giây từng shot"))


def _nhac_grok(c: dict, nhac: list[Loi]) -> None:
    """Spec 69 E: NHẮC điều Grok hay làm hỏng (không chặn; người viết sửa hay giữ có lý do). Nơi của cảnh ở c["noi"]."""
    ma, h = c["ma"], (c["hinh"] or "").lower()
    if m := RE_CU_GROK.search(h):
        nhac.append((c["dong"], f"{ma}: Grok không làm được cú '{m.group(0)}' (dolly zoom, vòng 360, trượt ngang theo người chạy): đổi cú khác"))
    if m := RE_NANG_GROK.search(h):
        nhac.append((c["dong"], f"{ma}: '{m.group(1)}' là hành động nặng Grok hay làm hỏng: chạm nhẹ một động tác, hay để việc xảy ra giữa hai clip"))
    if len(c["khung"] or []) > TRAN_KHUNG_GROK:
        nhac.append((c["khung_dong"], f"{ma}: {len(c['khung'])} người ở Khung:, Grok tối đa {TRAN_KHUNG_GROK} người rõ mặt: chia clip theo người nói"))
    if (m := RE_O.search(h)) and not RE_O_GAP.search(h) and RE_TRONG_NHA.search(h + " " + (c.get("noi") or "").lower()):
        nhac.append((c["dong"], f"{ma}: '{m.group(1)}' trong cảnh trong nhà: Grok hay mở ô, vẽ hai ô; để ô gập ở cửa"))
    if (m := RE_DONG_NGUOI.search(h)) and (not RE_DONG_MO.search(h) or RE_DONG_CAN.search(h)):
        nhac.append((c["dong"], f"{ma}: '{m.group(1)}' có mặt rõ: Grok vẽ người đám đông giống nhau, thừa tay; chỉ thấy lưng hay mờ phía sau, không cận"))


def _kiem_phan(phan: dict, loi: list[Loi], nhac: list[Loi], muc: int, grok: bool = False) -> None:
    for c in phan["clip_ngoai"]:
        loi.append((c["dong"], f"{c['ma']}: clip nằm ngoài cảnh (phải ở dưới một dòng ## Cxxx)"))
    for canh in phan["canh"]:
        if canh["co_mat"] is None:
            loi.append((canh["dong"], f"{canh['ma']}: cảnh thiếu dòng Có mặt:"))
        for c in canh["clip"]:
            _kiem_clip(c | {"noi": canh["noi"]}, canh["co_mat"], loi, nhac, muc, grok)
    s = so_do(phan)
    if not s["clip"]:
        return
    nhan = f"Phần {phan['so']}"
    if muc == 75 and not SEEDANCE_THAP <= s["ty_seedance"] <= SEEDANCE_CAO:
        nhac.append((phan["dong"], f"{nhan}: Seedance {round(s['ty_seedance'] * 100)}% giây, mức 75% nên 65–85%"))
    ba_muoi = s["loai"].get(("seedance", GIAY_30), 0) * 2 > s["clip"]       # phần đa số clip 30 giây
    cp = CLIP_PHUT_30 if ba_muoi else CLIP_PHUT[muc]
    if s["clip_phut"] is None:
        nhac.append((phan["dong"], f"{nhan}: tiêu đề phần không ghi số phút, chưa đo clip/phút"))
    elif abs(s["clip_phut"] - cp) > cp * LECH_CLIP_PHUT:
        nhan_muc = "Grok" if grok else "clip 30 giây" if ba_muoi else f"mức {ten_muc(muc)}"
        nhac.append((phan["dong"], f"{nhan}: {s['clip_phut']:.1f} clip/phút, {nhan_muc} nên khoảng {cp} (lệch quá 20%)".replace(".", ",")))
    if s["loi_nghi"] / s["clip"] > TRAN_LOI_NGHI:
        nhac.append((phan["dong"], f"{nhan}: {s['loi_nghi']} lời nghĩ trên {s['clip']} clip, nên tối đa khoảng {round(TRAN_LOI_NGHI * 100)}%"))
    if s["seedance"] and len(s["tinh"]) / s["seedance"] > TRAN_TINH:
        may, muc_tp = ("Grok", "grok-drama.md mục 8") if grok else ("Seedance", "drama-thoai.md mục 8")
        nhac.append((phan["dong"], f"{nhan}: {len(s['tinh'])}/{s['seedance']} clip {may} không có cú máy hay góc có ý đồ, nên tối đa "
                                   f"{round(TRAN_TINH * 100)}% ({muc_tp}): {', '.join(s['tinh'][:12])}" + (" …" if len(s["tinh"]) > 12 else "")))


def kiem(van_ban: str, ca_phim: bool = True, muc: int | None = None) -> tuple[list[Loi], list[Loi], dict]:
    """Kiểm luật mục E. ca_phim: văn bản có phần đầu phim (bản gộp, web dán) thì bắt dòng `Loại phim: drama_thoai`.
    muc: mức Seedance khi văn bản không có dòng `Seedance:` (file phần, lấy từ phan-01.md)."""
    phim = tach(van_ban)
    loi: list[Loi] = []
    nhac: list[Loi] = []
    if ca_phim and phim["loai"] != LOAI:
        loi.append((phim["loai_dong"], f"thiếu dòng 'Loại phim: {LOAI}' ở phần đầu phim" if phim["loai"] is None
                    else f"Loại phim: '{phim['loai']}', phải là {LOAI}"))
    if phim["seedance_goc"] is not None and phim["seedance"] is None and not phim["grok"]:
        loi.append((phim["seedance_dong"], f"Seedance: '{phim['seedance_goc']}', chỉ 100%, 75% hoặc 30s"))
    if not phim["grok"]:        # Spec 69 D.1: kịch bản Grok không có mức Seedance
        phim["seedance"] = phim["seedance"] or (muc if muc in MUC_SEEDANCE else MUC_MAC_DINH)
    if not phim["phan"]:
        loi.append((None, "không có phần nào (dòng # Phần n · tên · 10 phút)"))
    truoc, ma_truoc, da_co = None, "", set()
    for phan in phim["phan"]:
        _kiem_phan(phan, loi, nhac, phim["seedance"] or MUC_MAC_DINH, phim["grok"])
        for c in sorted(phan["clip_ngoai"] + cac_clip(phan), key=lambda c: c["dong"]):
            so = int(c["ma"][1:])
            if so in da_co:
                loi.append((c["dong"], f"{c['ma']}: mã clip trùng"))
            elif truoc is not None and so != truoc + 1:
                loi.append((c["dong"], f"{c['ma']}: mã clip không liền (clip trước {ma_truoc})"))
            da_co.add(so)
            truoc, ma_truoc = so, c["ma"]
    _kiem_tran(phim, loi, nhac)
    loi.sort(key=lambda x: x[0] or 0)
    nhac.sort(key=lambda x: x[0] or 0)
    return loi, nhac, phim


def _kiem_tran(phim: dict, loi: list[Loi], nhac: list[Loi]) -> None:
    """Spec 71 L.3: khối trận trong một phần, dòng đầu đúng dạng, khoảng Pa–Pb là mã clip có thật (a ≤ b), bảng khối mỗi clip trong khoảng
    ít nhất một dòng, không dòng clip ngoài khoảng. NHẮC: clip Veo trong khoảng (web không bật cờ hành động cho Veo), clip Seedance 30s
    trong khoảng có số shot ngoài 10–16."""
    for d in phim["tran_ngoai"]:
        loi.append((d, "khối trận nằm ở phần đầu phim: đặt trong phần chứa trận, ngay trên dòng ## Cxxx của cảnh mở trận"))
    clip = {int(c["ma"][1:]): c for p in phim["phan"] for c in p["clip_ngoai"] + cac_clip(p)}
    for p in phim["phan"]:
        for t in p["tran"]:
            if t.get("sai"):
                loi.append((t["dong"], "khối trận sai dạng (cần '## Thiết kế trận T1: tên · cỡ xô xát|chính|cuối · P045–P052')"))
                continue
            a, b, nhan = int(t["tu"][1:]), int(t["toi"][1:]), f"khối trận {t['so']} {t['tu']}–{t['toi']}"
            if a not in clip or b not in clip or a > b:
                loi.append((t["dong"], f"{nhan}: khoảng không khớp mã clip có trong kịch bản" + (" (mã đầu lớn hơn mã cuối)" if a > b else "")))
                continue
            trong = [clip[k] for k in sorted(clip) if a <= k <= b]
            hang = {int(x[1:]) for x in t["hang"]}
            thieu = [c["ma"] for c in trong if int(c["ma"][1:]) not in hang]
            thua = sorted({x for x in t["hang"] if not a <= int(x[1:]) <= b})
            if thieu or thua:
                loi.append((t["dong"], f"{nhan}: bảng khối không khớp clip trong khoảng" + (f"; thiếu dòng {', '.join(thieu)}" if thieu else "")
                            + (f"; thừa dòng {', '.join(thua)}" if thua else "")))
            for c in trong:
                if c["may"] == "veo":
                    nhac.append((c["may_dong"], f"{c['ma']}: clip Veo trong {nhan}: Veo không quay đánh nhau, web không bật cảnh hành động; "
                                                "đổi sang Seedance hay giữ khi clip không đánh"))
                elif c["may"] == "seedance" and c["giay"] == GIAY_30 and (n := len(shot_giay(c["hinh"])[0])) \
                        and not SHOT_TRAN_30[0] <= n <= SHOT_TRAN_30[1]:
                    nhac.append((c["dong"], f"{c['ma']}: clip trận 30 giây {n} shot, nên {SHOT_TRAN_30[0]}–{SHOT_TRAN_30[1]} (mỗi shot 2–3 giây)"))


def gop(cac_phan: list[str]) -> str:
    """Gộp các file phần (đã theo thứ tự): phần đầu phim lấy của file đầu, mỗi file lấy từ dòng `# Phần` đầu tiên."""
    ra = []
    for i, vb in enumerate(cac_phan):
        dong = vb.splitlines()
        dau = next((k for k, d in enumerate(dong) if RE_PHAN.match(d.strip())), len(dong))
        khuc = dong if i == 0 else dong[dau:]
        ra.append("\n".join(khuc).strip("\n"))
    return "\n\n".join(ra) + "\n"


def _in(van_ban: str, ca_phim: bool, nhan: str = "", muc: int | None = None) -> int:
    loi, nhac, phim = kiem(van_ban, ca_phim, muc)
    for p in phim["phan"]:
        print(nhan + tom_tat(p, phim["seedance"]))
    for dong, cau in loi:
        print("LỖI:", nhan + (f"dòng {dong} · " if dong else "") + cau)
    for dong, cau in nhac:
        print("NHẮC:", nhan + (f"dòng {dong} · " if dong else "") + cau)
    return 1 if loi else 0


def _so_file(f: Path) -> int:
    return int(re.sub(r"\D", "", f.stem) or 0)


def main(arg: list[str]) -> int:
    if not arg:
        print(__doc__)
        return 2
    if arg[0] == "gop":
        ra = None
        if "-o" in arg:
            k = arg.index("-o")
            ra, arg = Path(arg[k + 1]), arg[:k] + arg[k + 2:]
        vao = [Path(a) for a in arg[1:]]
        tep = sorted(vao[0].glob("phan-*.md"), key=_so_file) if len(vao) == 1 and vao[0].is_dir() else vao
        if not tep:
            print("LỖI: không thấy file phần (phan-*.md)")
            return 1
        ban_gop = gop([f.read_text(encoding="utf-8") for f in tep])
        if _in(ban_gop, True):
            print("Có lỗi: chưa ghi kich-ban.md.")
            return 1
        ra = ra or tep[0].parent / "kich-ban.md"
        ra.write_text(ban_gop, encoding="utf-8", newline="\n")
        print(f"Đã gộp {len(tep)} phần vào {ra}")
        return 0
    kq = 0
    for a in arg:
        f = Path(a)
        if not f.exists():
            print(f"LỖI: không thấy {f}")
            kq = 1
            continue
        vb = f.read_text(encoding="utf-8")
        dau = next((d.strip() for d in vb.splitlines() if d.startswith("# ")), "")
        ca_phim = not RE_PHAN.match(dau)
        muc = None
        if not ca_phim and (p1 := f.parent / "phan-01.md").exists() and p1.resolve() != f.resolve():
            muc = tach(p1.read_text(encoding="utf-8"))["seedance"]
        kq |= _in(vb, ca_phim, f"{f.name}: " if len(arg) > 1 else "", muc)
    return kq


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
