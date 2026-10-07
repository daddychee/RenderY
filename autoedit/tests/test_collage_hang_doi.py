"""Collage — HÀNG ĐỢI dựng video Vox cho CẢ ĐỘI editor (user chốt 06/10/2026).

Một GPU, nhiều người: người gửi 10 cảnh không được bắt người gửi 1 cảnh chờ hết 10.
Chia lượt theo NGƯỜI (ai lâu chưa được phục vụ thì tới lượt), trong một người thì
việc gửi trước làm trước. Thợ chết giữa chừng -> việc `dang` quay lại `cho` khi bật lại.
"""

from __future__ import annotations

from autoedit.collage.hang_doi import HangDoi


def _hd(tmp_path):
    return HangDoi(tmp_path / "hang_doi.db")


def test_tao_viec_o_trang_thai_cho_va_dung_thu_tu(tmp_path):
    hd = _hd(tmp_path)
    a = hd.tao(nguoi="an", model="VOX-chieu-sau", giay=5.0, cd="push_in", anh="x.png", nhan="SE001/c1")
    v = hd.doc(a)
    assert v["trang_thai"] == "cho" and v["giay"] == 5.0 and v["cd"] == "push_in"
    assert hd.thu_tu(a) == 1


def test_chia_luot_theo_nguoi_khong_de_mot_nguoi_chan_ca_hang(tmp_path):
    hd = _hd(tmp_path)
    a1, a2, a3 = (hd.tao(nguoi="an", model="VOX-chieu-sau", giay=5, cd="", anh="", nhan=f"a{i}") for i in range(3))
    b1 = hd.tao(nguoi="binh", model="VOX-chieu-sau", giay=5, cd="", anh="", nhan="b1")
    assert hd.thu_tu(b1) == 2, "B gửi sau 3 việc của A nhưng chỉ chờ 1 lượt"
    thu_tu_lam = [hd.lay_tiep()["id"] for _ in range(4)]
    assert thu_tu_lam == [a1, b1, a2, a3]
    assert hd.lay_tiep() is None


def test_xong_va_hong_ghi_lai_ket_qua(tmp_path):
    hd = _hd(tmp_path)
    a = hd.tao(nguoi="an", model="VOX-chieu-sau", giay=5, cd="", anh="", nhan="a")
    b = hd.tao(nguoi="an", model="VOX-chieu-sau", giay=5, cd="", anh="", nhan="b")
    assert hd.lay_tiep()["id"] == a
    assert hd.doc(a)["trang_thai"] == "dang"
    hd.xong(a, "F:/ra/a.mp4")
    hd.lay_tiep()
    hd.hong(b, "ffmpeg chết")
    assert hd.doc(a)["trang_thai"] == "xong" and hd.doc(a)["ra"] == "F:/ra/a.mp4"
    assert hd.doc(b)["trang_thai"] == "hong" and "ffmpeg" in hd.doc(b)["loi"]


def test_tho_chet_giua_chung_viec_dang_quay_lai_hang(tmp_path):
    hd = _hd(tmp_path)
    a = hd.tao(nguoi="an", model="VOX-chieu-sau", giay=5, cd="", anh="", nhan="a")
    hd.lay_tiep()
    assert HangDoi(tmp_path / "hang_doi.db").khoi_phuc() == 1     # thợ bật lại
    assert hd.doc(a)["trang_thai"] == "cho"
    assert hd.lay_tiep()["id"] == a
