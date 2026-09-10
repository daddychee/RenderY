r"""VIỆC F — pexels/pixabay đẩy xuống dưới envato trong khay.

User chốt 09/09: *"pexels/pixabay xấu hơn"* — **không loại, chỉ đẩy xuống**.
Thứ tự mong muốn: ref -> envato -> pexels -> pixabay. Nút lọc nguồn (việc E)
để người dựng tự gạt khi cần.

ĐO THẬT 10/09 trên 996 miếng production trước khi chọn mức phạt:

| Nguồn | Trong khay | Điểm trung vị |
|---|---|---|
| ref | 85.2% | 20.5 |
| envato | 9.0% | 10.0 |
| pexels | 0.2% | 8.0 |
| pixabay | 0.1% | 12.0 |

Khoảng cách điểm trong một khay: trung vị 13.0, **p25 = 7.0**.

Mô phỏng trên khay thật (chỉ nhóm `cham`, KHÔNG đụng ref vì ref được chèn theo
luật `suat_ref` riêng — sắp lại cả khay là phá cấu trúc đó):

| Phạt | Khay đổi thứ tự | Dịch envato | Dịch pexels |
|---|---|---|---|
| 2/3 | 6/31 | -0.19 | +0.52 |
| **3/4** | **8/31** | **-0.25** | **+0.70** |
| 5/6 | 14/31 | -0.42 | +1.12 |
| 8/9 | 16/31 | -0.57 | +1.42 |

Chốt **3.0 / 4.0**: đủ lật thứ tự khi điểm sát nhau (p25=7), không đủ để đẩy
stock văng khỏi khay — đúng yêu cầu "không loại".

TRẦN TỰ NHIÊN: 10/31 khay có stock thì stock là **toàn bộ** nhóm cham (không
có envato nào để so). Ở đó phạt bao nhiêu cũng không đổi được gì — đừng nâng
mức phạt để đuổi theo con số đó.
"""

from __future__ import annotations

import pytest

from autoedit.sotra import db as sdb
from autoedit.sotra.tag7 import tag_tu_tieu_de
from autoedit.sotra.tra import tra


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    yield c
    c.close()


def _them(c, nguon, i, ten):
    sdb.them_clip(c, {"id": sdb.lam_id(nguon, str(i)), "nguon": nguon,
                      "tieu_de": ten, **tag_tu_tieu_de(ten)})


LOP = {"L0": [], "L1": ["market"], "L2": [], "L3": []}


def test_pexels_xep_SAU_envato_khi_diem_bang_nhau(conn):
    """Cùng một tiêu đề = cùng điểm chữ. Envato phải đứng trước."""
    _them(conn, "pexels", 1, "busy market street")
    _them(conn, "envato", 1, "busy market street")
    conn.commit()
    ra = tra(conn, LOP, so=12, can_neo=False)
    nguon = [c["nguon"] for c in ra]
    assert nguon.index("envato") < nguon.index("pexels"), \
        f"pexels vẫn đứng trước envato: {nguon}"


def test_pixabay_xep_SAU_pexels(conn):
    """Thứ tự user chốt: ... pexels -> pixabay (pixabay kém nhất)."""
    _them(conn, "pixabay", 1, "busy market street")
    _them(conn, "pexels", 1, "busy market street")
    conn.commit()
    ra = tra(conn, LOP, so=12, can_neo=False)
    nguon = [c["nguon"] for c in ra]
    assert nguon.index("pexels") < nguon.index("pixabay"), \
        f"pixabay vẫn đứng trước pexels: {nguon}"


def test_stock_KHONG_bi_loai_khoi_khay(conn):
    """User chốt: *không loại, chỉ đẩy xuống*. Khay chỉ có stock thì stock
    vẫn phải ra — không được trả khay rỗng."""
    _them(conn, "pexels", 1, "busy market street")
    _them(conn, "pixabay", 1, "quiet market square")
    conn.commit()
    ra = tra(conn, LOP, so=12, can_neo=False)
    assert {c["nguon"] for c in ra} == {"pexels", "pixabay"}, \
        f"stock bị loại khỏi khay: {[c['nguon'] for c in ra]}"


def test_stock_THANG_RO_van_dung_tren_envato(conn):
    """Phạt là để lật khi ĐIỂM SÁT NHAU, không phải để chôn stock.

    Khoảng cách điểm trong khay thật: trung vị 13.0. Stock trúng L1 (10 điểm)
    còn envato chỉ trúng L3 (3 điểm) là hơn 7 điểm — phạt 3.0 không được lật
    ngược ca này, nếu không tool bỏ qua clip đúng nội dung hơn.
    """
    _them(conn, "pexels", 1, "busy market street")        # trúng L1 'market'
    _them(conn, "envato", 1, "quiet mountain river")      # trúng L3 'river'
    conn.commit()
    ra = tra(conn, {"L0": [], "L1": ["market"], "L2": [], "L3": ["river"]},
             so=12, can_neo=False)
    assert ra[0]["nguon"] == "pexels", \
        f"stock trúng L1 bị chôn dưới envato trúng L3: {[(c['nguon'], c['diem']) for c in ra]}"


def test_envato_va_kho_KHONG_bi_phat(conn):
    """Việc F chỉ phạt pexels/pixabay. Envato và kho phải giữ NGUYÊN điểm.

    Kho vốn hơn envato 2.0 điểm vì `co_neo` (luật `DIEM_NEO` có sẵn, không
    liên quan việc F) — kiểm đúng khoảng cách cũ đó, không kiểm bằng nhau.
    """
    _them(conn, "envato", 1, "busy market street")
    _them(conn, "kho", 1, "busy market street")
    conn.commit()
    d = {c["nguon"]: c["diem"] for c in tra(conn, LOP, so=12, can_neo=False)}
    assert d["kho"] - d["envato"] == 2.0, \
        f"việc F làm lệch thêm khoảng cách envato/kho: {d}"


def test_ref_KHONG_bi_cham(conn):
    """Ref chèn theo luật `suat_ref` riêng (user chốt 07/09) — việc F không
    được đụng vào. Sổ vòng 8: sắp lại cả khay gồm ref là PHÁ cấu trúc đó."""
    _them(conn, "ref", 1, "busy market street")
    _them(conn, "envato", 1, "busy market street")
    conn.commit()
    ra = tra(conn, LOP, so=12, can_neo=False)
    d = {c["nguon"]: c["diem"] for c in ra}
    assert d["ref"] >= d["envato"], f"ref bị đẩy xuống dưới envato: {d}"


def test_muc_phat_dung_nhu_da_do(conn):
    """Mức phạt là con số ĐO ĐƯỢC, không phải ước — khoá lại để lần sau ai
    đổi thì phải đọc lý do trong docstring đầu file."""
    from autoedit.sotra.tra import PHAT_NGUON

    assert PHAT_NGUON == {"pexels": 3.0, "pixabay": 4.0}, \
        f"mức phạt đổi mà không cập nhật số đo: {PHAT_NGUON}"


def test_uu_tien_nguon_van_LAT_NGUOC_duoc_phat(conn):
    """`--uu-tien-nguon pexels` phải kéo được stock lên lại — người dùng bảo
    ưu tiên thì luật chung phải nhường.

    Vì việc F mà `DIEM_UU_TIEN_NGUON` phải nâng **2.5 -> 6.0**: 2.5 không
    thắng nổi phạt tối đa 4.0, gõ ưu tiên vào mà stock vẫn nằm dưới là sai.
    """
    _them(conn, "pexels", 1, "busy market street")
    _them(conn, "envato", 1, "busy market street")
    conn.commit()
    thuong = [c["nguon"] for c in tra(conn, LOP, so=12, can_neo=False)]
    uu = [c["nguon"] for c in tra(conn, LOP, so=12, can_neo=False,
                                  uu_tien_nguon="pexels")]
    assert thuong.index("envato") < thuong.index("pexels"), thuong
    assert uu.index("pexels") < uu.index("envato"), \
        f"--uu-tien-nguon pexels không kéo nổi stock lên: {uu}"


def test_stock_KHONG_bi_giet_boi_gio_6_moi_tang(conn):
    """Ca THẬT bắt được lúc nghiệm thu 10/09 trên kho production (17.323 clip).

    Từ khoá `market vendor`: trước phạt khay là `ppRRRRRRE` (2 pexels đầu
    bảng); sau phạt thành `RRRRREEEEEE` — **mất sạch pexels**. Đó là LOẠI, chứ
    không phải "đẩy xuống" như user chốt.

    Nguyên nhân: vòng cân nhóm chặn **6 mục mỗi tầng**. Cả khay cùng tầng L1;
    pexels tụt 22.0 -> 19.0 nên rơi xuống dưới 6 envato 20.0 điểm và bị cắt
    khỏi giỏ L1. Phạt điểm mà không có suất giữ chỗ = xoá nguồn khỏi khay.

    3/8 từ khoá thử bị mất stock kiểu này (`market`, `ocean`, `desert`).
    """
    for i in range(8):                      # 8 envato cùng tầng, điểm cao hơn
        _them(conn, "envato", i, "busy market vendor street stall")
    _them(conn, "pexels", 1, "busy market street")
    _them(conn, "pixabay", 1, "busy market street")
    conn.commit()
    ra = tra(conn, LOP, so=12, can_neo=False)
    ng = [c["nguon"] for c in ra]
    assert "pexels" in ng, f"pexels bị XOÁ khỏi khay chứ không phải đẩy xuống: {ng}"
    assert "pixabay" in ng, f"pixabay bị XOÁ khỏi khay: {ng}"
    assert ng.index("envato") < ng.index("pexels"), \
        f"giữ chỗ mà lại kéo stock lên đầu: {ng}"


def test_san_suat_ref_van_duoc_giu(conn):
    """Việc F làm envato trồi lên (đúng mục tiêu), nên khay đầy hơn và ref
    nhận ít suất "dôi" hơn: đo trên kho thật 6 -> 4 ref/khay.

    LUẬT ref KHÔNG vỡ — `suat_ref` là SÀN (user chốt 07/09), và sàn 2 vẫn
    được tôn trọng ở cả 8 từ khoá thử. Khoá lại đây để lần sau ai chỉnh mức
    phạt thì thấy ngay nếu làm ref tụt dưới sàn.
    """
    # tiêu đề PHẢI khác nhau: `gop_ban_trung` (09/09) gộp cùng nguồn + cùng
    # tiêu đề về một thẻ, dựng 10 bản trùng tên là khay chỉ ra 1 thẻ.
    for i in range(10):
        _them(conn, "envato", i, f"busy market vendor stall number {i}")
    for i in range(4):
        _them(conn, "ref", i, f"busy market vendor corner {i}")
    _them(conn, "pexels", 1, "busy market street")
    conn.commit()
    ra = tra(conn, LOP, so=12, can_neo=False, suat_ref=2)
    so_ref = sum(1 for c in ra if c["nguon"] == "ref")
    assert so_ref >= 2, f"ref tụt dưới sàn suat_ref=2: {[c['nguon'] for c in ra]}"


def test_suat_giu_cho_SONG_SOT_qua_do_ung_vien(conn):
    """Mối nối dễ đứt: `dung.py:80` cắt lại khay bằng
    `khac[:so_moi_khoi - len(ref_uv)]`. Stock nằm CUỐI `khac` (điểm thấp nhất
    sau phạt) nên bị cắt trước tiên — suất giữ chỗ đặt trong `tra()` có thể
    chết ở đây mà không báo gì.

    Đo trên kho thật 10/09 qua đúng đường này: 3/8 khay không có stock trước
    phạt -> **0/8** sau phạt + giữ chỗ. Khoá lại bằng test vì hai hàm nằm ở hai
    file khác nhau, sửa một bên không ai nhắc bên kia.
    """
    from autoedit.offline.dung import do_ung_vien

    class _Lop:
        truc_chi, ngu_canh, khong_khi, neo = ["market"], [], [], False

    for i in range(12):                     # thừa envato để đẩy stock xuống cuối
        _them(conn, "envato", i, f"busy market vendor stall number {i}")
    _them(conn, "pexels", 1, "busy market street")
    conn.commit()
    uv = do_ung_vien(conn, [{"v0": 0.0, "v1": 2.0}], [_Lop()], [], so_moi_khoi=12)
    ng = [c["nguon"] for c in uv[0]]
    assert "pexels" in ng, \
        f"suất giữ chỗ bị `do_ung_vien` cắt mất: {ng}"
