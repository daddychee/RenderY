"""Test backend align đọc .srt (RenderY) — parse thuần logic, không cần model.

Voice của user luôn kèm .srt trích từ kịch bản gốc; đọc thẳng nhanh và đúng chữ hơn
nhận dạng lại. Test ở đây khoá 3 thứ dễ vỡ: định dạng file thật (CRLF, BOM, câu xuống
dòng), cách tìm file, và thông báo lỗi khi thiếu/hỏng.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.align.srt_file import SrtAligner, parse_srt, words_from_captions

SRT_MAU = """1
00:00:00,000 --> 00:00:02,566
let me show you something

2
00:00:02,833 --> 00:00:07,000
in 2025 one of China's biggest oil companies
"""


# ----------------------------- parse_srt ------------------------------------
def test_parse_srt_co_ban():
    caps = parse_srt(SRT_MAU)
    assert len(caps) == 2
    assert caps[0] == (0.0, 2.566, "let me show you something")
    assert caps[1][0] == 2.833
    assert caps[1][2].startswith("in 2025")


def test_parse_srt_chiu_crlf_va_bom():
    """File .srt thật trên Windows có CRLF; xuất từ CapCut hay kèm BOM."""
    caps = parse_srt("﻿" + SRT_MAU.replace("\n", "\r\n"))
    assert len(caps) == 2
    assert caps[0][2] == "let me show you something"


def test_parse_srt_gop_cau_xuong_dong():
    """Câu dài trong .srt xuống nhiều dòng -> gộp lại thành 1 câu."""
    caps = parse_srt("1\n00:00:01,000 --> 00:00:04,000\ndòng một\ndòng hai\n")
    assert caps == [(1.0, 4.0, "dòng một dòng hai")]


def test_parse_srt_chap_nhan_dau_cham():
    """Biến thể dùng '.' thay ',' cho phần mili giây."""
    caps = parse_srt("1\n00:00:01.500 --> 00:00:03.250\nxin chào\n")
    assert caps == [(1.5, 3.25, "xin chào")]


def test_parse_srt_bo_qua_block_hong():
    """Block hỏng bị bỏ, block lành vẫn đọc được — không chết cả file."""
    caps = parse_srt("1\nkhông có dòng thời gian\nlời thoại\n\n"
                     "2\n00:00:05,000 --> 00:00:06,000\ncâu lành\n")
    assert caps == [(5.0, 6.0, "câu lành")]


def test_parse_srt_bo_block_end_khong_lon_hon_start():
    assert parse_srt("1\n00:00:05,000 --> 00:00:05,000\nrỗng thời lượng\n") == []


def test_parse_srt_rong():
    assert parse_srt("") == []


def test_parse_srt_gio_lon_hon_9():
    """Video dài >10 tiếng: giờ có thể là 2 chữ số."""
    caps = parse_srt("1\n10:00:01,000 --> 10:00:02,000\ncâu muộn\n")
    assert caps[0][0] == 36001.0


# -------------------------- words_from_captions -----------------------------
def test_chia_deu_thoi_luong_cau_cho_tung_tu():
    words = words_from_captions([(0.0, 4.0, "một hai ba bốn")])
    assert [w.text for w in words] == ["một", "hai", "ba", "bốn"]
    assert words[0].start == 0.0
    assert words[1].start == pytest.approx(1.0)
    assert words[-1].end == pytest.approx(4.0)


def test_tu_noi_tiep_nhau_khong_ho_khong_de():
    words = words_from_captions([(0.0, 3.0, "a b c")])
    for truoc, sau in zip(words, words[1:]):
        assert truoc.end == pytest.approx(sau.start)


def test_cau_rong_bi_bo_qua():
    assert words_from_captions([(0.0, 1.0, "   ")]) == []


# ------------------------------ SrtAligner ----------------------------------
def test_tim_srt_cung_ten_voi_voice(tmp_path):
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"")
    (tmp_path / "voice.srt").write_text(SRT_MAU, encoding="utf-8")
    assert SrtAligner().find_srt(voice) == tmp_path / "voice.srt"


def test_tim_srt_duy_nhat_trong_thu_muc(tmp_path):
    """Tên khác voice nhưng là .srt duy nhất -> vẫn nhận."""
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"")
    (tmp_path / "chuong 1.srt").write_text(SRT_MAU, encoding="utf-8")
    assert SrtAligner().find_srt(voice) == tmp_path / "chuong 1.srt"


def test_nhieu_srt_khong_cung_ten_thi_khong_doan(tmp_path):
    """2 file .srt mà không cái nào trùng tên voice -> trả None, để user chỉ rõ."""
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"")
    (tmp_path / "a.srt").write_text(SRT_MAU, encoding="utf-8")
    (tmp_path / "b.srt").write_text(SRT_MAU, encoding="utf-8")
    assert SrtAligner().find_srt(voice) is None


def test_transcribe_tra_ve_rawword(tmp_path):
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"")
    (tmp_path / "voice.srt").write_text(SRT_MAU, encoding="utf-8")
    words = SrtAligner().transcribe(voice)
    assert [w.text for w in words[:5]] == ["let", "me", "show", "you", "something"]
    # Mốc CÂU phải giữ nguyên từ .srt (thứ duy nhất cần chính xác) — câu 1 có 5 từ
    assert words[0].start == 0.0
    assert words[4].end == pytest.approx(2.566)     # hết câu 1
    assert words[5].start == pytest.approx(2.833)   # vào câu 2
    assert words[5].text == "in"


def test_thieu_srt_bao_loi_ro_rang(tmp_path):
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"")
    with pytest.raises(FileNotFoundError, match="--backend whisper"):
        SrtAligner().transcribe(voice)


def test_srt_hong_bao_loi_ro_rang(tmp_path):
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"")
    (tmp_path / "voice.srt").write_text("không phải srt", encoding="utf-8")
    with pytest.raises(ValueError, match="SRT"):
        SrtAligner().transcribe(voice)


def test_bay_OptionInfo_khong_lam_no_align(tmp_path):
    """Bẫy OptionInfo: `run()` gọi `align()` trực tiếp thì tham số typer CHƯA được
    giải — `srt` là OptionInfo, `.is_file()` nổ AttributeError. Bắt được khi chạy
    thật qua worker hàng đợi (30/08/2026); cli.py lọc bằng isinstance(str, Path).
    """
    import typer

    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"")
    (tmp_path / "voice.srt").write_text(SRT_MAU, encoding="utf-8")

    srt_raw = typer.Option(None, "--srt")                 # đúng thứ run() truyền xuống
    assert not isinstance(srt_raw, (str, Path))           # ⇒ cli.py phải coi như None
    assert SrtAligner(srt_path=None).find_srt(voice) == tmp_path / "voice.srt"

    with pytest.raises(AttributeError):                   # nếu KHÔNG lọc thì nổ đúng chỗ này
        SrtAligner(srt_path=srt_raw).find_srt(voice)
