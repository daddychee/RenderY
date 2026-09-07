r"""KHAI QUẬT kho cũ — quét projects/ đã dựng, ghi vào Sổ Tra MỘT LẦN.

Kỳ vọng đã hiệu chỉnh qua phản biện (06/09): đây KHÔNG phải kho vàng —
98% ứng viên thua phễu thua rõ rệt, và "thắng phễu" chưa qua vòng phản biện
nào. Giá trị thật: (a) catalog 3.9k clip đang nằm sẵn trên đĩa trước khi bị
dọn; (b) sự kiện `len_final` từ shots — clip nào từng LÊN TIMELINE tập nào
(nhãn "đã dùng" chống lặp giữa tập); (c) nền cho vòng phản biện cắm điểm sau.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from autoedit.sotra import db as sdb
from autoedit.sotra.tag7 import tag_tu_tieu_de

# Tên nguồn trong project.json cũ -> tên KHO (user chốt 07/09: "download từ
# trang nào thì kho tên là trang đó · video ref đặt trong kho ref").
# `refvid` la tien to THAT trong asset_key (do 07/09: pexels 21.340 · pixabay
# 5.835 · refvid 4.857); `refvideo` la ten trong shots[].source. Thieu mot trong
# hai la bo sot — ban dau toi chi khai "refvideo" nen 446 clip ref bi giu nham
# nhan kho, chay thu che do CHI DOC moi lo ra.
DOI_TEN_NGUON = {"refvid": "ref", "refvideo": "ref", "ref": "ref",
                 "pexels": "pexels", "pixabay": "pixabay",
                 "envato": "envato", "local": "rec", "aigen": "aigen"}
# entity (ảnh tra Google) + chart (biểu đồ tự sinh): user chốt 07/09 BỎ HẲN,
# không phải tải từ trang nào nên không có kho tương ứng.
BO_HAN = {"entity", "chart"}


def _ban_do_nguon(p: dict) -> dict:
    r"""project.json -> {đuôi 6 hex trong tên file: tên kho thật}.

    Tên file asset là `b012_slug_<sha1(asset_key)[:6]>.mp4`, mà `asset_key`
    ("pexels:30281933") mang sẵn tiền tố nguồn và nằm trong `rank_log` — có cho
    CẢ ứng viên KHÔNG được chọn. Nhờ vậy tra được 98% (đo 07/09 trên 4.089 dòng:
    2.714 pexels · 870 ref · 429 pixabay · 64 chưa tra được).
    """
    khoa = {c.get("asset_key") for r in (p.get("rank_log") or [])
            for c in (r.get("ranked") or []) if c.get("asset_key")}
    khoa |= {s.get("asset_key") for s in (p.get("shots") or []) if s.get("asset_key")}
    ra = {}
    for k in khoa:
        if not k or ":" not in k:
            continue
        ten = DOI_TEN_NGUON.get(k.split(":")[0].lower())
        if ten:
            ra[hashlib.sha1(k.encode()).hexdigest()[:6]] = ten
    return ra


def _nguon_that(ten_file: str, ban_do: dict, theo_shot: dict) -> str:
    """Tên kho thật của 1 file asset; '' nếu KHÔNG tra được (không đoán bừa)."""
    m = re.search(r"_([0-9a-f]{6})\.\w+$", ten_file)
    if m and m.group(1) in ban_do:
        return ban_do[m.group(1)]
    src = (theo_shot.get(ten_file) or "").lower()
    if src in BO_HAN:
        return "BO"
    return DOI_TEN_NGUON.get(src, "")


def _ten_tap(p: dict) -> str:
    """Suy mã tập (LI100...) từ đường dẫn script gốc — không có thì id project."""
    goc = (p.get("inputs") or {}).get("original_script_path") or ""
    m = re.search(r"(?:^|[\\/])([A-Z]{2,4}\d{2,4})(?:_[\w-]+)?(?:[\\/])", goc)
    return m.group(1) if m else (p.get("project_id") or "")


def khai_quat(conn, projects_dir: Path, log=None) -> dict:
    """Quét mọi project.json: assets trên đĩa -> clip nguồn 'kho'; shots -> su_kien."""
    def ghi(m):
        if log:
            log(m)

    kq = {"clip_moi": 0, "su_kien": 0, "project": 0}
    for f in sorted(Path(projects_dir).glob("*/project.json")):
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        pdir = f.parent
        tap = _ten_tap(p)
        assets = {a.name: a for a in (pdir / "assets").glob("*.*")} if (pdir / "assets").is_dir() else {}
        if not assets:
            continue
        kq["project"] += 1
        # 1) mọi file asset -> 1 dòng clip mang ĐÚNG TÊN KHO nguồn của nó
        # (user chốt 07/09). Trước đây gán cứng 'kho' cho tất -> xoá sạch nguồn
        # gốc: 870 clip THẬT RA LÀ REF nằm nhầm trong panel stock.
        ban_do = _ban_do_nguon(p)
        theo_shot = {Path(s.get("asset_path") or "").name: (s.get("source") or "")
                     for s in (p.get("shots") or []) if s.get("asset_path")}
        for ten, duong in assets.items():
            ng = _nguon_that(ten, ban_do, theo_shot)
            if ng == "BO":
                continue                      # entity/chart: user chốt bỏ hẳn
            # b012_vietnam-beach-sunset_ab12cd.mp4 -> "vietnam beach sunset"
            m = re.match(r"b\d{3}_(.+?)(?:_[0-9a-f]{6})?\.\w+$", ten)
            mo_ta = (m.group(1) if m else duong.stem).replace("-", " ")
            # id GIỮ tiền tố kho cũ: nó là khoá tham chiếu của sự kiện và tên
            # file ảnh frame. `nguon` mới là sự thật về nguồn.
            r = {"id": sdb.lam_id("kho", f"{pdir.name}:{ten}"), "nguon": ng or "kho",
                 "tieu_de": mo_ta, "path_local": str(duong), "tap": tap,
                 **tag_tu_tieu_de(mo_ta)}
            kq["clip_moi"] += sdb.them_clip(conn, r)
        # 2) shots -> sự kiện LÊN FINAL (đã lên timeline thật của tập đó)
        for s in p.get("shots") or []:
            ap = s.get("asset_path") or ""
            ten = Path(ap).name if ap else ""
            if ten not in assets:
                continue
            cid = sdb.lam_id("kho", f"{pdir.name}:{ten}")
            sdb.ghi_su_kien(conn, cid, "len_final", tap=tap,
                            chi_tiet=f"beat {s.get('beat_id')} · {s.get('source', '')}")
            kq["su_kien"] += 1
        conn.commit()
        ghi(f"sotra: khai quật {pdir.name} ({tap}): {len(assets)} asset")
    return kq


def dan_lai_nhan(conn, projects_dir: Path, log=None) -> dict:
    """Dán lại nhãn cho các dòng đã lỡ mang 'kho' — theo NGUỒN THẬT.

    Chỉ đổi cột `nguon`; **id giữ nguyên** vì nó là khoá tham chiếu của bảng sự
    kiện và nằm trong tên file ảnh frame. Không tra được thì GIỮ 'kho', không
    đoán. entity/chart bị XOÁ (user chốt 07/09: bỏ hẳn).
    """
    def ghi(m):
        if log:
            log(m)

    kq: dict = {}
    for f in sorted(Path(projects_dir).glob("*/project.json")):
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        pj = f.parent.name
        ban_do = _ban_do_nguon(p)
        theo_shot = {Path(s.get("asset_path") or "").name: (s.get("source") or "")
                     for s in (p.get("shots") or []) if s.get("asset_path")}
        for (cid,) in conn.execute(
                "SELECT id FROM clip WHERE nguon='kho' AND id LIKE ?", (f"kho:{pj}:%",)):
            ten = cid.split(":", 2)[2]
            ng = _nguon_that(ten, ban_do, theo_shot)
            if ng == "BO":
                sdb.xoa_clip(conn, cid)
                kq["(xoá) entity/chart"] = kq.get("(xoá) entity/chart", 0) + 1
            elif ng:
                conn.execute("UPDATE clip SET nguon=? WHERE id=?", (ng, cid))
                kq[ng] = kq.get(ng, 0) + 1
    conn.commit()
    con = conn.execute(
        "SELECT COUNT(*) FROM clip WHERE nguon='kho'").fetchone()[0]
    kq["(giữ kho — chưa tra được)"] = con
    ghi("sotra: dán lại nhãn — " + " · ".join(f"{k} {v}" for k, v in kq.items()))
    return kq
