"""Gom kết quả dựng ra thư mục `Compose Timeline` trên NAS — bước cuối của 1 job.

Flow user (docs/TICH_HOP_CRM.md): nhân sự nộp folder chương -> máy chủ dựng ->
*"File được xuất ở trong thư mục Compose Timeline cùng folder bao gồm file timeline
và footage đã được phân theo từng đơn vị chapter"* -> nhân sự copy cả thư mục về máy.

Vì sao phải gom: project sống ở `autoedit/projects/<id>/` trên ổ local, draft CapCut
lại nằm ở draft root của máy. Nhân sự không biết 2 chỗ đó, và cũng không nên vào.
Gom về MỘT thư mục trên NAS đúng tên công việc họ đặt.

```
Compose Timeline/LI070-Han-Quoc/
├── ch01/
│   ├── draft/            ← draft CapCut chương 1 (copy cả thư mục vào CapCut là mở được)
│   ├── footage/          ← clip đã tải cho chương này
│   ├── nguon_footage.txt ← sổ nguồn gốc (nguồn + ID từng clip)
│   └── report.html       ← bảng duyệt của editor
├── ch02/ ...
└── DOC_TRUOC.txt         ← tóm tắt: chương nào xong, thiếu clip ở đâu
```

Copy (không move) vì project gốc còn để chạy lại/đối chiếu.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class ComposeError(RuntimeError):
    """Không gom được — job vẫn tính là xong phần dựng, chỉ báo lỗi bước giao."""


def _copytree(src: Path, dst: Path) -> int:
    """Copy cây thư mục, trả số file. Bỏ qua file đang bị khoá thay vì chết cả job."""
    if not src.is_dir():
        return 0
    n = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        target = dst / item.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(item, target)
            n += 1
        except OSError:
            pass          # file đang mở/khoá — bỏ qua, phần còn lại vẫn giao được
    return n


def _load_project(project_dir: Path) -> Optional[dict]:
    f = project_dir / "project.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def compose_chapter(project_dir: Path, dest: Path) -> dict:
    """Gom 1 chương: draft + footage + sổ nguồn + report. Trả tóm tắt để ghi DOC_TRUOC."""
    proj = _load_project(Path(project_dir))
    if proj is None:
        raise ComposeError(f"Không đọc được project.json trong {project_dir}")

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out = {"project_id": proj.get("project_id", ""), "draft": 0, "footage": 0,
           "thieu_clip": 0, "canh_bao": []}

    # 1) Draft CapCut — thứ nhân sự copy vào CapCut
    draft = proj.get("draft_path") or ""
    if draft and Path(draft).is_dir():
        out["draft"] = _copytree(Path(draft), dest / "draft")
        # Sổ nguồn gốc nằm cạnh draft (R6) -> đưa lên cấp chương cho dễ thấy
        for ten in ("nguon_footage.txt", "nguon_footage.json"):
            f = Path(draft) / ten
            if f.is_file():
                shutil.copy2(f, dest / ten)
    else:
        out["canh_bao"].append("chưa có draft CapCut")

    # 2) Footage đã tải — phân theo chương (chính là assets/ của project)
    out["footage"] = _copytree(Path(project_dir) / "assets", dest / "footage")

    # 3) Bản Premiere/Resolve — dịch từ CHÍNH draft vừa copy ở trên, nên đường dẫn
    # media trỏ vào `draft/materials/` NGAY TRONG thư mục giao. Dịch từ draft gốc
    # trên ổ local thì nhân sự mang thư mục về máy là mất sạch media.
    if out["draft"]:
        try:
            from autoedit.packager.fcpxml import xuat_fcpxml

            cb = xuat_fcpxml(dest / "draft", dest / f"{dest.name}.fcpxml",
                             ten_seq=dest.name)
            out["fcpxml"] = 1
            out["canh_bao"].extend(cb)
        except Exception as exc:
            # Không xuất được bản Premiere KHÔNG huỷ bản CapCut — chỉ báo.
            out["canh_bao"].append(f"chưa xuất được bản Premiere (.fcpxml): {exc}")

    # 3) Report cho editor duyệt
    report = proj.get("report_path") or ""
    if report and Path(report).is_file():
        shutil.copy2(report, dest / "report.html")

    # 4) Đếm beat chưa có footage — con số editor cần biết trước khi mở draft
    shots = proj.get("shots") or []
    out["thieu_clip"] = sum(1 for s in shots if not s.get("asset_path"))
    out["so_beat"] = len(shots)

    for st, rec in (proj.get("stages") or {}).items():
        for w in (rec.get("warnings") or [])[:3]:
            out["canh_bao"].append(f"{st}: {w}")
    return out


def write_readme(dest: Path, job_folder: str, chapters: list[dict],
                 xong_het: bool = True) -> Path:
    """DOC_TRUOC.txt — thứ nhân sự mở đầu tiên khi lấy thư mục về.

    `xong_het=False`: đang giao dần, tập CHƯA đủ chương. Phải ghi rõ ở dòng đầu —
    thấy thư mục có file mà tưởng xong rồi copy về thì thiếu chương lúc nào không hay.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")
    lines = [
        f"KẾT QUẢ DỰNG — {Path(job_folder).name}",
        f"Xong lúc: {now}" if xong_het else
        f"⏳ ĐANG CHẠY — cập nhật {now}. Đã xong {len(chapters)} chương, "
        f"CÒN CHƯƠNG ĐANG DỰNG. Chương nào có thư mục là dùng được ngay; "
        f"đợi dòng này đổi thành 'Xong lúc' rồi hãy copy CẢ TẬP về.",
        "",
        "CÁCH DÙNG",
        "  1. Copy CẢ THƯ MỤC này về máy cá nhân.",
        "  2. Mỗi chương có thư mục riêng. Chọn MỘT trong hai cách mở:",
        "       • CapCut   -> copy thư mục draft/ vào thư mục draft của CapCut rồi mở",
        "       • Premiere -> mở file .fcpxml (File > Import). DaVinci Resolve cũng mở được.",
        "     Hai bản CÙNG một timeline, dùng bản nào cũng được.",
        "  3. Còn lại trong thư mục chương:",
        "       footage/   -> clip đã tải sẵn cho chương này",
        "       report.html-> bảng duyệt: xem nhanh chương này dùng clip gì",
        "       nguon_footage.txt -> nguồn gốc từng clip (dùng khi cần đối chiếu bản quyền)",
        "",
        "  LƯU Ý bản Premiere: chữ trên màn hình thành MARKER (không phải title có",
        "  kiểu dáng) và hiệu ứng Ken Burns không mang sang — bản CapCut mới đủ.",
        "",
        "TỪNG CHƯƠNG",
    ]
    tong_thieu = 0
    for ch in chapters:
        thieu = ch.get("thieu_clip", 0)
        tong_thieu += thieu
        trang_thai = "OK" if not thieu else f"THIẾU {thieu}/{ch.get('so_beat', 0)} clip"
        lines.append(f"  {ch['ten']:<14} {trang_thai:<22} "
                     f"{ch.get('footage', 0)} file footage")
        for w in ch.get("canh_bao", [])[:3]:
            lines.append(f"       ⚠ {w}")
    if tong_thieu:
        lines += ["",
                  f"⚠ Còn {tong_thieu} chỗ chưa có footage. Trong CapCut chúng hiện là ảnh",
                  "  'EDITOR: ĐẮP FOOTAGE Ở ĐÂY' — thay bằng clip phù hợp rồi dựng tiếp."]
    p = dest / "DOC_TRUOC.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def thu_muc_giao(tap: Path, outbox: Optional[Path] = None) -> Path:
    """Nơi giao kết quả. Mặc định NGAY TRONG thư mục tập: `<tập>/RenderY/Compose Timeline/`.

    Để cạnh nguồn thay vì gom về một chỗ chung: nhân sự đã mở thư mục tập để đặt
    kịch bản + voice, lấy kết quả ngay tại đó là ngắn nhất — và mỗi tập tự mang
    kết quả của mình khi copy/lưu trữ.
    """
    from autoedit.web.chapters import THU_MUC_GIAO, thu_muc_rendery

    if outbox is not None:
        return Path(outbox) / Path(tap).name
    return thu_muc_rendery(tap) / THU_MUC_GIAO


def compose_job(job_folder: Path, project_dirs: list[Path],
                outbox: Optional[Path] = None) -> Path:
    """Gom cả job (nhiều chương) về thư mục giao.

    `project_dirs` theo ĐÚNG THỨ TỰ chương (H → C1..Cn → E). Tên thư mục chương lấy
    từ MÃ CHƯƠNG nhân sự đặt (H, C1, E) để nhận ra ngay, không phải project_id máy sinh.
    """
    job_folder = Path(job_folder)
    dest_root = thu_muc_giao(job_folder, outbox)
    if dest_root.exists():
        # Dựng lại lần 2: dọn sạch để không lẫn kết quả cũ với mới
        shutil.rmtree(dest_root, ignore_errors=True)
    dest_root.mkdir(parents=True, exist_ok=True)

    from autoedit.web.worker import chapters_of

    ten_chuong = [c.name for c in chapters_of(job_folder)]
    tom_tat: list[dict] = []
    for i, pdir in enumerate(project_dirs):
        ten = ten_chuong[i] if i < len(ten_chuong) else f"ch{i + 1:02d}"
        tom_tat.append(_giao_mot(Path(pdir), dest_root, ten))

    write_readme(dest_root, str(job_folder), tom_tat)
    return dest_root


def _giao_mot(pdir: Path, dest_root: Path, ten: str) -> dict:
    """Đổ 1 chương ra thư mục giao. Lỗi -> ghi vào tóm tắt, KHÔNG ném lên."""
    try:
        info = compose_chapter(Path(pdir), dest_root / ten)
    except ComposeError as exc:
        info = {"draft": 0, "footage": 0, "thieu_clip": 0,
                "so_beat": 0, "canh_bao": [str(exc)]}
    info["ten"] = ten
    return info


def compose_dan(job_folder: Path, ten_chuong: str, project_dir: Path,
                tom_tat: list[dict], xong_het: bool = False,
                outbox: Optional[Path] = None) -> Path:
    """Giao NGAY một chương vừa dựng xong, không đợi cả tập.

    31/08 (user hỏi "C7 C8 đã trả ra kết quả chưa?"): C7/c8 dựng xong từ lâu nhưng
    bước giao chỉ chạy MỘT LẦN ở cuối job, nên nhân sự phải ngồi chờ chương chậm
    nhất mới lấy được thứ đã xong. Giao dần thì mở C7 làm ngay trong khi C9 còn chạy.

    `tom_tat` là danh sách tích luỹ qua các lần gọi — README viết lại mỗi lần để luôn
    khớp với những gì ĐANG có trong thư mục. Chưa xong hết thì README ghi rõ còn chạy,
    tránh cảnh nhân sự tưởng tập đã đủ chương.
    """
    dest_root = thu_muc_giao(Path(job_folder), outbox)
    dest_root.mkdir(parents=True, exist_ok=True)
    tom_tat.append(_giao_mot(Path(project_dir), dest_root, ten_chuong))
    write_readme(dest_root, str(job_folder), tom_tat, xong_het=xong_het)
    return dest_root / ten_chuong


def don_thu_muc_giao(job_folder: Path, outbox: Optional[Path] = None) -> None:
    """Xoá thư mục giao cũ trước khi bắt đầu giao dần (khỏi lẫn kết quả lần trước)."""
    dest_root = thu_muc_giao(Path(job_folder), outbox)
    if dest_root.exists():
        shutil.rmtree(dest_root, ignore_errors=True)
