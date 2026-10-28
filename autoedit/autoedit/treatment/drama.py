r"""Drama thoại — kịch bản hai tầng khuôn Padoma -> tập treatment. Hàm thuần.

User chốt 27/10: thêm loại phim drama có thoại, "kịch bản drama theo khuôn
Padoma" (skill `/bien-kich-grok` chép ở `skill-bien-kich/`), độ dài clip chỉ
chọn trên treatment (skill luôn ghi `Grok 15s`).

Đo thật 27/10 (scratchpad drama_thu, Grok 1.5 + tấm GPT Image 2, 2 cảnh phim
186 của Padoma): thoại đúng chữ 12/12, cắt cứng 5/5 với khuôn prompt ở
`prompt_clip`. Nên khuôn đó chép nguyên, chỉ đổi chỗ chữ do LLM viết.

Ánh xạ vào treatment (không đẻ bảng mới):
  Phần n            -> chương Cn
  Cảnh Cxxx         -> một DÒNG (`en` = tiêu đề cảnh, `vi` = "Có mặt: …")
  Clip Pxxx         -> một CẢNH (`pm` mã clip, `gi` giây, `t` chữ clip, `ts` ảnh gửi)
  Cụm cố định / Nơi -> sổ asset (nhân vật `nvNN`, nơi chốn `noiNN`)

Chia vai (luật cứng 4): kiểm khuôn là của `kiem_drama` (bản chép Padoma);
CÂU THOẠI và MỐC GIÂY từng shot là của Python — LLM không viết lại câu, không
viết mốc. Nhờ vậy đổi 15 -> 10 giây trên trang là prompt ghép lại ngay.
"""

from __future__ import annotations

import json
import re

from autoedit.treatment import kiem_drama as kd

GIAY_CHON = (6, 10, 15)      # Grok 1.5 qua Seedvis: "6s"|"10s"|"15s", cùng giá 108 credit
MODEL_VIDEO = "grok-imagine-video-1.5"     # Seedance tắt ở Seedvis từ 25/10; đo 27/10 thoại 12/12
ANH_TOI_DA = 10              # Padoma Spec 65 E.1: trần thực tế ảnh tham chiếu Grok
GIAY_MAC_DINH = 15
TU_MOT_GIAY = kd.TU_MOT_GIAY_SEEDANCE     # 3 từ/giây gồm lời nghĩ (Padoma chốt 01/10)
SHOT_TOI_THIEU = 2.5         # Padoma gv3: shot 1,5 giây có lúc ra chồng mờ

_RE_TEN = re.compile(r"^(.*?)\s*\((?:he|she|it|they)\)\s*(?:,\s*dạng\s*(\d+))?\s*$", re.I)
_RE_MOC = re.compile(r"N(\d{1,3})(?:\s*[–-]\s*N?(\d{1,3}))?")
_RE_VIET = re.compile(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", re.I)
_CAM_GROK = ("dolly zoom", "360")       # grok-phim.md mục 1: Grok làm hỏng, máy kiểm bắt


def la_tieng_viet(s: str) -> bool:
    return bool(_RE_VIET.search(s or ""))


# ───────────────────────────── phần đầu phim ─────────────────────────────────
def doc_bang(dong: list[str], tieu_de: str) -> list[list[str]]:
    """Các hàng của bảng markdown nằm dưới tiêu đề `## tieu_de` / `### tieu_de`,
    bỏ hàng tên cột và hàng `|---|`. Dừng ở tiêu đề kế tiếp."""
    ra, trong, dau = [], False, True
    for d in dong:
        s = d.strip()
        if s.startswith("#"):
            if trong:
                break
            trong = s.lstrip("#").strip().lower().startswith(tieu_de.lower())
            continue
        if not trong or not s.startswith("|"):
            continue
        o = [x.strip() for x in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", x) for x in o if x):
            continue
        if dau:                 # hàng tên cột
            dau = False
            continue
        ra.append(o)
    return ra


def _ten(o: str) -> tuple[str, int]:
    """`Tasha (she), dạng 2` -> ("Tasha", 2); `Tasha (she)` -> ("Tasha", 0)."""
    m = _RE_TEN.match(o)
    if not m:
        return o.strip(), 0
    return m.group(1).strip(), int(m.group(2) or 0)


def _moc(ghi_chu: str) -> set[int]:
    ra: set[int] = set()
    for a, b in _RE_MOC.findall(ghi_chu or ""):
        ra.update(range(int(a), int(b or a) + 1))
    return ra


def nhan_vat(dau: list[str]) -> list[dict]:
    """Cụm cố định -> nhân vật. Mỗi `dạng` (bộ đồ) là một asset riêng: tấm nhân
    vật vẽ theo cụm, đổi đồ là đổi tấm. Giọng lấy ở bảng Nhân vật, đổi đồ không
    đổi giọng."""
    giong = {}
    for h in doc_bang(dau, "Nhân vật và bối cảnh"):
        if h and h[0]:
            giong[_ten(h[0])[0].lower()] = h[3] if len(h) > 3 else ""
    ngoai = {_ten(h[0])[0].lower(): (h[2] if len(h) > 2 else "")
             for h in doc_bang(dau, "Nhân vật và bối cảnh") if h and h[0]}
    ra = []
    for h in doc_bang(dau, "Cụm cố định"):
        if len(h) < 3 or not h[0] or not h[2]:
            continue
        ten, dang = _ten(h[1])
        ma = h[0].lower() + (f"_d{dang}" if dang else "")
        ra.append({"ma": ma, "loai": "nhan_vat", "ten": ten + (f" · dạng {dang}" if dang else ""),
                   "goc": ten, "chu": h[2], "tieng": giong.get(ten.lower(), ""),
                   "yc": ngoai.get(ten.lower(), ""), "moc": _moc(h[3] if len(h) > 3 else "")})
    return ra


def noi_chon(dau: list[str]) -> list[dict]:
    """Bảng Nơi -> bối cảnh. Tên phải y từng chữ như tiêu đề cảnh (khuôn Padoma).
    `yc` = câu tả tiếng Việt: nút Sinh Asset dịch ra `chu` tiếng Anh."""
    return [{"ma": f"noi{i:02d}", "loai": "boi_canh", "ten": h[0], "yc": h[1] if len(h) > 1 else ""}
            for i, h in enumerate((h for h in doc_bang(dau, "Nơi") if h and h[0]), 1)]


def _chon_dang(nv: list[dict], ten: str, nhip: str) -> dict | None:
    """Bộ đồ của `ten` ở mốc `nhip`: dạng có ghi mốc đó, không thì bộ đầu tiên."""
    ung = [x for x in nv if x["goc"].lower() == ten.lower()]
    if not ung:
        return None
    m = re.match(r"N(\d+)", nhip or "")
    so = int(m.group(1)) if m else None
    return next((x for x in ung if so is not None and so in x["moc"]), ung[0])


# ───────────────────────────── tách cả tập ───────────────────────────────────
def _chu_clip(c: dict) -> str:
    """Chữ của clip như trong kịch bản, BỎ `Máy:` (độ dài là trường `gi`) và
    `Khung:` (người trong khung là chip asset `ts`, một chỗ sự thật)."""
    dong = [c["ten"]]
    if c["hinh"]:
        dong.append("Hình: " + c["hinh"])
    for lt in c["thoai"]:
        dong.append("Thoại: " + lt["ten"] + (f" ({lt['cach']})" if lt["cach"] else "") + ": " + lt["cau"])
    if c["loi_nghi"]:
        dong.append("Lời nghĩ: " + c["loi_nghi"]["ten"] + ": " + c["loi_nghi"]["cau"])
    return "\n".join(dong)


def tach_tap(van_ban: str) -> dict:
    """Văn bản `kich-ban.md` -> {loi, nhac, so, chuong}. Có lỗi thì KHÔNG tách
    (giao ước với skill: kịch bản lỗi không được dán)."""
    loi, nhac, phim = kd.kiem(van_ban)
    nv, noi = nhan_vat(phim["dau"]), noi_chon(phim["dau"])
    theo_noi = {x["ten"].lower(): x["ma"] for x in noi}
    ra_loi = [f"dòng {d}: {s}" if d else s for d, s in loi]
    if not nv:
        ra_loi.append("phần đầu thiếu bảng '## Cụm cố định' — không có nhân vật để vẽ tấm")
    chuong = []
    for ph in phim["phan"]:
        ds = []
        for canh in ph["canh"]:
            cs = []
            for c in canh["clip"]:
                ts = [theo_noi[canh["noi"].lower()]] if canh["noi"].lower() in theo_noi else []
                for t in c["khung"] or []:
                    x = _chon_dang(nv, t, canh["nhip"])
                    if x is None:
                        ra_loi.append(f"dòng {c['khung_dong']}: {c['ma']}: '{t}' ở Khung: không có "
                                      "trong bảng Cụm cố định — không có tấm nhân vật để gửi")
                    elif x["ma"] not in ts:
                        ts.append(x["ma"])
                cs.append({"pm": c["ma"], "gi": str(c["giay"] or GIAY_MAC_DINH),
                           "t": _chu_clip(c), "ts": ts})
            tieu = " · ".join(x for x in (canh["ma"], canh["noi"], canh["luc"], canh["nhip"]) if x)
            ds.append({"en": tieu, "vi": "Có mặt: " + ", ".join(canh["co_mat"] or []),
                       "het": 0, "canh": cs})
        dau = " · ".join(str(x) for x in (f"Phần {ph['so']}", ph["ten"],
                                           f"{ph['phut']:g} phút" if ph["phut"] else "") if x)
        chuong.append({"ma": f"C{ph['so']}", "outline": (dau + "\n\n" + ph["ghi_chu_noi"]).strip(),
                       "dong": ds})
    so = [{k: x[k] for k in ("ma", "loai", "ten", "chu", "tieng", "yc")} for x in nv] + noi
    if ra_loi:
        return {"loi": ra_loi, "nhac": [], "so": [], "chuong": []}
    return {"loi": [], "nhac": [f"dòng {d}: {s}" if d else s for d, s in nhac], "so": so,
            "chuong": chuong}


def ghep_lai(cu: dict[str, list[dict]], moi: list[dict], ma_kich_ban: set[str]) -> list[dict]:
    """Dán lại: clip cùng mã P giữ mọi thứ của máy và của người dựng (mã ảnh/video,
    task đang chạy, độ dài đã chọn, prompt sửa tay); chỉ chữ `t` và asset suy từ
    kịch bản đổi theo bản mới. Asset người dựng gán tay (đồ vật) được giữ.
    `cu` = dòng cũ của MỌI chương (clip có thể dời phần)."""
    theo_pm = {c["pm"]: c for ds in cu.values() for d in ds for c in (d.get("canh") or [])
               if isinstance(c, dict) and c.get("pm")}
    ra = []
    for d in moi:
        cs = []
        for c in d["canh"]:
            o = theo_pm.get(c["pm"])
            if o is None:
                cs.append(dict(c))
                continue
            g = dict(o)
            if o.get("t", "") != c["t"]:
                # Tăng `v` như mọi đường sửa chữ ngoài trang: tab đang mở cầm chữ
                # cũ tự lưu về thì máy chủ giữ chữ mới (`Kho.luu_tu_trang`).
                g["v"] = str(int(o.get("v") or 0) + 1)
                # Câu thoại đổi số/người: shot cũ trỏ câu không còn -> bỏ shot lẫn
                # prompt viết theo shot đó, clip về "chưa breakdown" (kiểm thử 28/10:
                # giữ lại là prompt chết IndexError). Thoại giữ nguyên thì giữ mã
                # người dựng đã chọn; prompt thành "cũ" theo dấu vết.
                if kiem_pd({"shots": doc_sh(o.get("sh"))}, c["t"]):
                    g.pop("sh", None)
                    g.pop("pd", None)
            g["t"] = c["t"]
            g["ts"] = c["ts"] + [m for m in (o.get("ts") or []) if m not in c["ts"] and m not in ma_kich_ban]
            cs.append(g)
        ra.append(dict(d, canh=cs))
    return ra


# ───────────────────────────── thoại, trần từ ────────────────────────────────
def loi_thoai(t: str) -> list[dict]:
    """Câu thoại + lời nghĩ trong chữ clip, theo thứ tự: {ten, cach, cau, nghi}.
    Câu bỏ ngoặc kép bọc ngoài — prompt tự đặt ngoặc."""
    ra = []
    for d in (t or "").splitlines():
        k, _, v = d.partition(":")
        k = k.strip().lower()
        if k not in ("thoại", "lời nghĩ"):
            continue
        lt = kd.luot(v.strip(), 0)
        ra.append({"ten": lt["ten"], "cach": lt["cach"], "cau": lt["cau"].strip().strip('"“”').strip(),
                   "nghi": k == "lời nghĩ"})
    return ra


def so_tu(t: str) -> int:
    return sum(len(kd.RE_TU.findall(x["cau"])) for x in loi_thoai(t))


def nhac_clip(t: str, giay: int) -> list[str]:
    """NHẮC (không chặn — luật cứng 5) khi độ dài đã chọn không chứa nổi thoại."""
    n, tran = so_tu(t), TU_MOT_GIAY * int(giay)
    return [f"{n} từ thoại và lời nghĩ, clip {giay} giây tối đa {tran}: tăng giây hay bớt chữ"] if n > tran else []


def chia_giay(tu: list[int], giay: int) -> list[tuple[float, float]]:
    """Mốc giây từng shot. Mỗi shot nhận ĐỦ 2,5 giây trước (chạy thật 28/10: co
    giãn tỉ lệ ép shot im xuống 2 giây), phần dư chia theo độ dài câu (~2,5
    từ/giây + một nhịp thở), làm tròn XUỐNG 0,5; chỗ lẻ cộng vào shot dài nhất.
    Không đủ chỗ cho 2,5 giây mỗi shot thì chia đều (trang đã nhắc số shot)."""
    import math

    n = len(tu)
    w = [max(SHOT_TOI_THIEU, x / 2.5 + 0.8) if x else SHOT_TOI_THIEU for x in tu]
    if n * SHOT_TOI_THIEU > giay:
        dai = [giay / n] * n
    else:
        du, con = [x - SHOT_TOI_THIEU for x in w], giay - n * SHOT_TOI_THIEU
        dai = [SHOT_TOI_THIEU + math.floor((con * d / sum(du) if sum(du) else con / n) * 2) / 2 for d in du]
        dai[max(range(n), key=lambda i: w[i])] += giay - sum(dai)
    ra, a = [], 0.0
    for x in dai:
        ra.append((a, a + x))
        a += x
    ra[-1] = (ra[-1][0], float(giay))
    return [(x if x % 1 else int(x), y if y % 1 else int(y)) for x, y in ra]


def moc_shot(shots: list[dict], t: str, giay: int) -> list[tuple[float, float]]:
    """Mốc giây từng shot theo câu thoại shot đó nói — prompt và trang cùng đọc."""
    lt = loi_thoai(t)
    tu = [sum(len(kd.RE_TU.findall(lt[c]["cau"])) for c in chi_so(s) if 0 <= c < len(lt)) for s in shots]
    return chia_giay(tu, giay) if shots else []


def so_shot_qua_day(so_shot: int, giay: int) -> bool:
    """Số shot LLM viết theo độ dài cũ không còn chỗ 2,5 giây mỗi shot ở độ dài mới."""
    return so_shot * SHOT_TOI_THIEU > int(giay)


def chi_so(s: dict) -> list[int]:
    c = s.get("cau")
    if c is None or c == "" or c == []:
        return []
    return [int(x) for x in (c if isinstance(c, list) else [c])]


def kiem_pd(pd: dict, t: str) -> list[str]:
    """Kiểm phần LLM viết ở BIÊN TIN CẬY: mỗi câu thoại đúng một lần, đúng thứ
    tự; một shot chỉ một người nói; không cú máy Grok làm hỏng."""
    lt = loi_thoai(t)
    shots = pd.get("shots") if isinstance(pd, dict) else None
    if not shots:
        return ["LLM không trả shot nào"]
    loi, seen = [], []
    try:
        for i, s in enumerate(shots, 1):
            cs = chi_so(s)
            if any(not 0 <= c < len(lt) for c in cs):
                loi.append(f"shot {i} trỏ câu không có")
                continue
            if len({lt[c]["ten"].lower() for c in cs}) > 1:
                loi.append(f"shot {i} gộp câu của hai người")
            seen += cs
            for cam in _CAM_GROK:
                if cam in str(s.get("khung") or "").lower():
                    loi.append(f"shot {i} có '{cam}' — Grok làm hỏng cú này")
    except (TypeError, ValueError):
        return ["LLM trả `cau` sai dạng"]
    if seen != list(range(len(lt))):
        thieu = [c + 1 for c in range(len(lt)) if c not in seen]
        loi.append(f"thoại chia sai: thiếu câu {thieu}" if thieu else "thoại chia sai thứ tự hay lặp câu")
    return loi


def nhac_ten(chu: str, ten) -> list[str]:
    """Tên nào trong `ten` có trong `chu` (nguyên chữ, không phân biệt hoa thường).
    Câu vị trí nhắc người ngoài khung là Grok vẽ thêm người đó (kiểm thử 28/10, P013)."""
    return [n for n in ten if n and re.search(rf"\b{re.escape(n)}\b", chu or "", re.I)]


# ───────────────────────────── ghép prompt Grok ──────────────────────────────
# Chữ cố định chép nguyên từ lượt đo 27/10 (thu.py: REF_SHEET, CHOT_SD, khối
# [SHOTS]/[SOUND] của khuôn `g_drama` Padoma).
REF_SHEET = ("use this character sheet for the face, hair, body proportions, clothing and overall identity; on the left "
             "the face in close-up, on the right the same person full length, it is ONE person, not two; ignore the text "
             "caption at the bottom of the sheet, no text ever appears in the video. Do not copy the sheet background, "
             "lighting or pose.")
CAT_CUNG = "Hard cuts only between shots, no dissolves, no cross-fades, no fade to black."
LOI_DUNG = ("Dialogue: only the LINE of each shot, spoken once, in English, by the SPEAKER of that shot, inside that "
            "shot, in shot order. No other words, no repetition, no line moves to another shot or another person.")
CHOT = "No narration, no voice-over, no melodic music, no subtitles; only the location sound and the characters' own voices."
CHOT_NGHI = ("No narration, no melodic music, no subtitles; the only voice-over is {ten}'s inner voice; otherwise only the "
             "location sound and the characters' own voices.")


def _so(x: float) -> str:
    return f"{x:g}"


def _cau_dau(chu: str) -> str:
    """Câu đầu của mô tả, chữ đầu viết thường — chêm giữa câu "Image n shows …".
    Chạy thật 28/10: chèn nguyên mô tả nơi chốn (100+ từ, kèm "Light:" trùng
    khối [LOOK]) làm [REFERENCES] loãng; Đợt 1 đạt 12/12 với một cụm ngắn."""
    s = re.split(r"(?<=[.!?])\s+|\s+Light:", (chu or "").strip(), maxsplit=1)[0].strip().rstrip(".")
    return s[:1].lower() + s[1:] if s[:1].isupper() and not s[1:2].isupper() else s   # giữ "VIP …"


def prompt_clip(pd: dict, t: str, anh: list[dict], tieng: dict[str, str], giay: int) -> str:
    """Prompt Grok của MỘT clip. `anh` = ảnh gửi đi ĐÚNG THỨ TỰ (nơi chốn, nhân
    vật, đồ vật): {loai, ten, chu}. `tieng` = tên -> câu giọng tiếng Anh."""
    lt = loi_thoai(t)
    nv = [a for a in anh if a["loai"] == "nhan_vat"]
    ten_nv = [a["ten"].split(" · ")[0] for a in nv]
    ref, nhom = [], []
    for i, a in enumerate(anh, 1):
        mo_ta = _cau_dau(a.get("chu") or a["ten"])
        if a["loai"] == "boi_canh":
            ref.append(f"Image {i} shows the location, {mo_ta}: use it for the place, light and colour only, "
                       "it is not the first frame.")
        elif a["loai"] == "nhan_vat":
            nhom.append(i)
        else:
            ref.append(f"Image {i} shows {mo_ta}: use this reference only for the object's shape, size, colour and "
                       "material; do not copy the white background or lighting.")
    if nhom:
        cau = ", ".join(f"Image {i} {'is ' if k == 0 else ''}the character sheet of {ten_nv[k]}"
                        for k, i in enumerate(nhom))
        mo = " ".join(f"{ten_nv[k]}: {(nv[k].get('chu') or '').strip().rstrip('.')}." for k in range(len(nv)))
        ref.insert(1 if anh and anh[0]["loai"] == "boi_canh" else 0, f"{cau}: {REF_SHEET} {mo}".strip())
        ref.append(f"There is exactly {' and '.join('one ' + x for x in ten_nv)} in this scene. Nobody else appears.")
    if (pd.get("size") or "").strip():
        ref.append("\n" + pd["size"].strip())

    shots = pd.get("shots") or []
    moc = moc_shot(shots, t, giay)
    dong, am, noi = [], [], []
    for i, (s, (a, b)) in enumerate(zip(shots, moc), 1):
        cs = chi_so(s)
        h = f"Shot {i} ({_so(a)}-{_so(b)}s), {str(s.get('khung') or '').strip().rstrip('.')}."
        mat = str(s.get("mat") or "").strip().rstrip(".")
        if not cs:
            dong.append(f"{h}\n  NO LINE: nobody speaks in this shot.\n  FACE AND BODY: {mat}.")
        else:
            x = lt[cs[0]]
            cau = " ".join(lt[c]["cau"] for c in cs)
            if x["nghi"]:
                ai = f"{x['ten']}'s inner voice, voice-over, {x['ten']}'s lips do not move"
                im = ten_nv
            elif x["ten"].lower() not in [n.lower() for n in ten_nv]:
                ai = (f"{x['ten']}, standing just off frame, a real voice in the scene, not a thought, "
                      "not narration, not a voice-over")
                im = ten_nv
            else:
                ai = x["ten"]
                im = [n for n in ten_nv if n.lower() != x["ten"].lower()]
            noi.append(x["ten"])
            dong.append(f"{h}\n  SPEAKER: {ai}. LINE: \"{cau}\"\n"
                        f"  DELIVERY: {str(s.get('cach') or '').strip().rstrip('.')}.\n  FACE AND BODY: {mat}."
                        + (f"\n  {' and '.join(im)}: silent, lips closed." if im else ""))
        if (s.get("am") or "").strip():
            am.append(f"Shot {i}: {s['am'].strip().rstrip('.')}")
    giong = " ".join(tieng[n] for n in dict.fromkeys(noi) if tieng.get(n))
    nghi = next((x["ten"] for x in lt if x["nghi"]), "")
    sound = (f"Bed: {str(pd.get('nen') or '').strip().rstrip('.')}." + (f" {'; '.join(am)}." if am else "")
             + f"\n{LOI_DUNG}\n" + (giong + "\n" if giong else "")
             + (CHOT_NGHI.format(ten=nghi) if nghi else CHOT))
    giu = str(pd.get("giu") or "").strip().rstrip(".")
    keep = ((f"Keep consistent: {giu}. " if giu else "")
            + (f"Exactly {', '.join('one ' + x for x in ten_nv)}, no duplicates. " if ten_nv else "")
            + "Real-time speed, no slow motion.")
    return (f"[REFERENCES]\n{' '.join(ref).replace(' ' + chr(10), chr(10))}\n\n"
            f"[SCENE AND INTENT]\n{str(pd.get('y') or '').strip()}\n\n"
            f"[LOOK]\n{str(pd.get('look') or '').strip()}\n\n"
            f"[SHOTS]\n{CAT_CUNG} {str(pd.get('truc') or '').strip()}".rstrip() + "\n" + "\n".join(dong)
            + f"\n\n[SOUND]\n{sound}\n\n[KEEP]\n{keep}")


def doc_pd(chu: str) -> dict:
    try:
        x = json.loads(chu or "{}")
    except ValueError:
        return {}
    return x if isinstance(x, dict) else {}


def doc_sh(chu: str) -> list[dict]:
    """Cột `sh` -> danh sách shot; hỏng hay vắng thì rỗng (= chưa breakdown)."""
    try:
        x = json.loads(chu or "[]")
    except ValueError:
        return []
    return [s for s in x if isinstance(s, dict)] if isinstance(x, list) else []
