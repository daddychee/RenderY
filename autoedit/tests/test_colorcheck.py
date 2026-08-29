"""C3 — so màu nội bộ chương, chỉ cảnh báo (MO_TA_VAN_HANH_C_DOT_1.md §C3)."""

from types import SimpleNamespace

from autoedit.sourcer.colorcheck import check_project_colors, find_color_outliers


def _it(beat_id, chapter, v, s, h=30.0, hs=0.5, label="clip.mp4"):
    return {"beat_id": beat_id, "chapter": chapter, "label": label,
            "v": v, "s": s, "h": h, "hs": hs}


def test_brightness_outlier_flagged():
    """Ví dụ user b1: 1 clip sáng chói lọt chương u ám -> đúng 1 cảnh báo 'sáng hơn'."""
    items = [_it(1, 1, 0.20, 0.4), _it(2, 1, 0.25, 0.4),
             _it(3, 1, 0.22, 0.4), _it(4, 1, 0.85, 0.4, label="bright.mp4")]
    warns = find_color_outliers(items)
    assert len(warns) == 1 and "b004" in warns[0] and "sáng hơn hẳn" in warns[0]
    assert "bright.mp4" in warns[0]


def test_saturation_outlier_flagged():
    """Ví dụ user b1: clip vintage (xám) lọt chương colorful -> cảnh báo 'xám hơn'."""
    items = [_it(1, 1, 0.5, 0.70), _it(2, 1, 0.5, 0.65),
             _it(3, 1, 0.5, 0.75), _it(4, 1, 0.5, 0.15, label="vintage.mp4")]
    warns = find_color_outliers(items)
    assert len(warns) == 1 and "xám hơn hẳn" in warns[0]


def test_uniform_chapter_silent():
    items = [_it(i, 1, 0.4 + i * 0.02, 0.5, h=20.0 + i) for i in range(1, 6)]
    assert find_color_outliers(items) == []


def test_small_chapter_skipped():
    """<3 footage đo được -> không đủ 'xung quanh' để so tương đối -> im lặng."""
    items = [_it(1, 1, 0.1, 0.5), _it(2, 1, 0.9, 0.5)]
    assert find_color_outliers(items) == []


def test_hue_outlier_needs_dominant_tone():
    """Chương tông cam + 1 clip xanh dương -> cảnh báo lệch tông; clip XÁM (hs thấp)
    không bị xét hue (hue của màu xám là nhiễu)."""
    items = [_it(1, 1, 0.5, 0.5, h=25, hs=0.6), _it(2, 1, 0.5, 0.5, h=35, hs=0.6),
             _it(3, 1, 0.5, 0.5, h=30, hs=0.6),
             _it(4, 1, 0.5, 0.5, h=210, hs=0.6, label="blue.mp4"),
             _it(5, 1, 0.5, 0.5, h=210, hs=0.05, label="gray.mp4")]
    warns = find_color_outliers(items)
    assert len(warns) == 1 and "blue.mp4" in warns[0] and "lệch tông màu" in warns[0]


def test_hue_skipped_when_scattered():
    """Chương KHÔNG có tông chủ đạo (hue tản mác) -> không cảnh báo hue oan."""
    items = [_it(1, 1, 0.5, 0.5, h=0, hs=0.6), _it(2, 1, 0.5, 0.5, h=90, hs=0.6),
             _it(3, 1, 0.5, 0.5, h=180, hs=0.6), _it(4, 1, 0.5, 0.5, h=270, hs=0.6)]
    assert find_color_outliers(items) == []


def test_chapters_compared_separately():
    """So TƯƠNG ĐỐI trong từng chương: chương tối + chương sáng đều đồng màu nội bộ
    -> 0 cảnh báo (so tuyệt đối cả video sẽ báo oan)."""
    items = [_it(i, 1, 0.15, 0.5) for i in (1, 2, 3)] + \
            [_it(i, 2, 0.80, 0.5) for i in (4, 5, 6)]
    assert find_color_outliers(items) == []


def test_check_project_colors_on_real_images(tmp_path):
    """Integration: đo JPEG thật (PIL, không cần ffmpeg) — 2 ảnh tối + 1 ảnh sáng cùng
    chương -> warning 'sáng hơn' + dòng tổng; file hỏng -> đo hụt, không nổ stage."""
    from PIL import Image

    assets = tmp_path / "assets"
    assets.mkdir()
    for name, rgb in [("b001_dark.jpg", (20, 20, 40)), ("b002_dark.jpg", (25, 22, 38)),
                      ("b003_bright.jpg", (240, 235, 230))]:
        Image.new("RGB", (64, 64), rgb).save(assets / name)
    (assets / "b004_broken.jpg").write_bytes(b"not an image")

    beats = [SimpleNamespace(beat_id=i, chapter=1) for i in (1, 2, 3, 4)]
    shots = [SimpleNamespace(beat_id=i, status="ok", asset_path=f"assets/{n}",
                             extra_shots=[])
             for i, n in [(1, "b001_dark.jpg"), (2, "b002_dark.jpg"),
                          (3, "b003_bright.jpg"), (4, "b004_broken.jpg")]]
    project = SimpleNamespace(project_dir=str(tmp_path), beats=beats, shots=shots,
                              breath_shots=[])
    record = SimpleNamespace(warnings=[])
    check_project_colors(project, record)
    assert any("b003" in w and "sáng hơn hẳn" in w for w in record.warnings)
    assert any("đo 3 footage / 1 chương" in w and "đo hụt 1" in w for w in record.warnings)
