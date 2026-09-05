# -*- coding: utf-8 -*-
"""OFFLINE (Đợt 2) — cắt khối giao 2 bằng chứng, thở +/-1s, 4 lớp, chọn mặc
định (60s + chốt neo + cấm 3 L3), hợp đồng offline.json, API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoedit.offline import dung, lop4
from autoedit.offline.khoi import Khoi, cat_khoi, chinh_tho, tong_thoi_luong

W = [  # transcript giả: 2 câu quanh 1 ngắt 2s (5.0-7.0) + align lệch cả 2 chiều
    {"text": "one", "start": 0.5, "end": 1.2},
    {"text": "two", "start": 1.3, "end": 2.1},
    {"text": "three", "start": 2.2, "end": 5.2},    # align kết MUỘN hơn audio (5.2 > 5.0)
    {"text": "four", "start": 6.7, "end": 8.0},     # align bắt SỚM hơn silence hết (6.7 < 7.0)
    {"text": "five", "start": 8.1, "end": 10.0},
]
SIL = [(0.0, 0.5), (5.0, 7.0), (10.0, 11.0)]        # im mở đầu + ngắt giữa + đuôi


# ------------------------------------------------------- cắt khối
def test_cat_khoi_giao_2_bang_chung():
    """Nghiệm thu 06/09: thở bắt đầu = max(sil, từ kết) — không ăn voice cũ;
    thở kết = min(sil hết, từ kế bắt đầu) — dứt đúng lúc voice lên."""
    ds, off = cat_khoi(SIL, W, het=10.5)
    assert off == pytest.approx(0.5, abs=0.01)       # quy 0 tại khởi âm đầu
    assert len(ds) == 2
    a = ds[0]
    # thở bắt đầu 5.2 (từ 'three' kết — muộn hơn sil 5.0); kết 6.7 (từ 'four' bắt)
    assert a.v1 == pytest.approx(5.2 - off, abs=0.01)
    assert a.tho == pytest.approx(6.7 - 5.2, abs=0.01)
    assert "three" in a.loi and "four" in ds[1].loi


def test_cat_khoi_ranh_mem_va_goi_y_che():
    sil = SIL + [(3.0, 3.4)]                          # ngắt mềm 0.4s giữa khối 1
    ds, off = cat_khoi(sil, W, het=10.5, than_framing=2.0)
    assert ds[0].ranh_mem == [pytest.approx(3.0 - off, abs=0.01)]
    assert ds[0].goi_y_che is True                    # khối ~4.8s > 2.0*1.6


def test_chinh_tho_am_thanh_that():
    """+/-1s = thao tác ÂM THANH (user 06/09): + chèn cả nơi chưa nghỉ;
    − ăn được vào ngắt tự nhiên nhưng sàn 0.2s — không bao giờ chạm lời."""
    k = Khoi(v0=0, v1=3, tho=1.5)
    chinh_tho(k, 1)
    assert k.tho_them == 1.0
    chinh_tho(k, -1)
    chinh_tho(k, -1)
    assert k.tho_them == -1.0                         # 1 -> 0 -> -1
    chinh_tho(k, -1)
    assert k.tho_them == -1.3                         # chạm sàn 1.5-0.2
    chinh_tho(k, -1)
    assert k.tho_them == -1.3                         # không xuống thêm
    k2 = Khoi(v0=0, v1=3, tho=0.0)                    # nơi voice CHƯA nghỉ
    chinh_tho(k2, 1)
    assert k2.tho_them == 1.0
    chinh_tho(k2, -1)
    chinh_tho(k2, -1)
    assert k2.tho_them == 0.0                         # không âm khi không có ngắt


def test_tong_thoi_luong_voice_bat_bien():
    ds = [Khoi(v0=0, v1=3, tho=1.0), Khoi(v0=4, v1=7, tho=0.5)]
    goc = tong_thoi_luong(ds)
    chinh_tho(ds[0], 2)
    assert tong_thoi_luong(ds) == pytest.approx(goc + 2)
    # phần NÓI không đổi
    assert sum(k.v1 - k.v0 for k in ds) == 6.0


# ------------------------------------------------------- 4 lớp (GLM stub)
class _LLM:
    def complete(self, system, user, model):
        return model(chu_the_tap=["ecuador", "daily life"],
                     khoi=[lop4.LopKhoi(khoi=0, truc_chi=["market stall"],
                                        ngu_canh=["grocery shopping"],
                                        khong_khi=["quito street"], mood="warm")]), None


def test_gan_lop_fail_soft_khoi_sot():
    kq = lop4.gan_lop(["cau mot", "cau hai"], llm=_LLM())
    assert kq.chu_the_tap == ["ecuador", "daily life"]
    assert len(kq.khoi) == 2
    assert kq.khoi[1].truu_tuong is True              # khối LLM bỏ sót -> trừu tượng


# ------------------------------------------------------- chọn mặc định
def _uv(uid, lop, nguon="envato"):
    return {"id": uid, "nguon": nguon, "tieu_de": uid, "lop": lop, "diem": 5,
            "url_anh": "", "url_video": "", "geo": "x", "dai_s": 5}


def test_chon_mac_dinh_luat_60s_va_chot_neo():
    # 3 khối tại 0/30/61s, pool chung A+B: A -> B (A dính 60s) -> A (đã qua 61s)
    ds = [Khoi(v0=t, v1=t + 4) for t in (0.0, 30.0, 61.0)]
    uv = [[_uv("A", "L1"), _uv("B", "L1")] for _ in ds]
    chon = dung.chon_mac_dinh(ds, uv)
    assert [uv[i][c]["id"] for i, c in enumerate(chon)] == ["A", "B", "A"]
    assert dung.kiem_lap(ds, uv, chon) == []
    # pool cạn (2 clip / 3 khối trong 40s): vòng nới chấp nhận lặp NHƯNG
    # kiem_lap phải réo — đúng thiết kế "không chặn build, chỉ cảnh báo"
    ds2 = [Khoi(v0=t, v1=t + 4) for t in (0.0, 20.0, 40.0)]
    chon2 = dung.chon_mac_dinh(ds2, [uv[0]] * 3)
    assert dung.kiem_lap(ds2, [uv[0]] * 3, chon2) != []


def test_chon_mac_dinh_cam_3_khoi_L3_lien():
    ds = [Khoi(v0=i * 5.0, v1=i * 5.0 + 3) for i in range(4)]
    uv = [[_uv(f"K{i}", "L3"), _uv(f"N{i}", "L1")] for i in range(4)]
    chon = dung.chon_mac_dinh(ds, uv)
    lops = [uv[i][c]["lop"] for i, c in enumerate(chon)]
    for i in range(len(lops) - 2):
        assert not (lops[i] == lops[i + 1] == lops[i + 2] == "L3")


# ------------------------------------------------------- runner + API
@pytest.fixture()
def du_an(tmp_path):
    import math
    import struct
    import wave

    d = tmp_path / "proj"
    (d / "media").mkdir(parents=True)
    fr = bytearray()
    for dai, keu in [(0.3, False), (2.0, True), (1.5, False), (2.0, True), (0.5, False)]:
        n = int(dai * 22050)
        for i in range(n):
            v = int(9000 * math.sin(2 * math.pi * 440 * i / 22050)) if keu else 0
            fr += struct.pack("<h", v)
    with wave.open(str(d / "media" / "voice_master.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(bytes(fr))
    (d / "transcript.json").write_text(json.dumps([
        {"text": "hello", "start": 0.35, "end": 2.25},
        {"text": "world", "start": 3.85, "end": 5.75}]), encoding="utf-8")
    return d


def test_phan_tich_ra_hop_dong(du_an, tmp_path, monkeypatch):
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    from autoedit.offline import runner

    hd = runner.phan_tich(du_an, avd_s=360, mo_dau_tap_s=0, llm=_LLM())
    assert hd["trang_thai"] == "pha1"
    assert hd["dong_kiem"] is True                    # chương mở đầu < AVD
    assert len(hd["khoi"]) == 2
    assert hd["khoi"][0]["tho"] > 0.5                 # khoảng lặng giữa 2 câu
    assert runner.doc(du_an)["phien_ban"] == 1
    # chương sau AVD -> auto
    hd2 = runner.phan_tich(du_an, avd_s=360, mo_dau_tap_s=400, llm=_LLM())
    assert hd2["dong_kiem"] is False


def test_api_offline_luu_voice_bat_bien(du_an, tmp_path, monkeypatch):
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    from fastapi.testclient import TestClient

    from autoedit.offline import runner
    from autoedit.web import server

    runner.phan_tich(du_an, llm=_LLM())
    monkeypatch.setattr(server, "PROJECTS_DIR", du_an.parent)
    tc = TestClient(server.app)
    r = tc.get(f"/api/offline/{du_an.name}")
    assert r.status_code == 200 and len(r.json()["hop_dong"]["khoi"]) == 2
    hd = r.json()["hop_dong"]
    hd["khoi"][0]["tho_them"] = 2.0                   # chỉnh thở: hợp lệ
    assert tc.put(f"/api/offline/{du_an.name}", json=hd).status_code == 200
    hd["khoi"][0]["v1"] = hd["khoi"][0]["v1"] + 3.0   # đổi phần NÓI: cấm
    assert tc.put(f"/api/offline/{du_an.name}", json=hd).status_code == 422


def test_api_voice_va_khoa_so(du_an, tmp_path, monkeypatch):
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    from fastapi.testclient import TestClient

    from autoedit.offline import runner
    from autoedit.web import server

    runner.phan_tich(du_an, llm=_LLM())
    monkeypatch.setattr(server, "PROJECTS_DIR", du_an.parent)
    tc = TestClient(server.app)
    v = tc.get(f"/api/offline/{du_an.name}/voice")
    assert v.status_code == 200 and v.headers["content-type"].startswith("audio/wav")
    r = tc.post(f"/api/offline/{du_an.name}/khoa-so")
    assert r.status_code == 200
    assert runner.doc(du_an)["trang_thai"] == "khoa"


def test_gen_ai_vao_library_va_khay(du_an, tmp_path, monkeypatch):
    """Đợt 4.5 (user duyệt 07/09): ⚡ Gen = nguồn thứ 5, ảnh vào LIBRARY nguồn
    aigen + chèn đầu khay khối; prompt ghép từ 4 lớp + đuôi phong cách cố định."""
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    from autoedit.offline import runner
    from autoedit.offline.gen import gen_cho_khoi, prompt_cho_khoi

    runner.phan_tich(du_an, llm=_LLM())

    class _Ark:
        goi = []

        def gen_anh(self, prompt, dich, size="2560x1440"):
            self.goi.append(prompt)
            Path(dich).write_bytes(b"PNGfake")
            return Path(dich)

    moi = gen_cho_khoi(du_an, 0, so_anh=2, client=_Ark())
    assert len(moi) == 2
    assert all(m["nguon"] == "aigen" for m in moi)
    # prompt mang L1 + đuôi phong cách (không để model tự do phá mood)
    assert "market stall" in _Ark.goi[0] and "documentary still" in _Ark.goi[0]
    # vào Library: tra ra được, id chính tắc aigen:project:khối:hash
    conn = sdb.mo()
    kq = sdb.tim(conn, q="market", nguon="aigen")
    conn.close()
    assert kq and kq[0]["id"].startswith(f"aigen:{du_an.name}:0:")
    # chèn ĐẦU khay khối trong hợp đồng
    hd = runner.doc(du_an)
    assert hd["khoi"][0]["uv"][0]["nguon"] == "aigen"


def test_prompt_cho_khoi_ghep_4_lop():
    from autoedit.offline.gen import prompt_cho_khoi

    p = prompt_cho_khoi({"L1": ["cash in hand"], "neo": True, "mood": "tense"},
                        ["ecuador", "daily life"])
    assert p.startswith("cash in hand")
    assert "Ecuador" in p and "tense" in p and "no watermark" in p


# ------------------------------------------------------- Đợt 5: THAY MÁU
@pytest.fixture
def profile_gia(tmp_path):
    from autoedit.packager.machine import MachineProfile

    root = tmp_path / "com.lveditor.draft"
    root.mkdir(exist_ok=True)
    return MachineProfile(
        donor_name="donor", capcut_root=str(root), capcut_app_version="8.1.1",
        content_overrides={
            "platform": {"os": "mac"}, "last_modified_platform": {"os": "mac"},
            "new_version": "173.0.0", "version": 360000, "draft_type": "video",
            "function_assistant_info": {}, "mixed_track_mode_on": False,
            "smart_ads_info": {}, "uneven_animation_template_info": {},
        },
        meta_template={"draft_name": "donor", "draft_cover": ""},
    )


def _clip_that(dich: Path, dai: float = 8.0):
    import subprocess

    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"testsrc=duration={dai}:size=320x180:rate=30",
                    "-pix_fmt", "yuv420p", str(dich)], check=True, capture_output=True)


def test_thay_mau_chuong_khoa(du_an, tmp_path, monkeypatch, profile_gia):
    """Khóa sổ -> relocate (kho local + dự bị khi chết) -> voice cắt theo khối
    -> draft CapCut có track video + voice; sự kiện len_final ghi sổ."""
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    from autoedit.offline import runner
    from autoedit.offline.thay_mau import thay_mau

    runner.phan_tich(du_an, llm=_LLM())
    hd = runner.doc(du_an)
    # kho local: 1 clip thật + 1 clip CHẾT (path không tồn tại) để kiểm dự bị
    clip_ok = tmp_path / "clip_ok.mp4"
    _clip_that(clip_ok)
    conn = sdb.mo()
    sdb.them_clip(conn, {"id": "kho:t:ok.mp4", "nguon": "kho", "tieu_de": "quito ok",
                         "path_local": str(clip_ok)})
    sdb.them_clip(conn, {"id": "kho:t:chet.mp4", "nguon": "kho", "tieu_de": "chet",
                         "path_local": str(tmp_path / "khong_ton_tai.mp4")})
    conn.commit()
    conn.close()
    uv_chet = {"id": "kho:t:chet.mp4", "nguon": "kho", "tieu_de": "chet", "lop": "L1",
               "diem": 9, "url_anh": "", "url_video": "", "geo": "", "dai_s": 8}
    uv_ok = {"id": "kho:t:ok.mp4", "nguon": "kho", "tieu_de": "quito ok", "lop": "L1",
             "diem": 5, "url_anh": "", "url_video": "", "geo": "", "dai_s": 8}
    for k in hd["khoi"]:
        k["uv"] = [uv_chet, uv_ok]      # chọn mặc định = clip CHẾT -> phải rơi về dự bị
        k["chon"] = 0
    hd["khoi"][0]["tho_them"] = 1.0     # +1s: hình phủ thêm, voice gap im thật
    hd["trang_thai"] = "khoa"
    runner.luu(du_an, hd)

    kq = thay_mau(du_an, profile=profile_gia, log=lambda m: None)
    assert kq["khoi_co_hinh"] == kq["tong_khoi"] == 2
    d = json.loads((Path(kq["draft"]) / "draft_content.json").read_text(encoding="utf-8"))
    tr = {t["name"]: t for t in d["tracks"]}
    assert len(tr["video_l1"]["segments"]) >= 2
    assert len(tr["voice"]["segments"]) == 2
    # +1s: khối 2 bắt đầu sau (nói+thở+1s) của khối 1
    s0, s1 = tr["voice"]["segments"]
    giay = (s1["target_timerange"]["start"] - s0["target_timerange"]["start"]) / 1_000_000
    hd2 = runner.doc(du_an)
    k0 = hd2["khoi"][0]
    assert giay == pytest.approx((k0["v1"] - k0["v0"]) + k0["tho"] + 1.0, abs=0.15)
    # sự kiện len_final ghi cho clip DỰ BỊ (clip thật được dùng)
    conn = sdb.mo()
    sk = conn.execute("SELECT clip_id FROM su_kien WHERE loai='len_final'").fetchall()
    conn.close()
    assert all(r[0] == "kho:t:ok.mp4" for r in sk) and len(sk) == 2


def test_thay_mau_doi_khoa_so(du_an, tmp_path, monkeypatch, profile_gia):
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    from autoedit.offline import runner
    from autoedit.offline.thay_mau import thay_mau

    runner.phan_tich(du_an, llm=_LLM())
    with pytest.raises(RuntimeError, match="KHÓA SỔ"):
        thay_mau(du_an, profile=profile_gia)
