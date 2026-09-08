"""Đợt 3 (08/09) — CỔNG AUTO: khay mỏng thì Auto phải TỪ CHỐI, không dựng bừa.

Đo thật 07-08/09 (SEQUENCE PH8/PH9): Auto chạy 100% khối chỉ vì hai tập C1/H có
ref (648 và 252 ứng viên, 100% ref). Tập chưa có ref thì khay RỖNG TUYỆT ĐỐI —
0/36 và 0/14 khối. Auto khi đó không "dựng kém", nó dựng ra timeline không có
gì khớp ngữ nghĩa.

QĐ7 (user chốt 08/09): ngưỡng **60%** khối có ứng viên. Dưới ngưỡng -> chuyển
chương sang Đồng kiểm để người dựng đắp, kèm cảnh báo nói rõ vì sao.
"""

from __future__ import annotations

from autoedit.offline.runner import NGUONG_AUTO, du_khay_cho_auto


def test_nguong_dung_60_phan_tram():
    """Con số là QUYẾT ĐỊNH của user, không phải hằng số tiện tay đặt."""
    assert NGUONG_AUTO == 0.6


def test_khay_day_thi_auto_chay():
    assert du_khay_cho_auto([[{"id": "a"}]] * 10) is True


def test_khay_rong_hoan_toan_thi_tu_choi():
    """Tập chưa có ref, stock lệch geo bị loại sạch — đúng cảnh đo được ở PH8."""
    assert du_khay_cho_auto([[] for _ in range(14)]) is False


def test_dung_nguong_60_thi_van_chay():
    """6/10 = 60% — ngưỡng là 'từ 60% trở lên', không phải 'trên 60%'."""
    assert du_khay_cho_auto([[{"id": "a"}]] * 6 + [[]] * 4) is True


def test_duoi_nguong_thi_tu_choi():
    assert du_khay_cho_auto([[{"id": "a"}]] * 5 + [[]] * 5) is False


def test_chuong_khong_co_khoi_nao_thi_tu_choi():
    """Chia khối hỏng -> 0 khối. Chia 0/0 mà ra True là Auto chạy trên hư không."""
    assert du_khay_cho_auto([]) is False


def test_auto_khay_mong_bi_chuyen_sang_dong_kiem(tmp_path, monkeypatch):
    """Chương khai kieu_chay=auto nhưng khay mỏng -> hợp đồng ra `dong_kiem`
    True kèm cảnh báo, chứ không âm thầm dựng tiếp (BH5)."""
    import json

    from autoedit.offline import dung, runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setattr(dung, "do_ung_vien",
                        lambda *a, **k: [[] for _ in range(4)])   # khay rỗng
    d = _du_an_gia(tmp_path)
    hd = runner.phan_tich(d, kieu_chay="auto", llm=_LLM4())
    assert hd["dong_kiem"] is True
    assert any("khay" in c.lower() for c in hd["canh_bao"]), hd["canh_bao"]


def test_auto_khay_day_van_tu_chay(tmp_path, monkeypatch):
    from autoedit.offline import dung, runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setattr(dung, "do_ung_vien", lambda *a, **k: [
        [{"id": "ref:x", "nguon": "ref", "tieu_de": "t", "lop": "L1", "diem": 9,
          "url_anh": "", "url_video": "", "geo": "", "dai_s": 30}] for _ in range(4)])
    d = _du_an_gia(tmp_path)
    hd = runner.phan_tich(d, kieu_chay="auto", llm=_LLM4())
    assert hd["dong_kiem"] is False


# ------------------------------------------------------------------ đồ giả
class _LLM4:
    def chia_khoi(self, *a, **k):
        return None

    def __call__(self, *a, **k):
        return None


def _du_an_gia(tmp_path):
    """Dự án tối thiểu: 1 voice + transcript 4 câu."""
    import json
    import subprocess

    d = tmp_path / "projects" / "h-auto"
    (d / "media").mkdir(parents=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "sine=frequency=200:duration=8", "-ar", "16000",
                    str(d / "media" / "voice_master.wav")], check=True)
    (d / "transcript.json").write_text(json.dumps({"words": [
        {"w": f"tu{i}", "t0": i * 0.5, "t1": i * 0.5 + 0.4} for i in range(16)]}),
        encoding="utf-8")
    return d


def test_chuyen_sang_dong_kiem_thi_do_LAI_khay_co_envato(tmp_path, monkeypatch):
    """Chương Auto cố tình BỎ envato (không đốt hạn mức license). Khi cổng đẩy
    nó sang Đồng kiểm thì người dựng phải nhận khay ĐẦY ĐỦ — giữ khay Auto là
    bắt người chọn trong đúng cái rổ vừa bị kết luận là quá mỏng."""
    from autoedit.offline import dung, runner
    from autoedit.sotra import db as sdb

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    goi: list = []

    def _gia(*a, **k):
        goi.append(k.get("bo_nguon"))
        if k.get("bo_nguon") == ("envato",):
            return [[] for _ in range(4)]            # Auto: khay rỗng
        return [[{"id": "envato:x", "nguon": "envato", "tieu_de": "t", "lop": "L1",
                  "diem": 9, "url_anh": "", "url_video": "", "geo": "",
                  "dai_s": 30}] for _ in range(4)]   # Đồng kiểm: có hàng

    monkeypatch.setattr(dung, "do_ung_vien", _gia)
    hd = runner.phan_tich(_du_an_gia(tmp_path), kieu_chay="auto", llm=_LLM4())

    assert hd["dong_kiem"] is True
    assert goi == [("envato",), ()], f"chưa dò lại khay khi đổi diện: {goi}"
    assert hd["khoi"][0]["uv"], "người dựng nhận khay rỗng của Auto"
