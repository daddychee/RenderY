"""Sổ nguồn gốc footage — xuất cạnh draft CapCut (RenderY).

User chốt 29/08/2026: mỗi clip phải ghi **nguồn + ID**. Lý do là nỗi lo có thật với
padoma: *"kho của họ đều là đi cắt từ nguồn không legal... tôi không biết được tỉ trọng
và đâu là đoạn cắt"*. Trộn rồi thì không gỡ ra được nữa.

`project.json` đã có đủ dữ liệu (ShotPick.asset_key/source/licensing_flag), nhưng nó
nằm trong project chứ không đi cùng draft. Editor mở draft trên máy khác thì mất dấu.
Module này xuất 2 file NGAY CẠNH draft:

- `nguon_footage.json` — từng clip: nguồn, ID, đường dẫn, cờ pháp lý
- `nguon_footage.txt`  — bảng tỉ trọng đọc bằng mắt, cảnh báo nếu ytref vượt trần

Nhóm nguồn: stock (free) · sub (đã trả tiền) · ytref (CẮT — không có quyền) · local · other.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# Trần cảnh báo cho footage cắt từ YouTube — cùng số với gate C8 (REF_CAP_RATIO)
YTREF_WARN_RATIO = 0.15

_GROUP_OF = {
    "pexels": "stock", "pixabay": "stock",
    "envato": "sub", "vecteezy": "sub", "artlist": "sub",
    "ytref": "ytref", "local": "local",
    # refvid: video CÓ SẴN của user, đặt thẳng trong thư mục chương (02/09).
    # Tách khỏi ytref vì tình trạng pháp lý KHÁC HẲN — đây là tư liệu của mình.
    "refvid": "refvid",
}
_GROUP_LABEL = {
    "stock": "Stock free (dùng thương mại được)",
    "sub": "Subscription (đã trả tiền)",
    "ytref": "CẮT từ YouTube (KHÔNG có quyền)",
    "refvid": "Video có sẵn của bạn (cắt theo transcript)",
    "local": "Kho riêng",
    "other": "Khác",
}


def group_of(asset_key: str) -> str:
    """`pexels:123` -> stock · `ytref:ID@t=1-5` -> ytref · path trần -> local."""
    if not asset_key:
        return "other"
    prefix = asset_key.split(":", 1)[0] if ":" in asset_key else ""
    # Path Windows "C:\kho\a.mp4" có dấu ':' nhưng prefix là 1 chữ cái -> là local
    if len(prefix) <= 1:
        return "local"
    return _GROUP_OF.get(prefix.lower(), "other")


def collect_rows(project) -> list[dict]:
    """Mỗi shot có asset -> 1 dòng sổ. Bỏ beat chưa có footage (needs_human)."""
    rows: list[dict] = []
    beats = {b.beat_id: b for b in project.beats}
    for shot in project.shots:
        if not shot.asset_path:
            continue
        beat = beats.get(shot.beat_id)
        dur = round((beat.end - beat.start), 2) if beat else 0.0
        rows.append({
            "beat_id": shot.beat_id,
            "chapter": getattr(beat, "chapter", 0) if beat else 0,
            "asset_key": shot.asset_key,
            "group": group_of(shot.asset_key),
            "source": shot.source,
            "channel": shot.source_channel,
            "file": Path(shot.asset_path).name,
            "duration": dur,
            "licensing_flag": bool(shot.licensing_flag),
            "peak": bool(shot.peak),
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    """Tỉ trọng theo nhóm nguồn — nhìn 1 dòng biết ngay % footage cắt."""
    total = sum(r["duration"] for r in rows) or 1.0
    out: dict[str, dict] = {}
    for r in rows:
        g = out.setdefault(r["group"], {"clips": 0, "seconds": 0.0})
        g["clips"] += 1
        g["seconds"] += r["duration"]
    for g in out.values():
        g["seconds"] = round(g["seconds"], 1)
        g["ratio"] = round(g["seconds"] / total, 4)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["seconds"]))


def render_text(rows: list[dict], summary: dict, project_id: str = "") -> str:
    """Bảng đọc bằng mắt — thứ editor thật sự mở ra xem."""
    total = sum(r["duration"] for r in rows)
    lines = [
        f"SỔ NGUỒN FOOTAGE — {project_id}".rstrip(" —"),
        f"Xuất: {datetime.now(timezone.utc).astimezone().strftime('%d/%m/%Y %H:%M')}",
        f"Tổng: {len(rows)} clip · {total:.1f}s",
        "",
    ]
    for g, st in summary.items():
        lines.append(f"  {st['ratio']:>6.1%}  {st['seconds']:>7.1f}s  {st['clips']:>3} clip"
                     f"   {_GROUP_LABEL.get(g, g)}")

    yt = summary.get("ytref")
    if yt:
        lines += ["", f"  ⚠ Footage cắt từ YouTube: {yt['ratio']:.1%}"]
        if yt["ratio"] > YTREF_WARN_RATIO:
            lines.append(f"  ⚠⚠ VƯỢT TRẦN {YTREF_WARN_RATIO:.0%} — cân nhắc thay bớt bằng stock/subscription")

    flagged = [r for r in rows if r["licensing_flag"]]
    if flagged:
        lines += ["", f"  ⚠ {len(flagged)} clip cần người duyệt bản quyền:"]
        lines += [f"      beat {r['beat_id']:>3}  {r['asset_key']}" for r in flagged[:20]]

    lines += ["", "-" * 78, "CHI TIẾT TỪNG CLIP", "-" * 78,
              f"{'beat':>5} {'ch':>3} {'nhóm':<6} {'giây':>6}  nguồn / ID"]
    for r in sorted(rows, key=lambda r: r["beat_id"]):
        mark = "⭐" if r["peak"] else ("⚠" if r["licensing_flag"] else " ")
        lines.append(f"{r['beat_id']:>5} {r['chapter']:>3} {r['group']:<6} "
                     f"{r['duration']:>6.1f} {mark} {r['asset_key']}")
    return "\n".join(lines) + "\n"


def write_sourcebook(project, draft_dir: Path) -> tuple[Path, Path]:
    """Xuất sổ JSON + bảng text cạnh draft. Trả (json_path, txt_path)."""
    draft_dir = Path(draft_dir)
    draft_dir.mkdir(parents=True, exist_ok=True)
    rows = collect_rows(project)
    summary = summarize(rows)

    json_path = draft_dir / "nguon_footage.json"
    json_path.write_text(json.dumps(
        {"project_id": project.project_id,
         "exported_at": datetime.now(timezone.utc).isoformat(),
         "summary": summary, "clips": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")

    txt_path = draft_dir / "nguon_footage.txt"
    txt_path.write_text(render_text(rows, summary, project.project_id), encoding="utf-8")
    return json_path, txt_path
