r"""Miếng không lấy được nguồn nào -> draft HỞ -> CapCut dồn timeline (lệch tiếng).

ĐO THẬT 10/09 trên production, chương `c8-20260831-064152`:
  - `thay_mau.json` ghi: *"miếng 12: KHÔNG lấy được nguồn nào — timeline hở"*
  - draft đã sinh `OFF_c8-20260831-064152/draft_content.json`:
    **33 segment, hở 5.170s tại giây 67.020**.

Vì sao hở là hỏng CẢ chương chứ không chỉ một miếng: main track CapCut là
**track NAM CHÂM**. Draft có lỗ thì lúc MỞ, CapCut tự dồn mọi segment phía sau
về trước 5.17s và ghi đè `draft_content.json` — voice đứng yên (track khác),
nên toàn bộ hình nửa sau chương lệch tiếng tích luỹ. Đây đúng bug DS3-084 mà
đường Auto đã chữa từ lâu bằng `_fill_holes_with_slug`; đường Offline chưa gọi.

Đường Offline (`thay_mau.dung_draft`) hiện chỉ `if f is None: continue`
(thay_mau.py:361) — bỏ hẳn miếng, để lỗ.

USER CHỐT 09/09 (việc 1a): ô giữ chỗ phải **kèm LINK** và câu
*"Tool đang cập nhật, vui lòng tải bằng tay theo link"* — người dựng nhìn ảnh
là biết tải ở đâu, không phải mò lại sổ.

Test này kiểm KẾT QUẢ THẬT: dựng draft bằng chính `dung_draft`, đọc
`draft_content.json` ra đo mép segment — không kiểm chuỗi trong mã nguồn (bài
học BH9: test kiểm chuỗi là test báo xanh vô nghĩa).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from autoedit.packager.machine import MachineProfile, register_machine


def _video(f: Path, giay: float) -> Path:
    f.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"testsrc=duration={giay}:size=320x180:rate=30",
         "-pix_fmt", "yuv420p", str(f)], check=True)
    return f


@pytest.fixture
def profile(tmp_path) -> MachineProfile:
    """Donor giả — đủ trường để `package_draft` chạy (như test_packager)."""
    root = tmp_path / "com.lveditor.draft"
    donor = root / "0428"
    donor.mkdir(parents=True)
    (donor / "draft_info.json").write_text(json.dumps({
        "platform": {"os": "windows", "app_version": "9.1.0", "device_id": "abc"},
        "last_modified_platform": {"os": "windows", "app_version": "9.1.0"},
        "new_version": "173.0.0", "version": 360000, "draft_type": "video",
        "function_assistant_info": {}, "mixed_track_mode_on": False,
        "smart_ads_info": {}, "uneven_animation_template_info": {},
        "duration": 1000000, "materials": {"videos": [], "audios": []}, "tracks": [],
    }))
    (donor / "draft_meta_info.json").write_text(json.dumps({
        "draft_fold_path": str(donor), "draft_root_path": str(root),
        "draft_name": "0428", "draft_id": "OLD", "draft_cover": "draft_cover.jpg",
        "tm_draft_create": 1, "tm_draft_modified": 1, "tm_duration": 1000000,
        "cloud_draft_sync": False,
    }))
    (donor / "draft_cover.jpg").write_bytes(b"fake-jpg")
    return register_machine(donor, profile_path=tmp_path / "machine.json")


@pytest.fixture
def hop_dong() -> dict:
    """3 miếng liền nhau, mỗi miếng 2s — miếng GIỮA sẽ không có file."""
    khoi = [{"v0": 0.0, "v1": 2.0, "tho": 0.0},
            {"v0": 2.0, "v1": 4.0, "tho": 0.0},
            {"v0": 4.0, "v1": 6.0, "tho": 0.0}]
    return {"offset": 0.0, "khoi": khoi,
            "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "uv": [], "chon": -1},
                     {"t0": 2.0, "dur": 2.0, "khoi_goc": 1, "uv": [], "chon": -1},
                     {"t0": 4.0, "dur": 2.0, "khoi_goc": 2, "uv": [], "chon": -1}]}


def _dung(tmp_path, profile, hd, video: dict, ten: str) -> dict:
    from autoedit.offline import thay_mau as tm

    d = tm.dung_draft(tmp_path / "proj", hd, video, {}, ten, profile,
                      lambda m: None)
    return json.loads((Path(d) / "draft_content.json").read_text(encoding="utf-8"))


def _video_segs(noi_dung: dict) -> list[tuple[float, float]]:
    for t in noi_dung["tracks"]:
        if t["type"] != "video":
            continue
        return sorted(((s["target_timerange"]["start"] / 1e6,
                        s["target_timerange"]["duration"] / 1e6)
                       for s in t["segments"]), key=lambda x: x[0])
    return []


def _lo_ho(segs) -> list[tuple[float, float]]:
    """Khoảng hở > 20ms giữa các segment (20ms = sai số làm tròn microsecond)."""
    ra, truoc = [], None
    for st, du in segs:
        if truoc is not None and st - truoc > 0.02:
            ra.append((truoc, st - truoc))
        truoc = st + du
    return ra


def test_mieng_thieu_nguon_KHONG_de_ho_timeline(tmp_path, profile, hop_dong):
    """Ca c8 thật: miếng giữa không có file -> draft phải KHÔNG hở."""
    v = {0: _video(tmp_path / "a.mp4", 3), 2: _video(tmp_path / "c.mp4", 3)}
    segs = _video_segs(_dung(tmp_path, profile, hop_dong, v, "THU_HO"))
    ho = _lo_ho(segs)
    assert not ho, (
        f"draft hở {ho} — CapCut track nam châm sẽ dồn segment sau lên, "
        f"lệch tiếng tích luỹ (đúng bug đo trên OFF_c8-20260831-064152)")


def test_cho_lap_dung_cho_dung_do_dai(tmp_path, profile, hop_dong):
    """Ô giữ chỗ phải nằm ĐÚNG chỗ miếng thiếu và ĐÚNG độ dài — lấp lệch cũng là lệch."""
    v = {0: _video(tmp_path / "a.mp4", 3), 2: _video(tmp_path / "c.mp4", 3)}
    segs = _video_segs(_dung(tmp_path, profile, hop_dong, v, "THU_CHO"))
    assert len(segs) == 3, f"phải đủ 3 segment, đang {len(segs)}: {segs}"
    st, du = segs[1]
    assert abs(st - 2.0) < 0.02 and abs(du - 2.0) < 0.02, \
        f"miếng giữa phải ở 2.0s dài 2.0s, đang {st:.3f}s dài {du:.3f}s"


def test_lap_bang_ANH_khong_phai_video_that(tmp_path, profile, hop_dong):
    """Ô giữ chỗ là ẢNH: không Ken Burns, không tính pacing — và người dựng
    nhìn ra ngay đây là chỗ phải đắp, không tưởng là footage thật."""
    v = {0: _video(tmp_path / "a.mp4", 3), 2: _video(tmp_path / "c.mp4", 3)}
    nd = _dung(tmp_path, profile, hop_dong, v, "THU_ANH")
    duong = {m["id"]: (m.get("path") or "") for m in nd["materials"]["videos"]}
    for t in nd["tracks"]:
        if t["type"] != "video":
            continue
        giua = sorted(t["segments"], key=lambda s: s["target_timerange"]["start"])[1]
        p = duong.get(giua["material_id"], "").lower()
        assert p.endswith((".jpg", ".png")), f"ô giữ chỗ phải là ảnh, đang «{p}»"


def test_slug_MANG_LINK_va_cau_dan_tai_tay(tmp_path):
    """User chốt 09/09: ảnh giữ chỗ phải ghi LINK + câu dặn tải tay.

    Hàm trả cả phần chữ đã vẽ để test đọc được — matplotlib không cho đọc
    ngược chữ ra khỏi ảnh.
    """
    from autoedit.offline.thay_mau import anh_giu_cho

    f, chu = anh_giu_cho(tmp_path, "https://elements.envato.com/x-ABC123",
                         "Rome ruins at dawn")
    assert Path(f).is_file() and Path(f).stat().st_size > 5_000, "ảnh rỗng"
    assert "https://elements.envato.com/x-ABC123" in chu, f"thiếu link: {chu}"
    assert "tải bằng tay" in chu.lower(), f"thiếu câu dặn tải tay: {chu}"


def test_slug_khong_link_van_ra_anh(tmp_path):
    """Miếng khay RỖNG (ca c8 thật) thì không có link nào — vẫn phải ra ảnh."""
    from autoedit.offline.thay_mau import anh_giu_cho

    f, chu = anh_giu_cho(tmp_path, "", "")
    assert Path(f).is_file() and Path(f).stat().st_size > 5_000, "ảnh rỗng"
    assert "ĐẮP FOOTAGE" in chu.upper(), f"thiếu lời dặn editor: {chu}"


def test_anh_giu_cho_DUNG_LAI_khong_render_lai(tmp_path):
    """Mỗi link một ảnh riêng, nhưng gọi lại CÙNG link phải trả đúng file cũ —
    35 miếng hở mà render 35 lượt matplotlib là phí."""
    from autoedit.offline.thay_mau import anh_giu_cho

    f1, _ = anh_giu_cho(tmp_path, "https://a/1", "x")
    m1 = Path(f1).stat().st_mtime_ns
    f2, _ = anh_giu_cho(tmp_path, "https://a/1", "x")
    assert Path(f2) == Path(f1) and Path(f2).stat().st_mtime_ns == m1, \
        "render lại ảnh đã có"
    f3, _ = anh_giu_cho(tmp_path, "https://a/2", "x")
    assert Path(f3) != Path(f1), "hai link khác nhau mà dùng chung một ảnh"


def test_anh_hong_KHONG_giet_draft(tmp_path, profile, hop_dong, monkeypatch):
    """Lưới an toàn: matplotlib lỗi thì mất ô giữ chỗ, KHÔNG được mất draft."""
    from autoedit.offline import thay_mau as tm

    def no(*a, **k):
        raise RuntimeError("hỏng")

    monkeypatch.setattr(tm, "anh_giu_cho", no)
    v = {0: _video(tmp_path / "a.mp4", 3), 2: _video(tmp_path / "c.mp4", 3)}
    segs = _video_segs(_dung(tmp_path, profile, hop_dong, v, "THU_LOI"))
    assert len(segs) == 2, "ảnh hỏng mà draft chết theo"


def test_relocate_GHI_LINK_cua_clip_dang_chon(tmp_path):
    """Miếng có ứng viên nhưng tải hỏng hết -> ô giữ chỗ phải mang LINK của
    clip ĐANG CHỌN (clip người dựng đã duyệt), không phải link bất kỳ.

    Đây là logic nối `relocate` -> `dung_draft` qua `hinh[i]["ho_link"]`; không
    có check chạy được thì đổi tên trường một cái là link biến mất im lặng.
    """
    from autoedit.offline import thay_mau as tm
    from autoedit.sotra import db as sdb

    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "envato:V1", "nguon": "envato", "tieu_de": "Rome dawn",
                      "url_trang": "https://elements.envato.com/rome-V1",
                      "url_video": "", "path_local": ""})
    c.commit()
    hd = {"offset": 0.0,
          "khoi": [{"v0": 0.0, "v1": 2.0, "tho": 0.0}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": "envato:V1", "nguon": "envato",
                            "tieu_de": "Rome dawn"}]}]}
    (tmp_path / "proj").mkdir()
    video, _dung_id, warns, _du = tm.relocate(
        tmp_path / "proj", hd, c, lambda m: None)
    c.close()

    assert 0 not in video, "clip không có file mà vẫn coi là tải được"
    assert hd["hinh"][0]["ho_link"] == "https://elements.envato.com/rome-V1", \
        f"thiếu/sai link tải tay: {hd['hinh'][0].get('ho_link')!r}"
    assert hd["hinh"][0]["ho_ten"] == "Rome dawn"
    # Từ 10/09 (user họp team): clip envato thiếu bản sạch KHÔNG dùng preview
    # watermark nữa -> warning nói đúng nguyên nhân đó, không nói "khay rỗng".
    assert any("BẢN SẠCH" in w or "giữ chỗ" in w for w in warns), warns


def test_LINK_di_TU_relocate_TOI_anh_tren_draft(tmp_path, profile):
    """Mối nối dễ đứt nhất: `relocate` ghi `ho_link` vào hợp đồng, `dung_draft`
    đọc lại để in lên ảnh. Hai test riêng đều xanh mà mối nối đứt thì link vẫn
    mất — nên phải có một lượt đi XUYÊN SUỐT.
    """
    from autoedit.offline import thay_mau as tm
    from autoedit.sotra import db as sdb

    c = sdb.mo(tmp_path / "kho" / "sotra.db")
    sdb.them_clip(c, {"id": "envato:V9", "nguon": "envato", "tieu_de": "Rome dawn",
                      "url_trang": "https://elements.envato.com/rome-V9",
                      "url_video": "", "path_local": ""})
    c.commit()
    hd = {"offset": 0.0,
          "khoi": [{"v0": 0.0, "v1": 2.0, "tho": 0.0}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": "envato:V9", "nguon": "envato",
                            "tieu_de": "Rome dawn"}]}]}
    proj = tmp_path / "proj"
    proj.mkdir()
    video, _ids, _w, _du = tm.relocate(proj, hd, c, lambda m: None)
    c.close()

    ghi: list[tuple] = []
    that = tm.anh_giu_cho

    def bat(thu_muc, link="", tieu_de=""):
        ghi.append((link, tieu_de))
        return that(thu_muc, link, tieu_de)

    tm.anh_giu_cho, bo = bat, tm.anh_giu_cho
    try:
        d = tm.dung_draft(proj, hd, video, {}, "THU_XUYEN", profile, lambda m: None)
    finally:
        tm.anh_giu_cho = bo

    assert ghi == [("https://elements.envato.com/rome-V9", "Rome dawn")], \
        f"link không tới được ảnh giữ chỗ: {ghi}"
    nd = json.loads((Path(d) / "draft_content.json").read_text(encoding="utf-8"))
    assert not _lo_ho(_video_segs(nd)), "draft vẫn hở"


def test_LINK_DAI_khong_TRAN_khoi_khung(tmp_path):
    """Nhìn ảnh thật 10/09 mới thấy: link Envato/Pexels dài 82-226 ký tự bị
    matplotlib vẽ TRÀN cả hai mép — mất `https://...` ở đầu và mất ID ở đuôi,
    người dựng không tải được. `wrap=True` không bẻ được chuỗi không có
    khoảng trắng, nên phải tự bẻ dòng.

    Đo dài nhất trong kho thật (10/09): 226 ký tự (một link Pexels).
    """
    from autoedit.offline.thay_mau import anh_giu_cho, be_dong

    dai = ("https://www.pexels.com/video/landscape-shot-of-frozen-sissu-waterfall-"
           "during-the-winter-season-at-sissu-in-lahaul-valley-himachal-pradesh-"
           "india-frozen-sissu-waterfall-during-the-winter-in-himachal-due-to-"
           "extreme-cold-26182249/")
    assert len(dai) > 220, "mẫu thử phải là link dài nhất đo được"

    dong = be_dong(dai, 64)
    assert all(len(d) <= 64 for d in dong), f"còn dòng quá dài: {dong}"
    assert "".join(dong) == dai, "bẻ dòng làm MẤT/THÊM ký tự -> link sai"

    f, chu = anh_giu_cho(tmp_path, dai, "Sissu waterfall")
    assert Path(f).is_file(), "không render được ảnh"
    assert dai in chu.replace("\n", ""), "link bị cắt cụt trong phần chữ"


def test_be_dong_giu_nguyen_link_ngan(tmp_path):
    """Link ngắn không được bẻ — bẻ vô cớ là làm khó mắt."""
    from autoedit.offline.thay_mau import be_dong

    assert be_dong("https://a.com/x", 64) == ["https://a.com/x"]
    assert be_dong("", 64) == []
