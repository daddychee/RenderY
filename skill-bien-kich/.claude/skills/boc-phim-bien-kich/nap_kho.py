"""Nạp muc.json vào kho biên kịch nếu đang ở máy chủ; máy editor thì chỉ in lời nhắn (không có DB).
Máy chủ = tìm thấy kiem-chung/nap_kho_bien_kich.py ở gốc (repo chính) hay thư mục cha của gốc (`skill bien kich` nằm trong repo chính).
Chạy: py -3 <thư mục skill>/nap_kho.py <muc.json> [--the-loai <mã>]"""
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[3]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("Chạy: py -3 nap_kho.py <muc.json> [--the-loai <mã>]")
        return 1
    for g in (GOC, GOC.parent):
        nap = g / "kiem-chung" / "nap_kho_bien_kich.py"
        if nap.exists():
            return subprocess.call([sys.executable, str(nap), *sys.argv[1:]])
    tl = sys.argv[sys.argv.index("--the-loai") + 1] if "--the-loai" in sys.argv[:-1] else "chưa rõ"
    print(f"MÁY EDITOR: không nạp. Nhắn chủ dự án: thư mục {Path(sys.argv[1]).resolve().parent}, thể loại {tl}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
