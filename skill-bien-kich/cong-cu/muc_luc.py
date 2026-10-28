"""In mục lục một file md: dòng bắt đầu, số dòng và ước lượng token của từng mục, để Read đúng mục cần bằng offset và limit
thay vì đọc cả file (CLAUDE.md mục token). Chạy: python <thư mục>/muc_luc.py <file.md> [file khác …]
(repo GEN VIDEO: kiem-chung/; thư mục skill lam phim: cong-cu/, bản chép bằng dong_bo_skill_phim.py)"""
import re
import sys
from pathlib import Path

# Tiếng Việt có dấu: khoảng 1,7 ký tự một token, đo trên phiên Claude Code thật 22/09/2026 (skill lam phim/NHAT-KY.md mục 23/09 tối).
# Trước là 2,6 nên số in ra thấp hơn thực tế khoảng 1,5 lần.
KY_TU_MOT_TOKEN = 1.7

sys.stdout.reconfigure(encoding="utf-8")
for ten in sys.argv[1:] or [None]:
    if ten is None:
        sys.exit(__doc__)
    dong = Path(ten).read_text(encoding="utf-8").split("\n")
    moc = [i for i, d in enumerate(dong) if re.match(r"#{1,3} ", d)] + [len(dong)]
    print(f"{ten}: {len(dong)} dòng, khoảng {sum(map(len, dong)) / KY_TU_MOT_TOKEN:.0f} token")
    for a, b in zip(moc, moc[1:]):
        print(f"  offset {a + 1:>4} limit {b - a:>3} · {sum(map(len, dong[a:b])) / KY_TU_MOT_TOKEN:>5.0f} tok · {dong[a][:90]}")
