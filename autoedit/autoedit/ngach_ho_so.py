r"""HỒ SƠ NGÁCH — "ngách này quay ai, quay cái gì" (QĐ18, user chốt 18/09/2026).

Vì sao cần: cổng QĐ15 chặn cứng 422 khi ngách chưa khai nhân vật, mà đo trên
danh bạ thật 18/09 thì **13/16 ngách chưa khai** — gồm X FILE (`N-003`) vừa mở.
Đường khai duy nhất đang có là biến môi trường `RENDERY_NGACH_NHAN_VAT`, còn
câu báo lỗi lại chỉ sang "trang Cài đặt" — trang đó **không còn** trong giao
diện đang chạy (chỉ còn trong `index_cu.html`). Tức là đang bít cửa.

**Hai thứ mới:**

1. `loc_nguoi=False` — *"không lọc theo người"*. X FILE nói về ĐỒ VẬT; ép khai
   tuổi/chủng tộc là bịa luật cho ngách không cần. Trước đây "đã khai" được SUY
   RA từ "có nhân vật", nên không có cách nào nói "tôi cố ý không lọc".
2. Hồ sơ là **FILE trong kho dữ liệu**, không nhét `.env`: sửa được bằng giao
   diện, và ghi được AI DUYỆT + DUYỆT LÚC NÀO — `.env` không ghi nổi hai thứ đó.

**Thứ tự ưu tiên:** hồ sơ > `.env` > mặc định trong code. Hồ sơ là thứ người
bấm Duyệt trên màn hình, nó phải thắng dòng `.env` gõ tay từ đời nào.

Đặt cạnh Sổ Tra (`resolve_data_root()/ho_so_ngach`) vì đây là dữ liệu của MÁY
NÀY, không phải của bản checkout.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from autoedit.packager.machine import resolve_data_root

# Mã đi thẳng từ HTTP vào tên file — chặn ở đây, đừng tin phía gọi.
MA_HOP_LE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,39}")


def thu_muc() -> Path:
    return resolve_data_root() / "ho_so_ngach"


def _duong(ma: str) -> Path | None:
    k = (ma or "").strip().upper()
    if not MA_HOP_LE.fullmatch(k):
        return None
    return thu_muc() / f"{k}.json"


def _sach_tu(x) -> list[str]:
    """Từ khoá: thường hoá, bỏ trùng, GIỮ THỨ TỰ (thứ tự là ý của người duyệt)."""
    ra: list[str] = []
    if not isinstance(x, (list, tuple)):
        return ra
    for t in x:
        t = str(t or "").strip().lower()
        if t and t not in ra:
            ra.append(t)
    return ra


def _sach_nhan_vat(x) -> dict:
    if not isinstance(x, dict):
        return {}
    return {str(k).strip(): _sach_tu(v) for k, v in x.items()
            if isinstance(v, (list, tuple)) and _sach_tu(v)}


def doc(ma: str) -> dict | None:
    """Hồ sơ của một ngách, chưa có / hỏng -> None (KHÔNG ném).

    Ném ở đây là cả team không nộp được tập — y lý lẽ fail-open của `ngach.py`.
    """
    f = _duong(ma)
    if f is None:
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return d if isinstance(d, dict) else None


def luu(d: dict) -> dict:
    """Ghi hồ sơ — ATOMIC (ghi file tạm rồi `os.replace`).

    Máy mất điện giữa chừng mà hồ sơ cụt thì ngách đó tắc cổng nộp tập.
    """
    ma = str(d.get("ma") or "").strip().upper()
    f = _duong(ma)
    if f is None:
        raise ValueError(f"mã ngách không hợp lệ: {d.get('ma')!r}")
    loc = bool(d.get("loc_nguoi"))
    ra = {
        "ma": ma,
        "ten": str(d.get("ten") or "").strip(),
        # Khai rõ "không lọc" là MỘT LỜI KHAI, không phải bỏ trống.
        "loc_nguoi": loc,
        "nhan_vat": _sach_nhan_vat(d.get("nhan_vat")) if loc else {},
        "vat_the": _sach_tu(d.get("vat_the")),
        # Nơi chốn ngách CHẤP NHẬN (QĐ18b). Rỗng = ngách không gắn nơi chốn,
        # clip có nơi chốn bị `tra` loại. Khác «địa danh của TẬP» vốn là luật
        # chặt theo từng tập.
        "dia_ly": _sach_tu(d.get("dia_ly")),
        "nguon": d.get("nguon") if isinstance(d.get("nguon"), dict) else {},
        "nguoi_duyet": str(d.get("nguoi_duyet") or "").strip(),
        "duyet_luc": (str(d.get("duyet_luc") or "").strip()
                      or datetime.now().isoformat(timespec="seconds")),
    }
    f.parent.mkdir(parents=True, exist_ok=True)
    tam = f.with_name(f.name + ".tam")
    tam.write_text(json.dumps(ra, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tam, f)
    return ra


def liet_ke() -> list[dict]:
    """Mọi hồ sơ đã lưu. Gốc kho biến mất -> [] (fail-open)."""
    try:
        fs = sorted(thu_muc().glob("*.json"))
    except Exception:  # noqa: BLE001
        return []
    return [d for d in (doc(f.stem) for f in fs) if d]
