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

# QUY ƯỚC CHẶT — user chốt 30/08 "tên khác bị báo lỗi, KHÔNG đoán bừa".
# Rà go-live 06/09 có ý nới (team quen "Hook"/"End") nhưng đó là đảo quyết định
# đã chốt: đoán bừa "chapter1" -> C1 có thể sai thứ tự chương. Giữ chặt, thay
# vào đó thông báo lỗi nói RÕ phải đặt tên gì.
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
    # CẤU TRÚC PHẲNG (user nêu 07/09): file đặt thẳng trong RenderY/ theo tên
    # `C1.txt` + `C1.mp3`. Kiểu thư mục con để None -> `make` tự dò như cũ.
    script: Path | None = None
    voice: Path | None = None
    srt: Path | None = None

    @property
    def phang(self) -> bool:
        return self.script is not None

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


def _la_ref(f: Path) -> bool:
    """`ref 1.mp4` là phim mẫu của tập, không phải voice chương."""
    return f.stem.lower().startswith("ref")


def _chuong_phang(goc: Path) -> list[Chuong]:
    """File đặt THẲNG trong RenderY/ -> chương. Cần đủ cặp .txt + audio cùng tên."""
    theo_ma: dict[str, dict] = {}
    for f in sorted(goc.iterdir()):
        if not f.is_file() or f.name.startswith("."):
            continue
        pt = phan_tich_ten(f.stem)
        if pt is None:
            continue
        ma, thu_tu, nhan = pt
        o = theo_ma.setdefault(ma, {"pt": pt})
        if f.suffix.lower() in _TEXT_EXTS:
            o.setdefault("script", f)
        elif f.suffix.lower() in _AUDIO_EXTS:
            o.setdefault("voice", f)
        elif f.suffix.lower() in _SRT_EXTS:
            o.setdefault("srt", f)
    ra = []
    for ma, o in theo_ma.items():
        if not (o.get("script") and o.get("voice")):
            continue                     # thiếu nửa cặp -> chưa phải chương
        _ma, thu_tu, nhan = o["pt"]
        ra.append(Chuong(path=goc, ma=ma, thu_tu=thu_tu, nhan=nhan,
                         co_script=True, co_voice=True, co_srt=bool(o.get("srt")),
                         script=o["script"], voice=o["voice"], srt=o.get("srt")))
    return ra


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
            loi.append(
                f"Thư mục '{d.name}' sai quy ước. Đổi tên thành: H (hook) · "
                f"C1 C2 C3... (chương) · E (kết). CHỈ chữ cái + số, không viết "
                f"'Hook' hay 'Chapter 1'.")
            continue
        ma, thu_tu, nhan = pt
        s, v, srt = _kiem_file(d)
        chuong.append(Chuong(path=d, ma=ma, thu_tu=thu_tu, nhan=nhan,
                             co_script=s, co_voice=v, co_srt=srt))

    # ---- CẤU TRÚC PHẲNG: file đặt thẳng trong RenderY/ ----
    # LI103 làm vậy và cách này RÕ hơn: 17 chương nhìn một màn hình là thấy hết,
    # khỏi tạo 17 thư mục chỉ để chứa 2 file. Thư mục con VẪN chạy nguyên (LI104).
    if not chuong:
        chuong += _chuong_phang(goc)

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
        ten = c.ma if c.phang else c.path.name
        if not c.co_script:
            loi.append(f"{c.nhan} ({ten}): thiếu kịch bản (.txt)")
        if not c.co_voice:
            loi.append(f"{c.nhan} ({ten}): thiếu voice (.mp3/.wav)")

    # ĐỊNH DẠNG BẮT BUỘC (user chốt 06/09): Hook + ít nhất 1 Chapter + End.
    # CẤM gộp cả tập vào 1 voice/1 script — nhịp chia khối và đồng kiểm/auto
    # đều tính theo CHƯƠNG, gộp là toàn bộ logic phía sau sai lặng lẽ.
    # voice ở gốc = gộp chắc chắn; .txt lẻ (ghi chú) vô hại — chỉ tính khi có voice
    # File PHẲNG đúng quy ước (C1.mp3...) là CHƯƠNG, không phải gộp cả tập.
    giong = [f.name for f in goc.iterdir()
             if f.is_file() and f.suffix.lower() in _AUDIO_EXTS
             and phan_tich_ten(f.stem) is None and not _la_ref(f)]
    gop = giong + ([f.name for f in goc.iterdir()
                    if f.is_file() and f.suffix.lower() == ".txt"
                    and phan_tich_ten(f.stem) is None] if giong else [])
    if gop:
        loi.append("Voice/script đang nằm THẲNG trong RenderY/ (" + ", ".join(gop[:3])
                   + ") — không được gộp cả tập; chia vào thư mục H / C1 / C2... / E.")
    if chuong:
        ma_co = {c.ma for c in chuong}
        if "H" not in ma_co:
            loi.append("Thiếu thư mục H (Hook) — định dạng bắt buộc: H / C1..Cn / E.")
        if not any(m.startswith("C") for m in ma_co):
            loi.append("Chưa có chương C nào (C1, C2...) — định dạng bắt buộc: H / C1..Cn / E.")
        if "E" not in ma_co:
            loi.append("Thiếu thư mục E (End) — định dạng bắt buộc: H / C1..Cn / E.")

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

        # Ref của CẢ TẬP (đặt ở RenderY/, mọi chương dùng chung) và ref RIÊNG từng
        # chương. Đếm tách bạch: gộp chung thì 1 video của tập bị đếm 5 lần cho 5
        # chương, nhân sự tưởng mình đặt thừa file.
        goc = thu_muc_rendery(tap)
        ref_tap, loi_ref = doc_ref(goc)
        ref_rieng = 0
        for c in chuong:
            refs, cb = doc_ref(c.path)
            ref_rieng += len(refs)
            loi_ref += [f"{c.nhan}: {x}" for x in cb]
        phan = []
        if ref_tap:
            phan.append(f"{len(ref_tap)} video ref cho CẢ TẬP")
        if ref_rieng:
            phan.append(f"{ref_rieng} video ref riêng của chương")
        if phan:
            nhac.append(" · ".join(phan) +
                        " — tool khớp nội dung rồi cắt vào timeline.")
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
