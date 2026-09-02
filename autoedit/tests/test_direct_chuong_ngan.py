"""Đoạn NGẮN (hook/end) chỉ nên là MỘT chương.

30/08: hook 34 giây bị outline cắt thành 3 chương -> 6 lượt gọi LLM cho cùng một ý,
và chính validator kêu "tempo phẳng giữa chương: các chương cùng một nhịp". Chia
chương là logic của video 20 phút, áp lên 34 giây thì vừa tốn vừa dở.
"""

from __future__ import annotations

from autoedit.director.runner import NGUONG_MOT_CHUONG_GIAY, _gop_mot_chuong
from autoedit.director.schema import ChapterPlan, Outline


def _ch(cid, lo, hi, title="X"):
    return ChapterPlan(chapter_id=cid, title=title, start_word=lo, end_word=hi,
                       mood="warm", energy="high", music_hint="ambient",
                       tempo_curve="calm", summary="tóm ý", central_subject="Uzbekistan")


def _outline(chs):
    return Outline(tone="ấm", motifs=["chợ"], video_subject="Uzbekistan", chapters=chs)


def test_gop_ba_chuong_ve_mot():
    o = _gop_mot_chuong(_outline([_ch(0, 0, 18, "Hook"), _ch(1, 19, 41), _ch(2, 42, 68)]), [])
    assert len(o.chapters) == 1
    c = o.chapters[0]
    assert (c.start_word, c.end_word) == (0, 68)     # phủ trọn, không hụt từ nào
    assert c.title == "Hook"


def test_giu_nguyen_tone_va_motif():
    """Pass 1 vẫn cần thiết: nó cho tone/motif/chủ thể toàn cục cho pass 2."""
    goc = _outline([_ch(0, 0, 10), _ch(1, 11, 20)])
    o = _gop_mot_chuong(goc, [])
    assert o.tone == goc.tone and o.motifs == goc.motifs
    assert o.video_subject == goc.video_subject


def test_mot_chuong_thi_giu_nguyen():
    goc = _outline([_ch(0, 0, 68)])
    assert _gop_mot_chuong(goc, []).chapters == goc.chapters


def test_khong_doi_outline_goc():
    """model_copy chứ không sửa tại chỗ — outline gốc còn dùng để ghi project.json."""
    goc = _outline([_ch(0, 0, 10), _ch(1, 11, 20)])
    _gop_mot_chuong(goc, [])
    assert len(goc.chapters) == 2


def test_nguong_hop_ly_cho_hook_va_video_that():
    """Hook/End 20-60s phải lọt; video 20 phút (1200s) tuyệt đối KHÔNG lọt."""
    assert 60 < NGUONG_MOT_CHUONG_GIAY < 1200
