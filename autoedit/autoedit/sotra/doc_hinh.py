r"""ĐỌC HÌNH để biết NHÂN VẬT — tuổi · chủng tộc · vật thể · cỡ cảnh (QĐ15, 12/09).

Vì sao có file này. Kho 17.039 clip, trong đó **8.524 clip stock chưa bao giờ
được đọc hình**: `subject` của chúng chỉ là tiêu đề người bán bị xé chữ —

    tieu_de: "Man Counts Money at Glass Table in Office"
    subject: "counts,money,glass,table"      <- không ai xem hình này

nên tiêu đề nói dối là cả dây chuyền tin theo. Đo thật 12/09: câu "đột quỵ không
rải đều trong ngày" nhận `Sunrise at Andes Mountains... foggy morning` (nhờ chữ
`morning`), câu "phân tích 12.000 ca đột quỵ" nhận cờ Ecuador + mũi tên tăng
trưởng. Còn ref thì đã có mắt (`doc_canh` đọc 7.322 cảnh) — đó đúng là lý do
Life In chạy được mà Senior Health thì không.

Đã kiểm vision đọc được thật (12/09): 5/5 clip tiêu đề "Senior" -> `older`,
5/5 clip "Family" -> `young`/`mixed`, không cái nào nhầm; cỡ cảnh cũng đúng.
551 clip khay SH010 mất 8 phút ở 3 luồng, 3 lỗi (403 ảnh cover).

Ba luật của file này:
  · một clip đọc MỘT LẦN (`doc_nguoi=1`) — tiền thật, và clip nằm kho vĩnh viễn
  · lỗi một clip KHÔNG giết cả lô, và clip lỗi để `doc_nguoi=0` cho lần sau
  · giá trị lạ thì để TRỐNG, không bịa — ghi sai một lần là cửa nhân vật sai mãi
"""

from __future__ import annotations

import base64
import json
import subprocess
import sqlite3
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from autoedit.sotra import db as sdb

LUONG = 3          # PB3-B2: >3 luồng/khoá bigmodel cắt kết nối
TIMEOUT = 90

# Bộ giá trị ĐÓNG. Thêm giá trị = đọc lại kho, nên đừng thêm cho vui.
TUOI = ("child", "young", "middle", "older", "mixed", "none")
CHUNG_TOC = ("white", "black", "asian", "latino", "mixed", "unclear", "none")
CANH = ("close", "medium", "wide", "aerial")

# Model hay trả từ đồng nghĩa. Gom về bộ đóng, còn lại để TRỐNG.
_DONG_NGHIA_TUOI = {"elderly": "older", "senior": "older", "old": "older",
                    "older adult": "older", "old man": "older", "old woman": "older",
                    "young adult": "young", "youth": "young", "teen": "young",
                    "adult": "middle", "middle-aged": "middle", "middle aged": "middle",
                    "kid": "child", "baby": "child", "infant": "child",
                    "no people": "none", "nobody": "none"}
_DONG_NGHIA_CANH = {"close-up": "close", "closeup": "close", "close up": "close",
                    "medium close": "close", "extreme close": "close",
                    "wide shot": "wide", "full": "wide", "drone": "aerial",
                    "bird's eye": "aerial", "overhead": "aerial"}

CAU_LENH = """Bạn xem hình và trả DUY NHẤT JSON, không thêm chữ nào:
{"ai":"...","tuoi":"...","chung_toc":"...","object":"...","co_canh":"..."}

ai        : ai có trong hình, 1-4 từ tiếng Anh ("older woman", "young family",
            "no people"). Không có người thì "no people".
tuoi      : child / young / middle / older / mixed / none
            "older" = từ khoảng 60 tuổi trở lên (tóc bạc, da nhăn, dáng lớn tuổi)
chung_toc : white / black / asian / latino / mixed / unclear / none
object    : 3-6 vật thể NHÌN THẤY RÕ, cách nhau dấu phẩy, tiếng Anh
co_canh   : close / medium / wide / aerial"""


def _chuan(x: str, bo: tuple, dong_nghia: dict) -> str:
    v = str(x or "").strip().lower()
    if v in bo:
        return v
    return dong_nghia.get(v, "") if dong_nghia.get(v, "") in bo else ""


def chuan_tuoi(x: str) -> str:
    return _chuan(x, TUOI, _DONG_NGHIA_TUOI)


def chuan_chung_toc(x: str) -> str:
    return _chuan(x, CHUNG_TOC, {})


def chuan_canh(x: str) -> str:
    return _chuan(x, CANH, _DONG_NGHIA_CANH)


# ------------------------------------------------------------------ lấy ảnh
def anh_cua(r: dict, ffmpeg: str = "ffmpeg") -> bytes | None:
    """Một tấm ảnh đại diện clip. stock -> ảnh cover; ref/kho -> frame GIỮA khúc.

    Giữa khúc chứ không phải đầu: đầu khúc hay là frame chuyển cảnh (mờ/đen).
    """
    from autoedit.library.vision import shrink_for_api

    if r.get("url_anh"):
        # UA GIẢ TRÌNH DUYỆT — dùng chung `hut.UA` (BH4: một khái niệm một chỗ).
        # Chạy thật 13/09: urllib trần đọc được envato 322/322 nhưng pexels 0/191
        # và pixabay 0/179 ăn 403 Forbidden. `hut.py` gửi UA từ đầu, file này thì
        # không -> hỏng CHỈ MỘT PHẦN, dễ tưởng là xong.
        from autoedit.sotra.hut import UA

        req = urllib.request.Request(
            r["url_anh"], headers={"User-Agent": UA,
                                   "Accept-Language": "en-US,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=30) as f:
            return shrink_for_api(f.read())
    p = str(r.get("path_local") or "")
    if not p or not Path(p).is_file():
        return None
    t0, t1 = float(r.get("t0") or 0), float(r.get("t1") or 0)
    giua = t0 + max(0.0, t1 - t0) / 2
    with tempfile.TemporaryDirectory() as d:
        o = Path(d) / "f.jpg"
        subprocess.run([ffmpeg, "-ss", f"{max(0.0, giua):.3f}", "-i", p,
                        "-frames:v", "1", "-vf", "scale=960:-2", "-y", str(o)],
                       capture_output=True, timeout=TIMEOUT)
        return o.read_bytes() if o.is_file() else None


def _goi_glm(img: bytes) -> dict:
    from autoedit.library import vision

    body = {"model": vision.DEFAULT_GLM_VISION_MODEL, "temperature": 0,
            "max_tokens": 400, "thinking": {"type": "disabled"},
            "messages": [{"role": "system", "content": CAU_LENH},
                         {"role": "user", "content": [
                             {"type": "image_url", "image_url": {
                                 "url": "data:image/jpeg;base64,"
                                        + base64.standard_b64encode(img).decode("ascii")}},
                             {"type": "text", "text": "Trả JSON cho hình này."}]}]}
    req = urllib.request.Request(
        vision.glm_api_url(), data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + vision.glm_api_keys()[0]})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as f:
        d = json.loads(f.read())
    txt = ((d.get("choices") or [{}])[0].get("message", {}) or {}).get("content") or ""
    if not txt.strip():
        raise ValueError("GLM trả content rỗng")
    return json.loads(vision._clean_json(txt))


def doc_that(r: dict) -> dict:
    """Đọc hình THẬT một clip (lấy ảnh + gọi GLM). Dùng làm `doc=` mặc định."""
    img = anh_cua(r)
    if img is None:
        raise ValueError("không lấy được ảnh của clip")
    return _goi_glm(img)


# ------------------------------------------------------------------ điền kho
def bo_sung(conn: sqlite3.Connection, ids, doc=None, luong: int = LUONG,
            log=None) -> int:
    """Đọc hình những clip CHƯA đọc trong `ids`. Trả số clip đọc được.

    `doc(row_dict) -> dict` tiêm được (test không mạng). Đọc xong ghi
    `doc_nguoi=1` — kể cả khi model trả toàn giá trị lạ: đã tốn tiền xem hình
    rồi, xem lại cũng ra thế.
    """
    doc = doc or doc_that
    can: list[dict] = []
    for cid in ids:
        r = conn.execute("SELECT * FROM clip WHERE id=? AND COALESCE(doc_nguoi,0)=0",
                         (cid,)).fetchone()
        if r is not None:
            can.append(dict(r))
    if not can:
        return 0
    if log:
        log(f"đọc hình: {len(can)} clip chưa có nhân vật")

    def _mot(r: dict):
        try:
            return r, doc(r), ""
        except Exception as exc:  # noqa: BLE001
            return r, None, f"{type(exc).__name__}: {str(exc)[:70]}"

    xong = loi = 0
    with ThreadPoolExecutor(max_workers=max(1, luong)) as ex:
        for r, d, err in ex.map(_mot, can):
            if d is None:
                loi += 1
                if log and loi <= 3:
                    log(f"đọc hình LỖI {r['id']}: {err}")
                continue                      # doc_nguoi giữ 0 -> lần sau đọc lại
            tuoi = chuan_tuoi(d.get("tuoi"))
            ct = chuan_chung_toc(d.get("chung_toc"))
            canh = chuan_canh(d.get("co_canh"))
            ai = str(d.get("ai") or "").strip().lower()[:60]
            obj = str(d.get("object") or "").strip().lower()[:300]
            # `vat_the` của ref do `doc_canh` liệt kê rất kỹ — KHÔNG ghi đè.
            vat_the = r.get("vat_the") or obj
            conn.execute(
                "UPDATE clip SET tuoi=?, chung_toc=?, doc_nguoi=1, "
                "shot=COALESCE(NULLIF(?,''), shot), people=COALESCE(NULLIF(?,''), people), "
                "vat_the=? WHERE id=?",
                (tuoi, ct, canh, ai, vat_the, r["id"]))
            sdb.lam_moi_fts(conn, r["id"])
            xong += 1
    conn.commit()
    if log:
        log(f"đọc hình: xong {xong} clip, lỗi {loi}")
    return xong
