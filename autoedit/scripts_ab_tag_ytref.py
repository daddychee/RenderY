"""A/B mù tag bối cảnh ytref (M2 §3i — MO_TA_VAN_HANH_YTREF_DIEM_NHO): ~40 cảnh bộ
MOON cắt y production (bóp/neo đỉnh + zoom 112%) rồi tag 2 CÁCH bằng GLM:

  A = hiện trạng cũ  : source_title = stem tên file tải (cụt + lẫn mã)
  B = có bối cảnh    : title THẬT yt-dlp + section_hint chapter + --topic

Xuất bảng HTML SO MÙ (trái/phải đảo ngẫu nhiên từng dòng, seed cố định) cho user
phán + mục "điểm nhô đối chiếu" (link YouTube ?t= đúng mốc) cho cổng mắt kép (2).
Giải mù bằng mapping.json (đọc sau khi user phán xong, đừng mở trước).

Chạy:  uv run python scripts_ab_tag_ytref.py          (~$0.08, 5-10 phút)
       uv run python scripts_ab_tag_ytref.py --peaks-only   (0 GLM — chỉ tái sinh
       trang đối chiếu điểm nhô sau mỗi lần chỉnh luật cửa sổ/neo)
Output: ..\\AB_TAG_MOON\\ab_tag_moon.html + clips\\ + mapping.json
        (--peaks-only: ..\\AB_TAG_MOON\\diem_nho_doi_chieu.html)
"""
from __future__ import annotations

import html
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from autoedit.library.ingest import (
    VIRAL_ZOOM, apply_viral_rules, cut_scene, read_draft_scenes, scene_clip_name,
    youtube_infos_for, _chapter_title)
from autoedit.library.vision import GLMVisionTagger, glm_api_keys

DRAFTS = [
    Path(r"E:\CapCut Drafts\YTDown.com_YouTube_What-Artemis-II-Astronauts-Saw-"),
    Path(r"E:\CapCut Drafts\YTDown.com_YouTube_What-Artemis-II-Saw-On-the-Moon"),
    Path(r"E:\CapCut Drafts\YTDown.com_YouTube_What-China-Found-on-The-Moon_Me"),
]
PER_DRAFT = [12, 12, 16]        # China nhiều hơn — video duy nhất chắc chắn có chapters
TOPIC = "the Moon, lunar exploration"
OUT = Path(__file__).parent.parent / "AB_TAG_MOON"
SEED = 42


def pick_scenes(scenes, n):
    """Rải đều theo start + đảm bảo ≥2 cảnh cờ điểm nhô (nếu có) cho mục đối chiếu."""
    scenes = sorted(scenes, key=lambda s: s.start)
    step = max(1, len(scenes) // n)
    chosen = scenes[::step][:n]
    flagged = [s for s in scenes if s.peak_type]
    need = [f for f in sorted(flagged, key=lambda s: -s.peak_value)[:2] if f not in chosen]
    for f in need:      # thế chỗ cảnh không cờ cuối danh sách
        for i in range(len(chosen) - 1, -1, -1):
            if not chosen[i].peak_type:
                chosen[i] = f
                break
    return chosen


def peaks_only() -> None:
    """Trang đối chiếu điểm nhô riêng (cổng mắt 2) — top-5 cảnh cờ/video, cắt thật,
    link YouTube nhảy đúng mốc để soi đồ thị Most Replayed. Không GLM, chạy lại
    được sau mỗi lần chỉnh luật cửa sổ/neo."""
    (OUT / "clips").mkdir(parents=True, exist_ok=True)
    items = []
    for draft in DRAFTS:
        scenes, stats = read_draft_scenes(draft)
        infos, warns = youtube_infos_for(scenes)
        scenes = apply_viral_rules(scenes, stats, infos, warns)
        flagged = sorted((s for s in scenes if s.peak_type),
                         key=lambda s: -s.peak_value)[:5]
        for sc in flagged:
            info = infos.get(str(sc.source))
            clip, _ = cut_scene(sc, OUT / "clips", zoom=VIRAL_ZOOM)
            items.append((clip, info, sc))
        print(f"✓ {draft.name[:40]}: cờ {stats['peak_scenes']} cảnh, lấy {len(flagged)}")

    lis = []
    for clip, info, sc in items:
        t = int(sc.start)
        lis.append(
            f'<li><video src="clips/{html.escape(clip.name)}" controls muted loop '
            f'preload="metadata"></video><br>{html.escape(info.title)} · miếng cắt '
            f'{sc.start:.0f}s ({sc.duration:.0f}s) · {sc.peak_type} v={sc.peak_value:.2f}'
            f' · neo giữa bin {sc.peak_apex:.0f}s → '
            f'<a href="https://www.youtube.com/watch?v={info.video_id}&t={t}s" '
            f'target="_blank">mở YouTube tại {t // 60}:{t % 60:02d}</a></li>')
    (OUT / "diem_nho_doi_chieu.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Đối chiếu điểm nhô</title><style>"
        "body{font-family:Segoe UI,sans-serif;margin:16px} video{width:340px;display:block}"
        "li{margin-bottom:18px}</style>"
        "<h1>Đối chiếu điểm nhô — cửa sổ BIN đỉnh (v2, fix 2026-07-11)</h1>"
        "<p>Bấm link: đồ thị Most Replayed dưới thanh tua phải NHÔ CAO đúng quanh mốc.</p>"
        f"<ul>{''.join(lis)}</ul>", encoding="utf-8")
    print(f"\n✓ XONG: {OUT / 'diem_nho_doi_chieu.html'} ({len(items)} clip)")


def main() -> None:
    keys = glm_api_keys()
    if not keys:
        sys.exit("Thiếu GLM_API_KEY trong .env")
    taggers = [GLMVisionTagger(api_key=k) for k in keys]
    (OUT / "clips").mkdir(parents=True, exist_ok=True)

    jobs = []  # (clip_path, source_title_A, title_B, section_B, video_id, scene)
    for draft, n in zip(DRAFTS, PER_DRAFT):
        scenes, stats = read_draft_scenes(draft)
        infos, warns = youtube_infos_for(scenes)
        scenes = apply_viral_rules(scenes, stats, infos, warns)
        for w in warns:
            print(f"  ⚠ {w}")
        for sc in pick_scenes([s for s in scenes if s.media_type == "video"], n):
            info = infos.get(str(sc.source))
            clip, _ = cut_scene(sc, OUT / "clips", zoom=VIRAL_ZOOM)
            jobs.append((clip, Path(sc.source).stem,
                         (info.title if info and info.title else Path(sc.source).stem),
                         _chapter_title(info, sc.start + sc.duration / 2),
                         info.video_id if info else "", sc))
        print(f"✓ {draft.name[:40]}: chọn {n} cảnh")

    print(f"Tag {len(jobs)} cảnh × 2 cách ({len(taggers)} key)...")

    def tag_one(i_job):
        """Fail-open TỪNG cảnh (y production tag_jobs) — 1 cảnh GLM khăng khăng
        mood ngoài vocab (PB4) không được giết cả mẻ A/B."""
        i, (clip, stem, title, section, vid, sc) = i_job
        tg = taggers[i % len(taggers)]
        time.sleep((i % (3 * len(taggers))) * 0.7)  # so le khởi động (PB3)
        try:
            a = tg.tag(clip, source_title=stem)
            b = tg.tag(clip, source_title=title, section_hint=section, topic=TOPIC)
        except Exception as exc:
            print(f"  ⚠ [{i + 1}/{len(jobs)}] {clip.name}: BỎ ({str(exc)[:120]})")
            return i, None, None
        print(f"  [{i + 1}/{len(jobs)}] {clip.name}")
        return i, a, b

    results = {}
    with ThreadPoolExecutor(max_workers=3 * len(taggers)) as ex:
        for i, a, b in ex.map(tag_one, enumerate(jobs)):
            if a is not None:
                results[i] = (a, b)

    rng = random.Random(SEED)
    mapping, rows = {}, []
    for i, (clip, stem, title, section, vid, sc) in enumerate(jobs):
        if i not in results:  # cảnh fail-open đã bỏ
            continue
        a, b = results[i]
        a_left = rng.random() < 0.5
        mapping[str(i + 1)] = {"left": "A" if a_left else "B", "clip": clip.name,
                               "section_hint_B": section}
        left, right = (a, b) if a_left else (b, a)

        def cell(t):
            return (f"<b>{html.escape(t.subject)}</b><br>{html.escape(t.description)}"
                    f"<br><i>{html.escape(t.scene_type)} · {html.escape(', '.join(t.mood))}"
                    f"</i><br><small>{html.escape(', '.join(t.tags))}</small>")

        peak = (f' <span class="pk">⭐ điểm nhô {sc.peak_type} v={sc.peak_value:.2f}</span>'
                if sc.peak_type else "")
        rows.append(
            f'<tr><td class="n">{i + 1}{peak}<br>'
            f'<video src="clips/{html.escape(clip.name)}" controls muted loop '
            f'preload="metadata"></video></td>'
            f'<td>{cell(left)}</td><td>{cell(right)}</td>'
            f'<td class="v">TRÁI ◻ &nbsp; PHẢI ◻ &nbsp; HÒA ◻</td></tr>')

    peak_rows = []
    for i, (clip, stem, title, section, vid, sc) in enumerate(jobs):
        if sc.peak_type and vid:
            t = int(sc.start)
            peak_rows.append(
                f'<li>#{i + 1} — {html.escape(title)} · miếng cắt {sc.start:.0f}s '
                f'({sc.duration:.0f}s) · {sc.peak_type} v={sc.peak_value:.2f} → '
                f'<a href="https://www.youtube.com/watch?v={vid}&t={t}s" target="_blank">'
                f'mở YouTube tại {t // 60}:{t % 60:02d}</a> (soi đồ thị Most Replayed '
                f'ngay dưới thanh tua)</li>')

    (OUT / "mapping.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "ab_tag_moon.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>A/B tag MOON</title><style>"
        "body{font-family:Segoe UI,sans-serif;margin:16px} table{border-collapse:collapse;width:100%}"
        "td{border:1px solid #ccc;padding:8px;vertical-align:top;font-size:14px}"
        "video{width:300px} .n{white-space:nowrap} .v{white-space:nowrap;font-size:18px}"
        ".pk{color:#c60;font-weight:bold} h2{margin-top:28px}</style>"
        "<h1>A/B mù — tag bối cảnh ytref (bộ MOON)</h1>"
        "<p>Mỗi dòng: cùng 1 clip, 2 bộ tag (trái/phải đảo ngẫu nhiên). Đánh dấu bên"
        " MÔ TẢ ĐÚNG HÌNH + hữu ích cho tìm footage hơn. Đừng mở mapping.json trước.</p>"
        f"<table><tr><th>clip</th><th>Bên TRÁI</th><th>Bên PHẢI</th><th>phán</th></tr>"
        + "".join(rows) + "</table>"
        "<h2>Cổng mắt (2) — đối chiếu điểm nhô với YouTube</h2><ul>"
        + "".join(peak_rows) + "</ul>", encoding="utf-8")
    print(f"\n✓ XONG: {OUT / 'ab_tag_moon.html'} ({len(jobs)} cảnh, "
          f"{len(peak_rows)} clip điểm nhô đối chiếu)")


if __name__ == "__main__":
    peaks_only() if "--peaks-only" in sys.argv else main()
