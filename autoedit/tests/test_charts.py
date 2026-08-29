"""Test renderer biểu đồ (P1.5) — integration ffmpeg + matplotlib."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from autoedit.project import ChartDatum, GraphicSpec

needs_render = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="cần ffmpeg"
)


def _probe(path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=codec_name,width,height,pix_fmt", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=0", str(path)],
        capture_output=True, text=True,
    ).stdout
    return dict(line.split("=", 1) for line in out.strip().splitlines())


@needs_render
def test_render_bar_chart(tmp_path):
    from autoedit.packager.charts import render_chart

    spec = GraphicSpec(chart_type="bar", title="Chi phí thuê / tháng", unit="$",
                       data=[ChartDatum(label="Việt Nam", value=400),
                             ChartDatum(label="Mỹ", value=2500)])
    out = render_chart(spec, 4.0, tmp_path / "bar.mp4")
    assert out.is_file()
    p = _probe(out)
    assert p["codec_name"] == "h264" and p["pix_fmt"] == "yuv420p"
    assert p["width"] == "1920" and p["height"] == "1080"
    assert abs(float(p["duration"]) - 4.0) < 0.2


@needs_render
def test_render_line_chart(tmp_path):
    from autoedit.packager.charts import render_chart

    spec = GraphicSpec(chart_type="line", title="Tăng theo năm", unit="%",
                       data=[ChartDatum(label="2020", value=0), ChartDatum(label="2024", value=32),
                             ChartDatum(label="2026", value=45)])
    out = render_chart(spec, 3.0, tmp_path / "line.mp4")
    assert out.is_file() and _probe(out)["codec_name"] == "h264"


@needs_render
def test_render_line_axis_labels_light_theme(tmp_path):
    """Req 5: line nhiều điểm + nhãn trục + theme sáng vẫn ra mp4 hợp lệ yuv420p."""
    from autoedit.packager.charts import render_chart

    spec = GraphicSpec(chart_type="line", title="Nhiệt thấm mùa hè", unit="",
                       theme="light", x_label="Tuần", y_label="Độ sâu (ft)",
                       data=[ChartDatum(label=str(w), value=w * 1.1) for w in range(1, 9)])
    out = render_chart(spec, 4.0, tmp_path / "line_axis.mp4")
    assert out.is_file()
    p = _probe(out)
    assert p["codec_name"] == "h264" and p["pix_fmt"] == "yuv420p"
    assert p["width"] == "1920" and p["height"] == "1080"


@needs_render
def test_render_dark_line_backward_compat(tmp_path):
    """Chart cũ (không x_label/theme) render y như trước — không vỡ."""
    from autoedit.packager.charts import render_chart

    spec = GraphicSpec(chart_type="line", title="Tăng theo năm", unit="%",
                       data=[ChartDatum(label="2020", value=10), ChartDatum(label="2024", value=40)])
    out = render_chart(spec, 3.0, tmp_path / "line_dark.mp4")
    assert out.is_file() and _probe(out)["codec_name"] == "h264"


@needs_render
def test_render_pie_chart(tmp_path):
    from autoedit.packager.charts import render_chart

    spec = GraphicSpec(chart_type="pie", title="Lương hưu tiêu vào đâu", unit="%",
                       data=[ChartDatum(label="Tiền thuê nhà", value=50),
                             ChartDatum(label="Còn lại", value=50)])
    out = render_chart(spec, 4.0, tmp_path / "pie.mp4")
    assert out.is_file()
    p = _probe(out)
    assert p["codec_name"] == "h264" and p["pix_fmt"] == "yuv420p"
    assert p["width"] == "1920" and p["height"] == "1080"


@needs_render
def test_render_pie_half_layout(tmp_path):
    """pie dùng được cả layout half (PiP) — cùng đường ống bar/line."""
    from autoedit.packager.charts import render_chart

    spec = GraphicSpec(chart_type="pie", title="Ngân sách", unit="$", layout="half",
                       data=[ChartDatum(label="Thuê", value=400),
                             ChartDatum(label="Ăn", value=300),
                             ChartDatum(label="Khác", value=500)])
    out = render_chart(spec, 4.0, tmp_path / "pie_half.mp4")
    assert out.is_file() and _probe(out)["codec_name"] == "h264"
