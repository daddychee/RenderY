"""Đánh lại mã phân cảnh sau khi người dựng chèn, bỏ cảnh (Spec 40 B: mã liền P01, P02…, không đuôi `-b` trong bản dán). Ghi đè các
file trong `kich-ban/`. Chép một lần từ `skill lam phim/cong-cu/danh_lai_ma.py` (28/09), bỏ việc ghi dòng `Ngân sách:` giây (Spec 40 C).

Cảnh chèn có tiêu đề `## P42-b · tên · 15s · Nxx` (30s ở phim `Clip: 30s`) đặt ngay sau P42 (thêm nữa `P42-c`). Công cụ:
- đánh lại mã mọi cảnh P01, P02… liên tục theo thứ tự hồi và thứ tự trong file;
- sửa mọi chỗ trỏ mã cũ (bảng trạng thái, khối thiết kế trận, tóm tắt hồi, dòng `- Gieo, gặt phần n: G01 P03, …` ở Để viết hồi sau,
  `90-hau-ky.md`) theo mã mới; P003 và P03 coi là một mã (ghi ra dạng 2 chữ số như tiêu đề).
Chạy được sau mỗi phần (trợ lý soát chèn `P42-b` trong phần vừa viết), không cần đợi cuối phim.
Không sửa file khác trong `kich-ban/` (như danh sách cảnh chèn, bỏ): file đó ghi mã trước khi đánh lại.
Chỉ in kết quả và dòng lỗi. Xong thì chạy `kiem_kich_ban.py <mã>`.

Chạy: python cong-cu/danh_lai_ma.py <mã phim | đường dẫn thư mục phim>"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
from cau_hinh import thu_muc_phim  # noqa: E402

RE_TIEU_DE = re.compile(r"^## (P\d{2,3}(?:-[a-z])?)(?![\w-])(.*)$")
RE_MA = re.compile(r"\bP\d{2,3}(?:-[a-z])?(?![\w-])")


def chuan(ma: str) -> str:
    """Khóa so mã: P003 và P03 là một cảnh (dòng `Gieo, gặt phần n:` có thể ghi 3 chữ số)."""
    so, _, duoi = ma[1:].partition("-")
    return f"P{int(so):02d}" + (f"-{duoi}" if duoi else "")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    goc = Path(sys.argv[1])
    goc = goc if goc.is_dir() else thu_muc_phim() / sys.argv[1]
    tm = goc / "kich-ban"
    hoi = sorted(tm.glob("hoi-*.md"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    if not hoi:
        print(f"LỖI: không thấy hồi nào trong {tm}")
        return 1
    doi, i = {}, 0
    for f in hoi:
        for d in f.read_text(encoding="utf-8").splitlines():
            k = RE_TIEU_DE.match(d)
            if not k:
                continue
            if chuan(k.group(1)) in doi:
                print(f"LỖI: {f.name} mã {k.group(1)} lặp hai lần; đặt tên khác (P42-b, P42-c) rồi chạy lại")
                return 1
            i += 1
            doi[chuan(k.group(1))] = f"P{i:02d}"
    doi_that = {a: b for a, b in doi.items() if a != b}
    if doi_that:
        for f in [tm / "00-nhip.md", *hoi, tm / "90-hau-ky.md"]:
            if not f.exists():
                continue
            van = f.read_text(encoding="utf-8")
            moi = RE_MA.sub(lambda m: doi.get(chuan(m.group()), m.group()), van)
            if moi != van:
                f.write_text(moi, encoding="utf-8")
    print(f"{i} cảnh; đổi mã {len(doi_that)} cảnh"
          + (f" (từ {next(iter(doi_that))} → {doi_that[next(iter(doi_that))]})" if doi_that else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
