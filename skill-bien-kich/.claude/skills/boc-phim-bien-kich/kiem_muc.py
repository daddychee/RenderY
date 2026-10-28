"""Kiểm muc.json đúng định dạng nạp kho biên kịch, không nạp DB (luật chung với script nạp, ở luat_kho_bien_kich.py).

Chạy: py -3 <thư mục skill>/kiem_muc.py <muc.json>. Chạy được ở repo chính (đọc app/) và ở `skill bien kich/` (đọc cong-cu/, bản chép).
In dòng lỗi và số mục theo nhóm. Thoát 1 khi có lỗi.
"""
import json
import sys
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parents[3]              # gốc repo chính hay gốc "skill bien kich"
sys.stdout.reconfigure(encoding="utf-8")
for p in (GOC / "app", GOC / "cong-cu"):
    if (p / "luat_kho_bien_kich.py").exists():
        sys.path.insert(0, str(p))
        break
from luat_kho_bien_kich import kiem_file  # noqa: E402


def main() -> int:
    ds = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    loi = kiem_file(ds)
    for d in loi:
        print(f"LỖI {d}")
    if isinstance(ds, list):
        dem = Counter(m.get("nhom") for m in ds if isinstance(m, dict))
        print(f"{len(ds)} mục ({', '.join(f'{k} {v}' for k, v in sorted(dem.items()))}), {len(loi)} lỗi")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
