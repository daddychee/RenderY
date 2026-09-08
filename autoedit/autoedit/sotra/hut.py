r"""HÚT nguồn vào Sổ Tra — Envato (scraping preview công khai) + Pexels/Pixabay
(API chính thức, key sẵn trong .env/két) + nạp REF từ thư mục tập.

RÓN RÉN là luật (bài học YouTube ~9 lượt bị chặn IP + Envato cấm tải song song):
1 luồng tuần tự, giãn nhịp ngẫu nhiên GIAN_NHIP giữa 2 request, fail-open từng
từ khóa (lỗi thì ghi log đi tiếp, không giết phiên).

Hút CHỈ lấy metadata + URL (ảnh/video preview hotlink được trong app) — không
tải file nào về. Frames JPEG rút LAZY khi cần (media.py).
"""

from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from autoedit.sotra import db as sdb
from autoedit.sotra.tag7 import tag_tu_tieu_de

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
GIAN_NHIP = (2.5, 5.0)


def _get(url: str, headers: dict | None = None, timeout: float = 45.0) -> bytes:
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read()


# ------------------------------------------------------------ ENVATO (scraping)
def hut_envato(tu_khoa: str, trang: int = 1) -> list[dict]:
    """1 trang search công khai -> clip records. Đã kiểm 06/09: 200 OK không cần
    login; ảnh cover phải GIỮ NGUYÊN query (có chữ ký, tự chế là 403); video
    preview watermarked URL BỀN không ký."""
    q = urllib.parse.quote_plus(tu_khoa)
    # orientation=horizontal (user chốt 06/09: bỏ video dọc ngay từ nguồn)
    url = (f"https://elements.envato.com/stock-video/{q}?orientation=horizontal"
           + (f"&page={trang}" if trang > 1 else ""))
    h = _get(url).decode("utf-8", "replace")
    mp4: dict[str, str] = {}
    for m in re.finditer(r'https://video-previews\.elements\.envatousercontent\.com/'
                         r'([0-9a-f-]{36})/watermarked_preview/watermarked_preview\.mp4', h):
        mp4[m.group(1)] = m.group(0)
    ra, thay = [], set()
    # URL ITEM THẬT (user chốt 06/09 — "ghi URL + mã đuôi, đừng chỉ tên file"):
    # card = ảnh cover -> item-href ĐẦU TIÊN SAU ảnh (đã verify 06/09). Thiếu mã
    # là sau này item trôi hạng không tìm lại được để tải bản licensed.
    mau_item = re.compile(r'href="(/[a-z0-9][a-z0-9-]{10,}-[A-Z0-9]{7,8})"')
    mau = (r'<img[^>]+src="(https://elements-resized\.envatousercontent\.com/'
           r'elements-video-cover-images/([0-9a-f-]{36})/video_preview/'
           r'video_preview_\d{4}\.jpg[^"]*)"[^>]*alt="([^"]{5,160})"')
    for m in re.finditer(mau, h):
        uid = m.group(2)
        if uid in thay:
            continue
        thay.add(uid)
        ten = re.sub(r"\s+", " ", m.group(3)).strip()
        # user chốt 06/09: greenscreen/chroma/video dọc KHÔNG vào kho
        if re.search(r"green\s*screen|chroma|vertical|portrait|9\s*:\s*16",
                     ten, re.I):
            continue
        href = next((x.group(1) for x in mau_item.finditer(h, m.end())), "")
        ra.append({"id": sdb.lam_id("envato", uid), "nguon": "envato", "tieu_de": ten,
                   "url_trang": ("https://elements.envato.com" + href) if href else "",
                   "url_anh": m.group(1).replace("&amp;", "&"),
                   "url_video": mp4.get(uid, ""), "tu_khoa_hut": tu_khoa,
                   **tag_tu_tieu_de(ten)})
    return ra


# ------------------------------------------------------------ PEXELS (API)
def hut_pexels(tu_khoa: str, trang: int = 1, per_page: int = 40) -> list[dict]:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("thiếu PEXELS_API_KEY")
    d = json.loads(_get(
        "https://api.pexels.com/videos/search?query="
        f"{urllib.parse.quote_plus(tu_khoa)}&per_page={per_page}&page={trang}",
        headers={"Authorization": key}))
    ra = []
    for v in d.get("videos", []):
        # preview nhỏ nhất >=540p cho hover-play; link gốc để re-locate đợt 5
        files = sorted((f for f in v.get("video_files", []) if f.get("height")),
                       key=lambda f: f["height"])
        prev = next((f for f in files if f["height"] >= 360), files[0] if files else None)
        ten = (v.get("url") or "").rstrip("/").rsplit("/", 1)[-1].replace("-", " ")
        ten = re.sub(r"\s+\d+$", "", ten).strip() or f"pexels {v['id']}"
        ra.append({"id": sdb.lam_id("pexels", v["id"]), "nguon": "pexels",
                   "tieu_de": ten, "url_trang": v.get("url", ""),
                   "url_anh": v.get("image", ""),
                   "url_video": (prev or {}).get("link", ""),
                   "dai_s": float(v.get("duration") or 0), "tu_khoa_hut": tu_khoa,
                   **tag_tu_tieu_de(ten)})
    return ra


# ------------------------------------------------------------ PIXABAY (API)
def hut_pixabay(tu_khoa: str, trang: int = 1, per_page: int = 40) -> list[dict]:
    key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("thiếu PIXABAY_API_KEY")
    d = json.loads(_get(
        f"https://pixabay.com/api/videos/?key={key}&q="
        f"{urllib.parse.quote_plus(tu_khoa)}&per_page={per_page}&page={trang}"))
    ra = []
    for v in d.get("hits", []):
        vid = v.get("videos", {})
        prev = vid.get("small") or vid.get("tiny") or {}
        ten = (v.get("tags") or f"pixabay {v['id']}").replace(",", " ")
        ra.append({"id": sdb.lam_id("pixabay", v["id"]), "nguon": "pixabay",
                   "tieu_de": ten, "url_trang": v.get("pageURL", ""),
                   "url_anh": prev.get("thumbnail", ""),
                   "url_video": prev.get("url", ""),
                   "dai_s": float(v.get("duration") or 0), "tu_khoa_hut": tu_khoa,
                   **tag_tu_tieu_de(ten)})
    return ra


_BO_HUT = {"envato": hut_envato, "pexels": hut_pexels, "pixabay": hut_pixabay}


def phien_hut(conn, tu_khoas: list[str], nguons: list[str],
              so_trang: int = 1, log=None, ma_tap: str = "") -> dict:
    """Chạy 1 PHIÊN hút tuần tự rón rén. Trả {"moi": n, "trung": n, "loi": [..]}.

    `ma_tap` (hút TRONG LÚC dựng một tập): clip MỚI mang dấu hàng tạm của tập
    đó, đóng job là dọn. Bỏ trống = hút nghiên cứu từ trang Sổ Tra, vào kho
    thường trực như cũ.
    """
    def ghi(m):
        if log:
            log(m)

    kq = {"moi": 0, "trung": 0, "loi": []}
    for tk in tu_khoas:
        for ng in nguons:
            ham = _BO_HUT.get(ng)
            if ham is None:
                continue
            for tr in range(1, so_trang + 1):
                try:
                    ds = ham(tk, tr)
                except Exception as exc:  # noqa: BLE001 — fail-open từng lượt
                    kq["loi"].append(f"{ng} «{tk}» tr{tr}: {str(exc)[:90]}")
                    ghi(f"sotra: ! {ng} «{tk}»: {str(exc)[:80]}")
                    break
                moi = sum(sdb.them_clip(conn, {**r, "tam_tap": ma_tap}) for r in ds)
                sdb.ghi_phien_hut(conn, tk, ng, moi, len(ds) - moi, ma_tap=ma_tap)
                conn.commit()
                kq["moi"] += moi
                kq["trung"] += len(ds) - moi
                ghi(f"sotra: {ng} «{tk}» trang {tr}: {len(ds)} kq ({moi} mới)")
                time.sleep(random.uniform(*GIAN_NHIP))
    return kq


# ------------------------------------------------------------ REF của tập
def doc_srt(srt: Path) -> list[tuple[float, float, str]]:
    """[(t0, t1, lời)] từ file .srt."""
    txt = srt.read_text(encoding="utf-8", errors="replace")
    ra = []
    for m in re.finditer(r"(\d\d):(\d\d):(\d\d),(\d+)\s*-->\s*"
                         r"(\d\d):(\d\d):(\d\d),(\d+)\s*\n(.+?)(?:\n\n|\Z)",
                         txt, re.S):
        g = m.groups()
        t0 = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        t1 = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
        ra.append((t0, t1, re.sub(r"\s+", " ", g[8]).strip()))
    return ra


def loi_chong(cau: list[tuple[float, float, str]], t0: float, t1: float,
              gioi_han: int = 200) -> str:
    """Lời thoại CHỒNG THỜI GIAN với cảnh — làm ngữ cảnh, KHÔNG làm từ khóa."""
    return " ".join(c[2] for c in cau if c[1] > t0 and c[0] < t1)[:gioi_han]


def _da_nap(conn, vid: Path, du_s: float = 20.0) -> bool:
    """Video ref này đã cắt + nạp XONG vào Library chưa.

    Đo 07/09: `phan_tich` của MỖI chương gọi `nap_ref_cua_tap`, mà hàm đó trước
    đây cắt cảnh + đọc hình lại TOÀN BỘ ref của tập, mỗi lần. LI103 có 744 cảnh
    -> mỗi chương đốt ~15 phút GLM để ghi đè đúng thứ đã có (`them_clip` trả 0
    "mới"). 17 chương = 17 lần. Người dùng bắt đúng: chừng đó thời gian dựng
    xong cả một chương rồi.

    "Xong" = cảnh cuối chạm gần hết thời lượng video. Cắt dở giữa chừng (job
    trước bị ngắt) -> False để chạy lại; id cảnh tính từ (tap, stem, t0-t1) nên
    chạy lại là upsert, không nhân bản.
    """
    from autoedit.project import ffprobe_duration

    r = conn.execute("SELECT COUNT(*) n, MAX(t1) het FROM clip WHERE path_local=?",
                     (str(vid),)).fetchone()
    if not r or not r[0]:
        return False
    dai = ffprobe_duration(vid) or 0.0
    return bool(dai) and float(r[1] or 0.0) >= dai - du_s


# Thư mục KẾT QUẢ do chính tool sinh ra — video trong đó là footage đã tải/đã
# giao, không bao giờ là phim mẫu. Tên khớp compose.thu_muc_giao() + draft CapCut.
THU_MUC_KHONG_PHAI_REF = {"compose timeline", "materials", "draft", "feedback"}


def loc_file_ref(thu_muc_tap: Path) -> tuple[list[Path], int]:
    """(*.mp4 là REF, số file .mp4 bị loại). Quy ước: tên bắt đầu bằng «ref»."""
    ds, loai = [], 0
    for vid in sorted(Path(thu_muc_tap).rglob("*.mp4")):
        trong_thu_muc_ket_qua = any(
            phan.lower() in THU_MUC_KHONG_PHAI_REF
            for phan in vid.relative_to(thu_muc_tap).parts[:-1])
        if vid.stem.lower().startswith("ref") and not trong_thu_muc_ket_qua:
            ds.append(vid)
        else:
            loai += 1
    return ds, loai


def nap_ref_tap(conn, thu_muc_tap: Path, tap: str = "", quoc_gia: str = "",
                doc_hinh: bool = True, log=None) -> int:
    """Quét *.mp4 trong thư mục tập -> mỗi CẢNH QUAY là một khúc ref.

    Đổi 06/09 (user chốt): trước cắt theo CÂU PHỤ ĐỀ, nay cắt theo CẢNH QUAY.
    Phụ đề chồng thời gian chỉ làm `loi_quanh` (ngữ cảnh) — từ khóa do đọc HÌNH
    sinh ra. Lý do đo được: 11% cảnh không có phụ đề nào chồng (mà đó là b-roll
    đẹp nhất), 19% có >=3 câu trộn ý, và phụ đề ref là tiếng Bulgaria nên dựa
    vào nó thì vẫn phải gọi LLM.

    `quoc_gia` gắn CỨNG vào geo mọi cảnh của tập — GLM đọc geo chỉ ra 3/12 cảnh
    (giới hạn thật, nhắc trong prompt không sửa được), mà cả file ref quay ở một
    nước nên gắn cứng vừa rẻ vừa chắc đúng.

    CHỈ NHẬN FILE TÊN `ref*` (user chốt 07/09 sáng: *"`ref *.mp4` ở gốc = phim
    mẫu của tập"*). Trước đó hàm này `rglob("*.mp4")` nên nuốt luôn footage tool
    ĐÃ TẢI VỀ VÀ GIAO cho editor: LI103 có 78 clip trong `Compose Timeline/.../
    materials/`, LI104 có 224 — chúng bị cắt cảnh, đọc hình bằng GLM rồi ghi vào
    Library dưới nhãn `nguon='ref'`. Hai cái sai: tốn GLM đọc lại hình của clip
    vốn đã nằm trong kho, và SỔ NGUỒN GỐC ghi sai — clip mua từ Envato thành
    "phim mẫu của tập" (đo 07/09: kho thật đang có 42 cảnh như vậy).

    File KHÔNG copy — chỉ ghi path_local + t0/t1 (luật cứng của Library).
    """
    from autoedit.sotra.canh import cat_canh
    from autoedit.sotra.doc_canh import doc_nhieu, trich_anh

    thu_muc_tap = Path(thu_muc_tap)
    tap = tap or thu_muc_tap.name
    moi = 0
    bo_qua = 0
    ds_vid, khong_hop_le = loc_file_ref(thu_muc_tap)
    if khong_hop_le and log:
        log(f"sotra: bỏ qua {khong_hop_le} file .mp4 không phải ref "
            f"(tên không bắt đầu bằng «ref», hoặc nằm trong thư mục kết quả)")
    for vid in ds_vid:
        if _da_nap(conn, vid):
            bo_qua += 1
            continue
        cs = cat_canh(vid)
        if not cs:
            continue
        srt = vid.with_suffix(".srt")
        cau = doc_srt(srt) if srt.is_file() else []
        # Phụ đề DÀI HƠN video = .srt của phim khác bị copy nhầm tên. Gặp thật
        # 06/09: `ref 2.srt` trùng MD5 với `ref 1.srt` nhưng video 23' vs 52' —
        # nếu cứ dùng thì 228 cảnh bị gán lời của phim khác. Thà không có lời.
        if cau and cau[-1][1] > cs[-1].t1 + 60:
            if log:
                log(f"sotra: ⚠ «{srt.name}» dài tới {cau[-1][1]:.0f}s nhưng "
                    f"«{vid.name}» chỉ {cs[-1].t1:.0f}s — phụ đề của phim khác, BỎ")
            cau = []
        if log:
            log(f"sotra: «{vid.name}» -> {len(cs)} cảnh"
                + (f", {len(cau)} câu phụ đề" if cau else ", không có phụ đề"))

        # ---- việc 4: ảnh đại diện mỗi cảnh (15KB/ảnh, KHÔNG cắt video) ----
        thu = sdb.goc_so_tra() / "frames"
        ho_so = []
        for c in cs:
            cid = sdb.lam_id("ref", f"{tap}-{vid.stem}", f"{c.t0:.2f}-{c.t1:.2f}")
            anh = trich_anh(vid, c.t0, c.t1,
                            thu / sdb.ten_frame(cid, vid.stem, "dau"))
            ho_so.append((c, cid, anh, loi_chong(cau, c.t0, c.t1)))

        # ---- việc 2: đọc hình theo lô ----
        docs = {}
        if doc_hinh:
            # Cảnh ĐÃ đọc hình lần trước thì thôi — video cắt dở nửa chừng vẫn
            # còn phần cũ trong DB, đọc lại là trả tiền GLM cho câu trả lời cũ.
            da_co = {r[0] for r in conn.execute(
                "SELECT id FROM clip WHERE path_local=? AND COALESCE(subject,'')!=''",
                (str(vid),))}
            can = [h for h in ho_so if h[2] and h[1] not in da_co]
            if can:
                kq = doc_nhieu([(h[2], h[3]) for h in can], log=log)
                for h, d in zip(can, kq):
                    docs[h[1]] = d
            if log and da_co:
                log(f"sotra: «{vid.name}» {len(da_co)} cảnh đã đọc hình — "
                    f"chỉ đọc {len(can)} cảnh mới")

        for c, cid, anh, loi in ho_so:
            d = docs.get(cid)
            # geo: tên nước gắn cứng cấp tập + chi tiết GLM đọc được (nếu có)
            geo = ">".join(x for x in (quoc_gia.lower().strip(),
                                       (d.geo.lower() if d else "")) if x)
            r = {"id": cid, "nguon": "ref",
                 "tieu_de": (d.subject if d and d.subject else loi[:120]) or vid.stem,
                 "path_local": str(vid), "t0": float(c.t0), "t1": float(c.t1),
                 "dai_s": float(c.dai), "tap": tap,
                 "loi_quanh": loi, "may_dong": int(c.may_dong),
                 "frame_dau": str(anh) if anh else "",
                 "tag_nguon": "vision" if d and d.subject else "tieu_de"}
            if d and d.subject:
                r.update({"subject": d.subject, "vat_the": d.vat_the,
                          "action": d.action, "setting": d.setting, "geo": geo,
                          "people": d.people, "shot": d.shot, "mood": d.mood,
                          "khop": d.khop})
            else:                       # đọc hình hỏng/tắt -> tạm dùng lời
                r.update({**tag_tu_tieu_de(loi), "geo": geo})
            moi += sdb.them_clip(conn, r)
        conn.commit()
    if log:
        log(f"sotra: nạp ref «{tap}»: +{moi} cảnh"
            + (f", bỏ qua {bo_qua} video đã có" if bo_qua else ""))
    return moi
