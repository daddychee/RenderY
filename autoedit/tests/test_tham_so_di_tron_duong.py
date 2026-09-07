# -*- coding: utf-8 -*-
"""BẬC 0 (07/09) — tham số dựng phải ĐI TỚI NƠI, thiếu thì phải KÊU.

Bài học BH2 của METHODOLOGY: "bắt buộc nhập" ở form là kiểm tra vô dụng — phải
kiểm ở ĐẦU RA. Bug thật ngày 07/09 (SEQUENCE PH1): job nộp cả tập ghi
`project_id` là chuỗi nối 17 mã chương, nên `WHERE project_id=?` bằng một mã
chương không bao giờ khớp; cả 17 chương LI103 dựng với Framing rỗng + AVD vô
hiệu mà không một dòng cảnh báo.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _du_an(tmp_path: Path, **inputs) -> Path:
    """Thư mục project tối thiểu, chỉ cần project.json cho tham số."""
    d = tmp_path / "c2-20260907-050547"
    d.mkdir(parents=True, exist_ok=True)
    goc = {"script_path": "inputs/script.txt", "voice_path": "inputs/voice.mp3",
           "original_script_path": "", "original_voice_path": "", "script_text": ""}
    (d / "project.json").write_text(
        json.dumps({"project_id": d.name, "inputs": {**goc, **inputs}}),
        encoding="utf-8")
    return d


def _jobs_db(tmp_path: Path, project_id: str, opts: dict):
    """Bảng jobs giả, trỏ queue.db_path về tmp — trả lại conn đã đóng."""
    from autoedit.web import queue as q

    conn = q.connect(tmp_path / "jobs.db")
    conn.execute("INSERT INTO jobs (job_folder, project_id, status, created_at, opts) "
                 "VALUES (?,?,?,?,?)",
                 ("F:/tap", project_id, "done", "2026-09-07T05:00:00", json.dumps(opts)))
    conn.commit()
    conn.close()


# --------------------------------------------------- hồ sơ chương là sự thật
def test_tham_so_doc_tu_ho_so_chuong_khong_can_bang_jobs(tmp_path):
    from autoedit.web.server import tham_so_dung

    d = _du_an(tmp_path, kenh_ref="godoc-travel-doc", avd_phut=7.0,
               dia_danh="Afghanistan", uu_tien_nguon="ref")
    t = tham_so_dung(d, d.name)
    assert t["kenh_ref"] == "godoc-travel-doc"
    assert t["avd_s"] == pytest.approx(420.0)      # 7 phút
    assert t["dia_danh"] == "Afghanistan"
    assert t["uu_tien_nguon"] == "ref"


def test_job_nop_CA_TAP_khong_lam_rot_tham_so(tmp_path, monkeypatch):
    """Chính bug 07/09: project_id của job là chuỗi nối nhiều mã chương.

    Tra bảng jobs kiểu cũ chắc chắn trượt; hồ sơ chương phải cứu được.
    """
    from autoedit.web import queue as q
    from autoedit.web.server import tham_so_dung

    d = _du_an(tmp_path, kenh_ref="godoc-travel-doc", avd_phut=7.0)
    noi_chuoi = ",".join([f"c{i}-20260907-0000{i:02d}" for i in range(1, 18)])
    monkeypatch.setattr(q, "db_path", lambda root=None: tmp_path / "jobs.db")
    _jobs_db(tmp_path, noi_chuoi, {"kenh_ref": "godoc-travel-doc", "avd_phut": 7.0})

    # tra kiểu cũ (bằng 1 mã chương) TRƯỢT — giữ lại bằng chứng của bug
    conn = q.connect(tmp_path / "jobs.db")
    assert conn.execute("SELECT 1 FROM jobs WHERE project_id=?",
                        (d.name,)).fetchone() is None
    conn.close()
    # đường mới vẫn ra đủ tham số
    t = tham_so_dung(d, d.name)
    assert t["kenh_ref"] == "godoc-travel-doc" and t["avd_s"] == pytest.approx(420.0)


def test_project_cu_van_tra_duoc_qua_bang_jobs(tmp_path, monkeypatch):
    """Lưới đỡ: project dựng TRƯỚC bản này không có tham số trong hồ sơ."""
    from autoedit.web import queue as q
    from autoedit.web.server import tham_so_dung

    d = _du_an(tmp_path)                              # hồ sơ KHÔNG có tham số
    monkeypatch.setattr(q, "db_path", lambda root=None: tmp_path / "jobs.db")
    _jobs_db(tmp_path, d.name, {"kenh_ref": "fern", "avd_phut": 6.0,
                                "dia_danh": "Peru"})
    t = tham_so_dung(d, d.name)
    assert t["kenh_ref"] == "fern" and t["avd_s"] == pytest.approx(360.0)
    assert t["dia_danh"] == "Peru"


def test_khong_khai_gi_thi_KHONG_bia_so_mac_dinh(tmp_path, monkeypatch):
    """BH5: bản cũ tự điền AVD 6 phút khi tra trượt — nay phải trả 0."""
    from autoedit.web import queue as q
    from autoedit.web.server import tham_so_dung

    d = _du_an(tmp_path)
    monkeypatch.setattr(q, "db_path", lambda root=None: tmp_path / "jobs.db")
    t = tham_so_dung(d, d.name)
    assert t == {"avd_s": 0.0, "kenh_ref": "", "uu_tien_nguon": "", "dia_danh": "",
                 "kieu_chay": ""}


# ------------------------------------------------- thiếu thì hợp đồng phải KÊU
def test_thieu_framing_va_avd_thi_hop_dong_canh_bao(du_an, tmp_path, monkeypatch):
    from autoedit.offline import runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    hd = runner.phan_tich(du_an, avd_s=0, kenh_ref="", llm=_LLM())
    cb = " | ".join(hd["canh_bao"])
    assert "Framing Insight KHÔNG tới nơi" in cb
    assert "Mốc AVD chưa khai" in cb


def test_co_kenh_ref_nhung_chua_do_thi_bao_di_do(du_an, tmp_path, monkeypatch):
    from autoedit.offline import runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    hd = runner.phan_tich(du_an, avd_s=420, mo_dau_tap_s=0,
                          kenh_ref="kenh-chua-do", llm=_LLM())
    cb = " | ".join(hd["canh_bao"])
    assert "chưa đo được" in cb and "Mốc AVD" not in cb


def test_du_tham_so_thi_khong_canh_bao_oan(du_an, tmp_path, monkeypatch):
    from autoedit.kenh.hoso import HoSoKenh
    from autoedit.offline import runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setattr("autoedit.kenh.hoso.resolve_data_root",
                        lambda *a, **k: tmp_path)
    HoSoKenh(ten="godoc-travel-doc", than_trung_vi=4.73,
             than_ty_le_hold=0.38, hook_trung_vi=4.98, so_video_hoi_tu=5).ghi()
    hd = runner.phan_tich(du_an, avd_s=420, mo_dau_tap_s=0,
                          kenh_ref="godoc-travel-doc", llm=_LLM())
    assert hd["framing"].get("ten") == "godoc-travel-doc"
    assert not [c for c in hd["canh_bao"] if "Framing" in c or "AVD" in c]


# ------------------------------------------------------------- cây thước
def _hd_gia() -> dict:
    return {
        "ma_tap": "LI103", "trang_thai": "pha1", "dong_kiem": True, "avd_s": 420,
        "dia_danh": "Afghanistan", "uu_tien_nguon": "ref",
        "framing": {"ten": "godoc-travel-doc", "than": 4.0},
        "tong_voice": 20.0, "canh_bao": ["thử"],
        "khoi": [
            {"v0": 0, "v1": 2, "uv": [{"nguon": "ref"}], "chon": 0},
            {"v0": 2, "v1": 12, "uv": [{"nguon": "envato"}], "chon": 0},  # 10s > 6.4s
            {"v0": 12, "v1": 16, "uv": [], "chon": -1, "truu_tuong": True},
        ],
        "hinh": [{"t0": 0, "dur": 2}, {"t0": 2, "dur": 10}, {"t0": 12, "dur": 4}],
    }


def test_thuoc_do_dung_so():
    from autoedit.offline import thuoc

    s = thuoc.do(_hd_gia())
    assert s["so_khoi"] == 3 and s["so_hinh"] == 3
    assert s["khoi_median"] == 4.0 and s["khoi_max"] == 10.0
    assert s["khoi_qua_dai"] == 1                 # chỉ khối 10s vượt 4.0*1.6
    assert s["co_uv"] == 2 and s["ty_le_co_uv"] == pytest.approx(0.667, abs=0.01)
    assert s["nguon"] == {"ref": 1, "envato": 1}
    assert s["truu_tuong"] == 1


def test_thuoc_bao_cao_chi_ro_cho_THIEU():
    from autoedit.offline import thuoc

    hd = _hd_gia()
    hd["framing"] = {}                            # đúng cảnh 07/09
    hd["avd_s"] = 0
    dong = " ".join(thuoc.dong_bao_cao(thuoc.do(hd)))
    assert "Framing   : ✗ KHÔNG CÓ" in dong and "✗ chưa khai" in dong
    # khay phủ 2/3 = 67% -> KHÔNG được cảnh báo dưới 50%
    assert "dưới 50%" not in dong


def test_thuoc_keu_khi_khay_phu_duoi_mot_nua():
    from autoedit.offline import thuoc

    hd = _hd_gia()
    for k in hd["khoi"]:
        k["uv"] = []
    assert "dưới 50%" in " ".join(thuoc.dong_bao_cao(thuoc.do(hd)))


# ---- đồ nghề dùng chung với test_offline.py (giữ nguyên khuôn có sẵn) -------
from tests.test_offline import _LLM, du_an  # noqa: E402,F401


# ============================ BẬC 1 — ba kiểu chạy tường minh ================
# SEQUENCE QĐ1: `avd_s=0` đang mang hai nghĩa chồng nhau ("chưa khai" và "Auto")
# nên Auto KHÔNG khai báo được bằng số (PH4). Nay khai thẳng bằng `kieu_chay`.

def test_ba_kieu_chay_tren_chuong_GIUA_tap():
    """Chương bắt đầu ở phút 10 của tập, mốc AVD 7 phút — cổng của bậc 1."""
    from autoedit.offline.runner import tinh_dong_kiem

    avd, moc = 420.0, 600.0                       # 7 phút · chương mở ở phút 10
    assert tinh_dong_kiem("manual", avd, moc) is True    # người duyệt hết
    assert tinh_dong_kiem("auto", avd, moc) is False     # tự chạy hết
    assert tinh_dong_kiem("avd", avd, moc) is False      # sau mốc -> tự chạy
    assert tinh_dong_kiem("avd", avd, 60.0) is True      # trước mốc -> duyệt


def test_manual_va_auto_KHONG_phu_thuoc_con_so_avd():
    """Đúng chỗ bản cũ bó tay: cùng avd_s=0 mà phải ra hai kết quả khác nhau."""
    from autoedit.offline.runner import tinh_dong_kiem

    assert tinh_dong_kiem("manual", 0.0, 0.0) is True
    assert tinh_dong_kiem("auto", 0.0, 0.0) is False     # bản cũ luôn ra True
    assert tinh_dong_kiem("auto", 999999.0, 0.0) is False


def test_khong_khai_kieu_chay_thi_giu_nguyen_hanh_vi_cu():
    from autoedit.offline.runner import tinh_dong_kiem

    for avd, moc in ((0.0, 0.0), (360.0, 0.0), (360.0, 400.0), (0.0, 999.0)):
        assert tinh_dong_kiem("", avd, moc) == ((avd <= 0) or (moc < avd))


def test_kieu_chay_la_thi_DUNG_chu_khong_doan(du_an, tmp_path, monkeypatch):
    from autoedit.offline import runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    with pytest.raises(RuntimeError, match="kieu_chay lạ"):
        runner.phan_tich(du_an, kieu_chay="tu_dong", llm=_LLM())


def test_manual_khong_bi_canh_bao_thieu_AVD(du_an, tmp_path, monkeypatch):
    """Manual cố ý không có mốc AVD — cảnh báo ở đây là báo oan."""
    from autoedit.offline import runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    hd = runner.phan_tich(du_an, avd_s=0, kieu_chay="manual", llm=_LLM())
    assert hd["dong_kiem"] is True and hd["kieu_chay"] == "manual"
    assert not [c for c in hd["canh_bao"] if "AVD" in c]

    hd2 = runner.phan_tich(du_an, avd_s=0, kieu_chay="avd", llm=_LLM())
    assert [c for c in hd2["canh_bao"] if "AVD" in c]     # avd mà thiếu mốc -> kêu


def test_auto_ghi_vao_hop_dong_va_cay_thuoc_hien(du_an, tmp_path, monkeypatch):
    from autoedit.offline import runner, thuoc
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    hd = runner.phan_tich(du_an, avd_s=0, kieu_chay="auto", llm=_LLM())
    assert hd["dong_kiem"] is False and hd["kieu_chay"] == "auto"
    assert "Kiểu chạy : auto" in " ".join(thuoc.dong_bao_cao(thuoc.do(hd)))


def test_kieu_chay_di_het_duong_tu_ho_so_chuong(tmp_path):
    from autoedit.web.server import tham_so_dung

    d = _du_an(tmp_path, kieu_chay="auto", kenh_ref="godoc-travel-doc")
    assert tham_so_dung(d, d.name)["kieu_chay"] == "auto"


def test_nop_lai_tap_thi_tham_so_DUOC_CAP_NHAT():
    """Chạy thật 07/09 lộ ra: nhánh "dùng lại project cũ" return sớm nên tham
    số mới không tới đâu — user sửa Framing/AVD rồi nộp lại mà chương giữ số cũ.
    """
    from autoedit.cli import _gan_tham_so_dung
    from autoedit.project import Inputs

    class _Prj:
        def __init__(self):
            self.inputs = Inputs(script_path="", voice_path="",
                                 original_script_path="", original_voice_path="",
                                 script_text="", kenh_ref="fern", avd_phut=6.0,
                                 kieu_chay="manual")
            self.da_luu = False

        def save(self):
            self.da_luu = True

    p = _Prj()
    _gan_tham_so_dung(p, "godoc-travel-doc", 9.0, " Afghanistan ", "ref", "AUTO")
    assert p.inputs.kenh_ref == "godoc-travel-doc"
    assert p.inputs.avd_phut == 9.0
    assert p.inputs.dia_danh == "Afghanistan"        # đã cắt khoảng trắng
    assert p.inputs.kieu_chay == "auto"              # đã hạ về chữ thường
    assert p.da_luu is True                          # phải GHI xuống đĩa


def test_avd_phut_am_la_CHUA_KHAI_khong_de_len_so_cu():
    """`--avd-phut` mặc định -1 = chưa khai; không được xoá số đã có."""
    from autoedit.cli import _gan_tham_so_dung
    from autoedit.project import Inputs

    class _Prj:
        def __init__(self):
            self.inputs = Inputs(script_path="", voice_path="",
                                 original_script_path="", original_voice_path="",
                                 script_text="", avd_phut=7.0)

        def save(self):
            pass

    p = _Prj()
    _gan_tham_so_dung(p, "", -1.0, "", "", "")
    assert p.inputs.avd_phut == 7.0
