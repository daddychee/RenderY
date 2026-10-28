"""Kiểm bảng nhịp thô phủ kín cả phim (Spec 40 D bước 3).

Chạy: py -3 kiem_phu_kin.py <bang-nhip-tho.md> --dai <giây phim> [--nguong 20]
Mỗi dòng có mốc giờ (`1:05`, `1:05–1:30`, `1:02:10`) được tính là nhắc tới quãng đó; dòng tiêu đề (#) bỏ qua.
LỖI: quãng hơn --nguong giây không dòng nào nhắc (kể cả đầu và cuối phim).
CẢNH BÁO: một dòng gộp quãng dài hơn 60 giây, chỉ tính hai đầu mốc. Thoát 1 khi có LỖI.
"""
import argparse
import re
import sys
from pathlib import Path

DONG_DAI = 60      # dòng gộp quãng dài hơn chừng này chỉ tính hai đầu mốc, tránh một dòng "phủ" cả đoạn
_T = r"(?:\d+:)?\d{1,2}:\d{2}"
_QUANG = re.compile(rf"({_T})\s*(?:[–—-]|->|→|đến)\s*({_T})")
_MOC = re.compile(rf"(?<![\d:])({_T})(?![\d:])")


def giay(s: str) -> float:
    so = [int(x) for x in s.split(":")]
    return so[0] * 3600 + so[1] * 60 + so[2] if len(so) == 3 else so[0] * 60 + so[1]


def mmss(t: float) -> str:
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def doc_quang(van_ban: str) -> list[tuple[float, float, int]]:
    """(bắt đầu, kết thúc, số dòng) cho mọi mốc giờ trong bảng."""
    ra = []
    for so, dong in enumerate(van_ban.splitlines(), 1):
        if dong.lstrip().startswith("#"):
            continue                          # tiêu đề phần không tính là tả
        con = dong
        for m in _QUANG.finditer(dong):
            a, b = giay(m.group(1)), giay(m.group(2))
            ra.append((min(a, b), max(a, b), so))
            con = con.replace(m.group(0), " ")
        for m in _MOC.finditer(con):
            t = giay(m.group(1))
            ra.append((t, t, so))
    return ra


def kiem(van_ban: str, dai: float, nguong: float = 20.0) -> tuple[list[str], list[str]]:
    quang = sorted(doc_quang(van_ban))
    loi, canh_bao = [], []
    for a, b, so in list(quang):
        if b - a > DONG_DAI:
            canh_bao.append(f"CẢNH BÁO dòng {so}: một dòng gộp {mmss(a)}–{mmss(b)} ({b - a:.0f}s), chỉ tính hai đầu mốc")
            quang.remove((a, b, so))
            quang += [(a, a, so), (b, b, so)]
    quang.sort()
    truoc = 0.0
    for a, b, _ in quang + [(dai, dai, 0)]:
        a = min(a, dai)
        if a - truoc > nguong:
            loi.append(f"LỖI quãng {mmss(truoc)}–{mmss(a)} ({a - truoc:.0f}s) không dòng nào nhắc")
        truoc = max(truoc, min(b, dai))
    return loi, canh_bao


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("bang")
    p.add_argument("--dai", type=float, required=True, help="thời lượng phim (giây)")
    p.add_argument("--nguong", type=float, default=20.0)
    a = p.parse_args()
    van_ban = Path(a.bang).read_text(encoding="utf-8")
    loi, canh_bao = kiem(van_ban, a.dai, a.nguong)
    for d in canh_bao + loi:
        print(d)
    print(f"{len(doc_quang(van_ban))} mốc, {len(loi)} lỗi, {len(canh_bao)} cảnh báo")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
