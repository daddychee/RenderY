"""In đầy đủ các mục kho thủ pháp biên kịch theo mã (Spec 40 D "Cách biên kịch đọc kho"). Chỉ thư viện chuẩn, chỉ đọc
kien-thuc/kho/*/*.md, chạy độc lập.

    py -3 cong-cu/doc_kho.py KB07 KB35 ...          (hay KB07,KB35)
    py -3 cong-cu/doc_kho.py --hoi <00-nhip.md> <số hồi>   (các mã KB ở bảng nhịp và bảng phân clip, những nhịp thuộc hồi đó)

In theo thứ tự mã đưa vào. Mã không có trong kho thì in dòng báo; thoát 1 sau khi in các mã còn lại.
"""
import re
import sys
from pathlib import Path

KHO = Path(__file__).resolve().parent.parent / "kien-thuc" / "kho"
RE_MA = re.compile(r"\bKB\s*0*(\d+)\b", re.I)
RE_MUC = re.compile(r"^## (KB\d+)\b", re.M)


def chuan(ma: str) -> str | None:
    m = RE_MA.fullmatch(ma.strip())
    return f"KB{int(m.group(1)):02d}" if m else None


def doc(kho: Path = KHO) -> dict[str, str]:
    """Mã → toàn văn mục (từ dòng `## KBxx` tới trước mục kế), kèm thư mục thể loại và file ở cuối dòng tiêu đề. Bỏ mục lục."""
    ra = {}
    for f in sorted(kho.glob("*/*.md")):
        if f.name.startswith("muc-luc"):
            continue
        vb = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        dau = [m.start() for m in RE_MUC.finditer(vb)] + [len(vb)]
        for a, b in zip(dau, dau[1:]):
            tieu_de, _, than = vb[a:b].strip().partition("\n")
            ra[RE_MUC.match(tieu_de).group(1)] = f"{tieu_de} ({f.parent.name}/{f.name})\n{than}"
    return ra


def ma_cua_hoi(van_ban: str, hoi: int) -> list[str] | None:
    """Mã KB ở bảng nhịp (khung) rồi bảng phân clip, các dòng có nhịp thuộc hồi `hoi` (theo mục Ba hồi). None khi không thấy hồi đó."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dem_phan_canh as dpc
    pham_vi = [(a, b) for h, a, b, _ in dpc.RE_BA_HOI.findall(van_ban) if int(h) == hoi]
    if not pham_vi:
        return None
    tu, toi = int(pham_vi[0][0]), int(pham_vi[0][1])
    ra, dong = [], van_ban.replace("\r\n", "\n").split("\n")
    for h in dpc.bang(dong, "Bảng nhịp") + dpc.bang(dong, "Bảng phân clip"):
        n = dpc._ma(dpc._o(h, "Mã") or dpc._o(h, "Nhịp"))
        if n is not None and tu <= n <= toi:
            ra += [f"KB{int(x):02d}" for x in RE_MA.findall(" ".join(h.values()))]
    return list(dict.fromkeys(ra))


def main(argv: list[str], kho: Path = KHO) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if argv[:1] == ["--hoi"]:
        if len(argv) != 3 or not argv[2].isdigit():
            print("Cách chạy: py -3 cong-cu/doc_kho.py --hoi <00-nhip.md> <số hồi>")
            return 2
        ds = ma_cua_hoi(Path(argv[1]).read_text(encoding="utf-8"), int(argv[2]))
        if ds is None:
            print(f"LỖI: không thấy 'Hồi {argv[2]} (Nxx–Nyy, ~k%)' ở mục Ba hồi của {argv[1]}")
            return 1
        if not ds:
            print(f"Hồi {argv[2]}: bảng phân clip chưa ghi mã KB nào.")
            return 0
        print(f"Hồi {argv[2]}: {', '.join(ds)}\n")
    else:
        ds = [x for a in argv for x in a.split(",") if x.strip()]
        if not ds:
            print(__doc__.strip().splitlines()[2].strip())
            return 2
    kho_muc = doc(kho)
    thieu = []
    for ma in ds:
        m = chuan(ma)
        if m in kho_muc:
            print(kho_muc[m] + "\n")
        else:
            thieu.append(ma)
            print(f"KHÔNG CÓ: {ma} không có trong kho (chưa duyệt, thuộc thể loại chưa xuất, hay gõ sai)\n")
    return 1 if thieu else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
