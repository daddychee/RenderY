"""Nguồn footage từ VIDEO CÓ SẴN của user + transcript .srt (02/09).

Nhân sự đặt `Ref 1.mp4` + `Ref 1.srt` thẳng trong thư mục chương; tool khớp câu beat
với câu transcript rồi cắt clip vào timeline. Khớp LỜI-VỚI-LỜI — với kênh faceless
(user chốt) giả định "nói gì thì hình có cái đó" là đúng.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.sourcer.refvideo import (
    MAX_CLIP,
    MIN_CLIP,
    NGUONG,
    RefVideoError,
    Seg,
    _asset_key,
    _do_dai_can,
    _so_cuoi,
    cat_clip,
    chia_segment,
    doc_ref,
    tim_ung_vien,
)

SRT = """1
00:00:00,000 --> 00:00:21,000
Prayer flags snap in the high altitude wind.

2
00:00:21,000 --> 00:00:43,000
An old woman turns her prayer wheel at dawn.

3
00:00:43,000 --> 00:01:05,000
GDP grew six percent last year in the region.
"""


class _Beat:
    """Beat tối thiểu — chỉ các trường refvideo dùng tới."""

    def __init__(self, text, tl_start=0.0, tl_end=4.0):
        self.text = text
        self.timeline_start, self.timeline_end = tl_start, tl_end
        self.start, self.end = tl_start, tl_end


class _MatcherGia:
    """Matcher giả: điểm theo số từ CHUNG giữa hai câu. Không cần model, chạy tức thì."""

    san_sang = True

    def embed(self, texts):  # không dùng — do_tuong_dong bị thay ở dưới
        raise AssertionError("không nên gọi")


def _gia_lap_diem(monkeypatch, bang: dict):
    """bang[(câu beat, câu ref)] -> điểm. Thiếu cặp nào thì 0.5 (dưới ngưỡng)."""
    import numpy as np

    def gia(matcher, trai, phai):
        return np.array([[bang.get((t, p), 0.5) for p in phai] for t in trai],
                        dtype="float32")

    monkeypatch.setattr("autoedit.sourcer.refembed.do_tuong_dong", gia)


def _mk_chuong(tmp_path, *, ten_video="Ref 1.mp4", ten_srt="Ref 1.srt", srt=SRT):
    d = tmp_path / "C1"
    d.mkdir()
    (d / "script.txt").write_text("kịch bản chương", encoding="utf-8")
    (d / "voice.mp3").write_bytes(b"fake")
    if ten_video:
        (d / ten_video).write_bytes(b"fake video")
    if ten_srt:
        (d / ten_srt).write_text(srt, encoding="utf-8")
    return d


# --------------------------- ghép video ↔ transcript -------------------------
def test_ghep_theo_so_cuoi_ten_file(tmp_path):
    """Quy ước ME: 'Ref 1.mp4' ↔ 'Ref 1.srt'. Đã chạy thật nên không bịa quy ước mới."""
    d = _mk_chuong(tmp_path)
    refs, cb = doc_ref(d)
    assert len(refs) == 1 and not cb
    assert refs[0].ten == "Ref 1"


def test_ghep_dung_cap_khi_co_nhieu_ref(tmp_path):
    d = _mk_chuong(tmp_path)
    (d / "Ref 2.mp4").write_bytes(b"fake")
    (d / "Ref 2.srt").write_text(SRT, encoding="utf-8")
    refs, _ = doc_ref(d)
    assert {r.ten for r in refs} == {"Ref 1", "Ref 2"}
    for r in refs:
        assert _so_cuoi(r.video.name) == _so_cuoi(r.srt.name)


def test_mot_video_mot_srt_khong_can_so(tmp_path):
    """Nhân sự đặt 'phong van.mp4' + 'phong van.srt' — không số vẫn ghép được."""
    d = _mk_chuong(tmp_path, ten_video="phong van.mp4", ten_srt="phong van.srt")
    refs, cb = doc_ref(d)
    assert len(refs) == 1 and not cb


def test_thieu_srt_thi_canh_bao_ro_ten_file(tmp_path):
    """Phải bắt ở bước Kiểm tra, không để chạy 20 phút rồi mới biết (bài học 30/08)."""
    d = _mk_chuong(tmp_path, ten_srt=None)
    refs, cb = doc_ref(d)
    assert refs == []
    assert cb and "Ref 1.mp4" in cb[0]


def test_khong_co_video_thi_tra_rong(tmp_path):
    """Chương không có ref -> chạy y như trước, không cảnh báo thừa."""
    d = _mk_chuong(tmp_path, ten_video=None, ten_srt=None)
    assert doc_ref(d) == ([], [])


def test_bo_qua_script_va_voice(tmp_path):
    """script.txt/voice.mp3 của chính chương KHÔNG phải ref."""
    d = _mk_chuong(tmp_path, ten_video=None, ten_srt=None)
    (d / "script.srt").write_text(SRT, encoding="utf-8")
    (d / "voice.mp4").write_bytes(b"fake")
    assert doc_ref(d) == ([], [])


def test_srt_rong_thi_canh_bao(tmp_path):
    d = _mk_chuong(tmp_path, srt="")
    refs, cb = doc_ref(d)
    assert refs == [] and cb


# ------------------------------ chia segment ---------------------------------
def test_cat_tai_dau_cau_khong_tron_chu_de():
    """Đo thật 02/09: gom mù 14 từ ghép '...prayer wheel at dawn GDP grew six...'
    — lẫn cảnh chùa với cảnh kinh tế, cosine khớp sai CẢ HAI."""
    caps = [(0.0, 3.0, "The mountains are covered in snow."),
            (3.0, 6.0, "An old woman turns her prayer wheel."),
            (6.0, 9.0, "GDP grew six percent last year.")]
    segs = chia_segment(caps, Path("x.mp4"), "Ref 1")
    assert len(segs) == 3
    assert "prayer wheel" in segs[1].text and "GDP" not in segs[1].text


def test_giu_dung_moc_thoi_gian():
    caps = [(0.0, 3.0, "The first sentence runs here for a while."),
            (3.0, 7.5, "And the second sentence follows right after it.")]
    segs = chia_segment(caps, Path("x.mp4"), "Ref 1")
    assert len(segs) == 2
    assert segs[0].vao == pytest.approx(0.0)
    assert segs[1].ra == pytest.approx(7.5, abs=0.01)


def test_khong_dau_cau_thi_cat_theo_so_tu():
    """Transcript máy sinh thường không dấu câu -> về đúng cách ME (14 từ)."""
    caps = [(0.0, 12.0, " ".join(f"word{i}" for i in range(30)))]
    segs = chia_segment(caps, Path("x.mp4"), "Ref 1")
    assert len(segs) == 2
    assert len(segs[0].text.split()) == 14


def test_gop_manh_qua_ngan():
    """Mảnh 2 từ không đủ nghĩa để so cosine -> gộp vào đoạn trước."""
    caps = [(0.0, 5.0, "This is a reasonably long first sentence with many words. Ok.")]
    segs = chia_segment(caps, Path("x.mp4"), "Ref 1")
    assert all(len(s.text.split()) >= 2 for s in segs)
    assert "Ok." in segs[-1].text


# ------------------------------ tìm ứng viên ---------------------------------
def _refs_gia(tmp_path):
    return doc_ref(_mk_chuong(tmp_path))[0]


def test_tra_ung_vien_khi_vuot_nguong(tmp_path, monkeypatch):
    refs = _refs_gia(tmp_path)
    cau_ref = refs[0].segments[0].text
    _gia_lap_diem(monkeypatch, {("cờ cầu nguyện bay trong gió", cau_ref): 0.85})
    uv = tim_ung_vien(_Beat("cờ cầu nguyện bay trong gió"), refs, _MatcherGia())
    assert len(uv) == 1
    assert uv[0]["sim"] == pytest.approx(0.85)


def test_duoi_nguong_thi_khong_tra(tmp_path, monkeypatch):
    refs = _refs_gia(tmp_path)
    _gia_lap_diem(monkeypatch, {})       # mọi cặp = 0.5
    assert tim_ung_vien(_Beat("chủ đề hoàn toàn khác"), refs, _MatcherGia()) == []


def test_shape_ung_vien_dung_khuon_nguon_khac(tmp_path, monkeypatch):
    """Phải khớp shape candidate của Pexels/ytref — phễu dùng chung không phân biệt."""
    refs = _refs_gia(tmp_path)
    _gia_lap_diem(monkeypatch, {(t, s.text): 0.9
                                for t in ["x"] for s in refs[0].segments})
    c = tim_ung_vien(_Beat("x"), refs, _MatcherGia())[0]
    for k in ("asset_key", "url", "media_type", "duration", "description",
              "source", "src_in", "sim", "relevance"):
        assert k in c, k
    assert c["source"] == "refvideo"
    assert c["media_type"] == "video"


def test_asset_key_truy_nguoc_duoc():
    """Cùng khuôn ytref: — biết clip cắt từ video nào, giây nào."""
    k = _asset_key("Ref 1", 12.0, 15.4)
    assert k.startswith("refvid:")
    assert "Ref 1" in k and "12.0" in k and "15.4" in k


def test_do_dai_lay_theo_o_beat(tmp_path, monkeypatch):
    """Ô beat neo theo VOICE, không co giãn (user chốt 02/09)."""
    refs = _refs_gia(tmp_path)
    _gia_lap_diem(monkeypatch, {(t, s.text): 0.9
                                for t in ["x"] for s in refs[0].segments})
    c = tim_ung_vien(_Beat("x", 10.0, 13.4), refs, _MatcherGia())[0]
    assert c["duration"] == pytest.approx(3.4)


def test_do_dai_kep_trong_khung_me(tmp_path, monkeypatch):
    """MIN_CLIP=3 / MAX_CLIP=10 của ME — ô 20s không cho clip 20s."""
    refs = _refs_gia(tmp_path)
    _gia_lap_diem(monkeypatch, {(t, s.text): 0.9
                                for t in ["x"] for s in refs[0].segments})
    dai = tim_ung_vien(_Beat("x", 0.0, 20.0), refs, _MatcherGia())[0]
    ngan = tim_ung_vien(_Beat("x", 0.0, 1.0), refs, _MatcherGia())[0]
    assert dai["duration"] == pytest.approx(MAX_CLIP)
    assert ngan["duration"] == pytest.approx(MIN_CLIP)


def test_bo_qua_key_da_dung(tmp_path, monkeypatch):
    """Luật P7: một clip không dùng hai lần trong cùng video."""
    refs = _refs_gia(tmp_path)
    _gia_lap_diem(monkeypatch, {(t, s.text): 0.9
                                for t in ["x"] for s in refs[0].segments})
    dau = tim_ung_vien(_Beat("x"), refs, _MatcherGia())
    lai = tim_ung_vien(_Beat("x"), refs, _MatcherGia(),
                       used_keys={dau[0]["asset_key"]})
    assert dau[0]["asset_key"] not in {c["asset_key"] for c in lai}


def test_sap_theo_diem_giam_dan(tmp_path, monkeypatch):
    refs = _refs_gia(tmp_path)
    segs = refs[0].segments
    _gia_lap_diem(monkeypatch, {("x", segs[0].text): 0.75,
                                ("x", segs[1].text): 0.90,
                                ("x", segs[2].text): 0.82})
    uv = tim_ung_vien(_Beat("x"), refs, _MatcherGia())
    assert [round(c["sim"], 2) for c in uv] == [0.90, 0.82, 0.75]


def test_matcher_chua_san_sang_thi_tat_nguon(tmp_path):
    """Thiếu sentence-transformers -> bỏ nguồn ref, KHÔNG giết stage (fail-open)."""
    class Tat:
        san_sang = False

    refs = _refs_gia(tmp_path)
    assert tim_ung_vien(_Beat("x"), refs, Tat()) == []
    assert tim_ung_vien(_Beat("x"), refs, None) == []


def test_beat_khong_co_chu_thi_bo_qua(tmp_path):
    assert tim_ung_vien(_Beat(""), _refs_gia(tmp_path), _MatcherGia()) == []


def test_nguong_hop_ly():
    """Đo 02/09 (C9, 22 beat): bge-small nén điểm vào dải 0.71-0.84. Ngưỡng phải nằm
    trong dải đó — thấp quá thì nhận rác, cao quá thì loại sạch."""
    assert 0.70 <= NGUONG <= 0.80


# --------------------------------- cắt clip ----------------------------------
def test_cat_clip_bao_loi_ro_khi_thieu_file(tmp_path):
    with pytest.raises(RefVideoError):
        cat_clip(tmp_path / "khong-co.mp4", 0.0, 3.0, tmp_path / "ra.mp4")


def test_do_dai_can_uu_tien_timeline():
    """timeline_start/end là mốc SAU khi cut xử lý ô thở — đúng thứ cần lấp."""
    b = _Beat("x", 10.0, 14.0)
    b.start, b.end = 0.0, 99.0          # mốc voice thô, KHÔNG được dùng
    assert _do_dai_can(b) == pytest.approx(4.0)


# ------------- không lẫn với script/voice của chính chương -------------------
def test_srt_cua_ref_khong_bi_nham_la_transcript_voice(tmp_path):
    """'Ref 1.srt' đi kèm 'Ref 1.mp4' là phụ đề VIDEO THAM CHIẾU. Chỉ có nó trong
    thư mục thì _pick_input lấy nhầm -> align voice bằng phụ đề video khác, lệch
    TOÀN BỘ timeline mà không báo lỗi gì."""
    from autoedit.cli import _pick_input

    d = _mk_chuong(tmp_path)
    p, ly = _pick_input(d, (".srt",), "voice")
    assert p is None and ly == "none"


def test_srt_that_cua_voice_van_lay_duoc(tmp_path):
    """Có cả hai: 'voice.srt' (thật) và 'Ref 1.srt' (của ref) -> phải lấy đúng cái thật."""
    from autoedit.cli import _pick_input

    d = _mk_chuong(tmp_path)
    (d / "voice.srt").write_text(SRT, encoding="utf-8")
    p, ly = _pick_input(d, (".srt",), "voice")
    assert p is not None and p.name == "voice.srt"


def test_video_ref_khong_bi_nham_la_voice(tmp_path):
    """.mp4 không nằm trong danh sách đuôi audio — nhưng khoá lại phòng ai đó thêm."""
    from autoedit.cli import _AUDIO_EXTS

    assert ".mp4" not in _AUDIO_EXTS


def test_khong_cat_qua_cuoi_video(tmp_path, monkeypatch):
    """Video ref là file LIÊN TỤC: cắt từ mốc X lấy được bao lâu là do phần CÒN LẠI
    của video quyết. Segment cuối cách hết video 2s mà ô cần 6s -> clip hụt hình.
    Báo đúng độ dài lấy được để cửa kỹ thuật của phễu loại giúp."""
    refs = _refs_gia(tmp_path)
    seg_cuoi = refs[0].segments[-1]      # bắt đầu ~43s
    refs[0].thoi_luong = seg_cuoi.vao + 4.0    # chỉ còn 4s hình sau mốc đó
    _gia_lap_diem(monkeypatch, {("x", seg_cuoi.text): 0.9})
    c = tim_ung_vien(_Beat("x", 0.0, 10.0), refs, _MatcherGia())[0]
    assert c["duration"] == pytest.approx(4.0)   # kẹp về phần còn lại
    assert c["duration"] < 10.0                  # KHÔNG báo đủ 10s như ô yêu cầu


def test_khong_do_duoc_thoi_luong_thi_khong_kep(tmp_path, monkeypatch):
    """ffprobe hỏng -> thoi_luong = 0 -> coi như không giới hạn (fail-open)."""
    refs = _refs_gia(tmp_path)
    refs[0].thoi_luong = 0.0
    _gia_lap_diem(monkeypatch, {(t, s.text): 0.9
                                for t in ["x"] for s in refs[0].segments})
    c = tim_ung_vien(_Beat("x", 0.0, 6.0), refs, _MatcherGia())[0]
    assert c["duration"] == pytest.approx(6.0)


# ---------------- cắt clip đi qua đường DUY NHẤT của mọi ứng viên -------------
def test_materialize_cat_clip_khong_goi_stock_download(tmp_path, monkeypatch):
    """02/09: nhánh refvideo cắm trong MultiStockClient.download KHÔNG chạy khi chỉ
    có 1 nguồn stock — `stock` là PexelsClient trực tiếp. Kết quả: 8 beat chọn ref,
    cả 8 đều 'Tải hỏng sau 3 lần' vì Pexels đi tải một đường dẫn file local."""
    from autoedit.sourcer import runner

    da_cat, da_tai = [], []

    def gia_cat(video, vao, keo, dich, timeout=300):
        da_cat.append((Path(video).name, vao, keo))
        Path(dich).parent.mkdir(parents=True, exist_ok=True)
        Path(dich).write_bytes(b"clip")
        return Path(dich)

    class StockGia:
        def download(self, c, dest):
            da_tai.append(c["asset_key"])

    monkeypatch.setattr("autoedit.sourcer.refvideo.cat_clip", gia_cat)

    class B:
        beat_id = 3
        visual_concept = "prayer flags"

    cand = {"source": "refvideo", "asset_key": "refvid:Ref 1@t=12.0-15.4",
            "url": str(tmp_path / "Ref 1.mp4"), "src_in": 12.0, "duration": 3.4,
            "media_type": "video"}
    ra = runner._materialize(cand, B(), StockGia(), tmp_path / "assets", tmp_path)

    assert da_cat == [("Ref 1.mp4", 12.0, 3.4)]
    assert da_tai == [], "ứng viên refvideo KHÔNG được đi qua stock.download"
    assert "assets" in ra


def test_ung_vien_stock_van_di_duong_download(tmp_path, monkeypatch):
    """Sửa refvideo không được làm hỏng đường Pexels/Pixabay."""
    from autoedit.sourcer import runner

    da_tai = []

    class StockGia:
        def download(self, c, dest):
            da_tai.append(c["asset_key"])
            Path(dest).parent.mkdir(parents=True, exist_ok=True)
            Path(dest).write_bytes(b"x")

    class B:
        beat_id = 1
        visual_concept = "mountain"

    cand = {"source": "pexels", "asset_key": "pexels:123",
            "url": "https://x/v.mp4", "media_type": "video"}
    runner._materialize(cand, B(), StockGia(), tmp_path / "assets", tmp_path)
    assert da_tai == ["pexels:123"]
