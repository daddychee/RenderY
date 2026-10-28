"""In đúng phần kịch bản trợ lý viết (hay soát) cần cho MỘT phần, thay việc Read trọn `00-nhip.md` và hai mục cuối mọi hồi.

    python cong-cu/doc_phan.py <mã phim | đường dẫn thư mục phim> --phan <n> [--chi-nhip]
    python cong-cu/doc_phan.py <mã phim | đường dẫn thư mục phim> --nhip N72-N74 [--chi-nhip]
--phan n: khoảng nhịp lấy ở bảng `## Phần` của 00-nhip.md (khuôn ở kinh-nghiem/nang-cap-bien-kich/00-ke-hoach.md); in thêm dòng phần n
  ở bảng Phần, chỉ một cảnh cuối (cảnh trước chỉ tiêu đề) và dòng cuối số ký tự, token (NHẮC khi quá 9.000 token).
In ra:
- `00-nhip.md`: dòng đầu, Tựa và thumbnail, Logline, Cảm xúc chủ đạo, Khoảnh khắc chạm (dòng của các nhịp trong phần), Ba hồi (hồi của
  phần); các dòng của phần ở Bảng nhịp và Bảng phân clip, thêm một nhịp trước và một nhịp sau, cùng dòng ngân sách của hồi; Gieo và gặt
  (dòng gieo hay gặt trong phần, cùng dòng `vết`, `biết` còn hiệu lực); Thang vùi dập (bậc của phần và bậc liền trước); Mô típ, Cụm cố
  định (bỏ dòng chỉ ghi nhịp ngoài phần; `từ N13` là tới hết phim; giữ dòng không ghi nhịp và hàng NVxx gốc); Để viết hồi sau.
- File hồi của nhịp đầu phần nếu đã có cảnh trước phần, không thì hồi trước (phần mở hồi mới): dòng bảng trạng thái còn hiệu lực sau
  cảnh cuối trước phần (dòng đã đóng không in), mục "Để viết hồi sau", toàn văn 2 cảnh cuối trước phần (--phan: 1 cảnh).
  Không in hồi cũ hơn: bảng của hồi mới nhất đã chép mọi dòng còn hiệu lực.
- Cả phim: mã nơi `DDxx` đã dùng, số cú WOW đã dùng (tối đa 3).
Cụm cố định: dòng nhân vật (mã NVxx) bỏ cụm tiếng Anh (ô Có mặt chỉ ghi mã, web lấy cụm); dòng vật in đủ (vật chép nguyên văn).
Bản in quá 30.000 ký tự (Claude Code lưu ra file, phải Read lại): cảnh báo và bỏ bớt cảnh cuối trước.
--chi-nhip: bỏ phần file hồi (trợ lý soát một đoạn giữa hồi).
Chỉ thư viện chuẩn. Thoát 1 khi không đọc được phim, khoảng nhịp hay phần."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cau_hinh import thu_muc_phim  # noqa: E402
from dan_y import doc_nhip  # noqa: E402
from dan_y_drama import LOAI_MANG_SANG  # noqa: E402
from luat_kich_ban import TRAN_WOW, ma_wow, tp_canh  # noqa: E402

KHO_THU_PHAP = Path(__file__).resolve().parent.parent / "kien-thuc" / "tu-web" / "kho-thu-phap.md"
RE_KHOANG = re.compile(r"^N(\d{2,3})\s*[-–]\s*N?(\d{2,3})$", re.I)
RE_KHOANG_DONG = re.compile(r"\bN(\d{2,3})\s*[–-]\s*N?(\d{2,3})\b")
RE_TU_N = re.compile(r"\b[Tt]ừ\s+N(\d{2,3})\b")
RE_BA_HOI = re.compile(r"^-\s*\**Hồi\s+(\d+)\**\s*\(\s*N(\d+)\s*[–-]\s*N(\d+)", re.M)
RE_CANH = re.compile(r"^## P(\d{2,3})\b(.*)$")
RE_N = re.compile(r"\bN(\d{2,3})\b")
RE_P = re.compile(r"\bP(\d{2,3})\b")
RE_NOI = re.compile(r"\b(DD\d{2,3})\b\s*([^,|→;]*)")
MUC_DAU = ("Tựa và thumbnail", "Logline", "Cảm xúc chủ đạo", "Khoảnh khắc chạm", "Ba hồi")
MUC_SAU = ("Thang vùi dập", "Mô típ", "Cụm cố định", "Để viết hồi sau")
CON_HIEU_LUC = ("hết phim", "sang hồi", "còn")
TRAN_KY_TU = 30000
TRAN_TOKEN_PHAN, KY_TU_MOT_TOKEN = 9000, 1.7      # đích một phần (kinh-nghiem/nang-cap-bien-kich/00-ke-hoach.md); tỉ lệ như muc_luc.py


def muc(dong: list[str], ten: str) -> list[str]:
    """Các dòng của mục `## ten` (kể cả tiêu đề) tới tiêu đề `#`/`##` kế; không có thì rỗng."""
    for i, d in enumerate(dong):
        if d.startswith("## ") and d[3:].strip().lower().startswith(ten.lower()):
            het = next((j for j in range(i + 1, len(dong)) if dong[j].startswith(("# ", "## "))), len(dong))
            return dong[i:het]
    return []


def _gon(dong: list[str]) -> list[str]:
    while dong and not dong[-1].strip():
        dong = dong[:-1]
    return dong


def _ma_hang(d: str) -> int | None:
    """Số nhịp ở ô đầu một hàng bảng (`| N12 | …`)."""
    o = d.strip().strip("|").split("|")[0].strip()
    m = re.fullmatch(r"N(\d{2,3})", o)
    return int(m.group(1)) if m else None


def gon_cum(dong: list[str]) -> list[str]:
    """Mục Cụm cố định: hàng nhân vật (ô đầu `NVxx`) thay ô cụm tiếng Anh bằng `…`; hàng khác giữ nguyên."""
    ra = dong[:1] + ["(Nhân vật: bỏ cụm tiếng Anh, ô Có mặt chỉ ghi mã. Vật: chép nguyên cụm.)"]
    for d in dong[1:]:
        o = d.strip().strip("|").split("|")
        if d.startswith("|") and len(o) >= 3 and re.fullmatch(r"NV\d{2,3}", o[0].strip()):
            o[2] = " … "
            d = "|" + "|".join(o) + "|"
        ra.append(d)
    return ra


def loc_thang(dong: list[str], tu: int, toi: int) -> list[str]:
    """Thang vùi dập: bậc có nhịp trong tu..toi và bậc gần nhất trước tu; dòng không phải bậc giữ nguyên."""
    bac = [(i, [int(x) for x in RE_N.findall(d)]) for i, d in enumerate(dong) if d.startswith("|") and RE_N.search(d)]
    truoc = [i for i, n in bac if max(n) < tu]
    giu = {i for i, n in bac if any(tu <= x <= toi for x in n)} | set(truoc[-1:])
    bo = {i for i, _ in bac} - giu
    ra = [d for i, d in enumerate(dong) if i not in bo]
    return ra[:1] + [f"(chỉ bậc của phần và bậc liền trước; bỏ {len(bo)} bậc)"] + ra[1:] if bo else ra


def loc_bang(dong: list[str], tu: int, toi: int, ngan_sach: set[int]) -> list[str]:
    """Mục bảng (Bảng nhịp hay Bảng phân clip): tiêu đề mục, dòng `Ngân sách hồi h` của các hồi trong ngan_sach, đầu bảng (một lần),
    các hàng nhịp tu..toi."""
    ra, ns, xong_dau = [], [], False
    for d in dong[1:]:
        if d.lower().startswith("ngân sách hồi"):
            m = re.match(r"ngân sách hồi\s+(\d+)", d.lower())
            if m and int(m.group(1)) in ngan_sach:
                ns.append(d)
            continue
        if not d.startswith("|"):
            continue
        n = _ma_hang(d)
        if n is None:
            if not xong_dau:            # dòng tên cột và dòng gạch của bảng đầu
                ra.append(d)
                xong_dau = set(d.replace("|", "").strip()) <= set("-: ")
        elif tu <= n <= toi:
            ra.append(d)
    return dong[:1] + ns + ra


def doc_canh(dong: list[str]) -> list[tuple[int, int, int]]:
    """Các cảnh `## Pxx`: (số P, dòng đầu, dòng hết) theo chỉ số dòng."""
    moc = [i for i, d in enumerate(dong) if d.startswith(("# ", "## "))] + [len(dong)]
    return [(int(k.group(1)), a, b) for a, b in zip(moc, moc[1:]) if (k := RE_CANH.match(dong[a]))]


def so_hoi(f: Path) -> int:
    return int(re.sub(r"\D", "", f.stem) or 0)


def con_hieu_luc(toi: str, p_cuoi: int, n_cuoi: int) -> bool:
    """Dòng bảng trạng thái còn hiệu lực sau cảnh cuối: cột Tới tới cảnh cuối hay sau đó, ghi "hết phim"/"sang hồi"/"còn", hay không ghi mã."""
    t = toi.lower()
    p, n = [int(x) for x in RE_P.findall(toi)], [int(x) for x in RE_N.findall(toi)]
    return any(x in t for x in CON_HIEU_LUC) or not (p or n) or any(x >= p_cuoi for x in p) or any(x >= n_cuoi for x in n)


def trang_thai(dong: list[str], p_cuoi: int, n_cuoi: int) -> tuple[list[str], int, int]:
    """Bảng trạng thái liên tục, chỉ dòng còn hiệu lực. Trả (các dòng in, số dòng giữ, tổng số dòng)."""
    m = muc(dong, "Bảng trạng thái liên tục")
    if not m:
        return [], 0, 0
    ra, cot, giu, tong = [], None, 0, 0
    for d in m[1:]:
        if not d.startswith("|"):
            continue
        o = [x.strip() for x in d.strip().strip("|").split("|")]
        if cot is None:
            cot = [x.lower() for x in o]
            ra.append(d)
        elif set("".join(o)) <= set("-: "):
            ra.append(d)
        else:
            tong += 1
            toi = o[cot.index("tới")] if "tới" in cot and cot.index("tới") < len(o) else ""
            if con_hieu_luc(toi, p_cuoi, n_cuoi):
                ra.append(d)
                giu += 1
    return ra, giu, tong


def noi_da_dung(hoi: list[tuple[Path, list[str]]]) -> list[str]:
    """Mã nơi DDxx trong ô Bối cảnh các cảnh, theo số, kèm tên lần đầu gặp ở ô chỉ một mã (ô clip nối `DDxx → DDyy` ghi tên đường)."""
    ten: dict[str, str] = {}
    du_phong: dict[str, str] = {}
    for _, dong in hoi:
        for _, a, b in doc_canh(dong):
            for d in dong[a + 1:b]:
                if "Bối cảnh" not in d:
                    continue
                o = d.split("Bối cảnh", 1)[1].split(":", 1)[-1].split("  |  ")[0]
                ds = RE_NOI.findall(o)
                for ma, t in ds:
                    noi = ten if len({x for x, _ in ds}) == 1 else du_phong
                    if not noi.get(ma):
                        noi[ma] = " ".join(t.split())[:40]
    ten = {m: ten.get(m) or du_phong.get(m, "") for m in {**du_phong, **ten}}
    return [f"{m} {ten[m]}".strip() for m in sorted(ten, key=lambda x: int(x[2:]))]


def _trong(d: str, tu: int, toi: int) -> bool | None:
    """Dòng có nhịp trong tu..toi (khoảng `N04–N14` tính cả giữa)? None khi dòng không ghi mã nhịp nào."""
    ma = [int(x) for x in RE_N.findall(d)]
    if not ma:
        return None
    khoang = [(int(a), int(b)) for a, b in RE_KHOANG_DONG.findall(d)] + [(int(a), 999) for a in RE_TU_N.findall(d)]
    return any(tu <= x <= toi for x in ma) or any(a <= toi and tu <= b for a, b in khoang)


def loc_dong_nhip(dong: list[str], tu: int, toi: int, bang_: bool) -> list[str]:
    """Khoảnh khắc chạm (dòng `- Nxx · …`, xét mã đầu dòng; bang_=False) hay Mô típ, Cụm cố định (hàng bảng, xét mọi mã; `từ N13` là
    tới hết phim): bỏ dòng ghi mã nhịp mà không mã nào trong tu..toi. Giữ dòng không ghi mã nhịp và hàng nhân vật gốc (`NVxx`, không đuôi)."""
    ra, bo = [], 0
    for i, d in enumerate(dong):
        la = d.startswith("|") if bang_ else d.startswith("- ")
        dau_bang = bang_ and la and i + 1 < len(dong) and set(dong[i + 1].replace("|", "").strip()) <= set("-: ")
        xet = d if bang_ else " ".join(d.split(" · ")[:1])
        goc_nv = bang_ and re.match(r"\|\s*NV\d{2,3}\s*\|", d)
        if la and not dau_bang and not goc_nv and not set(d.replace("|", "").strip()) <= set("-: ") and _trong(xet, tu, toi) is False:
            bo += 1
            continue
        ra.append(d)
    return ra[:1] + [f"(chỉ dòng của N{tu:02d}–N{toi:02d} và dòng không ghi nhịp; bỏ {bo} dòng)"] + ra[1:] if bo else ra


def gieo_gat(nhip: list[str], ds: set[int], tu: int, toi: int) -> list[str]:
    """Mục Gieo và gặt: dòng gieo hay gặt trong các nhịp ds, cùng dòng `vết`, `biết` còn hiệu lực (gieo trước, chưa hết trước tu)."""
    m = muc(nhip, "Gieo và gặt")
    if not m:
        return []
    d = doc_nhip("\n".join(m))
    chon = []
    for r in d["gieo"]:
        cuoi = r["toi"] if r["toi"] is not None else max(r["gat"], default=None)
        mang = r["loai"] in LOAI_MANG_SANG and r["gieo"] is not None and r["gieo"] <= toi and (cuoi is None or cuoi >= tu)
        if r["gieo"] in ds or set(r["gat"]) & ds or mang:
            chon.append(r["goc"])
    k = next((i for i, x in enumerate(m) if x.startswith("|")), len(m))
    return [m[0] + f" (dòng gieo, gặt ở N{tu:02d}–N{toi:02d}; vết, biết còn hiệu lực)"] + m[k:k + 2] + chon


def in_phan(phim: Path, tu: int, toi: int, kho_tp: Path = KHO_THU_PHAP, chi_nhip: bool = False, so_phan: int | None = None) -> list[str]:
    tm = phim / "kich-ban"
    f_nhip = tm / "00-nhip.md"
    if not f_nhip.exists():
        raise SystemExit(f"LỖI: không thấy {f_nhip}")
    nhip = f_nhip.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    ba_hoi = [(int(h), int(a), int(b)) for h, a, b in RE_BA_HOI.findall("\n".join(muc(nhip, "Ba hồi")))]
    hoi_phan = [h for h, a, b in ba_hoi if a <= toi and tu <= b]
    if not hoi_phan:
        raise SystemExit(f"LỖI: N{tu:02d}–N{toi:02d} không nằm trong hồi nào ở mục Ba hồi")
    ten = f"phần {so_phan}: " if so_phan is not None else "phần "
    ra = [f"# 00-nhip.md ({ten}N{tu:02d}–N{toi:02d}, hồi {', '.join(map(str, hoi_phan))})"]
    dau = next((i for i, d in enumerate(nhip) if d.startswith("## ")), len(nhip))
    ra += _gon(nhip[:dau])
    for t in MUC_DAU:
        m = _gon(muc(nhip, t))
        if t == "Ba hồi":                # chỉ dòng của hồi đang viết
            m = [d for d in m if not (h := RE_BA_HOI.match(d)) or int(h.group(1)) in hoi_phan]
        if t == "Khoảnh khắc chạm" and m:
            m = loc_dong_nhip(m, tu, toi, False)
        ra += m
    for t in ("Bảng nhịp", "Bảng phân clip"):
        m = muc(nhip, t)
        if m:
            ra += [f"{m[0]} (N{max(tu - 1, 1):02d}–N{toi + 1:02d})"] + loc_bang(m, tu - 1, toi + 1, set(hoi_phan))[1:]
    co = {int(x) for d in muc(nhip, "Bảng nhịp") if (x := _ma_hang(d)) is not None}
    ra += gieo_gat(nhip, {x for x in co if tu <= x <= toi}, tu, toi)
    for t in MUC_SAU:
        m = _gon(muc(nhip, t))
        if t == "Cụm cố định" and m:
            m = loc_dong_nhip(gon_cum(m), tu, toi, True)
        elif t == "Thang vùi dập" and m:
            m = loc_thang(m, tu, toi)
        elif t == "Mô típ" and m:
            m = loc_dong_nhip(m, tu, toi, True)
        ra += m
    if so_phan is not None:
        m = muc(nhip, "Phần")
        k = next((i for i, x in enumerate(m) if x.startswith("|")), len(m))
        ra += m[:1] + m[k:k + 2] + [x for x in m[k + 2:] if x.startswith("|") and re.match(rf"\|\s*{so_phan}\s*\|", x)]

    hoi = [(f, f.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")) for f in sorted(tm.glob("hoi-*.md"), key=so_hoi)]
    hoi = [(f, d) for f, d in hoi if doc_canh(d)]
    h0 = hoi_phan[0]

    def truoc(dong: list[str]) -> list[tuple[int, int, int]]:
        """Cảnh trước phần (nhịp ở tiêu đề nhỏ hơn tu): khi viết lại hay soát, file hồi đã có cảnh của phần này hay sau."""
        return [c for c in doc_canh(dong) if max((int(x) for x in RE_N.findall(dong[c[1]])), default=0) < tu]
    nguon = next(((f, d, "viết tiếp") for f, d in hoi if so_hoi(f) == h0 and truoc(d)), None) or \
        next(((f, d, f"hồi trước; phần này mở hoi-{h0}.md") for f, d in reversed(hoi) if so_hoi(f) < h0), None)
    cuoi: list[list[str]] = []
    if chi_nhip:
        pass
    elif nguon is None:
        ra.append("\n# Chưa có hồi nào viết trước phần này (phần đầu phim)")
    else:
        f, dong, cach = nguon
        canh = truoc(dong)
        p_cuoi = max(p for p, _, _ in canh)
        n_cuoi = max((int(x) for _, a, _ in canh for x in RE_N.findall(dong[a])), default=0)
        ra.append(f"\n# {f.name} ({cach}; cảnh cuối P{p_cuoi:02d})")
        tt, giu, tong = trang_thai(dong, p_cuoi, n_cuoi)
        if tt:
            ra += [f"## Bảng trạng thái liên tục (còn hiệu lực sau P{p_cuoi:02d}: {giu}/{tong} dòng; dòng đã đóng không in)"] + tt
        else:
            ra.append("## Bảng trạng thái liên tục: không có")
        ra += _gon(muc(dong, "Để viết hồi sau")) or ["## Để viết hồi sau: không có"]
        if so_phan is None:
            ra.append("## Hai cảnh cuối")
            cuoi = [_gon(dong[a:b]) for _, a, b in canh[-2:]]
        else:                            # --phan: một cảnh cuối đủ để nối (khung cuối gài, cầu nối tiếng); cảnh trước chỉ tiêu đề
            ra.append("## Cảnh cuối" + (f" (cảnh trước: {dong[canh[-2][1]].lstrip('# ')})" if len(canh) > 1 else ""))
            cuoi = [_gon(dong[a:b]) for _, a, b in canh[-1:]]

    duoi = ["\n# Cả phim"]
    noi = noi_da_dung(hoi)
    duoi.append("- Mã nơi đã dùng: " + ("; ".join(noi) if noi else "chưa có"))
    if kho_tp.exists():
        w = ma_wow(kho_tp.read_text(encoding="utf-8"))
        dung = [f"{n} ({'/'.join(m for m in tp if m in w)})" for f, d in hoi for n, _, tp in tp_canh(f.name, d) if any(m in w for m in tp)]
        duoi.append(f"- Cú WOW đã dùng: {len(dung)}/{TRAN_WOW}" + (f" ({', '.join(dung)})" if dung else ""))
    else:
        duoi.append(f"- Cú WOW: thiếu {kho_tp.name}, chưa đếm")
    than = cat_tran(ra, cuoi, duoi)
    if so_phan is not None:
        n = len("\n".join(than))
        tok = round(n / KY_TU_MOT_TOKEN)
        if tok > TRAN_TOKEN_PHAN:
            than.append(f"NHẮC: bản in khoảng {tok} token, đích {TRAN_TOKEN_PHAN}: rút Sự kiện (tối đa 2 câu), Ghi chú Cụm cố định, "
                        f"'Để viết hồi sau' của file hồi (tối đa 30 dòng)")
        than.append(f"<!-- doc_phan phần {so_phan}: {n} ký tự, khoảng {tok} token -->")
    return than


def cat_tran(ra: list[str], cuoi: list[list[str]], duoi: list[str]) -> list[str]:
    """Ghép bản in; quá TRAN_KY_TU thì bỏ dần 2 cảnh cuối (cảnh cũ hơn trước) và in cảnh báo ở đầu."""
    def ghep(c: list[list[str]], bo: list[str]) -> list[str]:
        return ra + [x for k in c for x in k] + ([f"(đã bỏ {', '.join(bo)}: Read đúng cảnh ở file hồi nếu cần)"] if bo else []) + duoi
    bo: list[str] = []
    while cuoi and len("\n".join(ghep(cuoi, bo))) > TRAN_KY_TU:
        bo.append(cuoi.pop(0)[0].split(" · ")[0].lstrip("# "))
    than = ghep(cuoi, bo)
    n = len("\n".join(than))
    if bo or n > TRAN_KY_TU:
        than = [f"CẢNH BÁO: bản in {n} ký tự (trần {TRAN_KY_TU})" + (f", đã bỏ {', '.join(bo)}" if bo else "") + "."] + than
    return than


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    co = "--phan" if "--phan" in argv else "--nhip"
    if co not in argv or argv.index(co) + 1 >= len(argv):
        print("\n".join(__doc__.strip().splitlines()[2:4]))
        return 2
    i = argv.index(co)
    gt = argv[i + 1].strip()
    tep = [a for a in argv[:i] + argv[i + 2:] if a != "--chi-nhip"]
    k = RE_KHOANG.match(gt) if co == "--nhip" else re.fullmatch(r"\d+", gt)
    if not k or len(tep) != 1:
        print("Cần: <thư mục phim> --phan <n> | --nhip Nxx-Nyy")
        return 2
    phim = Path(tep[0])
    phim = phim if phim.is_dir() else thu_muc_phim() / tep[0]
    so_phan = None
    if co == "--phan":
        so_phan = int(gt)
        f_nhip = phim / "kich-ban" / "00-nhip.md"
        p = next((x for x in doc_nhip(f_nhip.read_text(encoding="utf-8"))["phan"] if x["so"] == so_phan), None) \
            if f_nhip.exists() else None
        if p is None or not p["nhip"]:
            print(f"LỖI: không thấy {f_nhip}" if not f_nhip.exists() else f"LỖI: bảng Phần của 00-nhip.md không có phần {so_phan} (hay nhịp trống)")
            return 1
        tu, toi = min(p["nhip"]), max(p["nhip"])
    else:
        tu, toi = sorted((int(k.group(1)), int(k.group(2))))
    try:
        print("\n".join(in_phan(phim, tu, toi, chi_nhip="--chi-nhip" in argv, so_phan=so_phan)))
    except SystemExit as e:
        print(e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
