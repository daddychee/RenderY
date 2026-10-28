"""Dàn ý drama thoại (khuôn ở kinh-nghiem/nang-cap-drama/00-ke-hoach.md mục 7) và phần đầu phim web đọc (của thư mục skill, không phải bản chép;
thay dau_drama.py). `kiem_drama.py` là bản chép của web (không sửa tay) nên các luật này ở đây.

Chạy: py -3 cong-cu/dan_y_drama.py kiem <thư mục kich-ban | 00-dan-y.md>      kiểm dàn ý
      py -3 cong-cu/dan_y_drama.py doc <thư mục kich-ban | 00-dan-y.md> <n>   in phần dàn ý trợ lý viết phần n cần (đích dưới 7.000 token)
      py -3 cong-cu/dan_y_drama.py dau <thư mục kich-ban>                     chép phần đầu phim từ 00-dan-y.md vào phan-01.md
                                                                              (thay mọi dòng trước `# Phần`), rồi kiểm phan-01.md như `phan`
      py -3 cong-cu/dan_y_drama.py phan <phan-NN.md | kich-ban.md> [...]      kiểm file phần hay bản gộp
      py -3 cong-cu/dan_y_drama.py danh-ma <thư mục kich-ban>                 đánh lại mã clip P, cảnh C liền cả phim sau khi chèn (mã tạm
                                                                              `P045-b`, `C009-b`), sửa mọi chỗ trỏ mã trong các file phần
Phần đầu phim = bốn dòng đầu dàn ý (tới trước mục `##` đầu tiên) + `## Nhân vật và bối cảnh` + `## Cụm cố định` (web đọc ở các dòng trước
`# Phần` đầu tiên: bảng nhân vật vào prompt khung cảnh, cột `Cụm…` của dòng `NV` là `nhan_dang`). Không chép Tựa và thumbnail, Gieo và gặt.
kiem · LỖI: thiếu mục, cột của khuôn; `Trả tựa ở` trỏ mốc có phút đầu quá 4; hai mốc liền cách quá 5 phút; phần ngoài 8–12 phút, phần không có
  dòng `dẫn sai` gặt trong phần (phim dưới 10 phút miễn hai luật này); mốc không thuộc phần nào; Gieo và gặt: loại lạ, Gieo ở không bắt đầu bằng
  mã mốc, Gặt ở sai dạng, gặt trước gieo, mã mốc không có ở Bảng mốc, `vết` thiếu trái/phải (hay cả người, hai bên…) hay thiếu `tới Nxx`; LỖI Cụm cố định (như `phan`).
  NHẮC: dàn ý không kể Cụm cố định quá khoảng 12.000 token; Việc quá 2 câu; cụm có chữ già, xấu da.
phan · LỖI: thiếu mục Nhân vật, Cụm cố định; thiếu dòng NV, dòng NV thiếu cụm hay thiếu tuổi; tên ở `Có mặt:`/`Khung:` không có ở Cụm cố định;
  dòng G có gieo hay gặt trong mốc của phần mà thiếu ở dòng `- Gieo, gặt:` của `## Ghi chú nối`, hay trỏ clip không có trong phần; mã G lạ.
  NHẮC: cụm có chữ già, xấu da; phần đầu file khác dàn ý; `Hình:` nhắc vết (vết, bầm, sẹo, băng, máu, rách, sưng) mà câu đó không có trái, phải;
  % giây có lời của phần từ 20 clip (ước: từ / 2,5 từ mỗi giây, không quá giây clip) ngoài 60–80%; cảnh từ 3 clip không clip nào thưa lời (tối đa 1,5 từ
  mỗi giây: nhịp diễn); clip đầu cảnh không có shot định vị (rộng, toàn).
Thoát 1 khi có LỖI."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kiem_drama import RE_PHAN, _so_file, cac_clip, so_tu, tach  # noqa: E402

MUC_NV, MUC_CUM = "Nhân vật và bối cảnh", "Cụm cố định"
MUC_KHUON = ("Tựa và thumbnail", "Logline", "Bí mật khán giả biết trước", MUC_NV, MUC_CUM, "Kẻ ác từng vòng", "Mở phim", "Bảng mốc",
             "Gieo và gặt", "Phần")
COT = {"Bảng mốc": ("Mốc", "Phút", "Ngày", "Đoạn khung", "Việc", "Ức trả ở", "Mã kho"),
       "Gieo và gặt": ("Mã", "Loại", "Điều", "Gieo ở", "Gặt ở"), "Phần": ("Phần", "Tên", "Mốc", "Phút")}
LOAI_GIEO = ("lật", "dẫn sai", "phi lý", "vết", "biết", "vật")
LOAI_MANG_SANG = ("vết", "biết")             # còn hiệu lực sang phần sau: `doc` in cả khi gieo, gặt ở phần khác
PHUT_TRA_TUA, CACH_MOC, PHAN_PHUT, PHIM_NGAN = 4, 5, (8, 12), 10
TRAN_TOKEN_DAN_Y, TRAN_TOKEN_DOC, TRAN_CAU_VIEC = 12000, 7000, 2
KY_TU_MOT_TOKEN = 1.7                        # như muc_luc.py (không import được: muc_luc chạy ngay khi nạp)
COT_NV_DOC = ("Tên", "Vai", "Giọng")         # `doc` bỏ cột ngoại hình
RE_TUOI = re.compile(r"\b\d{1,2}\b|\b(teen\w*|twenties|thirties|forties|fifties|sixties|seventies|eighties|nineties)\b", re.I)
RE_XAU = re.compile(r"eye ?bags|under-eye|dark circles|wrinkle|uneven skin|blemish|acne|pockmark|sagging|greying|graying", re.I)
RE_MOC = re.compile(r"\bN(\d{2,3})\b")
RE_KHOANG = re.compile(r"^(\d+(?:[,.]\d+)?)\s*(?:[–-]\s*(\d+(?:[,.]\d+)?))?$")
RE_DO_DAI = re.compile(r"Độ dài:\s*(\d+(?:[,.]\d+)?)\s*phút", re.I)
RE_TRA_TUA = re.compile(r"^Trả tựa ở:\s*(.*)$", re.I)
RE_NGOAC = re.compile(r"\"[^\"]*\"|“[^”]*”")
RE_CAU = re.compile(r"[.!?…]+(?=\s|$)")
RE_VET = re.compile(r"\b(vết|bầm|sẹo|máu|rách|sưng|(?<!đóng )băng(?! (?:ghế|camera|ghi|hình|video|qua|chuyền|tần|nhóm|đảng)\b))\b", re.I)
RE_KHONG_VET = re.compile(r"máu (?:rút|dồn|nóng|lạnh|mặt)|vết (?:gót|giày|bẩn|cà phê|nước|son|bánh|chân|xe)|"
                          r"(?:túi|áo|giấy|vải|váy|quần|thư|bao|rèm)(?: \w+)? rách", re.I)   # bỏ trước khi tìm vết (đo ở the-shop-girl phần 1)
# Bên của vết; trạng thái không có bên (ướt cả người, hai lòng bàn tay) cũng qua.
RE_BEN = re.compile(r"\b(trái|phải|cả người|toàn thân|khắp người|cả hai|hai bên|hai (?:tay|chân|lòng bàn tay|mu bàn tay|mắt|má|vai|gối))\b",
                    re.I)
RE_GIEO_GAT = re.compile(r"^-?\s*Gieo,\s*gặt\s*:(.*)$", re.I)
RE_GP = re.compile(r"\b([GP]\d{2,4})\b")

# Khán giả hiểu, diễn viên có đất diễn (CLAUDE.md; khung drama-da-den mục 5; chốt 02/10)
TU_MOI_GIAY_NOI = 2.5                        # tốc độ nói trong cảnh (khung mục 5: 2–2,6 từ/giây)
TY_LOI = (0.60, 0.80)                        # % giây đang nói mỗi phần; phim cũ đo 28–45% (rời rạc), đối thủ gần 100%
TU_NHIP_DIEN, CLIP_CANH_NHIP = 1.5, 3        # clip tối đa 1,5 từ/giây là nhịp diễn; cảnh từ 3 clip phải có một
CLIP_DO_TY_LOI = 20                          # đo % lời khi phần có từ 20 clip
RE_DINH_VI = re.compile(r"rộng|toàn cảnh|\btoàn\b|định vị", re.I)

Loi = tuple[int | None, str]


def _dong(vb: str) -> list[str]:
    return vb.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _so(s: str) -> float:
    return float(s.replace(",", "."))


def _tok(dong: list[str]) -> int:
    return round(sum(map(len, dong)) / KY_TU_MOT_TOKEN)


def muc(dong: list[str], ten: str) -> list[str]:
    """Các dòng của mục `## <ten>` kể cả tiêu đề, tới mục `## ` kế tiếp (bỏ dòng trống cuối)."""
    return khuc(dong, ten)[1]


def khuc(dong: list[str], ten: str) -> tuple[int, list[str]]:
    """(chỉ số dòng tiêu đề, các dòng) của mục `## <ten>`; không có thì (-1, [])."""
    ra, trong, dau = [], False, -1
    for i, d in enumerate(dong):
        if d.startswith("## "):
            trong = d[3:].strip().lower().startswith(ten.lower()) and dau < 0
            if trong:
                dau = i
        if trong:
            ra.append(d)
    while ra and not ra[-1].strip():
        ra.pop()
    return dau, ra


def phan_dau(dong: list[str]) -> list[str]:
    """Phần đầu phim từ dàn ý hay từ file (các dòng trước `# Phần` đầu tiên)."""
    k = next((i for i, d in enumerate(dong) if RE_PHAN.match(d.strip())), len(dong))
    dong = dong[:k]
    bon = []
    for d in dong:
        if d.startswith("## "):
            break
        bon.append(d)
    while bon and not bon[-1].strip():
        bon.pop()
    ra = bon
    for ten in (MUC_NV, MUC_CUM):
        m = muc(dong, ten)
        if m:
            ra += [""] + m
    return ra


def _o(d: str) -> list[str]:
    return [x.strip() for x in d.strip().strip("|").split("|")]


def bang(dong: list[str], goc: int = 0) -> tuple[list[str], list[dict]]:
    """Bảng markdown đầu tiên trong `dong` (dừng ở dòng `### ` hay dòng không phải bảng sau bảng): (cột, hàng).
    Mỗi hàng: {"o": {cột: ô}, "dong": số dòng từ 1 (goc là chỉ số của dong[0]), "goc": dòng gốc}."""
    cot, hang = None, []
    for i, d in enumerate(dong):
        if not d.strip().startswith("|"):
            if cot is not None and (d.startswith("#") or d.strip()):
                break
            continue
        o = _o(d)
        if cot is None:
            cot = o
        elif not all(set(x) <= set("-: ") for x in o):
            hang.append({"o": dict(zip(cot, o)), "dong": goc + i + 1, "goc": d})
    return cot or [], hang


def _cot(h: dict, ten: str) -> str:
    return next((v for k, v in h["o"].items() if k.startswith(ten)), "")


def cum(dau: list[str]) -> list[dict]:
    """Hàng NV của bảng Cụm cố định: {ma, ten (tên trơn), cum, dong}."""
    ra = []
    for h in bang(muc(dau, MUC_CUM))[1]:
        if _cot(h, "Mã").startswith("NV"):
            ra.append({"ma": _cot(h, "Mã"), "ten": re.split(r"\s*[(,]", _cot(h, "Tên"))[0].strip(), "cum": _cot(h, "Cụm"), "dong": h["dong"]})
    return ra


def kiem_cum(dau: list[str], vb: str | None) -> tuple[list[str], list[str]]:
    """Luật phần đầu phim: mục Nhân vật, bảng Cụm cố định; vb (văn bản có `# Phần`) thì thêm tên ở Có mặt/Khung phải có cụm."""
    loi, nhac = [], []
    if not muc(dau, MUC_NV):
        loi.append(f"phần đầu thiếu mục '## {MUC_NV}' (bảng Nhân vật, Nơi của dàn ý)")
    hang = cum(dau)
    if not hang:
        loi.append(f"phần đầu thiếu bảng '## {MUC_CUM}' có dòng NV (Mã | Tên | Cụm tiếng Anh): web sẽ tự đoán ngoại hình")
    ten_ma = {}
    for h in hang:
        if not h["cum"]:
            loi.append(f"{h['ma']} {h['ten']}: thiếu cụm tiếng Anh")
            continue
        if not RE_TUOI.search(h["cum"]):
            loi.append(f"{h['ma']} {h['ten']}: cụm thiếu tuổi (about 24, early thirties…)")
        if x := RE_XAU.search(h["cum"]):
            nhac.append(f"{h['ma']} {h['ten']}: cụm có '{x.group(0)}'; cặp chính drama da đen phải trẻ, đẹp (kẻ ác thì giữ được)")
        if ten_ma.setdefault(h["ten"], h["ma"]) != h["ma"]:
            loi.append(f"{h['ten']}: hai mã {ten_ma[h['ten']]} và {h['ma']} (đổi đồ giữa phim thì cùng mã, Tên ghi ', dạng 2')")
    if vb is not None and hang:
        thieu: dict[str, int] = {}
        for p in tach(vb)["phan"]:
            for c in p["canh"]:
                for t in c["co_mat"] or []:
                    thieu.setdefault(t, c["dong"])
                for cl in c["clip"]:
                    for t in cl["khung"] or []:
                        thieu.setdefault(t, cl["dong"])
        loi += [f"dòng {d} · '{t}' ở Có mặt/Khung không có ở bảng Cụm cố định" for t, d in thieu.items() if t not in ten_ma]
    return loi, nhac


# ---------- dàn ý ----------

def doc_dan_y(vb: str) -> dict:
    """Tách dàn ý khuôn mục 7. Mốc là số nguyên (N07 → 7). Gặt: list mốc; `toi` cho `tới Nxx`; `gach` cho `—`.
    Lỗi dạng ô (không đọc được) vào dy["loi"]."""
    dong = _dong(vb)
    dy = {"dong": dong, "loi": [], "moc": [], "gieo": [], "phan": [], "tra_tua": None, "do_dai": None}
    loi = dy["loi"]
    if m := RE_DO_DAI.search("\n".join(phan_dau(dong)[:6])):
        dy["do_dai"] = _so(m.group(1))
    for ten in MUC_KHUON:
        if khuc(dong, ten)[0] < 0:
            loi.append((None, f"thiếu mục '## {ten}'"))
    if khuc(dong, MUC_NV)[0] >= 0 and not any(d.startswith("### Nơi") for d in muc(dong, MUC_NV)):
        loi.append((None, "thiếu mục '### Nơi' trong Nhân vật và bối cảnh"))
    for ten, can in COT.items():
        g, m_ = khuc(dong, ten)
        if g < 0:
            continue
        cot = bang(m_, g)[0]
        for c in can:
            if not any(x.startswith(c) for x in cot):
                loi.append((g + 1, f"bảng {ten} thiếu cột '{c}'"))
    g, m_ = khuc(dong, "Tựa và thumbnail")
    for i, d in enumerate(m_):
        if t := RE_TRA_TUA.match(d.strip()):
            ma = RE_MOC.search(t.group(1))
            dy["tra_tua"] = (int(ma.group(1)) if ma else None, g + i + 1)
    g, m_ = khuc(dong, "Bảng mốc")
    for h in bang(m_, g)[1]:
        ma = RE_MOC.fullmatch(_cot(h, "Mốc"))
        k = RE_KHOANG.match(_cot(h, "Phút").replace(" phút", ""))
        if not ma:
            loi.append((h["dong"], f"Bảng mốc: mã '{_cot(h, 'Mốc')}' sai dạng (N01)"))
            continue
        if not k:
            loi.append((h["dong"], f"N{ma.group(1)}: Phút '{_cot(h, 'Phút')}' sai dạng (12–14 hay 1,5–3,5)"))
        dau = _so(k.group(1)) if k else None
        dy["moc"].append({"so": int(ma.group(1)), "dau": dau, "cuoi": _so(k.group(2)) if k and k.group(2) else dau, "viec": _cot(h, "Việc"),
                          **h})
    co = {m["so"] for m in dy["moc"]}
    g, m_ = khuc(dong, "Gieo và gặt")
    for h in bang(m_, g)[1]:
        ma, loai, gieo_o, gat_o = _cot(h, "Mã"), _cot(h, "Loại").lower(), _cot(h, "Gieo ở"), _cot(h, "Gặt ở").strip()
        r = {"ma": ma, "loai": loai, "dieu": _cot(h, "Điều"), "gieo": None, "gat": [], "toi": None, "gach": False, **h}
        if x := re.match(r"^N(\d{2,3})\b", gieo_o):
            r["gieo"] = int(x.group(1))
        else:
            loi.append((h["dong"], f"{ma}: Gieo ở '{gieo_o}' phải bắt đầu bằng mã mốc (N03, thoại bà)"))
        if gat_o in ("—", "–", "-"):
            r["gach"] = True
        elif x := re.fullmatch(r"tới\s+N(\d{2,3})", gat_o, re.I):
            r["toi"] = int(x.group(1))
        elif RE_MOC.search(gat_o) and not re.sub(r"[\s,]", "", RE_MOC.sub("", gat_o)):
            r["gat"] = [int(x) for x in RE_MOC.findall(gat_o)]
        else:
            loi.append((h["dong"], f"{ma}: Gặt ở '{gat_o}' sai dạng (N05 | N26, N29 | tới N06 | —)"))
        dy["gieo"].append(r)
    g, m_ = khuc(dong, "Phần")
    for h in bang(m_, g)[1]:
        ma = [int(x) for x in RE_MOC.findall(_cot(h, "Mốc"))]
        if len(ma) == 2 and re.search(r"[–-]", _cot(h, "Mốc")):
            moc = {x for x in co if ma[0] <= x <= ma[1]}
        else:
            moc = set(ma)
        p = _cot(h, "Phút").replace(" phút", "")
        so = re.match(r"\d+", _cot(h, "Phần"))
        dy["phan"].append({"so": int(so.group(0)) if so else None, "ma": ma, "moc": moc,
                           "phut": _so(p) if re.fullmatch(r"\d+(?:[,.]\d+)?", p) else None, **h})
    if dy["do_dai"] is None and dy["moc"]:
        dy["do_dai"] = max(m["cuoi"] or 0 for m in dy["moc"])
    return dy


def so_cau(viec: str) -> int:
    """Số câu của ô Việc: dấu chấm trong ngoặc kép không tính, câu trích kết bằng dấu chấm thì hết một câu."""
    s = RE_NGOAC.sub(lambda m: "Q." if re.search(r"[.!?…]\W?$", m.group(0)) else "Q", viec).strip()
    return len([x for x in RE_CAU.split(s) if x.strip()]) if s else 0


def _cuoi(r: dict) -> int | None:
    """Mốc cuối của dòng Gieo và gặt (gặt sau cùng hay `tới`); None khi `—` hay không đọc được."""
    return r["toi"] if r["toi"] is not None else (max(r["gat"]) if r["gat"] else None)


def kiem_dan_y(vb: str) -> tuple[list[Loi], list[Loi], dict]:
    dy = doc_dan_y(vb)
    loi, nhac = list(dy["loi"]), []
    dong = dy["dong"]
    phim = tach(vb)
    if phim["loai"] is None:
        loi.append((None, "thiếu dòng 'Loại phim: drama_thoai' ở đầu dàn ý"))
    if phim["seedance_goc"] is not None and phim["seedance"] is None:
        loi.append((phim["seedance_dong"], f"Seedance: '{phim['seedance_goc']}', chỉ 100%, 75% hoặc 30s"))
    ngan = (dy["do_dai"] or 0) < PHIM_NGAN
    moc = {m["so"]: m for m in dy["moc"]}
    if dy["tra_tua"] is None:
        if khuc(dong, "Tựa và thumbnail")[0] >= 0:
            loi.append((khuc(dong, "Tựa và thumbnail")[0] + 1, "Tựa và thumbnail thiếu dòng 'Trả tựa ở: Nxx'"))
    else:
        so, d = dy["tra_tua"]
        if so not in moc:
            loi.append((d, "Trả tựa ở: không trỏ mốc nào có ở Bảng mốc"))
        elif moc[so]["dau"] is not None and moc[so]["dau"] > PHUT_TRA_TUA:
            loi.append((d, f"Trả tựa ở N{so:02d}, mốc bắt đầu phút {moc[so]['dau']:g}: tựa phải trả trong {PHUT_TRA_TUA} phút đầu"))
    for a, b in zip(dy["moc"], dy["moc"][1:]):
        if a["dau"] is not None and b["dau"] is not None and b["dau"] - a["dau"] > CACH_MOC:
            loi.append((b["dong"], f"N{a['so']:02d} → N{b['so']:02d} cách {b['dau'] - a['dau']:g} phút, tối đa {CACH_MOC}: chèn mốc"))
    for m in dy["moc"]:
        if (n := so_cau(m["viec"])) > TRAN_CAU_VIEC:
            nhac.append((m["dong"], f"N{m['so']:02d}: Việc {n} câu, tối đa {TRAN_CAU_VIEC}: chi tiết sang Gieo và gặt"))
    thuoc = set()
    for p in dy["phan"]:
        thuoc |= p["moc"]
        for x in p["ma"]:
            if x not in moc:
                loi.append((p["dong"], f"Phần {p['so']}: mốc N{x:02d} không có ở Bảng mốc"))
        if ngan:
            continue
        phut = p["phut"]
        if phut is None and p["moc"] and all(moc[x]["dau"] is not None for x in p["moc"] if x in moc):
            ds = [moc[x] for x in p["moc"] if x in moc]
            phut = max(x["cuoi"] for x in ds) - min(x["dau"] for x in ds) if ds else None
        if phut is not None and not PHAN_PHUT[0] <= phut <= PHAN_PHUT[1]:
            loi.append((p["dong"], f"Phần {p['so']}: {phut:g} phút, phần dài {PHAN_PHUT[0]}–{PHAN_PHUT[1]} phút"))
        if not any(r["loai"] == "dẫn sai" and set(r["gat"]) & p["moc"] for r in dy["gieo"]):
            loi.append((p["dong"], f"Phần {p['so']}: không có dòng 'dẫn sai' gặt trong phần"))
    for m in dy["moc"]:
        if dy["phan"] and m["so"] not in thuoc:
            loi.append((m["dong"], f"N{m['so']:02d} không thuộc phần nào ở bảng Phần"))
    for r in dy["gieo"]:
        if r["loai"] not in LOAI_GIEO:
            loi.append((r["dong"], f"{r['ma']}: loại '{r['loai']}' lạ, chỉ {', '.join(LOAI_GIEO)}"))
        for x in [r["gieo"], r["toi"], *r["gat"]]:
            if x is not None and x not in moc:
                loi.append((r["dong"], f"{r['ma']}: mốc N{x:02d} không có ở Bảng mốc"))
        if r["gieo"] is not None and (c := min(r["gat"] + ([r["toi"]] if r["toi"] is not None else []), default=None)) is not None \
                and c < r["gieo"]:
            loi.append((r["dong"], f"{r['ma']}: gặt ở N{c:02d} trước gieo ở N{r['gieo']:02d}"))
        if r["loai"] == "vết":
            if not RE_BEN.search(r["dieu"]):
                loi.append((r["dong"], f"{r['ma']}: vết thiếu trái hay phải (của chính nhân vật)"))
            if r["toi"] is None:
                loi.append((r["dong"], f"{r['ma']}: vết ghi Gặt ở 'tới Nxx' (còn thấy tới mốc nào)"))
    l_cum, n_cum = kiem_cum(phan_dau(dong), None)
    loi += [(None, x) for x in l_cum]
    nhac += [(None, x) for x in n_cum]
    g, m_ = khuc(dong, MUC_CUM)
    tok = _tok([d for i, d in enumerate(dong) if not (g >= 0 and g <= i < g + len(m_))])
    if tok > TRAN_TOKEN_DAN_Y:
        nhac.append((None, f"dàn ý không kể Cụm cố định khoảng {tok} token, nên dưới {TRAN_TOKEN_DAN_Y}: rút Việc, Điều"))
    dy["token"] = tok
    loi.sort(key=lambda x: x[0] or 0)
    nhac.sort(key=lambda x: x[0] or 0)
    return loi, nhac, dy


def cat_phan(dy: dict, n: int) -> list[str] | None:
    """Phần dàn ý trợ lý viết phần n đọc. None khi bảng Phần không có phần n."""
    p = next((x for x in dy["phan"] if x["so"] == n), None)
    if p is None:
        return None
    dong, ra = dy["dong"], []

    def them(khoi: list[str]) -> None:
        if khoi:
            ra.extend(([""] if ra else []) + khoi)

    them(phan_dau(dong)[: next((i for i, d in enumerate(phan_dau(dong)) if d.startswith("## ")), None)])
    while ra and not ra[-1].strip():
        ra.pop()
    for ten in ("Tựa và thumbnail", "Logline", "Bí mật khán giả biết trước"):
        them(muc(dong, ten))
    nv = muc(dong, MUC_NV)
    k = next((i for i, d in enumerate(nv) if d.startswith("### ")), len(nv))
    cot, hang = bang(nv[:k])
    giu = [c for c in cot if c.startswith(COT_NV_DOC)]
    them([nv[0], "| " + " | ".join(giu) + " |", "|" + "---|" * len(giu)] + ["| " + " | ".join(h["o"].get(c, "") for c in giu) + " |" for h in hang])
    them([d for d in nv[k:]])
    while ra and not ra[-1].strip():
        ra.pop()
    them(muc(dong, "Kẻ ác từng vòng"))
    if n == 1:
        them(muc(dong, "Mở phim"))
    vi = [i for i, m in enumerate(dy["moc"]) if m["so"] in p["moc"]]
    if vi:
        lay = dy["moc"][max(vi[0] - 1, 0): vi[-1] + 2]
        them(_dau_bang(dong, "Bảng mốc") + [m["goc"] for m in lay])
    a, b = min(p["moc"], default=0), max(p["moc"], default=0)
    chon = []
    for r in dy["gieo"]:
        trong = r["gieo"] in p["moc"] or set(r["gat"]) & p["moc"]
        cuoi = _cuoi(r)
        mang = r["loai"] in LOAI_MANG_SANG and r["gieo"] is not None and r["gieo"] <= b and (cuoi is None or cuoi >= a)
        if trong or mang:
            chon.append(r["goc"])
    them(_dau_bang(dong, "Gieo và gặt") + chon)
    them(_dau_bang(dong, "Phần") + [p["goc"]])
    return ra


def _dau_bang(dong: list[str], ten: str) -> list[str]:
    """Tiêu đề mục và hai dòng đầu bảng (cột, ---)."""
    m = muc(dong, ten)
    k = next((i for i, d in enumerate(m) if d.strip().startswith("|")), None)
    return [m[0]] + (m[k:k + 2] if k is not None else []) if m else []


# ---------- file phần ----------

def _tim_dan_y(f: Path) -> Path | None:
    return next((x for x in (f.parent / "00-dan-y.md", f.parent / "kich-ban" / "00-dan-y.md") if x.exists()), None)


def kiem_gieo_phan(vb: str, dy: dict | None) -> tuple[list[str], list[str], int]:
    """Dòng `- Gieo, gặt:` của mỗi phần so với Gieo và gặt của dàn ý; NHẮC vết ở Hình: thiếu bên. Trả (lỗi, nhắc, số mã G đã đủ)."""
    loi, nhac, du = [], [], 0
    phim = tach(vb)
    for p in phim["phan"]:
        clip = {c["ma"] for c in cac_clip(p) + p["clip_ngoai"]}
        for c in cac_clip(p):
            for cau in re.split(r"[.;]|\bShot\b", c["hinh"] or "", flags=re.I):
                if (v := RE_VET.search(RE_KHONG_VET.sub("", cau))) and not RE_BEN.search(cau):
                    nhac.append(f"dòng {c['dong']} · {c['ma']}: Hình: có '{v.group(1)}' mà câu đó không ghi trái hay phải (của chính nhân vật)")
                    break
        if dy is None:
            continue
        hp = next((x for x in dy["phan"] if x["so"] == p["so"]), None)
        moc = hp["moc"] if hp else {int(RE_MOC.search(c["nhip"]).group(1)) for c in p["canh"] if RE_MOC.search(c["nhip"] or "")}
        can = {r["ma"]: r for r in dy["gieo"] if r["gieo"] in moc or set(r["gat"]) & moc}
        dong_gg = next((x for x in p["ghi_chu_noi"].split("\n") if RE_GIEO_GAT.match(x.strip())), None)
        if dong_gg is None:
            if can:
                loi.append(f"dòng {p['dong']} · Phần {p['so']}: Ghi chú nối thiếu dòng '- Gieo, gặt: G01 P003, …' (mã G và clip nơi gieo "
                           f"hay gặt), cần: {', '.join(sorted(can))}")
            continue
        co: dict[str, list[str]] = {}
        g = None
        for t in RE_GP.findall(RE_GIEO_GAT.match(dong_gg.strip()).group(1)):
            if t[0] == "G":
                g = t
                co.setdefault(g, [])
            elif g:
                co[g].append(t)
        ma_dy = {r["ma"] for r in dy["gieo"]}
        for g, ps in co.items():
            if g not in ma_dy:
                loi.append(f"Phần {p['so']}: Gieo, gặt: {g} không có ở bảng Gieo và gặt của dàn ý")
            elif not ps:
                loi.append(f"Phần {p['so']}: Gieo, gặt: {g} thiếu mã clip")
            for x in ps:
                if x not in clip:
                    loi.append(f"Phần {p['so']}: Gieo, gặt: {g} trỏ {x}, phần không có clip này")
            if g in ma_dy and g not in can:
                nhac.append(f"Phần {p['so']}: Gieo, gặt: {g} không gieo hay gặt ở mốc của phần (dàn ý)")
        for g, r in can.items():
            if g not in co:
                loi.append(f"Phần {p['so']}: {g} ({r['loai']}: {r['dieu'][:50]}) gieo hay gặt trong phần mà thiếu ở dòng Gieo, gặt")
            elif co[g]:
                du += 1
    return loi, nhac, du


def _tu(c: dict) -> int:
    return sum(so_tu(lt["cau"]) for lt in c["thoai"]) + (so_tu(c["loi_nghi"]["cau"]) if c["loi_nghi"] else 0)


def kiem_nhip(vb: str) -> list[str]:
    """NHẮC đất diễn và neo cảnh: % giây có lời mỗi phần, cảnh thiếu nhịp diễn, clip đầu cảnh thiếu shot định vị."""
    nhac = []
    for p in tach(vb)["phan"]:
        tong = loi = 0.0
        for canh in p["canh"]:
            clip = [c for c in canh["clip"] if c["giay"]]
            for c in clip:
                tong += c["giay"]
                loi += min(c["giay"], _tu(c) / TU_MOI_GIAY_NOI)
            if len(clip) >= CLIP_CANH_NHIP and not any(_tu(c) <= TU_NHIP_DIEN * c["giay"] for c in clip):
                nhac.append(f"dòng {canh['dong']} · {canh['ma']}: {len(clip)} clip đều dày lời, không nhịp diễn (clip tối đa "
                            f"{TU_NHIP_DIEN} từ/giây ở đỉnh: phản ứng, đẩy vào, đặc tả vật)")
            if canh["clip"] and not RE_DINH_VI.search(canh["clip"][0]["hinh"] or ""):
                nhac.append(f"dòng {canh['clip'][0]['dong']} · {canh['clip'][0]['ma']}: clip đầu {canh['ma']} không có shot định vị "
                            f"(trung rộng, toàn: nơi, ai đứng đâu)")
        if tong and sum(len(c["clip"]) for c in p["canh"]) >= CLIP_DO_TY_LOI:
            ty = loi / tong
            if not TY_LOI[0] <= ty <= TY_LOI[1]:
                nhac.append(f"Phần {p['so']}: khoảng {round(ty * 100)}% giây có lời, nên {round(TY_LOI[0] * 100)}–{round(TY_LOI[1] * 100)}% "
                            + ("(gần toàn lời: chừa nhịp diễn ở đỉnh cảnh)" if ty > TY_LOI[1] else "(thưa lời: khán giả thiếu ngữ cảnh)"))
    return nhac


def kiem_file(f: Path, nhan: str) -> int:
    if not f.exists():
        print(f"LỖI: không thấy {f}")
        return 1
    vb = f.read_text(encoding="utf-8")
    dau = phan_dau(_dong(vb))
    if len(dau) == 0 and (p1 := f.parent / "phan-01.md").exists():
        dau = phan_dau(_dong(p1.read_text(encoding="utf-8")))
    loi, nhac = kiem_cum(dau, vb)
    dy_f = _tim_dan_y(f)
    dy = doc_dan_y(dy_f.read_text(encoding="utf-8")) if dy_f else None
    l2, n2, du = kiem_gieo_phan(vb, dy)
    loi += l2
    nhac += n2 + kiem_nhip(vb)
    if dy is None:
        nhac.append("không thấy 00-dan-y.md cạnh file: bỏ kiểm dòng Gieo, gặt")
    elif dau and phan_dau(dy["dong"]) != dau and f.name in ("phan-01.md", "kich-ban.md"):
        nhac.append("phần đầu khác dàn ý: chạy 'py -3 cong-cu/dan_y_drama.py dau <thư mục kich-ban>' rồi gộp lại")
    for x in loi:
        print("LỖI:", nhan + x)
    for x in nhac:
        print("NHẮC:", nhan + x)
    print(f"{nhan}Cụm cố định: {len(cum(dau))} dòng NV · Gieo, gặt: {du} mã đủ clip · {len(loi)} LỖI, {len(nhac)} NHẮC")
    return 1 if loi else 0


# ---------- lệnh ----------

def _file_dan_y(a: str) -> Path:
    f = Path(a)
    return f / "00-dan-y.md" if f.is_dir() else f


def lenh_kiem(a: str) -> int:
    f = _file_dan_y(a)
    if not f.exists():
        print(f"LỖI: không thấy {f}")
        return 1
    loi, nhac, dy = kiem_dan_y(f.read_text(encoding="utf-8"))
    for d, x in loi:
        print("LỖI:", (f"dòng {d} · " if d else "") + x)
    for d, x in nhac:
        print("NHẮC:", (f"dòng {d} · " if d else "") + x)
    print(f"Dàn ý: {len(dy['moc'])} mốc, {len(dy['phan'])} phần, {len(dy['gieo'])} dòng Gieo và gặt, khoảng {dy['token']} token "
          f"(không kể Cụm cố định) · {len(loi)} LỖI, {len(nhac)} NHẮC")
    return 1 if loi else 0


def lenh_doc(a: str, n: str) -> int:
    f = _file_dan_y(a)
    if not f.exists() or not n.isdigit():
        print(f"LỖI: không thấy {f}" if not f.exists() else f"LỖI: số phần '{n}' sai")
        return 1
    dy = doc_dan_y(f.read_text(encoding="utf-8"))
    ra = cat_phan(dy, int(n))
    if ra is None:
        print(f"LỖI: bảng Phần của dàn ý không có phần {n}")
        return 1
    print("\n".join(ra))
    tok = _tok(ra)
    if tok > TRAN_TOKEN_DOC:
        print(f"NHẮC: phần {n} khoảng {tok} token, nên dưới {TRAN_TOKEN_DOC}: rút Việc, Điều ở dàn ý")
    print(f"<!-- dan_y_drama doc phần {n}: khoảng {tok} token -->")
    return 0


def lenh_dau(a: str) -> int:
    d = Path(a)
    dy, p1 = d / "00-dan-y.md", d / "phan-01.md"
    if not dy.exists() or not p1.exists():
        print(f"LỖI: {d} thiếu 00-dan-y.md hay phan-01.md")
        return 1
    dau = phan_dau(_dong(dy.read_text(encoding="utf-8")))
    d1 = _dong(p1.read_text(encoding="utf-8"))
    k = next((i for i, x in enumerate(d1) if RE_PHAN.match(x.strip())), None)
    if k is None:
        print(f"LỖI: {p1.name} chưa có dòng '# Phần 1'")
        return 1
    p1.write_text("\n".join(dau + [""] + d1[k:]), encoding="utf-8", newline="\n")
    print(f"Đã chép phần đầu ({len(dau)} dòng) từ dàn ý vào {p1.name}")
    return kiem_file(p1, "")


RE_TIEU_DE_MA = re.compile(r"^(###? )([PC])(\d{2,4})(?:-([a-z]))?(?![\w-])")
RE_MA_TRO = re.compile(r"\b([PC])(\d{2,4})(?:-([a-z]))?(?![\w-])")


def danh_ma(vbs: list[str]) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """Đánh lại mã clip (`### P`) và cảnh (`## C`) liền qua các phần (đã theo thứ tự), từ mã đầu của mỗi loại, giữ số chữ số; sửa mọi chỗ trỏ
    mã (khối trận, Mã cuối, Gieo, gặt) theo mã mới. P45 và P045 là một mã. → (văn bản mới, lỗi, [(P đầu, C đầu) từng phần])."""
    doi, loi, dem, dau = {}, [], {}, []
    for vb in vbs:
        dau.append(["", ""])
        for d in vb.splitlines():
            if not (m := RE_TIEU_DE_MA.match(d)) or (m.group(1) == "## ") != (m.group(2) == "C"):
                continue
            k = (m.group(2), int(m.group(3)), m.group(4) or "")
            if k in doi:
                loi.append(f"mã {d.split()[1]} trùng: đổi mã tạm của clip, cảnh chèn thành -b, -c")
                continue
            so, rong = dem.get(k[0], (k[1], len(m.group(3))))
            doi[k], dem[k[0]] = f"{k[0]}{so:0{rong}d}", (so + 1, rong)
            dau[-1][k[0] == "C"] = dau[-1][k[0] == "C"] or doi[k]
    moi = [RE_MA_TRO.sub(lambda m: doi.get((m.group(1), int(m.group(2)), m.group(3) or ""), m.group(0)), vb) for vb in vbs]
    return moi, loi, [tuple(x) for x in dau]


def lenh_danh_ma(a: str) -> int:
    tep = sorted(Path(a).glob("phan-*.md"), key=_so_file)
    if not tep:
        print(f"LỖI: {a} không có file phần (phan-*.md)")
        return 1
    cu = [f.read_text(encoding="utf-8") for f in tep]
    moi, loi, dau = danh_ma(cu)
    if loi:
        print("\n".join(f"LỖI: {x}" for x in loi) + "\nChưa ghi file nào.")
        return 1
    for f, c, m in zip(tep, cu, moi):
        if c != m:
            f.write_text(m, encoding="utf-8", newline="\n")
    print(f"Đã đánh lại mã {sum(c != m for c, m in zip(cu, moi))}/{len(tep)} file. Bảng Phần (P đầu, C đầu): "
          + ", ".join(f"{f.stem} {p} {c}" for f, (p, c) in zip(tep, dau)))
    return 0


def main(arg: list[str]) -> int:
    lenh = arg[0] if arg else ""
    if lenh == "kiem" and len(arg) == 2:
        return lenh_kiem(arg[1])
    if lenh == "doc" and len(arg) == 3:
        return lenh_doc(arg[1], arg[2])
    if lenh == "dau" and len(arg) == 2:
        return lenh_dau(arg[1])
    if lenh == "danh-ma" and len(arg) == 2:
        return lenh_danh_ma(arg[1])
    if lenh == "phan" and len(arg) >= 2:
        kq = 0
        for a in arg[1:]:
            kq |= kiem_file(Path(a), f"{Path(a).name}: " if len(arg) > 2 else "")
        return kq
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
