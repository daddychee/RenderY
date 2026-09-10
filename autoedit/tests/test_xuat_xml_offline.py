r"""Export xong CHƯA CÓ XML — user báo 10/09/2026: *"nó vẫn chưa có Xml anh ạ"*.

Đo 10/09: mã xuất XML **đã có sẵn và đầy đủ**
  - `packager/xmeml.py`  -> `.xml`    (FCP7 XML — Premiere chỉ import kiểu này)
  - `packager/fcpxml.py` -> `.fcpxml` (DaVinci Resolve / Final Cut)
  - `web/compose.py:96-118` gọi cả hai

Nhưng đường **Offline** ráp draft ở `offline/thay_mau.py` và giao giấy tờ ở
`offline/giao.py` — không chỗ nào gọi compose (grep `xml` trong hai file đó:
0 kết quả). Nên bấm Export chỉ ra draft CapCut. Thiếu đúng MỘT mối nối.

KHÔNG dùng lại `compose_chapter`: hàm đó **copy cả draft** sang thư mục giao,
trong khi đường Offline đã chốt 09/09 là KHÔNG chép draft (đo LI106: 10 draft
= 992MB, chép sang là nhân đôi và đẻ hai bản lệch nhau). Chỉ gọi thẳng
`xuat_xmeml` / `xuat_fcpxml` trỏ vào draft tại chỗ.

USER CHỐT 10/09: xuất **cùng lúc với draft CapCut**, không thêm nút. Hỏng XML
KHÔNG được giết draft — chỉ ghi cảnh báo (cùng luật với sổ nguồn gốc).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _draft_gia(d: Path) -> Path:
    """Draft CapCut tối thiểu mà `xuat_xmeml` đọc được."""
    d.mkdir(parents=True, exist_ok=True)
    (d / "materials").mkdir(exist_ok=True)
    v = d / "materials" / "v0.mp4"
    v.write_bytes(b"\x00" * 4096)
    noi_dung = {
        "fps": 30, "duration": 4_000_000,
        "canvas_config": {"width": 1920, "height": 1080},
        "materials": {
            "videos": [{"id": "m1", "path": str(v), "material_name": "v0.mp4",
                        "duration": 4_000_000, "type": "video",
                        "width": 1920, "height": 1080}],
            "audios": [],
        },
        "tracks": [{"id": "t1", "type": "video", "segments": [{
            "id": "s1", "material_id": "m1",
            "target_timerange": {"start": 0, "duration": 4_000_000},
            "source_timerange": {"start": 0, "duration": 4_000_000},
            "speed": 1.0}]}],
    }
    (d / "draft_content.json").write_text(json.dumps(noi_dung), encoding="utf-8")
    (d / "draft_info.json").write_text(json.dumps(noi_dung), encoding="utf-8")
    return d


def test_xuat_ca_HAI_ban_canh_draft(tmp_path):
    """Premiere đọc `.xml`, Resolve/FCP đọc `.fcpxml` — phải có cả hai, và nằm
    CẠNH draft như `nguon_footage.*` để editor mở draft ở máy khác vẫn thấy."""
    from autoedit.offline.thay_mau import xuat_xml_canh_draft

    d = _draft_gia(tmp_path / "OFF_c1")
    cb = xuat_xml_canh_draft(d, log=lambda m: None)
    assert (d / "OFF_c1.xml").is_file(), f"thiếu bản Premiere (.xml): {cb}"
    assert (d / "OFF_c1.fcpxml").is_file(), f"thiếu bản Resolve (.fcpxml): {cb}"


def test_xml_KHONG_rong_va_dung_dinh_dang(tmp_path):
    """File tồn tại chưa đủ — Premiere từ chối XML sai gốc. Kiểm nội dung
    thật, không kiểm sự tồn tại (bài học BH11)."""
    from autoedit.offline.thay_mau import xuat_xml_canh_draft

    d = _draft_gia(tmp_path / "OFF_c2")
    xuat_xml_canh_draft(d, log=lambda m: None)
    x = (d / "OFF_c2.xml").read_text(encoding="utf-8")
    assert "<xmeml" in x, "không phải FCP7 XML — Premiere sẽ không import được"
    assert "<sequence" in x and "OFF_c2" in x, "thiếu sequence hoặc tên sequence"
    f = (d / "OFF_c2.fcpxml").read_text(encoding="utf-8")
    assert "<fcpxml" in f, "không phải fcpxml — Resolve sẽ không mở được"


def test_XML_hong_KHONG_giet_draft(tmp_path):
    """Cùng luật với sổ nguồn gốc: mất XML chứ KHÔNG được mất draft đã dựng."""
    from autoedit.offline import thay_mau as tm

    d = tmp_path / "OFF_c3"
    d.mkdir()                     # draft rách: không có draft_content.json
    cb = tm.xuat_xml_canh_draft(d, log=lambda m: None)
    assert cb, "draft hỏng mà không có cảnh báo nào"
    assert any("xml" in c.lower() for c in cb), cb


def test_dung_draft_TU_GOI_xuat_xml(tmp_path, monkeypatch):
    """Mối nối: `dung_draft` phải tự gọi — hàm có mà không ai gọi thì user vẫn
    không có XML, đúng như đang xảy ra với `compose_chapter`."""
    from autoedit.offline import thay_mau as tm

    goi: list[Path] = []
    monkeypatch.setattr(tm, "xuat_xml_canh_draft",
                        lambda draft, log=None: goi.append(Path(draft)) or [])
    import inspect
    src = inspect.getsource(tm.dung_draft)
    assert "xuat_xml_canh_draft" in src, \
        "dung_draft không gọi xuat_xml_canh_draft — XML sẽ không bao giờ ra"
