r"""ĐƠN HÀNG HÚT TỪ REF — "lấy ref làm gốc" (user chốt 12/09).

Mỗi cảnh ref đã được đọc hình (nhân vật + vật thể) nên nó TỰ SINH RA câu tìm
chính xác: từ tuổi của ngách + vật thể của cảnh. Đó đúng là thứ kho đang thiếu —
kho hiện tại hút cho ngách du lịch, nên trong 548 clip khay SH010 chỉ **64 clip**
đạt cửa nhân vật (già + da trắng), chia theo nguồn:

    ref 31/95 (33%) · envato 28/372 (7,5%) · pexels 5/62 (8%) · pixabay 0/16 (0%)

**Tỉ lệ 1 ref : 1 envato : 1 pexels : 1 pixabay là MỤC TIÊU CÓ BÁO CÁO, không
phải hạn mức cứng.** Tra thật ngoài kia 12/09: Pexels có hàng ("elderly men
running on the beach", "an elderly couple exercising together"); Pixabay thì
không — cùng từ khoá `elderly hands coffee cup` nó trả "pie fruit pie dessert",
"mount fuji morning clouds", tức bỏ qua hẳn chữ `elderly`. Ép một suất pixabay
mỗi khay = ép một clip sai vào khay, đúng cái bệnh đang chữa. Nên nguồn nào
không giao được thì **ghi là thiếu**, không lấp.

Chủng tộc KHÔNG vào câu tìm: kho stock không đánh chỉ mục việc đó, nhồi vào chỉ
làm câu lệch. Nó là CỬA lúc đọc hình (`doc_hinh`), không phải từ khoá lúc hút.

Chi phí: `hut_envato` là trang search CÔNG KHAI, không login (đã kiểm 06/09) —
trần 20 clip/giờ của `sourcer/subscription.py` chỉ áp cho TẢI bản có bản quyền,
không áp cho tìm. Nên 119 cảnh ref × 3 nguồn ≈ 360 lượt tìm là vài phút.
"""

from __future__ import annotations

import sqlite3

from autoedit.offline.dung import TU_DO_DAC
from autoedit.sotra import db as sdb

NGUON = ("envato", "pexels", "pixabay")
SO_VAT = 3          # 3 vật thể/câu: dài hơn thì stock không còn kết quả nào
TRAN_CAU = 40       # trần câu mỗi đơn — khỏi đốt cả buổi cho một tập

# Tuổi -> từ mà kho stock thật sự đánh chỉ mục (đo 12/09: `senior`/`elderly`/
# `older adult` đều ra hàng trên Pexels; `older` một mình thì không).
_TU_TUOI = {"older": "older adult", "child": "child", "young": "young adult",
            "middle": "middle aged", "mixed": "", "none": ""}


def cau_tim(nhan_vat: dict, vat_the: str, so_vat: int = SO_VAT) -> str:
    """Một câu tìm: từ tuổi của ngách + vật thể của cảnh ref (bỏ từ đồ đạc)."""
    vat = [v.strip().lower() for v in str(vat_the or "").split(",") if v.strip()]
    vat = [v for v in vat if not set(v.split()) <= TU_DO_DAC][:max(1, so_vat)]
    tuoi = (nhan_vat or {}).get("tuoi") or []
    dau = _TU_TUOI.get(str(tuoi[0]).lower(), "") if tuoi else ""
    return " ".join(x for x in ([dau] + vat) if x).strip()


def don_tu_ref(conn: sqlite3.Connection, tap: str, nhan_vat: dict,
               so_vat: int = SO_VAT, tran: int = TRAN_CAU) -> list[str]:
    """Danh sách câu tìm KHÔNG TRÙNG, sinh từ các cảnh ref CỦA TẬP này.

    Cảnh ref không có `vat_the` thì bỏ: câu còn lại chỉ là "older adult", hút về
    một rổ vô hướng — thà không hút.
    """
    ra: list[str] = []
    thay: set[str] = set()
    for r in conn.execute(
            "SELECT vat_the FROM clip WHERE nguon='ref' AND trang_thai='song' "
            "AND tap=? AND COALESCE(vat_the,'')<>'' ORDER BY id", (tap,)):
        c = cau_tim(nhan_vat, r["vat_the"], so_vat)
        # chỉ có từ tuổi, không có vật nào -> vô hướng, bỏ
        if not c or c == cau_tim(nhan_vat, "", so_vat):
            continue
        if c in thay:
            continue
        thay.add(c)
        ra.append(c)
        if len(ra) >= tran:
            break
    return ra


def _tim_that(nguon: str, cau: str) -> list[dict]:
    from autoedit.sotra import hut

    return {"envato": hut.hut_envato, "pexels": hut.hut_pexels,
            "pixabay": hut.hut_pixabay}[nguon](cau)


def chay_don(conn: sqlite3.Connection, tap: str, nhan_vat: dict, tim=None,
             so_vat: int = SO_VAT, tran: int = TRAN_CAU, tam_tap: bool = False,
             log=None) -> dict:
    """Chạy đơn hàng: mỗi câu tìm hỏi cả 3 nguồn, nạp clip mới vào kho.

    Trả báo cáo {so_cau, theo_nguon, thieu, cau}. `thieu` là thứ user yêu cầu:
    "thiếu thì ghi sổ chứ không lấp".
    """
    tim = tim or _tim_that
    cau = don_tu_ref(conn, tap, nhan_vat, so_vat, tran)
    theo_nguon = {n: 0 for n in NGUON}
    thieu: list[str] = []
    for c in cau:
        for n in NGUON:
            try:
                ds = tim(n, c) or []
            except Exception as exc:  # noqa: BLE001
                thieu.append(f"{n} «{c}»: lỗi {type(exc).__name__} {str(exc)[:60]}")
                if log:
                    log(f"đơn hàng: {n} «{c}» LỖI {str(exc)[:60]}")
                continue
            if not ds:
                thieu.append(f"{n} «{c}»: không có kết quả")
                continue
            moi = 0
            for r in ds:
                r = dict(r)
                r["tu_khoa_hut"] = c
                if tam_tap:
                    r["tam_tap"] = tap
                try:
                    moi += bool(sdb.them_clip(conn, r))
                except Exception:  # noqa: BLE001
                    pass          # một clip rác không được giết cả đơn hàng
            theo_nguon[n] += moi
        conn.commit()
        if log:
            log(f"đơn hàng «{c}» -> " + " · ".join(f"{n} {theo_nguon[n]}" for n in NGUON))
    conn.commit()
    return {"so_cau": len(cau), "theo_nguon": theo_nguon, "thieu": thieu, "cau": cau}
