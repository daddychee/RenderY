"""Tìm khoảng không thoại từ phụ đề có mốc giờ (Spec 40 D bước 2).

Chạy: py -3 khoang_khong_thoai.py <phu_de.vtt|.srt|.json> --dai <giây phim> [--nguong 8] [--ra khoang.json] [--thoai thoai.txt]
In các khoảng không thoại từ --nguong giây, luôn cộng 90 giây đầu và 60 giây cuối, đã gộp chồng nhau.
Dòng chỉ có [music], [panting]... tính là không thoại. Phụ đề tự động YouTube: tính theo mốc từng từ,
vì mốc kết thúc câu hay kéo dài qua đoạn im.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

DAU, CUOI = 90.0, 60.0
GIAY_MOI_TU = 0.5          # một từ không có mốc riêng thì tính nửa giây
# Phụ đề tự động hay chép tiếng nhạc, tiếng gầm thành các từ này; câu chỉ có chúng tính là không thoại
TU_NHIEU = {"", "heat", "wow", "huh", "oh", "ah", "aah", "uh", "um", "hmm", "hm", "mm", "whoa", "ooh"}
_MOC = re.compile(r"(\d+):(\d{2}):(\d{2})[.,](\d{3})|(\d+):(\d{2})[.,](\d{3})")
_DONG_MOC = re.compile(r"^\s*([\d:.,]+)\s*-->\s*([\d:.,]+)")
_TU_MOC = re.compile(r"<(\d+:\d{2}:\d{2}\.\d{3})>")


def giay(s: str) -> float:
    m = _MOC.search(s)
    if not m:
        raise ValueError(f"mốc giờ lạ: {s}")
    if m.group(1):
        h, mi, se, ms = (int(m.group(i)) for i in range(1, 5))
    else:
        h, (mi, se, ms) = 0, (int(m.group(i)) for i in range(5, 8))
    return h * 3600 + mi * 60 + se + ms / 1000


def mmss(t: float) -> str:
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def _chu_that(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"\[[^\]]*\]|\([^)]*\)|♪|>>", " ", s)
    return " ".join(s.split())


def _doan_noi(bd: float, kt: float, van_ban: str) -> tuple[float, float] | None:
    """Khoảng có tiếng nói của một câu phụ đề, None nếu câu chỉ có nhạc, tiếng động."""
    chu = _chu_that(van_ban)
    if not chu or all(re.sub(r"\W", "", w.lower()) in TU_NHIEU for w in chu.split()):
        return None
    moc = [giay(x) for x in _TU_MOC.findall(van_ban)]
    if moc:
        return bd, min(kt, max(moc) + GIAY_MOI_TU + 0.3)
    return bd, min(kt, bd + GIAY_MOI_TU * len(chu.split()) + 1.0)


def doc_phu_de(duong: Path) -> list[tuple[float, float]]:
    return [(a, b) for a, b, _ in doc_cau(duong)]


def doc_cau(duong: Path) -> list[tuple[float, float, str]]:
    """(bắt đầu, kết thúc nói, chữ) từng câu có tiếng nói; bỏ dòng lặp của phụ đề tự động."""
    txt = duong.read_text(encoding="utf-8", errors="replace")
    ra = []
    if duong.suffix.lower() == ".json":
        du = json.loads(txt)
        if isinstance(du, dict):
            du = du.get("transcript") or du.get("segments") or du.get("data") or []
        for c in du:
            bd = float(c.get("start", c.get("offset", 0)))
            kt = float(c["end"]) if "end" in c else bd + float(c.get("duration", 0))
            d = _doan_noi(bd, kt, c.get("text", ""))
            if d:
                ra.append((*d, _chu_that(c.get("text", ""))))
        return sorted(ra)
    tu_dong = "<c>" in txt          # phụ đề tự động YouTube: mỗi câu chỉ dòng cuối là chữ mới
    for k in re.split(r"\n[ \t]*\n(?=[^\n]*-->|\d+\n)", txt.replace("\r", "")):
        dong = k.rstrip("\n").split("\n")
        for i, d in enumerate(dong):
            m = _DONG_MOC.match(d)
            if m:
                than = dong[i + 1:]
                if tu_dong:
                    if giay(m.group(2)) - giay(m.group(1)) < 0.05:
                        break                # câu chuyển tiếp 10 ms, chỉ lặp chữ cũ
                    than = than[-1:]
                doan = _doan_noi(giay(m.group(1)), giay(m.group(2)), "\n".join(than))
                if doan:
                    ra.append((*doan, _chu_that(" ".join(than))))
                break
    return sorted(ra)


def gop(ds: list[tuple[float, float]], khe: float = 0.0) -> list[tuple[float, float]]:
    ra: list[list[float]] = []
    for a, b in sorted(ds):
        if ra and a <= ra[-1][1] + khe:
            ra[-1][1] = max(ra[-1][1], b)
        else:
            ra.append([a, b])
    return [(a, b) for a, b in ra]


def khoang_khong_thoai(noi: list[tuple[float, float]], dai: float, nguong: float = 8.0) -> list[tuple[float, float]]:
    noi = gop(noi)
    im, truoc = [], 0.0
    for a, b in noi + [(dai, dai)]:
        if a - truoc >= nguong:
            im.append((truoc, min(a, dai)))
        truoc = max(truoc, b)
    im += [(0.0, min(DAU, dai)), (max(0.0, dai - CUOI), dai)]
    return gop(im)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("phu_de")
    p.add_argument("--dai", type=float, required=True, help="thời lượng phim (giây)")
    p.add_argument("--nguong", type=float, default=8.0)
    p.add_argument("--ra")
    p.add_argument("--thoai", help="ghi file chữ: mốc giờ + câu thoại, cho trợ lý phụ đọc")
    a = p.parse_args()
    noi = doc_phu_de(Path(a.phu_de))
    if not noi:
        print("LỖI: phụ đề không có câu thoại nào đọc được")
        return 1
    im = khoang_khong_thoai(noi, a.dai, a.nguong)
    for x, y in im:
        print(f"{mmss(x)}–{mmss(y)}  {y - x:.0f}s")
    tong = sum(y - x for x, y in im)
    print(f"{len(im)} khoảng, {tong:.0f}s xem dày / {a.dai:.0f}s phim ({tong / a.dai:.0%})")
    if a.ra:
        Path(a.ra).write_text(json.dumps({"dai": a.dai, "khoang": im}, ensure_ascii=False), encoding="utf-8")
    if a.thoai:
        cau = doc_cau(Path(a.phu_de))
        Path(a.thoai).write_text("".join(f"{mmss(x)}  {c}\n" for x, _, c in cau), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
