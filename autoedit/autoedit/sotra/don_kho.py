"""Dọn kho MỘT LẦN — bỏ thứ không còn lý do tồn tại (đợt 2, 08/09/2026).

User chốt 07/09: *"ngoài ref, tôi không cần lưu vĩnh viễn cái gì cả... Bởi sau
khi clip được dựng xong có chứa các stock đó, thì lần tới cần sử dụng, video
được tạo ra lần trước sẽ chính là ref của lần sau"* và *"stock nào đã được
download tức là đã được dùng thì giữ lại. nhưng phải đúng từ khóa"*.

Đo thật trên kho 08/09: envato 5.149 dòng nhưng chỉ **102 từng tải** và **20
từng lên timeline**; 5.102 dòng còn lại chưa bao giờ là gì ngoài một cái link
preview — mà link preview thì CHẾT (chạy chương H: 2/9 clip người dựng chọn đã
bị gỡ khỏi Envato). Giữ chúng chỉ để khay ứng viên đầy lên bằng hàng không tải
được.

GIỮ LẠI ba loại, kể cả khi không có file: đã tải (`path_local`), đã lên
timeline (`len_final`), có giấy phép (`giay_phep` — chứng từ đã trả tiền).
"""

from __future__ import annotations

import re
import sqlite3

# Từ ngắn hơn thế này không đủ đặc trưng để kết luận khớp/lệch ("in", "of").
DAI_TOI_THIEU = 4


def _tu(s: str) -> set[str]:
    return {t for t in re.split(r"[^0-9a-zA-ZÀ-ỹ]+", (s or "").lower()) if t}


def lech_tu_khoa(tieu_de: str, tu_khoa: str) -> bool:
    """Tiêu đề clip có LỆCH khỏi từ khoá đã hút nó về không?

    Khớp theo GỐC TỪ (4 ký tự đầu) chứ không phải khớp nguyên chữ: "market"
    hút về "Crowded markets in Kabul" là đúng hàng, khớp nguyên chữ sẽ kết tội
    oan vì "markets" ≠ "market".

    Không có từ khoá (clip vào kho bằng đường khác) thì KHÔNG kết tội.
    """
    tk = {t for t in _tu(tu_khoa) if len(t) >= DAI_TOI_THIEU}
    if not tk:
        return False
    goc = {t[:DAI_TOI_THIEU] for t in _tu(tieu_de) if len(t) >= DAI_TOI_THIEU}
    return not any(t[:DAI_TOI_THIEU] in goc for t in tk)


_GIU = ("COALESCE(c.path_local,'')<>'' "
        "OR EXISTS(SELECT 1 FROM su_kien s WHERE s.clip_id=c.id AND s.loai='len_final') "
        "OR EXISTS(SELECT 1 FROM giay_phep g WHERE g.clip_id=c.id)")


def _xoa(conn: sqlite3.Connection, ids: list[str]) -> int:
    for cid in ids:
        conn.execute("DELETE FROM clip WHERE id=?", (cid,))
        conn.execute("DELETE FROM clip_fts WHERE id=?", (cid,))
    conn.commit()
    return len(ids)


def liet_ke_preview(conn: sqlite3.Connection, nguon: str = "envato") -> list[str]:
    return [r[0] for r in conn.execute(
        f"SELECT c.id FROM clip c WHERE c.nguon=? AND NOT ({_GIU})", (nguon,))]


def don_preview(conn: sqlite3.Connection, nguon: str = "envato",
                xoa: bool = False) -> int:
    """Xoá dòng CHỈ-LÀ-PREVIEW của `nguon`. `xoa=False` = đếm thử, không đụng."""
    ids = liet_ke_preview(conn, nguon)
    return _xoa(conn, ids) if xoa else len(ids)


def liet_ke_lech_tu_khoa(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Clip ĐÃ TẢI mà tiêu đề lệch từ khoá hút — giữ lại thì kho hết sạch."""
    return [r for r in conn.execute(
        "SELECT id, nguon, tieu_de, tu_khoa_hut, path_local FROM clip "
        "WHERE COALESCE(path_local,'')<>'' AND COALESCE(tu_khoa_hut,'')<>''")
        if lech_tu_khoa(r["tieu_de"], r["tu_khoa_hut"])]


def don_lech_tu_khoa(conn: sqlite3.Connection, xoa: bool = False) -> int:
    ds = liet_ke_lech_tu_khoa(conn)
    return _xoa(conn, [r["id"] for r in ds]) if xoa else len(ds)
