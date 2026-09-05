"""Hồ Sơ Kênh (Đợt A) — đo kênh ref → hồ sơ 3 tầng, cache theo kênh.

Không mạng: hàm tải tiêm được (`tai=`); đo nhịp dùng video tổng hợp ffmpeg
(cắt cứng biết trước — đúng khuôn hiệu chuẩn nhip/do.py); nhạc dùng wav
tổng hợp có đoạn to/nhỏ biết trước.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from autoedit.kenh.do_kenh import (DoKenhError, _hook_kieu, do_kenh,
                                   do_nhac_ffmpeg, slug_tu_link)
from autoedit.kenh.hoso import HoSoKenh


# ------------------------------------------------------------ slug
def test_slug_kenh_handle():
    assert slug_tu_link("https://www.youtube.com/@fern-tv") == "fern-tv"
    assert slug_tu_link("https://youtube.com/@JohnnyHarris/videos") == "johnnyharris"


def test_slug_video_le_lowercase_nhat_quan():
    """Lowercase MỌI nhánh (05/09): dropdown UI gửi lại slug làm kenh_ref, lệch
    case là trượt cache (Windows FS vốn không phân biệt hoa thường)."""
    assert slug_tu_link("https://www.youtube.com/watch?v=-Gnrp_caPvo") == "video--gnrp_capvo"
    assert slug_tu_link("https://youtu.be/frr9AdZXrJc") == "video-frr9adzxrjc"
    # slug đã có gửi lại qua dropdown -> ra chính nó (idempotent)
    assert slug_tu_link("video--gnrp_capvo") == "video--gnrp_capvo"
    assert slug_tu_link("fern-tv") == "fern-tv"


def test_slug_link_rac_bao_loi():
    with pytest.raises(DoKenhError):
        slug_tu_link("???")


def test_slug_tu_ten_phong_cach_bo_dau():
    from autoedit.kenh.do_kenh import slug_tu_ten
    assert slug_tu_ten("Fern chậm rãi") == "fern-cham-rai"
    assert slug_tu_ten("Đối thủ #1!") == "doi-thu-1"
    with pytest.raises(DoKenhError):
        slug_tu_ten("???")


# ------------------------------------------------------------ hook kiểu
def test_hook_kieu_theo_ty_le():
    assert _hook_kieu(0.72, 2.1) == "no"      # Fern thật: 0.72/2.1 ≈ 0.34
    assert _hook_kieu(1.8, 2.5) == "leo"
    assert _hook_kieu(2.4, 2.5) == "em"
    assert _hook_kieu(0, 2.5) == ""           # thiếu số -> không đoán


# ------------------------------------------------------------ nhạc ffmpeg
def test_do_nhac_ffmpeg_bat_duoc_doan_to(tmp_path):
    """WAV 24s: 8s nhỏ + 8s TO + 8s nhỏ -> bucket giữa phải mạnh nhất."""
    f = tmp_path / "test.wav"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-filter_complex",
        "[0]volume=0.05[a];[1]volume=1.0[b];[2]volume=0.05[c];[a][b][c]concat=n=3:v=0:a=1",
        str(f)], check=True)
    kq = do_nhac_ffmpeg(f)
    assert len(kq["curve"]) == 12
    assert 0.25 < kq["vi_tri_drop"] < 0.75, f"drop phải ở GIỮA: {kq['vi_tri_drop']}"
    assert kq["do_dong"] > 10, "chênh 0.05 vs 1.0 volume phải ra dải động lớn"


def test_do_nhac_ffmpeg_file_cut_tra_rong(tmp_path):
    f = tmp_path / "hong.wav"
    f.write_bytes(b"khong phai wav")
    kq = do_nhac_ffmpeg(f)
    assert kq["curve"] == []                   # không nổ, trả rỗng để caller bỏ qua


# ------------------------------------------------------------ do_kenh + cache
def _video_cat_cung(dich: Path, ten: str, n_shot: int = 80, shot_s: float = 3.0):
    """Video tổng hợp n_shot cảnh màu khác nhau — điểm cắt biết trước, đủ dài
    (240s+) để qua lọc thời lượng và đo được hook/thân."""
    mau = ["red", "blue", "green", "yellow", "purple", "orange"]
    inputs, filters = [], []
    for i in range(n_shot):
        inputs += ["-f", "lavfi", "-t", str(shot_s),
                   "-i", f"color=c={mau[i % len(mau)]}:s=320x180:r=10"]
        filters.append(f"[{i}]")
    fc = "".join(filters) + f"concat=n={n_shot}:v=1:a=0[v]"
    f = dich / ten
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs
                   + ["-filter_complex", fc, "-map", "[v]", str(f)], check=True)
    return f


@pytest.fixture()
def cache_rieng(tmp_path, monkeypatch):
    """Trỏ cache kênh vào tmp — không đụng data root thật của máy."""
    import autoedit.kenh.hoso as mh
    monkeypatch.setattr(mh, "resolve_data_root", lambda *a, **k: tmp_path)
    return tmp_path


def test_do_kenh_do_that_va_cache(cache_rieng, tmp_path):
    video_dir = tmp_path / "vids"
    video_dir.mkdir()
    _video_cat_cung(video_dir, "v1.mp4")

    goi_tai = []

    def tai_gia(link, dich, so_video=3, log=None):
        goi_tai.append(link)
        import shutil
        ra = []
        for f in video_dir.glob("*.mp4"):
            d = dich / f.name
            shutil.copy2(f, d)
            ra.append(d)
        return ra

    hs = do_kenh("https://www.youtube.com/@test-kenh", tai=tai_gia)
    assert hs.ten == "test-kenh"
    assert hs.so_video_hoi_tu == 1
    # video cắt cứng 3s/shot -> trung vị thân phải quanh 3s (thước là cận dưới)
    assert 2.0 <= hs.than_trung_vi <= 4.5, hs.than_trung_vi
    assert HoSoKenh.doc("test-kenh") is not None    # đã cache

    # lần 2: CACHE HIT — không được gọi tải nữa (luật né chặn IP)
    hs2 = do_kenh("https://www.youtube.com/@test-kenh", tai=tai_gia)
    assert len(goi_tai) == 1, "cache hit vẫn tải lại = vi phạm luật né chặn IP"
    assert hs2.than_trung_vi == hs.than_trung_vi

    # --do-lai (user 05/09): PHÂN TÍCH LẠI từ kho video bền <kenh>/videos/ —
    # không gọi YouTube nữa (né chặn IP, đo lại tức thì, thêm thước mới là có số)
    hs3 = do_kenh("https://www.youtube.com/@test-kenh", do_lai=True, tai=tai_gia)
    assert len(goi_tai) == 1, "đo lại vẫn tải lại = trái yêu cầu user 05/09"
    assert hs3.than_trung_vi == hs.than_trung_vi


def test_do_kenh_khong_video_nao_hoi_tu_bao_ro(cache_rieng, tmp_path):
    def tai_rong(link, dich, so_video=3, log=None):
        f = dich / "hong.mp4"
        f.write_bytes(b"khong phai video")
        return [f]

    with pytest.raises(DoKenhError, match="hội tụ"):
        do_kenh("https://www.youtube.com/@kenh-hong", tai=tai_rong)


# ------------------------------------------------------------ áp vào HoSoNhip
def test_ap_vao_nhip_chi_de_truong_co_so():
    from autoedit.nhip.profile import nap
    hs_nhip = nap("investigate")
    goc_chu_ky = hs_nhip.bung_chu_ky_s
    hk = HoSoKenh(ten="t", than_trung_vi=1.8, than_ty_le_nhanh=0.6,
                  than_ty_le_hold=0.1, hook_trung_vi=0.8, hook_ty_le_nhanh=0.9,
                  hook_kieu="no", bung_chu_ky_s=0.0)     # chu kỳ KHÔNG đo được
    hs_moi, log = hk.ap_vao_nhip(hs_nhip)
    assert hs_moi.than_trung_vi == 1.8
    assert hs_moi.hook_kieu == "no"
    assert hs_moi.bung_chu_ky_s == goc_chu_ky             # 0 = giữ số niche, không đè
    assert hs_nhip.than_trung_vi == 2.5                    # bản gốc frozen giữ nguyên
    assert log and "«t»" in log[0]


# ------------------------------------------------------------ Đợt B: loại cảnh
def _tra_glm(phan_loai):
    return {"choices": [{"message": {"content":
        __import__("json").dumps({"phan_loai": phan_loai})}}]}


def test_cham_loai_canh_ra_ty_trong():
    from autoedit.kenh.loai_canh import cham_loai_canh
    goi = lambda body: _tra_glm(["tu_quay", "tu_quay", "b_roll", "do_hoa"])
    kq = cham_loai_canh([b"jpg1", b"jpg2", b"jpg3", b"jpg4"], goi=goi)
    assert kq == {"tu_quay": 0.5, "b_roll": 0.25, "do_hoa": 0.25, "ai_render": 0.0}


def test_cham_loai_canh_loai_la_bi_bo_qua():
    from autoedit.kenh.loai_canh import cham_loai_canh
    goi = lambda body: _tra_glm(["tu_quay", "bay_ba", "b_roll"])
    kq = cham_loai_canh([b"a", b"b", b"c"], goi=goi)
    assert kq["tu_quay"] == 0.5 and kq["b_roll"] == 0.5   # chỉ đếm loại hợp lệ


def test_cham_loai_canh_glm_chet_tra_rong():
    from autoedit.kenh.loai_canh import cham_loai_canh

    def goi_chet(body):
        raise RuntimeError("gia lap GLM chet")

    assert cham_loai_canh([b"a"], goi=goi_chet) == {}     # fail-open, khong no


def test_do_kenh_kem_loai_canh(cache_rieng, tmp_path):
    """do_kenh với goi_vision stub -> hồ sơ có đủ 3 tầng, cache giữ nguyên tầng 3."""
    video_dir = tmp_path / "vids2"
    video_dir.mkdir()
    _video_cat_cung(video_dir, "v1.mp4")

    def tai_gia(link, dich, so_video=3, log=None):
        import shutil
        ra = []
        for f in video_dir.glob("*.mp4"):
            d = dich / f.name
            shutil.copy2(f, d)
            ra.append(d)
        return ra

    goi = lambda body: _tra_glm(["do_hoa"] * 6 + ["b_roll"] * 2)
    hs = do_kenh("https://www.youtube.com/@kenh-vision", tai=tai_gia, goi_vision=goi)
    assert hs.loai_canh["do_hoa"] == 0.75
    assert hs.loai_canh["b_roll"] == 0.25
    doc_lai = HoSoKenh.doc("kenh-vision")
    assert doc_lai.loai_canh == hs.loai_canh              # tầng 3 vào cache


# ------------------------------------------------------------ mô tả (Framing Insight)
class _LLMGia:
    """Stub GLMDirectorClient.complete — trả schema hợp lệ, ghi lại prompt."""

    def __init__(self, no=False):
        self.no = no
        self.system = self.user = ""

    def complete(self, system, user, model):
        if self.no:
            raise RuntimeError("GLM chết")
        self.system, self.user = system, user
        return model(la_gi="Kênh cắt chậm, giữ khung dài.",
                     ky_thuat=["thân trung vị 3.0s — chậm gấp rưỡi chuẩn"],
                     nhip_do="chậm đều", duong_hinh="đồ hoạ chiếm 75%",
                     am_nhac="phẳng", nang_luong="đều, không sóng",
                     hop_voi="video giải thích", khong_hop="vlog nhanh",
                     mood="trầm", chi_lenh=["giữ 3s", "hold 20%", "ít cắt"]), None


def test_sinh_mo_ta_chi_dua_so_do():
    """LLM chỉ được thấy SỐ ĐO — link/nguồn/mo_ta cũ không vào prompt."""
    from autoedit.kenh.mo_ta import sinh_mo_ta

    hs = HoSoKenh(ten="t", link="https://youtube.com/@t", nguon=["v1"],
                  than_trung_vi=3.0, so_video_hoi_tu=4, mo_ta={"la_gi": "cũ"})
    llm = _LLMGia()
    m = sinh_mo_ta(hs, llm=llm)
    assert m["la_gi"].startswith("Kênh cắt chậm")
    assert len(m["chi_lenh"]) == 3
    assert "than_trung_vi" in llm.user
    for cam in ("youtube.com", "v1", '"la_gi": "cũ"'):
        assert cam not in llm.user, f"{cam} lọt vào prompt"


def test_do_kenh_kem_mo_ta(cache_rieng, tmp_path):
    """do_kenh sinh mô tả sau khi đo — cache round-trip giữ nguyên."""
    video_dir = tmp_path / "vids3"
    video_dir.mkdir()
    _video_cat_cung(video_dir, "v1.mp4")

    def tai_gia(link, dich, so_video=3, log=None):
        import shutil
        ra = []
        for f in video_dir.glob("*.mp4"):
            d = dich / f.name
            shutil.copy2(f, d)
            ra.append(d)
        return ra

    hs = do_kenh("https://www.youtube.com/@kenh-mota", tai=tai_gia,
                 llm_mo_ta=_LLMGia())
    assert hs.mo_ta["nhip_do"] == "chậm đều"
    assert HoSoKenh.doc("kenh-mota").mo_ta == hs.mo_ta


def test_do_kenh_mo_ta_loi_fail_open(cache_rieng, tmp_path):
    """LLM chết -> mô tả trống nhưng hồ sơ SỐ vẫn đo xong + cache đủ."""
    video_dir = tmp_path / "vids4"
    video_dir.mkdir()
    _video_cat_cung(video_dir, "v1.mp4")

    def tai_gia(link, dich, so_video=3, log=None):
        import shutil
        ra = []
        for f in video_dir.glob("*.mp4"):
            d = dich / f.name
            shutil.copy2(f, d)
            ra.append(d)
        return ra

    hs = do_kenh("https://www.youtube.com/@kenh-mota-loi", tai=tai_gia,
                 llm_mo_ta=_LLMGia(no=True))
    assert hs.mo_ta == {}
    assert hs.than_trung_vi > 0
    assert HoSoKenh.doc("kenh-mota-loi") is not None


# ------------------------------------------------------- đồ thị nhịp + frames
def test_resample_cong_theo_vi_tri():
    """Đường cong cửa sổ trượt → 24 bucket theo VỊ TRÍ 0..1 (video dài ngắn
    khác nhau chồng khớp). Bucket lấy cửa sổ gần tâm nhất."""
    from autoedit.kenh.do_kenh import _resample_cong

    cong = [(30.0, 10.0), (60.0, 20.0), (90.0, 30.0)]
    ra = _resample_cong(cong, tong=120.0, n=4)
    # tâm bucket: 15s→(30,10), 45s→(30 hay 60 đều cách 15, min chọn 30), 75s→(60 hoặc 90), 105s→(90,30)
    assert len(ra) == 4
    assert ra[0] == 10.0 and ra[3] == 30.0


def test_do_kenh_luu_frames_va_nhip_curve(cache_rieng, tmp_path):
    """Đo xong phải còn frame minh hoạ trên đĩa (video tạm đã xoá) — user 05/09."""
    from autoedit.kenh.hoso import thu_muc_kenh

    video_dir = tmp_path / "vids5"
    video_dir.mkdir()
    _video_cat_cung(video_dir, "v1.mp4")

    def tai_gia(link, dich, so_video=3, log=None):
        import shutil
        ra = []
        for f in video_dir.glob("*.mp4"):
            d = dich / f.name
            shutil.copy2(f, d)
            ra.append(d)
        return ra

    hs = do_kenh("https://www.youtube.com/@kenh-frame", tai=tai_gia,
                 llm_mo_ta=_LLMGia())
    frames = sorted((thu_muc_kenh("kenh-frame") / "frames").glob("f*.jpg"))
    assert len(frames) == 2                      # 1 video × 2 frame
    assert frames[0].stat().st_size > 100  # JPEG thật (màu phẳng nén rất nhỏ)
    # video test ngắn hơn cửa sổ 60s -> nhip_curve rỗng là HỢP LỆ (không nổ)
    assert isinstance(hs.nhip_curve, list)


# ------------------------------------------------- Framing BỘ-OUTLIER (Đợt 3)
def test_do_kenh_bo_outlier_nhieu_link(cache_rieng, tmp_path):
    """User chốt 06/09: framing không theo KÊNH — bộ VIDEO OUTLIER gom 1 hồ sơ.
    Nhiều link -> tải từng link (video lẻ = 1), đo GỘP; 1 link chết không giết
    cả bộ; hs.link lưu trọn bộ để Đo lại chạy lại đủ."""
    video_dir = tmp_path / "vids_bo"
    video_dir.mkdir()
    _video_cat_cung(video_dir, "a.mp4")
    _video_cat_cung(video_dir, "b.mp4")

    goi = []

    def tai_gia(link, dich, so_video=3, log=None):
        goi.append((link, so_video))
        if "chet" in link:
            from autoedit.kenh.do_kenh import DoKenhError
            raise DoKenhError("403 gia lap")
        import shutil
        ten = "a.mp4" if "aaa" in link else "b.mp4"
        d = dich / ten
        if not d.exists():
            shutil.copy2(video_dir / ten, d)
        return [d]

    links = ["https://youtu.be/aaa111aaa", "https://youtu.be/chet404xx",
             "https://youtu.be/bbb222bbb"]
    hs = do_kenh(links, ten="bo-thu", ten_phong_cach="Bộ outlier thử",
                 tai=tai_gia, llm_mo_ta=None, so_video=6)
    assert len(goi) == 3                              # gọi đủ 3 link
    assert all(sv == 2 for _, sv in goi)              # 6 quota / 3 link
    assert hs.so_video_hoi_tu == 2                    # link chết bị bỏ, bộ vẫn sống
    assert hs.link.count(chr(10)) == 2                # lưu TRỌN 3 link (2 xuống dòng)
    # chuỗi nhiều dòng cũng nhận (đường API textarea)
    hs2 = do_kenh(chr(10).join(links), ten="bo-thu")  # cache hit
    assert hs2.so_video_hoi_tu == 2
