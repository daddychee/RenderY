"""Stage ENRICH (P2B) — TẮT từ 05/09 (user bỏ graphic tự render).

Trước đây stage này gọi LLM sinh chart bổ sung + info card (đều là graphic tự
render) gắn vào beat, chờ người duyệt qua enrich_review.json. User bỏ toàn bộ
graphic (chart/card xấu, không work) nên stage thành NO-OP: không gọi LLM, không
tốn tiền, vẫn ghi stage DONE để pipeline gọi `--enrich` không gãy.
Toàn bộ logic cũ (propose + validate + review file): xem git history file này.
"""

from __future__ import annotations

from datetime import datetime, timezone

from autoedit.director.client import DirectorClient
from autoedit.project import Project, Stage, StageRecord, StageStatus


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_enrich(project: Project, client: DirectorClient, max_per_60s: float = 1.0,
               use_web: bool = False) -> Project:
    direct = project.stages.get(Stage.DIRECT)
    if direct is None or direct.status != StageStatus.DONE or not project.beats:
        raise RuntimeError("Stage direct chưa xong — chạy `autoedit direct` trước.")

    record = StageRecord.running()
    record.warnings.append("enrich bỏ qua: graphic (chart/info-card) đã tắt 05/09")
    record.status = StageStatus.DONE
    record.completed_at = _now()
    project.stages[Stage.ENRICH] = record
    project.save()
    return project
