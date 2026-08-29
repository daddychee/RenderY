"""Stage REPORT — sinh report.html bàn giao editor (CHỈ ĐỌC project.json).

Không LLM, không tốn tiền, chạy lại tùy ý. Gom mọi quyết định của tool thành 1 trang:
việc CẦN XỬ LÝ (footage thiếu / kiểm bản quyền / enrich chờ duyệt) + bảng beat + nhạc +
enrich + cảnh báo. Editor dùng làm checklist 20% cuối, tự thay file rồi chạy lại assemble.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

from autoedit.project import Project, Stage, StageRecord, StageStatus


def run_report(project: Project) -> Project:
    src = project.stages.get(Stage.SOURCE)
    if src is None or src.status != StageStatus.DONE or not project.beats:
        raise RuntimeError("Stage source chưa xong — chạy `autoedit source` trước.")

    record = StageRecord.running()
    project.stages[Stage.REPORT] = record
    project.save()
    try:
        html_str = _render_html(project)
        out = Path(project.project_dir) / "report.html"
        out.write_text(html_str, encoding="utf-8")
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.save()
        raise

    project.report_path = str(out)
    record.status = StageStatus.DONE
    record.completed_at = datetime.now(timezone.utc).isoformat()
    project.save()
    return project


# ----------------------------------------------------------------------------
def _t(sec) -> str:
    if sec is None:
        return "—"
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def _esc(x) -> str:
    return html.escape(str(x))


def _queries(beat) -> str:
    """Gợi ý từ khoá cho beat thiếu footage (specific + broad)."""
    sq = beat.search_queries
    spec = getattr(sq, "specific", None) or (sq.get("specific") if isinstance(sq, dict) else [])
    broad = getattr(sq, "broad", None) or (sq.get("broad") if isinstance(sq, dict) else [])
    return ", ".join(spec + broad) or _esc(beat.visual_concept)


def _mograph(beat) -> str:
    """Tóm tắt motion graphic gắn vào beat."""
    bits = []
    for o in beat.overlays:
        bits.append(f"{o.kind}:{_esc(o.text)}")
    if beat.graphic_spec:
        org = " (bổ sung)" if getattr(beat.graphic_spec, "data_origin", "script") == "supplementary" else ""
        bits.append(f"chart {beat.graphic_spec.chart_type}{org}")
    if beat.info_card:
        bits.append("thẻ chữ")
    if beat.text_sequence:
        bits.append(f"kinetic {len(beat.text_sequence.phrases)} cụm")
    return ", ".join(bits)


def _render_html(project: Project) -> str:
    shots = {s.beat_id: s for s in project.shots}
    segs = project.segments
    total = (segs[-1].timeline_end + segs[-1].breathing_after) if segs else 0
    chapters = (project.outline or {}).get("chapters", [])
    n_ch = len(chapters)

    # ---- gom CẦN XỬ LÝ ----
    needs, licensing, enrich_todo = [], [], []
    for b in project.beats:
        sh = shots.get(b.beat_id)
        if sh and sh.status == "needs_human":
            needs.append((b, sh))
        if sh and sh.licensing_flag:
            licensing.append((b, sh))
        gs = b.graphic_spec
        if gs is not None and getattr(gs, "data_origin", "script") == "supplementary" and not getattr(gs, "approved", True):
            enrich_todo.append((b, f"biểu đồ bổ sung: {_esc(gs.title)}"))
        if b.info_card is not None and not b.info_card.approved:
            enrich_todo.append((b, f"thẻ chữ: {_esc(b.info_card.title)}"))

    def cost(prefix):
        return round(sum(c.usd for c in project.cost_log if c.stage.startswith(prefix)), 4)

    p = []
    p.append(_HEAD)
    p.append(f"<h1>Báo cáo bàn giao — {_esc(project.project_id)}</h1>")
    # tổng quan
    p.append("<div class='grid'>")
    p.append(f"<div class='card'><b>Thời lượng</b><br>{_t(total)}</div>")
    p.append(f"<div class='card'><b>Chương / Beat</b><br>{n_ch} / {len(project.beats)}</div>")
    tone = (project.outline or {}).get("tone", "")
    if tone:  # C4/b1: tone = hằng số thái độ video — editor đối chiếu mood/nhạc khi duyệt
        p.append(f"<div class='card'><b>Tone video</b><br>{_esc(tone)}</div>")
    p.append(f"<div class='card'><b>Chi phí LLM</b><br>direct ${cost('direct')} · enrich ${cost('enrich')}</div>")
    p.append(f"<div class='card'><b>Draft CapCut</b><br>{_esc(Path(project.draft_path).name) if project.draft_path else '—'}</div>")
    p.append("</div>")

    # ---- CẦN XỬ LÝ ----
    total_todo = len(needs) + len(licensing) + len(enrich_todo)
    p.append(f"<h2 class='todo'>🔴 CẦN XỬ LÝ ({total_todo})</h2>")
    if not total_todo:
        p.append("<p class='ok'>✅ Không có việc bắt buộc — kiểm tra nhanh rồi dựng.</p>")
    if needs:
        p.append("<h3>Thiếu footage (editor tự đắp)</h3><table><tr><th>Lúc</th><th>Lời thoại</th><th>Gợi ý từ khoá</th></tr>")
        for b, sh in needs:
            p.append(f"<tr><td>{_t(b.timeline_start)}</td><td>{_esc(b.text[:70])}</td><td>{_queries(b)}</td></tr>")
        p.append("</table>")
    if licensing:
        p.append("<h3>Kiểm bản quyền (ảnh thực thể)</h3><table><tr><th>Lúc</th><th>Footage</th><th>Nguồn</th></tr>")
        for b, sh in licensing:
            p.append(f"<tr><td>{_t(b.timeline_start)}</td><td>{_esc(Path(sh.asset_path).name) if sh.asset_path else '—'}</td><td>{_esc(sh.note[:80])}</td></tr>")
        p.append("</table>")
    if enrich_todo:
        p.append("<h3>Nội dung bổ sung chờ DUYỆT (chạy <code>enrich-approve</code> rồi assemble lại)</h3><table><tr><th>Lúc</th><th>Mục</th></tr>")
        for b, label in enrich_todo:
            p.append(f"<tr><td>{_t(b.timeline_start)}</td><td>{label}</td></tr>")
        p.append("</table>")

    # ---- bảng beat ----
    rank_by_beat = {r.get("beat_id"): r for r in project.rank_log}
    p.append("<h2>Chi tiết theo beat</h2>")
    p.append("<table><tr><th>Lúc</th><th>Lời thoại</th><th>Footage</th><th>Vì sao chọn (NÃO)</th><th>Route</th><th>TT</th><th>Motion graphic</th><th>Phương án thay</th></tr>")
    for b in project.beats:
        sh = shots.get(b.beat_id)
        st = sh.status if sh else "—"
        cls = "warn" if st == "needs_human" else ("lic" if (sh and sh.licensing_flag) else "")
        asset = _esc(Path(sh.asset_path).name) if (sh and sh.asset_path) else "—"
        if sh and sh.peak:  # ytref §3h: pick là cảnh điểm nhô Most Replayed của video nguồn
            asset = f"⭐ {asset}"
        rk = rank_by_beat.get(b.beat_id)
        ly_do = _esc(rk.get("chosen_ly_do", "")) if rk else ""
        n_shot = 1 + len(sh.extra_shots) if sh else 0
        if n_shot > 1:
            asset = f"{asset} <b>+{n_shot - 1}</b> ({n_shot} shot)"
        alts = "<br>".join(_esc(a) for a in (sh.alternates[:3] if sh else [])) or "—"
        p.append(
            f"<tr class='{cls}'><td>{_t(b.timeline_start)}</td><td>{_esc(b.text[:60])}</td>"
            f"<td>{asset}</td><td>{ly_do or '—'}</td><td>{_esc(b.sourcing_route)}</td><td>{_esc(st)}</td>"
            f"<td>{_mograph(b)}</td><td class='alt'>{alts}</td></tr>"
        )
    p.append("</table>")
    n_peak = sum(1 for s in project.shots if s.peak)
    if n_peak:
        p.append(f"<p style='color:#5a5a6a;font-size:12px'>⭐ = cảnh ĐIỂM NHÔ Most Replayed "
                 f"của video nguồn (ytref §3h) — pick điểm nhô: {n_peak} shot chính "
                 f"(số ở dòng viral c8 đếm cả shot phụ)</p>")

    # ---- kill-log phễu c5 (F5) ----
    if project.rank_log:
        p.append("<h2>Phễu chọn footage (kill-log)</h2>")
        p.append("<table><tr><th>Beat</th><th>Thu</th><th>Chết kỹ thuật</th><th>Veto nghĩa</th><th>Trả lại sàn</th><th>Còn lại</th></tr>")
        tot = {"thu": 0, "hong_ky_thuat": 0, "veto_nghia": 0, "tra_lai_san": 0, "con_lai": 0}
        for r in project.rank_log:
            kl = r.get("kill_log", {})
            for k in tot:
                tot[k] += kl.get(k, 0)
            p.append(
                f"<tr><td>b{r.get('beat_id', '?'):02d}</td><td>{kl.get('thu', 0)}</td>"
                f"<td>{kl.get('hong_ky_thuat', 0)}</td><td>{kl.get('veto_nghia', 0)}</td>"
                f"<td>{kl.get('tra_lai_san', 0)}</td><td>{kl.get('con_lai', 0)}</td></tr>"
            )
        p.append(
            f"<tr><th>Tổng</th><th>{tot['thu']}</th><th>{tot['hong_ky_thuat']}</th>"
            f"<th>{tot['veto_nghia']}</th><th>{tot['tra_lai_san']}</th><th>{tot['con_lai']}</th></tr>"
        )
        p.append("</table>")
        p.append("<p style='color:#5a5a6a;font-size:12px'>Cửa nào giết nhiều bất thường → nới ĐỊNH NGHĨA cửa đó, không siết footage (luật c5).</p>")

    # ---- C5 vision gate (C đợt 5) — mắt soi top-pick, user phán trúng/oan từ bảng này ----
    gates = [(r.get("beat_id"), g) for r in project.rank_log
             for g in r.get("vision_gate", [])]
    if gates:
        flagged = [(b, g) for b, g in gates if g.get("action") != "pass"]
        p.append(f"<h2>C5 vision gate — mắt soi top-pick ({len(gates)} lượt soi, "
                 f"{len(flagged)} đáng chú ý)</h2>")
        if flagged:
            act_vi = {"demote": "gạt — lấy ứng viên kế",
                      "giu_du_nghi_sai": "GIỮ dù nghi sai — SOÁT TAY",
                      "mood_warning": "giữ pick, mood nghi lệch"}
            p.append("<table><tr><th>Beat</th><th>Footage</th><th>Chủ thể</th><th>Mood</th>"
                     "<th>Mắt thấy</th><th>Xử lý</th></tr>")
            for b, g in flagged:
                cls = "warn" if g.get("action") == "giu_du_nghi_sai" else ""
                p.append(
                    f"<tr class='{cls}'><td>b{b:02d}</td><td>{_esc(g.get('asset_key', ''))}</td>"
                    f"<td>{_esc(g.get('subject_match', ''))}</td><td>{_esc(g.get('mood_match', ''))}</td>"
                    f"<td>{_esc(g.get('seen', ''))}</td>"
                    f"<td>{act_vi.get(g.get('action'), _esc(g.get('action', '')))}</td></tr>"
                )
            p.append("</table>")
        p.append("<p style='color:#5a5a6a;font-size:12px'>Gate chỉ soi shot CHÍNH; demote tối đa "
                 "1 lần/beat, chê cả 2 thì giữ điểm phễu cao nhất; mood CHỈ cảnh báo (chưa có quyền "
                 "đổi pick — nâng/hạ quyền sau khi user phán trúng/oan từng dòng).</p>")

    # ---- nhạc ----
    if project.music_selections:
        ch_mood = {str(c.get("chapter_id")): c.get("mood", "") for c in chapters}
        plan_by = {str(e.chapter_id): e for e in project.music_plan}
        if plan_by:
            # MUSIC SYNC: tier + offset đã neo + neo vào đâu — editor đối chiếu điểm nhấn
            p.append("<h2>Nhạc nền theo chương — MUSIC SYNC</h2>"
                     "<table><tr><th>Chương</th><th>Mood</th><th>Bài</th><th>Tier nhịp</th>"
                     "<th>Offset</th><th>Neo</th></tr>")
            for cid, f in project.music_selections.items():
                e = plan_by.get(cid)
                tier = _esc(e.beat_tier) if e else ""
                off = f"{e.start_offset:.2f}s" if e else ""
                note = _esc(e.anchor_note) if e else ""
                p.append(f"<tr><td>{_esc(cid)}</td><td>{_esc(ch_mood.get(cid, ''))}</td>"
                         f"<td>{_esc(Path(f).stem)}</td><td>{tier}</td><td>{off}</td><td>{note}</td></tr>")
            p.append("</table><p style='color:#5a5a6a;font-size:12px'>Tier A nhịp rõ / B chỉ accent "
                     "/ C ambient (sync tắt). Chi tiết snap + đổi nhạc: xem cảnh báo stage assemble.</p>")
        else:
            p.append("<h2>Nhạc nền theo chương</h2><table><tr><th>Chương</th><th>Mood</th><th>Bài</th></tr>")
            for cid, f in project.music_selections.items():
                p.append(f"<tr><td>{_esc(cid)}</td><td>{_esc(ch_mood.get(cid, ''))}</td><td>{_esc(Path(f).stem)}</td></tr>")
            p.append("</table>")

    # ---- ambient ô thở (C1) ----
    if project.ambient_log:
        n_on = sum(1 for a in project.ambient_log if a.get("file"))
        p.append(f"<h2>Ambient ô thở — C1 ({n_on}/{len(project.ambient_log)} ô có tiếng)</h2>")
        p.append("<table><tr><th>Lúc</th><th>Dài</th><th>Beat</th><th>Loại cảnh</th><th>File</th><th>Ghi chú</th></tr>")
        for a in project.ambient_log:
            cls = "" if a.get("file") else "warn"
            bid = a.get("beat_id")
            p.append(
                f"<tr class='{cls}'><td>{_t(a.get('start', 0))}</td>"
                f"<td>{a.get('end', 0) - a.get('start', 0):.1f}s</td>"
                f"<td>{f'b{bid:02d}' if bid is not None else '—'}</td>"
                f"<td>{_esc(a.get('scene_type') or 'mù tag')}</td>"
                f"<td>{_esc(a.get('file') or '—')}</td><td>{_esc(a.get('note', ''))}</td></tr>"
            )
        p.append("</table>")
        p.append("<p style='color:#5a5a6a;font-size:12px'>Ambient LOẠI CẢNH 0dB (cổng tai V4 2026-07-10, KHÔNG hạ); tiếng CHỦ THỂ thắng ô -5dB (user chốt 2026-07-18, nâng từ -10dB). Nghe lệch cảnh → xem tag/kho biến thể.</p>")

    # ---- drone nền (S1) + SFX chủ thể (S2) ----
    if project.drone_log:
        d = project.drone_log
        gate = f" — gate cảnh <b>{_esc(d['gate'])}</b>, {d.get('runs', 1)} run" if d.get("gate") else ""
        p.append(f"<h2>Drone nền — S1</h2><p><b>{_esc(d.get('file', ''))}</b> phủ "
                 f"{d.get('covered_s', d.get('total_s', 0)):.0f}/{d.get('total_s', 0):.0f}s "
                 f"({d.get('loops', 0)} đoạn nối), volume {d.get('volume', 0)}{gate}.</p>")
    if project.subject_sfx_log:
        n_on = sum(1 for a in project.subject_sfx_log if a.get("file"))
        p.append(f"<h2>SFX chủ thể trong voice — S2 ({n_on} tiếng)</h2>")
        p.append("<table><tr><th>Lúc</th><th>Dài</th><th>Beat</th><th>Chủ thể</th><th>File</th><th>Match từ</th><th>Ghi chú</th></tr>")
        for a in project.subject_sfx_log:
            cls = "" if a.get("file") else "warn"
            src = {"kho": "tag kho (vision)", "concept": "concept NÃO"}.get(a.get("source", ""), "")
            p.append(
                f"<tr class='{cls}'><td>{_t(a.get('start', 0))}</td>"
                f"<td>{a.get('end', 0) - a.get('start', 0):.1f}s</td>"
                f"<td>b{a.get('beat_id', 0):02d}</td><td>{_esc(a.get('kind', ''))}</td>"
                f"<td>{_esc(a.get('file') or '—')}</td><td>{_esc(src)}</td>"
                f"<td>{_esc(a.get('note', ''))}</td></tr>"
            )
        p.append("</table>")
        p.append("<p style='color:#5a5a6a;font-size:12px'>SUBJECT_VOL -8dB trong voice / -5dB trong ô thở (user chốt 2026-07-18, nâng từ -15/-10dB của PB13); match-driven không trần (Milestone C 2026-07-13).</p>")
    if project.whoosh_log:
        n_on = sum(1 for w in project.whoosh_log if w.get("placed"))
        p.append(f"<h2>Whoosh khúc chuyển — S3 ({n_on}/{len(project.whoosh_log)} mốc)</h2>")
        p.append("<table><tr><th>Lúc</th><th>Loại</th><th>Mốc chuyển</th><th>Ghi chú</th></tr>")
        for w in project.whoosh_log:
            cls = "" if w.get("placed") else "warn"
            p.append(f"<tr class='{cls}'><td>{_t(w.get('at', 0))}</td>"
                     f"<td>{_esc(w.get('kind', ''))}</td><td>{_esc(w.get('label', ''))}</td>"
                     f"<td>{_esc(w.get('note', ''))}</td></tr>")
        p.append("</table>")
        p.append("<p style='color:#5a5a6a;font-size:12px'>Luật PB11: ~1 whoosh/phút ở khúc chuyển LỚN (chương = swell dài, vào ô thở = whoosh ngắn), không rắc theo cut.</p>")

    # ---- cảnh báo ----
    warns = [(s.value, w) for s, rec in project.stages.items() for w in rec.warnings]
    if warns:
        p.append(f"<h2>Cảnh báo ({len(warns)})</h2><ul class='warns'>")
        for stage, w in warns:
            p.append(f"<li><b>{_esc(stage)}</b>: {_esc(w)}</li>")
        p.append("</ul>")

    p.append("</body></html>")
    return "\n".join(p)


_HEAD = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<title>AutoEdit — Báo cáo bàn giao</title>
<style>
 body{font-family:-apple-system,Segoe UI,Arial,sans-serif;margin:24px;color:#1a1a22;background:#fafafc;line-height:1.45}
 h1{font-size:22px} h2{margin-top:28px;border-bottom:2px solid #e0e0e8;padding-bottom:4px}
 h2.todo{color:#c0392b;border-color:#e8b4ad} h3{margin:14px 0 6px;font-size:15px}
 .grid{display:flex;gap:12px;flex-wrap:wrap} .card{background:#fff;border:1px solid #e0e0e8;border-radius:8px;padding:10px 14px;min-width:140px}
 table{border-collapse:collapse;width:100%;background:#fff;font-size:13px;margin:6px 0}
 th,td{border:1px solid #e6e6ee;padding:6px 8px;text-align:left;vertical-align:top}
 th{background:#f0f0f5} tr.warn{background:#fdecea} tr.lic{background:#fff6e5}
 td.alt{color:#5a5a6a;font-size:11px;max-width:260px;word-break:break-all}
 .ok{color:#1a7f3c} code{background:#eee;padding:1px 4px;border-radius:3px}
 ul.warns{font-size:12px;color:#5a5a6a}
</style></head><body>"""
