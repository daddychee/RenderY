r"""VẤN ĐỀ 3 — trùng clip GIỮA CÁC CHƯƠNG trong một tập.

User chốt 10/09: phạm vi MỘT TẬP; đo 5 video rồi tính logic; "ref nguồn có giá
trị với từng quốc gia" nên KHÔNG đặt trần mới thay `LIMIT 600`.

ĐO THẬT (mô phỏng `chon_mac_dinh` qua 14/11/7 chương, than=4.73, chỉ phạt từ
chương TRƯỚC, đếm CHƯƠNG chứ không đếm sự kiện):

| Phạt | Trùng LI106 / LI102 / LI089 | Điểm gốc | Ref trong final |
|---|---|---|---|
| 0 | 34% / 33% / 22% | 30.8 | 100% |
| 6 | 12% / 15% / 7% | 30.4 | 100% |
| **20** | **0.6% / 0% / 0%** | 29.7 (−4%) | 100% |

Hai gốc rễ đo được:
1. `tra()` quét ref bằng `LIMIT 600` KHÔNG sắp xếp -> 600 dòng ĐẦU theo rowid,
   72% kho Nepal (1.523/2.123) chưa từng được máy nhìn tới; 100% ref lên final
   LI106 nằm trong đúng 600 dòng đó. Bỏ LIMIT: điểm khớp +12%.
2. `chon_mac_dinh` chỉ nhớ 60s TRONG một chương — sang chương sau quên sạch.
   Phạt 20/chương đã dùng (trần 5) đọc từ `offline.json` chương anh em (KHÔNG
   từ `su_kien len_final`: chỉ ghi khi XUẤT draft, chương `h` LI106 chưa xuất
   bao giờ, c1 có 210 sự kiện vì xuất lại nhiều lần -> phạt oan).
"""

from __future__ import annotations

import json

import pytest

from autoedit.offline import dung
from autoedit.sotra import db as sdb
from autoedit.sotra.tra import PHAT_DA_DUNG, TRAN_DA_DUNG, tra


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    yield c
    c.close()


def _ref(c, i, ten, tap="T1"):
    cid = sdb.lam_id("ref", f"{tap}-ref {i}", "0.00-5.00")
    # tiêu đề phải KHÁC nhau: `gop_ban_trung` gộp cùng nguồn + cùng tiêu đề về
    # một thẻ (user chốt 09/09) — số trong ngoặc không phải chữ nên không vào điểm
    sdb.them_clip(c, {"id": cid, "nguon": "ref", "tieu_de": f"{ten} ({i})", "tap": tap,
                      "geo": "nepal", "t0": 0.0, "t1": 5.0})
    return cid


LOP = {"L0": [], "L1": ["market"], "L2": [], "L3": []}


# ───────────────────────── tra(): phạt clip đã dùng ─────────────────────────

def test_hang_so_da_chot():
    assert PHAT_DA_DUNG == 20.0
    assert TRAN_DA_DUNG == 5


def test_clip_da_dung_o_chuong_khac_tut_xuong_duoi(conn):
    a = _ref(conn, 1, "market stall")
    b = _ref(conn, 2, "market stall")
    # cùng điểm chữ; a đã lên final ở 1 chương khác -> b phải đứng trên
    ra = tra(conn, LOP, so=12, tap="T1", da_dung={a: 1})
    ids = [c["id"] for c in ra]
    assert ids.index(b) < ids.index(a)
    da, db_ = next(c for c in ra if c["id"] == a), next(c for c in ra if c["id"] == b)
    assert db_["diem"] - da["diem"] == pytest.approx(PHAT_DA_DUNG)


def test_phat_theo_so_chuong_co_tran(conn):
    a = _ref(conn, 1, "market stall")
    b = _ref(conn, 2, "market stall")
    d5 = next(c for c in tra(conn, LOP, so=12, tap="T1", da_dung={a: 5}) if c["id"] == a)["diem"]
    d50 = next(c for c in tra(conn, LOP, so=12, tap="T1", da_dung={a: 50}) if c["id"] == a)["diem"]
    d0 = next(c for c in tra(conn, LOP, so=12, tap="T1") if c["id"] == b)["diem"]
    assert d5 == d50                                   # quá trần không phạt thêm
    assert d0 - d5 == pytest.approx(PHAT_DA_DUNG * TRAN_DA_DUNG)


def test_khong_truyen_da_dung_thi_y_nhu_cu(conn):
    for i in range(6):
        _ref(conn, i, f"market stall {i}")
    cu = [c["id"] for c in tra(conn, LOP, so=12, tap="T1", seed=3)]
    moi = [c["id"] for c in tra(conn, LOP, so=12, tap="T1", seed=3, da_dung=None)]
    rong = [c["id"] for c in tra(conn, LOP, so=12, tap="T1", seed=3, da_dung={})]
    assert cu == moi == rong


def test_phat_la_day_xuong_khong_loai(conn):
    a = _ref(conn, 1, "market stall")
    _ref(conn, 2, "market stall")
    ids = [c["id"] for c in tra(conn, LOP, so=12, tap="T1", da_dung={a: 5})]
    assert a in ids


# ───────────────────── tra(): bỏ trần LIMIT 600 khi quét ref ─────────────────

def test_ref_sau_dong_800_van_vao_khay(conn):
    """900 ref cùng khớp từ khoá: FTS cắt 800 (không ORDER BY), quét ref cắt 600
    -> clip 801..900 KHÔNG BAO GIỜ được xét. Bỏ LIMIT thì phải thấy chúng."""
    ids = [_ref(conn, i, f"market view {i}") for i in range(900)]
    sau = set(ids[800:])
    thay = set()
    for seed in range(30):
        thay |= {c["id"] for c in tra(conn, LOP, so=12, tap="T1", seed=seed)}
    assert thay & sau, "clip sau dòng 800 chưa từng vào khay — kho vẫn bị cắt cụt"


# ─────────────── dung: đọc lựa chọn của chương anh em trong tập ───────────────

def _chuong(root, ten, ma_tap, picks, nguoi_sua=False, hong=False):
    d = root / ten
    d.mkdir()
    if hong:
        (d / "offline.json").write_text("{không phải json", encoding="utf-8")
        return
    hinh = []
    for p in picks:
        if p is None:
            hinh.append({"uv": [{"id": "ref:x"}], "chon": -1})
        else:
            hinh.append({"uv": [{"id": "ref:khac"}, {"id": p}], "chon": 1,
                         "nguoi_sua": nguoi_sua})
    (d / "offline.json").write_text(
        json.dumps({"ma_tap": ma_tap, "hinh": hinh}), encoding="utf-8")


def test_dem_theo_chuong_khong_dem_mieng(tmp_path):
    _chuong(tmp_path, "c1-a", "LI9", ["ref:1", "ref:1", "ref:2"])   # ref:1 dùng 2 miếng
    _chuong(tmp_path, "c2-a", "LI9", ["ref:1"])
    _chuong(tmp_path, "c3-a", "LI9", [None])                        # chưa chọn
    _chuong(tmp_path, "h-a", "LI9", ["ref:9"])                      # chương ĐANG dựng
    da = dung.clip_da_dung_trong_tap(tmp_path, "LI9", tru="h-a")
    assert da == {"ref:1": 2, "ref:2": 1}


def test_khong_dem_tap_khac_va_bo_qua_file_hong(tmp_path):
    _chuong(tmp_path, "c1-a", "LI9", ["ref:1"])
    _chuong(tmp_path, "c1-b", "LI8", ["ref:1", "ref:7"])
    _chuong(tmp_path, "c2-b", "LI9", [], hong=True)
    (tmp_path / "rac.txt").write_text("x")
    assert dung.clip_da_dung_trong_tap(tmp_path, "LI9", tru="h") == {"ref:1": 1}


def test_lua_chon_cua_nguoi_cung_tinh(tmp_path):
    _chuong(tmp_path, "c1-a", "LI9", ["ref:5"], nguoi_sua=True)
    assert dung.clip_da_dung_trong_tap(tmp_path, "LI9", tru="h") == {"ref:5": 1}


def test_khong_ma_tap_thi_khong_phat(tmp_path):
    _chuong(tmp_path, "c1-a", "", ["ref:1"])
    assert dung.clip_da_dung_trong_tap(tmp_path, "", tru="h") == {}


# ──────────────────── do_ung_vien / do_lai_khay nối dây xuống tra ────────────

class _Lop:
    truc_chi = ["market"]
    ngu_canh: list = []
    khong_khi: list = []
    neo = ""


def test_do_ung_vien_truyen_da_dung(conn):
    a = _ref(conn, 1, "market stall")
    b = _ref(conn, 2, "market stall")
    k = [object()]
    khay = dung.do_ung_vien(conn, k, [_Lop()], [], tap="T1", da_dung={a: 1})[0]
    ids = [c["id"] for c in khay]
    assert ids.index(b) < ids.index(a)


def test_do_lai_khay_truyen_da_dung(conn):
    a = _ref(conn, 1, "market stall")
    b = _ref(conn, 2, "market stall")
    hd = {"ma_tap": "T1", "chu_the_tap": [], "dia_danh": "",
          "khoi": [{"L1": ["market"], "L2": [], "L3": [], "neo": ""}], "hinh": []}
    dung.do_lai_khay(hd, conn, da_dung={a: 1})
    ids = [c["id"] for c in hd["khoi"][0]["uv"]]     # khay nằm ở KHỐI
    assert ids.index(b) < ids.index(a)
