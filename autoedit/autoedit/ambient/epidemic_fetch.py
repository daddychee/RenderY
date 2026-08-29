"""Nạp SFX Epidemic vào kho ambient per-niche — `autoedit epidemic-sfx`.

Tách khỏi epidemic.py (client thuần API) để chỗ này chỉ lo NGHIỆP VỤ nạp kho:
kind nào -> tìm term gì -> tải mấy file -> giao library.import_from_manifest.

Nguồn ghi vào records: `artlist_url` = link Epidemic (truy license ngược, cùng cột
với kho Artlist cũ — KHÔNG đẻ cột mới, THU_VIEN_NHAC.md mục 6).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from autoedit.ambient.epidemic import EpidemicClient, EpidemicError, SoundEffect
from autoedit.ambient.library import (
    MANIFEST_FILE,
    import_from_manifest,
    list_variants,
    niche_kinds,
)

# SFX chủ thể dài quá thành ambient nền, ngắn quá thì hụt — khớp cách dùng ở
# schedule.choose_subject_files (chèn tại beat, không loop).
DEFAULT_MIN_S = 1.0
DEFAULT_MAX_S = 30.0
WEB_URL = "https://www.epidemicsound.com/sound-effects/tracks/{id}/"


@dataclass
class FetchPlan:
    """Một dòng kế hoạch: kind <- term, lấy tối đa n file."""
    kind: str
    term: str
    limit: int = 3


# Từ CHUNG CHUNG không đủ để nhận diện chủ thể — "Goose, Call" mà khớp `call` thì
# penguin.wav sẽ kêu tiếng ngỗng (test bắt được 2026-07-18). Chỉ dùng để LỌC term,
# không bao giờ dùng để khớp.
_GENERIC_WORDS = frozenset({
    "call", "calls", "sound", "sounds", "noise", "audio", "effect", "effects",
    "bird", "birds", "animal", "animals", "engine", "motor", "moving", "movement",
    "close", "loud", "single", "group", "the", "and",
})


def title_matches(title: str, kind: str, term: str) -> bool:
    """Title có nhắc đúng CHỦ THỂ đang tìm không?

    LƯỚI LOÀI (đo thật 2026-07-18): search Epidemic ngữ nghĩa lỏng, cố lấy đủ `limit`
    nên vét sang loài họ hàng — tìm `penguin` ra NGỖNG/HẢI ÂU/vịt đồ chơi, `vulture` ra
    currawong/mallard. Nạp mù thì penguin.wav kêu tiếng vịt = tái lập RD-89.

    Luật: kind (hoặc từ RIÊNG của term) phải có mặt trong title. Từ chung chung bị
    loại khỏi phép khớp — nếu không "penguin call" sẽ khớp "Goose, Call". Bỏ đuôi 's'
    để "seagulls" khớp "seagull". Kind chuyên biệt (snowmobile/escalator) vốn đã đúng
    4/4 nên lưới không đụng tới.
    """
    low = title.lower()
    words = [kind.replace("_", " ").lower()]
    words += [w for w in term.lower().split()
              if len(w) > 2 and w not in _GENERIC_WORDS]
    for w in words:
        w = w.strip()
        if w and (w in low or w.rstrip("s") in low):
            return True
    return False


@dataclass
class FetchResult:
    downloaded: list[str] = field(default_factory=list)   # "<kind> <- <title>"
    skipped: list[str] = field(default_factory=list)      # kind đã đủ file
    failed: list[tuple[str, str]] = field(default_factory=list)
    imported: list[str] = field(default_factory=list)     # từ ImportResult
    import_failed: list[tuple[str, str]] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)     # lưới loài loại (title lệch)


def parse_plan(specs: list[str]) -> list[FetchPlan]:
    """`"kind=term"` hoặc `"kind=term:n"` -> FetchPlan. Term rỗng -> dùng chính kind."""
    plans = []
    for spec in specs:
        if "=" not in spec:
            plans.append(FetchPlan(kind=spec.strip(), term=spec.strip()))
            continue
        kind, _, rest = spec.partition("=")
        term, sep, n = rest.rpartition(":")
        if sep and n.strip().isdigit():
            plans.append(FetchPlan(kind.strip(), term.strip() or kind.strip(), int(n)))
        else:
            plans.append(FetchPlan(kind.strip(), rest.strip() or kind.strip()))
    return plans


def fetch_to_niche(
    plans: list[FetchPlan],
    niche_path: Path,
    *,
    filetype: str = "MP3",
    min_s: float = DEFAULT_MIN_S,
    max_s: float = DEFAULT_MAX_S,
    target_per_kind: int | None = None,
    client: EpidemicClient | None = None,
    dry_run: bool = False,
    strict: bool = True,
) -> FetchResult:
    """Tải SFX theo kế hoạch rồi nạp vào kho niche (chuẩn hóa WAV PCM 48k).

    target_per_kind: kind đã có ≥ ngần này biến thể thì BỎ QUA (khỏi tải trùng khi
    chạy lại). None = luôn tải.
    strict: bật LƯỚI LOÀI (title_matches) — loại kết quả lệch loài. Tắt khi cố ý gom
    rộng (vd kind rổ vét `animal_wildlife`).
    """
    client = client or EpidemicClient()
    niche_path = Path(niche_path)
    result = FetchResult()
    valid = set(niche_kinds(niche_path))
    entries: list[dict] = []
    tmp = Path(tempfile.mkdtemp(prefix="epidemic_sfx_"))

    for plan in plans:
        if plan.kind not in valid:
            result.failed.append((plan.kind, f"kind không hợp lệ với niche này "
                                             f"(khai thêm trong subject_rules.yaml nếu cần)"))
            continue
        if target_per_kind is not None and len(list_variants(plan.kind, niche_path)) >= target_per_kind:
            result.skipped.append(f"{plan.kind} (đã đủ {target_per_kind})")
            continue
        try:
            hits = client.search(plan.term, limit=plan.limit, min_s=min_s, max_s=max_s)
        except EpidemicError as exc:
            result.failed.append((plan.kind, str(exc)))
            continue
        if not hits:
            result.failed.append((plan.kind, f"không thấy SFX nào cho '{plan.term}'"))
            continue
        for se in hits:
            if strict and not title_matches(se.title, plan.kind, plan.term):
                result.rejected.append(f"{plan.kind} ✗ {se.title}")
                continue
            if dry_run:
                result.downloaded.append(f"{plan.kind} <- {se.title} ({se.duration_s:.1f}s)")
                continue
            raw = tmp / f"{se.slug}.{filetype.lower()}"
            try:
                client.download(se, raw, filetype=filetype)
            except EpidemicError as exc:
                result.failed.append((plan.kind, str(exc)))
                continue
            entries.append({
                "file": raw.name, "kind": plan.kind,
                "artlist_url": WEB_URL.format(id=se.id), "title": se.title,
            })
            result.downloaded.append(f"{plan.kind} <- {se.title} ({se.duration_s:.1f}s)")

    if dry_run or not entries:
        return result

    manifest = tmp / MANIFEST_FILE
    manifest.write_text(yaml.safe_dump({"ambient": entries}, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
    imported = import_from_manifest(manifest, tmp, niche_path)
    result.imported = imported.imported
    result.import_failed = imported.failed
    return result
