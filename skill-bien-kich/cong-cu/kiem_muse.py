# File chép từ app/kiem_muse.py của repo GEN VIDEO bằng kiem-chung/dong_bo_skill_phim.py. Không sửa tay.
"""Kiểm và tách kịch bản phim Muse hai tầng cảnh và clip (Spec 63 B, C). **Khuôn là giao ước giữa hai repo** như `kiem_drama.py`:
đổi khuôn thì đổi cả skill `/bien-kich-muse`, file này và web.

Hàm thuần, không import gì của app (bản chép `skill bien kich/cong-cu/kiem_muse.py` chạy độc lập ở máy editor), hằng số viết trong file.
- `tach(van_ban)`: phim (tên, loại, thể loại), phần `# Phần n · tên · 10 phút`, cảnh `## Cxxx · nơi · lúc · Nxx` (+ `Có mặt:`),
  clip `### Pxxx · tên` với Khung, Hình, Thoại, Lời nghĩ, Lời ngoài hình (và Máy để báo lỗi), mục `## Ghi chú nối`; mọi mục kèm số dòng (từ 1).
  Mỗi clip có `may` "muse", `giay` 10; `thoai` là danh sách lượt (kiểm xong còn tối đa 1), `loi_nghi`, `loi_ngoai` lượt đầu hay None
  (`cac_loi_nghi`, `cac_loi_ngoai`: mọi dòng, để kiểm). Qua kiem thì mỗi clip tối đa một trong ba.
- `kiem(van_ban, ca_phim=True)`: trả (lỗi, nhắc, phim). Lỗi và nhắc là cặp (số dòng hoặc None, câu có mã clip). ca_phim=False: file một phần
  không có phần đầu phim, bỏ luật dòng `Loại phim:`.
- `tom_tat(phan)`: một dòng số clip, có thoại, có lời nghĩ, có lời ngoài hình, không người, tổng giây, clip/phút, ước chi
  (khung đầu + ai33 đọc lời nghĩ, lời ngoài hình).
- `gop(van_ban_cac_phan)`: phần đầu phim của file đầu + từ `# Phần` trở đi của mọi file, ra `kich-ban.md`.

Chạy: py -3 kiem_muse.py <file phần> [...]                  kiểm từng file, in tóm tắt, LỖI, NHẮC; thoát 1 khi có lỗi
      py -3 kiem_muse.py gop <thư mục | file phần ...> [-o kich-ban.md]
            gộp `phan-*.md` (theo số) rồi kiểm bản gộp (mã clip liền qua các phần); có lỗi thì không ghi. Mặc định ghi kich-ban.md cạnh các phần."""
import re
import sys
from pathlib import Path

LOAI = "phim_muse"
GIAY_CLIP = 10                                # mọi clip là Muse 10 giây (Spec 63 B)
TU_THOAI_MIN, TU_THOAI_MAX, TU_NGHI_MAX, TU_NGOAI_MAX = 3, 25, 25, 25
KHUNG_THOAI_MAX, KHUNG_MAX = 2, 4
CLIP_PHUT, LECH_CLIP_PHUT = 6, 0.20
TRAN_LOI_NGHI = 0.10
# Ước chi (Spec 63 A, E.7 chốt 19/10 tối, đồng): khung đầu GPT Image 2 4 credit × 13đ mỗi clip có người; thoại giữ giọng Muse (0đ);
# ai33 đọc mỗi câu lời nghĩ, lời ngoài hình
DONG_KHUNG_DAU, DONG_DOC_AI33 = 52, 8
# NHẮC 1: chữ bộ lọc Muse hay chặn (spec/47-muse/lich-su-bi-chan.md). Cụm vô hại chứa chữ đó bỏ trước khi dò.
TU_BO_LOC = ("đánh", "đấm", "máu", "vết thương", "cắn", "xác", "đẻ", "xô ngã", "ngã", "chết")
CUM_VO_HAI = ("chính xác", "xác nhận", "xác định", "xác suất", "đánh rơi", "đánh thức", "đánh răng", "đánh dấu", "đánh giá", "đánh máy",
              "cắn môi", "ngã tư", "ngã ba", "ngã rẽ")
# NHẮC 2: cú máy Muse không làm được
TU_GOC_KHO = ("góc rất thấp", "góc thấp", "góc rất cao", "góc cao", "từ trên xuống", "sát đất", "chuyển nét", "toàn thân quay lưng",
              "quay lưng về máy", "quay lưng lại máy")
NHOM_CU_MAY = (("đẩy vào", "đẩy tới"), ("lùi ra", "máy lùi"), ("lia",), ("trượt ngang", "máy trượt"), ("nâng lên", "máy nâng"),
               ("hạ xuống", "máy hạ"), ("vòng quanh", "nửa vòng"), ("bám theo",))    # mỗi nhóm một cú; hai nhóm trở lên là cú nhiều bước
TU_MAT_MAT = ("cúi xuống", "cúi đầu", "cúi mặt", "quay đi", "quay mặt đi", "quay lưng")
TU_DUNG_YEN = ("đứng yên", "máy tĩnh", "máy yên")
# NHẮC 4: sinh vật to hơn ngựa
RE_KHONG_LO = re.compile(r"khổng lồ|cao như (?:nhà|cây|tòa)|to như (?:nhà|voi|xe)|to hơn (?:ngựa|voi|nhà)|gấp \w+ lần người", re.I)

RE_PHAN = re.compile(r"^# Phần\s+(\d+)\b(.*)$")
RE_CANH = re.compile(r"^## (C\d{2,4})\b(.*)$")
RE_CLIP = re.compile(r"^### (P\d{2,4})\b(.*)$")
RE_PHUT = re.compile(r"(\d+)\s*phút")
RE_NHIP = re.compile(r"\bN\d{2,3}\b")
RE_LUOT = re.compile(r"^(.+?)\s*(?:\(([^)]*)\))?\s*:\s*(.*)$")
RE_NGOAC = re.compile(r"\"([^\"]*)\"|“([^”]*)”")
RE_TU = re.compile(r"\w[\w'’-]*")
RE_HAI_NGUOI = re.compile(r",|&|\bvà\b|\band\b", re.I)
KHOA_CLIP = {"máy": "may", "khung": "khung", "hình": "hinh", "thoại": "thoai", "lời nghĩ": "loi_nghi", "lời ngoài hình": "loi_ngoai"}
TEN_LOI = {"thoai": "Thoại", "loi_nghi": "Lời nghĩ", "loi_ngoai": "Lời ngoài hình"}

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
    """`Tên (cách nói): "câu"` → {ten, cach, cau, dong}. Lời nghĩ `Tên (cách nghĩ): "câu"` dùng chung."""
    m = RE_LUOT.match(noi_dung)
    if not m or '"' in m.group(1) or "“" in m.group(1):
        return {"ten": "", "cach": "", "cau": noi_dung, "dong": dong}
    return {"ten": m.group(1).strip(), "cach": (m.group(2) or "").strip(), "cau": m.group(3).strip(), "dong": dong}


def _hai_nguoi(lt: dict) -> bool:
    """Một dòng có hai người: tên ghép (`A, B`, `A và B`) hay sau câu trong ngoặc còn lượt `Tên: "…"` nữa."""
    return bool(lt["ten"] and RE_HAI_NGUOI.search(lt["ten"])) or ":" in RE_NGOAC.sub("", lt["cau"])


def _clip(ma: str, tieu_de: str, dong: int) -> dict:
    return {"ma": ma, "ten": " · ".join(_cham(tieu_de)), "dong": dong, "may": "muse", "giay": GIAY_CLIP, "may_dong": None,
            "khung": None, "khung_dong": None, "hinh": None, "thoai": [], "loi_nghi": None, "cac_loi_nghi": [],
            "loi_ngoai": None, "cac_loi_ngoai": []}


def tach(van_ban: str) -> dict:
    """Tách khuôn mục B. Clip nằm ngoài cảnh (trước `## C…` đầu phần, hay sau `## Ghi chú nối`) vào phan["clip_ngoai"]."""
    phim = {"ten": "", "loai": None, "loai_dong": None, "the_loai": "", "dau": [], "phan": []}
    phan = canh = clip = None
    muc = None                                  # None | "canh" | "ghi_chu"
    for i, d in enumerate(van_ban.splitlines(), 1):
        s = d.strip()
        if m := RE_PHAN.match(s):
            t = _cham(m.group(2))
            phut = RE_PHUT.search(m.group(2))
            phan = {"so": int(m.group(1)), "ten": t[0] if t and not RE_PHUT.fullmatch(t[0]) else "", "phut": int(phut.group(1)) if phut else None,
                    "dong": i, "canh": [], "clip_ngoai": [], "ghi_chu_noi": ""}
            phim["phan"].append(phan)
            canh = clip = muc = None
            continue
        if phan is None:
            phim["dau"].append(d)
            if s.startswith("# ") and not phim["ten"]:
                phim["ten"] = s[2:].strip()
            elif s.lower().startswith("loại phim:"):
                phim["loai"], phim["loai_dong"] = s.split(":", 1)[1].strip(), i
            elif s.lower().startswith("thể loại:"):
                phim["the_loai"] = (_cham(s.split(":", 1)[1]) or [""])[0]
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
        if not s:
            continue
        khoa, _, gia_tri = s.partition(":")
        khoa, gia_tri = KHOA_CLIP.get(khoa.strip().lower()), gia_tri.strip()
        if clip is not None and khoa == "may":
            clip["may_dong"] = i
        elif clip is not None and khoa == "khung":
            clip["khung"], clip["khung_dong"] = _ten(gia_tri), i
        elif clip is not None and khoa == "hinh":
            clip["hinh"] = gia_tri
        elif clip is not None and khoa == "thoai":
            clip["thoai"].append(luot(gia_tri, i))
        elif clip is not None and khoa in ("loi_nghi", "loi_ngoai"):
            clip["cac_" + khoa].append(luot(gia_tri, i))
            clip[khoa] = clip["cac_" + khoa][0]
        elif clip is not None and clip["hinh"] is not None and not _cac_loi(clip):
            clip["hinh"] += " " + s                 # Hình viết tràn nhiều dòng
        elif canh is not None and clip is None and s.lower().startswith("có mặt:"):
            canh["co_mat"] = _ten(s.split(":", 1)[1])
    return phim


def _cac_loi(c: dict) -> list[tuple[str, dict]]:
    """Mọi dòng lời của clip theo thứ tự dòng: (khóa thoai | loi_nghi | loi_ngoai, lượt)."""
    return sorted([("thoai", x) for x in c["thoai"]] + [("loi_nghi", x) for x in c["cac_loi_nghi"]]
                  + [("loi_ngoai", x) for x in c["cac_loi_ngoai"]], key=lambda kx: kx[1]["dong"])


def cac_clip(phan: dict) -> list[dict]:
    return [c for canh in phan["canh"] for c in canh["clip"]]


def so_do(phan: dict) -> dict:
    """Số đo một phần: số clip, có thoại, có lời nghĩ, không người, tổng giây, clip/phút, ước chi (đồng)."""
    clip = cac_clip(phan)
    thoai = sum(1 for c in clip if c["thoai"])
    nghi = sum(1 for c in clip if c["loi_nghi"])
    ngoai = sum(1 for c in clip if c["loi_ngoai"])
    khong_nguoi = sum(1 for c in clip if not c["khung"])
    chi = (len(clip) - khong_nguoi) * DONG_KHUNG_DAU + (nghi + ngoai) * DONG_DOC_AI33
    return {"clip": len(clip), "thoai": thoai, "loi_nghi": nghi, "loi_ngoai": ngoai, "khong_nguoi": khong_nguoi, "giay": len(clip) * GIAY_CLIP,
            "clip_phut": len(clip) / phan["phut"] if phan["phut"] else None, "chi": chi}


def tom_tat(phan: dict) -> str:
    s = so_do(phan)
    cp = f"{s['clip_phut']:.1f}".replace(".", ",") if s["clip_phut"] is not None else "?"
    return (f"Phần {phan['so']} · Muse: {s['clip']} clip · {s['thoai']} có thoại · {s['loi_nghi']} lời nghĩ · {s['loi_ngoai']} lời ngoài hình · "
            f"{s['khong_nguoi']} không người · "
            f"{s['giay']} giây · {cp} clip/phút · ước " + f"{s['chi']:,}".replace(",", ".") + "đ (khung đầu + ai33 đọc lời nghĩ, lời ngoài hình)")


def _co(chu: str, tu: tuple[str, ...]) -> list[str]:
    return [t for t in tu if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", chu)]


def _kiem_clip(c: dict, co_mat: list[str] | None, loi: list[Loi], nhac: list[Loi]) -> None:
    ma = c["ma"]
    if c["may_dong"] is not None:
        loi.append((c["may_dong"], f"{ma}: có dòng Máy:, phim Muse không ghi máy (mọi clip Muse {GIAY_CLIP} giây)"))
    if c["khung"] is None:
        loi.append((c["dong"], f"{ma}: thiếu dòng Khung: (để trống khi clip không người)"))
    if c["hinh"] is None:
        loi.append((c["dong"], f"{ma}: thiếu dòng Hình:"))
    khung = [t.lower() for t in c["khung"] or []]
    if co_mat is not None:
        cm = {t.lower() for t in co_mat}
        for t in c["khung"] or []:
            if t.lower() not in cm:
                loi.append((c["khung_dong"], f"{ma}: '{t}' ở Khung: không có ở Có mặt: của cảnh"))
    if len(cl := _cac_loi(c)) > 1:
        loai = ", ".join(f"{TEN_LOI[k]}:" for k in dict.fromkeys(k for k, _ in cl))
        loi.append((cl[1][1]["dong"], f"{ma}: {len(cl)} dòng lời ({loai}), mỗi clip tối đa một dòng Thoại:, Lời nghĩ: hay Lời ngoài hình: "
                                      f"(Muse chỉ một lượt nói): chia mỗi lượt một clip"))
    tran = {"thoai": TU_THOAI_MAX, "loi_nghi": TU_NGHI_MAX, "loi_ngoai": TU_NGOAI_MAX}
    for k, lt in cl:
        nhan = TEN_LOI[k]
        if not lt["ten"]:
            loi.append((lt["dong"], f'{ma}: dòng {nhan}: sai dạng (Tên (cách): "câu tiếng Anh")'))
            continue
        if _hai_nguoi(lt):
            loi.append((lt["dong"], f"{ma}: dòng {nhan}: có hai người, mỗi dòng một người và mỗi clip một người nói"))
            continue
        tu = so_tu(lt["cau"])
        if tu > tran[k]:
            loi.append((lt["dong"], f"{ma}: {nhan.lower()} {tu} từ, tối đa {tran[k]}: bớt chữ hay chia clip"))
        elif nhan == "Thoại" and tu < TU_THOAI_MIN:
            loi.append((lt["dong"], f"{ma}: thoại {tu} từ, tối thiểu {TU_THOAI_MIN} (câu 1–2 tiếng Muse làm mất): thêm chữ hay bỏ thoại"))
        if k == "loi_ngoai":
            if lt["ten"].lower() in khung:
                loi.append((lt["dong"], f"{ma}: '{lt['ten']}' có ở Khung: mà dòng là Lời ngoài hình: (thấy mặt thì viết Thoại:)"))
        elif c["khung"] is not None and lt["ten"].lower() not in khung:
            ai = "người nói" if nhan == "Thoại" else "người nghĩ"
            loi.append((lt["dong"], f"{ma}: {ai} '{lt['ten']}' không có tên ở Khung: (Muse cho người trong khung nói thay)"))
    if c["thoai"] and len(khung) > KHUNG_THOAI_MAX:
        loi.append((c["khung_dong"], f"{ma}: clip có thoại mà {len(khung)} người ở Khung:, tối đa {KHUNG_THOAI_MAX}"))
    elif len(khung) > KHUNG_MAX:
        loi.append((c["khung_dong"], f"{ma}: {len(khung)} người ở Khung:, tối đa {KHUNG_MAX}"))
    _nhac_clip(c, khung, nhac)


def _nhac_clip(c: dict, khung: list[str], nhac: list[Loi]) -> None:
    ma, hinh = c["ma"], (c["hinh"] or "").lower()
    chu = " ".join([hinh] + [lt["cach"].lower() for _, lt in _cac_loi(c)])
    for cum in CUM_VO_HAI:
        chu = chu.replace(cum, " ")
    if tu := _co(chu, TU_BO_LOC):
        nhac.append((c["dong"], f"{ma}: chữ bộ lọc Muse hay chặn: {', '.join(tu)} (chặn một lần mất tài khoản cả ngày): tả nhẹ hơn"))
    if tu := _co(hinh, TU_GOC_KHO):
        nhac.append((c["dong"], f"{ma}: Muse khó làm '{tu[0]}': dùng cận vai, trung cảnh ngang mắt"))
    elif len(cu := [n[0] for n in NHOM_CU_MAY if _co(hinh, n)]) > 1:
        nhac.append((c["dong"], f"{ma}: cú máy nhiều bước ({', '.join(cu)}), Muse chỉ làm một cú: giữ một"))
    if c["thoai"] and (tu := _co(hinh, TU_MAT_MAT)):
        nhac.append((c["dong"], f"{ma}: clip có thoại mà '{tu[0]}' (mất mặt, Muse cho người khác nói): mặt nhìn về máy"))
    if len(khung) >= 2 and not _co(hinh, TU_DUNG_YEN):
        nhac.append((c["dong"], f"{ma}: hai người trong Khung: mà máy không đứng yên (đẩy vào làm rơi người thứ hai): ghi 'Máy đứng yên'"))
    if m := RE_KHONG_LO.search(hinh):
        nhac.append((c["dong"], f"{ma}: '{m.group(0)}': Muse làm sinh vật tới cỡ ngựa, to hơn dễ hỏng"))


def _kiem_phan(phan: dict, loi: list[Loi], nhac: list[Loi]) -> None:
    for c in phan["clip_ngoai"]:
        loi.append((c["dong"], f"{c['ma']}: clip nằm ngoài cảnh (phải ở dưới một dòng ## Cxxx)"))
    for canh in phan["canh"]:
        if canh["co_mat"] is None:
            loi.append((canh["dong"], f"{canh['ma']}: cảnh thiếu dòng Có mặt:"))
        for c in canh["clip"]:
            _kiem_clip(c, canh["co_mat"], loi, nhac)
    s = so_do(phan)
    if not s["clip"]:
        return
    nhan = f"Phần {phan['so']}"
    if s["clip_phut"] is None:
        nhac.append((phan["dong"], f"{nhan}: tiêu đề phần không ghi số phút, chưa đo clip/phút"))
    elif abs(s["clip_phut"] - CLIP_PHUT) > CLIP_PHUT * LECH_CLIP_PHUT:
        nhac.append((phan["dong"], f"{nhan}: {s['clip_phut']:.1f} clip/phút, nên khoảng {CLIP_PHUT} (lệch quá 20%)".replace(".", ",")))
    if s["loi_nghi"] / s["clip"] > TRAN_LOI_NGHI:
        nhac.append((phan["dong"], f"{nhan}: {s['loi_nghi']} lời nghĩ trên {s['clip']} clip, nên tối đa khoảng {round(TRAN_LOI_NGHI * 100)}%"))


def kiem(van_ban: str, ca_phim: bool = True) -> tuple[list[Loi], list[Loi], dict]:
    """Kiểm luật mục C. ca_phim: văn bản có phần đầu phim (bản gộp, web dán) thì bắt dòng `Loại phim: phim_muse`."""
    phim = tach(van_ban)
    loi: list[Loi] = []
    nhac: list[Loi] = []
    if ca_phim and phim["loai"] != LOAI:
        loi.append((phim["loai_dong"], f"thiếu dòng 'Loại phim: {LOAI}' ở phần đầu phim" if phim["loai"] is None
                    else f"Loại phim: '{phim['loai']}', phải là {LOAI}"))
    if not phim["phan"]:
        loi.append((None, "không có phần nào (dòng # Phần n · tên · 10 phút)"))
    truoc, ma_truoc, da_co = None, "", set()
    for phan in phim["phan"]:
        _kiem_phan(phan, loi, nhac)
        for c in sorted(phan["clip_ngoai"] + cac_clip(phan), key=lambda c: c["dong"]):
            so = int(c["ma"][1:])
            if so in da_co:
                loi.append((c["dong"], f"{c['ma']}: mã clip trùng"))
            elif truoc is not None and so != truoc + 1:
                loi.append((c["dong"], f"{c['ma']}: mã clip không liền (clip trước {ma_truoc})"))
            da_co.add(so)
            truoc, ma_truoc = so, c["ma"]
    loi.sort(key=lambda x: x[0] or 0)
    nhac.sort(key=lambda x: x[0] or 0)
    return loi, nhac, phim


def gop(cac_phan: list[str]) -> str:
    """Gộp các file phần (đã theo thứ tự): phần đầu phim lấy của file đầu, mỗi file lấy từ dòng `# Phần` đầu tiên."""
    ra = []
    for i, vb in enumerate(cac_phan):
        dong = vb.splitlines()
        dau = next((k for k, d in enumerate(dong) if RE_PHAN.match(d.strip())), len(dong))
        ra.append("\n".join(dong if i == 0 else dong[dau:]).strip("\n"))
    return "\n\n".join(ra) + "\n"


def _in(van_ban: str, ca_phim: bool, nhan: str = "") -> int:
    loi, nhac, phim = kiem(van_ban, ca_phim)
    for p in phim["phan"]:
        print(nhan + tom_tat(p))
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
        kq |= _in(vb, not RE_PHAN.match(dau), f"{f.name}: " if len(arg) > 1 else "")
    return kq


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
