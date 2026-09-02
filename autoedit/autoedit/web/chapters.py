r"""Nhận diện thư mục chương theo quy ước OUTLIERY — H / C<số> / E.

Mỗi tập có mã riêng (LI001, SH042, IN002...) và nằm rải khắp NAS theo series
(`Life In/Han Quoc/LI063-KOREA`, `Investigate/IN002`, `SH/KIM040`...). Nhân sự tạo
thư mục con `RenderY` trong thư mục tập, rồi trong đó là các chương:

```
F:\OutlierY Nas 2\Investigate\IN002\      ← thư mục tập (đã có voice/, visual/, .prproj)
└── RenderY\                              ← nhân sự tạo
    ├── H\    script.txt + voice.mp3      ← Hook (luôn đầu)
    ├── C1\                               ← Chapter 1
    ├── C2\
    └── E\                                ← End (luôn cuối)
```

Thứ tự trên timeline là **H → C1..Cn → E**, KHÔNG phải A-Z: sắp theo tên thì "E"
đứng trước "H" và "C10" đứng trước "C2" — sai cả hai đầu.

Quy ước CHẶT (user chốt 30/08/2026): chỉ nhận đúng `H`, `C<số>`, `E`. Tên khác bị
báo lỗi ngay trên UI thay vì âm thầm xếp sai — dựng nhầm thứ tự chương thì phải
dựng lại cả tập.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

THU_MUC_CON = "RenderY"          # tên thư mục con trong thư mục tập
# Thư mục KẾT QUẢ do chính tool tạo ra, nằm cạnh các chương. Không loại trừ thì nộp
# lại tập đã dựng bị chặn ngay ở bước Kiểm tra: "'Compose Timeline' sai quy ước"
# (31/08). Tên phải khớp compose.thu_muc_giao().
THU_MUC_GIAO = "Compose Timeline"

_HOOK = re.compile(r"^H$", re.IGNORECASE)
_CHAP = re.compile(r"^C(\d+)$", re.IGNORECASE)
_END = re.compile(r"^E$", re.IGNORECASE)

_TEXT_EXTS = {".txt", ".md", ".rtf"}
_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
_SRT_EXTS = {".srt"}


@dataclass
class Chuong:
    """1 chương đã nhận diện, kèm khoá sắp xếp."""

    path: Path
    ma: str            # H | C1 | C2 | E (viết hoa chuẩn)
    thu_tu: int        # 0 = Hook · 1..n = Chapter · 999999 = End
    nhan: str          # tên đọc được: "Hook" / "Chương 1" / "Kết"
    co_script: bool
    co_voice: bool
    co_srt: bool

    @property
    def du_file(self) -> bool:
        return self.co_script and self.co_voice


def phan_tich_ten(ten: str) -> tuple[str, int, str] | None:
    """Tên thư mục -> (mã chuẩn, thứ tự, nhãn). None nếu KHÔNG đúng quy ước."""
    t = ten.strip()
    if _HOOK.match(t):
        return "H", 0, "Hook"
    if _END.match(t):
        return "E", 999_999, "Kết"
    m = _CHAP.match(t)
    if m:
        so = int(m.group(1))
        # C0 vô nghĩa (Hook đã là mở đầu) — coi như sai quy ước, báo cho người sửa
        if so >= 1:
            return f"C{so}", so, f"Chương {so}"
    return None


def _kiem_file(d: Path) -> tuple[bool, bool, bool]:
    """(có script, có voice, có srt) trong thư mục chương."""
    try:
        exts = {f.suffix.lower() for f in d.iterdir() if f.is_file()}
    except OSError:
        return False, False, False
    return (bool(exts & _TEXT_EXTS), bool(exts & _AUDIO_EXTS), bool(exts & _SRT_EXTS))


def thu_muc_rendery(tap: Path) -> Path:
    """Thư mục chương của một tập. Nhận cả đường dẫn tập lẫn đường dẫn RenderY sẵn."""
    tap = Path(tap)
    if tap.name.lower() == THU_MUC_CON.lower():
        return tap
    return tap / THU_MUC_CON


def doc_chuong(tap: Path) -> tuple[list[Chuong], list[str]]:
    """Đọc các chương của 1 tập. Trả (danh sách đã SẮP ĐÚNG THỨ TỰ, lỗi).

    Lỗi trả về là thứ hiện thẳng cho nhân sự sửa, không phải log kỹ thuật.
    """
    goc = thu_muc_rendery(tap)
    if not goc.is_dir():
        return [], [f"Chưa có thư mục '{THU_MUC_CON}' trong {Path(tap).name} — "
                    f"tạo {goc} rồi đặt các chương H / C1 / C2 / E vào đó."]

    chuong: list[Chuong] = []
    loi: list[str] = []
    for d in sorted(goc.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name.lower() == THU_MUC_GIAO.lower():
            continue          # thư mục KẾT QUẢ của chính tool, không phải chương
        pt = phan_tich_ten(d.name)
        if pt is None:
            loi.append(f"'{d.name}' sai quy ước — chỉ nhận H (hook), C1/C2/... (chương), E (kết)")
            continue
        ma, thu_tu, nhan = pt
        s, v, srt = _kiem_file(d)
        chuong.append(Chuong(path=d, ma=ma, thu_tu=thu_tu, nhan=nhan,
                             co_script=s, co_voice=v, co_srt=srt))

    if not chuong and not loi:
        loi.append(f"Thư mục '{THU_MUC_CON}' trống — chưa có chương nào.")

    # Trùng mã: 2 thư mục cùng là C1 (vd 'C1' và 'c1') -> dựng sai thứ tự lặng lẽ
    da_thay: dict[str, str] = {}
    for c in chuong:
        if c.ma in da_thay:
            loi.append(f"Trùng mã {c.ma}: '{da_thay[c.ma]}' và '{c.path.name}'")
        else:
            da_thay[c.ma] = c.path.name

    for c in chuong:
        if not c.co_script:
            loi.append(f"{c.nhan} ({c.path.name}): thiếu kịch bản (.txt)")
        if not c.co_voice:
            loi.append(f"{c.nhan} ({c.path.name}): thiếu voice (.mp3/.wav)")

    chuong.sort(key=lambda c: c.thu_tu)
    return chuong, loi


def tom_tat(tap: Path) -> dict:
    """Tóm tắt cho UI: sẵn sàng chưa, mấy chương, thiếu gì."""
    chuong, loi = doc_chuong(tap)
    # Thiếu .srt KHÔNG chặn (Whisper nhận dạng được) nhưng phải báo trước: chậm hơn
    # và timestamp kém chính xác hơn .srt trích thẳng từ kịch bản.
    thieu_srt = [c.nhan for c in chuong if c.du_file and not c.co_srt]
    nhac = []
    # Video ref (02/09): báo TRƯỚC có mấy video, thiếu .srt cái nào. Bắt ở đây chứ
    # không để chạy 20 phút rồi mới biết (bài học 30/08).
    try:
        from autoedit.sourcer.refvideo import doc_ref

        co_ref, loi_ref = 0, []
        for c in chuong:
            refs, cb = doc_ref(c.path)
            co_ref += len(refs)
            loi_ref += [f"{c.nhan}: {x}" for x in cb]
        if co_ref:
            nhac.append(f"{co_ref} video ref sẽ được cắt vào timeline theo khớp ngữ nghĩa.")
        # Video ref thiếu .srt là NHẮC chứ không CHẶN: chương vẫn dựng được bằng
        # Pexels/kho như thường, chỉ mất phần footage từ video đó.
        nhac.extend(loi_ref[:4])
    except Exception:
        pass          # fail-open: hỏng phần ref KHÔNG chặn việc nộp
    if thieu_srt:
        nhac.append(f"{', '.join(thieu_srt)} chưa có .srt — tool sẽ tự nhận dạng "
                    f"giọng (chậm hơn ~1 phút/10 phút voice). Có .srt thì nhanh và "
                    f"khớp chữ chính xác hơn.")
    return {
        "tap": Path(tap).name,
        "duong_dan": str(Path(tap)),
        "rendery": str(thu_muc_rendery(tap)),
        "chuong": [{"ma": c.ma, "nhan": c.nhan, "thu_muc": c.path.name,
                    "srt": c.co_srt, "du_file": c.du_file} for c in chuong],
        "so_chuong": len(chuong),
        "san_sang": bool(chuong) and not loi,
        "loi": loi[:8],
        "nhac": nhac,
    }
