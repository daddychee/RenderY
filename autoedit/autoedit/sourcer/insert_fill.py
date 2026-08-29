"""M4c — FOOTAGE THẬT cho đoạn chèn Δ (thay slug giữ chỗ của M2/M4b).

User chốt 2026-07-21: nguồn LAI — clip trong folder editor đưa (`insert --footage`)
dùng TRƯỚC, thiếu thì KHO đắp bù theo PROMPT editor khai (`insert --prompt`, NÃO dịch
sang query kho lúc khai); cỡ cảnh do GLM tag. Luật nội dung e2 §5: ô HOLD (hình giữ
lâu) = cảnh RỘNG/nhiều chi tiết, ô RUN = cận/chi tiết.

Chọn ở SOURCE (sau mọi pick beat/thở — used_in_video đầy đủ, chống NAM CHÂM kho),
ghi `InsertSpec.footage_picks` theo INDEX Ô của lưới (không lưu mốc tuyệt đối: cut
chạy lại là timeline dịch, còn lưới chỉ phụ thuộc dur+nhịp+seed nên index ổn định —
cùng `cov.insert_grids` với assemble). Ô không có pick / pick hỏng -> slug như M4b
(fail-open, không bao giờ chặn dựng).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from pydantic import BaseModel, field_validator

from autoedit.project import InsertClip, InsertPick, Project

# Cỡ cảnh hợp ô HOLD (cảnh rộng đáng ngắm) vs RUN (cận/chi tiết). medium xếp phe RUN
# (e2 §5: "hình ngắn = cận/chi tiết"); "" (tag lỗi/chưa tag) = trung tính, dùng sau cùng.
WIDE_SIZES = {"wide", "aerial"}
RUN_SIZES = {"close_up", "extreme_close_up", "medium"}

# Kho đắp bù: trần ứng viên mỗi query (đủ chọn theo cỡ cảnh, không quét cả kho).
LIBRARY_PER_QUERY = 40

# --- Cổng LOCATION cho kho đắp bù (user chốt 2026-07-21 sau V13: Δ video Oman dính
# clip Vietnam/Bosnia/Djibouti qua query chữ). Geo-gate PA2 chỉ gác cây "Khu Vực..."
# — mẻ nạp (nap\EXxxx) là phi-địa-lý nên lọt hết; nhưng TÊN NƯỚC nằm ngay trong tên
# video nguồn/tag. Luật: ứng viên mà siêu dữ liệu nhắc tên một QUỐC GIA script không
# nhắc -> loại khỏi pool Δ. Match theo TOKEN (không blob-substring: "oman" ⊂ "romance").
# Clip HINH THO / --footage do editor TỰ CHỌN -> miễn cổng. Chỉ áp cho pool Δ, KHÔNG
# đụng phễu beat thường (đường đó đã có geo-gate + NÃO chấm nghĩa).
_COUNTRY_TOKENS: tuple[tuple[str, ...], ...] = tuple(
    tuple(name.split()) for name in (
        "afghanistan albania algeria angola argentina armenia australia austria "
        "azerbaijan bahrain bangladesh belarus belgium belize benin bhutan bolivia "
        "bosnia botswana brazil brunei bulgaria burundi cambodia cameroon canada "
        "chad chile china colombia congo croatia cuba cyprus denmark djibouti "
        "ecuador egypt eritrea estonia eswatini ethiopia fiji finland france gabon "
        "gambia georgia germany ghana greece greenland guatemala guinea guyana "
        "haiti honduras hungary iceland india indonesia iran iraq ireland israel "
        "italy jamaica japan jordan kazakhstan kenya kiribati kosovo kuwait "
        "kyrgyzstan laos latvia lebanon lesotho liberia libya lithuania luxembourg "
        "madagascar malawi malaysia maldives mali malta mauritania mauritius mexico "
        "moldova mongolia montenegro morocco mozambique myanmar namibia nepal "
        "nicaragua niger nigeria norway oman pakistan palau panama paraguay peru "
        "philippines poland portugal qatar romania russia rwanda samoa senegal "
        "serbia seychelles singapore slovakia slovenia somalia spain sudan suriname "
        "sweden switzerland syria taiwan tajikistan tanzania thailand togo tonga "
        "tunisia turkey turkmenistan tuvalu uganda ukraine uruguay uzbekistan "
        "vanuatu venezuela vietnam yemen zambia zimbabwe scotland wales england"
    ).split()
) + (
    # tên nhiều từ + biến thể hay gặp trong tên video/tag
    ("viet", "nam"), ("saudi", "arabia"), ("sri", "lanka"), ("south", "korea"),
    ("north", "korea"), ("new", "zealand"), ("costa", "rica"), ("el", "salvador"),
    ("papua", "new", "guinea"), ("united", "states"), ("united", "kingdom"),
    ("czech", "republic"), ("dominican", "republic"), ("hong", "kong"),
    ("burkina", "faso"), ("sierra", "leone"), ("south", "africa"),
    ("south", "sudan"), ("timor", "leste"), ("cape", "verde"), ("usa",), ("uae",),
    ("emirates",), ("herzegovina",), ("czechia",), ("korea",), ("america",),
    ("netherlands", ), ("holland",),
)


def _norm_tokens(text: str) -> list[str]:
    """Bỏ dấu + thường hóa + tách token alnum — khớp tên nước trong path/tag/mô tả."""
    import re
    import unicodedata

    s = unicodedata.normalize("NFD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", s.lower())


def foreign_location(row: dict, script_blob: str) -> str:
    """Tên nước LẠ đầu tiên tìm thấy trong siêu dữ liệu ứng viên ('' = qua cổng).

    script_blob = _blob(script_text). Nước có trong script -> hợp lệ (video Oman dùng
    mọi cảnh Oman); metadata không nhắc nước nào -> qua (fail-open, không đẻ cửa loại
    cho clip không nhãn — cổng chỉ chặn ca CHẮC CHẮN sai như phễu c5)."""
    meta = " ".join(str(row.get(k) or "") for k in
                    ("source_video", "folder_path", "subject", "description"))
    tags = row.get("tags")
    if isinstance(tags, (list, tuple)):
        meta += " " + " ".join(str(t) for t in tags)
    toks = _norm_tokens(meta)
    tok_set = set(toks)
    joined = "\x00" + "\x00".join(toks) + "\x00"   # đệm 2 đầu: cụm chỉ khớp TRỌN token
    for country in _COUNTRY_TOKENS:
        if len(country) == 1:
            hit = country[0] in tok_set
        else:
            hit = ("\x00" + "\x00".join(country) + "\x00") in joined
        if hit and "".join(country) not in script_blob:
            return " ".join(country)
    return ""


class InsertFootageQueries(BaseModel):
    """Output NÃO dịch prompt editor -> query kho (NT4: LLM chỉ trả NGHĨA)."""

    queries: list[str]

    @field_validator("queries")
    @classmethod
    def _clean(cls, v: list[str]) -> list[str]:
        out = [" ".join(str(q).lower().split()) for q in v]
        out = [q for q in out if q and len(q.split()) <= 5]
        if not out:
            raise ValueError("cần ≥1 query (1-5 từ tiếng Anh)")
        return list(dict.fromkeys(out))[:6]


def queries_from_prompt(prompt: str, vocab_lines: str, client) -> list[str]:
    """Dịch prompt tiếng Việt của editor -> query tiếng Anh khớp vocab tag kho (C4).

    client = ClaudeCodeDirectorClient (injectable cho test). Lỗi -> caller quyết
    (cli cảnh báo + queries rỗng = kho đắp bù tắt, ô thiếu giữ slug)."""
    system = (
        "You translate a Vietnamese video-editor brief into English stock-footage "
        "search queries for a local footage library. Return 2-6 queries, each 1-4 "
        "lowercase English words, concrete and visual (subjects/scenery, no verbs of "
        "intent). Cover EVERY distinct visual idea in the brief."
        + (f"\n\nThe library's real tag vocabulary (prefer these words):\n{vocab_lines}"
           if vocab_lines else "")
    )
    parsed, _ = client.complete(system, prompt, InsertFootageQueries)
    return parsed.queries


def ingest_insert_footage(folder: Path, project_dir: Path, tagger,
                          context: str = "") -> tuple[list[InsertClip], list[str]]:
    """Copy media trong folder editor vào media/insert/ + GLM tag cỡ cảnh từng file.

    Trả (clips, warnings). Prefix crc8 theo path GỐC chống đè trùng tên (họ bug F6 —
    norm_dir ghi theo asset.name, hai file trùng tên là file sau ĐÈ file trước).
    Tag lỗi/tagger None -> shot_size "" (trung tính), file vẫn dùng được."""
    import shutil
    import zlib

    from autoedit.library.vision import media_type_of
    from autoedit.project import ffprobe_duration

    warns: list[str] = []
    files = sorted((p for p in folder.iterdir()
                    if p.is_file() and media_type_of(p)), key=lambda p: p.name.lower())
    dest = project_dir / "media" / "insert"
    dest.mkdir(parents=True, exist_ok=True)
    clips: list[InsertClip] = []
    for f in files:
        pref = f"{zlib.crc32(str(f.resolve()).encode('utf-8')):08x}"
        dst = dest / f"{pref}_{f.name}"
        if not dst.exists():
            shutil.copy2(f, dst)
        shot = ""
        if tagger is not None:
            try:
                shot = tagger.tag(f, folder_context=context).shot_size or ""
            except Exception as exc:
                warns.append(f"tag cỡ cảnh lỗi {f.name} ({exc}) — dùng trung tính")
        dur = 0.0
        if media_type_of(f) == "video":
            dur = ffprobe_duration(dst) or 0.0
        clips.append(InsertClip(path=dst.relative_to(project_dir).as_posix(),
                                shot_size=shot, duration=round(dur, 3)))
    return clips, warns


def _cell_durs(project: Project, ins) -> list[float] | None:
    """Độ dài từng ô của Δ theo lưới (None = Δ chưa có mép trên timeline — cut chưa chạy).
    Không có lưới (tier C/không nhịp) -> 1 ô phủ trọn Δ, y hành vi M3."""
    from autoedit.music.plan import insert_edges
    from autoedit.packager import coverage as cov

    edge = insert_edges(project).get(ins.after_beat)
    if edge is None:
        return None
    cuts = cov.insert_grids(project).get(ins.after_beat)
    if not cuts or len(cuts) < 2:
        return [round(edge[1] - edge[0], 4)]
    marks = cuts + [edge[1]]
    return [round(b - a, 4) for a, b in zip(marks, marks[1:])]


def _assign_editor_clips(picks: list[InsertPick | None], holds: list[bool],
                         durs: list[float], clips: list[InsertClip],
                         speed: float) -> None:
    """Điền clip editor vào ô trống — HOLD trước (ít ứng viên rộng), mỗi clip 1 ô.

    Ưu tiên 4 nấc mỗi ô: đúng-cỡ + đủ-dài > đúng-cỡ > chưa-tag + đủ-dài > chưa-tag;
    quét vét cuối: editor đưa clip là MUỐN dùng — còn clip còn ô trống thì đắp chéo cỡ
    (ưu tiên vẫn giữ, chỉ không đẻ cửa loại — foundation filter-overload-guard)."""
    remaining = list(clips)

    def take(i: int, tiers: list) -> InsertClip | None:
        need = durs[i] * speed
        for pred in tiers:
            for c in remaining:
                ok_dur = c.duration <= 0 or c.duration >= need
                if pred(c, ok_dur):
                    remaining.remove(c)
                    return c
        return None

    order = [i for i, h in enumerate(holds) if h] + [i for i, h in enumerate(holds) if not h]
    for i in order:
        want = WIDE_SIZES if holds[i] else RUN_SIZES
        c = take(i, [lambda c, ok, w=want: c.shot_size in w and ok,
                     lambda c, ok, w=want: c.shot_size in w,
                     lambda c, ok: not c.shot_size and ok,
                     lambda c, ok: not c.shot_size])
        if c is not None:
            picks[i] = InsertPick(path=c.path, source="editor", shot_size=c.shot_size,
                                  hold=holds[i])
    for i in order:  # quét vét: clip lệch cỡ còn lại vẫn hơn slug
        if picks[i] is not None or not remaining:
            continue
        c = take(i, [lambda c, ok: ok, lambda c, ok: True])
        if c is not None:
            picks[i] = InsertPick(path=c.path, source="editor", shot_size=c.shot_size,
                                  hold=holds[i], note="lệch cỡ cảnh")


def _library_pool(conn: sqlite3.Connection, niche: str, queries: list[str],
                  used_keys: set[str], script_blob: str = "",
                  reserved_prefixes: tuple[str, ...] = ()) -> tuple[list[dict], list[str]]:
    """Ứng viên kho cho Δ theo query đã dịch — VIDEO có duration, P7 lọc trước limit,
    CỔNG LOCATION (geo-gate PA2 cây Khu Vực + tên nước lạ trong siêu dữ liệu).
    reserved_prefixes = vùng HINH THO đặt chỗ cho chỗ KHÁC (chương khác + Mini Hook)
    — nếu không loại thì search chữ vớt lại chính cảnh đã dành riêng, đặt-chỗ thành
    hư danh (V14 lần đầu: Δ ch3 vớt 13 cảnh HINH THO\\chapter 1 qua query "oman").
    Trả (pool, [ghi chú clip bị cổng chặn] cho tầng đo)."""
    from autoedit.library.db import search_assets
    from autoedit.sourcer.local import _used_paths, passes_geo

    exclude = _used_paths(used_keys)
    pool: list[dict] = []
    blocked: list[str] = []
    seen: set[str] = set()
    for q in queries:
        for row in search_assets(conn, niche, q, limit=LIBRARY_PER_QUERY,
                                 exclude_paths=exclude):
            if row["path"] in seen or row.get("media_type") != "video":
                continue
            if (row.get("duration") or 0) <= 0:
                continue
            seen.add(row["path"])
            if reserved_prefixes and str(row.get("source_video") or "").lower()\
                    .startswith(reserved_prefixes):
                continue
            if script_blob:
                if not passes_geo(row.get("folder_path", ""), script_blob):
                    blocked.append(Path(row["path"]).name)
                    continue
                country = foreign_location(row, script_blob)
                if country:
                    blocked.append(f"{Path(row['path']).name} ({country})")
                    continue
            pool.append(row)
    return pool, blocked


def _hinhtho_pool(conn: sqlite3.Connection, niche: str, scan: dict,
                  chapter: int | None, used_keys: set[str]) -> list[dict]:
    """Clip HINH THO cho Δ thuộc `chapter`: folder `chapter N` ĐÚNG chương + vùng chung
    (file ở gốc/folder tên khác khuôn); KHÔNG đụng chương khác/Mini Hook (giữ cho chỗ
    của nó). Editor TỰ CHỌN các clip này -> miễn cổng location. Đúng-chương xếp trước
    chung; trong nhóm giữ thứ tự sổ (approved/indexed_at/id)."""
    from autoedit.sourcer.local import _used_paths

    roots = scan.get("all") or ()
    if not roots:
        return []
    sql = ("SELECT * FROM library_assets WHERE niche = ? AND ("
           + " OR ".join("substr(lower(source_video), 1, ?) = ?" for _ in roots)
           + ") ORDER BY approved DESC, indexed_at DESC, id DESC")
    params: list = [niche]
    for p in roots:
        params += [len(p), p]
    exclude = _used_paths(used_keys)
    my = scan.get("by_chapter", {}).get(chapter, ()) if chapter is not None else ()
    other = tuple(p for n, ps in scan.get("by_chapter", {}).items()
                  if n != chapter for p in ps) + (scan.get("minihook") or ())
    pool: list[dict] = []
    for r in conn.execute(sql, params).fetchall():
        row = dict(r)
        sv = str(row.get("source_video") or "").lower()
        if row.get("media_type") != "video" or (row.get("duration") or 0) <= 0:
            continue
        if row["path"] in exclude:
            continue
        if other and sv.startswith(other) and not (my and sv.startswith(my)):
            continue
        pool.append(row)
    # Đúng-chương trước chung; trong nhóm xếp scene CHẴN trước LẺ rồi theo chỉ số —
    # 13 pick đầu cách nhau ≥2 cảnh trong video nguồn (mẻ HINH THO là class viral:
    # lấy cảnh LIỀN KỀ = tái hiện nguyên đoạn documentary, đúng lớp rủi ro luật "kề"
    # của ViralLedger; Δ chưa qua ledger — ghi còn ngỏ MO_TA §6, đây là giảm nhẹ rẻ).
    pool.sort(key=lambda r: (
        0 if my and str(r.get("source_video") or "").lower().startswith(my) else 1,
        int(r.get("scene_index") or 0) % 2, int(r.get("scene_index") or 0)))
    return pool


def _assign_library(picks: list[InsertPick | None], holds: list[bool],
                    durs: list[float], pool: list[dict], speed: float,
                    used_in_video: set[str], source: str = "library") -> None:
    """Kho/HINH THO đắp ô còn trống — cùng bậc ưu tiên cỡ cảnh như clip editor."""
    remaining = list(pool)

    def take(i: int, tiers: list) -> dict | None:
        need = durs[i] * speed
        for pred in tiers:
            for r in remaining:
                ok_dur = (r.get("duration") or 0) >= need
                if pred((r.get("shot_size") or "").strip(), ok_dur):
                    remaining.remove(r)
                    return r
        return None

    order = [i for i, h in enumerate(holds) if h] + [i for i, h in enumerate(holds) if not h]
    for i in order:
        if picks[i] is not None:
            continue
        want = WIDE_SIZES if holds[i] else RUN_SIZES
        r = take(i, [lambda s, ok, w=want: s in w and ok,
                     lambda s, ok, w=want: s in w,
                     lambda s, ok: ok,          # kho dồi dào: lệch cỡ + đủ dài vẫn hơn slug
                     lambda s, ok: True])
        if r is not None:
            key = f"local:{r['path']}"
            used_in_video.add(key)
            picks[i] = InsertPick(path=r["path"], source=source, asset_key=key,
                                  shot_size=(r.get("shot_size") or "").strip(),
                                  hold=holds[i],
                                  note="" if (r.get("shot_size") or "") else "kho chưa tag cỡ")


def pick_insert_footage(project: Project, conn: sqlite3.Connection | None,
                        used_in_video: set[str], record,
                        channel: str = "", footage_speed: float = 0.9) -> None:
    """Điền `footage_picks` cho mọi Δ có nguồn. Ưu tiên 4 tầng (user chốt 2026-07-21):
    ① clip `--footage` (editor đưa tay cho ĐÚNG Δ này) ② HINH THO trong folder --ref
    (đúng chương Δ + vùng chung — M4d) ③ kho theo `--prompt` (qua CỔNG LOCATION)
    ④ slug. Tầng ①② do editor tự chọn nên miễn cổng location.

    Fail-open TỪNG Δ: lỗi ở đâu Δ đó giữ slug + warning, không giết stage source.
    Pick từ sổ (HINH THO/kho) LOG usage P7 — clip editor NGOÀI kho, không đếm (y luật
    nhạc editor M3)."""
    from autoedit.sourcer import usage
    from autoedit.sourcer.local import _blob, ref_hinhtho_scan

    hinhtho: dict = {"all": ()}
    if conn is not None and project.niche:
        try:
            refs = tuple(str(s).lower() for s in (project.inputs.ref_sources or [])
                         if str(s).strip())
            hinhtho = ref_hinhtho_scan(conn, project.niche, refs)
        except Exception:
            hinhtho = {"all": ()}
    script_blob = _blob(project.inputs.script_text or "")
    by_id = {b.beat_id: b for b in project.beats}

    for ins in project.inserts:
        if not (ins.footage_clips or ins.footage_queries or hinhtho.get("all")):
            continue
        try:
            durs = _cell_durs(project, ins)
            if durs is None:
                record.warnings.append(
                    f"M4c Δ sau beat {ins.after_beat}: chưa có timeline (chạy `cut` "
                    "trước `source`) — Δ giữ slug")
                continue
            from autoedit.packager.coverage import insert_hold_flags
            holds = insert_hold_flags(durs)
            picks: list[InsertPick | None] = [None] * len(durs)
            if ins.footage_clips:
                _assign_editor_clips(picks, holds, durs, ins.footage_clips, footage_speed)
            n_editor = sum(1 for p in picks if p is not None)
            # M4d: HINH THO của mẻ --ref — footage editor dành riêng cho Δ chương này
            n_ht = 0
            if (any(p is None for p in picks) and hinhtho.get("all")
                    and conn is not None and project.niche):
                beat = by_id.get(ins.after_beat)
                pool = _hinhtho_pool(conn, project.niche, hinhtho,
                                     beat.chapter if beat else None, used_in_video)
                _assign_library(picks, holds, durs, pool, footage_speed, used_in_video,
                                source="hinh_tho")
                n_ht = sum(1 for p in picks if p is not None) - n_editor
            # kho theo prompt — CỔNG LOCATION gác (V13: Vietnam/Bosnia/Djibouti lọt)
            n_lib = 0
            blocked: list[str] = []
            if (any(p is None for p in picks) and ins.footage_queries
                    and conn is not None and project.niche):
                beat = by_id.get(ins.after_beat)
                ch = beat.chapter if beat else None
                reserved = tuple(p for n, ps in hinhtho.get("by_chapter", {}).items()
                                 if n != ch for p in ps) + (hinhtho.get("minihook") or ())
                pool, blocked = _library_pool(conn, project.niche, ins.footage_queries,
                                              used_in_video, script_blob,
                                              reserved_prefixes=reserved)
                _assign_library(picks, holds, durs, pool, footage_speed, used_in_video)
                n_lib = sum(1 for p in picks if p is not None) - n_editor - n_ht
            if channel and conn is not None:
                for p in picks:
                    if p is not None and p.source in ("library", "hinh_tho"):
                        usage.log_usage(conn, channel, p.asset_key, project.project_id)
            ins.footage_picks = [p if p is not None else InsertPick() for p in picks]
            n_slug = len(durs) - n_editor - n_ht - n_lib
            record.warnings.append(
                f"M4c Δ sau beat {ins.after_beat}: {len(durs)} ô "
                f"({sum(holds)} HOLD) — editor {n_editor} · HINH THO {n_ht} · "
                f"kho {n_lib} · slug {n_slug}"
                + (f" · cổng location chặn {len(blocked)} "
                   f"({', '.join(blocked[:3])}{'…' if len(blocked) > 3 else ''})"
                   if blocked else "")
                + (" ⚠ kho đắp bù TẮT (không có prompt/query)"
                   if n_slug and not ins.footage_queries else ""))
        except Exception as exc:
            ins.footage_picks = []
            record.warnings.append(
                f"M4c Δ sau beat {ins.after_beat} lỗi ({exc}) — Δ giữ slug")
