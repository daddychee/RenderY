r"""Nạp đủ script rồi vẫn báo "transcript rỗng" — user báo 10/09/2026.

CA THẬT, chương `e-20260908-115102`:

| | |
|---|---|
| `E.txt` trên NAS | **1139 byte**, sửa **15:45 ngày 10/09** — user đã nạp thật |
| `inputs/script.txt` trong chương | **0 byte**, từ 08/09 |
| `project.json` -> `inputs.script_text` | rỗng |
| Hệ quả | align khớp **0%** -> `transcript.json` có `words: []` -> "transcript rỗng — chạy align trước" |

Log production: `POST /api/offline/e-20260908-115102/phan-tich` lặp **hơn 15
lần**, tất cả 200 OK. User bấm mãi mà không hiểu vì sao.

HAI LỖI CHỒNG NHAU:

1. **Tạo chương với script RỖNG mà không chặn.** `project.py:618` copy script
   rồi đi tiếp, không kiểm nội dung. Chương hỏng ngay từ lúc sinh ra, và chỗ
   duy nhất phàn nàn là align — báo "transcript rỗng", tức là đổ lỗi cho khâu
   SAU chứ không chỉ ra khâu thật sự hỏng.

2. **Không bao giờ đọc lại script gốc.** Copy một lần lúc tạo (chú thích
   "self-contained, resume độc lập file gốc"). User sửa `E.txt` xong bấm Phân
   tích 15 lần, tool vẫn dùng bản rỗng cũ.

Quét 90 chương: 1 chương dính. Hiếm — nhưng khi dính là chặn hẳn người dùng.

USER CHỐT 10/09: *tự đọc lại script gốc* — chỉ khi bản trong chương RỖNG.
Không đụng chương đang chạy bình thường (giữ tính self-contained cho chúng).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _du_an(tmp: Path, chu_local: str, chu_goc: str | None) -> Path:
    """Chương như `tao_project` sinh ra, với script local/gốc đặt được."""
    p = tmp / "projects" / "e-thu"
    (p / "inputs").mkdir(parents=True)
    (p / "media").mkdir()
    (p / "inputs" / "script.txt").write_text(chu_local, encoding="utf-8")
    goc = tmp / "nas" / "E" / "E.txt"
    if chu_goc is not None:
        goc.parent.mkdir(parents=True)
        goc.write_text(chu_goc, encoding="utf-8")
    (p / "project.json").write_text(json.dumps({
        "project_id": "e-thu", "title": "E", "created_at": "2026-09-08T11:51:02",
        "project_dir": str(p),
        "inputs": {"script_path": "inputs\\script.txt",
                   "voice_path": "inputs\\voice.mp3",
                   "original_script_path": str(goc),
                   "original_voice_path": str(goc.with_suffix(".mp3")),
                   "script_text": chu_local, "voice_duration_sec": 89.6},
        "stages": {},
    }, ensure_ascii=False), encoding="utf-8")
    return p


BAI = "Người dân Pakistan sống ra sao. Đây là câu thứ hai của kịch bản."


def test_script_local_RONG_thi_doc_lai_ban_goc(tmp_path):
    """Ca user gặp: bản trong chương rỗng, bản gốc trên NAS có nội dung."""
    from autoedit.project import doc_script

    p = _du_an(tmp_path, "", BAI)
    assert doc_script(p) == BAI, "không đọc lại được script gốc khi bản local rỗng"


def test_doc_lai_thi_GHI_DE_ban_local(tmp_path):
    """Đọc lại rồi phải LƯU vào chương — nếu không thì mỗi khâu sau lại phải
    tự đọc NAS, và chương vẫn không self-contained như thiết kế."""
    from autoedit.project import doc_script

    p = _du_an(tmp_path, "", BAI)
    doc_script(p)
    assert (p / "inputs" / "script.txt").read_text(encoding="utf-8") == BAI
    d = json.loads((p / "project.json").read_text(encoding="utf-8"))
    assert d["inputs"]["script_text"] == BAI, "project.json chưa cập nhật script_text"


def test_script_local_CO_thi_KHONG_dung_ban_goc(tmp_path):
    """User chốt: chỉ chép khi bản trong chương RỖNG. Chương đang chạy bình
    thường phải giữ self-contained — sửa file gốc KHÔNG được âm thầm đổi
    chương đã dựng dở."""
    from autoedit.project import doc_script

    p = _du_an(tmp_path, "bản trong chương", "bản gốc ĐÃ SỬA")
    assert doc_script(p) == "bản trong chương", \
        "bản gốc đè lên bản local dù local không rỗng"


def test_ca_HAI_deu_rong_thi_bao_RO_khau_hong(tmp_path):
    """Không được để align đổ lỗi "transcript rỗng" — đó là khâu SAU. Phải
    chỉ đúng khâu hỏng và nói làm gì tiếp."""
    from autoedit.project import doc_script

    p = _du_an(tmp_path, "", "")
    with pytest.raises(RuntimeError) as e:
        doc_script(p)
    loi = str(e.value).lower()
    assert "kịch bản" in loi and "rỗng" in loi, f"lời báo không nêu script rỗng: {e.value}"
    assert "e.txt" in loi or str(tmp_path).lower() in loi, \
        f"lời báo không chỉ ra file nào cần nạp: {e.value}"


def test_ban_goc_MAT_thi_van_bao_ro(tmp_path):
    """NAS rút dây / file bị xoá — không được ném lỗi khó hiểu."""
    from autoedit.project import doc_script

    p = _du_an(tmp_path, "", None)
    with pytest.raises(RuntimeError) as e:
        doc_script(p)
    assert "kịch bản" in str(e.value).lower(), e.value


def test_TAO_CHUONG_script_rong_bi_CHAN_ngay(tmp_path):
    """Lỗi gốc: chương sinh ra đã hỏng. Chặn tại chỗ tạo thì user biết ngay
    lúc nộp tập, không phải mò sau 15 lần bấm Phân tích."""
    from autoedit.project import create_project

    sc = tmp_path / "E.txt"
    sc.write_text("", encoding="utf-8")
    vo = tmp_path / "E.mp3"
    vo.write_bytes(b"\x00" * 2048)
    with pytest.raises(ValueError) as e:
        create_project(sc, vo, out_dir=tmp_path / "projects")
    assert "rỗng" in str(e.value).lower(), \
        f"tạo chương với script rỗng mà không báo rõ: {e.value}"


def test_TAO_CHUONG_script_chi_co_khoang_trang_cung_bi_chan(tmp_path):
    """File 3 byte toàn xuống dòng cũng là rỗng — kiểm nội dung, không kiểm
    kích thước."""
    from autoedit.project import create_project

    sc = tmp_path / "E.txt"
    sc.write_text("\n\n \n", encoding="utf-8")
    vo = tmp_path / "E.mp3"
    vo.write_bytes(b"\x00" * 2048)
    with pytest.raises(ValueError) as e:
        create_project(sc, vo, out_dir=tmp_path / "projects")
    assert "rỗng" in str(e.value).lower(), e.value


def _du_an_day_du(tmp: Path, chu_local: str, chu_goc: str) -> Path:
    """Chương đã align xong nhưng transcript RỖNG — đúng trạng thái chương E."""
    p = _du_an(tmp, chu_local, chu_goc)
    (p / "media" / "voice_master.wav").write_bytes(b"RIFF" + b"\x00" * 2048)
    (p / "transcript.json").write_text(json.dumps({
        "match_ratio": 0.0, "words": [],
        "warnings": ["Script và voice lệch nhau: chỉ 0% từ khớp trực tiếp"],
    }, ensure_ascii=False), encoding="utf-8")
    return p


def test_PHAN_TICH_bao_dung_khau_hong_va_TU_NAP_LAI_script(tmp_path):
    """Ca user gặp: bấm Phân tích 15 lần, mỗi lần chỉ nhận "transcript rỗng —
    chạy align trước". Câu đó ĐÚNG về triệu chứng nhưng SAI về nguyên nhân:
    align đã chạy rồi (`stages.align = done`), nó rỗng vì script rỗng.

    Sau vá: `runner` phải (a) tự nạp lại kịch bản từ bản gốc, (b) nói rõ phải
    chạy Align lại — vì chương này không có `.srt` nên align cần whisper, không
    chạy ngầm trong một request được.
    """
    from autoedit.offline import runner as orun

    p = _du_an_day_du(tmp_path, "", BAI)
    with pytest.raises(RuntimeError) as e:
        orun.phan_tich(p)
    loi = str(e.value)
    assert "align" in loi.lower(), f"không chỉ ra bước tiếp theo: {loi}"
    assert "kịch bản" in loi.lower() or "script" in loi.lower(), \
        f"không nói nguyên nhân thật (script rỗng): {loi}"
    # (a) đã tự nạp lại -> lần chạy Align tới sẽ có chữ THẬT
    assert (p / "inputs" / "script.txt").read_text(encoding="utf-8") == BAI, \
        "chưa tự nạp lại kịch bản từ bản gốc"


def test_PHAN_TICH_script_van_rong_that_thi_bao_KHAC(tmp_path):
    """Script rỗng cả hai nơi là ca KHÁC — phải bảo user đi nạp kịch bản, chứ
    không bảo chạy align (chạy lại cũng rỗng)."""
    from autoedit.offline import runner as orun

    p = _du_an_day_du(tmp_path, "", "")
    with pytest.raises(RuntimeError) as e:
        orun.phan_tich(p)
    assert "kịch bản" in str(e.value).lower(), str(e.value)


def test_transcript_rong_ma_SCRIPT_KHONG_rong_thi_bao_khac(tmp_path):
    """Không được đổ mọi ca transcript rỗng cho script. Script có chữ mà
    transcript vẫn rỗng là chuyện khác (align dở dang / voice lệch hẳn) —
    báo sai nguyên nhân là đẩy người dùng đi sai hướng, đúng lỗi vừa vá."""
    from autoedit.offline import runner as orun

    p = _du_an_day_du(tmp_path, BAI, BAI)
    with pytest.raises(RuntimeError) as e:
        orun.phan_tich(p)
    loi = str(e.value).lower()
    assert "không rỗng" in loi, f"vẫn đổ lỗi cho kịch bản: {e.value}"
    assert "align" in loi, e.value
