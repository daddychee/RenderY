# File chép từ app/luat_kho_bien_kich.py của repo GEN VIDEO bằng kiem-chung/dong_bo_skill_phim.py. Không sửa tay.
"""Luật kiểm mục kho biên kịch (Spec 40 mục D): nhãn và hàm kiểm thuần, không import app hay thư viện ngoài.
`app/kho_bien_kich.py` dùng lại; `kiem-chung/dong_bo_skill_phim.py` chép sang `skill bien kich/cong-cu/` cho skill `/boc-phim-bien-kich`."""

NHOM = {"khung": "Khung cả phim", "khoanh_khac": "Khoảnh khắc", "thoai": "Thoại"}
HOP_PHIM = {"it_thoai": "phim ít thoại", "nhieu_thoai": "phim nhiều thoại", "ca_hai": "phim ít và nhiều thoại"}
THE_LOAI = {"fantasy-drama": "Fantasy drama", "phieu-luu-ky-ao": "Phiêu lưu kỳ ảo", "drama-thoai": "Drama thoại",
            "drama-da-den": "Drama da đen Mỹ", "chung": "Dùng chung", "chua_xep": "Chưa xếp"}  # mã cũng là tên thư mục xuất
CHUA_XEP, CHUNG = "chua_xep", "chung"
CHU = ("ten", "nguyen_ly", "cach_phim_goc", "dat_o_dau", "dung_sai", "phim_nguon")      # trường chữ bắt buộc
BAT_BUOC = ("nhom", "hop_phim", *CHU, "cach_khac")
TUY_CHON = ("link", "moc_gio", "the_loai")


def khoa_nap(phim_nguon: str, ten: str) -> str:
    return " ".join(f"{phim_nguon} | {ten}".lower().split())


def kiem_muc(m, i: int) -> list[str]:
    """Dòng lỗi của mục thứ i (đếm từ 1); rỗng là hợp lệ."""
    if not isinstance(m, dict):
        return [f"mục {i}: không phải object"]
    ten = str(m.get("ten") or "").strip()
    dau = f"mục {i}" + (f" ({ten})" if ten else "")
    loi = [f"{dau}: thiếu {k}" for k in CHU if not isinstance(m.get(k), str) or not m[k].strip()]
    if m.get("nhom") not in NHOM:
        loi.append(f"{dau}: nhom phải là {' / '.join(NHOM)}")
    if m.get("hop_phim") not in HOP_PHIM:
        loi.append(f"{dau}: hop_phim phải là {' / '.join(HOP_PHIM)}")
    ck = m.get("cach_khac")
    if not isinstance(ck, list) or len([x for x in ck if isinstance(x, str) and x.strip()]) < 2:
        loi.append(f"{dau}: cach_khac phải là danh sách ít nhất 2 chuỗi")
    loi += [f"{dau}: {k} phải là chuỗi" for k in TUY_CHON if m.get(k) is not None and not isinstance(m[k], str)]
    if isinstance(m.get("the_loai"), str) and m["the_loai"].strip() and m["the_loai"].strip() not in THE_LOAI:
        loi.append(f"{dau}: the_loai phải là {' / '.join(THE_LOAI)}")
    thua = sorted(set(m) - set(BAT_BUOC) - set(TUY_CHON))
    if thua:
        loi.append(f"{dau}: trường lạ {', '.join(thua)}")
    return loi


def kiem_file(ds) -> list[str]:
    if not isinstance(ds, list) or not ds:
        return ["file phải là danh sách mục, không rỗng"]
    loi = [x for i, m in enumerate(ds, 1) for x in kiem_muc(m, i)]
    thay = {}
    for i, m in enumerate(ds, 1):
        k = khoa_nap(m.get("phim_nguon") or "", m.get("ten") or "")
        if k in thay:
            loi.append(f"mục {i}: trùng tên với mục {thay[k]} cùng phim nguồn")
        thay.setdefault(k, i)
    return loi
