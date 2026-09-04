"""aigen/motif.py — gom beat thiếu hình thành motif + sinh ảnh phương án.

Không mạng: LLM + Ark đều giả. Thứ cần khoá là LUẬT MÁY KIỂM (_hop_le) —
GLM trả gì cũng không được lách giãn cách 60s / trần motif / beat lạ.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from autoedit.aigen.duyet import PhienDuyet
from autoedit.aigen.motif import (GIAN_CACH_S, SO_MOTIF_TOI_DA, KetQuaGom,
                                  MotifDeXuat, _hop_le, de_xuat_motif,
                                  gen_anh_phuong_an)


def _kq(*motif):
    return KetQuaGom(motif=[MotifDeXuat(mo_ta=f"c{i}", prompt=p, beat_ids=ids)
                            for i, (p, ids) in enumerate(motif)])


# ------------------------------------------------------------------ _hop_le
def test_hop_le_giu_gian_cach_60s():
    t = {1: 0.0, 2: 30.0, 3: 90.0}
    ra = _hop_le(_kq(("scene", [1, 2, 3])), t)
    assert ra[0].beat_ids == [1, 3]          # beat 2 cách beat 1 có 30s -> bỏ


def test_hop_le_beat_la_va_trung_motif():
    t = {1: 0.0, 2: 100.0}
    ra = _hop_le(_kq(("a", [1, 99]), ("b", [1, 2])), t)
    assert ra[0].beat_ids == [1]             # 99 không tồn tại
    assert ra[1].beat_ids == [2]             # 1 đã thuộc motif trước


def test_hop_le_cat_tran_va_bo_rong():
    t = {i: i * 100.0 for i in range(1, 10)}
    nhieu = [(f"p{i}", [i]) for i in range(1, 9)]
    ra = _hop_le(_kq(("", [1]), *nhieu), t)   # prompt rỗng -> bỏ
    assert len(ra) == SO_MOTIF_TOI_DA


def test_hop_le_sap_theo_thoi_gian():
    t = {5: 200.0, 7: 0.0}
    ra = _hop_le(_kq(("x", [5, 7])), t)
    assert ra[0].beat_ids == [7, 5]          # giữ cả hai (cách 200s), theo t tăng


# ------------------------------------------------------------------ gom_motif
class _LLMGia:
    def __init__(self, kq):
        self.kq = kq
        self.goi = 0

    def complete(self, system, user, output_model, context=None):
        self.goi += 1
        assert str(GIAN_CACH_S.__int__()) in system   # luật 60s phải nằm trong prompt
        return self.kq, None


class _ArkGia:
    def __init__(self, hong=()):
        self.hong = set(hong)
        self.goi = []

    def gen_anh(self, prompt, dich, size="2560x1440"):
        self.goi.append(Path(dich).name)
        if Path(dich).name in self.hong:
            raise RuntimeError("gia lap Seedream chet")
        Path(dich).write_bytes(b"png")
        return Path(dich)


def _project(tmp_path, thieu=(1, 2), t=(0.0, 100.0)):
    beats = [SimpleNamespace(beat_id=b, chapter=1, mood="tense", shot_size="wide",
                             visual_concept=f"canh {b}", text="loi thoai dai",
                             timeline_start=tt, start=tt)
             for b, tt in zip(thieu, t)]
    shots = [SimpleNamespace(beat_id=b, status="needs_human") for b in thieu]
    shots.append(SimpleNamespace(beat_id=999, status="ok"))
    return SimpleNamespace(project_dir=str(tmp_path), project_id="p-test",
                           beats=beats, shots=shots)


def test_de_xuat_tao_phien_cong1_khong_ton_anh(tmp_path):
    p = _project(tmp_path)
    llm = _LLMGia(_kq(("cinematic scene", [1, 2])))
    phien = de_xuat_motif(p, llm=llm)
    assert phien is not None and llm.goi == 1
    assert [m.ma for m in phien.motif] == ["m1"]
    assert phien.motif[0].beat_ids == [1, 2]
    assert phien.motif[0].phuong_an == []              # CỔNG 1: chưa ảnh, 0 đồng
    assert PhienDuyet.doc(tmp_path).trang_thai == "cho_gen_anh"


def test_de_xuat_khong_de_phien_dang_duyet(tmp_path):
    p = _project(tmp_path)
    PhienDuyet(project_id="p-test").ghi(tmp_path)
    llm = _LLMGia(_kq(("x", [1])))
    assert de_xuat_motif(p, llm=llm) is None
    assert llm.goi == 0                                # không đốt lượt LLM nào


def test_de_xuat_khong_thieu_hinh_thi_thoi(tmp_path):
    p = _project(tmp_path, thieu=())
    assert de_xuat_motif(p, llm=_LLMGia(_kq())) is None


def _phien_cong1(tmp_path, p):
    de_xuat_motif(p, llm=_LLMGia(_kq(("scene A", [1, 2]), ("scene B", [3]))))


def test_gen_anh_chi_motif_duoc_tick(tmp_path):
    p = _project(tmp_path, thieu=(1, 2, 3), t=(0.0, 100.0, 300.0))
    _phien_cong1(tmp_path, p)
    ark = _ArkGia()
    gen_anh_phuong_an(tmp_path, giu=["m1"], ark=ark)   # m2 KHÔNG tick
    doc = PhienDuyet.doc(tmp_path)
    assert doc.trang_thai == "cho_duyet"
    assert [m.ma for m in doc.motif] == ["m1"]         # m2 bị bỏ — beat tự lo
    assert len(doc.motif[0].phuong_an) == 2
    assert all(f.startswith("m1_") for f in ark.goi)   # không đốt tiền cho m2
    assert all((tmp_path / "aigen" / pa.file).is_file()
               for pa in doc.motif[0].phuong_an)


def test_gen_anh_mot_anh_hong_van_giu_motif(tmp_path):
    p = _project(tmp_path)
    _phien_cong1(tmp_path, p)
    gen_anh_phuong_an(tmp_path, giu=["m1"], ark=_ArkGia(hong={"m1_pa2.png"}))
    doc = PhienDuyet.doc(tmp_path)
    assert doc.trang_thai == "cho_duyet"
    assert len(doc.motif[0].phuong_an) == 1            # còn 1 phương án vẫn duyệt được


def test_gen_anh_moi_anh_hong_quay_ve_cong1(tmp_path):
    p = _project(tmp_path)
    _phien_cong1(tmp_path, p)
    gen_anh_phuong_an(tmp_path, giu=["m1"],
                      ark=_ArkGia(hong={"m1_pa1.png", "m1_pa2.png"}))
    assert PhienDuyet.doc(tmp_path).trang_thai == "cho_gen_anh"   # tick lại được


def test_ghi_chu_khong_xoa_lua_chon(tmp_path):
    """Bug 04/09: UI gửi chon=None khi sửa ghi chú — không được xoá 'đã chọn'."""
    from autoedit.aigen.duyet import Motif, PhuongAn
    phien = PhienDuyet(project_id="p", motif=[Motif(
        ma="m1", mo_ta="x", prompt="p",
        phuong_an=[PhuongAn(file="a.png", chon=True), PhuongAn(file="b.png")])])
    phien.chon("m1", "a.png", None, "bớt sương")
    assert phien.motif[0].phuong_an[0].chon is True        # lựa chọn còn nguyên
    assert phien.motif[0].phuong_an[0].ghi_chu == "bớt sương"
    assert phien.du_de_chot()[0]


def test_gen_anh_giu_motif_anh_ref(tmp_path):
    """Motif editor tự đưa ảnh ref ($0) phải SỐNG SÓT qua lượt gen của motif khác."""
    from autoedit.aigen.duyet import PhuongAn
    p = _project(tmp_path, thieu=(1, 2, 3), t=(0.0, 100.0, 300.0))
    _phien_cong1(tmp_path, p)                              # m1 (gen), m2
    doc = PhienDuyet.doc(tmp_path)
    (tmp_path / "aigen").mkdir()
    (tmp_path / "aigen" / "m2_ref.png").write_bytes(b"anh cua editor")
    doc.motif[1].phuong_an = [PhuongAn(file="m2_ref.png", chon=True)]
    doc.ghi(tmp_path)
    ark = _ArkGia()
    gen_anh_phuong_an(tmp_path, giu=["m1"], ark=ark)
    doc = PhienDuyet.doc(tmp_path)
    assert doc.trang_thai == "cho_duyet"
    assert [m.ma for m in doc.motif] == ["m1", "m2"]        # ref không bị vứt
    assert doc.motif[1].anh_chot.file == "m2_ref.png"       # vẫn chọn sẵn
    assert all(f.startswith("m1_") for f in ark.goi)        # m2 không đốt tiền


def test_gen_anh_sai_trang_thai_bo_qua(tmp_path):
    p = _project(tmp_path)
    _phien_cong1(tmp_path, p)
    doc = PhienDuyet.doc(tmp_path)
    doc.trang_thai = "da_chot"
    doc.ghi(tmp_path)
    ark = _ArkGia()
    msg = gen_anh_phuong_an(tmp_path, giu=["m1"], ark=ark)
    assert "bỏ qua" in msg and ark.goi == []           # không đốt tiền sai cửa
