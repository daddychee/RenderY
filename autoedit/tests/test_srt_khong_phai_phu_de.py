r""".SRT KHÔNG PHẢI PHỤ ĐỀ — haint báo 18/09: *"các chương của em nó không đổ
khối được, đổ được mỗi hook"*.

MỔ TRÊN DỮ LIỆU THẬT (LI042_Hai, job 31 + 32, 18/09):

    CHƯƠNG 1/6: H    -> không có H.srt -> whisper -> ✓ align xong, 66 từ
    CHƯƠNG 2/6: C2   -> "✓ Thấy C2.srt — align đọc thẳng file này"
                     -> Lỗi align: voice.srt không có block nào đọc được
    C3, C4, C5, E    -> y hệt

`inputs/voice.srt` của C2 dài 2018 byte, mở ra là **chữ kịch bản**:

    FACT 6 — TOUCH THIS AND IT COSTS YOU $3,000
    Off the northern coast, wrapped around the Bay Islands...

Không một dòng thời gian nào. Ai đó lưu kịch bản thành đuôi `.srt`. Đó là lỗi
dữ liệu — NHƯNG tool phải chặn ở lượt nộp chứ không để chết từng chương sau đó,
và cổng "kiểm trước khi chạy" (17/09) đang thủng HAI chỗ:

1. **`do_khop_srt` trả None khi srt không đọc được -> cổng MỞ.** Fail-open đúng
   cho "đo không được", nhưng "có .srt mà không phải phụ đề" là hỏng CHẮC CHẮN:
   align sẽ chết, không phải có thể chết.

2. **Cổng đọc nhầm file với bố cục PHẲNG.** `_khop_chuong_kem` quét
   `c.path.iterdir()` lấy `.srt` ĐẦU TIÊN — mà bố cục phẳng thì `c.path` là cả
   thư mục `RenderY/`, nên nó vớ `ref 1.srt` (phụ đề VIDEO MẪU) và `.txt` đầu
   tiên của chương khác. LI042_Hai có đúng bố cục đó: 6 chương + `ref 1..3.srt`
   nằm chung một thư mục. `_chuong_phang` ĐÃ điền sẵn `c.script`/`c.srt` đúng
   của từng chương, cổng lại không dùng.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SRT_THAT = """1
00:00:00,000 --> 00:00:02,000
The first food is broccoli sprouts

2
00:00:02,500 --> 00:00:05,000
they are rich in sulforaphane
"""

# chính là thứ nằm trong C2.srt của LI042_Hai
SRT_GIA = """FACT 6 — TOUCH THIS AND IT COSTS YOU $3,000

Off the northern coast, wrapped around the Bay Islands and the island of Roatán,
sits a reef so fragile that touching it carries a fine.
"""

SCRIPT = ("The first food is broccoli sprouts they are rich in sulforaphane")


# ───────────────────── nhận diện: file này có phải phụ đề ─────────────────────

def test_srt_that_thi_nhan_la_phu_de(tmp_path):
    from autoedit.align.runner import la_phu_de

    f = tmp_path / "C2.srt"
    f.write_text(SRT_THAT, encoding="utf-8")
    assert la_phu_de(f) is True


def test_kich_ban_doi_duoi_srt_thi_KHONG_phai_phu_de(tmp_path):
    from autoedit.align.runner import la_phu_de

    f = tmp_path / "C2.srt"
    f.write_text(SRT_GIA, encoding="utf-8")
    assert la_phu_de(f) is False


def test_srt_co_BOM_van_la_phu_de(tmp_path):
    """.srt xuất từ Windows/CapCut hay có BOM — `SrtAligner` đọc utf-8-sig, cổng
    phải đọc y như vậy, không thì chặn oan đúng file lành."""
    from autoedit.align.runner import la_phu_de

    f = tmp_path / "C2.srt"
    f.write_bytes(b"\xef\xbb\xbf" + SRT_THAT.encode("utf-8"))
    assert la_phu_de(f) is True


def test_file_khong_ton_tai_hoac_rong(tmp_path):
    from autoedit.align.runner import la_phu_de

    assert la_phu_de(tmp_path / "khong-co.srt") is False
    f = tmp_path / "rong.srt"
    f.write_text("", encoding="utf-8")
    assert la_phu_de(f) is False


# ───────────────── cổng lúc nộp tập: chặn + gọi ĐÚNG TÊN FILE ─────────────────

def _tap_phang(goc: Path, srt: dict[str, str]) -> Path:
    """Bố cục PHẲNG y như LI042_Hai: H/C2/C3/E + video ref dùng chung."""
    d = goc / "LI042_Hai" / "RenderY"
    d.mkdir(parents=True)
    for ma in ("H", "C2", "C3", "E"):
        (d / f"{ma}.txt").write_text(SCRIPT, encoding="utf-8")
        (d / f"{ma}.mp3").write_bytes(b"\0" * 2048)
        if ma in srt:
            (d / f"{ma}.srt").write_text(srt[ma], encoding="utf-8")
    # video mẫu của TẬP + phụ đề của nó — KHÔNG phải phụ đề voice
    (d / "ref 1.mp4").write_bytes(b"\0" * 4096)
    (d / "ref 1.srt").write_text(SRT_THAT, encoding="utf-8")
    return d.parent


@pytest.fixture
def may_chu(monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.web import server as sv

    monkeypatch.setattr(sv, "_trust_proxy", lambda r: True)
    monkeypatch.setattr(sv, "_trong_nas", lambda p: p)
    return TestClient(sv.app)


def _nop(tc, folder: Path):
    return tc.post("/api/jobs", json={"folder": str(folder), "niche": "N-SENIOR-HEALTH"},
                   headers={"X-Remote-User": "haint", "X-Forwarded-Host": "crm.outliery",
                            "X-Remote-Level": "3", "X-Remote-Role": "manager"})


def test_cong_CHAN_va_goi_dung_ten_file_srt_hong(may_chu, tmp_path):
    """Điều haint cần thấy NGAY lúc nộp, thay vì 5 chương chết lần lượt."""
    tap = _tap_phang(tmp_path, {"C2": SRT_GIA, "C3": SRT_GIA})
    r = _nop(may_chu, tap)
    assert r.status_code == 422, r.text
    assert "C2.srt" in r.text and "C3.srt" in r.text, r.text
    assert "phụ đề" in r.text.lower(), r.text
    # H không có .srt -> không được réo tên
    assert "H.srt" not in r.text, r.text


def test_cong_KHONG_CHAN_khi_srt_that(may_chu, tmp_path):
    tap = _tap_phang(tmp_path, {"C2": SRT_THAT})
    r = _nop(may_chu, tap)
    assert r.status_code != 422, r.text


def test_cong_KHONG_CHAN_khi_khong_chuong_nao_co_srt(may_chu, tmp_path):
    """Đúng ca của H: không có .srt thì whisper lo, không phải lỗi."""
    tap = _tap_phang(tmp_path, {})
    r = _nop(may_chu, tap)
    assert r.status_code != 422, r.text


def test_cong_KHONG_doc_nham_phu_de_VIDEO_REF(may_chu, tmp_path):
    """Bố cục phẳng: `ref 1.srt` nằm chung thư mục với 6 chương. Cổng vớ nó là
    vừa chặn oan vừa bỏ lọt — đo ratio của chương này bằng phụ đề phim khác."""
    from autoedit.web import server as sv
    from autoedit.web.chapters import doc_chuong

    tap = _tap_phang(tmp_path, {})           # KHÔNG chương nào có .srt
    chuong, loi = doc_chuong(tap)
    assert not loi, loi
    assert sv._srt_khong_phai_phu_de(chuong) == [], "vớ nhầm ref 1.srt"
    assert sv._khop_chuong_kem(chuong) == [], "đo khớp bằng phụ đề video ref"


def test_cong_KHOP_doc_dung_file_cua_TUNG_chuong(tmp_path):
    """Bố cục phẳng (LI042_Hai): 6 chương, mỗi chương một cặp .txt/.srt riêng,
    nằm CHUNG một thư mục. Quét thư mục rồi lấy 'file .srt đầu tiên' nghĩa là
    mọi chương đều bị đo bằng phụ đề của C2 — chặn oan hàng loạt."""
    from autoedit.web import server as sv
    from autoedit.web.chapters import doc_chuong

    SRT_C3 = """1
00:00:00,000 --> 00:00:03,000
completely different sentence about a bridge

2
00:00:03,500 --> 00:00:06,000
and the river underneath it
"""
    d = tmp_path / "LI999" / "RenderY"
    d.mkdir(parents=True)
    for ma in ("H", "C2", "C3", "E"):
        (d / f"{ma}.mp3").write_bytes(b"\0" * 2048)
        (d / f"{ma}.txt").write_text(SCRIPT, encoding="utf-8")
    # C2 lệch THẬT (script chẳng liên quan phụ đề của chính nó) -> đáng bị chặn.
    # C3 khớp ĐÚNG phụ đề của nó -> không được chặn. Đọc nhầm 'file đầu tiên'
    # thì C3 bị đo bằng cặp của C2 và bị chặn oan theo.
    (d / "C2.txt").write_text("hom nay troi dep chung ta di choi cong vien an kem",
                              encoding="utf-8")
    (d / "C2.srt").write_text(SRT_THAT, encoding="utf-8")
    (d / "C3.txt").write_text("completely different sentence about a bridge "
                              "and the river underneath it", encoding="utf-8")
    (d / "C3.srt").write_text(SRT_C3, encoding="utf-8")
    chuong, loi = doc_chuong(d.parent)
    assert not loi, loi
    assert [m for m, _ in sv._khop_chuong_kem(chuong)] == ["C2"], \
        "đo chương này bằng phụ đề của chương kia"


def test_cong_van_CHAN_chuong_lech_that_bo_cuc_PHANG(tmp_path):
    """Không được sửa lỗ thủng bằng cách tắt luôn cổng: srt THẬT mà script lệch
    hẳn thì vẫn phải chặn (luật 17/09)."""
    from autoedit.web import server as sv
    from autoedit.web.chapters import doc_chuong

    d = tmp_path / "LI998" / "RenderY"
    d.mkdir(parents=True)
    for ma in ("H", "C2", "E"):
        (d / f"{ma}.mp3").write_bytes(b"\0" * 2048)
        (d / f"{ma}.txt").write_text("hom nay troi dep chung ta di choi cong vien",
                                     encoding="utf-8")
    (d / "C2.srt").write_text(SRT_THAT, encoding="utf-8")
    kem = sv._khop_chuong_kem(doc_chuong(d.parent)[0])
    assert [m for m, _ in kem] == ["C2"], kem


def test_bo_cuc_THU_MUC_CON_van_chay_nhu_cu(tmp_path):
    """Kiểu thư mục con (LI104) không được hỏng theo."""
    from autoedit.web import server as sv
    from autoedit.web.chapters import doc_chuong

    goc = tmp_path / "LI997" / "RenderY"
    for ma in ("H", "C1", "E"):
        d = goc / ma
        d.mkdir(parents=True)
        (d / "script.txt").write_text(SCRIPT, encoding="utf-8")
        (d / "voice.mp3").write_bytes(b"\0" * 2048)
    (goc / "C1" / "voice.srt").write_text(SRT_GIA, encoding="utf-8")
    chuong, loi = doc_chuong(goc.parent)
    assert not loi, loi
    assert [m for m, _f in sv._srt_khong_phai_phu_de(chuong)] == ["C1"]


def test_thu_muc_con_bo_qua_phu_de_video_ref(tmp_path):
    """Ref RIÊNG của chương cũng nằm trong thư mục chương (khuôn refvideo)."""
    from autoedit.web import server as sv
    from autoedit.web.chapters import doc_chuong

    goc = tmp_path / "LI996" / "RenderY"
    for ma in ("H", "C1", "E"):
        d = goc / ma
        d.mkdir(parents=True)
        (d / "script.txt").write_text(SCRIPT, encoding="utf-8")
        (d / "voice.mp3").write_bytes(b"\0" * 2048)
    (goc / "C1" / "Ref 1.mp4").write_bytes(b"\0" * 4096)
    (goc / "C1" / "Ref 1.srt").write_text(SRT_GIA, encoding="utf-8")
    chuong, _ = doc_chuong(goc.parent)
    assert sv._srt_khong_phai_phu_de(chuong) == [], "chặn oan vì phụ đề video ref"


# ───────────── lỗi align phải gọi tên file NGƯỜI TA ĐẶT, không phải voice.srt ─────────────

def test_loi_align_goi_ten_file_GOC_tren_NAS(tmp_path):
    """Người dựng đọc "voice.srt không có block nào" thì không biết sửa file nào
    — trên NAS đâu có file tên đó. Phải nói `C2.srt`."""
    from autoedit.align.srt_file import SrtAligner

    d = tmp_path / "proj" / "inputs"
    d.mkdir(parents=True)
    (d / "voice.mp3").write_bytes(b"\0" * 16)
    (d / "voice.srt").write_text(SRT_GIA, encoding="utf-8")
    (tmp_path / "proj" / "project.json").write_text(json.dumps(
        {"inputs": {"original_script_path": r"F:\NAS\LI042_Hai\RenderY\C2.txt",
                    "original_srt_path": r"F:\NAS\LI042_Hai\RenderY\C2.srt"}}),
        encoding="utf-8")
    with pytest.raises(ValueError) as e:
        SrtAligner().transcribe(d / "voice.mp3")
    assert "C2.srt" in str(e.value), str(e.value)
