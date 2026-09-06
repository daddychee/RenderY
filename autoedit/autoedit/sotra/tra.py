r"""TRA 4 LỚP — hàm truy xuất cho Đường Dây (đợt 4 gọi; đợt 1 nghiệm thu logic).

Mô hình tập-giao (user chốt 06/09): L0 chủ thể tập là CỬA BẮT BUỘC, các lớp
còn lại cộng điểm L1 trực chỉ > L2 ngữ cảnh > L3 không khí; nguồn ref/kho được
ưu tiên nhẹ theo switch; luật 60s do caller lo (cần vị trí timeline).
Đây là bản đã nghiệm thu ở prototype V5 — giờ đọc từ db thay JSON.
"""

from __future__ import annotations

import re

from autoedit.sotra import db as sdb

DIEM = {"L1": 10.0, "L2": 6.0, "L3": 3.0}
DIEM_NEO = 2.0
DIEM_UU_TIEN_NGUON = 2.5


def _tokens(cum) -> set:
    if isinstance(cum, str):
        cum = [cum]
    return {w for c in (cum or []) for w in re.findall(r"[a-z]{4,}", str(c).lower())}


def tra(conn, lop: dict, so: int = 12, uu_tien_nguon: str = "",
        can_neo: bool = True, suat_ref: int = 2, seed: int = 0) -> list[dict]:
    """lop = {"L0": [...], "L1": [...], "L2": [...], "L3": [...]} -> ứng viên xếp
    hạng, mỗi cái kèm `lop` (tầng trúng) + `diem`. Khay chia nhóm theo `lop`.

    suat_ref: REF luôn được GIỮ CHỖ (bài học V5: điểm chữ Envato đè chết ref)."""
    l0, l1 = _tokens(lop.get("L0")), _tokens(lop.get("L1"))
    l2, l3 = _tokens(lop.get("L2")), _tokens(lop.get("L3"))
    # kéo ứng viên qua FTS bằng TOÀN BỘ từ của các lớp (OR) — rẻ hơn quét cả bảng
    moi_tu = l1 | l2 | l3 | l0
    if not moi_tu:
        return []
    fts = " OR ".join(f'"{t}"' for t in sorted(moi_tu))
    rows = conn.execute(
        "SELECT c.* FROM clip_fts f JOIN clip c ON c.id=f.id "
        "WHERE clip_fts MATCH ? AND c.trang_thai='song' LIMIT 800", (fts,)).fetchall()
    # REF lấy RIÊNG, không qua FTS (bài học V5: ref ít + từ khóa lệch ngôn ngữ
    # -> FTS bỏ rơi; suất giữ chỗ phải đến từ quét thẳng bảng, ref mỗi tập ít)
    da_co = {r["id"] for r in rows}
    rows = list(rows) + [r for r in conn.execute(
        "SELECT * FROM clip WHERE nguon='ref' AND trang_thai='song' LIMIT 600")
        if r["id"] not in da_co]

    cham, refs = [], []
    for r in rows:
        c = dict(r)
        # vat_the + loi_quanh PHẢI vào điểm (user bắt 06/09: cùng một câu mà
        # khay ref ra cảnh chẳng liên quan): vat_the là vật NHÌN THẤY trong
        # hình (giàu nghĩa nhất của ref), loi_quanh là lời quanh cảnh — thiếu
        # cả hai thì mọi ref 0 điểm, suất giữ chỗ lấy đại 2 cảnh đầu bảng.
        chu = " ".join(str(c.get(k) or "")
                       for k in ("tieu_de", "vat_the", "loi_quanh") + sdb.TRUC)
        tt = _tokens([chu])
        la_ref = c["nguon"] in ("ref",)
        co_neo = bool(c.get("geo")) or c["nguon"] in ("ref", "kho")
        # CỬA L0: thuộc thế giới video (neo địa lý HOẶC trúng chủ thể tập)
        if can_neo and not (co_neo or la_ref or (tt & l0)):
            continue
        s1, s2, s3 = len(tt & l1), len(tt & l2), len(tt & l3)
        if not (s1 or s2 or s3) and not la_ref:
            continue
        tang = "L1" if s1 else ("L2" if s2 else "L3")
        d = s1 * DIEM["L1"] + s2 * DIEM["L2"] + s3 * DIEM["L3"]
        d += DIEM_NEO if co_neo else 0
        if uu_tien_nguon and c["nguon"] == uu_tien_nguon:
            d += DIEM_UU_TIEN_NGUON
        c["lop"], c["diem"] = tang, round(d, 1)
        (refs if la_ref else cham).append(c)

    cham.sort(key=lambda c: -c["diem"])
    # ref đồng điểm: RẢI theo seed (mỗi khối một seed) — không thì cả tập bị
    # đề xuất đúng 2 cảnh đầu bảng cho mọi câu (triệu chứng user thấy 06/09)
    refs.sort(key=lambda c: (-c["diem"], hash((c["id"], seed)) % 9973))
    # cân nhóm: tối đa 6 mỗi tầng để khay luôn đủ 4 tầng lựa chọn
    gio = {"L1": 0, "L2": 0, "L3": 0}
    ra = []
    for c in cham:
        if gio[c["lop"]] >= 6:
            continue
        gio[c["lop"]] += 1
        ra.append(c)
        if len(ra) >= so:
            break
    return ra + refs[:suat_ref]
