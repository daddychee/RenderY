"""Dàn ý loại phim thường (`00-nhip.md` khuôn mới ở kinh-nghiem/nang-cap-bien-kich/00-ke-hoach.md) và dòng `Gieo, gặt phần n:` ở file hồi.
Của thư mục skill, không phải bản chép: luật web (`luat_kich_ban.py`, chạy qua `kiem_kich_ban.py`) bỏ qua các mục mới nên luật của chúng ở đây.

Chạy: py -3 cong-cu/dan_y.py kiem <thư mục kich-ban | 00-nhip.md>     kiểm dàn ý
      py -3 cong-cu/dan_y.py phan <hoi-n.md> --phan <n>              kiểm dòng `- Gieo, gặt phần <n>: G01 P03, …` ở `## Để viết hồi sau`
                                                                     (00-nhip.md và các hoi-*.md lấy cạnh file)
In phần dàn ý trợ lý viết phần n cần: py -3 cong-cu/doc_phan.py <phim> --phan <n>.
Phút của nhịp = cột Cảnh (số clip) / 6; phút phần = tổng các nhịp của phần. Phim `Clip: 30s` (dòng `Thể loại: …`, Spec 55): cột Cảnh
là số đơn vị 15 giây (cảnh 30s = 2), phút = đơn vị / 4,5.
kiem · LỖI: thiếu mục Tựa và thumbnail (dòng Tựa, Thumbnail, Trả tựa ở), Ba hồi, Bảng nhịp, Gieo và gặt, Phần, hay cột của khuôn; `Trả tựa ở`
  không phải mã nhịp có thật; cột Cảnh không phải số; Gieo và gặt: loại lạ (chỉ lật, dẫn sai, phi lý, vết, biết, vật), Gieo ở không bắt đầu
  bằng mã nhịp, Gặt ở sai dạng (N05 | N26, N29 | tới N06 | —), gặt trước gieo, mã nhịp không có ở Bảng nhịp, `vết` thiếu trái/phải (hay
  cả người, hai bên…) hay thiếu `tới Nxx`; Phần: mã nhịp không có, nhịp không thuộc phần nào hay thuộc hai phần, nhịp trong phần không liền,
  phần trùm hai hồi (theo Ba hồi) trừ khi một hồi dưới 5 phút, phần ngoài 5–9 phút (phim dưới 10 phút miễn), cột Clip lệch tổng cột Cảnh.
  NHẮC: phần không có dòng `dẫn sai` gặt trong phần; Sự kiện quá 2 câu (không tính ngoặc mã KB, `(nhắc: …)`); cột Hồi của Phần khác Ba hồi;
  Bảng nhịp còn cột Gieo hay Trả ở (khuôn cũ).
phan · LỖI: thiếu dòng `Gieo, gặt phần <n>:` khi phần có dòng G gieo hay gặt; dòng G gieo hay gặt ở nhịp của phần mà thiếu ở dòng đó; mã G
  lạ hay không kèm cảnh; cảnh P không có trong các hồi hay không mang nhịp của phần (P003 và P03 là một; cảnh chèn P42-b đọc được, nhưng
  chạy danh_lai_ma.py trước rồi mới kiểm). NHẮC: mã G không gieo, gặt trong phần; câu ở cảnh của
  phần có chữ vết thương (vết, bầm, sẹo, băng bó, máu, rách, sưng, wound, bandage, scar, bruise, cut) mà không có trái/phải (left/right).
In LỖI, NHẮC và một dòng tóm tắt. Chỉ thư viện chuẩn. Thoát 1 khi có LỖI."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dan_y_drama import LOAI_GIEO, RE_BEN, RE_KHONG_VET, _cot, _dong, _so, bang, khuc, so_cau  # noqa: E402
from luat_kich_ban import clip_phim, dong_cap_phim  # noqa: E402

MUC_KHUON = ("Tựa và thumbnail", "Ba hồi", "Bảng nhịp", "Gieo và gặt", "Phần")
COT = {"Bảng nhịp": ("Mã", "Cảnh", "Sự kiện"), "Gieo và gặt": ("Mã", "Loại", "Điều", "Gieo ở", "Gặt ở"),
       "Phần": ("Phần", "Hồi", "Nhịp", "Phút", "Clip")}
DONG_TUA = (("tựa:", "Tựa: <tựa YouTube>"), ("thumbnail:", "Thumbnail: <ai, mặc gì, làm gì>"), ("trả tựa ở:", "Trả tựa ở: Nxx"))
CLIP_MOT_PHUT, PHAN_PHUT, PHIM_NGAN, HOI_NGAN, TRAN_CAU = 6, (5, 9), 10, 5, 2
DON_VI_MOT_PHUT_30 = 4.5         # phim Clip: 30s: đơn vị 15 giây mỗi phút
RE_N = re.compile(r"\bN(\d{2,3})\b")
RE_DAI = re.compile(r"Dài:\s*(\d+(?:[,.]\d+)?)", re.I)
RE_BA_HOI = re.compile(r"^-\s*\**Hồi\s+(\d+)\**\s*\(\s*N(\d+)\s*[–-]\s*N(\d+)")
RE_KB_NGOAC = re.compile(r"\((?:\s*KB\s*\d+\s*[,;]?)+\)|\(nhắc:[^)]*\)", re.I)
RE_GG_PHAN = re.compile(r"^-?\s*\**Gieo,\s*gặt\s+phần\s+(\d+)\**\s*:(.*)$", re.I)
RE_GP = re.compile(r"\b(G\d{2,4}|P\d{2,4})(?:-([a-z]))?\b")
RE_CANH = re.compile(r"^## P(\d{2,4})(?:-([a-z]))?(?![\w-])(.*)$")
# Chữ vết thương. `băng` chỉ khi là băng bó (fantasy có điện băng, sông băng); `máu` bỏ dòng máu, mạch máu; `cut` bỏ hard cut, cut to.
RE_VET = re.compile(r"\b(vết|bầm|sẹo|sưng|rách|máu(?! (?:mủ|lạnh|rút|dồn|nóng|mặt|lửa|rồng))|băng (?:bó|vải|quấn|kín|trắng|cho|vết|ở|trên|quanh)|"
                    r"(?:quấn|bó|thay|tháo|cuộn|dải|miếng|vải) băng|wound\w*|bandage\w*|scar\w*|bruis\w*|"
                    r"(?<!hard )(?<!jump )(?<!smash )(?<!match )cuts?(?! to\b| away\b))\b", re.I)
RE_KHONG_VET2 = re.compile(r"dòng máu|mạch máu|như máu|dấu vết|vết (?:xe|móng|khắc)|rách (?:\w+ )?(?:áo|vải|váy|quần|giấy|rèm|buồm|túi)", re.I)
RE_BEN_EN = re.compile(r"\b(left|right|both|all over|whole body)\b", re.I)

Loi = tuple[int | None, str]


def _ma(s: str) -> int | None:
    m = RE_N.search(s)
    return int(m.group(1)) if m else None


def doc_nhip(vb: str) -> dict:
    """Tách 00-nhip.md khuôn mới. Nhịp là số nguyên (N07 → 7). Lỗi dạng (không đọc được) vào d["loi"]."""
    dong = _dong(vb)
    d = {"dong": dong, "loi": [], "nhac": [], "nhip": [], "gieo": [], "phan": [], "hoi": [], "tra_tua": None, "dai": None}
    loi = d["loi"]
    dau = next((i for i, x in enumerate(dong) if x.startswith("## ")), len(dong))
    d["clip"] = clip_phim(dong_cap_phim(dong[:dau])[1]) or 15
    if m := RE_DAI.search("\n".join(dong[:dau])):
        d["dai"] = _so(m.group(1))
    for ten in MUC_KHUON:
        if khuc(dong, ten)[0] < 0:
            loi.append((None, f"thiếu mục '## {ten}'"))
    for ten, can in COT.items():
        g, m_ = khuc(dong, ten)
        if g < 0:
            continue
        cot = bang(m_, g)[0]
        for c in can:
            if not any(x.startswith(c) for x in cot):
                loi.append((g + 1, f"bảng {ten} thiếu cột '{c}'"))
        if ten == "Bảng nhịp" and (cu := [x for x in cot if x == "Gieo" or x.startswith("Trả ở")]):
            d["nhac"].append((g + 1, f"Bảng nhịp còn cột {', '.join(cu)} (khuôn cũ): chuyển sang mục Gieo và gặt rồi bỏ cột"))
    g, m_ = khuc(dong, "Tựa và thumbnail")
    if g >= 0:
        for dau_dong, mau in DONG_TUA:
            i = next((i for i, x in enumerate(m_) if x.strip().lower().startswith(dau_dong)), None)
            if i is None:
                loi.append((g + 1, f"Tựa và thumbnail thiếu dòng '{mau}'"))
            elif dau_dong == "trả tựa ở:":
                d["tra_tua"] = (_ma(m_[i]), g + i + 1)
    g, m_ = khuc(dong, "Ba hồi")
    for i, x in enumerate(m_):
        if h := RE_BA_HOI.match(x.strip()):
            d["hoi"].append({"so": int(h.group(1)), "tu": int(h.group(2)), "toi": int(h.group(3)), "dong": g + i + 1})
    g, m_ = khuc(dong, "Bảng nhịp")
    for h in bang(m_, g)[1]:
        ma = re.fullmatch(r"N(\d{2,3})", _cot(h, "Mã"))
        if not ma:
            continue                          # mã sai dạng: luat_kich_ban (kiem_kich_ban.py) báo
        c = _cot(h, "Cảnh")
        if not c.isdigit():
            loi.append((h["dong"], f"N{ma.group(1)}: cột Cảnh '{c}' phải là số clip"))
        d["nhip"].append({"so": int(ma.group(1)), "canh": int(c) if c.isdigit() else 0, "su_kien": _cot(h, "Sự kiện"), **h})
    g, m_ = khuc(dong, "Gieo và gặt")
    for h in bang(m_, g)[1]:
        ma, loai, gieo_o, gat_o = _cot(h, "Mã"), _cot(h, "Loại").lower(), _cot(h, "Gieo ở"), _cot(h, "Gặt ở").strip()
        r = {"ma": ma, "loai": loai, "dieu": _cot(h, "Điều"), "gieo": None, "gat": [], "toi": None, "gach": False, **h}
        if x := re.match(r"^N(\d{2,3})\b", gieo_o):
            r["gieo"] = int(x.group(1))
        else:
            loi.append((h["dong"], f"{ma}: Gieo ở '{gieo_o}' phải bắt đầu bằng mã nhịp (N03, cô thổi còi)"))
        if gat_o in ("—", "–", "-"):
            r["gach"] = True
        elif x := re.fullmatch(r"tới\s+N(\d{2,3})", gat_o, re.I):
            r["toi"] = int(x.group(1))
        elif RE_N.search(gat_o) and not re.sub(r"[\s,]", "", RE_N.sub("", gat_o)):
            r["gat"] = [int(x) for x in RE_N.findall(gat_o)]
        else:
            loi.append((h["dong"], f"{ma}: Gặt ở '{gat_o}' sai dạng (N05 | N26, N29 | tới N06 | —)"))
        d["gieo"].append(r)
    co = [n["so"] for n in d["nhip"]]
    g, m_ = khuc(dong, "Phần")
    for h in bang(m_, g)[1]:
        o = _cot(h, "Nhịp")
        ma = [int(x) for x in RE_N.findall(o)]
        nhip = [x for x in co if ma[0] <= x <= ma[1]] if len(ma) == 2 and re.search(r"[–-]", o) else ma
        so = re.match(r"\d+", _cot(h, "Phần"))
        clip = _cot(h, "Clip")
        d["phan"].append({"so": int(so.group(0)) if so else None, "ma": ma, "nhip": nhip, "hoi_ghi": {int(x) for x in re.findall(r"\d+", _cot(h, "Hồi"))},
                          "clip": int(clip) if clip.isdigit() else None, **h})
    return d


def phut_nhip(d: dict, nhip) -> float:
    canh = {n["so"]: n["canh"] for n in d["nhip"]}
    return sum(canh.get(x, 0) for x in nhip) / (DON_VI_MOT_PHUT_30 if d.get("clip") == 30 else CLIP_MOT_PHUT)


def hoi_cua(d: dict, n: int) -> int | None:
    return next((h["so"] for h in d["hoi"] if h["tu"] <= n <= h["toi"]), None)


def cau_su_kien(s: str) -> int:
    return so_cau(RE_KB_NGOAC.sub("", s))


def kiem_nhip(vb: str) -> tuple[list[Loi], list[Loi], dict]:
    d = doc_nhip(vb)
    loi, nhac = list(d["loi"]), list(d["nhac"])
    nhip = {n["so"]: n for n in d["nhip"]}
    thu_tu = [n["so"] for n in d["nhip"]]
    tong = phut_nhip(d, thu_tu)
    ngan = (d["dai"] if d["dai"] is not None else tong) < PHIM_NGAN
    if d["tra_tua"] is not None:
        so, dg = d["tra_tua"]
        if so not in nhip:
            loi.append((dg, "Trả tựa ở: phải là mã nhịp có ở Bảng nhịp (N02)"))
    for n in d["nhip"]:
        if (k := cau_su_kien(n["su_kien"])) > TRAN_CAU:
            nhac.append((n["dong"], f"N{n['so']:02d}: Sự kiện {k} câu, tối đa {TRAN_CAU}: chi tiết sang Gieo và gặt, Bảng phân clip"))
    thuoc: dict[int, list] = {}
    for p in d["phan"]:
        ten = f"Phần {p['so']}"
        for x in p["ma"]:
            if x not in nhip:
                loi.append((p["dong"], f"{ten}: nhịp N{x:02d} không có ở Bảng nhịp"))
        ds = [x for x in p["nhip"] if x in nhip]
        for x in ds:
            thuoc.setdefault(x, []).append(p["so"])
        vi = sorted(thu_tu.index(x) for x in ds)
        if vi and vi != list(range(vi[0], vi[0] + len(vi))):
            loi.append((p["dong"], f"{ten}: các nhịp không liền ({', '.join(f'N{x:02d}' for x in ds)})"))
        hoi = sorted({h for x in ds if (h := hoi_cua(d, x)) is not None})
        if len(hoi) > 1:
            phut_hoi = {h: phut_nhip(d, [x for x in thu_tu if hoi_cua(d, x) == h]) for h in hoi}
            if all(v >= HOI_NGAN for v in phut_hoi.values()):
                loi.append((p["dong"], f"{ten} trùm hồi {', '.join(map(str, hoi))} (mỗi hồi từ {HOI_NGAN} phút): cắt ở ranh giới hồi"))
        if hoi and p["hoi_ghi"] and p["hoi_ghi"] != set(hoi):
            nhac.append((p["dong"], f"{ten}: cột Hồi ghi {', '.join(map(str, sorted(p['hoi_ghi'])))}, theo Ba hồi là {', '.join(map(str, hoi))}"))
        p["phut_tinh"] = phut = phut_nhip(d, ds)
        if not ngan and not PHAN_PHUT[0] <= phut <= PHAN_PHUT[1]:
            loi.append((p["dong"], f"{ten}: {f'{phut:.1f}'.replace('.', ',')} phút (tổng Cảnh / {'4,5' if d.get('clip') == 30 else 6}), phần dài {PHAN_PHUT[0]}–{PHAN_PHUT[1]} phút"))
        so_clip = sum(nhip[x]["canh"] for x in ds)
        if p["clip"] != so_clip:
            loi.append((p["dong"], f"{ten}: cột Clip '{_cot(p, 'Clip')}' lệch tổng cột Cảnh {so_clip}"))
        if not any(r["loai"] == "dẫn sai" and set(r["gat"]) & set(ds) for r in d["gieo"]):
            nhac.append((p["dong"], f"{ten}: không có dòng 'dẫn sai' gặt trong phần"))
    if d["phan"]:
        for n in d["nhip"]:
            if n["so"] not in thuoc:
                loi.append((n["dong"], f"N{n['so']:02d} không thuộc phần nào ở bảng Phần"))
            elif len(thuoc[n["so"]]) > 1:
                loi.append((n["dong"], f"N{n['so']:02d} thuộc nhiều phần ({', '.join(map(str, thuoc[n['so']]))})"))
    for r in d["gieo"]:
        if r["loai"] not in LOAI_GIEO:
            loi.append((r["dong"], f"{r['ma']}: loại '{r['loai']}' lạ, chỉ {', '.join(LOAI_GIEO)}"))
        for x in [r["gieo"], r["toi"], *r["gat"]]:
            if x is not None and x not in nhip:
                loi.append((r["dong"], f"{r['ma']}: nhịp N{x:02d} không có ở Bảng nhịp"))
        dau = min(r["gat"] + ([r["toi"]] if r["toi"] is not None else []), default=None)
        if r["gieo"] is not None and dau is not None and dau < r["gieo"]:
            loi.append((r["dong"], f"{r['ma']}: gặt ở N{dau:02d} trước gieo ở N{r['gieo']:02d}"))
        if r["loai"] == "vết":
            if not (RE_BEN.search(r["dieu"]) or RE_BEN_EN.search(r["dieu"])):
                loi.append((r["dong"], f"{r['ma']}: vết thiếu trái hay phải (của chính nhân vật; hay cả người, hai bên)"))
            if r["toi"] is None:
                loi.append((r["dong"], f"{r['ma']}: vết ghi Gặt ở 'tới Nxx' (còn thấy tới nhịp nào)"))
    loi.sort(key=lambda x: x[0] or 0)
    nhac.sort(key=lambda x: x[0] or 0)
    d["phut"] = tong
    return loi, nhac, d


# ---------- file hồi ----------

def khoa(so: str, duoi: str = "") -> str:
    """Mã cảnh chuẩn: P003 và P03 là một (`P03`), cảnh chèn giữ đuôi (`P42-b`)."""
    return f"P{int(so):02d}" + (f"-{duoi}" if duoi else "")


def canh_hoi(tm: Path, them: Path | None = None) -> dict[str, dict]:
    """Các cảnh `## Pxx · … · Nyy` của mọi hoi-*.md trong tm (và file them): mã chuẩn → {file, nhịp, dòng đầu, các dòng}."""
    ra = {}
    tep = sorted(set(tm.glob("hoi-*.md")) | ({them.resolve()} if them else set()), key=lambda f: f.name)
    for f in tep:
        dong = _dong(f.read_text(encoding="utf-8"))
        moc = [i for i, x in enumerate(dong) if x.startswith(("# ", "## "))] + [len(dong)]
        for a, b in zip(moc, moc[1:]):
            if k := RE_CANH.match(dong[a]):
                ra.setdefault(khoa(k.group(1), k.group(2)), {"file": f.resolve(), "nhip": {int(x) for x in RE_N.findall(k.group(3))}, "dau": a,
                                                "dong": dong[a:b]})
    return ra


def vet_thieu_ben(dong: list[str], goc: int) -> tuple[int, str] | None:
    """Câu đầu tiên có chữ vết thương mà không có bên: (số dòng từ 1, chữ)."""
    for i, x in enumerate(dong):
        if x.startswith("#"):
            continue                          # tiêu đề cảnh là nhãn ngắn
        for cau in re.split(r"[.;!?→]|\s\|\s", x):
            sach = RE_KHONG_VET2.sub("", RE_KHONG_VET.sub("", cau))
            if (v := RE_VET.search(sach)) and not (RE_BEN.search(cau) or RE_BEN_EN.search(cau)):
                return goc + i + 1, v.group(1)
    return None


def kiem_phan(f: Path, n: int) -> tuple[list[str], list[str], str]:
    tm = f.parent
    f_nhip = tm / "00-nhip.md"
    if not f.exists() or not f_nhip.exists():
        return [f"không thấy {f if not f.exists() else f_nhip}"], [], ""
    d = doc_nhip(f_nhip.read_text(encoding="utf-8"))
    p = next((x for x in d["phan"] if x["so"] == n), None)
    if p is None:
        return [f"bảng Phần của 00-nhip.md không có phần {n}"], [], ""
    loi, nhac = [], []
    nhip = set(p["nhip"])
    canh = canh_hoi(tm, f)
    cua_file = {k: c for k, c in canh.items() if c["file"] == f.resolve() and c["nhip"] & nhip}
    for k, c in sorted(cua_file.items(), key=lambda x: (x[1]["file"].name, x[1]["dau"])):
        if v := vet_thieu_ben(c["dong"], c["dau"]):
            nhac.append(f"dòng {v[0]} · {k}: có '{v[1]}' mà câu đó không ghi trái hay phải (left/right) của chính nhân vật")
    can = {r["ma"]: r for r in d["gieo"] if r["gieo"] in nhip or set(r["gat"]) & nhip}
    dong = _dong(f.read_text(encoding="utf-8"))
    g, m_ = khuc(dong, "Để viết hồi sau")
    hang = next(((g + i + 1, h) for i, x in enumerate(m_) if (h := RE_GG_PHAN.match(x.strip())) and int(h.group(1)) == n), None)
    tom = f"Phần {n} ({f.name}): {len(cua_file)} cảnh, nhịp N{min(nhip, default=0):02d}–N{max(nhip, default=0):02d}"
    if hang is None:
        if can:
            loi.append(f"mục '## Để viết hồi sau' thiếu dòng '- Gieo, gặt phần {n}: G01 P03, …' (mã G và cảnh nơi gieo hay gặt), "
                       f"cần: {', '.join(sorted(can))}")
        return loi, nhac, tom + f" · Gieo, gặt: 0/{len(can)} mã"
    so_dong, h = hang
    co: dict[str, list[tuple[str, str]]] = {}
    gma = None
    for t, duoi in RE_GP.findall(h.group(2)):
        if t[0] == "G":
            gma = t
            co.setdefault(gma, [])
        elif gma:
            co[gma].append((khoa(t[1:], duoi), t + (f"-{duoi}" if duoi else "")))
    ma_g = {r["ma"] for r in d["gieo"]}
    du = 0
    for gm, ps in co.items():
        if gm not in ma_g:
            loi.append(f"dòng {so_dong} · {gm} không có ở bảng Gieo và gặt")
        elif not ps:
            loi.append(f"dòng {so_dong} · {gm} thiếu mã cảnh")
        elif gm not in can:
            nhac.append(f"dòng {so_dong} · {gm} không gieo hay gặt ở nhịp của phần {n} (00-nhip.md)")
        for so, nhan in ps:
            if so not in canh:
                loi.append(f"dòng {so_dong} · {gm} trỏ {nhan}, các hồi không có cảnh này")
            elif not canh[so]["nhip"] & nhip:
                loi.append(f"dòng {so_dong} · {gm} trỏ {nhan}, cảnh không mang nhịp của phần {n}")
    for gm, r in can.items():
        if gm not in co:
            loi.append(f"dòng {so_dong} · {gm} ({r['loai']}: {r['dieu'][:50]}) gieo hay gặt trong phần mà thiếu ở dòng Gieo, gặt")
        elif co[gm]:
            du += 1
    return loi, nhac, tom + f" · Gieo, gặt: {du}/{len(can)} mã đủ cảnh"


# ---------- lệnh ----------

def lenh_kiem(a: str) -> int:
    f = Path(a)
    f = f / "00-nhip.md" if f.is_dir() else f
    if not f.exists():
        print(f"LỖI: không thấy {f}")
        return 1
    loi, nhac, d = kiem_nhip(f.read_text(encoding="utf-8"))
    for dg, x in loi:
        print("LỖI:", (f"dòng {dg} · " if dg else "") + x)
    for dg, x in nhac:
        print("NHẮC:", (f"dòng {dg} · " if dg else "") + x)
    phut = " · ".join(f"{p['so']}: {p.get('phut_tinh', 0):.1f}".replace(".", ",") for p in d["phan"])
    print(f"Dàn ý: {len(d['nhip'])} nhịp ({d['phut']:.1f} phút theo cột Cảnh)".replace(".", ",") + f", {len(d['phan'])} phần (phút {phut or '—'}), "
          f"{len(d['gieo'])} dòng Gieo và gặt · {len(loi)} LỖI, {len(nhac)} NHẮC")
    return 1 if loi else 0


def lenh_phan(a: str, n: str) -> int:
    if not n.isdigit():
        print(f"LỖI: số phần '{n}' sai")
        return 1
    loi, nhac, tom = kiem_phan(Path(a), int(n))
    for x in loi:
        print("LỖI:", x)
    for x in nhac:
        print("NHẮC:", x)
    print((tom + " · " if tom else "") + f"{len(loi)} LỖI, {len(nhac)} NHẮC")
    return 1 if loi else 0


def main(arg: list[str]) -> int:
    lenh = arg[0] if arg else ""
    if lenh == "kiem" and len(arg) == 2:
        return lenh_kiem(arg[1])
    if lenh == "phan" and "--phan" in arg and (i := arg.index("--phan")) + 1 < len(arg):
        tep = arg[1:i] + arg[i + 2:]
        if len(tep) == 1:
            return lenh_phan(tep[0], arg[i + 1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
