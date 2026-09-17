r"""KIỂM SCRIPT KHỚP VOICE **TRƯỚC KHI CHẠY** (user chốt 17/09).

User báo: *"Mất kịch bản hoặc mất bản dịch"*. Mổ ra: chương lệch script/voice thì
`match_script_to_whisper` phải nội suy gần hết, dồn từ vào một chỗ, các khối còn
lại được 0 từ -> `loi` rỗng -> `dich` rỗng.

ĐO THẬT trên chương hỏng `c3-20260915-101131` (KIM048), 17/09:

    match_ratio 0.0917 · 198/218 từ (91%) là NỘI SUY, dồn hết vào 60–80s
    khối 11 nuốt 198 từ · khối 1–9 được 0 từ -> mất chữ

Tool ĐÃ tự đo và tự ghi cảnh báo vào `transcript.json` — nhưng ghi xong để đấy:
`align/runner.py` bỏ vào `record.warnings`, không ai chuyển sang hợp đồng, panel
Offline cũng chưa hiện `canh_bao` bao giờ.

NGƯỠNG LẤY TỪ SỐ ĐO, không tự đặt — phân bố 119 chương đang có:

    0–19%    3 chương   mất 4–9 khối mỗi chương (22 khối)
    50–59%   1 chương   không mất khối nào
    80–89%   5 chương   nhiều nhất 1 khối
    90–99% 110 chương   nhiều nhất 1–2 khối

Giữa 11% và 56% KHÔNG có chương nào — khoảng trống rộng. Chặn ở 50% bắt đúng 3
chương thảm hoạ, không chặn oan chương nào. (Hằng số cũ `MATCH_RATIO_MIN = 0.95`
nếu đem ra chặn sẽ chặn 44/119 chương = 37%, phần lớn chỉ mất 0–1 khối.)

Kiểm bằng `.srt` có sẵn: không gọi whisper, không gọi LLM, không tốn gì.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SRT = """1
00:00:00,000 --> 00:00:02,000
The first food is broccoli sprouts

2
00:00:02,500 --> 00:00:05,000
they are rich in sulforaphane
"""


def test_khop_hoan_hao_thi_1(tmp_path):
    from autoedit.align.runner import do_khop_srt

    f = tmp_path / "v.srt"
    f.write_text(SRT, encoding="utf-8")
    tl = do_khop_srt("The first food is broccoli sprouts they are rich in sulforaphane", f)
    assert tl == pytest.approx(1.0, abs=0.05)


def test_script_KHAC_HAN_voice_thi_gan_0(tmp_path):
    from autoedit.align.runner import do_khop_srt

    f = tmp_path / "v.srt"
    f.write_text(SRT, encoding="utf-8")
    tl = do_khop_srt("hom nay troi dep chung ta di choi cong vien va an kem", f)
    assert tl < 0.5, f"lệch hẳn mà vẫn báo khớp {tl:.0%}"


def test_srt_hong_thi_MO_CUA_khong_chan_oan(tmp_path):
    """Không đọc được thì trả None -> cổng bỏ qua. Fail-open đúng khuôn các cổng
    khác (ngách, địa danh): sổ hỏng thì mở, đừng chặn người đang làm việc."""
    from autoedit.align.runner import do_khop_srt

    f = tmp_path / "hong.srt"
    f.write_text("khong phai srt gi ca", encoding="utf-8")
    assert do_khop_srt("bat ky", f) is None
    assert do_khop_srt("bat ky", tmp_path / "khong-co.srt") is None
    assert do_khop_srt("", f) is None


def test_NGUONG_lay_tu_so_do():
    from autoedit.align import runner as ar

    assert ar.KHOP_CHAN == 0.50, "ngưỡng chặn phải là 50% (khoảng trống 11%–56%)"
    assert ar.MATCH_RATIO_MIN == 0.95, "ngưỡng CẢNH BÁO cũ giữ nguyên, không đem đi chặn"


# ─────────────────────── cổng ở lượt nộp tập ───────────────────────

def test_cong_CHAN_tap_co_chuong_lech_nang(tmp_path, monkeypatch):
    """Chặn lúc nộp, không để worker chạy 24 phút rồi mới lộ ra mất chữ."""
    from fastapi.testclient import TestClient

    from autoedit.web import server as sv

    monkeypatch.setattr(sv, "_trust_proxy", lambda r: True)
    monkeypatch.setattr(sv, "_trong_nas", lambda p: p)

    class C:
        def __init__(self, ma, path):
            self.ma, self.path = ma, path
            self.thu_tu, self.nhan = 1, ma
            self.co_script = self.co_voice = self.co_srt = True

    d = tmp_path / "C1"
    d.mkdir()
    (d / "script.txt").write_text("hom nay troi dep di choi cong vien an kem", encoding="utf-8")
    (d / "voice.srt").write_text(SRT, encoding="utf-8")
    monkeypatch.setattr("autoedit.web.chapters.doc_chuong",
                        lambda f: ([C("C1", d)], []))

    cl = TestClient(sv.app)
    r = cl.post("/api/jobs", json={"folder": str(tmp_path), "niche": "N-SENIOR-HEALTH"},
                headers={"X-Remote-User": "haint", "X-Forwarded-Host": "crm.outliery",
                         "X-Remote-Level": "3", "X-Remote-Role": "manager"})
    assert r.status_code == 422, r.text
    assert "lệch" in r.text.lower() or "khớp" in r.text.lower(), r.text
    assert "C1" in r.text, r.text


def test_cong_CHO_QUA_khi_khop_du(tmp_path, monkeypatch):
    """Khớp tốt thì cổng phải im — không được đẻ thêm rào cho việc đang chạy."""
    from autoedit.align.runner import do_khop_srt

    f = tmp_path / "v.srt"
    f.write_text(SRT, encoding="utf-8")
    tl = do_khop_srt("The first food is broccoli sprouts they are rich in sulforaphane", f)
    from autoedit.align import runner as ar

    assert tl >= ar.KHOP_CHAN


def test_KHONG_co_srt_thi_bo_qua(tmp_path, monkeypatch):
    """Chương không có .srt -> phải dùng whisper mới đo được, mà whisper tốn thời
    gian thật. Cổng bỏ qua chương đó chứ không chặn."""
    from autoedit.web.server import _khop_chuong_kem

    class C:
        def __init__(self, path):
            self.ma, self.path = "C2", path
            self.co_srt = False

    d = tmp_path / "C2"
    d.mkdir()
    (d / "script.txt").write_text("gi cung duoc", encoding="utf-8")
    assert _khop_chuong_kem([C(d)]) == []


# ──────────── 50–95%: cho chạy nhưng PHẢI nói ra (user chốt 17/09) ────────────

def test_hop_dong_GHI_canh_bao_khi_co_khoi_khong_nhan_duoc_loi():
    """Không đoán theo tỉ lệ — đếm THIỆT HẠI THẬT: khối nào không có lời."""
    from autoedit.offline.runner import canh_bao_mat_loi

    khoi = [{"loi": "co chu"}, {"loi": ""}, {"loi": "  "}, {"loi": "co"}]
    cb = canh_bao_mat_loi(khoi)
    assert cb and "2/4" in cb[0], cb
    assert "lời" in cb[0].lower()


def test_du_loi_thi_KHONG_canh_bao():
    from autoedit.offline.runner import canh_bao_mat_loi

    assert canh_bao_mat_loi([{"loi": "a"}, {"loi": "b"}]) == []


def test_PANEL_hien_canh_bao():
    """Khoảng trống có từ 12/09: hợp đồng ghi `canh_bao` mà panel Offline không
    hiện ở đâu cả — cảnh báo nằm trong log job thì người dựng không bao giờ thấy."""
    from pathlib import Path

    h = (Path(__file__).resolve().parents[1] / "autoedit" / "web" / "static"
         / "index.html").read_text(encoding="utf-8")
    assert 'id="of-canh-bao"' in h, "panel chưa có chỗ hiện cảnh báo"
    assert "canh_bao" in h, "JS không đọc canh_bao của hợp đồng"
