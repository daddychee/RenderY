r"""Kho NHẠC — Epidemic Sound, quản theo bộ tiêu chí chốt 06/09.

Khảo sát 06/09 (đo thật, không đoán): endpoint JSON công khai
`epidemicsound.com/json/search/tracks/` KHÔNG cần login, trả đủ trục
(moods/genres/bpm/energyLevel/length/hasVocals) + `stems.full.lqMp3Url` là
TRỌN bài 128kbps trên CDN không chữ ký (đo: track 195s = 3MB, HTTP 200).
Bản sạch chỉ tải qua tài khoản trong két lúc khóa sổ — đúng khuôn Envato.

Trục chính: MOOD quy về vocab NỘI BỘ (cùng ngôn ngữ với footage — "mood là
trụ"); mood_goc giữ nguyên không mất tin. Luật gác: hasVocals chặn mặc định,
isSfx không vào kho, chống lặp theo su_kien len_final cùng kênh.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

EPIDEMIC_URL = "https://www.epidemicsound.com/json/search/tracks/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
CHONG_LAP_TAP = 3          # track đã lên final: không đề xuất lại trong 3 tập kề

# mood Epidemic -> vocab NỘI BỘ (cùng bộ với footage: tense/calm/...)
_MOOD_NOI_BO = {
    "tense": ("suspense", "tense", "dark", "mysterious", "angry", "eerie"),
    "calm": ("dreamy", "laid back", "peaceful", "relaxing", "sentimental",
             "romantic", "hopeful"),
    "epic": ("epic", "heroic", "marching"),
    "upbeat": ("happy", "euphoric", "quirky", "funny", "glamorous", "busy"),
    "sad": ("sad", "sombre", "melancholy"),
    "chaotic": ("chaotic", "restless", "running", "wild"),
}
_TRA_MOOD = {goc: nb for nb, ds in _MOOD_NOI_BO.items() for goc in ds}


def quy_mood(moods_goc: list[str]) -> str:
    """[mood Epidemic] -> mood nội bộ ĐẦU TIÊN khớp (thứ tự Epidemic = độ mạnh)."""
    for m in moods_goc:
        nb = _TRA_MOOD.get(m.strip().lower())
        if nb:
            return nb
    return "neutral"


def _get_json(url: str, timeout: float = 45.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def parse_track(t: dict) -> dict | None:
    """1 track JSON Epidemic -> dòng bảng nhac. isSfx -> None (không vào kho)."""
    if t.get("isSfx"):
        return None
    moods_goc = [m.get("displayTag") or m.get("tag") or "" for m in (t.get("moods") or [])]
    genres = [g.get("displayTag") or g.get("tag") or "" for g in (t.get("genres") or [])]
    stems = (t.get("stems") or {}).get("full") or {}
    ns = [c.get("name", "") for c in ((t.get("creatives") or {}).get("mainArtists") or [])]
    return {
        "id": f"epidemic:{t.get('id')}",
        "nguon": "epidemic",
        "tieu_de": (t.get("title") or "").strip(),
        "nghe_si": ", ".join(n for n in ns if n),
        "mood": quy_mood(moods_goc),
        "mood_goc": ", ".join(m.lower() for m in moods_goc if m),
        "genre": ", ".join(g.lower() for g in genres if g),
        "bpm": int(t.get("bpm") or 0),
        "energy": (t.get("energyLevel") or "").lower(),
        "dai_s": float(t.get("length") or 0),
        "co_loi": 1 if t.get("hasVocals") else 0,
        "url_nghe": stems.get("lqMp3Url") or "",
        "url_anh": t.get("cover") or t.get("imageUrl") or "",
        "url_trang": f"https://www.epidemicsound.com/track/{t.get('publicSlug')}/"
                     if t.get("publicSlug") else "",
    }


def them_nhac(conn, r: dict) -> bool:
    """Upsert 1 track. Trả True nếu MỚI."""
    cot = ["id", "nguon", "tieu_de", "nghe_si", "mood", "mood_goc", "genre",
           "bpm", "energy", "dai_s", "co_loi", "url_nghe", "url_anh", "url_trang"]
    d = {k: r.get(k, "") for k in cot}
    d["ngay_them"] = datetime.now(timezone.utc).isoformat()
    moi = conn.execute("SELECT 1 FROM nhac WHERE id=?", (d["id"],)).fetchone() is None
    if moi:
        conn.execute("INSERT INTO nhac({}) VALUES({})".format(
            ",".join(d), ",".join("?" * len(d))), list(d.values()))
    else:
        conn.execute("UPDATE nhac SET " + ",".join(f"{k}=?" for k in cot[2:])
                     + " WHERE id=?", [d[k] for k in cot[2:]] + [d["id"]])
        conn.execute("DELETE FROM nhac_fts WHERE id=?", (d["id"],))
    chu = " ".join(str(d.get(k) or "") for k in
                   ("tieu_de", "nghe_si", "mood", "mood_goc", "genre", "energy"))
    conn.execute("INSERT INTO nhac_fts(id, chu) VALUES(?,?)", (d["id"], chu))
    return moi


def hut_epidemic(conn, tu_khoa: str = "", moods: str = "", so_trang: int = 2,
                 log=None, tai=None) -> int:
    """Hút metadata (KHÔNG file). 1 trang ~ 40 track; giãn 1.5s giữa trang."""
    tai = tai or _get_json
    moi = 0
    for trang in range(1, so_trang + 1):
        q = {"limit": 40, "page": trang}
        if tu_khoa:
            q["term"] = tu_khoa
        if moods:
            q["moods"] = moods
        d = tai(EPIDEMIC_URL + "?" + urllib.parse.urlencode(q))
        tracks = list(((d.get("entities") or {}).get("tracks") or {}).values())
        if not tracks:
            break
        for t in tracks:
            r = parse_track(t)
            if r:
                moi += them_nhac(conn, r)
        if log:
            log(f"nhạc: trang {trang} — +{moi} track mới")
        if trang < so_trang:
            time.sleep(1.5)
    conn.commit()
    return moi


# ------------------------------------------------------------ đề xuất
def _da_dung_gan(conn, kenh: str) -> set[str]:
    """id track đã LÊN FINAL trong CHONG_LAP_TAP tập gần nhất của kênh."""
    if not kenh:
        return set()
    taps = [r[0] for r in conn.execute(
        "SELECT DISTINCT tap FROM su_kien WHERE loai='len_final' "
        "AND clip_id LIKE 'epidemic:%' AND tap LIKE ? ORDER BY ts DESC LIMIT ?",
        (f"{kenh}%", CHONG_LAP_TAP)).fetchall()]
    if not taps:
        return set()
    dau = ",".join("?" * len(taps))
    return {r[0] for r in conn.execute(
        f"SELECT DISTINCT clip_id FROM su_kien WHERE loai='len_final' "
        f"AND tap IN ({dau})", taps).fetchall()}


def de_xuat(conn, mood: str, energy: str = "", bpm_muc_tieu: int = 0,
            kenh: str = "", so: int = 8, cho_phep_loi: bool = False) -> list[dict]:
    """Track cho MỘT CHƯƠNG, xếp điểm. Mỗi track kèm `ly_do` một dòng —
    editor biết vì sao máy đưa, không phải đoán."""
    da_dung = _da_dung_gan(conn, kenh)
    rows = conn.execute(
        "SELECT * FROM nhac WHERE trang_thai != 'loai_tru'"
        + ("" if cho_phep_loi else " AND co_loi=0")).fetchall()
    ra = []
    for r in rows:
        d = dict(r)
        diem, vi = 0.0, []
        if mood and d["mood"] == mood:
            diem += 10
            vi.append(d["mood"])
        elif mood and mood in (d["mood_goc"] or ""):
            diem += 6
            vi.append(mood)
        if energy and d["energy"] == energy:
            diem += 4
            vi.append(d["energy"])
        if bpm_muc_tieu and d["bpm"]:
            lech = abs(d["bpm"] - bpm_muc_tieu)
            diem += max(0.0, 3.0 - lech / 20.0)      # lệch 60bpm = mất hết
            vi.append(f"{d['bpm']}bpm")
        if d["id"] in da_dung:
            diem -= 8
            vi.append(f"đã dùng {CHONG_LAP_TAP} tập gần")
        d["diem"] = round(diem, 2)
        d["ly_do"] = ", ".join(vi) or "chưa khớp trục nào"
        ra.append(d)
    ra.sort(key=lambda x: -x["diem"])
    return ra[:so]


def tim_nhac(conn, q: str = "", mood: str = "", limit: int = 40) -> list[dict]:
    dk, tham = ["n.trang_thai != 'loai_tru'"], []
    if mood:
        dk.append("n.mood=?")
        tham.append(mood)
    if q.strip():
        tokens = re.findall(r"[\w]+", q)
        fts = " OR ".join(f'"{t}"' for t in tokens)
        rows = conn.execute(
            f"SELECT n.*, bm25(nhac_fts) hang FROM nhac_fts f JOIN nhac n ON n.id=f.id "
            f"WHERE nhac_fts MATCH ? AND {' AND '.join(dk)} ORDER BY hang LIMIT ?",
            [fts, *tham, limit]).fetchall()
    else:
        rows = conn.execute(
            f"SELECT n.* FROM nhac n WHERE {' AND '.join(dk)} "
            f"ORDER BY n.ngay_them DESC LIMIT ?", [*tham, limit]).fetchall()
    ra = []
    for r in rows:
        d = dict(r)
        d.pop("hang", None)
        ra.append(d)
    # nhãn "đã dùng": track chảy qua tập nào (flow 06/09 — Library là nơi xem
    # cái đã tích tụ, nên phải thấy được vết sử dụng)
    if ra:
        dau = ",".join("?" * len(ra))
        dung: dict[str, list] = {}
        for cid, tap, loai in conn.execute(
                f"SELECT clip_id, tap, loai FROM su_kien WHERE clip_id IN ({dau}) "
                f"AND loai IN ('duoc_chon','len_final')", [d["id"] for d in ra]):
            if tap:
                dung.setdefault(cid, []).append((tap, loai))
        for d in ra:
            v = dung.get(d["id"]) or []
            fin = sorted({t for t, lo in v if lo == "len_final"})
            chon = sorted({t for t, lo in v if lo == "duoc_chon"})
            d["da_dung"] = (" · ".join(f"✓{t}" for t in fin[-3:])
                            + (" " if fin and chon else "")
                            + " ".join(chon[-3:] if not fin else [])).strip()
    return ra
