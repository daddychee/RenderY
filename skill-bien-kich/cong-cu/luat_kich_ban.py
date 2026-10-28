# File chép từ app/kiem_kich_ban.py của repo GEN VIDEO bằng kiem-chung/dong_bo_skill_phim.py. Không sửa tay.
"""Khuôn kịch bản phim (Spec 22 B2, Spec 27 D): kiểm và tách. **Khuôn là giao ước giữa hai repo:** đổi khuôn thì đổi cả agent kịch bản và app.

Hai đường dùng chung các hàm kiểm:
- `cong-cu/kiem_kich_ban.py` của thư mục `skill lam phim` (bản chép `luat_kich_ban.py`): đọc thư mục `kich-ban/` (`00-nhip.md`, `hoi-*.md`), nhãn lỗi là tên file.
- Trang Phim mới (`app/routes/phim_moi.py`): editor dán nguyên bản gộp `kich-ban.md`; `kiem_van_ban` tách phần đầu, từng `# Hồi n`, phần hậu kỳ,
  báo lỗi kèm số dòng trong ô dán; `tach_phim` lấy tên, thể loại, lời bình và từng cảnh `## Pxx · tên · 15s · Nyy`.
Kiểm máy được: mã nhịp liên tục, "Vì nhịp" và "Trả ở" trỏ tới nhịp có thật và đúng chiều, mọi ô "Gieo" có "Trả ở", mô típ có gieo và trả,
mỗi nhịp có ít nhất một phân cảnh (tới nhịp lớn nhất đã dùng), ô `Clip:` của dòng cấp phim chỉ 15s hay 30s (Spec 55 C),
mã phân cảnh liên tục không trùng, mỗi hồi có hai mục bắt buộc, thời lượng trong bộ `gia_credit.GIAY_PHIM` (10 tới 30; Spec 29 H), tổng giây từng hồi so với dòng `Ngân sách: hồi 1 270s · hồi 2 810s …` (lệch quá 15% thì lỗi),
mã thủ pháp `TPxx` có trong kho, cú WOW (dòng kho có "Điểm nhấn:") cả phim tối đa 3 và không hai cảnh liền nhau
(Spec 34; chỉ bản skill, đọc bản xuất `kho-thu-phap.md`), thoại mỗi nhịp tối đa 3 từ một giây và phải trong ngoặc kép (`kiem_thoai`, chỉ bản skill).
`luat_chung`: ba luật viết prompt mức cảnh báo (Spec 34 K4), web gọi ở `kiem_prompt_phim` và `bang_tai_san`, skill gọi từng dòng kịch bản;
kèm nhắc chữ dễ bị chặn khi có trẻ em (Spec 35 G, `TU_CHAN`; web viết prompt kiểm mức lỗi ở `viet_prompt`).
`than_sinh_vat`: cụm có cánh mà không ghi số chân (Spec 34 K7), skill kiểm bảng Cụm cố định, web kiểm bảng tài sản.
Chỉ import `app.gia_credit` (không phụ thuộc gì) để script ngoài venv chạy được. Lỗi là cặp (số dòng hoặc None, câu); script chỉ in câu."""
import re

GIAY_PHIM = (10, 15, 20, 25, 30)  # giá trị app/gia_credit.GIAY_PHIM lúc đồng bộ

RE_NHIP = re.compile(r"^N\d{2,3}$")
RE_CANH = re.compile(r"^## (P\d{2,3})\b(.*)$")
RE_GIAY = re.compile(r"\b(\d{1,3})s\b")
RE_MA_NHIP = re.compile(r"\bN\d{2,3}\b")
RE_HOI = re.compile(r"^# Hồi\s+(\d+)\s*[:.·-]?\s*(.*)$", re.I)
RE_NGAN_SACH = re.compile(r"hồi\s*(\d+)\s+(\d+)s")
RE_GIONG = re.compile(r"\b(elevenlabs_\w+|minimax_\w+|openai_\w+)\b")
RE_MA_TP = re.compile(r"\bTP\d{2,3}\b")
RE_DONG_KHO = re.compile(r"^- (TP\d{2,3}) · ")
GIAY_CHO_PHEP = set(GIAY_PHIM)
LECH_CHO_PHEP = 0.15
DAU_WOW = "Điểm nhấn:"      # dấu cú WOW trong ô "dùng khi" của kho thủ pháp
TRAN_WOW = 3
MUC_HOI = ("Để viết hồi sau", "Bảng trạng thái liên tục")

Loi = tuple[int | None, str]


def dong_cap_phim(dong: list[str]) -> tuple[int | None, dict[str, str]]:
    """Dòng `Thể loại: … · Dài: … · Lời bình: … · Clip: 30s` của phần đầu → (chỉ số dòng hoặc None, {khóa chữ thường: giá trị})."""
    for i, d in enumerate(dong):
        if d.lower().startswith("thể loại"):
            return i, {p.split(":", 1)[0].strip().lower(): p.split(":", 1)[1].strip() for p in d.split(" · ") if ":" in p}
    return None, {}


def clip_phim(o_dau: dict[str, str]) -> int | None:
    """Ô `Clip:` (Spec 55 C): vắng là 15; "15s", "30s" thành số; ghi khác thì None (lỗi kiểm)."""
    return {"15s": 15, "30s": 30}.get(o_dau.get("clip", "15s").lower().replace(" ", ""))


def kiem_clip(nhan: str, dong: list[str], loi: list[Loi], dong0: int = 0) -> None:
    i, o_dau = dong_cap_phim(dong)
    if i is not None and clip_phim(o_dau) is None:
        loi.append((dong0 + i + 1, f"{nhan}: Clip chỉ ghi 15s hay 30s"))


def ngan_sach(dong: list[str]) -> dict[int, int]:
    """Dòng `Ngân sách: hồi 1 270s · hồi 2 810s …` ở phần đầu → {số hồi: giây}; không có thì {}."""
    for d in dong:
        if d.lower().startswith("ngân sách"):
            return {int(h): int(g) for h, g in RE_NGAN_SACH.findall(d)}
    return {}


def bang(dong_md: list[str], ten_muc: str) -> list[dict]:
    """Các hàng của bảng markdown ngay dưới mục `## <ten_muc>`; mỗi hàng là dict cột → ô, thêm "_dong" (chỉ số dòng, từ 0)."""
    hang, cot, trong = [], None, False
    for i, d in enumerate(dong_md):
        if d.startswith("## "):
            trong = d[3:].strip().lower().startswith(ten_muc.lower())
            cot = None
            continue
        if not trong or not d.startswith("|"):
            continue
        o = [x.strip() for x in d.strip().strip("|").split("|")]
        if cot is None:
            cot = o
        elif all(set(x) <= set("-: ") for x in o):
            continue
        else:
            hang.append({**dict(zip(cot, o)), "_dong": i})
    return hang


def kiem_nhip(nhan: str, dong: list[str], loi: list[Loi], dong0: int = 0) -> list[str]:
    """Bảng nhịp và bảng mô típ của phần đầu. Trả danh sách mã nhịp. dong0: số dòng (từ 0) của dòng đầu `dong` trong văn bản gốc."""
    nhip = bang(dong, "Bảng nhịp")
    ma = [h.get("Mã", "") for h in nhip]
    if not ma:
        loi.append((dong0 + 1, f"{nhan}: không có bảng nhịp (mục '## Bảng nhịp' với cột Mã)"))
        return []

    def them(h: dict, cau: str):
        loi.append((dong0 + h["_dong"] + 1, f"{nhan}: {cau}"))
    for i, h in enumerate(nhip, 1):
        m = h.get("Mã", "")
        if not RE_NHIP.match(m):
            them(h, f"mã nhịp '{m}' sai dạng (N01, N02…)")
        elif int(m[1:]) != i:
            them(h, f"mã nhịp {m} không liên tục (chờ N{i:02d})")
    co = set(ma)
    for h in nhip:
        m = h.get("Mã", "")
        vi = h.get("Vì nhịp", "").strip()
        for v in RE_MA_NHIP.findall(vi):
            if v not in co:
                them(h, f"{m} 'Vì nhịp' {v} không có trong bảng")
            elif v >= m:
                them(h, f"{m} 'Vì nhịp' {v} phải là nhịp trước")
        if vi and vi not in ("–", "-", "—") and not RE_MA_NHIP.search(vi):
            them(h, f"{m} 'Vì nhịp' phải là mã nhịp hoặc –")
        gieo, tra = h.get("Gieo", "").strip(), h.get("Trả ở", "").strip()
        if gieo and not RE_MA_NHIP.search(tra):
            them(h, f"{m} có gieo '{gieo[:30]}' nhưng 'Trả ở' trống hay không phải mã nhịp")
        for t in RE_MA_NHIP.findall(tra):
            if t not in co:
                them(h, f"{m} 'Trả ở' {t} không có trong bảng")
            elif t <= m:
                them(h, f"{m} 'Trả ở' {t} phải là nhịp sau")
        muc = h.get("Mức", "").strip()
        if muc and not (muc.isdigit() and 1 <= int(muc) <= 5):
            them(h, f"{m} 'Mức' phải từ 1 đến 5")
    for h in bang(dong, "Mô típ"):
        ten = h.get("Mô típ", "")[:30]
        for cot in ("Gieo ở", "Trả ở"):
            ds = RE_MA_NHIP.findall(h.get(cot, ""))
            if not ds:
                them(h, f"mô típ '{ten}' thiếu '{cot}'")
            for t in ds:
                if t not in co:
                    them(h, f"mô típ '{ten}' '{cot}' {t} không có trong bảng nhịp")
    return ma


def kiem_hoi(nhan: str, so_hoi: int, dong: list[str], ma_nhip: list[str], loi: list[Loi], ngan_sach_hoi: dict[int, int],
             dong0: int = 0, ten_nhip: str = "00-nhip.md") -> tuple[list[tuple[str, int]], set[str], str]:
    """Một hồi. Trả (các cảnh (mã, số dòng), các nhịp đã dùng, dòng tóm tắt số cảnh và tổng giây)."""
    muc = {d[3:].strip().lower() for d in dong if d.startswith("## ")}
    for ten in MUC_HOI:
        if not any(m.startswith(ten.lower()) for m in muc):
            loi.append((dong0 + 1, f"{nhan}: thiếu mục '## {ten}'"))
    canh, nhip_dung, tong_giay = [], set(), 0
    for i, d in enumerate(dong):
        k = RE_CANH.match(d)
        if not k:
            continue
        p, phan, so_dong = k.group(1), k.group(2), dong0 + i + 1
        canh.append((p, so_dong))
        g = RE_GIAY.search(phan)
        if not g:
            loi.append((so_dong, f"{nhan}: {p} thiếu thời lượng (… · 15s · …)"))
        elif int(g.group(1)) not in GIAY_CHO_PHEP:
            loi.append((so_dong, f"{nhan}: {p} thời lượng {g.group(1)}s ngoài bộ {'/'.join(map(str, sorted(GIAY_CHO_PHEP)))}"))
        else:
            tong_giay += int(g.group(1))
        n = RE_MA_NHIP.findall(phan)
        if not n:
            loi.append((so_dong, f"{nhan}: {p} thiếu mã nhịp ở tiêu đề"))
        for x in n:
            if ma_nhip and x not in ma_nhip:
                loi.append((so_dong, f"{nhan}: {p} nhịp {x} không có trong {ten_nhip}"))
            nhip_dung.add(x)
    if not canh:
        loi.append((dong0 + 1, f"{nhan}: không có phân cảnh nào (dòng '## P01 · tên · 15s · N01')"))
    ns = ngan_sach_hoi.get(so_hoi)
    if ns:
        lech = (tong_giay - ns) / ns
        tom = f"{nhan}: {len(canh)} cảnh, {tong_giay}s / ngân sách {ns}s ({lech:+.0%})"
        if abs(lech) > LECH_CHO_PHEP:
            loi.append((dong0 + 1, f"{nhan}: {'hụt' if lech < 0 else 'vượt'} ngân sách {tong_giay}s so với {ns}s (quá {LECH_CHO_PHEP:.0%})"))
    else:
        tom = f"{nhan}: {len(canh)} cảnh, {tong_giay}s"
    return canh, nhip_dung, tom


def ma_kho(ban_xuat: str) -> set[str]:
    """Mã thủ pháp dùng được trong bản xuất kho (Spec 34 F3, dòng `- TPxx · …`; thủ pháp hỏng ghi `- Đừng dùng TPxx` nên không tính)."""
    return {m.group(1) for d in ban_xuat.splitlines() if (m := RE_DONG_KHO.match(d))}


def kiem_thu_phap(nhan: str, dong: list[str], ma_co: set[str], loi: list[Loi], dong0: int = 0) -> None:
    """Mã `TPxx` ghi trong hồi phải có trong kho thủ pháp (Spec 34 F3). Bản skill truyền `ma_kho(kho-thu-phap.md)`; web cảnh báo trên thẻ cảnh."""
    for i, d in enumerate(dong):
        for m in dict.fromkeys(RE_MA_TP.findall(d)):
            if m not in ma_co:
                loi.append((dong0 + i + 1, f"{nhan}: thủ pháp {m} không có trong kho (kien-thuc/tu-web/kho-thu-phap.md), hoặc đã hỏng"))


def ma_wow(ban_xuat: str) -> set[str]:
    """Mã cú WOW trong bản xuất kho: dòng dùng được có `DAU_WOW` ở ô "dùng khi" (ô thứ ba, Spec 34 mục H). Cú WOW nạp sau tự được tính."""
    return {m.group(1) for d in ban_xuat.splitlines()
            if (m := RE_DONG_KHO.match(d)) and len(o := d.split(" · ")) > 2 and DAU_WOW in o[2]}


def tp_canh(nhan: str, dong: list[str], dong0: int = 0) -> list[tuple[str, int, list[str]]]:
    """Từng cảnh của một hồi: (nhãn, số dòng tiêu đề, các mã TPxx trong cảnh). Mã nằm ngoài cảnh (trước P đầu, trong mục khác) không tính."""
    ra, trong = [], False
    for i, d in enumerate(dong):
        if d.startswith("## "):
            k = RE_CANH.match(d)
            trong = bool(k)
            if k:
                ra.append((f"{nhan} {k.group(1)}", dong0 + i + 1, []))
            continue
        if trong:
            ra[-1][2].extend(m for m in RE_MA_TP.findall(d) if m not in ra[-1][2])
    return ra


def kiem_wow(canh: list[tuple[str, int, list[str]]], wow: set[str], loi: list[Loi]) -> None:
    """Cú WOW (Spec 34 mục H): cả phim tối đa TRAN_WOW cảnh, không hai cảnh liền nhau (kể cả qua hồi). `canh` là `tp_canh` của mọi hồi nối lại."""
    co = [(i, n, so, [m for m in tp if m in wow]) for i, (n, so, tp) in enumerate(canh)]
    co = [x for x in co if x[3]]
    if len(co) > TRAN_WOW:
        loi.append((co[TRAN_WOW][2], f"{len(co)} cảnh dùng cú WOW, cả phim tối đa {TRAN_WOW}: "
                                     + ", ".join(f"{n} ({'/'.join(m)})" for _, n, _, m in co)))
    for a, b in zip(co, co[1:]):
        if b[0] == a[0] + 1:
            loi.append((b[2], f"{a[1]} và {b[1]} liền nhau đều dùng cú WOW ({'/'.join(a[3])}, {'/'.join(b[3])}); chèn cảnh thường giữa"))


# ----- Tốc độ thoại (chốt 01/10/2026): câu dài trong nhịp ngắn thì Seedance nói vội. Phim 173 và 184: 34/229 clip, có shot 5–8 từ/giây.
TU_THOAI_MOT_GIAY = 3
RE_KHOANG_NHIP = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*[–—-]\s*(\d+(?:[.,]\d+)?)\s*s\b")
RE_NGOAC_KEP = re.compile(r'"([^"]*)"|“([^”]*)”')
RE_TU_ANH = re.compile(r"[A-Za-z][A-Za-z'’-]*")
# Thoại thiếu ngoặc kép: chữ chỉ việc nói, dấu hai chấm, rồi ít nhất 3 từ tiếng Anh có một từ thường gặp (đo trên 2.377 cảnh trong DB, không báo nhầm)
RE_NOI_HAI_CHAM = re.compile(r"(?:nói|hỏi|gọi|thầm|gào|hét|quát|rít|đáp|lẩm bẩm|thét|giọng|bảo|kêu|ra lệnh|thốt|nhắc|says?|whispers?|shouts?)"
                             r"[^:→]{0,40}:\s*([^:]+)", re.I)
TU_ANH_THUONG = set("i you we he she it they me my your our his her the a an is are was be to of and not don't can't i'm it's that's "
                    "this that here now what no yes go come get let will have just".split())


def kiem_thoai(nhan: str, dong: list[str], loi: list[Loi], dong0: int = 0) -> None:
    """Ô "Hành động theo nhịp" từng cảnh: thoại (trong ngoặc kép) của một nhịp tối đa TU_THOAI_MOT_GIAY từ một giây;
    thoại viết không ngoặc kép là lỗi vì máy không đếm được. Chỉ skill gọi (web không chặn khi dán)."""
    p, so = None, 0
    for i, d in enumerate(dong):
        if d.startswith("## "):
            k = RE_CANH.match(d)
            p, so = (k.group(1), dong0 + i + 1) if k else (None, 0)
            continue
        if not p or "Hành động theo nhịp" not in d:
            continue
        for doan in _o([d], "Hành động theo nhịp").split("→"):
            m = RE_KHOANG_NHIP.match(doan)
            if not m:
                continue
            a, b = (float(x.replace(",", ".")) for x in m.groups())
            than = doan[m.end():]
            tu = sum(len(RE_TU_ANH.findall(x or y)) for x, y in RE_NGOAC_KEP.findall(than))
            nhip = f"{m.group(1)}–{m.group(2)}s"
            if b > a and tu > TU_THOAI_MOT_GIAY * (b - a):
                loi.append((so, f"{nhan}: {p} nhịp {nhip} thoại {tu} từ cho {b - a:g} giây (tối đa {TU_THOAI_MOT_GIAY} từ một giây): "
                                f"kéo dài nhịp hay tách câu, không kéo sang shot sau"))
            ngoai = re.sub(r"\([^)]*\)", " ", RE_NGOAC_KEP.sub(" ¶ ", than))
            for k in RE_NOI_HAI_CHAM.finditer(ngoai):
                chuoi = []
                for t in k.group(1).split():
                    w = t.strip(".,!?;…—–-")
                    if w and re.fullmatch(r"[A-Za-z'’-]+", w):
                        chuoi.append(w.lower().replace("’", "'"))
                    elif w:
                        break
                if len(chuoi) >= 3 and any(w in TU_ANH_THUONG for w in chuoi):
                    loi.append((so, f"{nhan}: {p} nhịp {nhip} thoại không trong ngoặc kép ('{' '.join(chuoi[:5])}…'): viết \"câu\""))
                    break


# ----- Spec 34 K4: ba luật chung viết prompt, chỉ cảnh báo. Đọc chữ tiếng Anh: prompt video (web, `kiem_prompt_phim`), hằng và tài sản
# nhân vật (`bang_tai_san`), cụm tiếng Anh trong kịch bản (bản skill). Regex siết theo prompt thật phim 156 đến 163 (25/09).
_SINH_VAT = ("man|woman|men|women|boy|girl|child|children|kid|person|people|figure|stranger|silhouette|soldier|guard|hunter|warrior|"
             "fighter|villager|creature|beast|monster|dragon|dinosaur|wolf|wolves|pup|bear|tiger|lion|horse|rex|raptor|serpent|snake|"
             "shark|whale|bird|fox|deer|dog|cat")
RE_HIEN_RA = re.compile(rf"(?:\b(?:he|she|they)|\b[A-Z][a-z]{{2,}}|\b(?:{_SINH_VAT})s?)(?:\s+(?:\w+ly|then|now|finally|also))?\s+"
                        r"(appears?|appearing|emerges?|emerging|materiali[sz]es|pops? up|(?:is|are) now standing|now stands?|"
                        r"steps? into (?:the )?(?:frame|shot|view))\b")
_KHONG_CHU = {"Nothing", "Ignore", "Image", "Shot", "No", "The", "This", "That", "Then", "Exactly", "Hard", "Keep", "Only", "Nobody"}
_PHU_DINH = re.compile(r"\b(?:no|nothing|nobody|no one|never|not|n't)\b[^.;\n]{0,40}$", re.I)
_SAU_HIEN_RA = re.compile(r"^\s*(?:to|as)\b|^[^.;\n]*\bonly\b|^[^.;\n]{0,60}\b(?:edge|off-?screen|out of frame|outside the frame|"
                          r"from (?:the )?(?:frame )?(?:left|right|bottom|top))", re.I)
RE_SO_CO = re.compile(r"\bsize of an? ((?:[a-z'-]+ ?){1,3})", re.I)
_CAT_SO_CO = re.compile(r"\s(?:in|of|and|with|on|at|that|but)\b.*", re.I)
_KHONG_PHAI_DO = set(("man woman child boy girl adult human person baby newborn infant hand fist palm finger thumb thumbnail fingertip "
                      "head arm forearm leg foot knee shoulder torso "
                      "dog cat kitten puppy pup pony horse foal bull calf cow sheep lamb goat pig wolf bear cub deer fox rabbit mouse rat "
                      "bird eagle hawk owl crow chicken hen duck goose whale shark dolphin seal elephant lion tiger dragon crocodile snake "
                      "lizard fish hound mule donkey ox camel monkey ape bat frog turtle spider insect").split())
_CAM = r"(?:hold(?:s|ing)?|carr(?:y|ies|ying)|grip(?:s|ping)?|clutch(?:es|ing)?|wield(?:s|ing)?|in (?:his|her|their|its|one|both) hands?)"
_LUON = r"(?:throughout|always|at all times|never (?:lets go|puts down)|constantly|in every (?:shot|scene))"
RE_DO_CAM = re.compile(rf"[^.;\n]*?(?:{_LUON}[^.;\n]*?{_CAM}|{_CAM}[^.;\n]*?{_LUON})[^.;\n]*", re.I)


def _trich(chu: str, a: int, b: int) -> str:
    """Câu chứa đoạn [a, b), cắt còn khoảng 90 ký tự quanh chỗ bắt."""
    dau = max(chu.rfind(x, 0, a) for x in ".;\n") + 1
    cuoi = min([x for x in (chu.find(y, b) for y in ".;\n") if x != -1] or [len(chu)])
    dau, cuoi = max(dau, a - 45), min(cuoi, b + 45)
    return ("…" if dau > 0 else "") + " ".join(chu[dau:cuoi].split()) + ("…" if cuoi < len(chu) else "")


# ----- Spec 35 G: chữ dễ bị Seedvis chặn khi cảnh có trẻ em. Danh sách chạy thử trên prompt đã gửi phim 156 đến 163 (25/09) trước khi chốt.
_CON_VAT = "dragon|kraken|wolf|wolves|bear|bird|goat|fox|foxes|deer|seal|owl|horse|shark|whale|creature|monster|beast|serpent|rex|raptor|dinosaur|tooth|teeth"
RE_TRE_EM = re.compile(rf"\b(?:girls?|boys?|child|children|(?<!goat )kids?|infants?|toddlers?)\b|\bbab(?:y|ies)\b(?![\s-]+(?:\w+[\s-]+)?(?:{_CON_VAT})s?\b)|"
                       r"\b(?:[1-9]|1[0-5])[- ]years?[- ]old\b|\b(?:[1-9]|1[0-5]) tuổi\b|(?<!nhỏ )\bbé\b|\b(?:trẻ (?:em|con|nhỏ)|(?:đứa|lũ|bọn) trẻ)\b", re.I)
_Y = "shirt|dress|tunic|clothes|clothing|trousers|pants|sleeves?|coat|smock|cloak|skirt|shift|garment|hem|sweater|bodice"
TU_CHAN = {     # mức "loi": web tự sửa 1 lần khi cảnh có trẻ em; "nhac": chỉ nhắc. Viết lại an toàn bắt cả hai mức. Chữ trong câu phủ định không tính.
    "loi": [r"bare-?foot(?:ed)?", r"bare[- ](?:feet|foot|legs?|arms?|chest(?:ed)?|skin|shoulders?|back|torso|belly)", r"shirtless", r"naked",
            r"skinny", r"emaciated", r"gaunt", r"bony", r"starv(?:ing|ed)", r"filthy", r"rags", rf"(?:ragged|tattered|torn) (?:\w+ )?(?:{_Y})",
            r"blood(?:y|ied|stained)?", r"bleed(?:s|ing)?", r"bruis(?:e|es|ed|ing)", r"corpses?", r"beaten",
            r"(?<!stops )(?<!stop )(?<!stopped )(?<!cut )(?<!cuts )dead(?! (?:still|silent|silence|of|centre|center|ahead|calm|straight|quiet|end|dry|grey|gray|branchw*|wood|leaves|grass|trees?|reeds|bracken))",
            r"(?:stones?|rocks?)[^.;\n]{0,40}\b(?:hits?|strikes?|struck|smacks?)\b"],
    # hạ từ mức lỗi (đo 25/09: bắt nhiều bản đã qua, gần như không bản bị chặn; xích rồng, khăn buộc sừng, dây thuyền)
    "nhac": [r"thin", r"frayed", r"patched", r"soot(?:y|-\w+)?", r"mud(?:dy)?", r"dirty", r"lifeless", r"ropes?", r"tied", r"(?<!-)bound",
             r"chains?", r"chained", r"shackle[sd]?", r"whip(?:s|ped|ping)?",
             r"(?<!is )(?<!was )wound(?:s|ed)?(?! (?:around|round|tight|between|up|into|through|about|across))"],
}
TU_CHAN_MOI_NGUOI = [r"corpses?", r"dead bod(?:y|ies)", r"giving birth", r"naked", r"blood(?:y|ied|stained)?"]   # Viết lại an toàn: mọi nhân vật
_RE_CHAN = {k: re.compile(r"\b(?:" + "|".join(v) + r")\b", re.I) for k, v in TU_CHAN.items()}
_RE_CHAN_MOI_NGUOI = re.compile(r"\b(?:" + "|".join(TU_CHAN_MOI_NGUOI) + r")\b", re.I)

# ----- Spec 47 AF.4: chữ Dola AI Creation hay chặn (chặn theo CHỮ, đổi ảnh không cứu). Mỗi mục (mẫu, gợi ý thay); máy làm mềm bọc \b(?:…)\b, re.I,
# không miễn câu phủ định, bỏ thoại ngoặc kép. "loi": có lượt chặn mà 0 bản qua AI Creation chứa; "nhac": nghi, hay còn ở bản qua. Đo 21/10 trên
# 138 prompt khác nhau gửi AI Creation 13–21/10 (84 qua, 54 chặn; cách đo ở spec/47-muse/lich-su-bi-chan.md mục Dola). Dola có chặn ngẫu nhiên
# (phim 474: 5 bản chặn rồi qua y nguyên).
TU_CHAN_DOLA = {
    "loi": [
        (r"very fast", "at real-time speed"),                                       # 37808, 37817, 37822 chặn (IDALL B3/ĐD)
        (r"an? (?:move|hit|blow|strike|punch) every (?:second|beat)", ""),          # 37808, 37817, 37822
        (r"draws? (?:his|her|their) (?:right |left )?fist back", ""),               # D9b 37864/37873, C1_10_dd 37882/37890 (D9 viết gọn qua)
        (r"folds? over the fist", "folds over"),                                    # cùng trên
        (r"(?:spear|sword|arrow|knife|blade|bite|claw|scraped|fresh|open|raw|crusted|deep|bleeding) wounds?", "an old pale mark"),  # 350 P50–P140
        (r"punctur(?:e|ed|es)(?: marks?)?", "a small scar"),                        # 350 P140, P142
        (r"(?<!no )(?<!without )blood(?:y|ied|stained)?", ""),                      # 350 P64, P130 ("golden blood"); "no blood" có ở 3 bản qua
        (r"bleed(?:s|ing)?", ""),                                                   # 350
        (r"captiv(?:e|es|ity)", "the soldiers' own"),                               # 350: 12 bản chặn, 0 qua
        (r"captured(?! (?:on|in) (?:camera|film|frame|one take))", ""),             # 350
        (r"(?:black |iron |metal )?bit in (?:the|its|his|her) mouth", "a dark leather halter"),  # 350 (13 chặn)
        (r"(?:a|the|his|her|their|long|leather) whips?(?! (?:around|round|past|toward|towards|back|up|out|through|across|into|over|aside))", ""),  # 350 (12 chặn; bản qua chỉ có động từ "whips")
        (r"hooked (?:lance|pole|spear)s?", "a long pole"),                          # 350
        (r"rope nets?", "a coil of rope"),                                          # 350
        (r"(?:crown )?brand(?:ed)? on (?:the |its |his |her )?(?:left |right )?neck", "a pale crown-shaped marking"),  # 350
        (r"nobody (?:is hurt|is injured|dies|burns|is burned|bleeds)|no one (?:is hurt|is injured|dies)|(?:nothing|never) gory|no gore",
         ""),                                                                       # 350 (6 chặn, 0 qua): phủ định đưa chữ hại vào
    ],
    "nhac": [
        (r"glances? off (?:\w+ )?(?:shoulder|arm|head|face|back|chest)", ""),       # D10 37865 (D9b đã chặn trước đó, chưa tách riêng)
        (r"(?:sore|red|raw) (?:mouth|corners)|terrified|frightened eyes|weakened", "alert, tired"),  # 350 (2–6 chặn)
        (r"saddled|saddles?|bridles?|reins", ""),                                   # 350: con vật bị cưỡi, ép phục dịch (17 chặn; 1 bản qua là màu lông)
        (r"scale armou?r|dragon-skull helm", "dark-cloaked"),                       # 350
        (r"never bit(?:es?|ing)", "keeps a few paces away"),                        # 212_P25 34585 chặn (qua kỹ năng)
        (r"yelps?|yelping|(?:hits?|struck) (?:\w+ )?(?:on the )?muzzle", "jerks its head away"),  # 212_P25 34585
        (r"(?:long )?leather hood(?:ed)?|hooded", "a fur cap"),                     # B3: 7/17 chặn, 0/20 qua (S6 37867: người cầm đuốc trùm mũ dài)
        (r"ordinary adults", "ordinary adult humans"),                              # B3 S7 37868, 37888: 6/17 chặn, 0/20 qua; L0 "ordinary adult humans" qua
        (r"wooden house", "the granary"),                                           # B3: 9/17 chặn, 1/20 qua (đuốc chạy về nhà, nghi đốt nhà có người)
        (r"rope burns?|shackle[sd]?", ""),                                          # 350; "chained to the oak post" có ở 18/20 bản B3 qua, "leashed hounds" qua (366)
        (r"kill(?:s|ed|ing)?", "strike"),                                           # 350 P142
        (r"soaked|dripping", "wet"),                                                # 474 (2 chặn), 350 AN_TOAN
        (r"chok(?:e|es|ed|ing)", ""),                                               # 350, 388
        (r"cock(?:s|ed|ing)? (?:the|his|her) (?:rifle|gun|pistol|hammer)|(?:works?|eases?) the lever|racks? the slide|chambers? a round|metallic click", ""),  # 394_27 chặn: súng đang lên đạn (súng nằm yên qua)
    ],
}


def co_tre_em(chu: str) -> bool:
    return bool(RE_TRE_EM.search(chu or ""))


def tu_de_chan(chu: str, muc: tuple[str, ...] = ("loi",), moi_nguoi: bool = False, bo: tuple[str, ...] = ()) -> list[str]:
    """Chữ dễ bị chặn tìm thấy (viết thường, không trùng). bo: đoạn bỏ qua (cụm nhận dạng tài sản ở lần viết thường)."""
    for x in bo:
        if x:
            chu = re.sub(re.escape(x), " ", chu, flags=re.I)
    ms = [m for k in muc for m in _RE_CHAN[k].finditer(chu)] + (list(_RE_CHAN_MOI_NGUOI.finditer(chu)) if moi_nguoi else [])
    ra = []
    for m in ms:
        dau = max(chu.rfind(x, 0, m.start()) for x in ".;\n") + 1
        if not (_PHU_DINH.search(chu[dau:m.start()]) or re.search(r"\b(?:no|never|not|nobody)\b", m.group(0), re.I)):
            ra.append(" ".join(m.group(0).lower().split()))
    return list(dict.fromkeys(ra))


def luat_chung(chu: str, hang: bool = False, tre_em: bool = True) -> list[str]:
    """Cảnh báo ba luật K4 cho một đoạn chữ tiếng Anh. hang=True: chữ là câu tả cố định (hằng, cụm nhận dạng, cụm cố định) thì kiểm thêm
    đồ cầm tay suốt clip; prompt cảnh thì không (đồ cầm ở cảnh cần là đúng). tre_em (Spec 35 G): chữ có trẻ em thì nhắc chữ dễ bị chặn
    (prompt web tắt: viet_prompt kiểm theo tài sản của cảnh, mức lỗi)."""
    ra = []
    if tre_em and co_tre_em(chu) and (ds := tu_de_chan(chu, ("loi", "nhac"))):
        ra.append(f"có trẻ em cùng chữ dễ bị Seedvis chặn ({', '.join(ds)}): tả trẻ em an toàn (\"worn wool sweater\" thay \"torn rags\", "
                  "\"slim\" thay \"skinny\", \"lies still, eyes closed\" thay \"dead\", đá ném rơi xuống đất cạnh trẻ)")
    for m in RE_HIEN_RA.finditer(chu):
        dau = max(chu.rfind(x, 0, m.start()) for x in ".;\n") + 1
        if (m.group(0).split()[0] in _KHONG_CHU or _PHU_DINH.search(chu[dau:m.start()] + " " + m.group(0).split()[0])
                or _SAU_HIEN_RA.search(chu[m.end():])):
            continue
        ra.append(f"nhân vật hiện ra giữa clip (\"{_trich(chu, m.start(), m.end())}\"): cho có sẵn từ khung đầu "
                  "(\"already standing still in frame from the first frame of this shot\") hoặc đi vào từ mép khung")
    for m in RE_SO_CO.finditer(chu):
        tu = _CAT_SO_CO.sub("", m.group(1)).lower().split()
        if tu and not _KHONG_PHAI_DO & {t.rstrip("s'") for t in tu} and not _KHONG_PHAI_DO & set(tu):
            ra.append(f"so cỡ bằng đồ vật (\"{_trich(chu, m.start(), m.end())}\"): model hay vẽ luôn đồ vật đó; "
                      "tả cỡ bằng bàn tay, thân người hay khung hình (\"no wider than the palm\")")
    if hang:
        for m in RE_DO_CAM.finditer(chu):
            ra.append(f"đồ cầm tay suốt clip trong câu tả cố định (\"{_trich(chu, m.start(), m.end()).strip()}\"): model cho cầm ở mọi cảnh; "
                      "bỏ khỏi câu cố định, chỉ ghi đồ cầm tay ở cảnh cần")
    return list(dict.fromkeys(ra))


RE_CO_CANH = re.compile(r"\bwing(?:s|ed)?\b", re.I)
RE_SO_CHAN = re.compile(r"\b(?:no|two|four|six|eight|[2468])[- ](?:[\w-]+ ){0,2}(?:legs?|limbs?|feet|hooves|paws)\b|\b(?:legless|bipedal|quadruped(?:al)?)\b", re.I)


def than_sinh_vat(chu: str) -> str | None:
    """Spec 34 K7 (7c): cụm sinh vật có cánh mà không ghi số chân thì model gộp chân với cánh (phim 160 clip 1038). Mức nhắc."""
    if RE_CO_CANH.search(chu or "") and not RE_SO_CHAN.search(chu):
        return "cụm có cánh mà không ghi số chân: ghi cấu trúc thân (\"four legs and two wings growing from the shoulders\")"
    return None


def kiem_tong(canh: list[tuple[str, int]], ma_nhip: list[str], nhip_dung: set[str], co_hoi: bool, loi: list[Loi]) -> None:
    """Mã phân cảnh liên tục qua các hồi; nhịp chưa có cảnh (chỉ tới nhịp lớn nhất đã dùng: hồi sau chưa viết thì chưa lỗi)."""
    for i, (p, so_dong) in enumerate(canh, 1):
        if int(p[1:]) != i:
            loi.append((so_dong, f"mã phân cảnh {p} không liên tục qua các hồi (chờ P{i:02d})"))
            break
    if co_hoi and ma_nhip:
        lon_nhat = max(nhip_dung) if nhip_dung else ""
        thieu = [m for m in ma_nhip if m < lon_nhat and m not in nhip_dung]
        if thieu:
            loi.append((None, "nhịp chưa có phân cảnh nào: " + ", ".join(thieu)))


# ----- bản gộp dán trên web -----
def chia_phan(van_ban: str) -> dict:
    """Bản gộp → {"dong": mọi dòng, "dau": (từ, tới), "hoi": [{so, ten, tu, toi}], "sau": (từ, tới) | None}; từ/tới là chỉ số dòng (từ 0, tới không tính).
    Hồi bắt đầu ở dòng `# Hồi n: tên`, hết ở dòng `---` đứng riêng hoặc ở hồi kế. Sau hồi cuối, phần sau `---` là hậu kỳ."""
    dong = van_ban.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    hoi, sau, dau_toi = [], None, len(dong)
    for i, d in enumerate(dong):
        m = RE_HOI.match(d.strip())
        if m:
            if not hoi:
                dau_toi = i
            elif hoi[-1]["toi"] is None:
                hoi[-1]["toi"] = i
            hoi.append({"so": int(m.group(1)), "ten": m.group(2).strip(), "tu": i, "toi": None})
        elif d.strip() == "---" and hoi and hoi[-1]["toi"] is None:
            hoi[-1]["toi"] = i
    if hoi:
        if hoi[-1]["toi"] is None:
            hoi[-1]["toi"] = len(dong)
        elif any(x.strip() for x in dong[hoi[-1]["toi"] + 1:]):
            sau = (hoi[-1]["toi"] + 1, len(dong))
    return {"dong": dong, "dau": (0, dau_toi), "hoi": hoi, "sau": sau}


def kiem_van_ban(van_ban: str) -> tuple[list[Loi], list[str], dict]:
    """Kiểm bản gộp dán trên web. Trả (lỗi xếp theo dòng, dòng tóm tắt từng hồi, phần đã chia)."""
    loi: list[Loi] = []
    ph = chia_phan(van_ban)
    dong = ph["dong"]
    a, b = ph["dau"]
    if not any(d.startswith("# ") and not RE_HOI.match(d) for d in dong[a:b]):
        loi.append((1, "Phần đầu: thiếu dòng tên phim '# Tên phim'"))
    ma_nhip = kiem_nhip("Phần đầu", dong[a:b], loi, a)
    kiem_clip("Phần đầu", dong[a:b], loi, a)
    if not ph["hoi"]:
        loi.append((None, "không có hồi nào (dòng '# Hồi 1: tên hồi' mở đầu mỗi hồi)"))
    ns = ngan_sach(dong[a:b])
    tom, canh, nhip_dung = [], [], set()
    for i, h in enumerate(ph["hoi"], 1):
        if h["so"] != i:
            loi.append((h["tu"] + 1, f"Hồi {h['so']}: số hồi không liên tục (chờ Hồi {i})"))
        c, n, t = kiem_hoi(f"Hồi {h['so']}", h["so"], dong[h["tu"]:h["toi"]], ma_nhip, loi, ns, h["tu"], "bảng nhịp")
        canh += c
        nhip_dung |= n
        tom.append(t)
    kiem_tong(canh, ma_nhip, nhip_dung, bool(ph["hoi"]), loi)
    loi.sort(key=lambda x: (x[0] is None, x[0] or 0))
    return loi, tom, ph


def _muc(dong: list[str], ten: str) -> str:
    """Nội dung một mục `## <ten>` tới mục `## ` kế tiếp."""
    ra, trong = [], False
    for d in dong:
        if d.startswith("## "):
            trong = d[3:].strip().lower().startswith(ten.lower())
            continue
        if trong:
            ra.append(d)
    return "\n".join(ra).strip()


def _o(dong_canh: list[str], nhan: str) -> str:
    """Ô "Nhãn: nội dung" trong các dòng `- …` của một cảnh (ô cắt ở dấu `  |  `)."""
    for d in dong_canh:
        for phan in d.lstrip("- ").split("  |  "):
            if phan.strip().lower().startswith(nhan.lower() + ":"):
                return phan.split(":", 1)[1].strip()
    return ""


def tach_phim(ph: dict) -> dict:
    """Phần đã chia (của bản không lỗi) → thông tin phim, từng hồi, từng cảnh. Lời bình "không" thành rỗng; thời lượng lấy từ tiêu đề cảnh.
    `clip`: mức clip mặc định (15 hay 30, Spec 55 D.1); model từng cảnh chọn lúc tạo phim bằng `gia_credit.model_canh_nhap`."""
    dong = ph["dong"]
    a, b = ph["dau"]
    dau = dong[a:b]
    ten = next((d[2:].strip() for d in dau if d.startswith("# ")), "")
    _, o_dau = dong_cap_phim(dau)
    lb = o_dau.get("lời bình", "")
    giong = RE_GIONG.search(lb)
    dai = re.search(r"\d+", o_dau.get("dài", ""))
    phim = {"ten": ten, "the_loai": o_dau.get("thể loại", ""), "do_dai_phut": int(dai.group()) if dai else None,
            "ngon_ngu": lb.split(",")[0].strip() if lb else "", "voice_id": giong.group(1) if giong else None,
            "clip": clip_phim(o_dau) or 15, "hoi": [], "canh": []}
    for h in ph["hoi"]:
        dh = dong[h["tu"]:h["toi"]]
        phim["hoi"].append({"so": h["so"], "ten": h["ten"], "bang_trang_thai": _muc(dh, "Bảng trạng thái liên tục"),
                            "de_viet_hoi_sau": _muc(dh, "Để viết hồi sau")})
        vt = [i for i, d in enumerate(dh) if d.startswith("## ")] + [len(dh)]
        for i, j in zip(vt, vt[1:]):
            k = RE_CANH.match(dh[i])
            if not k:
                continue
            o = [x.strip() for x in k.group(2).split("·")]
            ten_canh = next((x for x in o if x and not RE_GIAY.fullmatch(x) and not RE_MA_NHIP.fullmatch(x)), "")
            dong_canh = [d for d in dh[i + 1:j] if d.strip()]
            loi_binh = _o(dong_canh, "Lời bình")
            ngoac = re.match(r'"([^"]+)"', loi_binh)      # `"câu đọc" (7 từ, đặt ở giây 4–8)`: chỉ lấy phần trong ngoặc kép
            loi_binh = "" if re.match(r"(không|none)\b", loi_binh.lower()) else ngoac.group(1) if ngoac else loi_binh
            phim["canh"].append({"ma": k.group(1), "ten": ten_canh, "giay": int(RE_GIAY.search(k.group(2)).group(1)),
                                 "nhip": RE_MA_NHIP.findall(k.group(2)), "hoi": h["so"], "dong": h["tu"] + i + 1,
                                 "muc_dich": _o(dong_canh, "Mục đích kể chuyện"),
                                 "loi_binh": loi_binh,
                                 "doan": "\n".join(dh[i:j]).strip()})
    phim["do_dai_giay"] = sum(c["giay"] for c in phim["canh"])
    return phim
