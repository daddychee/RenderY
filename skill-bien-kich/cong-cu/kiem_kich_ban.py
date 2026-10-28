"""Kiểm kịch bản chia theo hồi của một phim (skill biên kịch) rồi gộp ra `kich-ban.md`. Chỉ in lỗi và cảnh báo.
Chép một lần từ `skill lam phim/cong-cu/kiem_kich_ban.py` (28/09, Spec 40 bước 5a-1), bỏ các kiểm trái Spec 40 C: ngân sách giây,
5 phút đầu chỉ cảnh 15 giây, sức nặng theo cột Cảnh (mẫu nhịp cảm xúc). Luật số clip (ngân sách clip, trần, trận) ở `dem_phan_canh.py`.

Đọc `<THU_MUC_PHIM>/<mã>/kich-ban/`: `00-nhip.md` (bảng nhịp, bảng mô típ, bảng cụm cố định) và `hoi-*.md` (phân cảnh
`## Pxx · tên · 15s · Nyy`, mục "Bảng trạng thái liên tục", mục "Để viết hồi sau").
- LỖI: luật ở `luat_kich_ban.py` (bản chép luật web nhận khi dán, không sửa tay); dòng `Ngân sách: hồi 1 270s …` (web chặn khi tổng giây
  lệch quá 15%; Spec 40 bỏ ngân sách giây nên phải xóa dòng này);
  mã thủ pháp TPxx phải có trong `kien-thuc/tu-web/kho-thu-phap.md` (bản xuất kho trên web, Spec 34);
  cú WOW (dòng kho có "Điểm nhấn:") cả phim tối đa 3 cảnh, không hai cảnh liền nhau;
  thoại mỗi nhịp của "Hành động theo nhịp" tối đa 3 từ một giây, viết trong ngoặc kép (Seedance nói vội khi vượt);
  ô `Clip:` dòng `Thể loại: …` của `00-nhip.md` chỉ 15s hay 30s (Spec 55 C, như web).
  Không lỗi thì gộp `00-nhip.md` + các hồi + `90-hau-ky.md` (nếu có) thành `kich-ban.md` để dán vào trang Phim mới trên web.
- CẢNH BÁO: luật máy kiểm được mà web không chặn (mức nhịp, số lần mô típ, cụm cố định (cánh mà thiếu số chân), bảng trạng thái nối hồi,
  tốc độ lời bình, tóm tắt hồi, móc mở phim N01 (phim `Clip: 30s`: cảnh N01 vẫn 15s); chữ tiếng Anh: nhân vật hiện ra giữa clip, so cỡ bằng đồ vật, dòng bảng có đồ cầm tay
  suốt clip, dòng có trẻ em cùng chữ dễ bị Seedvis chặn, theo `luat_chung`). Không chặn gộp.

Chạy: python cong-cu/kiem_kich_ban.py <mã phim | đường dẫn thư mục phim> [--dang-viet N]
--dang-viet N: hồi N đang viết dở giữa hai phần (chat điều phối): không gộp `kich-ban.md`.
Thoát 1 khi có lỗi."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
from cau_hinh import thu_muc_phim  # noqa: E402
from luat_kich_ban import (RE_CANH, RE_GIAY, RE_MA_NHIP, _o, bang, clip_phim, dong_cap_phim, kiem_clip, kiem_hoi,  # noqa: E402
                           kiem_nhip, kiem_thoai, kiem_thu_phap, kiem_tong, kiem_wow, luat_chung, ma_kho, ma_wow, ngan_sach,
                           than_sinh_vat, tp_canh)

TU_MOT_GIAY = 2.5       # lời bình: trần của cảnh thiết lập
IN_TOI_DA = 40          # số cảnh báo in ra
RE_NV = re.compile(r"\bNV\d{2,3}\b")
RE_P = re.compile(r"\bP(\d{2,3})\b")
RE_N = re.compile(r"\bN(\d{2,3})\b")
KHO_THU_PHAP = Path(__file__).resolve().parent.parent / "kien-thuc" / "tu-web" / "kho-thu-phap.md"


def _dong(f: Path) -> list[str]:
    return f.read_text(encoding="utf-8").splitlines()


def _so_hoi(f: Path) -> int:
    return int(re.sub(r"\D", "", f.stem) or 0)


def gop(tm: Path, hoi: list[Path]) -> None:
    phan = [(tm / "00-nhip.md").read_text(encoding="utf-8")]
    phan += [h.read_text(encoding="utf-8") for h in hoi]
    hk = tm / "90-hau-ky.md"
    if hk.exists():
        phan.append(hk.read_text(encoding="utf-8"))
    ra = "<!-- File gộp do kiem_kich_ban.py sinh từ kich-ban/. Không sửa tay; sửa trong kich-ban/ rồi chạy lại. -->\n\n"
    (tm.parent / "kich-ban.md").write_text(ra + "\n\n---\n\n".join(p.rstrip() + "\n" for p in phan), encoding="utf-8")


# ----- cảnh báo -----
def _canh(dong: list[str]):
    """Từng cảnh của một hồi: (mã P, số giây hay None, các số nhịp ở tiêu đề, các dòng thân cảnh)."""
    moc = [i for i, d in enumerate(dong) if d.startswith("## ")] + [len(dong)]
    for a, b in zip(moc, moc[1:]):
        k = RE_CANH.match(dong[a])
        if k:
            g = RE_GIAY.search(k.group(2))
            yield (k.group(1), int(g.group(1)) if g else None, [int(x) for x in RE_N.findall(k.group(2))],
                   [d for d in dong[a + 1:b] if d.strip()])


def _cum(o: str) -> str:
    """Phần tiếng Anh cố định của một ô bảng trạng thái: trước dấu `;` hay `(` đầu tiên (sau đó là ghi chú)."""
    return re.sub(r"\s+", " ", re.split(r"[;(]", o)[0]).strip().lower()


def _ten_tt(h: dict) -> str:
    """Khóa tên một dòng bảng trạng thái: mã NV nếu có, không thì tên (bỏ ghi chú trong ngoặc)."""
    nv = h.get("Nhân vật", "")
    m = RE_NV.search(nv)
    return m.group() if m else re.sub(r"\(.*?\)", "", nv).strip().lower()


def _lech(moi: str, cu: str) -> str:
    """Hai cụm, cắt quanh chỗ bắt đầu khác nhau."""
    i = next((k for k, (a, b) in enumerate(zip(moi, cu)) if a != b), min(len(moi), len(cu)))
    a = max(i - 15, 0)
    return f"'…{moi[a:i + 30]}…' ≠ '…{cu[a:i + 30]}…'"


def canh_bao_nhip(nhip: list[str], cb: list[str]) -> set[str]:
    """Mức nhịp, số lần mô típ, bảng cụm cố định. Trả các mã NV có trong bảng cụm cố định (rỗng nếu không có bảng)."""
    muc = [(h.get("Mã", ""), h.get("Mức", "").strip()) for h in bang(nhip, "Bảng nhịp")]
    for i in range(2, len(muc)):
        if muc[i][1] and muc[i][1] == muc[i - 1][1] == muc[i - 2][1]:
            cb.append(f"00-nhip.md: {muc[i - 2][0]}–{muc[i][0]} ba nhịp liền cùng mức {muc[i][1]}")
    dinh = [m for m, v in muc if v == "5"]
    if len(dinh) != 1:
        cb.append(f"00-nhip.md: đỉnh mức 5 phải đúng một lần, đang có {len(dinh)} ({', '.join(dinh) or 'không'})")
    for h in bang(nhip, "Mô típ"):
        lan = sum(len(RE_MA_NHIP.findall(h.get(c, ""))) for c in ("Gieo ở", "Lặp ở", "Trả ở"))
        if lan < 3:
            cb.append(f"00-nhip.md: mô típ '{h.get('Mô típ', '')[:30]}' mới xuất hiện {lan} lần (cần 3 đến 4)")
    cum = bang(nhip, "Cụm cố định")
    if not cum:
        cb.append("00-nhip.md: thiếu mục '## Cụm cố định' (bảng Mã | Tên | Cụm tiếng Anh, chốt ở phiên 1a)")
    for h in cum:
        o = next((v for k, v in h.items() if k.startswith("Cụm")), "")
        if x := than_sinh_vat(o):
            cb.append(f"00-nhip.md dòng {h['_dong'] + 1}: {h.get('Mã', '')} {x}")
    return {m for h in cum for m in RE_NV.findall(h.get("Mã", ""))}


def canh_bao_hoi(hoi: list[Path], ma_nv: set[str], cb: list[str]) -> None:
    """Từng hồi: mã nhân vật ngoài bảng cụm cố định, tốc độ lời bình, tóm tắt hồi; giữa hai hồi liền nhau: bảng trạng thái nối."""
    truoc = None  # (tên file, số P cuối, số N lớn nhất, các dòng bảng trạng thái)
    for f in hoi:
        dong = _dong(f)
        p_cuoi, n_max, la = 0, 0, {}
        for p, giay, so_nhip, than in _canh(dong):
            p_cuoi = max(p_cuoi, int(p[1:]))
            n_max = max([n_max] + so_nhip)
            if ma_nv:
                for m in RE_NV.findall(_o(than, "Có mặt")):
                    if m not in ma_nv:
                        la.setdefault(m, []).append(p)
            lb = _o(than, "Lời bình")
            if giay and lb and not re.match(r"(không|none)\b", lb.lower()):
                ngoac = re.findall(r'"([^"]+)"', lb)
                cau = re.sub(r"\([^)]*\)", " ", " ".join(ngoac) if ngoac else lb)
                tu = len(re.findall(r"[A-Za-z][A-Za-z'’-]*", cau))
                if tu > TU_MOT_GIAY * giay:
                    cb.append(f"{f.name}: {p} lời bình {tu} từ cho {giay}s (quá {TU_MOT_GIAY:g} từ một giây)")
        for m, ds in la.items():
            cb.append(f"{f.name}: {m} ({', '.join(ds[:4])}{'…' if len(ds) > 4 else ''}) không có trong bảng Cụm cố định")
        sau = dong[next((i for i, d in enumerate(dong) if d.startswith("## Để viết hồi sau")), len(dong)):]
        if sau and not any(re.match(r"\s*-\s*\**Tóm tắt", d) for d in sau):
            cb.append(f"{f.name}: mục 'Để viết hồi sau' thiếu dòng '- Tóm tắt hồi: …'")
        tt = [(_ten_tt(h), h.get("Từ", "").strip(), _cum(h.get("Cụm tiếng Anh cố định", "")), h)
              for h in bang(dong, "Bảng trạng thái liên tục")]
        if truoc:
            ten0, p0, n0, tt0 = truoc
            for ten, tu, cum, h in tt0:
                toi = h.get("Tới", "")
                con = ("sang hồi" in toi.lower() or "hết phim" in toi.lower()
                       or any(int(x) > p0 for x in RE_P.findall(toi)) or any(int(x) > n0 for x in RE_N.findall(toi)))
                cung_ten = [x for x in tt if x[0] == ten]
                if not con or any(x[2] == cum for x in cung_ten):
                    continue
                nhan = f"'{h.get('Nhân vật', '')[:24]}' từ {tu}"
                cung_tu = [x for x in cung_ten if x[1] == tu]
                if cung_tu:
                    cb.append(f"{f.name}: cụm của {nhan} lệch chữ với {ten0}: {_lech(cung_tu[0][2], cum)}")
                else:
                    cb.append(f"{f.name}: {nhan} ghi còn hiệu lực ở {ten0} nhưng bảng hồi này không có "
                              f"(đổi trạng thái thì sửa cột Tới cho đúng cảnh)")
        truoc = (f.name, p_cuoi, n_max, tt)


def canh_bao_moc(nhip: list[str], hoi: list[Path], tm: Path, cb: list[str]) -> None:
    """Móc mở phim (`kien-thuc/moc-mo-phim.md`): N01 mức ≥ 4; cảnh N01 nhiều shot, không lời bình, đủ dài; có nhạc móc."""
    n01 = next((h for h in bang(nhip, "Bảng nhịp") if h.get("Mã", "").strip() == "N01"), None)
    if n01 and n01.get("Mức", "").strip().isdigit() and int(n01["Mức"]) < 4:
        cb.append(f"00-nhip.md: N01 là móc, mức {n01['Mức'].strip()} (cần 4; moc-mo-phim.md)")
    canh = [c for f in hoi for c in _canh(_dong(f))]
    moc = [c for c in canh if 1 in c[2]]
    if not moc:
        return
    phim_30 = clip_phim(dong_cap_phim(nhip)[1]) == 30
    for p, giay, _, than in moc:
        if phim_30 and giay == 30:
            cb.append(f"hoi-1.md: {p} là cảnh móc N01 30s; phim Clip: 30s giữ móc 2–3 cảnh 15s (`phan-canh-30s.md`)")
        if "cú máy liền" in _o(than, "Cách dựng").lower():
            cb.append(f"hoi-1.md: {p} là cảnh móc N01 mà dựng một cú máy liền (cần 6 đến 8 shot hard cut)")
        lb = _o(than, "Lời bình")
        if lb and not re.match(r"(không|none)\b", lb.lower()):
            cb.append(f"hoi-1.md: {p} là cảnh móc N01 mà có lời bình (móc không lời)")
    tong, giay_moc = sum(c[1] or 0 for c in canh), sum(c[1] or 0 for c in moc)
    toi_thieu = 25 if tong >= 600 else 15
    if giay_moc < toi_thieu:
        cb.append(f"hoi-1.md: móc N01 dài {giay_moc}s (cần từ {toi_thieu}s, mẫu 34s; moc-mo-phim.md mục 3)")
    hk = tm / "90-hau-ky.md"
    if not hk.exists() or "nhạc móc mở phim" not in hk.read_text(encoding="utf-8").lower():
        cb.append("90-hau-ky.md: thiếu mục '## Nhạc móc mở phim' (nhạc vào khung 1, hit từng lần suýt, cắt ở đích trú)")


def canh_bao_luat_chung(tep: list[Path], cb: list[str]) -> None:
    """Ba luật viết prompt (Spec 34 K4) trên chữ tiếng Anh từng dòng; dòng bảng (cụm cố định, trạng thái) là câu tả cố định."""
    for f in tep:
        for i, d in enumerate(_dong(f), 1):
            cb += [f"{f.name} dòng {i}: {x}" for x in luat_chung(d, hang=d.startswith("|"))]


def main() -> int:
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    dang_viet = None
    if "--dang-viet" in sys.argv:
        i = sys.argv.index("--dang-viet")
        dang_viet = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit() else None
        arg = [a for a in arg if a != str(dang_viet)]
    if not arg:
        print(__doc__)
        return 2
    goc = Path(arg[0])
    goc = goc if goc.is_dir() else thu_muc_phim() / arg[0]
    tm = goc / "kich-ban"
    loi: list = []
    if not (tm / "00-nhip.md").exists():
        print(f"LỖI: không thấy {tm / '00-nhip.md'}")
        return 1
    nhip = _dong(tm / "00-nhip.md")
    ma_nhip = kiem_nhip("00-nhip.md", nhip, loi)
    kiem_clip("00-nhip.md", nhip, loi)
    hoi = sorted(tm.glob("hoi-*.md"), key=_so_hoi)
    if ngan_sach(nhip):
        loi.append((0, "00-nhip.md: có dòng 'Ngân sách: hồi N …s' (ngân sách giây, web chặn khi lệch 15%); Spec 40 bỏ, xóa dòng này"))
    tat_ca_canh, nhip_dung = [], set()
    cb: list[str] = []
    kho = KHO_THU_PHAP.read_text(encoding="utf-8") if KHO_THU_PHAP.exists() else None
    ma_tp = ma_kho(kho) if kho is not None else None
    canh_tp = []
    if ma_tp is None:
        cb.append(f"thiếu {KHO_THU_PHAP.name}: chưa kiểm mã thủ pháp TPxx")
    for h in hoi:
        c, n, tom = kiem_hoi(h.name, _so_hoi(h), _dong(h), ma_nhip, loi, {})
        kiem_thoai(h.name, _dong(h), loi)
        if ma_tp is not None:
            kiem_thu_phap(h.name, _dong(h), ma_tp, loi)
            canh_tp += tp_canh(h.name, _dong(h))
        print(tom + (" (đang viết dở)" if _so_hoi(h) == dang_viet else ""))
        tat_ca_canh += c
        nhip_dung |= n
    kiem_tong(tat_ca_canh, ma_nhip, nhip_dung, bool(hoi), loi)
    if kho is not None:
        kiem_wow(canh_tp, ma_wow(kho), loi)
    canh_bao_hoi(hoi, canh_bao_nhip(nhip, cb), cb)
    canh_bao_moc(nhip, hoi, tm, cb)
    canh_bao_luat_chung([tm / "00-nhip.md", *hoi], cb)
    for _, cau in loi:
        print("LỖI:", cau)
    for cau in cb[:IN_TOI_DA]:
        print("CẢNH BÁO:", cau)
    if len(cb) > IN_TOI_DA:
        print(f"CẢNH BÁO: … và {len(cb) - IN_TOI_DA} cảnh báo nữa")
    if loi:
        return 1
    if dang_viet:
        print(f"Hồi {dang_viet} đang viết dở: chưa gộp kich-ban.md.")
        return 0
    gop(tm, hoi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
