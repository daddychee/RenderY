"""Tập đặt PHẲNG: 16 chương chung một thư mục -> chỉ ra MỘT project (08/09).

User báo: thanhdn nộp LI089 (16 chương), owner không mở được khối Offline.
Đo trên dữ liệu thật:
  - hàng đợi job 23 ghi `project_id` = `h-20260908-081546` LẶP 16 LẦN;
  - `projects/` chỉ có ĐÚNG MỘT thư mục cho cả tập;
  - log job: từ chương 2 trở đi đều in "'RenderY' đã chuẩn bị trước đó — dùng
    lại, không tạo bản mới";
  - `F:\...\LI089\RenderY\` chứa `H.mp3 H.txt C1.mp3 C1.txt ...` đặt PHẲNG,
    còn LI103 (chạy đúng, ra 17 project) thì mỗi chương một THƯ MỤC CON.

Nguyên nhân: `_project_cu_dung_duoc` khớp project cũ theo **thư mục cha của
script** (`sc.parent == folder`). Đặt phẳng thì mọi chương chung một cha, nên
project của chương H khớp với TẤT CẢ chương sau — 15 chương còn lại không bao
giờ được align, và Offline không có gì để mở.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


def _tap_phang(tmp_path: Path) -> Path:
    """Thư mục chương đặt phẳng: H và C1 nằm cạnh nhau."""
    d = tmp_path / "LI089" / "RenderY"
    d.mkdir(parents=True)
    for ten in ("H", "C1"):
        (d / f"{ten}.txt").write_text("xin chao", encoding="utf-8")
        (d / f"{ten}.mp3").write_bytes(b"\0" * 64)
    return d


def _project_da_align(out: Path, pid: str, script: Path, voice: Path) -> Path:
    """Project đã CHUẨN BỊ xong (có transcript + voice_master) cho `script`.

    Dựng qua chính `Project` + `Inputs` — đồ giả viết tay thiếu trường thì
    `Project.load` ném ValidationError, hàm khớp rơi vào nhánh fail-safe và trả
    None: test đỏ vì lý do SAI, không phải vì lỗi đang truy.
    """
    from autoedit.project import Inputs, Project

    p = out / pid
    (p / "media").mkdir(parents=True)
    (p / "transcript.json").write_text("[]", encoding="utf-8")
    (p / "media" / "voice_master.wav").write_bytes(b"x" * 16)
    pj = Project(project_id=pid, title=pid,
                 created_at=datetime.now(timezone.utc).isoformat(),
                 project_dir=str(p),
                 inputs=Inputs(script_path=str(script), voice_path=str(voice),
                               original_script_path=str(script),
                               original_voice_path=str(voice),
                               script_text="xin chao"))
    (p / "project.json").write_text(pj.model_dump_json(), encoding="utf-8")
    return p


def test_chuong_phang_KHONG_dung_lai_project_cua_chuong_khac(tmp_path):
    """H đã chuẩn bị xong thì C1 phải được TẠO MỚI, không dùng lại project của H."""
    from autoedit.cli import _project_cu_dung_duoc

    d = _tap_phang(tmp_path)
    out = tmp_path / "projects"
    out.mkdir()
    _project_da_align(out, "h-2026", d / "H.txt", d / "H.mp3")

    cu = _project_cu_dung_duoc(d, out, chi_align=True, script=d / "C1.txt")
    assert cu is None, "C1 dùng lại project của H — 15 chương sau không bao giờ align"


def test_chuong_phang_VAN_dung_lai_dung_chuong_cua_no(tmp_path):
    """Nộp lại đúng chương H thì vẫn tái dùng — không được dựng lại từ đầu."""
    from autoedit.cli import _project_cu_dung_duoc

    d = _tap_phang(tmp_path)
    out = tmp_path / "projects"
    out.mkdir()
    _project_da_align(out, "h-2026", d / "H.txt", d / "H.mp3")

    cu = _project_cu_dung_duoc(d, out, chi_align=True, script=d / "H.txt")
    assert cu is not None, "nộp lại chương H mà dựng lại từ đầu — mất công đã làm"


def test_thu_muc_rieng_tung_chuong_giu_nguyen_hanh_vi(tmp_path):
    """Bố cục cũ (mỗi chương một thư mục) không truyền `script` — giữ y như cũ."""
    from autoedit.cli import _project_cu_dung_duoc

    d = tmp_path / "LI103" / "RenderY" / "H"
    d.mkdir(parents=True)
    (d / "script.txt").write_text("xin chao", encoding="utf-8")
    (d / "voice.mp3").write_bytes(b"\0" * 64)
    out = tmp_path / "projects"
    out.mkdir()
    _project_da_align(out, "h-2026", d / "script.txt", d / "voice.mp3")

    assert _project_cu_dung_duoc(d, out, chi_align=True) is not None


def test_worker_truyen_script_khi_chuong_dat_phang():
    """Rào ở tầng gọi: worker đã truyền `--script/--voice` cho chương phẳng thì
    `make` PHẢI chuyển tiếp xuống hàm khớp project — thiếu một mắt là lỗi quay
    lại y nguyên."""
    import inspect

    from autoedit import cli

    src = inspect.getsource(cli.make)
    assert "_project_cu_dung_duoc(" in src
    i = src.index("_project_cu_dung_duoc(")
    assert "script" in src[i:i + 200], "make không chuyển `script` xuống hàm khớp project"


# ---------------------------------------------------------------------------
# Lỗi THỨ HAI, chính là thứ user nhìn thấy: tab Offline không có LI089, thay
# vào đó hiện một mục lạ `US` với chương tên `RENDERY`.
#
# `api_offline_tap_list` suy mã tập bằng `re.search(r"[\/]([A-Z]{2,4}\d{2,4})")`.
# Trong LỚP KÝ TỰ, `\/` chỉ là dấu `/` — lớp KHÔNG chứa dấu `\`. Đường dẫn
# Windows toàn `\` nên biểu thức này KHÔNG BAO GIỜ khớp (đo thật: cả LI103 lẫn
# LI089 đều trượt). Mọi tập lâu nay đều đi bằng nhánh dự phòng
# `parent.parent.parent.name` — nhánh đó đếm LÙI 3 CẤP, đúng với bố cục thư mục
# con (`LI103\Rendery\H\H.txt`) và SAI với bố cục phẳng (`LI089\RenderY\H.txt`,
# lùi 3 cấp ra `US`).

def test_ma_tap_doc_dung_o_ca_hai_bo_cuc():
    from autoedit.web.server import ma_tap_tu_script

    assert ma_tap_tu_script(r"F:\Nas\Life In\US\LI103\Rendery\H\H.txt") == "LI103"
    assert ma_tap_tu_script(r"F:\Nas\Life In\US\LI089\RenderY\H.txt") == "LI089"
    # dấu gạch xuôi cũng phải chạy — đường dẫn qua API có thể là kiểu POSIX
    assert ma_tap_tu_script("F:/Nas/Life In/US/LI089/RenderY/C1.txt") == "LI089"


def test_nhan_chuong_doc_dung_o_ca_hai_bo_cuc():
    from autoedit.web.server import nhan_chuong_tu_script

    assert nhan_chuong_tu_script(r"F:\Nas\US\LI103\Rendery\H\H.txt") == "H"
    assert nhan_chuong_tu_script(r"F:\Nas\US\LI103\Rendery\C12\script.txt") == "C12"
    # PHẲNG: nhãn nằm ở TÊN FILE, không phải thư mục cha (nếu không ra "RENDERY")
    assert nhan_chuong_tu_script(r"F:\Nas\US\LI089\RenderY\H.txt") == "H"
    assert nhan_chuong_tu_script(r"F:\Nas\US\LI089\RenderY\C12.txt") == "C12"


def test_khong_co_thu_muc_RenderY_thi_khong_vo():
    """Đường dẫn lạ (thư mục test, project cũ) không được ném lỗi."""
    from autoedit.web.server import ma_tap_tu_script, nhan_chuong_tu_script

    assert ma_tap_tu_script("") == ""
    assert nhan_chuong_tu_script("") == ""
    assert ma_tap_tu_script(r"C:\linh tinh\a.txt")          # có gì đó, không vỡ
