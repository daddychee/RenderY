"""Tra thư viện niche local TRƯỚC khi đi stock (P6) — đã người duyệt, rủi ro cấn ≈ 0."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path

from autoedit.library import db
from autoedit.project import SearchQueries

# --- Geo-gate (PA2, 20/06): chặn footage SAI QUỐC GIA ----------------------------
# Thư viện sắp xếp 'Khu Vực <Region> (English)/<QUỐC GIA>/<sub>/...'. Cây khác
# (signature/NGHỈ HƯU/...) = phi-địa-lý. Quốc gia (segment sau region-header) là tín
# hiệu địa danh đáng tin nhất (segment sâu hơn lẫn 'VIDEO'/'1'/'Storyblock').
_GEO_ROOT_PREFIX = "khuvuc"   # blob của "Khu Vực ..."


def _blob(s: str) -> str:
    """Bỏ dấu + thường hoá + bỏ ký tự không alnum -> token liền. Khớp địa danh bất chấp
    khoảng trắng/dấu: 'Việt Nam' -> 'vietnam', 'HA GIANG' -> 'hagiang'."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _country_of(folder_path: str) -> str:
    """Blob tên QUỐC GIA của clip; '' nếu clip KHÔNG nằm trong cây địa lý (không gate)."""
    segs = [s for s in re.split(r"[\\/]+", folder_path) if s.strip()]
    if len(segs) < 2 or not _blob(segs[0]).startswith(_GEO_ROOT_PREFIX):
        return ""
    return _blob(segs[1])


def passes_geo(folder_path: str, script_blob: str) -> bool:
    """Clip qua geo-gate? Phi-địa-lý (signature) LUÔN qua; còn lại chỉ qua khi QUỐC GIA của
    clip xuất hiện trong script. Chặn footage sai nước (video Mỹ ra Hà Giang/Albania/Kenya).
    Video Việt Nam (script có 'vietnam') vẫn dùng được mọi cảnh Việt Nam. Khán giả > tái dùng."""
    country = _country_of(folder_path)
    return not country or country in script_blob


# --- C6 drop-list (C đợt 1, 2026-07-09 — MO_TA_VAN_HANH_C_DOT_1.md): GLM tag từ
# frame TĨNH nên kho KHÔNG BAO GIỜ có tag chuyển động — query mang từ camera/chuyển
# động AND-trượt oan (PB8: 'spiral galaxy rotating' 0 khớp dù kho 39 clip spiral
# galaxy). Bỏ các từ đó TRƯỚC khi match: kết quả query gốc luôn là tập con của query
# đã bỏ (AND ít điều kiện hơn) nên không mất khớp nào, chỉ thêm — phễu c5 vẫn chấm.
# CHỈ từ camera/thời-gian; KHÔNG đụng từ sự kiện có nghĩa (explosion, eruption...).
_MOTION_PHRASES = (
    "zooming in", "zooming out", "zoom in", "zoom out", "slow motion", "time lapse",
    "flying through", "fly through", "flying over", "fly over", "pull back",
)
_MOTION_WORDS = frozenset({
    "rotating", "rotation", "spinning", "revolving", "orbiting", "swirling",
    "timelapse", "time-lapse", "hyperlapse", "zoom", "zooming", "zoomed",
    "panning", "drifting", "floating", "flyover", "flythrough",
    "pulsing", "flickering", "shimmering",
})


def _strip_motion_terms(query: str) -> str:
    """Bỏ từ/cụm chuyển động khỏi query local (C6). Bỏ hết sạch -> giữ NGUYÊN query gốc."""
    q = " " + " ".join(query.lower().split()) + " "   # đệm space: cụm chỉ khớp trọn token
    for ph in _MOTION_PHRASES:
        q = q.replace(f" {ph} ", " ")
    kept = [t for t in q.split() if t not in _MOTION_WORDS]
    return " ".join(kept) if kept else query


# D3 (C đợt 2, 2026-07-09 — MO_TA_VAN_HANH_C_DOT_2.md): trần TỔNG ứng viên local/beat,
# TÁCH khỏi limit per-query (5, giữ nguyên). Số 5 cũ gánh cả 2 vai từ hồi kho 282 asset;
# kho 1874 + C6 mở recall (query khớp 80-742) -> query đầu nuốt hết suất, các query sau
# vô nghĩa. Pool phễu/beat ~12,5 -> tối đa ~17-18; prompt batch PA-1 +~5 dòng/beat.
LOCAL_TOTAL_CAP = 10


def _used_paths(used_keys: set[str] | None) -> set[str]:
    """asset_key local ('local:<path>') -> path, cho exclude_paths của db.
    P7-trước-limit (bug DS3-084): lọc đã-dùng phải nằm TRƯỚC nhát cắt limit."""
    if not used_keys:
        return set()
    return {k[len("local:"):] for k in used_keys if k.startswith("local:")}


def find_local_candidates(
    conn: sqlite3.Connection, niche: str, queries: SearchQueries, limit: int = 5,
    script_text: str = "", used_keys: set[str] | None = None,
    own_only: bool = False, no_people: bool = False,
) -> list[dict]:
    """Ứng viên local — tier `local` (C4, viết theo vocab tag kho) TRƯỚC, rồi `specific`.

    Vì sao CẤM broad/thematic (sửa 20/06, bug thật): 2 tier đó do LLM cố ý để
    GENERIC 2 từ, KHÔNG địa danh ('remote forest', 'small town', 'rural worker') làm lưới
    vớt cho Pexels. Nếu cho local match các tier đó, footage SAI ĐỊA DANH bị kéo lên và
    (vì local ghép trước Pexels, không có cổng relevance) ĐÈ luôn footage đúng của Pexels:
    video Alaska ra cảnh Hà Giang; video Hà Nội ra cảnh Hà Giang — khán giả thoát ngay.
    Tier specific mang địa danh ('alaska bush aerial', 'hanoi old quarter') -> AND-match
    trong search_assets tự lọc đúng nơi (clip Hà Giang không có chữ 'alaska'/'hanoi' -> loại).
    Tier local (C4) được match vì KHÔNG generic: NÃO viết theo danh sách từ vựng tag thật
    của kho (mục TỪ VỰNG KHO trong direct_context.md) — và geo-gate PA2 vẫn gác mọi ứng viên.
    KHÁN GIẢ > tái dùng siêu dữ liệu: thà đi Pexels còn hơn chiếu sai địa danh.

    Trả list dict: {asset_key, path, media_type, description} (đồng dạng với pexels).
    """
    if not niche:
        return []
    script_blob = _blob(script_text) if script_text else ""
    exclude = _used_paths(used_keys)
    results: list[dict] = []
    seen: set[str] = set()
    for q in list(queries.local) + list(queries.specific):
        # C6: bỏ từ chuyển động (GLM không tag được từ frame tĩnh) rồi mới AND-match
        for row in db.search_assets(conn, niche, _strip_motion_terms(q), limit=limit,
                                    exclude_paths=exclude, own_only=own_only,
                                    no_people=no_people):
            if row["path"] in seen:
                continue
            seen.add(row["path"])
            # dòng db cũ trỏ file đã xóa/di chuyển (chưa re-index) -> bỏ qua
            if not Path(row["path"]).is_file():
                continue
            # PA2 geo-gate: bỏ clip SAI QUỐC GIA so với script (chỉ khi có script_text)
            if script_blob and not passes_geo(row.get("folder_path", ""), script_blob):
                continue
            results.append(_row_to_candidate(row))
    return results[:LOCAL_TOTAL_CAP]


# REF (user chốt 2026-07-11): trần số cảnh nguồn-mẫu CHÈN thêm vào pool mỗi beat —
# pool hiện ~15-28, +6 không phình token batch PA-1.
REF_INJECT_CAP = 6
# BOOST (user chốt 2026-07-17): trần cảnh sở-thích-khán-giả chèn/beat — cùng cỡ REF.
BOOST_INJECT_CAP = 6
_REF_QUERY_STOPWORDS = frozenset({
    "a", "an", "the", "in", "on", "at", "of", "with", "and", "or", "to", "from", "for",
})
# REF THEO CHƯƠNG (VD2, user chốt 2026-07-18): folder con "Chapter N" ngay dưới folder
# --ref = mẫu RIÊNG chương N. Khuôn tên nhận cả tiếng Việt; so trên path đã lower().
_REF_CHAPTER_PAT = re.compile(r"(?:chapter|chuong|chương|ch)[\s_-]*(\d+)")


def ref_chapter_scan(
    conn: sqlite3.Connection, niche: str, ref_prefixes: tuple[str, ...],
) -> tuple[dict[int, tuple[str, ...]], dict]:
    """VD2 ref-theo-chương: quét sổ 1 LẦN lúc vào stage source — path cảnh mẫu có segment
    'Chapter N' NGAY DƯỚI prefix --ref -> cảnh thuộc RIÊNG chương N; còn lại (file ở gốc,
    folder con tên khác khuôn) = mẫu CHUNG. Đọc PATH trong sổ, KHÔNG quét đĩa. Prefix trả
    về gồm cả dấu phân cách sau tên folder ('chapter 1\\' không nuốt 'chapter 10\\').
    Trả (map chương -> prefixes, đếm cảnh theo chương + 'chung') cho tầng ĐO."""
    if not niche or not ref_prefixes:
        return {}, {}
    # substr thay LIKE — cùng lý do fix 2026-07-17 ở find_ref_candidates (PG coi `\` là
    # ESCAPE của pattern LIKE -> prefix Windows match hụt im lặng)
    sql = ("SELECT source_video FROM library_assets WHERE niche = ? AND ("
           + " OR ".join("substr(lower(source_video), 1, ?) = ?" for _ in ref_prefixes)
           + ")")
    params: list = [niche]
    for p in ref_prefixes:
        params += [len(p), p]
    mapping: dict[int, set[str]] = {}
    counts: dict = {}
    for r in conn.execute(sql, params).fetchall():
        low = str(r["source_video"] or "").lower()
        ch = None
        hinhtho = False
        for p in ref_prefixes:
            if not low.startswith(p):
                continue
            rest = low[len(p):].lstrip("\\/")
            m = re.match(r"([^\\/]+)[\\/]", rest)   # file ngay gốc (không segment con) -> chung
            if m:
                pm = _REF_CHAPTER_PAT.fullmatch(m.group(1).strip())
                if pm:
                    ch = int(pm.group(1))
                    # prefix cắt tới HẾT dấu phân cách sau tên folder chương
                    mapping.setdefault(ch, set()).add(low[:len(low) - len(rest) + m.end()])
                elif _blob(m.group(1)) == "hinhtho":
                    # M4d: cảnh HINH THO bị tước chèn REF (ref_excludes) — đếm riêng
                    # để warning "chung=N" không phồng số cảnh không bao giờ được chèn
                    hinhtho = True
            break  # prefix đầu trúng là đủ (khai prefix chồng nhau hiếm, hành xử ổn định)
        key = ch if ch is not None else ("hinh_tho" if hinhtho else "chung")
        counts[key] = counts.get(key, 0) + 1
    return {n: tuple(sorted(ps)) for n, ps in mapping.items()}, counts


def ref_hinhtho_scan(
    conn: sqlite3.Connection, niche: str, ref_prefixes: tuple[str, ...],
) -> dict:
    """M4d (user chốt 2026-07-21): folder `HINH THO` NGAY DƯỚI folder --ref = footage
    editor DÀNH RIÊNG cho đoạn chèn Δ sau chương / mini-hook đầu video — KHÔNG chèn
    REF vào beat thường (ledger.ref_excludes tước chèn+bonus; search thường vẫn vớt
    được — mềm, y tiền lệ REF theo chương).

    Con của HINH THO: `chapter N` -> Δ riêng chương N; `mini hook` -> để dành tính
    năng mini-hook đầu video (chưa tiêu thụ); còn lại/file ở gốc -> "chung" (mọi Δ).
    Đọc PATH sổ (source_video) không quét đĩa; substr thay LIKE (vết PG escape).
    Trả {"all": (prefix,...), "by_chapter": {n: (prefix,...)}, "chung": (prefix,...),
    "minihook": (prefix,...), "counts": {...}} — "all" rỗng = không có HINH THO."""
    if not niche or not ref_prefixes:
        return {"all": (), "by_chapter": {}, "chung": (), "minihook": (), "counts": {}}
    sql = ("SELECT source_video FROM library_assets WHERE niche = ? AND ("
           + " OR ".join("substr(lower(source_video), 1, ?) = ?" for _ in ref_prefixes)
           + ")")
    params: list = [niche]
    for p in ref_prefixes:
        params += [len(p), p]
    roots: set[str] = set()
    by_ch: dict[int, set[str]] = {}
    chung: set[str] = set()
    minihook: set[str] = set()
    counts: dict = {}
    for r in conn.execute(sql, params).fetchall():
        low = str(r["source_video"] or "").lower()
        for p in ref_prefixes:
            if not low.startswith(p):
                continue
            rest = low[len(p):].lstrip("\\/")
            m = re.match(r"([^\\/]+)[\\/]", rest)
            if not m or _blob(m.group(1)) != "hinhtho":
                break                      # không thuộc HINH THO -> đường REF thường lo
            root = low[:len(low) - len(rest) + m.end()]
            roots.add(root)
            sub = rest[m.end():]
            m2 = re.match(r"([^\\/]+)[\\/]", sub)
            key: object = "chung"
            if m2:
                seg = m2.group(1).strip()
                pm = _REF_CHAPTER_PAT.fullmatch(seg)
                sub_prefix = root + sub[:m2.end()]
                if pm:
                    key = int(pm.group(1))
                    by_ch.setdefault(key, set()).add(sub_prefix)
                elif _blob(seg) == "minihook":
                    key = "minihook"
                    minihook.add(sub_prefix)
                else:
                    chung.add(sub_prefix)  # folder con tên khác khuôn = chung
            counts[key] = counts.get(key, 0) + 1
            break
    return {"all": tuple(sorted(roots)),
            "by_chapter": {n: tuple(sorted(ps)) for n, ps in by_ch.items()},
            "chung": tuple(sorted(chung)), "minihook": tuple(sorted(minihook)),
            "counts": counts}


def find_ref_candidates(
    conn: sqlite3.Connection, niche: str, ref_prefixes: tuple[str, ...],
    queries: SearchQueries, script_text: str = "", limit: int = REF_INJECT_CAP,
    used_keys: set[str] | None = None, exclude_prefixes: tuple[str, ...] = (),
) -> list[dict]:
    """Lưới vớt NGUỒN MẪU CỦA BÀI (user chốt 2026-07-11): editor đã chọn video mẫu đúng
    đề tài nên relevance tiên nghiệm cao — match NỚI (trúng ≥1 từ của tier local/specific)
    CHỈ trong tập cảnh có source_video thuộc prefix khai --ref, rồi CHÈN vào pool cho
    phễu chấm nghĩa/mood như mọi ứng viên. Khác kho chung (AND-match chặt vì đủ mọi đề
    tài): tập mẫu đã được NGƯỜI khoanh vùng, nới recall là chủ đích. Không trúng từ nào
    (beat ẩn dụ chủ đích) -> KHÔNG chèn — không nhiễu pool.

    Xếp theo số từ trúng giảm dần (hòa giữ thứ tự approved/indexed_at của DB). Geo-gate
    PA2 + ledger gate (kề + trần) vẫn gác SAU hàm này — chèn ≠ miễn pháp lý."""
    if not niche or not ref_prefixes:
        return []
    words: list[str] = []
    for q in list(queries.local) + list(queries.specific):
        for w in _strip_motion_terms(q).lower().split():
            w = w.strip(".,;:!?'\"()")
            if len(w) >= 3 and w not in _REF_QUERY_STOPWORDS and w not in words:
                words.append(w)
    if not words:
        return []
    # So prefix bằng substr thay LIKE (fix 2026-07-17): trên Postgres dấu `\` trong
    # pattern LIKE là ký tự ESCAPE -> prefix Windows `f:\space\...` match hụt = REF
    # chạy RỖNG im lặng trên máy đã flip PG (SQLite không sao nên test cũ không lộ).
    # substr không có pattern language — 2 lưng hành xử y nhau.
    sql = ("SELECT * FROM library_assets WHERE niche = ? AND ("
           + " OR ".join("substr(lower(source_video), 1, ?) = ?" for _ in ref_prefixes)
           + ") ORDER BY approved DESC, indexed_at DESC, id DESC")  # tie-break G2 như search_assets
    params: list = [niche]
    for p in ref_prefixes:
        params += [len(p), p]
    rows = conn.execute(sql, params).fetchall()
    script_blob = _blob(script_text) if script_text else ""
    scored: list[tuple[int, dict]] = []
    for r in rows:
        row = dict(r)
        # REF theo chương (VD2 mềm): cảnh chương KHÁC beat đang dựng mất suất CHÈN
        # (nhường slot đúng chương) — search thường vẫn vớt được, không phải cửa loại
        if exclude_prefixes and str(row.get("source_video") or "").lower().startswith(exclude_prefixes):
            continue
        blob = " ".join(str(row.get(k) or "") for k in ("subject", "description", "tags")).lower()
        n_hit = sum(1 for w in words if w in blob)
        if n_hit:
            scored.append((n_hit, row))
    scored.sort(key=lambda t: -t[0])  # sort ổn định: hòa giữ thứ tự DB
    exclude = _used_paths(used_keys)  # P7-trước-limit (bug DS3-084)
    results: list[dict] = []
    for _, row in scored:
        if row["path"] in exclude:
            continue
        if not Path(row["path"]).is_file():
            continue
        if script_blob and not passes_geo(row.get("folder_path", ""), script_blob):
            continue
        results.append(_row_to_candidate(row))
        if len(results) >= limit:
            break
    return results


def _row_to_candidate(row: dict) -> dict:
    """Dòng DB -> dict ứng viên đồng dạng pexels. Mang theo tag vision (shot_size/mood)
    cho phễu c5/c7 — trước đây bị đánh rơi (bug ghi ở foundation c7)."""
    cand = {
        "asset_key": f"local:{row['path']}",
        "path": row["path"],
        "media_type": row["media_type"],
        "description": row["subject"],
        "source": "local",
        "shot_size": row.get("shot_size", ""),
        "mood": row.get("mood", ""),
    }
    # BOOST: tags lên ứng viên để nhãn is_boost match tại chokepoint (chống vết PB7
    # cột-rơi). search_assets trả list đã parse JSON; đường ref SQL thô trả string.
    tags = row.get("tags")
    if tags:
        cand["tags"] = " ".join(tags) if isinstance(tags, list) else str(tags)
    # PB7: duration vào phễu (cửa clip-quá-ngắn + điểm khớp-độ-dài). Asset cũ trước
    # migrate PB4 có duration 0/NULL -> KHÔNG gắn key (phễu coi là không rõ, không loại oan).
    if row.get("duration"):
        cand["duration"] = float(row["duration"])
    # VD4 ghi công: kênh nguồn lên ứng viên -> ShotPick (chống vết PB7 cột-rơi).
    # KHÔNG vào điểm/lọc — chỉ truy vết + credit overlay.
    if row.get("source_channel"):
        cand["source_channel"] = row["source_channel"]
    # C8 gói CHỌN: ứng viên viral mang nhãn nguồn gốc cho ViralLedger gate (luật 3 + 5)
    if row.get("source_class") == "viral":
        cand.update(source_class="viral", source_video=row.get("source_video", ""),
                    scene_index=int(row.get("scene_index") or 0),
                    source_duration=float(row.get("source_duration") or 0))
        # ytref: cờ điểm nhô vào ứng viên (chống vết PB7 cột-rơi) — ledger đọc để
        # miễn luật kề; M3 sẽ đọc thêm cho PEAK_BONUS
        if row.get("peak_value") is not None:
            cand.update(peak_value=float(row["peak_value"]),
                        peak_type=row.get("peak_type") or "")
    return cand


def find_signature_candidates(conn: sqlite3.Connection, niche: str, limit: int = 5,
                              used_keys: set[str] | None = None) -> list[dict]:
    """Ứng viên từ thư mục signature/ (luật c6): CHỈ gom cho beat HOOK hoặc SLOT CHÊM,
    xếp LÊN ĐẦU danh sách THU. Không điểm, không lọc — veto nghĩa c2 vẫn áp ở phễu."""
    if not niche:
        return []
    return [
        _row_to_candidate(row)
        for row in db.signature_assets(conn, niche, limit=limit,
                                       exclude_paths=_used_paths(used_keys))
        if Path(row["path"]).is_file()
    ]


def find_boost_candidates(
    conn: sqlite3.Connection, niche: str, boost_terms: tuple[str, ...],
    script_text: str = "", used_keys: set[str] | None = None,
    limit: int = BOOST_INJECT_CAP,
) -> list[dict]:
    """Chèn cảnh SỞ THÍCH KHÁN GIẢ (BOOST, user chốt 2026-07-17): editor/niche khai
    cảnh dạng X (--boost / audience_bias) — CHỈ KHO local (editor thật né Pexels),
    AND-match từng term qua search_assets (term viết theo từ vựng tag kho). Chèn vào
    pool cho phễu chấm như mọi ứng viên — bonus/nhãn is_boost gắn ở chokepoint
    _gather_candidates, KHÔNG gắn ở đây (nhãn trên bản chèn RƠI theo dedup — vết PB7).

    Cùng 3 cửa với find_local/find_ref (P5 đã rà): file tồn tại + geo-gate PA2
    (X sai quốc gia không vào bài — phụ nữ phố Tokyo không vào bài Pháp) + loại
    đã-dùng TRƯỚC limit (bug DS3-084). Ledger gate (kề + trần) vẫn gác SAU hàm này."""
    if not niche or not boost_terms:
        return []
    script_blob = _blob(script_text) if script_text else ""
    exclude = _used_paths(used_keys)
    results: list[dict] = []
    seen: set[str] = set()
    for term in boost_terms:
        q = _strip_motion_terms(term)  # C6: GLM không tag từ chuyển động từ frame tĩnh
        if not q.strip():
            continue
        for row in db.search_assets(conn, niche, q, limit=limit, exclude_paths=exclude):
            if row["path"] in seen:
                continue
            seen.add(row["path"])
            if not Path(row["path"]).is_file():
                continue
            if script_blob and not passes_geo(row.get("folder_path", ""), script_blob):
                continue
            results.append(_row_to_candidate(row))
            if len(results) >= limit:
                return results
    return results
