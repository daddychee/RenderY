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


# ===================== BẬC 2 — đo "nếu chạy AUTO thì còn phủ bao nhiêu" =====
# QĐ5: Auto không dùng Envato. Máy chỉ tự khoá sổ khi khay phủ >= 50% khối, nên
# nếu tỉ trọng thật thấp thì ca đêm chạy xong KHÔNG giao gì — phải đo trước.

def test_do_nhu_auto_bo_envato_thi_phu_giam(tmp_path, monkeypatch):
    from autoedit.offline import thuoc
    from autoedit.sotra import db as sdb
    from autoedit.sotra.tag7 import tag_tu_tieu_de

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    conn = sdb.mo()
    try:
        for i, (nguon, ten) in enumerate([
                ("envato", "Woman Buying Vegetables at Quito Market"),
                ("pexels", "Snow Capped Volcano in the Andes"),
        ]):
            sdb.them_clip(conn, {"id": sdb.lam_id(nguon, str(i)), "nguon": nguon,
                                 "tieu_de": ten, **tag_tu_tieu_de(ten)})
        hd = {"ma_tap": "LI999", "dia_danh": "", "chu_the_tap": [],
              "khoi": [
                  {"v0": 0, "v1": 2, "L1": ["market"], "L2": [], "L3": [],
                   "neo": False, "uv": [{"nguon": "envato"}]},
                  {"v0": 2, "v1": 4, "L1": ["volcano"], "L2": [], "L3": [],
                   "neo": False, "uv": [{"nguon": "pexels"}]},
              ]}
        # còn Envato: cả 2 khối có hình
        day_du = thuoc.do_nhu_auto(conn, hd, bo_nguon=())
        assert day_du["co_uv"] == 2 and day_du["mat"] == 0
        # bỏ Envato: khối "market" trống -> đúng chỗ Auto hụt so với đồng kiểm
        auto = thuoc.do_nhu_auto(conn, hd)
        assert auto["co_uv"] == 1 and auto["ty_le_co_uv"] == 0.5
        assert auto["mat"] == 1
    finally:
        conn.close()


def test_lop_dung_lai_tu_hop_dong_khong_goi_LLM():
    from autoedit.offline import thuoc

    lop = thuoc.lop_tu_hop_dong({"khoi": [
        {"L1": ["a"], "L2": ["b"], "L3": ["c"], "neo": False, "mood": "warm"},
        {"L1": [], "L2": [], "L3": [], "truu_tuong": True},
    ]})
    assert lop[0].truc_chi == ["a"] and lop[0].neo is False
    assert lop[0].mood == "warm" and lop[1].truu_tuong is True
    assert lop[1].neo is True                      # thiếu khoá -> mặc định cũ


# ============ Footage ĐÃ GIAO không được ghi thành "ref" (07/09 tối) ========
# Trước bản vá, `nap_ref_tap` rglob("*.mp4") nuốt cả `Compose Timeline/.../
# materials/` — footage tool đã tải và giao cho editor — rồi ghi vào Library
# dưới nhãn nguon='ref'. Sổ nguồn gốc ghi sai: clip mua Envato thành "phim mẫu".

def test_chi_nhan_file_ten_ref_o_thu_muc_tap(tmp_path):
    from autoedit.sotra.hut import loc_file_ref

    tap = tmp_path / "RenderY"
    (tap / "Compose Timeline" / "C1" / "draft" / "materials").mkdir(parents=True)
    (tap / "C1").mkdir()
    for p in ["ref 1.mp4", "ref 2.mp4", "LI103 1080 0sub.mp4"]:
        (tap / p).write_bytes(b"x")
    (tap / "C1" / "Ref tu quay.mp4").write_bytes(b"x")          # ref riêng chương
    (tap / "Compose Timeline/C1/draft/materials/b000_aerial.mp4").write_bytes(b"x")
    (tap / "Compose Timeline/C1/draft/materials/ref_nham.mp4").write_bytes(b"x")

    ds, loai = loc_file_ref(tap)
    ten = sorted(p.name for p in ds)
    assert ten == ["Ref tu quay.mp4", "ref 1.mp4", "ref 2.mp4"]
    assert loai == 3          # bản final + b000 + ref_nham nằm trong materials


def test_don_ref_nham_go_dung_dong_va_giu_file(tmp_path, monkeypatch):
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    conn = sdb.mo()
    try:
        anh = tmp_path / "frame.jpg"
        anh.write_bytes(b"jpg")
        goc = tmp_path / "vid.mp4"
        goc.write_bytes(b"mp4")
        sdb.them_clip(conn, {"id": "ref:x:0-1", "nguon": "ref", "tieu_de": "that",
                             "path_local": str(tmp_path / "ref 1.mp4")})
        sdb.them_clip(conn, {"id": "ref:y:0-1", "nguon": "ref", "tieu_de": "nham",
                             "path_local": str(goc), "frame_dau": str(anh)})
        sdb.ghi_su_kien(conn, "ref:y:0-1", "them")
        sdb.xoa_clip(conn, "ref:y:0-1")
        conn.commit()

        con = [r[0] for r in conn.execute("SELECT id FROM clip")]
        assert con == ["ref:x:0-1"]                   # chỉ gỡ dòng sai
        assert conn.execute("SELECT COUNT(*) FROM clip_fts WHERE id=?",
                            ("ref:y:0-1",)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM su_kien WHERE clip_id=?",
                            ("ref:y:0-1",)).fetchone()[0] == 0
        assert not anh.exists()                       # ảnh frame Library sinh: xoá
        assert goc.exists()                           # FILE VIDEO: không đụng
    finally:
        conn.close()


# ================= BẬC 3 — dải hình chẻ theo Framing (07/09 tối) ============
# PH3: dải hình sinh 1-1 với khối nên nhịp video = nhịp THỞ của người đọc voice,
# không phải nhịp kênh ref. Đo được: median miếng hình lệch -32%/-34% dưới chuẩn
# kênh ở 2 chương độc lập, và có chương chứa shot 18 giây.

def _khoi(v0, v1, tho=0.0, ranh_mem=None):
    return {"v0": v0, "v1": v1, "tho": tho, "tho_them": 0.0,
            "ranh_mem": ranh_mem or [], "uv": [{"nguon": "ref"}], "chon": 0}


def test_khong_co_framing_thi_GIU_NGUYEN_hanh_vi_cu():
    from autoedit.offline import hinh

    k = [_khoi(0, 18, tho=0.5)]
    assert len(hinh.sinh_tu_khoi(k)) == 1                  # than=0 -> 1 khối 1 miếng
    assert hinh.sinh_tu_khoi(k)[0]["dur"] == 18.5


def test_khoi_dai_duoc_che_ve_quanh_chuan_kenh():
    from autoedit.offline import hinh

    ra = hinh.sinh_tu_khoi([_khoi(0, 18, tho=0.5)], than=4.73, hold=0.0)
    assert len(ra) == 4
    assert all(1.6 * 4.73 > h["dur"] >= hinh.SAN_CHE_S for h in ra)
    assert sum(h["dur"] for h in ra) == pytest.approx(18.5, abs=0.01)
    assert all(h["khoi_goc"] == 0 for h in ra)             # vẫn thuộc khối gốc


def test_che_NE_VE_ranh_mem_co_san():
    """Chẻ giữa câu liền mạch thì thấy gượng — né về chỗ người đọc đã ngắt."""
    from autoedit.offline import hinh

    ra = hinh.sinh_tu_khoi([_khoi(0, 18, tho=0.5, ranh_mem=[4.5, 9.0, 13.6])],
                           than=4.73)
    assert [h["t0"] for h in ra] == [0.0, 4.5, 9.0, 13.6]


def test_khoi_NGAN_khong_bi_dong_toi():
    from autoedit.offline import hinh

    ra = hinh.sinh_tu_khoi([_khoi(0, 3), _khoi(3, 6)], than=4.73)
    assert len(ra) == 2 and [h["dur"] for h in ra] == [3.0, 3.0]


def test_khong_de_lai_mieng_duoi_san():
    """Ranh mềm lệch sát mép cũng không được đẻ ra miếng 0,2s."""
    from autoedit.offline import hinh

    ra = hinh.sinh_tu_khoi([_khoi(0, 10, ranh_mem=[4.9, 5.0, 5.1])], than=4.73)
    assert all(h["dur"] >= hinh.SAN_CHE_S for h in ra)
    assert sum(h["dur"] for h in ra) == pytest.approx(10.0, abs=0.01)


def test_hold_giu_lai_shot_dai_nhung_KHONG_giu_shot_qua_dai():
    from autoedit.offline import hinh

    # 8s = 1,7× chuẩn: trong trần giữ (2,5×) -> quota hold cho phép để nguyên
    giu = hinh.sinh_tu_khoi([_khoi(0, 8)], than=4.73, hold=1.0)
    assert len(giu) == 1
    # 18s = 3,8× chuẩn: quá trần -> PHẢI chẻ dù quota hold còn
    van_che = hinh.sinh_tu_khoi([_khoi(0, 18)], than=4.73, hold=1.0)
    assert len(van_che) == 4


def test_ung_vien_cua_khoi_gan_vao_MIENG_DAU():
    from autoedit.offline import hinh

    ra = hinh.sinh_tu_khoi([_khoi(0, 18)], than=4.73)
    assert ra[0]["uv"] and ra[0]["chon"] == 0
    assert all(not h["uv"] and h["chon"] == -1 for h in ra[1:])


def test_mieng_phu_kin_o_khoi_khong_ho_khong_lan():
    """Bất biến của dải hình: miếng phải lát KÍN ô [nói..thở] của khối gốc."""
    from autoedit.offline import hinh

    khoi = [_khoi(0, 12, tho=1.0), _khoi(13, 20, tho=0.5)]
    ra = hinh.sinh_tu_khoi(khoi, than=4.73)
    moc = hinh.moc_timeline(khoi)
    for i, (n0, _n1, n2) in enumerate(moc):
        ds = [h for h in ra if h["khoi_goc"] == i]
        assert ds and ds[0]["t0"] == pytest.approx(n0, abs=0.01)
        assert ds[-1]["t0"] + ds[-1]["dur"] == pytest.approx(n2, abs=0.01)
        for a, b in zip(ds, ds[1:]):
            assert a["t0"] + a["dur"] == pytest.approx(b["t0"], abs=0.01)
