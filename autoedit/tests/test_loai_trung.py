r"""Loại trùng — user chốt 09/09 sau khi hút thật ra "117 mới, 3 trùng".

Đo trên kho thật 09/09 (8.472 clip stock):
  - **2.093 bản thừa (25%)** cùng NGUỒN + cùng TIÊU ĐỀ, khác id
  - **606/951 khay (64%)** có bản trùng; gộp lại bỏ được 1.565 ô (12%)
  - chỉ **7 nhóm** trùng đúng `url_video`

Vì sao KHÔNG xoá theo tiêu đề: soi 13 clip envato cùng tên "Aerial view of the
jungle, Ecuador." thì **khác id, khác `url_video`, khác `url_anh`** — chúng là
các clip KHÁC NHAU trong một bộ, tác giả đặt trùng tên. Xoá là mất hàng thật.

User chốt hai việc, khác nhau về bản chất:
  1. **Lúc HÚT: bỏ qua bản trùng URL** — cùng `url_video` là chắc chắn cùng một
     file, giữ lại là rác thật.
  2. **Trùng tiêu đề mà khác id/URL: GỘP hiển thị** — không xoá, chỉ dồn về một
     thẻ kèm "+N bản" như trang Library đã làm (`db.tim`, db.py:344-350). Khay
     Offline đi qua `tra()` nên chưa được gộp — đó là chỗ người dựng thấy 13 thẻ
     giống nhau.
"""

from __future__ import annotations

import sqlite3

import pytest

from autoedit.sotra import db as sdb
from autoedit.sotra import hut


@pytest.fixture
def kho(tmp_path):
    """Kho thật qua `db.mo` — KHÔNG dựng tay bằng `_SCHEMA`.

    `_SCHEMA` là bản gốc; các cột thêm sau (`vat_the`, `tam_tap`...) nằm ở phần
    migration trong `mo()`. Dựng tay là thiếu cột, test đỏ vì lý do không liên
    quan tới thứ đang kiểm.
    """
    return sdb.mo(tmp_path / "kho.db")


def _clip(cid, tieu_de="clip", nguon="envato", url_video="", **kw):
    return {"id": cid, "nguon": nguon, "tieu_de": tieu_de,
            "url_video": url_video or f"https://x/{cid}.mp4", **kw}


# ═══════════════ 1. LÚC HÚT: bỏ bản trùng URL ═══════════════

def test_hut_BO_QUA_ban_trung_url_video(kho):
    """Cùng `url_video` = cùng một file. Id khác chỉ là mã trang khác."""
    conn = kho
    sdb.them_clip(conn, _clip("envato:cu", url_video="https://x/CUNG.mp4"))
    moi = sdb.them_clip(conn, _clip("envato:moi", url_video="https://x/CUNG.mp4"))
    assert moi is False, "clip cùng url_video vẫn được thêm -> kho phình rác"
    assert conn.execute("SELECT COUNT(*) FROM clip").fetchone()[0] == 1


def test_hut_van_nhan_clip_KHAC_url(kho):
    """Không được chặn oan: khác file là hàng khác, dù trùng tiêu đề."""
    conn = kho
    sdb.them_clip(conn, _clip("envato:a", "Aerial jungle", url_video="https://x/a.mp4"))
    moi = sdb.them_clip(conn, _clip("envato:b", "Aerial jungle", url_video="https://x/b.mp4"))
    assert moi is True, "khác url_video là clip khác — không được bỏ"
    assert conn.execute("SELECT COUNT(*) FROM clip").fetchone()[0] == 2


def test_url_video_rong_thi_KHONG_gop_bua(kho):
    """Ref/kho không có `url_video`. Coi rỗng là 'trùng nhau' -> gộp sạch kho."""
    conn = kho
    sdb.them_clip(conn, _clip("ref:a", nguon="ref", url_video=""))
    moi = sdb.them_clip(conn, _clip("ref:b", nguon="ref", url_video=""))
    assert moi is True, "hai clip ref không url bị coi là trùng nhau"
    assert conn.execute("SELECT COUNT(*) FROM clip").fetchone()[0] == 2


def test_them_lai_CHINH_NO_van_la_cap_nhat(kho):
    """Cùng id thì vẫn upsert như cũ, không được biến thành 'bỏ qua'."""
    conn = kho
    sdb.them_clip(conn, _clip("envato:a", "tên cũ", url_video="https://x/a.mp4"))
    moi = sdb.them_clip(conn, _clip("envato:a", "tên mới", url_video="https://x/a.mp4"))
    assert moi is False
    r = conn.execute("SELECT tieu_de FROM clip WHERE id='envato:a'").fetchone()
    assert r[0] == "tên mới", "upsert theo id phải cập nhật nội dung"


def test_phien_hut_dem_ban_trung_url_vao_muc_TRUNG(kho):
    """Số user nhìn thấy phải thật: bỏ vì trùng URL vẫn là 'trùng', không phải 'mới'."""
    conn = kho
    ds = [_clip("envato:1", "A", url_video="https://x/CUNG.mp4"),
          _clip("envato:2", "B", url_video="https://x/CUNG.mp4"),
          _clip("envato:3", "C", url_video="https://x/rieng.mp4")]
    kq = hut.phien_hut(conn, ["tk"], ["envato"], so_trang=1,
                       _bo_hut={"envato": lambda tk, tr: ds})
    assert kq["moi"] == 2, f"phải 2 mới (1 bị trùng URL), được {kq}"
    assert kq["trung"] == 1, f"bản trùng URL phải tính vào 'trùng', được {kq}"


# ═══════════════ 2. KHAY: gộp trùng tiêu đề, KHÔNG xoá ═══════════════

def test_khay_GOP_ban_cung_nguon_cung_tieu_de():
    """13 clip cùng tên -> 1 thẻ. Người dựng thấy 13 thẻ y hệt là vô dụng."""
    uv = [{"id": f"envato:{i}", "nguon": "envato", "tieu_de": "Aerial jungle",
           "lop": "L2", "diem": 9 - i} for i in range(13)]
    ra = sdb.gop_ban_trung(uv)
    assert len(ra) == 1, f"phải gộp về 1 thẻ, còn {len(ra)}"
    assert ra[0]["so_ban"] == 13
    assert ra[0]["id"] == "envato:0", "phải giữ bản ĐIỂM CAO NHẤT làm đại diện"


def test_khay_GIU_du_cac_ban_de_van_chon_duoc():
    """Gộp là HIỂN THỊ, không phải xoá — phải mở ra chọn bản khác được."""
    uv = [{"id": "envato:a", "nguon": "envato", "tieu_de": "X", "lop": "L2", "diem": 9},
          {"id": "envato:b", "nguon": "envato", "tieu_de": "X", "lop": "L2", "diem": 8}]
    ra = sdb.gop_ban_trung(uv)
    assert [b["id"] for b in ra[0]["ban_khac"]] == ["envato:b"], (
        "mất bản còn lại -> người dựng không đổi sang bản khác được")


def test_khay_KHAC_nguon_thi_KHONG_gop():
    """Cùng tên nhưng envato và pexels là hai hàng khác nhau."""
    uv = [{"id": "envato:a", "nguon": "envato", "tieu_de": "X", "lop": "L2", "diem": 9},
          {"id": "pexels:a", "nguon": "pexels", "tieu_de": "X", "lop": "L2", "diem": 8}]
    assert len(sdb.gop_ban_trung(uv)) == 2


def test_khay_KHAC_tieu_de_thi_KHONG_gop():
    uv = [{"id": "envato:a", "nguon": "envato", "tieu_de": "X", "lop": "L2", "diem": 9},
          {"id": "envato:b", "nguon": "envato", "tieu_de": "Y", "lop": "L2", "diem": 8}]
    assert len(sdb.gop_ban_trung(uv)) == 2


def test_khay_tieu_de_RONG_thi_KHONG_gop():
    """Ref hay dùng tên chung ('woman', 'street'); rỗng thì càng không được gộp."""
    uv = [{"id": "ref:a", "nguon": "ref", "tieu_de": "", "lop": "L1", "diem": 9},
          {"id": "ref:b", "nguon": "ref", "tieu_de": "", "lop": "L1", "diem": 8}]
    assert len(sdb.gop_ban_trung(uv)) == 2


def test_khay_giu_nguyen_THU_TU_diem():
    uv = [{"id": "e:1", "nguon": "envato", "tieu_de": "A", "lop": "L2", "diem": 5},
          {"id": "e:2", "nguon": "envato", "tieu_de": "B", "lop": "L2", "diem": 9},
          {"id": "e:3", "nguon": "envato", "tieu_de": "A", "lop": "L2", "diem": 4}]
    assert [b["id"] for b in sdb.gop_ban_trung(uv)] == ["e:1", "e:2"]


def test_khay_khong_co_trung_thi_GIU_NGUYEN():
    uv = [{"id": "e:1", "nguon": "envato", "tieu_de": "A", "lop": "L2", "diem": 9},
          {"id": "e:2", "nguon": "envato", "tieu_de": "B", "lop": "L2", "diem": 8}]
    ra = sdb.gop_ban_trung(uv)
    assert len(ra) == 2 and all(b.get("so_ban", 1) == 1 for b in ra)


def test_khay_rong_khong_no():
    assert sdb.gop_ban_trung([]) == []


def test_KHUC_TRIM_khong_bi_chan_du_trung_url_cua_clip_me(kho):
    """Trim thừa kế `url_video` của clip mẹ nhưng là HÀNG MỚI (mốc in/out riêng).

    Chặn nó là người dựng cắt khúc xong không lưu được vào kho — suite bắt được
    09/09 qua `test_offline::test_api_trim_ghi_so_va_nap_vao_mieng`.
    """
    conn = kho
    sdb.them_clip(conn, _clip("envato:me", url_video="https://x/me.mp4"))
    moi = sdb.them_clip(conn, {**_clip("envato:me#2.00-6.50",
                                       url_video="https://x/me.mp4"),
                               "t0": 2.0, "t1": 6.5})
    assert moi is True, "khúc trim bị chặn oan vì trùng url clip mẹ"


def test_ban_DA_TAI_ve_may_khong_bi_chan(kho):
    """Có `path_local` là hàng thật đã tải — không được coi là bản trùng."""
    conn = kho
    sdb.them_clip(conn, _clip("envato:a", url_video="https://x/CUNG.mp4"))
    moi = sdb.them_clip(conn, {**_clip("envato:b", url_video="https://x/CUNG.mp4"),
                               "path_local": r"F:\kho\b.mp4"})
    assert moi is True, "bản đã tải về máy bị chặn oan"


def test_so_ban_KHONG_bi_roi_khi_do_vao_khay(kho):
    """`do_ung_vien` chép theo DANH SÁCH TRẮNG — quên `so_ban` là mất nhãn.

    Lỗi im lặng: khay vẫn gộp đúng, chỉ nhãn "+N bản" biến mất, không báo gì.
    """
    from types import SimpleNamespace as NS

    from autoedit.offline.dung import do_ung_vien

    conn = kho
    for i in range(4):
        sdb.them_clip(conn, {**_clip(f"envato:{i}", "central market scene",
                                     url_video=f"https://x/{i}.mp4"),
                             "tag_nguon": "tieu_de"})
    conn.commit()
    lop = [NS(truc_chi=["market"], ngu_canh=[], khong_khi=[], neo=False)]
    ra = do_ung_vien(conn, [NS(v0=0.0, v1=3.0, tho=0.0)], lop, [], so_moi_khoi=12)
    gop = [c for c in ra[0] if c.get("so_ban", 1) > 1]
    assert gop, "khay mất trường so_ban -> nhãn '+N bản' không bao giờ hiện"
    assert "ban_khac" not in gop[0], "chép cả ban_khac vào hợp đồng -> phình file"


def test_tra_da_GOP_san_khi_tra_ve_khay(kho):
    """Điểm nối thật: `tra()` là đường khay Offline đi qua."""
    from autoedit.sotra import tra as mtra

    conn = kho
    for i in range(5):
        sdb.them_clip(conn, _clip(f"envato:{i}", "Cùng một tên",
                                  url_video=f"https://x/{i}.mp4",
                                  tag_nguon="tieu_de"))
    conn.commit()
    ra = mtra.tra(conn, {"L0": [], "L1": ["tên"], "L2": [], "L3": []}, so=12)
    ten = [c for c in ra if c["tieu_de"] == "Cùng một tên"]
    assert len(ten) <= 1, f"khay còn {len(ten)} bản cùng tên — chưa gộp"
