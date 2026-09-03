"""aigen/motif.py — gom beat thiếu hình thành motif + sinh ảnh phương án.

Không mạng: LLM + Ark đều giả. Thứ cần khoá là LUẬT MÁY KIỂM (_hop_le) —
GLM trả gì cũng không được lách giãn cách 60s / trần motif / beat lạ.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from autoedit.aigen.duyet import PhienDuyet
from autoedit.aigen.motif import (GIAN_CACH_S, SO_MOTIF_TOI_DA, KetQuaGom,
                                  MotifDeXuat, _hop_le, gom_motif)


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


def test_gom_motif_tao_phien_du_anh(tmp_path):
    p = _project(tmp_path)
    llm = _LLMGia(_kq(("cinematic scene", [1, 2])))
    phien = gom_motif(p, llm=llm, ark=_ArkGia())
    assert phien is not None and llm.goi == 1
    assert [m.ma for m in phien.motif] == ["m1"]
    assert phien.motif[0].beat_ids == [1, 2]
    assert len(phien.motif[0].phuong_an) == 2          # 2 phương án/motif
    doc = PhienDuyet.doc(tmp_path)                     # đã ghi JSON + trạng thái
    assert doc.trang_thai == "cho_duyet"
    assert all((tmp_path / "aigen" / pa.file).is_file()
               for pa in doc.motif[0].phuong_an)


def test_gom_motif_khong_de_phien_dang_duyet(tmp_path):
    p = _project(tmp_path)
    PhienDuyet(project_id="p-test").ghi(tmp_path)
    llm = _LLMGia(_kq(("x", [1])))
    assert gom_motif(p, llm=llm, ark=_ArkGia()) is None
    assert llm.goi == 0                                # không đốt lượt LLM nào


def test_gom_motif_khong_thieu_hinh_thi_thoi(tmp_path):
    p = _project(tmp_path, thieu=())
    assert gom_motif(p, llm=_LLMGia(_kq()), ark=_ArkGia()) is None


def test_gom_motif_mot_anh_hong_van_giu_motif(tmp_path):
    p = _project(tmp_path)
    phien = gom_motif(p, llm=_LLMGia(_kq(("scene", [1, 2]))),
                      ark=_ArkGia(hong={"m1_pa2.png"}))
    assert len(phien.motif[0].phuong_an) == 1          # còn 1 phương án vẫn duyệt được


def test_gom_motif_moi_anh_hong_tra_none(tmp_path):
    p = _project(tmp_path)
    ark = _ArkGia(hong={"m1_pa1.png", "m1_pa2.png"})
    assert gom_motif(p, llm=_LLMGia(_kq(("scene", [1, 2]))), ark=ark) is None
    assert not PhienDuyet.duong(tmp_path).is_file()    # không ghi phiên rỗng
