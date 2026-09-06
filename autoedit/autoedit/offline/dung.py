r"""Đổ ỨNG VIÊN + chọn mặc định cho các khối — pha 2 của Offline.

Ứng viên tra từ Library (sotra.tra — 4 lớp giao nhau, suất REF giữ chỗ).
Chọn mặc định theo bộ luật nghiệm thu ở prototype V5:
  - luật 60s: cùng clip không xuất hiện 2 lần trong cửa sổ
  - chốt neo: mỗi CHOT_NEO_S phải có >=1 khối lớp trực chỉ
  - cấm 3 khối liền cùng lớp không khí (trôi thành slideshow)
"Thắng ở đây" chỉ là ĐỀ XUẤT — điểm chất lượng thật chờ phản biện ngoài
(người thay/khóa sổ/retention) ghi vào su_kien.
"""

from __future__ import annotations

CUA_SO_LAP_S = 60.0
CHOT_NEO_S = 30.0


def do_ung_vien(conn, khoi: list, lop, chu_the_tap: list[str],
                uu_tien_nguon: str = "", so_moi_khoi: int = 12) -> list[list[dict]]:
    """Mỗi khối một danh sách ứng viên (đã xếp lớp/điểm) từ Library."""
    from autoedit.sotra.tra import tra

    ra = []
    for i, k in enumerate(khoi):
        o = lop[i]
        uv = tra(conn, {"L0": chu_the_tap, "L1": o.truc_chi,
                        "L2": o.ngu_canh, "L3": o.khong_khi},
                 so=so_moi_khoi, uu_tien_nguon=uu_tien_nguon,
                 can_neo=bool(o.neo))
        ra.append([{"id": c["id"], "nguon": c["nguon"], "tieu_de": c["tieu_de"],
                    "lop": c["lop"], "diem": c["diem"],
                    "url_anh": c.get("url_anh", ""), "url_video": c.get("url_video", ""),
                    "geo": c.get("geo", ""), "dai_s": c.get("dai_s", 0),
                    # t0/t1 để UI gắn #t= — không có thì hover ref tải cả file 1GB
                    "t0": c.get("t0", 0), "t1": c.get("t1", 0)}
                   for c in uv])
    return ra


def chon_mac_dinh(khoi: list, ung_vien: list[list[dict]]) -> list[int]:
    """Chỉ số ứng viên mặc định mỗi khối (-1 = không có) theo 3 luật trên."""
    dung_luc: dict[str, float] = {}
    lop_gan: list[str] = []
    neo_cuoi = -999.0
    chon: list[int] = []
    for i, k in enumerate(khoi):
        uv = ung_vien[i]
        if not uv:
            chon.append(-1)
            continue
        can_l1 = (k.v0 - neo_cuoi) >= CHOT_NEO_S
        ba_l3 = len(lop_gan) >= 2 and lop_gan[-1] == "L3" and lop_gan[-2] == "L3"
        c = -1
        for khat_khe in (True, False):          # vòng 1 đủ luật, vòng 2 nới
            for j, u in enumerate(uv):
                gan = dung_luc.get(u["id"])
                if gan is not None and k.v0 - gan < CUA_SO_LAP_S:
                    continue                     # luật 60s là CỨNG cả 2 vòng
                if khat_khe and (can_l1 or ba_l3) and u["lop"] != "L1":
                    continue
                c = j
                break
            if c >= 0:
                break
        if c < 0:
            c = 0
        chon.append(c)
        u = uv[c]
        dung_luc[u["id"]] = k.v0
        lop_gan.append(u["lop"])
        if u["lop"] == "L1":
            neo_cuoi = k.v0
    return chon


def kiem_lap(khoi: list, ung_vien: list[list[dict]], chon: list[int]) -> list[int]:
    """Chỉ số các khối vi phạm 60s (UI tô đỏ; rào kiểm sau phân tích)."""
    xau = set()
    for i, k in enumerate(khoi):
        if chon[i] < 0:
            continue
        uid = ung_vien[i][chon[i]]["id"]
        for j in range(i):
            if chon[j] < 0:
                continue
            if (ung_vien[j][chon[j]]["id"] == uid
                    and abs(k.v0 - khoi[j].v0) < CUA_SO_LAP_S):
                xau.update((i, j))
    return sorted(xau)
