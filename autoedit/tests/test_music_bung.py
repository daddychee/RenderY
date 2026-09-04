"""N2 (04/09): nhạc nhảy đoạn tại mốc BÙNG — bên trong CÙNG bài đang phát.

User chốt hướng: KHÔNG đổi bài (rủi ro lệch mood/tone giữa 2 bài đang phát liền
nhau) — chỉ nhảy tới sections.drop của chính track đang chạy trong span đó.

Nguồn mốc bùng = `lap_ke_hoach.bung_beat_ids` NGUYÊN VẸN (đã dùng chung với
SFX S3-HOOK qua vung_nhan) — KHÔNG phải chu kỳ lặp bung_chu_ky_s (phát hiện
04/09: field đó tồn tại trong HoSoNhip nhưng lap_ke_hoach chưa dùng tới, chỉ
đánh dấu 15% MỞ CHƯƠNG + KẾT CHƯƠNG). User chốt: không sửa nhip/ep.py ở đây.

PHẠM VI THẬT (phát hiện 04/09, user chấp nhận): mốc MỞ chương luôn dính đầu
span nhạc (nhạc vừa vào — nhảy đoạn lúc này vô nghĩa, bị luật biên seg_start+20
lọc tự nhiên) — chương THÂN (C1/C2/C3) do đó không đổi gì (vô hại, chỉ không có
tác dụng). Chỉ chương KẾT (E, bung_ket=True) có thêm cụm mốc ở CUỐI mới thật
sự dùng được — test cho hiệu ứng thật đều dùng title="E".
"""

from __future__ import annotations

from autoedit.music.plan import bung_music_spans


class _Beat:
    def __init__(self, bid, ts, te, chapter=1):
        self.beat_id = bid
        self.timeline_start, self.timeline_end = ts, te
        self.start, self.end = ts, te
        self.breathing_after = 0.0
        self.shot_count = 1
        self.chapter = chapter


def _beats_deu(n=20, dai=15.0):
    return [_Beat(i, i * dai, (i + 1) * dai) for i in range(n)]


class _HoSoGia:
    than_trung_vi = 3.0
    than_ty_le_nhanh = 0.30
    than_ty_le_hold = 0.25
    hook_kieu = "leo"
    hook_trung_vi = 2.0
    bung_chu_ky_s = 240.0
    bung_he_so = 2.0
    bung_ket = True


def _span_1_bai(file="a.mp3", seg_start=0.0, seg_end=300.0):
    return [{"chapter_id": 0, "file": file, "start_offset": 0.0,
             "seg_start": seg_start, "seg_end": seg_end, "is_insert": False}]


def _index_co_drop(file="a.mp3", drop_at=40.0):
    return {file: {"file": file, "sections": {"drop": [drop_at, drop_at + 8.0]}}}


def test_hook_khong_qua_day():
    """Chương H không có mốc bùng qua N2 — S3-HOOK đã lo trọn hook, tránh chồng lấn."""
    spans = _span_1_bai()
    ra, log = bung_music_spans(spans, _beats_deu(), _HoSoGia(), "H", _index_co_drop())
    assert ra == spans and log == []


def test_chuong_than_khong_co_moc_dung_duoc():
    """C1/C2/C3: mốc bùng chỉ ở MỞ chương (đầu span) — luật biên lọc hết, giữ nguyên
    spans. Vô hại (đúng như user chấp nhận), không phải bug."""
    spans = _span_1_bai(seg_end=300.0)
    ra, log = bung_music_spans(spans, _beats_deu(20, dai=15.0), _HoSoGia(), "C3",
                               _index_co_drop())
    assert ra == spans and log == []


def test_chuong_ket_co_moc_o_cuoi_chen_them_1_span():
    """Chương E (bung_ket=True): cụm mốc cuối chương lọt qua biên -> chẻ span."""
    spans = _span_1_bai(seg_end=300.0)
    ra, log = bung_music_spans(spans, _beats_deu(20, dai=15.0), _HoSoGia(), "E",
                               _index_co_drop())
    assert len(ra) == 2, "phải chẻ thành 2 span tại mốc bùng cuối chương"
    assert ra[0]["seg_start"] == 0.0
    assert ra[1]["seg_end"] == 300.0
    assert ra[0]["seg_end"] == ra[1]["seg_start"], "liền mạch, không hở/không đè"
    assert log and "bùng" in log[0]


def test_nhay_dung_toi_drop_cua_chinh_bai():
    spans = _span_1_bai(file="song.mp3")
    ra, _ = bung_music_spans(spans, _beats_deu(20, dai=15.0), _HoSoGia(), "E",
                             _index_co_drop(file="song.mp3", drop_at=55.0))
    span_sau = ra[1]
    assert span_sau["file"] == "song.mp3", "KHÔNG đổi bài — vẫn track cũ"
    assert span_sau["start_offset"] == 55.0
    assert span_sau["is_insert"] and span_sau["is_bung"]
    assert not ra[0].get("is_bung")


def test_bai_khong_do_duoc_drop_thi_bo_qua_moc():
    """Track thiếu sections.drop -> KHÔNG nhảy (thà giữ liên tục còn hơn tụt về 0)."""
    spans = _span_1_bai(file="ambient.mp3")
    ra, log = bung_music_spans(spans, _beats_deu(20, dai=15.0), _HoSoGia(), "E",
                               {"ambient.mp3": {"file": "ambient.mp3", "sections": {}}})
    assert ra == spans and log == []


def test_moc_qua_gan_mep_span_bi_bo():
    """Mốc bùng cách mép span < 20s (biên an toàn tránh crossfade chồng) -> bỏ."""
    spans = _span_1_bai(seg_start=0.0, seg_end=30.0)   # ngắn, mọi mốc đều sát mép
    ra, log = bung_music_spans(spans, _beats_deu(2, dai=10.0), _HoSoGia(), "E",
                               _index_co_drop())
    assert ra == spans and log == []


def test_khong_co_beat_bung_thi_giu_nguyen():
    """Chương quá ngắn (không đủ để lap_ke_hoach đánh dấu bùng) -> spans y hệt input."""
    spans = _span_1_bai(seg_end=15.0)
    ra, log = bung_music_spans(spans, _beats_deu(1, dai=15.0), _HoSoGia(), "E",
                               _index_co_drop())
    assert ra == spans and log == []


def test_gom_moc_bung_lien_ke_chi_nhay_1_lan():
    """bung_beat_ids là các CỤM liền kề (mở + kết chương) — mốc trong cùng cụm chỉ
    tạo ĐÚNG 1 lần chẻ tại mốc ĐẦU cụm, không chẻ vụn từng beat."""
    beats = _beats_deu(20, dai=15.0)                    # 300s: cụm mở (0-30) + kết (240-285)
    spans = _span_1_bai(seg_end=300.0)
    ra, log = bung_music_spans(spans, beats, _HoSoGia(), "E", _index_co_drop())
    assert len(log) == 1, f"phải gộp cụm kết thành 1 mốc: {log}"
    assert len(ra) == 2
