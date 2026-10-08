"""VOX nhập PSD team đã chia layer (user chốt 08/10/2026: "cách tách cơ học lỗi chồng lỗi" -> có PSD thì
dùng THẲNG layer người cắt, không máy cắt). Đo thật trên PSD của team: Pillow đọc được tên layer nhưng
KHÔNG lấy được điểm ảnh từng layer; psd-tools ghép lại khớp Photoshop 54,8 dB.
Test tự sinh PSD bằng psd-tools (tên không dấu: psd-tools ghi tên layer bằng macroman).
"""

from __future__ import annotations

import io

import numpy as np
import pytest

pytest.importorskip("psd_tools")

from autoedit.collage import psd as mpsd  # noqa: E402

XANH, DO, VANG = (40, 80, 160), (250, 20, 20), (240, 220, 30)


def _psd(duong=None, lo_nen=False):
    """Canvas 200x100 (2:1), từ DƯỚI lên: Nen (kín, hoặc thủng giữa) · Nguoi (alpha dải mềm) · An (ẩn) ·
    nhóm 'Nhom chu' (1 mảnh vàng). Trả bytes PSD."""
    from PIL import Image
    from psd_tools import PSDImage
    from psd_tools.api.layers import Group, PixelLayer

    p = PSDImage.new("RGB", (200, 100), color=(0, 0, 0))
    nen = Image.new("RGBA", (200, 100), XANH + (255,))
    if lo_nen:
        nen.paste((0, 0, 0, 0), (80, 30, 120, 70))                # nền KHÔNG vẽ sau người
    p.append(PixelLayer.frompil(nen, p, "Nen", 0, 0))
    nguoi = Image.new("RGBA", (60, 40), DO + (255,))
    nguoi.putalpha(Image.linear_gradient("L").rotate(90).resize((60, 40)))
    p.append(PixelLayer.frompil(nguoi, p, "Nguoi", 30, 70))       # top=30 left=70 -> hộp (70,30,130,70)
    an = PixelLayer.frompil(Image.new("RGBA", (20, 20), (0, 255, 0, 255)), p, "An", 5, 5)
    an.visible = False
    p.append(an)
    g = Group.new(p, "Nhom chu")
    g.append(PixelLayer.frompil(Image.new("RGBA", (30, 10), VANG + (255,)), p, "chu", 75, 150))
    p.append(g)
    b = io.BytesIO()
    p.save(b)
    if duong:
        duong.write_bytes(b.getvalue())
    return b.getvalue()


def test_nhan_ra_psd_qua_chu_ky_dau_file():
    assert mpsd.la_psd(_psd()) and not mpsd.la_psd(b"\x89PNG\r\n\x1a\n....")


def test_doc_liet_ke_layer_cap_ngoai_cung_tu_duoi_len():
    d = mpsd.doc(_psd())
    assert (d["rong"], d["cao"]) == (200, 100)
    assert [x["ten"] for x in d["lop"]] == ["Nen", "Nguoi", "An", "Nhom chu"], "nhóm tính là MỘT khối"
    nguoi, an, nhom = d["lop"][1], d["lop"][2], d["lop"][3]
    assert nguoi["hop"] == [70, 30, 130, 70] and nguoi["hien"] and nguoi["loai"] == "pixel"
    assert not an["hien"] and nhom["loai"] == "group"
    assert not any(x["chu"] for x in d["lop"]), "không có layer chữ (type) nào"
    assert [x["chi_so"] for x in d["lop"]] == [0, 1, 2, 3]


def test_de_xuat_moi_layer_hien_tru_nen_duoi_cung():
    d = mpsd.doc(_psd())
    assert mpsd.de_xuat(d["lop"]) == [1, 3], "bỏ nền (dưới cùng) và layer đang ẩn"


def test_tach_nen_la_layer_KHONG_chon_lop_giu_dung_diem_anh_va_alpha_mem():
    nen, lop = mpsd.tach(_psd(), [1, 3], 200, 100)
    assert nen.shape == (100, 200, 4) and np.allclose(nen[50, 100, :3], np.float32(XANH) / 255, atol=0.01)
    assert nen[..., 3].min() > 0.99, "nền kín"
    assert [c for c, _, _ in lop] == [1, 3], "giữ thứ tự xếp chồng từ dưới lên"
    _, mau_, a = lop[0]
    assert np.allclose(mau_[50, 100], np.float32(DO) / 255, atol=0.02)
    assert abs(a[50, 100] - 0.51) < 0.05 and abs(a[50, 80] - 0.17) < 0.05, "alpha mềm của PSD giữ nguyên"
    assert a[50, 20] == 0
    assert np.allclose(nen[80, 160, :3], np.float32(XANH) / 255, atol=0.01), "khối CHỌN không lẫn vào nền"
    _, mau_c, ac = lop[1]
    assert ac[80, 160] > 0.99 and np.allclose(mau_c[80, 160], np.float32(VANG) / 255, atol=0.02)


def test_tach_cat_giua_dung_ti_le_khung_hinh():
    """Canvas 2:1 vào khung 16:9 -> cắt giữa còn 178 px rộng, lề trái 11 px: layer dịch theo."""
    nen, lop = mpsd.tach(_psd(), [1], 1920, 1080)
    assert nen.shape[:2] == (100, 178)
    a = lop[0][2]
    xs = np.nonzero(a.max(0) > 0)[0]
    assert (xs.min(), xs.max() + 1) == (70 - 11, 130 - 11)


def test_tach_bao_cho_nen_thung():
    nen, _ = mpsd.tach(_psd(lo_nen=True), [1, 3], 200, 100)
    assert nen[50, 100, 3] < 0.01 and nen[10, 10, 3] > 0.99, "chỗ nền trống trả alpha 0 để bộ dựng vá"


def test_doc_tu_duong_dan(tmp_path):
    p = tmp_path / "a.psd"
    _psd(p)
    assert mpsd.doc(p)["lop"][1]["ten"] == "Nguoi"


def test_de_xuat_nen_la_layer_phu_kin_khung_cao_nhat():
    """Đo thật PSD PayPal của team (08/10): Background trắng + 'Layer 1' = CẢ ảnh phẳng phủ kín khung + 4 khối
    cắt. Nền thật là layer phủ kín CAO NHẤT (mọi thứ dưới nó bị che) — tick cả Layer 1 thì nền thành trắng."""
    from PIL import Image
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer

    p = PSDImage.new("RGB", (200, 100), color=(0, 0, 0))
    p.append(PixelLayer.frompil(Image.new("RGBA", (200, 100), (255, 255, 255, 255)), p, "Background", 0, 0))
    p.append(PixelLayer.frompil(Image.new("RGBA", (200, 100), XANH + (255,)), p, "Layer 1", 0, 0))
    vat = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    vat.paste(DO + (255,), (60, 20, 120, 80))
    p.append(PixelLayer.frompil(vat, p, "Layer 2", 0, 0))     # khối cắt nhưng layer cỡ cả canvas (trong suốt quanh)
    b = io.BytesIO()
    p.save(b)
    d = mpsd.doc(b.getvalue())
    assert [x["kin"] for x in d["lop"]] == [True, True, False]
    assert mpsd.de_xuat(d["lop"]) == [2]


def _psd_ban_sao(ban_sao: bool) -> bytes:
    """Kiểu PSD PayPal của team: 'Layer 1' = cả ảnh phẳng làm nền; 'Layer 2' = khối đỏ cắt sẵn ở trên.
    ban_sao=True: nền VẪN còn khối đỏ (team chưa xoá); False: nền đã xoá sạch (Content-Aware Fill)."""
    from PIL import Image
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer

    p = PSDImage.new("RGB", (200, 100), color=(0, 0, 0))
    nen = Image.new("RGBA", (200, 100), XANH + (255,))
    if ban_sao:
        nen.paste(DO + (255,), (60, 20, 120, 80))
    p.append(PixelLayer.frompil(nen, p, "Layer 1", 0, 0))
    p.append(PixelLayer.frompil(Image.new("RGBA", (60, 60), DO + (255,)), p, "Layer 2", 20, 60))
    b = io.BytesIO()
    p.save(b)
    return b.getvalue()


def test_bao_khoi_con_ban_sao_trong_nen():
    """User chốt 08/10: TEAM tự xoá khối khỏi layer nền trong Photoshop; tool chỉ CẢNH BÁO. Nền còn bản sao
    -> khối bay đi là lộ 2 bản (đo thật PSD PayPal: 2 ông Elon, 2 nhóm người)."""
    assert mpsd.khoi_con_trong_nen(_psd_ban_sao(True), [1]) == [1]
    assert mpsd.khoi_con_trong_nen(_psd_ban_sao(False), [1]) == []
