"""Cắt khung hình và ghép lưới có mốc giờ cho trợ lý phụ xem (Spec 40 D bước 2).

Chạy: py -3 cat_khung.py <phim.mp4> <khoang.json> <thu_muc_ra> [--day 1.5] [--thua 10] [--luoi 4x3]
Trong các khoảng của khoang.json (từ khoang_khong_thoai.py --ra): 1 khung mỗi --day giây.
Phần còn lại: 1 khung mỗi --thua giây. Mỗi khung in mốc giờ, ghép lưới theo thứ tự thời gian.
Ghi `luoi/luoi_NNN.jpg` và `luoi/muc-luc.txt` (lưới nào, từ mốc nào tới mốc nào, dày hay thưa).
"""
import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FONT = "C\\:/Windows/Fonts/arial.ttf"


def mmss(t: float) -> str:
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def cac_moc(khoang: list[list[float]], dai: float, day: float, thua: float) -> list[tuple[float, bool]]:
    """(giây, có phải khung dày) theo thứ tự thời gian."""
    trong = lambda t: any(a <= t <= b for a, b in khoang)
    ra = []
    for a, b in khoang:
        t = a
        while t < b:
            ra.append((round(t, 2), True))
            t += day
    t = 0.0
    while t < dai:
        if not trong(t):
            ra.append((round(t, 2), False))
        t += thua
    return sorted(set(ra))


def _cat(phim: Path, t: float, ra: Path) -> bool:
    nhan = mmss(t).replace(":", "\\:")
    vf = (f"scale=426:-2,drawtext=fontfile='{FONT}':text='{nhan}':x=6:y=6:fontsize=26:"
          "fontcolor=yellow:box=1:boxcolor=black@0.7:boxborderw=4")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(phim),
                        "-frames:v", "1", "-vf", vf, "-q:v", "4", str(ra)], capture_output=True)
    return r.returncode == 0 and ra.exists()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("phim")
    p.add_argument("khoang")
    p.add_argument("thu_muc")
    p.add_argument("--day", type=float, default=1.5)
    p.add_argument("--thua", type=float, default=10.0)
    p.add_argument("--luoi", default="4x3")
    a = p.parse_args()
    du = json.loads(Path(a.khoang).read_text(encoding="utf-8"))
    moc = cac_moc(du["khoang"], du["dai"], a.day, a.thua)
    goc = Path(a.thu_muc)
    khung, luoi = goc / "khung", goc / "luoi"
    for d in (khung, luoi):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    with ThreadPoolExecutor(6) as ex:
        ok = list(ex.map(lambda x: _cat(Path(a.phim), x[1][0], khung / f"k_{x[0]:05d}.jpg"), enumerate(moc)))
    hong = [mmss(moc[i][0]) for i, o in enumerate(ok) if not o]
    for h in hong:
        print(f"LỖI cắt khung {h}")
    c, h = (int(x) for x in a.luoi.split("x"))
    n = c * h
    dong_ml = []
    for i in range(0, len(moc), n):
        nhom = moc[i:i + n]
        ten = f"luoi_{i // n + 1:03d}.jpg"
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-start_number", str(i), "-i", str(khung / "k_%05d.jpg"),
                            "-frames:v", str(len(nhom)), "-vf", f"tile={a.luoi}", "-frames:v", "1", "-q:v", "4",
                            str(luoi / ten)], capture_output=True)
        if r.returncode:
            print(f"LỖI ghép {ten}: {r.stderr.decode(errors='replace')[-200:]}")
        so_day = sum(1 for _, d in nhom if d)
        kieu = "dày" if so_day == len(nhom) else "thưa" if so_day == 0 else "lẫn"
        dong_ml.append(f"{ten}\t{mmss(nhom[0][0])}–{mmss(nhom[-1][0])}\t{kieu}")
    (luoi / "muc-luc.txt").write_text("\n".join(dong_ml) + "\n", encoding="utf-8")
    so_day = sum(1 for _, d in moc if d)
    print(f"{len(moc)} khung ({so_day} dày, {len(moc) - so_day} thưa), {len(dong_ml)} lưới, {len(hong)} lỗi")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())
