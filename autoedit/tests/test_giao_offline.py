"""Export xong mà thư mục tập trên NAS RỖNG (user báo 09/09).

Hải bấm Export, draft RA THẬT — nhưng ở kho draft CapCut
(`...\Tool Edit\Capcut Draft\CapCut Drafts\OFF_<chương>`), còn thư mục tập
`...\LI106_Hai\RenderY\Compose Timeline\<chương>\` thì **rỗng hết 14 thư
mục**.

Không phải hiểu nhầm — chính `DOC_TRUOC.txt` nằm trong đó hứa: *"Copy cả thư
mục này về máy… mỗi chương có draft/, footage/, report.html,
nguon_footage.txt"*. Đường Offline không giao gì vào đó, nên tờ hướng dẫn hứa
một đằng thực tế một nẻo.

Đo: 10/14 chương có draft, tổng **992MB**. User chốt (09/09) **KHÔNG chép draft**
sang (nhân đôi 992MB mỗi tập + đẻ ra hai bản lệch nhau), chỉ giao **giấy tờ +
lối mở**: `nguon_footage.*`, `GIAY_PHEP.txt`, và một file chỉ rõ mở draft nào.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _draft_gia(d: Path) -> Path:
    """Thư mục draft như thay_mau sinh ra."""
    d.mkdir(parents=True, exist_ok=True)
    (d / "draft_content.json").write_text("{}", encoding="utf-8")
    (d / "nguon_footage.txt").write_text("SỔ NGUỒN FOOTAGE — thử", encoding="utf-8")
    (d / "nguon_footage.json").write_text('{"clips": []}', encoding="utf-8")
    (d / "GIAY_PHEP.txt").write_text("envato:x\thttp://i\tf.mp4\t2026-09-01",
                                     encoding="utf-8")
    (d / "materials").mkdir(exist_ok=True)
    (d / "materials" / "to.mp4").write_bytes(b"x" * 4096)
    return d


def _project_gia(tmp: Path, pid: str, script: str) -> Path:
    p = tmp / "projects" / pid
    p.mkdir(parents=True)
    p.joinpath("project.json").write_text(json.dumps({
        "project_id": pid, "title": pid, "created_at": "2026-09-08T00:00:00",
        "project_dir": str(p),
        "inputs": {"script_path": script, "voice_path": script,
                   "original_script_path": script, "original_voice_path": script,
                   "script_text": "x"}}), encoding="utf-8")
    return p


def test_giao_GIAY_TO_va_LOI_MO_vao_thu_muc_tap(tmp_path):
    from autoedit.offline.giao import giao_giay_to

    tap = tmp_path / "NAS" / "LI106_Hai" / "RenderY"
    (tap / "Compose Timeline").mkdir(parents=True)
    p = _project_gia(tmp_path, "c9-2026", str(tap / "C9.txt"))
    draft = _draft_gia(tmp_path / "CapCut Drafts" / "OFF_c9-2026")

    dest = giao_giay_to(p, draft)
    assert dest is not None and dest.is_dir()
    assert dest.name == "C9", f"giao nhầm thư mục chương: {dest}"
    co = {f.name for f in dest.iterdir()}
    assert "nguon_footage.txt" in co and "GIAY_PHEP.txt" in co, co
    # LỐI MỞ: phải chỉ đúng tên draft, nếu không nhân sự tự mò trong hàng trăm draft
    mo = next(f for f in dest.iterdir() if f.suffix == ".txt"
              and "draft" in f.name.lower())
    chu = mo.read_text(encoding="utf-8")
    assert "OFF_c9-2026" in chu and str(draft) in chu, chu[:200]


def test_KHONG_chep_draft_sang_thu_muc_tap(tmp_path):
    """User chốt: không nhân đôi 992MB, và không đẻ ra hai bản có thể lệch nhau."""
    from autoedit.offline.giao import giao_giay_to

    tap = tmp_path / "NAS" / "LI106_Hai" / "RenderY"
    (tap / "Compose Timeline").mkdir(parents=True)
    p = _project_gia(tmp_path, "c9-2026", str(tap / "C9.txt"))
    draft = _draft_gia(tmp_path / "CapCut Drafts" / "OFF_c9-2026")

    dest = giao_giay_to(p, draft)
    assert not (dest / "materials").exists(), "đã chép materials sang — nhân đôi dung lượng"
    assert not (dest / "draft_content.json").exists(), "đã chép draft sang"
    tong = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
    assert tong < 100_000, f"thư mục giao phình {tong} byte — phải là giấy tờ thôi"


def test_bo_cuc_THU_MUC_CON_cung_giao_dung_cho(tmp_path):
    """`LI103/Rendery/C9/script.txt` -> vẫn phải ra thư mục chương `C9`."""
    from autoedit.offline.giao import giao_giay_to

    tap = tmp_path / "NAS" / "LI103" / "RenderY"
    (tap / "Compose Timeline").mkdir(parents=True)
    p = _project_gia(tmp_path, "c9-2026", str(tap / "C9" / "script.txt"))
    draft = _draft_gia(tmp_path / "CapCut Drafts" / "OFF_c9-2026")

    dest = giao_giay_to(p, draft)
    assert dest is not None and dest.name == "C9"


def test_giao_hong_KHONG_giet_draft(tmp_path, monkeypatch):
    """Giao là thứ đi kèm — hỏng thì mất giấy tờ, KHÔNG được mất draft đã dựng."""
    from autoedit.offline import giao

    p = _project_gia(tmp_path, "c9-2026", "")      # thiếu đường dẫn NAS
    draft = _draft_gia(tmp_path / "CapCut Drafts" / "OFF_c9-2026")
    assert giao.giao_giay_to(p, draft) is None     # không ném lỗi


def test_thay_mau_goi_buoc_giao(tmp_path):
    """Rào: `thay_mau` phải GỌI bước giao, nếu không vá xong vẫn không ai thấy."""
    import inspect

    from autoedit.offline import thay_mau as tm

    src = inspect.getsource(tm.thay_mau) + inspect.getsource(tm.dung_draft)
    assert "giao_giay_to" in src, "thay_mau chưa gọi bước giao"
