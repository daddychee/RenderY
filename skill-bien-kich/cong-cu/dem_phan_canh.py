"""Đếm phân cảnh theo luật viết phân cảnh (kien-thuc/phan-canh.md luật 1–6, phan-clip.md luật 7–9; Spec 40 C và F.1). Chỉ thư viện chuẩn, chạy độc lập.

    python cong-cu/dem_phan_canh.py <kịch bản .md> [--nhip <00-nhip.md>] [--uoc]

Hai chế độ, tự chọn theo kịch bản:
- **Ghi rõ** (kịch bản viết theo phan-canh.md): ô Mục đích mở bằng loại (`việc`, `sau đỉnh`, `đe dọa`, `nối`, `đệm`, `lớn k/n tên`,
  `lật k/n`) rồi ` · ` rồi việc; ô Bối cảnh mở bằng mã nơi `DDxx` (clip nối đường đi: `DDxx → DDyy`). Báo LỖI khi chắc, CẢNH BÁO khi nên đọc lại.
  Bản 2 (luật 7–9) đọc thêm phần đầu (từ `--nhip`, hay phần đầu bản gộp): "Dài: N phút", mục Ba hồi, bảng nhịp (cột Mức),
  thang vùi dập, bảng phân clip, mục Gieo và gặt (khuôn mới, bảng nhịp không còn cột Gieo, Trả ở; chỉ để ghi "gặt Gxx" khi nhịp không
  có clip); soát ngân sách, trần clip việc, sau đỉnh (nhịp Loại `Móc` không cần clip lớn hay sau đỉnh), đe dọa, nhịp không clip, khớp bảng phân clip, mã KB không có
  trong kien-thuc/kho/ (đều CẢNH BÁO).
  Trận (Spec 39 A.5, khối `## Thiết kế trận` theo kien-thuc/tran-danh.md): LỖI khi bảng phân clip ghi trận mà không có khối, bảng khối
  không khớp các cảnh Pa–Pb; CẢNH BÁO số clip việc ngoài tối thiểu/trần theo cỡ, ô Đổi thế có ';', cú đỉnh TP lặp, đồ môi trường dùng
  hai lần, người phụ tăng không ghi ai vào, cỡ chính/cuối thiếu Lý do đảo thế, bảng trạng thái thiếu dòng từ cảnh cuối trận.
  Neo đoạn (phan-canh.md "Khán giả hiểu chỉ bằng màn hình"): CẢNH BÁO khi clip đầu đoạn (đổi mã nơi; sau clip nối là clip kế)
  không có shot định vị (chữ rộng, toàn, định vị ở Hành động theo nhịp).
  Cảnh trong khối trận tính ngoài ngân sách clip và trần clip việc theo mức.
  Cú WOW (mã TP có "Điểm nhấn:" ở kien-thuc/tu-web/kho-thu-phap.md) đếm cả phim: file `hoi-n.md` thì đọc mọi `hoi-*.md` cạnh nó; LỖI khi
  quá 3 cảnh hay hai cảnh liền nhau (như kiem_kich_ban.py ở bước gộp).
- **Chỉ bảng** (chưa có cảnh, file có `## Bảng phân clip`, như `00-nhip.md` ở chat 1): dựng clip ảo từ bảng phân clip rồi soát bản 2;
  clip `việc` của dòng ghi `trận` tính ngoài ngân sách, số đó so tối thiểu/trần theo cỡ ghi trong ngoặc (`việc 4 (trận xô xát T1)`).
- **Phim `Clip: 30s`** (dòng đầu `Thể loại: … · Clip: 30s` của `00-nhip.md`, `phan-canh-30s.md`; Spec 55): số clip
  tính bằng đơn vị 15 giây (cảnh 30s = 2; ô Mục đích hai khối `việc + sau đỉnh · …` mỗi loại 1), ngân sách 4,5 đơn vị mỗi phút; bảng phân
  clip ghi số cảnh (`việc+sau đỉnh 1, việc 2, nối 1 15s`). Cảnh 30s (Mango, không ép cắt giữa, Spec 71 K.4): LỖI khi hơn một mã nơi;
  CẢNH BÁO shot đầu quá 4s, shot quá 6s, số shot ngoài 6–9 (cảnh trận 10–16), thoại quá 4 câu, 40 từ, câu quá 12 từ, hơn 3 mã NV ở Có mặt;
  cảnh không phải 10/15/30s; cảnh 10/15s quá 20% giây; trận: cảnh 30s một dòng ở bảng khối. Vắng `Clip:` là phim 15s, máy chạy như cũ.
- **Ước lượng** (kịch bản cũ, hay `--uoc`): việc = số vế của ô Mục đích; nơi = mã DD hay phần đầu ô Bối cảnh. Chỉ in số và CẢNH BÁO.
In số và dòng lỗi. Mã thoát 1 khi có LỖI.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from luat_kich_ban import TRAN_WOW, clip_phim, dong_cap_phim, kiem_wow, ma_wow, tp_canh  # noqa: E402

RE_CANH = re.compile(r"^## (P\d{2,3})\b(.*)$")
RE_GIAY = re.compile(r"\b(\d{1,3})s\b")
RE_DD = re.compile(r"\bDD\d{2,3}\b")
RE_LOAI = re.compile(r"^(việc|sau đỉnh|đe d(?:ọa|oạ)|nối|đệm|lớn\s+(\d+)\s*/\s*(\d+)\s*([^·+]*?)|lật\s+(\d+)\s*/\s*(\d+))"
                     r"(?:\s*\+\s*(việc|sau đỉnh|đe d(?:ọa|oạ)|nối|đệm))?\s*·\s*(.*)$", re.I | re.S)     # `+ loại`: khối B cảnh 30s
RE_NHIP = re.compile(r"\bN(\d{2,3})\b")
RE_DAI = re.compile(r"Dài:\s*(\d+)\s*phút")
RE_BA_HOI = re.compile(r"^-\s*\**Hồi\s+(\d+)\**\s*\(\s*N(\d+)\s*[–-]\s*N(\d+)[^)]*?(\d+)\s*%", re.M)
RE_CLIP_LOAI = re.compile(r"(việc|sau đỉnh|đe d(?:ọa|oạ)|nối|đệm|lớn|lật)\s*:?\s*(\d+)", re.I)
LOAI = ("việc", "sau đỉnh", "đe dọa", "nối", "đệm", "lớn", "lật")
CLIP_MOI_PHUT = 6
DON_VI_MOI_PHUT_30 = 4.5          # phim Clip: 30s, đơn vị 15 giây mỗi phút (Spec 55 đề xuất B câu 2)
RE_LOAI_30 = r"việc|sau đỉnh|đe d(?:ọa|oạ)|nối|đệm|lớn|lật"
RE_CLIP_30 = re.compile(rf"((?:{RE_LOAI_30})(?:\s*\+\s*(?:{RE_LOAI_30}))*)\s*:?\s*(\d+)(\s*(?:\([^)]*\)\s*)?(?:\b(?:10|15)\s*s\b)?)", re.I)
RE_SHOT = re.compile(r"(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*s\b")
RE_THOAI = re.compile(r'"([^"]+)"|“([^”]+)”')
RE_NV = re.compile(r"\bNV\d{2,3}\b")
KHO = Path(__file__).resolve().parent.parent / "kien-thuc" / "kho"
KHO_TP = Path(__file__).resolve().parent.parent / "kien-thuc" / "tu-web" / "kho-thu-phap.md"
RE_KB = re.compile(r"\bKB\s*0*(\d+)\b", re.I)
RE_NOI_VE = re.compile(r"\s*;\s*|\s*,?\s+rồi\s+|\s*→\s*")
RE_NHAN = re.compile(r"^([^:;]{1,40}):\s+(\S.*)$", re.S)
TU_NOI = ("toàn cảnh", "trên đường", "đường đi", "thiết lập", "cảnh nối", "clip nối")
TU_DOI_NOI = re.compile(r"\s+rồi\s+|→|\s+sang\s+|\s+ra\s+tới\s+|\s+tới\s+")
TU_HAI_VIEC = re.compile(r"\s+rồi\s+|,\s+và\s+|\s+xong\s+")
RE_DINH_VI = re.compile(r"rộng|toàn|định vị", re.I)          # shot định vị ở clip đầu đoạn (phan-canh.md "Shot định vị")
RE_TRAN = re.compile(r"^## Thiết kế trận\s+T(\d+)\s*:\s*(.*?)\s*·\s*cỡ\s+(xô xát|chính|cuối)\s*·\s*(P\d{2,3})\s*[–-]\s*(P\d{2,3})\s*$", re.I)
CO_TRAN = {"xô xát": (3, 4), "chính": (6, 10), "cuối": (10, 16)}      # clip `việc` tối thiểu, trần (Spec 39 A.2)
RE_P = re.compile(r"\bP(\d{2,3})\b")
RE_TP = re.compile(r"\bTP\d{2,3}\b")
RE_CON_PHU = re.compile(r"còn\s+(\d+)\s+người phụ", re.I)
RE_DO_MT = re.compile(r"([^,;()]+?)\s*\(([^)]*)\)")
TU_VAO = re.compile(r"\b(?:vào|thêm|tới|đến|xông|nhập)\b", re.I)
TU_BO = set("và của ở trong ngoài trên dưới giữa bên cạnh một hai các những rồi như khi lúc đêm ngày sáng chiều tối khuya trưa".split())


def doc_canh(van_ban: str) -> list[dict]:
    """Mỗi `## Pxx · tên · 15s · Nyy` tới tiêu đề `#`/`##` kế: mã, giây, các ô (Mục đích, Bối cảnh…)."""
    dong = van_ban.replace("\r\n", "\n").split("\n")
    canh, cur = [], None
    for i, d in enumerate(dong, 1):
        k = RE_CANH.match(d)
        if k:
            g = RE_GIAY.search(k.group(2))
            cur = {"ma": k.group(1), "ten": k.group(2), "dong": i, "giay": int(g.group(1)) if g else 15, "o": {}}
            canh.append(cur)
            continue
        if d.startswith("#"):
            cur = None
            continue
        if cur is not None and d.startswith("- "):
            for phan in d[2:].split("  |  "):
                if ":" in phan:
                    nhan, nd = phan.split(":", 1)
                    cur["o"].setdefault(nhan.strip().lower(), nd.strip())
    for c in canh:
        c["muc_dich"] = c["o"].get("mục đích kể chuyện", "")
        c["boi_canh"] = c["o"].get("bối cảnh, thời điểm", c["o"].get("bối cảnh", ""))
    return canh


def so_ve(muc_dich: str) -> int:
    """Số vế việc của ô Mục đích (kịch bản cũ): bỏ nhãn ngắn đầu câu ("vùi dập 8: …"), cắt ở `;`, "rồi", "→"."""
    s = muc_dich.strip()
    m = RE_NHAN.match(s)
    if m and len(m.group(1).split()) <= 6:
        s = m.group(2)
    return max(1, sum(1 for v in RE_NOI_VE.split(s) if len(v.split()) >= 2))


def _tu(s: str) -> set[str]:
    return {w for w in re.findall(r"\w+", s.lower()) if w not in TU_BO and not w.isdigit()}


def _doi(s: str) -> set[str]:
    w = [x for x in re.findall(r"\w+", s.lower()) if x not in TU_BO]
    return {f"{x} {y}" for x, y in zip(w, w[1:])}


def noi_uoc(boi_canh: str) -> tuple[str, bool]:
    """(khóa nơi, có đổi nơi trong clip) từ ô Bối cảnh kịch bản cũ."""
    dd = RE_DD.findall(boi_canh)
    if dd:
        return " ".join(sorted(set(dd))), len(set(dd)) > 1
    phan = boi_canh.split(",")[0]
    return phan.strip().lower(), bool(TU_DOI_NOI.search(phan))


def cung_noi(a: str, b: str) -> bool:
    if a == b or b.startswith("như") or not a or not b:
        return True
    if "DD" in a and "DD" in b:
        return bool(set(a.split()) & set(b.split()))
    ta, tb = _tu(a), _tu(b)
    if _doi(a) & _doi(b):       # chung một cụm hai tiếng ("cối xay", "nhà thờ"): cùng nơi, khác góc
        return True
    return bool(ta and tb) and len(ta & tb) / min(len(ta), len(tb)) >= 0.5


def uoc_luong(canh: list[dict]) -> tuple[list[str], list[str]]:
    ve = [so_ve(c["muc_dich"]) for c in canh]
    clip15 = [max(1.0, c["giay"] / 15) for c in canh]
    tong_giay = sum(c["giay"] for c in canh)
    noi = [noi_uoc(c["boi_canh"]) for c in canh]
    la_noi = [any(t in (c["muc_dich"] + " " + c["ten"]).lower() for t in TU_NOI) for c in canh]
    doi, khong_noi, bao = 0, 0, []
    for i in range(1, len(canh)):
        if not cung_noi(noi[i - 1][0], noi[i][0]):
            doi += 1
            if not la_noi[i]:
                khong_noi += 1
    trong = sum(1 for _, x in noi if x)
    so = [f"Việc mỗi cảnh: TB {sum(ve) / len(ve):.1f}; mỗi 15 giây: {sum(ve) / (tong_giay / 15):.2f} "
          f"(cảnh ≥3 vế: {sum(1 for v in ve if v >= 3)}, 1 vế: {sum(1 for v in ve if v == 1)})",
          f"Đổi nơi giữa hai cảnh: {doi}, không có clip nối: {khong_noi}",
          f"Đổi nơi trong một cảnh: {trong}",
          "Khoảnh khắc lớn, cú lật: không đếm được (kịch bản cũ không ghi rõ)"]
    for c, v, cl in zip(canh, ve, clip15):
        if v / cl > 2:
            bao.append(f"CẢNH BÁO {c['ma']} (dòng {c['dong']}): {v} vế trong {c['giay']}s")
    return so, bao


def che_do_clip(van_ban: str) -> int:
    """15 hay 30 theo ô `Clip:` dòng `Thể loại: …` (vắng hay ghi sai là 15; kiem_kich_ban.py báo ghi sai)."""
    return clip_phim(dong_cap_phim(van_ban.replace("\r\n", "\n").split("\n"))[1]) or 15


def don_vi(c: dict, clip: int) -> list[tuple[str, int]]:
    """(loại, số đơn vị) của một cảnh. Phim 15s: mỗi cảnh 1 clip. Phim 30s: đơn vị 15 giây; cảnh hai khối mỗi loại 1."""
    if clip != 30:
        return [(c["loai"], 1)]
    if c.get("loai2"):
        return [(c["loai"], 1), (c["loai2"], 1)]
    return [(c["loai"], max(1, round(c["giay"] / 15)))]


def _giay(x: str) -> float:
    return float(x.replace(",", "."))


def kiem_30(canh: list[dict], trong_tran: set[str] = frozenset()) -> tuple[list[str], list[str], list[str]]:
    """Cảnh phim `Clip: 30s` (`phan-canh-30s.md`). Cảnh 30s trong bảng khối trận (`trong_tran`, `tran-danh.md`) cho 10–16 shot. Trả (dòng số, LỖI, CẢNH BÁO)."""
    loi, bao = [], []
    dai = [c for c in canh if c["giay"] == 30]
    ngan = sum(c["giay"] for c in canh if c["giay"] != 30)
    tong = sum(c["giay"] for c in canh) or 1
    for c in canh:
        ma = f"{c['ma']} (dòng {c['dong']})"
        if c["giay"] not in (10, 15, 30):
            bao.append(f"CẢNH BÁO {ma}: phim Clip: 30s mà cảnh {c['giay']}s (chỉ 30s, hay 10/15s ở bốn chỗ)")
        if c.get("loai2") and c["giay"] != 30:
            bao.append(f"CẢNH BÁO {ma}: hai loại '{c['loai']} + {c['loai2']}' ở cảnh {c['giay']}s (hai khối chỉ ở cảnh 30s)")
        if c["giay"] != 30:
            continue
        hanh = c["o"].get("hành động theo nhịp", "")
        shot = [(m.start(), _giay(m.group(1)), _giay(m.group(2))) for m in RE_SHOT.finditer(hanh)]
        if not shot:
            bao.append(f"CẢNH BÁO {ma}: không đọc được mốc giây shot ở Hành động theo nhịp ('0–3s trung rộng: …')")
            continue
        if shot[0][2] - shot[0][1] > 4:
            bao.append(f"CẢNH BÁO {ma}: shot đầu {shot[0][2] - shot[0][1]:g}s (tối đa 4s, model hay giãn shot đầu)")
        if dai_nhat := [f"{a:g}–{b:g}s" for _, a, b in shot if b - a > 6]:
            bao.append(f"CẢNH BÁO {ma}: shot quá 6s ({', '.join(dai_nhat)})")
        it, nhieu = (10, 16) if c["ma"] in trong_tran else (6, 9)
        if not it <= len(shot) <= nhieu:
            bao.append(f"CẢNH BÁO {ma}: {len(shot)} shot (cảnh {'trận ' if c['ma'] in trong_tran else ''}30s: {it}–{nhieu})")
        cau, tu = [], 0
        for m in RE_THOAI.finditer(hanh):
            q = m.group(1) or m.group(2)
            tu += len(q.split())
            cau += [len(x.split()) for x in re.split(r"[.!?…]+", q) if x.strip()]
        if len(cau) > 4 or tu > 40:
            bao.append(f"CẢNH BÁO {ma}: thoại {len(cau)} câu, {tu} từ (cảnh 30s: tối đa 4 câu, 40 từ)")
        if any(k > 12 for k in cau):
            bao.append(f"CẢNH BÁO {ma}: câu thoại quá 12 từ")
        if len(nv := set(RE_NV.findall(c["o"].get("có mặt", "")))) > 3:
            bao.append(f"CẢNH BÁO {ma}: {len(nv)} nhân vật ở Có mặt (cảnh 30s: tối đa 3 rõ mặt; Mango tối đa 9 ảnh)")
    if ngan / tong > 0.2:
        bao.append(f"CẢNH BÁO: cảnh 10/15s {ngan}s, {ngan / tong:.0%} giây (phim 30s: tối đa 20%, chỉ móc, nối đường đi, shot liền dài, bộ lọc)")
    so = [f"Phim 30s: {len(dai)} cảnh 30s, {len(canh) - len(dai)} cảnh 10/15s ({ngan / tong:.0%} giây)"]
    return so, loi, bao


def ghi_ro(canh: list[dict], clip: int = 15) -> tuple[list[str], list[str]]:
    loi, bao = [], []
    loai_dem = dict.fromkeys(LOAI, 0)
    lon: dict[str, list[tuple[int, int, dict]]] = {}
    lat: list[tuple[int, int, dict]] = []
    nhieu_viec, trong, doi, khong_noi, ve_cu = 0, 0, 0, 0, 0
    da_thay, truoc, cho_neo = set(), None, False
    for c in canh:
        ma = f"{c['ma']} (dòng {c['dong']})"
        m = RE_LOAI.match(c["muc_dich"].strip())
        if not m:
            loi.append(f"LỖI {ma}: ô Mục đích không mở bằng loại (việc, sau đỉnh, đe dọa, nối, đệm, lớn k/n tên, lật k/n) và ' · '")
            c["loai"], viec = None, c["muc_dich"]
        else:
            t = m.group(1).lower()
            c["loai"] = "lớn" if t.startswith("lớn") else "lật" if t.startswith("lật") else "đe dọa" if t.startswith("đe") else t
            t2 = (m.group(7) or "").lower()
            c["loai2"] = "đe dọa" if t2.startswith("đe") else t2 or None
            viec = m.group(8)
            if c["loai2"] and clip != 30:
                loi.append(f"LỖI {ma}: hai loại '{c['loai']} + {c['loai2']}' chỉ ở phim Clip: 30s (một clip, một loại)")
            for loai, k in don_vi(c, clip):
                loai_dem[loai] += k
            if c["loai"] == "lớn":
                lon.setdefault(m.group(4).strip().lower() or "?", []).append((int(m.group(2)), int(m.group(3)), c))
            elif c["loai"] == "lật":
                lat.append((int(m.group(5)), int(m.group(6)), c))
        if ";" in viec:
            nhieu_viec += 1
            loi.append(f"LỖI {ma}: việc có ';' ({viec.count(';') + 1} việc trong một clip)")
        elif TU_HAI_VIEC.search(viec):
            bao.append(f"CẢNH BÁO {ma}: việc có 'rồi'/'và', có thể là hai việc: {viec[:80]}")
        dd = RE_DD.findall(c["boi_canh"].split(",")[0])
        if not dd:
            loi.append(f"LỖI {ma}: ô Bối cảnh không mở bằng mã nơi DDxx")
            continue
        if len(set(dd)) > 1 and (c["loai"] != "nối" or c.get("loai2") or (clip == 30 and c["giay"] == 30)):
            trong += 1
            loi.append(f"LỖI {ma}: đổi nơi trong một clip ({' → '.join(dd)}) mà không phải clip nối"
                       + (" (cảnh 30s một nơi; nối đường đi là cảnh 15s riêng)" if clip == 30 else ""))
        dau, cuoi = dd[0], dd[-1]
        if c["loai"] == "nối" and not c.get("loai2") and (c["giay"] not in (10, 15) if clip == 30 else c["giay"] != 10):
            bao.append(f"CẢNH BÁO {ma}: clip nối {c['giay']}s (luật: 10 giây)" if clip != 30 else
                       f"CẢNH BÁO {ma}: cảnh nối riêng {c['giay']}s (phim 30s: nối là khối A 'nối + việc', hay cảnh 10/15s đường đi)")
        if truoc is not None and cuoi != truoc:
            doi += 1
            if c["loai"] not in ("nối", "đệm") and dau != truoc:
                if cuoi in da_thay:
                    ve_cu += 1
                    bao.append(f"CẢNH BÁO {ma}: về lại {cuoi} từ {truoc} không có clip nối")
                else:
                    khong_noi += 1
                    loi.append(f"LỖI {ma}: đổi nơi {truoc} → {cuoi} không có clip nối")
        cho_neo = cho_neo or (truoc is not None and cuoi != truoc)
        if cho_neo and (c["loai"] not in ("nối", "đệm") or c.get("loai2")):        # clip đầu đoạn (sau clip nối cũng vậy) cho ai đứng đâu
            cho_neo = False
            if not RE_DINH_VI.search(c["o"].get("hành động theo nhịp", "")):
                bao.append(f"CẢNH BÁO {ma}: clip đầu đoạn ở {cuoi} không có shot định vị (trung rộng, toàn: nơi, ai đứng đâu)")
        da_thay.update(dd)
        truoc = cuoi
    so_lon = []
    for ten, ds in lon.items():
        n = ds[0][1]
        so_lon.append(f"{ten} {len(ds)}")
        if clip == 30:
            if (k := sum(sum(x for _, x in don_vi(c, clip)) for _, _, c in ds)) < 2:
                loi.append(f"LỖI {ds[0][2]['ma']}: khoảnh khắc lớn '{ten}' chỉ có {k} đơn vị 15 giây (phim 30s: một cảnh 30s)")
        elif len(ds) < 2:
            loi.append(f"LỖI {ds[0][2]['ma']}: khoảnh khắc lớn '{ten}' chỉ có {len(ds)} clip (luật: 2)")
        if sorted(k for k, _, _ in ds) != list(range(1, len(ds) + 1)) or any(x != n for _, x, _ in ds) or n != len(ds):
            loi.append(f"LỖI {ds[0][2]['ma']}: khoảnh khắc lớn '{ten}' đánh số k/n không khớp số clip ({len(ds)})")
    if lat:
        ma_lat = [c["ma"] for _, _, c in lat]
        dv_lat = sum(sum(x for _, x in don_vi(c, clip)) for _, _, c in lat)
        if not 4 <= dv_lat <= 6:
            loi.append(f"LỖI {ma_lat[0]}: cú lật lớn nhất {len(lat)} clip (luật: 4 đến 6)" if clip != 30 else
                       f"LỖI {ma_lat[0]}: cú lật lớn nhất {dv_lat} đơn vị 15 giây (phim 30s: 4 đến 6, tức 2–3 cảnh 30s)")
        idx = [canh.index(c) for _, _, c in lat]
        if idx != list(range(idx[0], idx[0] + len(idx))):
            loi.append(f"LỖI {ma_lat[0]}: cú lật lớn nhất phải là các clip liền nhau")
        if [k for k, _, _ in lat] != list(range(1, len(lat) + 1)) or any(n != len(lat) for _, n, _ in lat):
            loi.append(f"LỖI {ma_lat[0]}: cú lật lớn nhất đánh số k/n không khớp số clip ({len(lat)})")
    so = [f"Việc mỗi clip: clip có hơn 1 việc {nhieu_viec}/{len(canh)}",
          ("Loại (đơn vị 15 giây): " if clip == 30 else "Loại: ") + ", ".join(f"{k} {v}" for k, v in loai_dem.items()),
          f"Đổi nơi giữa hai cảnh: {doi}, không có clip nối: {khong_noi} (về lại nơi cũ không nối: {ve_cu})",
          f"Đổi nơi trong một clip (ngoài clip nối): {trong}",
          "Khoảnh khắc lớn (số clip): " + (", ".join(so_lon) or "không có"),
          f"Cú lật lớn nhất: {len(lat)} clip" if lat else "Cú lật lớn nhất: không có trong file này"]
    return so, loi + bao


def bang(dong: list[str], ten_muc: str) -> list[dict]:
    """Các hàng của bảng markdown dưới mục `## <ten_muc>` (mọi lần gặp); mỗi hàng là dict cột → ô."""
    hang, cot, trong = [], None, False
    for d in dong:
        if d.startswith("#"):
            trong = d.lstrip("#").strip().lower().startswith(ten_muc.lower())
            cot = None
            continue
        if not trong or not d.startswith("|"):
            continue
        o = [x.strip() for x in d.strip().strip("|").split("|")]
        if cot is None:
            cot = o
        elif not all(set(x) <= set("-: ") for x in o):
            hang.append(dict(zip(cot, o)))
    return hang


def _o(h: dict, dau: str) -> str:
    """Ô của cột có tên mở bằng `dau` (không phân biệt hoa thường)."""
    return next((v for k, v in h.items() if k.lower().startswith(dau.lower())), "")


def _ma(s: str) -> int | None:
    m = RE_NHIP.search(s)
    return int(m.group(1)) if m else None


def doc_dau(van_ban: str, clip: int = 15) -> dict:
    """Phần đầu: độ dài phim, các hồi (nhịp từ, tới, %), mức và gieo-trả từng nhịp, nhịp vùi dập, bảng phân clip."""
    dong = van_ban.replace("\r\n", "\n").split("\n")
    m = RE_DAI.search(van_ban)
    nhip = {}
    ma_kb = []
    for h in bang(dong, "Bảng nhịp"):
        ma_kb += [f"KB{int(x):02d}" for x in RE_KB.findall(" ".join(h.values()))]      # mã khung ghi ở bảng nhịp
        n = _ma(_o(h, "Mã"))
        muc = re.search(r"\d", _o(h, "Mức"))
        if n is not None:
            nhip[n] = {"muc": int(muc.group()) if muc else None, "gieo": _o(h, "Gieo").strip(" –-"), "loai": _o(h, "Loại").strip().lower(),
                       "tra": [int(x) for x in RE_NHIP.findall(_o(h, "Trả"))]}
    pc = {}
    for h in bang(dong, "Bảng phân clip"):
        ma_kb += [f"KB{int(x):02d}" for x in RE_KB.findall(" ".join(h.values()))]
        n = _ma(_o(h, "Nhịp"))
        if n is None:
            continue
        loai = dict.fromkeys(LOAI, 0)
        if clip == 30:                # số cảnh → đơn vị 15 giây: cảnh 30s một loại 2, hai loại mỗi loại 1, cảnh ghi 10s/15s 1
            for ts, so, duoi in RE_CLIP_30.findall(_o(h, "Clip")):
                ts = [t.lower() for t in re.split(r"\s*\+\s*", ts)]
                moi = 1 if len(ts) > 1 or re.search(r"\b(?:10|15)\s*s\b", duoi) else 2
                for t in ts:
                    loai["đe dọa" if t.startswith("đe") else t] += int(so) * moi
        else:
            for t, so in RE_CLIP_LOAI.findall(_o(h, "Clip")):
                t = t.lower()
                loai["đe dọa" if t.startswith("đe") else t] += int(so)
        muc = re.search(r"\d", _o(h, "Mức"))
        pc[n] = {"loai": loai, "ly_do": _o(h, "Lý do").strip(" –-"), "muc": int(muc.group()) if muc else None, "clip": _o(h, "Clip")}
    gat: dict[int, list[str]] = {}            # khuôn mới: bảng nhịp bỏ cột Gieo, Trả ở; nhịp gặt ở mục Gieo và gặt
    for h in bang(dong, "Gieo và gặt"):
        for x in RE_NHIP.findall(_o(h, "Gặt")):
            gat.setdefault(int(x), []).append(_o(h, "Mã"))
    return {"dai": int(m.group(1)) if m else None,
            "hoi": [(int(a), int(b), int(c), int(d)) for a, b, c, d in RE_BA_HOI.findall(van_ban)],
            "nhip": nhip, "gat": gat, "vui_dap": {n for h in bang(dong, "Thang vùi dập") if (n := _ma(_o(h, "Nhịp"))) is not None},
            "phan_clip": pc, "ma_kb": list(dict.fromkeys(ma_kb))}


def ma_kb_la(ma: list[str], kho: Path = KHO) -> list[str]:
    """Mã KB ở bảng phân clip mà kho (kien-thuc/kho/*/*.md) không có. Kho chưa xuất thì không soát."""
    co = {f"KB{int(x):02d}" for f in kho.glob("*/*.md") for x in re.findall(r"^## KB0*(\d+)\b", f.read_text(encoding="utf-8"), re.M)}
    return [m for m in ma if m not in co] if co else []


def tran_viec(muc: int | None) -> int | None:
    """Trần clip `việc` một nhịp theo mức (luật 8)."""
    return None if muc is None else 2 if muc <= 2 else 3 if muc == 3 else 4


def doc_tran(van_ban: str) -> tuple[list[dict], list[str]]:
    """Các khối `## Thiết kế trận Tn: tên · cỡ … · Pa–Pb` (Spec 39 A.3): dòng đầu khối, bảng từng cảnh, và bảng trạng thái liên tục
    đầu tiên sau khối trong cùng hồi. Trả (các khối, dòng LỖI tiêu đề sai dạng)."""
    dong = van_ban.replace("\r\n", "\n").split("\n")
    ds, loi = [], []
    for i, d in enumerate(dong):
        if not d.lower().startswith("## thiết kế trận"):
            continue
        m = RE_TRAN.match(d.strip())
        if not m:
            loi.append(f"LỖI dòng {i + 1}: khối trận sai dạng (cần '## Thiết kế trận T1: tên · cỡ xô xát|chính|cuối · P09–P16')")
            continue
        het = next((j for j in range(i + 1, len(dong)) if dong[j].startswith("#")), len(dong))
        het_hoi = next((j for j in range(i + 1, len(dong)) if dong[j].startswith("# ")), len(dong))
        dau = {}
        for x in dong[i + 1:het]:
            if x.startswith("- ") and ":" in x:
                k, v = x[2:].split(":", 1)
                dau.setdefault(k.strip().lower(), v.strip())
        ds.append({"ten": f"T{m.group(1)}", "dong": i + 1, "co": m.group(3).lower(), "tu": int(m.group(4)[1:]), "toi": int(m.group(5)[1:]),
                   "hang": bang(["## khối"] + dong[i + 1:het], "khối"), "ly_do": dau.get("lý do đảo thế", ""),
                   "do_mt": dau.get("đồ môi trường", ""), "trang_thai": bang(dong[het:het_hoi], "Bảng trạng thái")})
    return ds, loi


def kiem_tran(canh: list[dict], dau: dict, van_ban: str, clip: int = 15) -> tuple[list[str], list[str], set[str]]:
    """Máy kiểm trận (Spec 39 A.5). Trả (dòng số, dòng LỖI/CẢNH BÁO, mã các cảnh trong khối trận để trừ khỏi ngân sách)."""
    ds, loi = doc_tran(van_ban)
    so, bao, trong, tp = [], [], set(), {}
    ma_canh = {int(c["ma"][1:]): c for c in canh}
    for t in ds:
        nhan = f"{t['ten']} (dòng {t['dong']})"
        trong_khoang = [ma_canh[k] for k in sorted(ma_canh) if t["tu"] <= k <= t["toi"]]
        trong |= {c["ma"] for c in trong_khoang}
        hang = [(int(p.group(1)), h) for h in t["hang"] if (p := RE_P.search(_o(h, "Cảnh")))]
        thieu = [c["ma"] for c in trong_khoang if int(c["ma"][1:]) not in dict(hang)]
        thua = [f"P{k:02d}" for k, _ in hang if k not in {int(c["ma"][1:]) for c in trong_khoang}]
        if t["tu"] not in ma_canh or t["toi"] not in ma_canh:
            loi.append(f"LỖI {nhan}: khoảng P{t['tu']:02d}–P{t['toi']:02d} không có trong kịch bản")
        elif thieu or thua:
            loi.append(f"LỖI {nhan}: bảng khối không khớp cảnh P{t['tu']:02d}–P{t['toi']:02d}"
                       + (f"; thiếu dòng {', '.join(thieu)}" if thieu else "") + (f"; thừa dòng {', '.join(thua)}" if thua else ""))
        viec = sum(k for c in trong_khoang if c.get("loai") for loai, k in don_vi(c, clip) if loai == "việc")
        it, tran = CO_TRAN[t["co"]]
        dv = "đơn vị việc" if clip == 30 else "clip việc"
        so.append(f"Trận {t['ten']} cỡ {t['co']} P{t['tu']:02d}–P{t['toi']:02d}: {len(trong_khoang)} clip, {viec} {dv} ({it}–{tran})")
        if not it <= viec <= tran:
            bao.append(f"CẢNH BÁO {nhan}: {viec} {dv}, cỡ {t['co']} cần {it} đến {tran}")
        if clip == 30:
            dem_dong = [k for k, _ in hang]
            for c in trong_khoang:
                if c["giay"] == 30 and dem_dong.count(int(c["ma"][1:])) < 2:
                    bao.append(f"CẢNH BÁO {nhan} {c['ma']}: cảnh 30s một dòng ở bảng khối (phim 30s: hai dòng, mỗi lần đổi thế một dòng, như '{c['ma']} 0–17', '{c['ma']} 17–30')")
        con_truoc = None
        for k, h in hang:
            doi = _o(h, "Đổi thế")
            if ";" in doi:
                bao.append(f"CẢNH BÁO {nhan} P{k:02d}: ô Đổi thế có ';' ({doi.count(';') + 1} lần đổi thế, trận nhồi)")
            for m in RE_TP.findall(_o(h, "Cú đỉnh")):
                tp.setdefault(m, []).append(f"P{k:02d}")
            con = RE_CON_PHU.search(_o(h, "Cuối cảnh"))
            if con:
                if con_truoc is not None and int(con.group(1)) > con_truoc and not TU_VAO.search(doi):
                    bao.append(f"CẢNH BÁO {nhan} P{k:02d}: còn {con.group(1)} người phụ đứng, tăng từ {con_truoc} mà ô Đổi thế không ghi ai vào")
                con_truoc = int(con.group(1))
        ten_do = {}
        for ten, o in RE_DO_MT.findall(t["do_mt"]):
            ten_do.setdefault(ten.strip().lower(), []).extend(RE_P.findall(o))
        for ten, p in ten_do.items():
            if len(p) > 1:
                bao.append(f"CẢNH BÁO {nhan}: đồ môi trường '{ten}' dùng {len(p)} lần (P{', P'.join(p)}), mỗi món một lần")
        if t["co"] in ("chính", "cuối") and not t["ly_do"].strip(" –-"):
            bao.append(f"CẢNH BÁO {nhan}: trận cỡ {t['co']} thiếu dòng '- Lý do đảo thế:'")
        if not any(t["toi"] in [int(x) for x in RE_P.findall(_o(h, "Từ"))] for h in t["trang_thai"]):
            bao.append(f"CẢNH BÁO {nhan}: Bảng trạng thái liên tục không có dòng bắt đầu ở P{t['toi']:02d} (cảnh cuối trận)")
    for m, p in tp.items():
        if len(p) > 1:
            bao.append(f"CẢNH BÁO: cú đỉnh {m} lặp {len(p)} lần trong phim ({', '.join(p)}), mỗi cú một lần")
    # bảng phân clip ghi trận: nhịp đã có cảnh trong file này phải có khối (theo mã Tn, hay khối chứa cảnh của nhịp đó)
    co_khoi = {t["ten"].upper() for t in ds}
    nhip_trong_khoi = {_ma(c["ten"]) for c in canh if c["ma"] in trong}
    nhip_co_canh = {_ma(c["ten"]) for c in canh}
    for n, r in dau["phan_clip"].items():
        if "trận" not in r["clip"].lower() or n not in nhip_co_canh:
            continue
        ma_t = [f"T{x}" for x in re.findall(r"\bT(\d+)\b", r["clip"])]
        if (ma_t and not all(x in co_khoi for x in ma_t)) or (not ma_t and n not in nhip_trong_khoi):
            loi.append(f"LỖI N{n:02d}: bảng phân clip ghi trận ({r['clip']}) mà hồi không có khối '## Thiết kế trận'"
                       + (f" {', '.join(x for x in ma_t if x not in co_khoi)}" if ma_t else ""))
    return so, loi + bao, trong


def ban_2(canh: list[dict], dau: dict, trong_tran: set[str] = frozenset(), clip: int = 15) -> tuple[list[str], list[str]]:
    """Luật 7–9 (Spec 40 F.1 bản 2). Mọi mục là CẢNH BÁO. trong_tran: mã cảnh trong khối trận, tính ngoài ngân sách và trần
    clip việc theo mức (Spec 39 A.2; trận có trần riêng theo cỡ ở kiem_tran)."""
    so, bao = [], []
    if not dau["nhip"]:
        return so, ["CẢNH BÁO: không đọc được bảng nhịp (thêm --nhip <00-nhip.md>), bỏ qua ngân sách và bảng phân clip"]
    theo: dict[int, dict[str, int]] = {}
    ngoai: dict[int, dict[str, int]] = {}         # như theo, bỏ cảnh trong khối trận
    for c in canh:
        n = _ma(c["ten"])
        if n is not None and c.get("loai"):
            for loai, k in c.get("dv") or don_vi(c, clip):
                theo.setdefault(n, dict.fromkeys(LOAI, 0))[loai] += k
                ngoai.setdefault(n, dict.fromkeys(LOAI, 0))[loai] += k * (c["ma"] not in trong_tran)
    viet = set(theo)
    hoi = [h for h in dau["hoi"] if any(h[1] <= n <= h[2] for n in viet)]
    pham_vi = sorted(n for n in dau["nhip"] if any(h[1] <= n <= h[2] for h in hoi)) if hoi else \
        sorted(n for n in dau["nhip"] if viet and min(viet) <= n <= max(viet))
    # luật 7: ngân sách clip mỗi hồi
    for so_hoi, tu, toi, pt in hoi:
        n_clip = sum(sum(ngoai[n].values()) for n in ngoai if tu <= n <= toi)
        n_tran = sum(sum(theo[n].values()) for n in theo if tu <= n <= toi) - n_clip
        if not dau["dai"]:
            bao.append("CẢNH BÁO: không thấy 'Dài: N phút', bỏ qua ngân sách clip")
            break
        ns = (DON_VI_MOI_PHUT_30 if clip == 30 else CLIP_MOI_PHUT) * dau["dai"] * pt / 100
        lech = (n_clip - ns) / ns * 100
        dv = "đơn vị" if clip == 30 else "clip"
        so.append(f"Hồi {so_hoi}: {n_clip} {dv} / ngân sách {ns:.0f} ({lech:+.0f}%)" + (f", ngoài {n_tran} {dv} trận" if n_tran else ""))
        if abs(lech) > 20:
            bao.append(f"CẢNH BÁO hồi {so_hoi}: {n_clip} {dv}, lệch ngân sách {ns:.0f} quá 20% ({lech:+.0f}%)")
        lat = sum(theo[n]["lật"] for n in theo if tu <= n <= toi)
        if 0 < lat < 6 and n_clip < ns:
            bao.append(f"CẢNH BÁO hồi {so_hoi}: cú lật lớn nhất {lat} {dv} khi hồi còn dưới ngân sách "
                       + ("(phim 30s: 3 cảnh 30s)" if clip == 30 else "(luật 6: 6 clip)"))
    pc = dau["phan_clip"]
    if not pc:
        bao.append("CẢNH BÁO: chưa có '## Bảng phân clip' (luật 8)")
    co_ly_do = []
    for n in pham_vi:
        ten, muc = f"N{n:02d}", dau["nhip"][n]["muc"]
        d = theo.get(n, dict.fromkeys(LOAI, 0))
        if not sum(d.values()):
            vi = (["có dòng thang vùi dập"] if n in dau["vui_dap"] else []) + \
                 [f"trả gieo của N{g:02d}" for g in pham_vi if n in dau["nhip"][g]["tra"] and dau["nhip"][g]["gieo"]] + \
                 ([f"gặt {', '.join(dau['gat'][n])}"] if dau.get("gat", {}).get(n) else [])
            bao.append(f"CẢNH BÁO {ten}: nhịp không có clip" + (f" ({', '.join(vi)})" if vi else ""))
            continue
        tran, viec = tran_viec(muc), ngoai.get(n, d)["việc"]
        if tran is not None and viec > tran:
            if pc.get(n, {}).get("ly_do"):
                co_ly_do.append(ten)
            else:
                bao.append(f"CẢNH BÁO {ten}: {viec} {'đơn vị' if clip == 30 else 'clip'} việc, trần mức {muc} là {tran}; ghi lý do ở bảng phân clip hay gộp (luật 9)")
        if muc is not None and muc >= 4 and not (d["lớn"] or d["lật"] or d["sau đỉnh"]) and dau["nhip"][n].get("loai") != "móc":
            bao.append(f"CẢNH BÁO {ten}: nhịp mức {muc} không có clip lớn, lật hay sau đỉnh")
        if muc is not None and muc <= 3 and d["sau đỉnh"] and not (d["lớn"] or d["lật"]):
            bao.append(f"CẢNH BÁO {ten}: {d['sau đỉnh']} clip sau đỉnh ở nhịp mức {muc} (luật 2: chỉ sau mức 4–5 hay khoảnh khắc lớn)")
        if d["đe dọa"] > 1:
            bao.append(f"CẢNH BÁO {ten}: {d['đe dọa']} clip đe dọa (luật 2: mỗi nhịp tối đa 1)")
        if pc:
            if n not in pc:
                bao.append(f"CẢNH BÁO {ten}: không có dòng ở bảng phân clip")
            elif pc[n]["loai"] != d:
                khac = ", ".join(f"{k} {pc[n]['loai'][k]}/{d[k]}" for k in LOAI if pc[n]["loai"][k] != d[k])
                bao.append(f"CẢNH BÁO {ten}: bảng phân clip lệch cảnh (bảng/cảnh: {khac})")
    so.append("Clip từng nhịp: " + ", ".join(f"N{n:02d} {sum(theo.get(n, {}).values())}" for n in pham_vi))
    if co_ly_do:
        so.append("Vượt trần clip việc có lý do: " + ", ".join(co_ly_do))
    return so, bao


def chi_bang(dau: dict, kho: Path = KHO, clip: int = 15) -> tuple[list[str], list[str]]:
    """Chat 1, chưa có cảnh: clip ảo theo bảng phân clip, soát bản 2 (luật 7–9) và cỡ trận ghi ở ô Clip theo loại."""
    canh, trong, so, bao, i = [], set(), [], [], 0
    for n, r in sorted(dau["phan_clip"].items()):
        tran = "trận" in r["clip"].lower()
        for loai, k in r["loai"].items():
            for _ in range(k):
                i += 1
                canh.append({"ma": f"P{i:02d}", "ten": f" · N{n:02d}", "loai": loai, "dv": [(loai, 1)]})
                if tran and loai == "việc":
                    trong.add(f"P{i:02d}")
        if tran:
            co = next((c for c in CO_TRAN if c in r["clip"].lower()), None)
            it, tr = CO_TRAN.get(co, (None, None))
            if co is None:
                bao.append(f"CẢNH BÁO N{n:02d}: dòng trận chưa ghi cỡ (xô xát, chính, cuối): {r['clip']}")
            elif not it <= r["loai"]["việc"] <= tr:
                bao.append(f"CẢNH BÁO N{n:02d}: trận cỡ {co} {r['loai']['việc']} {'đơn vị' if clip == 30 else 'clip'} việc, cần {it} đến {tr}")
    so2, bao2 = ban_2(canh, dau, trong, clip)
    if la := ma_kb_la(dau["ma_kb"], kho):
        bao2.append(f"CẢNH BÁO: bảng nhịp, bảng phân clip ghi mã không có trong kho: {', '.join(la)} (xem các muc-luc-*.md)")
    return [f"{len(canh)} {'đơn vị 15 giây (phim Clip: 30s)' if clip == 30 else 'clip'} theo bảng phân clip, chế độ chỉ bảng"] + so2, bao + bao2


def dem_wow(tep: list[tuple[str, str]], kho_tp: Path = KHO_TP) -> tuple[list[str], list[str]]:
    """Cú WOW cả phim (Spec 34 mục H) trên các file (tên, văn bản) theo thứ tự hồi. Trả (dòng số khi có cú WOW, dòng LỖI).
    Thiếu kho-thu-phap.md thì không đếm (kiem_kich_ban.py đã báo)."""
    if not kho_tp.exists():
        return [], []
    wow = ma_wow(kho_tp.read_text(encoding="utf-8"))
    canh = [c for ten, vb in tep for c in tp_canh(ten, vb.splitlines())]
    dung = [f"{n.strip()} ({'/'.join(m for m in tp if m in wow)})" for n, _, tp in canh if any(m in wow for m in tp)]
    loi: list = []
    kiem_wow(canh, wow, loi)
    so = [f"Cú WOW cả phim: {len(dung)}/{TRAN_WOW} ({', '.join(dung)})"] if dung else []
    return so, [f"LỖI {cau}" for _, cau in loi]


def dem(van_ban: str, uoc: bool = False, nhip: str = "", kho: Path = KHO, ca_phim: list[tuple[str, str]] | None = None,
        kho_tp: Path = KHO_TP) -> tuple[str, list[str], list[str]]:
    """Trả (chế độ, dòng số, dòng LỖI/CẢNH BÁO). nhip: văn bản phần đầu (00-nhip.md) khi kịch bản không phải bản gộp.
    ca_phim: các hồi (tên, văn bản) để đếm cú WOW cả phim; không có thì đếm trên van_ban."""
    canh = doc_canh(van_ban)
    clip = che_do_clip(nhip + "\n" + van_ban)
    if not canh:
        dau = doc_dau(nhip + "\n" + van_ban, clip)
        if dau["phan_clip"]:
            so, dong = chi_bang(dau, kho, clip)
            return "chỉ bảng", so, dong
        return "trống", [], ["LỖI: không có phân cảnh nào (dòng '## P01 · tên · 15s · N01')"]
    co_loai = sum(1 for c in canh if RE_LOAI.match(c["muc_dich"].strip()))
    che_do = "ước lượng" if uoc or co_loai < len(canh) / 2 else "ghi rõ"
    so, dong = uoc_luong(canh) if che_do == "ước lượng" else ghi_ro(canh, clip)
    if che_do == "ghi rõ":
        dau = doc_dau(nhip + "\n" + van_ban, clip)
        so_tran, dong_tran, trong_tran = kiem_tran(canh, dau, van_ban, clip)
        so2, bao2 = ban_2(canh, dau, trong_tran, clip)
        so2, bao2 = so_tran + so2, dong_tran + bao2
        if clip == 30:
            so30, loi30, bao30 = kiem_30(canh, trong_tran)
            so2, bao2 = so30 + so2, loi30 + bao30 + bao2
        if la := ma_kb_la(dau["ma_kb"], kho):
            bao2.append(f"CẢNH BÁO: bảng nhịp, bảng phân clip ghi mã không có trong kho: {', '.join(la)} (xem các muc-luc-*.md)")
        so_w, loi_w = dem_wow(ca_phim or [("", van_ban)], kho_tp)
        so, dong = so + so2 + so_w, loi_w + dong + bao2
    tong = sum(c["giay"] for c in canh)
    return che_do, [f"{len(canh)} cảnh, {tong}s (tương đương {tong / 15:.0f} clip 15 giây), chế độ {che_do}"] + so, dong


def main(argv: list[str]) -> int:
    nhip = ""
    if "--nhip" in argv:
        i = argv.index("--nhip")
        if i + 1 >= len(argv):
            print("thiếu tên file sau --nhip")
            return 2
        nhip = Path(argv[i + 1]).read_text(encoding="utf-8")
        argv = argv[:i] + argv[i + 2:]
    tep = [a for a in argv if not a.startswith("--")]
    if len(tep) != 1:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    f = Path(tep[0])
    ca_phim = None
    if re.fullmatch(r"hoi-\d+\.md", f.name):      # một hồi: đếm cú WOW trên mọi hồi cạnh nó
        hoi = sorted(f.parent.glob("hoi-*.md"), key=lambda x: int(re.sub(r"\D", "", x.stem) or 0))
        ca_phim = [(h.name, h.read_text(encoding="utf-8")) for h in hoi]
    _, so, dong = dem(f.read_text(encoding="utf-8"), "--uoc" in argv, nhip, ca_phim=ca_phim)
    print(Path(tep[0]).name + ": " + so[0] if so else Path(tep[0]).name)
    for s in so[1:] + dong:
        print("  " + s)
    return 1 if any(d.startswith("LỖI") for d in dong) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
