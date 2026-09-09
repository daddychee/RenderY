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


# ------------------------------------------------- dây chuyền Auto đầu-cuối

def _may_chu_auto(tmp_path, monkeypatch, khay_day: bool):
    """Máy chủ + 1 chương, khay đầy hoặc rỗng, sẵn sàng bấm Phân tích."""
    from fastapi.testclient import TestClient

    from autoedit.offline import dung
    from autoedit.sotra import db as sdb
    from autoedit.web import server

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    mot = [{"id": "ref:x", "nguon": "ref", "tieu_de": "t", "lop": "L1", "diem": 9,
            "url_anh": "", "url_video": "", "geo": "", "dai_s": 30}]
    monkeypatch.setattr(dung, "do_ung_vien",
                        lambda c, k, *a, **kw: [(list(mot) if khay_day else []) for _ in k])
    d = _du_an_gia(tmp_path)
    monkeypatch.setattr(server, "PROJECTS_DIR", d.parent)
    server._offline_dang.clear()          # trạng thái dùng chung giữa các test
    goi: list = []
    monkeypatch.setattr("autoedit.offline.thay_mau.thay_mau",
                        lambda *a, **k: goi.append(a) or {"draft": "x"})
    return TestClient(server.app), d, goi


def test_auto_khay_day_thi_TU_khoa_so_va_dung(tmp_path, monkeypatch):
    """Bấm Phân tích một lần là xong: máy tự khoá sổ rồi chạy Online. Nếu dây
    chuyền này đứt thì `kieu_chay=auto` chỉ còn nghĩa 'khỏi duyệt khay', chứ
    không phải 'tool tự dựng' như tên gọi hứa."""
    tc, d, goi = _may_chu_auto(tmp_path, monkeypatch, khay_day=True)
    r = tc.post(f"/api/offline/{d.name}/phan-tich", json={"kieu_chay": "auto"})
    assert r.status_code == 200, r.text
    hd = _cho_xong(d, lambda h: h.get("trang_thai") == "khoa")
    assert hd["dong_kiem"] is False
    assert hd["trang_thai"] == "khoa", "auto không tự khoá sổ"
    assert goi, "auto không tự chạy Online"


def test_auto_khay_rong_thi_DUNG_va_bao(tmp_path, monkeypatch):
    """Khay rỗng -> KHÔNG được tự khoá sổ. Giao draft rác kèm nhãn '✓ xong'
    tệ hơn không làm gì (rà go-live 06/09)."""
    tc, d, goi = _may_chu_auto(tmp_path, monkeypatch, khay_day=False)
    r = tc.post(f"/api/offline/{d.name}/phan-tich", json={"kieu_chay": "auto"})
    assert r.status_code == 200, r.text
    # Tín hiệu XONG THẬT của luồng nền là trạng thái phiên, không phải nội dung
    # hợp đồng: đợi `canh_bao` khác rỗng là đoán mò — cảnh báo có thể tới trước,
    # sau, hoặc không tới. Test này từng đỏ chập chờn đúng vì đợi nhầm tín hiệu.
    _cho_luong_nen_xong(d.name)
    # Đợi ĐÚNG thứ sắp assert: `phan_tich` ghi hợp đồng NHIỀU LẦN, `_cho_xong`
    # không điều kiện trả về bản đầu tiên đọc được (lại BH10).
    hd = _cho_xong(d, lambda h: h.get("canh_bao"))
    assert hd["trang_thai"] != "khoa", "khay rỗng mà vẫn tự khoá sổ"
    assert not goi, "khay rỗng mà vẫn chạy Online"
    assert any("khay" in c.lower() or "auto" in c.lower() for c in hd["canh_bao"])


def _cho_xong(d, dieu_kien=None, giay: float = 120.0):
    """Endpoint chạy nền — đợi tới ĐIỀU KIỆN CUỐI, không chỉ đợi file hiện ra.

    Đợi file là chưa đủ: `phan_tich` ghi hợp đồng TRƯỚC, dây chuyền auto (khoá
    sổ + Online) chạy SAU. Máy tải nặng thì assert chạy trúng khoảng giữa —
    test đỏ chập chờn (bắt được 08/09 khi chạy suite trên checkout production:
    xanh lúc chạy riêng, đỏ khi chạy cùng 1497 test khác).
    """
    import time

    from autoedit.offline import runner

    het = time.time() + giay
    cuoi = None
    while time.time() < het:
        hd = runner.doc(d)
        if hd is not None:
            cuoi = hd
            if dieu_kien is None or dieu_kien(hd):
                return hd
        time.sleep(0.2)
    raise AssertionError(
        f"quá hạn {giay:.0f}s — hợp đồng: "
        + ("chưa ghi ra" if cuoi is None else f"trang_thai={cuoi.get('trang_thai')!r}"))


def _cho_luong_nen_xong(pid: str, giay: float = 180.0):
    """Đợi luồng phân tích nền rời trạng thái 'dang'. Báo rõ nếu nó BÁO LỖI.

    Hạn 180s chứ không phải 60s: `phan_tich` chạy ffmpeg thật (dò im lặng trên
    voice_master.wav). Rảnh thì cả file test xong trong ~13s, nhưng khi chạy
    cùng 1600 test khác — nhiều test cũng gọi ffmpeg — máy nghẽn và lượt đó mất
    **69s** (đo 09/09: 5 lần xanh rồi 1 lần đỏ đúng ở mốc 60s).

    Đây KHÔNG phải test đợi nhầm tín hiệu, mà hạn đặt quá sát chi phí thật.
    Nới hạn không làm test chậm đi khi máy rảnh — nó thoát ngay khi đủ điều kiện.
    """
    import time

    from autoedit.web import server as _sv

    het = time.time() + giay
    while time.time() < het:
        tt = dict(_sv._offline_dang.get(pid, {}))
        if tt.get("tt") and tt["tt"] != "dang":
            assert tt["tt"] != "loi", f"luồng nền báo lỗi: {tt.get('ghi_chu')}"
            return tt
        time.sleep(0.2)
    raise AssertionError(f"luồng nền chưa xong sau {giay:.0f}s: "
                         f"{dict(_sv._offline_dang.get(pid, {}))}")
