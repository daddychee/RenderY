r"""⚡ Gen AI cho một KHỐI Offline — nguồn thứ 5 của khay, nằm trong LIBRARY.

Thiết kế ghép (user duyệt 07/09): Generation không còn là màn riêng — là thao
tác per-khối trong pha 2. Chỉ sinh ẢNH lúc duyệt (Seedream, rẻ); bước i2v đắt
(Seedance 5s) chạy ở THAY MÁU đợt 5, chỉ cho ảnh ĐÃ CHỐT — đúng khuôn
"preview trước, bản sạch sau". Ảnh ghi vào Library nguồn `aigen` (id
`aigen:{project}:{khối}:{hash8}`) — tập sau tra lại dùng miễn phí.

Prompt ghép từ chính khối: L1 + neo + mood + đuôi phong cách cố định — không
để model tự do phá mood (nguyên tắc trụ số 1).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from autoedit.offline import runner as orun

DUOI_PHONG_CACH = ("documentary still, natural light, muted colors, "
                   "photorealistic, no text, no watermark")


def prompt_cho_khoi(k: dict, chu_the_tap: list[str]) -> str:
    """Khối 4 lớp -> prompt Seedream. L1 là ruột; neo + mood + chủ thể là khung."""
    ruot = ", ".join((k.get("L1") or k.get("L2") or k.get("L3") or ["scene"])[:2])
    neo = "Ecuador, South America" if k.get("neo") else ""
    mood = k.get("mood") or ""
    bo = ", ".join(x for x in [ruot, neo, mood, ", ".join(chu_the_tap[:2])] if x)
    return f"{bo}, {DUOI_PHONG_CACH}"


def gen_cho_khoi(project_dir: Path, khoi_idx: int, so_anh: int = 2,
                 client=None, conn=None, log=None) -> list[dict]:
    """Sinh ảnh cho 1 khối -> ghi Library + chèn đầu uv của khối trong
    offline.json. Trả danh sách clip mới. `client`/`conn` tiêm được."""
    def ghi(m):
        if log:
            log(m)

    project_dir = Path(project_dir)
    hd = orun.doc(project_dir)
    if hd is None:
        raise RuntimeError("chưa có offline.json")
    if not 0 <= khoi_idx < len(hd["khoi"]):
        raise RuntimeError(f"khối {khoi_idx} không tồn tại")
    k = hd["khoi"][khoi_idx]
    prompt = prompt_cho_khoi(k, hd.get("chu_the_tap") or [])
    ghi(f"offline-gen: khối {khoi_idx + 1} — {prompt[:90]}")

    if client is None:
        from autoedit.aigen.client import ArkClient

        client = ArkClient()
    kho = project_dir / "aigen_offline"
    kho.mkdir(exist_ok=True)

    from autoedit.sotra import db as sdb
    from autoedit.sotra.tag7 import tag_tu_tieu_de

    c = conn or sdb.mo()
    moi: list[dict] = []
    try:
        for i in range(max(1, min(4, so_anh))):
            ma = hashlib.sha1(f"{prompt}|{i}".encode()).hexdigest()[:8]
            dich = kho / f"khoi{khoi_idx:02d}_{ma}.png"
            try:
                client.gen_anh(prompt, dich)
            except Exception as exc:  # noqa: BLE001 — 1 ảnh hỏng không giết lượt
                ghi(f"offline-gen: ảnh {i + 1} LỖI ({str(exc)[:80]})")
                continue
            clip_id = sdb.lam_id("aigen", f"{project_dir.name}:{khoi_idx}", ma)
            tieu_de = f"[AI] {prompt.split(',')[0]} — {k.get('mood') or 'gen'}"
            sdb.them_clip(c, {"id": clip_id, "nguon": "aigen", "tieu_de": tieu_de,
                              "path_local": str(dich), "tap": project_dir.name,
                              **tag_tu_tieu_de(prompt)})
            sdb.ghi_su_kien(c, clip_id, "de_xuat", tap=project_dir.name,
                            vi_tri=k["v0"], chi_tiet=f"gen cho khối {khoi_idx + 1}")
            moi.append({"id": clip_id, "nguon": "aigen", "tieu_de": tieu_de,
                        "lop": "L1", "diem": 9.0, "url_anh": "", "url_video": "",
                        "geo": "ecuador" if k.get("neo") else "", "dai_s": 0})
        c.commit()
    finally:
        if conn is None:
            c.close()

    if moi:  # chèn ĐẦU khay khối — người duyệt thấy ngay, chọn hay không là quyền họ
        k["uv"] = moi + (k.get("uv") or [])
        orun.luu(project_dir, hd)
        ghi(f"offline-gen: +{len(moi)} ảnh vào khay khối {khoi_idx + 1}")
    return moi
