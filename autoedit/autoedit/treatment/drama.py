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
from pathlib import Path

from autoedit.treatment import kiem_drama as kd
from autoedit.treatment.tai_san import LOI_REF

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


# ─────────────────── mỗi shot một video: đồng nhất phối cảnh ─────────────────
# docs/SPEC_DONG_NHAT_PHOI_CANH.md (đo 29/10, DM001 P031 lần 4: phông 3/3, hướng
# nhìn 3/3). Ảnh khung đầu mỗi shot vẽ từ MẢNH CẮT ảnh dàn cảnh; luật 180°: mọi máy
# cùng phía máy dàn cảnh, nên trái/phải trong ảnh dàn cảnh (`pd["ben"]`) quyết
# hướng nhìn và vai. Chữ chép từ `ghep_dm4.py` (ảnh) và `ghep_dm.py` (video).
BEN = ("trai", "phai", "giua")
_HOP = {"trai": (0.115, 0.30, 0.515, 0.70), "phai": (0.56, 0.30, 0.96, 0.70), "giua": (0.30, 0.30, 0.70, 0.70)}
VIEN_DEN = 12                # cột/hàng trung bình tối hơn là viền đen (P031: viền từ x≈2665/2752)
IM = "The LINE is spoken exactly once; after it, everyone stays silent and holds their expression until the end of the shot."
IM_CAM = "Nobody speaks in this shot: everyone stays silent, lips closed, for the whole shot."
MOT = "One continuous shot, no cuts."


def khung_cat(ben: str) -> tuple[float, float, float, float]:
    """Mảnh cắt mặc định quanh người ở `ben`, tỉ lệ 0–1 của ảnh dàn cảnh GỐC (trang
    cho kéo khung trên ảnh gốc). Trái/phải đo ở P031 2752 px (Nia x 316–1417),
    16:9, cùng dải dọc 0,30–0,70. `ben` lạ: giữa."""
    return _HOP.get(ben, _HOP["giua"])


def khung_mac_dinh(pd: dict, ten: str) -> tuple[float, float, float, float]:
    """Mảnh cắt mặc định của `ten` khi người dựng chưa kéo khung. Cảnh 2 người: hộp theo
    `ben` (đo P031). Cảnh từ 3 người (chạy thật C005 29/10, 4 người: hộp "giua" cắt mất
    nửa người, hộp "phai" dính người bên cạnh): chia bề ngang theo THỨ TỰ trái→phải
    `hang` — tâm (i + 0,5)/n, rộng 1/n + lề 0,02 mỗi bên, tối đa 0,4 như hộp đã đo, cùng
    tâm dọc 0,5. Rộng = cao trên tỉ lệ 0–1 là 16:9 trên ảnh dàn cảnh 16:9. Lề chọn theo
    ảnh C005 thật (Miles 0,05–0,12 · Nia 0,28–0,45 · Hattie 0,6–0,8 · Julian 0,81–0,91):
    lề 0,04 thì hộp Julian sát mép phải trùm tâm Hattie. Mới một cảnh, người dựng vẫn kéo được."""
    hang = [x for x in (pd.get("hang") or []) if isinstance(x, str)]
    if len(hang) < 3 or ten not in hang:
        return khung_cat((pd.get("ben") or {}).get(ten, "giua"))
    n, i = len(hang), hang.index(ten)
    r = min(1 / n + 0.04, 0.40)
    x0 = min(max((i + 0.5) / n - r / 2, 0.0), 1 - r)
    return (round(x0, 4), round(0.5 - r / 2, 4), round(x0 + r, 4), round(0.5 + r / 2, 4))


def cat_master(master: Path, hop, dich: Path) -> Path:
    """Cắt `hop` (x0, y0, x1, y1 tỉ lệ 0–1 của ảnh GỐC) khỏi ảnh dàn cảnh, kẹp vào
    vùng không viền đen (cột/hàng ở mép có trung bình xám < VIEN_DEN)."""
    from PIL import Image

    a = Image.open(master).convert("RGB")
    xam = a.convert("L")
    cot = xam.resize((a.width, 1), Image.BOX).tobytes()     # BOX = trung bình đúng từng cột
    hang = xam.resize((1, a.height), Image.BOX).tobytes()
    x = [i for i, v in enumerate(cot) if v >= VIEN_DEN] or [0, a.width - 1]
    y = [i for i, v in enumerate(hang) if v >= VIEN_DEN] or [0, a.height - 1]
    x0, y0, x1, y1 = hop
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    a.crop((max(round(x0 * a.width), x[0]), max(round(y0 * a.height), y[0]),
            min(round(x1 * a.width), x[-1] + 1), min(round(y1 * a.height), y[-1] + 1))).save(dich)
    return dich


def _trong(ten: str, ds) -> str:
    """Tên trong `ds` trùng `ten` không phân biệt hoa thường, viết như trong `ds`."""
    return next((x for x in ds if ten and str(x).lower() == ten.lower()), "")


def _cua(d, ten: str) -> str:
    """Giá trị của `ten` trong dict LLM viết (`ben`, `phong`, `tieng`)."""
    return next((str(v).strip() for k, v in (d if isinstance(d, dict) else {}).items()
                 if str(k).lower() == (ten or "").lower()), "")


def _nguoi_noi(s: dict, lt: list[dict]) -> str:
    cs = [c for c in chi_so(s) if 0 <= c < len(lt)]
    return lt[cs[0]]["ten"] if cs else ""


_RE_QUA_VAI = re.compile(r"qua vai\s+(\w+)", re.I)


def nguoi_tien_canh(s: dict) -> str:
    """Người ở tiền cảnh của shot qua vai: X trong "Qua vai X" của chữ shot `t`
    (Breakdown chép từ `Hình:`), viết như trong `co_mat`. Không đọc được hay X
    ngoài khung: ""."""
    m = _RE_QUA_VAI.search(str(s.get("t") or ""))
    return _trong(m.group(1), s.get("co_mat") or []) if m else ""


def chu_the(s: dict, lt: list[dict]) -> str:
    """Người máy hướng tới (S): `huong` người dựng chọn, rồi người nói của shot,
    rồi người duy nhất trong khung — cả ba phải có trong `co_mat`. Shot qua vai
    bỏ người tiền cảnh ra trước (DM002 C1 29/10: 8/13 shot qua vai chọn trúng
    người nói đang quay lưng, hoặc rỗng vì shot im). Chưa rõ thì "" (app dùng
    nguyên ảnh dàn cảnh; `nhac_qua_vai` nhắc người dựng)."""
    co = s.get("co_mat") or []
    tien = nguoi_tien_canh(s) if s.get("goc") == "ots" else ""
    con = [x for x in co if x.lower() != tien.lower()] if tien else co
    return (_trong(str(s.get("huong") or ""), co) or _trong(_nguoi_noi(s, lt), con)
            or (con[0] if len(con) == 1 else ""))


def ca_canh(s: dict) -> bool:
    """Hai người trở lên trong khung mà không qua vai: Image 1 là NGUYÊN ảnh dàn cảnh."""
    return len(s.get("co_mat") or []) >= 2 and s.get("goc") != "ots"


def giay_shot(s: dict, lt: list[dict]) -> int:
    """`gi` người dựng chọn; không có thì 6 giây, câu cần hơn ~5 giây (3 từ/giây
    + 1 giây) thì 10 (`ghep_dm.py`, đo DM001)."""
    try:
        g = int(s.get("gi") or 0)
    except (TypeError, ValueError):
        g = 0
    if g in GIAY_CHON:
        return g
    tu = sum(len(kd.RE_TU.findall(lt[c]["cau"])) for c in chi_so(s) if 0 <= c < len(lt))
    return 10 if tu / TU_MOT_GIAY + 1 > 5 else 6


def nhac_lap(lap: str) -> list[str]:
    """NHẮC (không chặn — luật cứng 5) khi câu khung tả phông. Phông lấy từ ảnh
    dàn cảnh; LLM tả theo khung hình là sai chỗ (P031 lần 2: sofa sau lưng Nia)."""
    if re.search(r"\bbehind\b", lap or "", re.I):
        return ["câu khung tả thứ sau lưng ('behind'): phông lấy từ ảnh dàn cảnh, nên bỏ cụm này"]
    return []


def nhac_qua_vai(s: dict, lt: list[dict]) -> list[str]:
    """NHẮC (không chặn — luật cứng 5) shot qua vai mà người dựng chưa chọn
    `huong` và máy chưa rõ hướng tới ai."""
    if s.get("goc") != "ots" or _trong(str(s.get("huong") or ""), s.get("co_mat") or []):
        return []
    if not nguoi_tien_canh(s):
        return ["không đọc được \"Qua vai X\" trong chữ shot nên máy đang đoán hướng: chọn ở ô Máy hướng tới"]
    if not chu_the(s, lt):
        return ["shot qua vai không có người ở xa trong khung: chọn ở ô Máy hướng tới hoặc sửa Trong khung"]
    return []


TAM_BEN = {"trai": 0.2, "giua": 0.5, "phai": 0.8}   # chỗ đứng ƯỚC theo `ben` (DM002: Hattie≈0,15 Brooke≈0,43 Evelyn≈0,87)
NUA_NGUOI = 0.08             # nửa bề ngang một người trong ảnh dàn cảnh (DM002: Brooke x 0,344–0,51)


def _khung_cua(pd: dict, ten: str) -> tuple:
    """Khung cắt app dùng cho `ten`, như `_hop` của app: người dựng kéo thì theo đó, chưa thì theo `ben`."""
    hop = (pd.get("cat") or {}).get(ten)
    return tuple(hop) if hop else khung_cat((pd.get("ben") or {}).get(ten, "giua"))


def nhac_khung(pd: dict, s: dict, lt: list[dict]) -> list[str]:
    """NHẮC (không chặn — luật cứng 5) khi mảnh cắt quanh S có thể dính người KHÔNG có trong
    shot mà shot lại phải vẽ thêm người: model đem người dính đó làm người còn lại (P004 shot 4,
    29/10: khung Hattie dính Brooke đứng giữa -> Evelyn ĐỨNG cạnh Hattie, thêm một người lạ).
    Shot một người không nhắc: 7/7 ảnh Hattie một mình ở DM002 vẫn sạch dù mảnh cắt dính Brooke.
    Chỗ đứng ƯỚC: tâm khung người dựng đã kéo, chưa kéo thì `TAM_BEN`, ± `NUA_NGUOI`."""
    ai, co = chu_the(s, lt), s.get("co_mat") or []
    if not ai or ca_canh(s) or len(co) < 2:
        return []
    x0, _, x1, _ = _khung_cua(pd, ai)
    trong = {str(x).lower() for x in co}
    dinh = []
    for ten, b in (pd.get("ben") or {}).items():
        hop = (pd.get("cat") or {}).get(ten)
        c = (hop[0] + hop[2]) / 2 if hop else TAM_BEN.get(b, 0.5)
        if ten.lower() not in trong and c - NUA_NGUOI < x1 and c + NUA_NGUOI > x0:
            dinh.append(ten)
    return [f"mảnh cắt quanh {ai} có thể dính {', '.join(dinh)} (không có trong shot): kéo khung {ai} ở ô "
            "dàn cảnh cho sạch"] if dinh else []


def _phia_nhin(pd: dict, ai: str, toi: str) -> str:
    """Phía `ai` nhìn để thấy `toi` ("right"/"left"/""). Luật 180°: người bên trái
    ảnh dàn cảnh nhìn phải và ngược lại; người ở giữa nhìn về phía người kia."""
    b = _cua(pd.get("ben"), ai)
    if b == "giua":
        return {"trai": "left", "phai": "right"}.get(_cua(pd.get("ben"), toi), "")
    return {"trai": "right", "phai": "left"}.get(b, "")


def _nguoi_kia(s: dict, lt: list[dict], ai: str, nguoi) -> str:
    """O — người S nhìn tới. Qua vai: người tiền cảnh ("Qua vai X"), rồi người còn
    lại trong `co_mat`. Còn lại: người nói của shot nếu không phải S, rồi người đầu
    tiên khác S có tấm trong clip (thứ tự `nguoi`). `pd.shots` không mang `cau` nên
    không dò shot kề bên: hai người thì như nhau; ba người trở lên CHƯA ĐO."""
    ds = ([nguoi_tien_canh(s)] + list(s.get("co_mat") or []) if s.get("goc") == "ots" else []) \
        + [_nguoi_noi(s, lt)] + list(nguoi)
    return next((x for x in ds if x and x.lower() != ai.lower()), "")


def _cau_nhin(pd: dict, s: dict, ai: str, kia: str) -> str:
    """Câu hướng nhìn (L5): ảnh và video cùng dùng. Shot nhiều người không qua vai: không có."""
    if not (ai and kia) or ca_canh(s):
        return ""
    p = _phia_nhin(pd, ai, kia)
    if s.get("goc") == "ots":
        return f"{ai} looks at {kia}" + (f", toward the {p} of the frame" if p else "") + ", not at the camera."
    return f"{ai} looks toward {kia}" + (f", just off the {p} edge of the frame" if p else "") + ", not at the camera."


def _hoa(x: str) -> str:
    x = (x or "").strip()
    return x[:1].upper() + x[1:]


def _cham(x: str) -> str:
    x = (x or "").strip()
    return x if not x or x.endswith((".", "!", "?")) else x + "."


def _ps(pd: dict, k: int) -> dict:
    ds = pd.get("shots") or []
    return ds[k] if 0 <= k < len(ds) and isinstance(ds[k], dict) else {}


def prompt_dan_canh(pd: dict, nguoi: list[dict], noi: dict | None) -> str:
    """Prompt ẢNH DÀN CẢNH (WS) của một cảnh. Ảnh gửi: [nơi chốn nếu có] + tấm
    `nguoi` đúng thứ tự. Câu `phong` từng người vào luôn ảnh này: ảnh shot sau
    nói "Behind S: …, exactly as in Image 1", ảnh dàn cảnh phải có đúng thứ đó."""
    ten = [x["ten"].split(" · ")[0] for x in nguoi]
    loai = (["boi_canh"] if noi else []) + ["nhan_vat"] * len(nguoi)
    sau = [f"Behind {n}: {_cham(_cua(pd.get('phong'), n))}" for n in ten if _cua(pd.get("phong"), n)]
    mo_ta = " ".join(f"{n}: {str(x.get('chu') or '').strip().rstrip('.')}." for n, x in zip(ten, nguoi))
    khoi = [f"{_cham(pd.get('dan'))} Photorealistic film still, 16:9.".strip(),
            " ".join(LOI_REF[x].format(i=i) for i, x in enumerate(loai, 1)),
            " ".join(sau + [str(pd.get("cho") or "").strip()]).strip(),
            " ".join(x for x in (mo_ta, f"Exactly {' and '.join('one ' + n for n in ten)}, nobody else." if ten
                                 else "") if x),
            str(pd.get("look") or "").strip()]
    return "\n\n".join(x for x in khoi if x)


def prompt_anh_shot(pd: dict, s: dict, k: int, t: str, nguoi: dict[str, dict], do: list[dict], kh: str) -> str:
    """Prompt ẢNH KHUNG ĐẦU shot `k` (tính từ 0) — khuôn `ghep_dm4.py`.

    `s` = sh[k]; `nguoi` = {Tên: mục sổ} mọi người có tấm trong clip; `kh` = câu
    khung KHÔNG có máy (`khung_shot(dict(s, cd=""))`). Ảnh gửi đúng thứ tự:
      1. mảnh cắt quanh `chu_the`, hay NGUYÊN ảnh dàn cảnh khi `ca_canh(s)` hoặc
         `chu_the` rỗng;
      2. tấm từng tên trong `s["co_mat"]` có trong `nguoi`, đúng thứ tự;
      3. `do`.
    Câu `truc` của LLM KHÔNG vào đây (L6: viết theo khung hình, vẽ thêm người)."""
    lt = loi_thoai(t)
    ai = chu_the(s, lt)
    co = list(s.get("co_mat") or [])
    ots = s.get("goc") == "ots"
    kia = _nguoi_kia(s, lt, ai, nguoi) if ai else ""
    mat = str(_ps(pd, k).get("mat") or "").strip().rstrip(".")
    cho = str(pd.get("cho") or "").strip()
    if ca_canh(s) or not ai:
        loi = [LOI_REF["truong_doan"].format(i=1)]
        may = [cho]
    else:
        # `vi_tri` (chỗ riêng từng người theo đồ đạc) cho lại đúng chữ bản đo; vắng thì chữ chung
        cho_s, cho_o = _cua(pd.get("vi_tri"), ai), _cua(pd.get("vi_tri"), kia)
        loi = ["Image 1 is a crop of the master wide shot of this scene" + (f": {ai} {cho_s}." if cho_s else
               f", around {ai}.") + " Keep this exact room, background and light; it is the same moment."]
        if ots:
            # vai PHÍA MÁY DÀN CẢNH: O nhìn sang trái (đứng bên phải) thì tay phải chỉ ra xa
            # máy, máy đứng sau vai trái; nhìn sang phải thì vai phải (bản đo P031 ghi ngược)
            vai = {"right": "right ", "left": "left "}.get(_phia_nhin(pd, kia, ai), "")
            gan = f"just behind {kia}'s {vai}shoulder, " if kia else ""
        else:
            gan = (f"near {kia}'s place {cho_o}, " if cho_o else f"near {kia}, ") if kia else ""
        may = [f"Camera position: on the same side of the room as the master shot, {gan}angled toward {ai}."]
        phong = re.split(r"(?<=[.!?])\s+", _cua(pd.get("phong"), ai), maxsplit=1)
        if phong[0]:
            may.append(f"Behind {ai}: {phong[0].rstrip('.')}, exactly as in Image 1."
                       + (f" {_cham(phong[1])}" if len(phong) > 1 else ""))
        if kia and not ots:
            p = _phia_nhin(pd, ai, kia)
            may.append(f"{kia} is off-screen" + (f" to the {p}" if p else "") + " and does not appear.")
        may.append(cho)
    tam = [n for n in co if n in nguoi]
    loi += [LOI_REF["nhan_vat"].format(i=i) for i in range(2, 2 + len(tam))]
    loi += [LOI_REF.get(d.get("loai"), LOI_REF["dao_cu"]).format(i=i) for i, d in enumerate(do, 2 + len(tam))]
    phan = str(pd.get("giu") or "").strip().rstrip(".").split(";")
    giu = "; ".join(c.strip() for n in co for c in phan if nhac_ten(c, [n]))
    nguoi_khung = " ".join(x for x in (
        " ".join(f"{n}: {str(nguoi[n].get('chu') or '').strip().rstrip('.')}." for n in tam),
        f"Keep consistent: {giu}." if giu else "",
        f"Exactly {' and '.join('one ' + n for n in co)} in frame, nobody else." if co else "Nobody in frame.") if x)
    khoi = [" ".join(x for x in (_hoa(kh), f"{mat}." if mat else "", _cau_nhin(pd, s, ai, kia),
                                  "Photorealistic film still, 16:9.") if x),
            " ".join(loi), " ".join(x for x in may if x), nguoi_khung, str(pd.get("look") or "").strip()]
    return "\n\n".join(x for x in khoi if x)


def prompt_video_shot(pd: dict, s: dict, k: int, t: str, nguoi: dict[str, dict], tieng: dict[str, str],
                      do: list[dict], kh: str, may: str, giay: int) -> str:
    """Prompt Grok i2v của shot `k` (tính từ 0), từ ảnh khung đầu đã duyệt —
    khuôn `ghep_dm.py`, câu hướng nhìn chèn ngay sau dòng mặt/thân (L7, như
    `ghep_dm4.py`). `may` = câu máy (CD_DRAMA). `do` chưa dùng: i2v chỉ nhận ảnh
    khung đầu, đồ vật đã nằm trong ảnh. Người nói ngoài khung / lời nghĩ: chữ
    của `prompt_clip` (đo 27/10)."""
    lt = loi_thoai(t)
    co = list(s.get("co_mat") or [])
    ai = chu_the(s, lt)
    kia = _nguoi_kia(s, lt, ai, nguoi) if ai else ""
    ps = _ps(pd, k)
    cs = [c for c in chi_so(s) if 0 <= c < len(lt)]
    mat = str(ps.get("mat") or "").strip().rstrip(".")
    mat_ai = ai or _nguoi_noi(s, lt) or (co[0] if co else "")
    if mat and mat_ai and not any(mat.lower().startswith(n.lower()) for n in co):
        mat = f"{mat_ai}: {mat[:1].lower() + mat[1:]}"
    dong = [" ".join(x for x in (may.strip(), _hoa(kh), f"Continue this camera move for the full {giay} seconds.") if x)]
    dong += [x for x in (f"{mat}." if mat else "", _cau_nhin(pd, s, ai, kia)) if x]
    if cs:
        x = lt[cs[0]]
        if x["nghi"]:
            noi, im = f"{x['ten']}'s inner voice, voice-over, {x['ten']}'s lips do not move", co
        elif not _trong(x["ten"], co):
            noi, im = (f"{x['ten']}, standing just off frame, a real voice in the scene, not a thought, "
                       "not narration, not a voice-over"), co
        else:
            noi, im = x["ten"], [n for n in co if n.lower() != x["ten"].lower()]
        cach = str(ps.get("cach") or "").strip().rstrip(".")
        dong += [f"SPEAKER: {noi}. LINE: \"{' '.join(lt[c]['cau'] for c in cs)}\""]
        dong += [x for x in (f"DELIVERY: {cach}." if cach else "",
                             f"{' and '.join(im)}: silent, lips closed." if im else "") if x]
        giong = _cua(tieng, x["ten"])
        cuoi = (f"Dialogue: only this LINE, spoken once, in English, by {x['ten']}. "
                + (CHOT_NGHI.format(ten=x["ten"]) if x["nghi"] else CHOT))
        dong += [IM, MOT]
    else:
        giong, cuoi = "", f"No dialogue in this shot. {CHOT}"
        dong += [IM_CAM, MOT]
    am = "; ".join(x for x in (str(pd.get("nen") or "").strip().rstrip("."),
                               str(ps.get("am") or "").strip().rstrip(".")) if x)
    return "\n".join(dong) + "\n\n" + "\n".join(x for x in (giong, f"Sound: {am}." if am else "", cuoi) if x)
