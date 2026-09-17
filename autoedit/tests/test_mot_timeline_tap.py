r"""MỘT TIMELINE CHO CẢ TẬP — QĐ17 (user chốt 17/09).

User: *"Vẫn với cách nhập liệu cũ (H, C, E) nhưng bây giờ tôi muốn hòa chung tất
cả vào 1 timeline thay vì chia như cũ. Việc chia chỉ thể hiện bằng cách đặt tên
khối."* Chốt: **hướng A** (gộp thật ở tầng dữ liệu), **khoá sổ và giao hàng cho
cả tập**, chương AUTO không tự khoá/xuất nữa, gộp thêm chương chưa duyệt ranh
thì tập lùi về pha 1, nhãn khối = mã chương (H, C1, C2…, E), có khoá phiên bản
khi lưu.

THIẾT KẾ: tập là MỘT PROJECT BÌNH THƯỜNG — `media/voice_master.wav` là voice
các chương nối lại (mỗi chương cắt từ `offset` của nó), `offline.json` là hợp
đồng các chương nối lại (mốc dịch, mỗi khối mang `chuong`). Nhờ vậy 16 endpoint
`/api/offline/{project_id}` và panel dùng lại nguyên: voice, PUT, khoá sổ,
Export, trim, Add Shot, nhạc, ±1s.

ĐO THẬT 17/09 (projects production):
    - 9/11 tập về đúng thứ tự H→C→E; **LI103 lệch**: C2 chạy lại 4 lần, C4 về
      SAU CÙNG -> không thể "nối vào đuôi", phải ghép THEO ĐOẠN (thay/chèn đúng
      đoạn của chương đó, giữ chỉnh tay các đoạn khác).
    - voice master đều PCM 48 kHz nhưng 2 file mono / 4 file stereo -> nối phải
      ép về cùng số kênh.
    - 0/86 hợp đồng có khe giữa khối -> nối liền mạch không sinh lỗ.
    - hợp đồng tập LI089 ≈ 5,3 MB JSON (571 khối · 587 miếng · 7 971 ứng viên).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1] / "autoedit" / "web" / "static" / "index.html"


# ───────────────────────────── dựng chương giả ─────────────────────────────

def _wav(dich: Path, giay: float, sr: int = 48000, kenh: int = 2) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"sine=frequency=220:duration={giay}",
                    "-ar", str(sr), "-ac", str(kenh), str(dich)], check=True)


def _dai(f: Path) -> float:
    from autoedit.project import ffprobe_duration

    return float(ffprobe_duration(f) or 0.0)


def _probe(f: Path) -> tuple[int, int]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                        "-show_entries", "stream=sample_rate,channels", "-of", "json",
                        str(f)], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    return int(s["sample_rate"]), int(s["channels"])


def _uv(i: str) -> dict:
    return {"id": f"pexels:{i}", "nguon": "pexels", "tieu_de": i, "lop": "L1",
            "url_anh": "", "url_video": "", "dai_s": 20}


def _hd_chuong(offset: float, dai_wav: float, ma_tap: str = "LI900",
               trang_thai: str = "pha2", du_cuoi: float = 0.0) -> dict:
    """2 khối phủ [0 .. dai_wav-offset-du_cuoi]; `du_cuoi` = im lặng thừa cuối file
    không nằm trong khối nào (cat_khoi bỏ đuôi < 1s)."""
    from autoedit.offline import hinh as mhinh

    het = round(dai_wav - offset - du_cuoi, 2)
    a = round(het / 2, 2)
    khoi = [{"v0": 0.0, "v1": round(a - 0.4, 2), "tho": 0.4, "tho_them": 0.0,
             "loi": "cau mot", "ranh_mem": [], "goi_y_che": False,
             "uv": [_uv("a")], "chon": 0, "khoa": False, "nguoi_sua": False,
             "dich": "câu một"},
            {"v0": a, "v1": round(het - 0.3, 2), "tho": 0.3, "tho_them": 0.0,
             "loi": "cau hai", "ranh_mem": [], "goi_y_che": False,
             "uv": [_uv("b")], "chon": 0, "khoa": False, "nguoi_sua": False,
             "dich": "câu hai"}]
    hd = {"phien_ban": 1, "ma_tap": ma_tap, "dia_danh": "", "ngach": "SENIOR HEALTH",
          "nhan_vat": {}, "nguoi_tao": "haint", "offset": offset,
          "tong_voice": round(dai_wav - offset, 2), "avd_s": 0, "dong_kiem": True,
          "kieu_chay": "manual", "framing": {}, "uu_tien_nguon": "",
          "chu_the_tap": ["x"], "trang_thai": trang_thai, "khoi": khoi,
          "canh_bao": ["thiếu framing"]}
    hd["hinh"] = mhinh.sinh_tu_khoi(khoi)
    return hd


def _chuong_gia(projects: Path, ma: str, offset: float, dai_wav: float,
                sr: int = 48000, kenh: int = 2, trang_thai: str = "pha2",
                du_cuoi: float = 0.0, ten_tap: str = "LI900",
                pid: str | None = None) -> Path:
    d = projects / (pid or f"{ma.lower()}-20260917-{int(dai_wav * 100):06d}")
    (d / "media").mkdir(parents=True)
    _wav(d / "media" / "voice_master.wav", dai_wav, sr, kenh)
    goc = projects.parent / "US" / ten_tap / "RenderY" / ma / f"{ma}.txt"
    (d / "project.json").write_text(json.dumps({
        "project_id": d.name, "title": ma, "created_at": "2026-09-17T00:00:00+00:00",
        "inputs": {"original_script_path": str(goc), "channel": "SENIOR HEALTH"},
        "stages": {}}, ensure_ascii=False), encoding="utf-8")
    (d / "offline.json").write_text(json.dumps(
        _hd_chuong(offset, dai_wav, ten_tap, trang_thai, du_cuoi), ensure_ascii=False),
        encoding="utf-8")
    return d


# ─────────────────────────── hàm thuần: nối hợp đồng ───────────────────────────

def test_noi_hop_dong_dich_moc_va_gan_nhan_chuong():
    """H (5,0s voice) + C1 (3,4s): khối C1 dịch đúng 5,0s trên trục VOICE; miếng
    hình C1 dịch đúng tổng timeline của H (voice + thở người thêm)."""
    from autoedit.offline import hinh as mhinh
    from autoedit.offline.tap import noi_hop_dong

    h = _hd_chuong(0.5, 5.5)                      # voice 5,0s
    h["khoi"][1]["tho_them"] = 1.0                # người nới thở +1s ở khối cuối H
    h["hinh"] = mhinh.sinh_tu_khoi(h["khoi"])
    c1 = _hd_chuong(1.0, 4.4)                     # voice 3,4s
    c1["khoi"][0]["tho_them"] = -0.2
    c1["hinh"] = mhinh.sinh_tu_khoi(c1["khoi"])

    hd = noi_hop_dong([{"ma": "H", "project_id": "h-1", "hd": h, "dai_voice": 5.0},
                       {"ma": "C1", "project_id": "c1-1", "hd": c1, "dai_voice": 3.4}])

    assert hd["la_tap"] is True and hd["offset"] == 0
    assert [k["chuong"] for k in hd["khoi"]] == ["H", "H", "C1", "C1"]
    assert hd["khoi"][2]["v0"] == pytest.approx(5.0, abs=0.001)
    assert hd["khoi"][3]["v1"] == pytest.approx(5.0 + c1["khoi"][1]["v1"], abs=0.001)
    # miếng đầu của C1 nằm ở tổng timeline của H = 5,0 voice + 1,0 thở thêm
    dau_c1 = [x for x in hd["hinh"] if x["khoi_goc"] == 2][0]
    assert dau_c1["t0"] == pytest.approx(mhinh.tong_dai(h["khoi"]), abs=0.001)
    assert dau_c1["t0"] == pytest.approx(6.0, abs=0.001)
    assert mhinh.kiem(hd) == [], mhinh.kiem(hd)
    assert mhinh.tong_dai(hd["khoi"]) == pytest.approx(5.0 + 3.4 + 1.0 - 0.2, abs=0.001)
    assert hd["tong_voice"] == pytest.approx(8.4, abs=0.001)
    assert [c["ma"] for c in hd["chuong_ds"]] == ["H", "C1"]
    assert hd["chuong_ds"][0]["dai_voice"] == 5.0
    assert hd["canh_bao"] == ["H: thiếu framing", "C1: thiếu framing"]


def test_noi_hop_dong_GIU_tong_noi_va_lua_chon():
    """Voice bất biến (`_noi`) + lựa chọn hình/chỉnh tay đi theo đoạn."""
    from autoedit.offline.tap import noi_hop_dong

    h, c1 = _hd_chuong(0.5, 5.5), _hd_chuong(1.0, 4.4)
    c1["hinh"][0]["chon"] = -1
    c1["hinh"][0]["nguoi_sua"] = True
    hd = noi_hop_dong([{"ma": "H", "project_id": "h", "hd": h, "dai_voice": 5.0},
                       {"ma": "C1", "project_id": "c1", "hd": c1, "dai_voice": 3.4}])
    noi = lambda x: round(sum(k["v1"] - k["v0"] for k in x["khoi"]), 3)  # noqa: E731
    assert noi(hd) == pytest.approx(noi(h) + noi(c1), abs=0.001)
    mieng_c1 = [x for x in hd["hinh"] if x["khoi_goc"] >= 2]
    assert mieng_c1[0]["chon"] == -1 and mieng_c1[0]["nguoi_sua"] is True
    assert hd["khoi"][0]["uv"][0]["id"] == "pexels:a"


def test_im_lang_thua_cuoi_chuong_NHAP_vao_tho_khoi_cuoi():
    """`cat_khoi` bỏ đuôi im lặng < 1s. File voice vẫn CÓ đoạn đó, nên khi nối
    chương sau phải bắt đầu SAU đoạn đó — nếu không voice C1 lệch hình 0,7s.
    Cách xử: thở khối cuối nở ra phủ hết đuôi (đúng bản chất: im lặng thật)."""
    from autoedit.offline import hinh as mhinh
    from autoedit.offline.tap import noi_hop_dong

    h = _hd_chuong(0.5, 5.5, du_cuoi=0.7)        # khối phủ tới 4,3 · file dài 5,0
    c1 = _hd_chuong(1.0, 4.4)
    hd = noi_hop_dong([{"ma": "H", "project_id": "h", "hd": h, "dai_voice": 5.0},
                       {"ma": "C1", "project_id": "c1", "hd": c1, "dai_voice": 3.4}])
    cuoi_h = hd["khoi"][1]
    assert cuoi_h["v1"] + cuoi_h["tho"] == pytest.approx(5.0, abs=0.001)
    assert hd["khoi"][2]["v0"] == pytest.approx(5.0, abs=0.001)
    assert mhinh.kiem(hd) == [], mhinh.kiem(hd)


def test_tach_doan_la_nghich_dao_cua_noi():
    """Gộp lại lần sau phải lấy được đoạn CŨ (đã chỉnh tay) ra ở toạ độ chương."""
    from autoedit.offline.tap import noi_hop_dong, tach_doan

    h, c1 = _hd_chuong(0.5, 5.5), _hd_chuong(1.0, 4.4)
    h["khoi"][1]["tho_them"] = 1.0
    hd = noi_hop_dong([{"ma": "H", "project_id": "h", "hd": h, "dai_voice": 5.0},
                       {"ma": "C1", "project_id": "c1", "hd": c1, "dai_voice": 3.4}])
    doan = tach_doan(hd)
    assert [d["ma"] for d in doan] == ["H", "C1"]
    assert doan[1]["dai_voice"] == 3.4 and doan[1]["project_id"] == "c1"
    kc = doan[1]["hd"]["khoi"]
    assert kc[0]["v0"] == pytest.approx(0.0, abs=0.001)
    assert kc[1]["v1"] == pytest.approx(c1["khoi"][1]["v1"], abs=0.001)
    hc = doan[1]["hd"]["hinh"]
    assert hc[0]["t0"] == pytest.approx(0.0, abs=0.001) and hc[0]["khoi_goc"] == 0
    # nối lại từ đoạn đã tách phải ra y nguyên
    lai = noi_hop_dong(doan)
    assert [round(k["v0"], 3) for k in lai["khoi"]] == [round(k["v0"], 3) for k in hd["khoi"]]
    assert [round(x["t0"], 3) for x in lai["hinh"]] == [round(x["t0"], 3) for x in hd["hinh"]]


def test_thu_tu_chuong_H_C_E_khong_phai_A_Z():
    from autoedit.offline.tap import thu_tu_chuong

    assert sorted(["E", "C10", "H", "C2", "C1"], key=thu_tu_chuong) == \
        ["H", "C1", "C2", "C10", "E"]


# ────────────────────────── ổ đĩa: gộp tập thật ──────────────────────────

def test_gop_tap_noi_voice_khac_kenh_va_ra_project_binh_thuong(tmp_path):
    """H mono 22,05k + C1 stereo 48k -> master tập 48k stereo, dài đúng tổng
    (mỗi chương cắt từ offset). Project tập đọc được như mọi project khác."""
    from autoedit.duong_dan import nhan_chuong_tu_script, ten_draft_chuong
    from autoedit.offline import hinh as mhinh, runner as orun
    from autoedit.offline.tap import gop_tap, ten_project_tap
    from autoedit.sotra.db import ma_tap_tu_duong_dan
    from autoedit.web import server

    pr = tmp_path / "projects"
    dh = _chuong_gia(pr, "H", 0.5, 6.0, sr=22050, kenh=1)
    dc = _chuong_gia(pr, "C1", 1.0, 5.0, sr=48000, kenh=2)
    kq = gop_tap(pr, "LI900", {"H": dh, "C1": dc}, nguoi_tao="haint")

    assert kq["project_id"] == ten_project_tap("LI900") == "li900-tap"
    d = pr / "li900-tap"
    master = d / "media" / "voice_master.wav"
    assert _dai(master) == pytest.approx((6.0 - 0.5) + (5.0 - 1.0), abs=0.06)
    assert _probe(master) == (48000, 2)

    hd = orun.doc(d)
    assert hd["la_tap"] is True and hd["offset"] == 0
    assert [c["ma"] for c in hd["chuong_ds"]] == ["H", "C1"]
    assert hd["chuong_ds"][0]["project_id"] == dh.name
    assert len(hd["khoi"]) == 4 and hd["khoi"][2]["chuong"] == "C1"
    assert hd["khoi"][2]["v0"] == pytest.approx(5.5, abs=0.06)
    assert hd["tong_voice"] == pytest.approx(9.5, abs=0.06)
    assert hd["nguoi_tao"] == "haint" and hd["ma_tap"] == "LI900"
    assert mhinh.kiem(hd) == [], mhinh.kiem(hd)
    assert kq["moi"] == ["H", "C1"] and kq["giu"] == []

    assert server._read_project(d) is not None, "project.json tập không đọc được"
    goc = json.loads((d / "project.json").read_text(encoding="utf-8"))["inputs"]["original_script_path"]
    assert nhan_chuong_tu_script(goc) == "TAP"
    assert ma_tap_tu_duong_dan(goc) == "LI900"
    assert ten_draft_chuong(ma_tap_tu_duong_dan(goc), nhan_chuong_tu_script(goc)) == "OFF_LI900_TAP"


def test_gop_lai_GIU_chinh_tay_va_CHEN_chuong_ve_muon_dung_cho(tmp_path):
    """LI103 thật: C4 về SAU CÙNG. H+E gộp trước, người chỉnh E; C1 về sau
    -> chèn giữa H và E, E trượt theo nhưng giữ nguyên chỉnh tay."""
    from autoedit.offline import runner as orun
    from autoedit.offline.tap import gop_tap

    pr = tmp_path / "projects"
    dh = _chuong_gia(pr, "H", 0.5, 6.0)
    de = _chuong_gia(pr, "E", 0.0, 4.0)
    gop_tap(pr, "LI900", {"H": dh, "E": de}, nguoi_tao="haint")
    d = pr / "li900-tap"
    hd = orun.doc(d)
    assert [k["chuong"] for k in hd["khoi"]] == ["H", "H", "E", "E"]
    hd["khoi"][2]["tho_them"] = 0.5                   # người chỉnh E
    hd["khoi"][2]["nguoi_sua"] = True
    hd["hinh"][-1]["chon"] = -1
    hd["hinh"][-1]["nguoi_sua"] = True
    hd["nhac"] = {"id": "nhac:1", "tieu_de": "x", "dai_s": 60}
    orun.luu(d, hd)

    dc = _chuong_gia(pr, "C1", 1.0, 5.0)
    kq = gop_tap(pr, "LI900", {"H": dh, "C1": dc, "E": de}, nguoi_tao="haint")
    hd = orun.doc(d)
    assert kq["moi"] == ["C1"] and sorted(kq["giu"]) == ["E", "H"]
    assert [k["chuong"] for k in hd["khoi"]] == ["H", "H", "C1", "C1", "E", "E"]
    assert hd["khoi"][4]["v0"] == pytest.approx(5.5 + 4.0, abs=0.06)
    assert hd["khoi"][4]["tho_them"] == 0.5 and hd["khoi"][4]["nguoi_sua"] is True
    assert hd["hinh"][-1]["chon"] == -1 and hd["hinh"][-1]["nguoi_sua"] is True
    assert hd["nhac"]["id"] == "nhac:1", "nhạc của tập mất sau khi gộp lại"
    assert _dai(d / "media" / "voice_master.wav") == pytest.approx(5.5 + 4.0 + 4.0, abs=0.08)


def test_lam_lai_chuong_THAY_dung_doan_do(tmp_path):
    """Phân tích lại C1 -> gộp lại với lam_lai={C1}: đoạn C1 lấy bản mới (mất
    chỉnh tay ĐOẠN ĐÓ, như luật phân tích lại), H giữ nguyên."""
    from autoedit.offline import runner as orun
    from autoedit.offline.tap import gop_tap

    pr = tmp_path / "projects"
    dh = _chuong_gia(pr, "H", 0.5, 6.0)
    dc = _chuong_gia(pr, "C1", 1.0, 5.0)
    gop_tap(pr, "LI900", {"H": dh, "C1": dc}, nguoi_tao="haint")
    d = pr / "li900-tap"
    hd = orun.doc(d)
    hd["khoi"][0]["tho_them"] = 1.0        # chỉnh H
    hd["khoi"][2]["tho_them"] = 0.8        # chỉnh C1
    orun.luu(d, hd)

    kq = gop_tap(pr, "LI900", {"H": dh, "C1": dc}, lam_lai={"C1"}, nguoi_tao="haint")
    hd = orun.doc(d)
    assert kq["thay"] == ["C1"] and kq["giu"] == ["H"]
    assert hd["khoi"][0]["tho_them"] == 1.0, "chỉnh tay H bị mất"
    assert hd["khoi"][2]["tho_them"] == 0.0, "C1 chưa lấy bản mới"


def test_gop_them_chuong_CHUA_duyet_ranh_thi_tap_lui_pha_1(tmp_path):
    """User chốt 17/09: tập pha 2 gộp thêm chương pha 1 -> lùi về pha 1 (bấm
    một cái là về pha 2, không mất lựa chọn hình). Chương đã pha 2 (AUTO) thì
    tập giữ pha 2. Tập ĐÃ KHOÁ mà gộp thêm -> mở lại ở pha 2."""
    from autoedit.offline import runner as orun
    from autoedit.offline.tap import gop_tap

    pr = tmp_path / "projects"
    dh = _chuong_gia(pr, "H", 0.5, 6.0, trang_thai="pha2")
    gop_tap(pr, "LI900", {"H": dh})
    d = pr / "li900-tap"
    assert orun.doc(d)["trang_thai"] == "pha2"

    dc = _chuong_gia(pr, "C1", 1.0, 5.0, trang_thai="pha2")
    gop_tap(pr, "LI900", {"H": dh, "C1": dc})
    assert orun.doc(d)["trang_thai"] == "pha2", "chương pha 2 mà tập bị lùi"

    dc2 = _chuong_gia(pr, "C2", 0.0, 3.0, trang_thai="pha1")
    gop_tap(pr, "LI900", {"H": dh, "C1": dc, "C2": dc2})
    assert orun.doc(d)["trang_thai"] == "pha1", "chương pha 1 vào mà tập không lùi"

    hd = orun.doc(d)
    hd["trang_thai"] = "khoa"
    orun.luu(d, hd)
    de = _chuong_gia(pr, "E", 0.0, 3.0, trang_thai="pha2")
    gop_tap(pr, "LI900", {"H": dh, "C1": dc, "C2": dc2, "E": de})
    assert orun.doc(d)["trang_thai"] == "pha2", "tập khoá rồi gộp thêm phải mở lại"


def test_clip_da_dung_KHONG_dem_hop_dong_tap(tmp_path):
    """Hợp đồng tập chứa lại lựa chọn của mọi chương -> đếm nó là đếm đôi."""
    from autoedit.offline.dung import clip_da_dung_trong_tap

    pr = tmp_path / "projects"
    for ten, la_tap in (("c1-x", False), ("li900-tap", True)):
        d = pr / ten
        d.mkdir(parents=True)
        (d / "offline.json").write_text(json.dumps({
            "ma_tap": "LI900", "la_tap": la_tap,
            "hinh": [{"chon": 0, "uv": [{"id": "pexels:1"}]}]}), encoding="utf-8")
    assert clip_da_dung_trong_tap(pr, "LI900", tru="c2-dang-dung") == {"pexels:1": 1}


# ───────────────────────────── máy chủ ─────────────────────────────

@pytest.fixture
def may_chu(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.sotra import db as sdb
    from autoedit.web import server

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    pr = tmp_path / "projects"
    pr.mkdir()
    monkeypatch.setattr(server, "PROJECTS_DIR", pr)
    return TestClient(server.app), pr


def test_api_gop_tap_va_tap_list(may_chu):
    tc, pr = may_chu
    _chuong_gia(pr, "H", 0.5, 6.0)
    _chuong_gia(pr, "C1", 1.0, 5.0)
    _chuong_gia(pr, "E", 0.0, 3.0, trang_thai="pha1")

    r = tc.post("/api/offline/tap/LI900/gop", json={})
    assert r.status_code == 200, r.text
    assert r.json()["project_id"] == "li900-tap"
    assert r.json()["moi"] == ["H", "C1", "E"]

    t = [x for x in tc.get("/api/offline/tap-list").json()["tap"] if x["ma"] == "LI900"]
    assert t, "tap-list không có LI900"
    assert t[0]["gop"]["project_id"] == "li900-tap"
    assert t[0]["gop"]["chuong"] == ["H", "C1", "E"]
    assert t[0]["gop"]["trang_thai"] == "pha1"
    assert [c["nhan"] for c in t[0]["chuong"]] == ["H", "C1", "E"], \
        "project tập lọt vào hàng chip chương"

    # tập là project bình thường: đọc, voice, khoá sổ đều chạy đường cũ
    d = tc.get("/api/offline/li900-tap")
    assert d.status_code == 200 and d.json()["hop_dong"]["la_tap"] is True
    v = tc.get("/api/offline/li900-tap/voice")
    assert v.status_code == 200 and v.headers["content-type"].startswith("audio/wav")
    k = tc.post("/api/offline/li900-tap/khoa-so")
    assert k.status_code == 200
    assert tc.get("/api/offline/li900-tap").json()["hop_dong"]["trang_thai"] == "khoa"


def test_api_gop_tap_chua_co_chuong_nao_phan_tich_thi_422(may_chu):
    tc, pr = may_chu
    d = _chuong_gia(pr, "H", 0.5, 6.0)
    (d / "offline.json").unlink()
    r = tc.post("/api/offline/tap/LI900/gop", json={})
    assert r.status_code == 422, r.text


# ───────────────────── khoá phiên bản khi lưu (chốt 17/09) ─────────────────────

def _hop_dong_don(pr: Path, phien_ban: int = 3, tab_cuoi: str = "") -> Path:
    d = pr / "c9-x"
    d.mkdir(parents=True, exist_ok=True)
    hd = {"phien_ban": phien_ban, "tab_cuoi": tab_cuoi, "trang_thai": "pha2",
          "khoi": [{"v0": 0.0, "v1": 3.0, "tho": 0.0, "tho_them": 0.0, "loi": "a"}],
          "hinh": [{"t0": 0.0, "dur": 3.0, "khoi_goc": 0, "uv": [], "chon": -1}]}
    (d / "offline.json").write_text(json.dumps(hd), encoding="utf-8")
    return d


def _doc(d: Path) -> dict:
    return json.loads((d / "offline.json").read_text(encoding="utf-8"))


def test_luu_tang_phien_ban_va_ghi_tab(may_chu):
    tc, pr = may_chu
    d = _hop_dong_don(pr, 3)
    r = tc.put("/api/offline/c9-x", json=_doc(d), headers={"X-Of-Tab": "A"})
    assert r.status_code == 200, r.text
    assert r.json()["phien_ban"] == 4
    assert _doc(d)["phien_ban"] == 4 and _doc(d)["tab_cuoi"] == "A"


def test_tab_khac_luu_ban_CU_hon_thi_409_bao_tai_lai(may_chu):
    """Hai tab (hay hai người) cùng mở: tab sau lưu bản cũ thì phải bị chặn,
    không được đè lên bản mới của tab trước."""
    tc, pr = may_chu
    d = _hop_dong_don(pr, 3)
    cu = _doc(d)                                    # cả hai tab mở bản 3
    assert tc.put("/api/offline/c9-x", json=cu, headers={"X-Of-Tab": "A"}).status_code == 200
    r = tc.put("/api/offline/c9-x", json=cu, headers={"X-Of-Tab": "B"})
    assert r.status_code == 409, r.text
    assert "tải lại" in r.text.lower()
    assert _doc(d)["tab_cuoi"] == "A", "bản của B đã đè lên A"


def test_tab_khac_nhung_ban_MOI_thi_luu_duoc(may_chu):
    tc, pr = may_chu
    d = _hop_dong_don(pr, 4, tab_cuoi="A")
    r = tc.put("/api/offline/c9-x", json=_doc(d), headers={"X-Of-Tab": "B"})
    assert r.status_code == 200, r.text
    assert _doc(d)["phien_ban"] == 5 and _doc(d)["tab_cuoi"] == "B"


def test_cung_tab_ban_cu_van_luu_duoc(may_chu):
    """Các endpoint phía máy chủ (hinh, trim, khoá sổ...) tự tăng phiên bản; tab
    đó lưu tiếp với số cũ KHÔNG phải xung đột — chỉ tab KHÁC mới bị chặn."""
    tc, pr = may_chu
    d = _hop_dong_don(pr, 4, tab_cuoi="A")
    hd = _doc(d)
    hd["phien_ban"] = 2
    assert tc.put("/api/offline/c9-x", json=hd, headers={"X-Of-Tab": "A"}).status_code == 200


def test_client_cu_khong_gui_phien_ban_van_luu(may_chu):
    tc, pr = may_chu
    d = _hop_dong_don(pr, 4, tab_cuoi="A")
    hd = _doc(d)
    hd.pop("phien_ban")
    assert tc.put("/api/offline/c9-x", json=hd).status_code == 200


def test_endpoint_may_chu_ghi_tab_de_tab_khac_bi_chan(may_chu):
    """Khoá sổ từ tab A rồi tab B lưu bản cũ -> 409. Nếu khoá sổ không ghi tab
    thì B đè lên và trạng thái 'khoa' bay mất."""
    tc, pr = may_chu
    d = _hop_dong_don(pr, 3)
    cu = _doc(d)
    assert tc.post("/api/offline/c9-x/khoa-so", headers={"X-Of-Tab": "A"}).status_code == 200
    assert _doc(d)["tab_cuoi"] == "A"
    assert tc.put("/api/offline/c9-x", json=cu, headers={"X-Of-Tab": "B"}).status_code == 409
    assert _doc(d)["trang_thai"] == "khoa"


def test_luu_nhanh_mang_tab_trong_than(may_chu):
    """sendBeacon không gửi được header -> tab nằm trong thân JSON (`_tab`),
    máy chủ đọc rồi bỏ, không lưu vào hợp đồng."""
    tc, pr = may_chu
    d = _hop_dong_don(pr, 4, tab_cuoi="A")
    hd = _doc(d)
    hd["phien_ban"] = 3
    assert tc.post("/api/offline/c9-x/luu-nhanh", json={**hd, "_tab": "B"}).status_code == 409
    assert tc.post("/api/offline/c9-x/luu-nhanh", json={**hd, "_tab": "A"}).status_code == 200
    assert "_tab" not in _doc(d)


# ──────────────────────────── giao diện (Chrome thật) ────────────────────────────

def _h() -> str:
    return GOC.read_text(encoding="utf-8")


def _ham(ten: str) -> str:
    src = _h()
    m = re.search(rf"^(?:async )?function\s+{re.escape(ten)}\s*\(", src, re.M)
    assert m, f"không thấy hàm {ten}"
    i = src.index("{", m.end() - 1)
    sau, muc = i, 0
    while sau < len(src):
        if src[sau] == "{":
            muc += 1
        elif src[sau] == "}":
            muc -= 1
            if muc == 0:
                break
        sau += 1
    return src[m.start():sau + 1]


def _dong(dau: str) -> str:
    for d in _h().splitlines():
        if d.strip().startswith(dau):
            return d.strip()
    raise AssertionError(f"không thấy dòng «{dau}»")


@pytest.fixture(scope="module")
def chrome():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception as exc:  # noqa: BLE001 — máy không có Chrome thì bỏ qua
            pytest.skip(f"không mở được Chrome: {str(exc)[:80]}")
        yield b
        b.close()


def _mo(chrome, tmp_path, html: str):
    f = tmp_path / "t.html"
    f.write_text(html, encoding="utf-8")
    pg = chrome.new_page()
    loi: list[str] = []
    pg.on("pageerror", lambda e: loi.append(str(e)))
    pg.goto(f.as_uri())
    pg.wait_for_timeout(300)
    return pg, loi


TRANG_TL = """<!doctype html><meta charset="utf-8">
<div id="of-thuoc"></div><div id="of-dai"><div id="of-ph"></div></div>
<div id="of-dai-au"></div><div id="of-dai-nh"></div>
<script>
let OF_PID = 'p', OF_PHA = 1, OF_CHON = 0, OF_HCHON = 0, OF_PXS = 14
let OF_HONG = new Set(), OF_AUDIO = null, OF_LANG = null
let OF_HD = __HD__
const esc = s => String(s == null ? '' : s)
function ofAnh() { return '' }
function ofKiemLap() { return new Set() }
function ofVeAll() {} function ofDatPh() {} function toastOf() {}
function ofBoMieng() {} function ofReview() {} function ofKeoMep() {}
__DONG__
__HAM__
</script>"""


def _hd_ui(co_chuong: bool) -> dict:
    from autoedit.offline import hinh as mhinh

    khoi = [{"v0": 0.0, "v1": 2.0, "tho": 0.5, "tho_them": 0.0, "loi": "mot"},
            {"v0": 2.5, "v1": 4.0, "tho": 0.3, "tho_them": 0.0, "loi": "hai"},
            {"v0": 4.3, "v1": 7.0, "tho": 0.2, "tho_them": 0.0, "loi": "ba"}]
    if co_chuong:
        for k, c in zip(khoi, ("H", "H", "C1")):
            k["chuong"] = c
    return {"offset": 0, "khoi": khoi, "hinh": mhinh.sinh_tu_khoi(khoi)}


def _trang_tl(chrome, tmp_path, co_chuong: bool):
    html = (TRANG_TL.replace("__HD__", json.dumps(_hd_ui(co_chuong)))
            .replace("__DONG__", "\n".join([_dong("const ofK ="), _dong("const ofDoiTruoc ="),
                                            _dong("const ofHinh ="), _dong("const ofTong ="),
                                            _dong("const ofUv ="), _dong("const ofFmt =")]))
            .replace("__HAM__", "\n".join([_ham("ofMoc"), _ham("ofVeTL")])))
    return _mo(chrome, tmp_path, html)


def test_ui_khoi_mang_nhan_chuong_va_vach_ranh(chrome, tmp_path):
    """User: "khối H thì tên là H, khối C thì tên là C" — nhãn trên MỖI khối
    voice, cộng vạch ranh ở chỗ đổi chương."""
    pg, loi = _trang_tl(chrome, tmp_path, co_chuong=True)
    pg.evaluate("ofVeTL()")
    assert loi == [], loi
    nhan = pg.evaluate("[...document.querySelectorAll('#of-dai-au .of-au .ch')].map(e => e.textContent)")
    assert nhan == ["H", "H", "C1"], nhan
    ranh = pg.evaluate("[...document.querySelectorAll('#of-dai-au .of-ranh')].map(e => e.textContent.trim())")
    assert ranh == ["H", "C1"], ranh
    # vạch C1 đứng đúng mốc khối 3 (4,3s × 14 px)
    left = pg.evaluate("parseFloat(document.querySelectorAll('#of-dai-au .of-ranh')[1].style.left)")
    assert left == pytest.approx(4.3 * 14, abs=0.05), left


def test_ui_hop_dong_mot_chuong_KHONG_co_nhan(chrome, tmp_path):
    """Chương lẻ (chưa gộp) vẽ y như cũ — không nhãn, không vạch."""
    pg, loi = _trang_tl(chrome, tmp_path, co_chuong=False)
    pg.evaluate("ofVeTL()")
    assert loi == [], loi
    assert pg.evaluate("document.querySelectorAll('#of-dai-au .ch').length") == 0
    assert pg.evaluate("document.querySelectorAll('#of-dai-au .of-ranh').length") == 0
    assert pg.evaluate("document.querySelectorAll('#of-dai-au .of-au').length") == 3


TRANG_CHIP = """<!doctype html><meta charset="utf-8">
<select id="of-tap"><option value="LI900" selected>LI900</option></select>
<span id="of-chuong"></span><select id="of-project"></select>
<script>
let OF_PID = ''
let OF_TAPS = __TAPS__
const OF_TT_NHAN = {chua_phan_tich: 'chưa', pha1: 'duyệt khối', pha2: 'đổ hình', khoa: 'khóa sổ'}
const esc = s => String(s == null ? '' : s)
function ofNap() {} function ofGopTap() {}
__HAM__
</script>"""


def _taps(gop):
    return [{"ma": "LI900", "gop": gop,
             "chuong": [{"project_id": "h-1", "nhan": "H", "trang_thai": "khoa",
                         "he": "dong_kiem", "co_draft": False},
                        {"project_id": "c1-1", "nhan": "C1", "trang_thai": "pha2",
                         "he": "dong_kiem", "co_draft": False}]}]


def test_ui_chip_TAP_va_nut_gop(chrome, tmp_path):
    gop = {"project_id": "li900-tap", "trang_thai": "pha2", "chuong": ["H"], "so_khoi": 12}
    html = (TRANG_CHIP.replace("__TAPS__", json.dumps(_taps(gop)))
            .replace("__HAM__", _ham("ofVeChuong")))
    pg, loi = _mo(chrome, tmp_path, html)
    pg.evaluate("ofVeChuong()")
    assert loi == [], loi
    chip = pg.evaluate("[...document.querySelectorAll('#of-chuong .of-ch.tap')].map(e => e.textContent)")
    assert len(chip) == 1 and "TẬP" in chip[0], chip
    nut = pg.evaluate("[...document.querySelectorAll('#of-chuong button')].map(e => e.textContent)")
    assert any("Gộp" in n for n in nut), nut
    # chip chương vẫn còn (để Phân tích / Phân tích lại)
    assert pg.evaluate("document.querySelectorAll('#of-chuong .of-ch:not(.tap)').length") == 2


def test_ui_chua_co_tap_thi_van_co_nut_gop(chrome, tmp_path):
    html = (TRANG_CHIP.replace("__TAPS__", json.dumps(_taps(None)))
            .replace("__HAM__", _ham("ofVeChuong")))
    pg, loi = _mo(chrome, tmp_path, html)
    pg.evaluate("ofVeChuong()")
    assert loi == [], loi
    assert pg.evaluate("document.querySelectorAll('#of-chuong .of-ch.tap').length") == 0
    nut = pg.evaluate("[...document.querySelectorAll('#of-chuong button')].map(e => e.textContent)")
    assert any("Gộp" in n for n in nut), nut


TRANG_API = """<!doctype html><meta charset="utf-8"><script>
const GUI = []
window.fetch = async (u, o) => { GUI.push({u, headers: o.headers})
  return {ok: true, headers: {get: () => 'application/json'}, json: async () => ({})} }
__DONG__
__HAM__
</script>"""


def test_ui_api_gui_ma_tab(chrome, tmp_path):
    """Mỗi tab một mã; máy chủ dựa vào đó phân biệt 'chính tab này' với 'tab khác'."""
    html = (TRANG_API.replace("__DONG__", "\n".join([_dong("const TOKEN ="), _dong("const H ="),
                                                     _dong("const OF_TAB =")]))
            .replace("__HAM__", _ham("api")))
    pg, loi = _mo(chrome, tmp_path, html)
    pg.evaluate("api('/x', {method: 'PUT', body: '{}'})")
    pg.wait_for_function("() => GUI.length > 0", timeout=3000)
    assert loi == [], loi
    h = pg.evaluate("GUI[0].headers")
    assert h.get("X-Of-Tab") and len(h["X-Of-Tab"]) >= 6, h
