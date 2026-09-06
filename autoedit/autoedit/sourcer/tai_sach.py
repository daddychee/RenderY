r"""Tải BẢN SẠCH Envato bằng phiên đăng nhập server — cho bản ONLINE.

Đường đi (đo thật 06/09, từng bước có bằng chứng):
  1. url_trang trong kho là URL TỰ CHẾ (item-<uuid>) — Envato không nhận. URL
     thật tìm qua trang search công khai: cắt trang thành card, ảnh cover mang
     uuid -> item-href ĐẦU TIÊN SAU ảnh là link thật (đã verify: trang mở ra
     chứa đúng uuid). Tìm được thì VÁ url_trang vào kho — tự lành dần.
  2. Trang item với phiên đăng nhập: nút "Download 4K", license TỰ ĐỘNG
     ("Automatically licensed") — expect_download hứng file.
     Đo thật: 386MB/21s clip 4K, 64 giây tải.
  3. File về so_tra/ban_sach/<uuid>.mp4 — MỘT lần cho mãi mãi (mọi tập sau
     dùng lại); clip trong kho vá path_local + trang_thai='da_tai'.

Luật rón rén (Envato chặn IP tải ồ ạt): MỘT phiên trình duyệt cho cả lượt,
tuần tự từng clip, giãn 2-5s. Hỏng clip nào bỏ clip đó (fail-open) — bản
Online vẫn ra với preview cho clip thiếu.
"""
from __future__ import annotations

import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from autoedit.sotra import db as sdb

GIAN_S = (2.0, 5.0)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
_MAU_ITEM = re.compile(r'href="(/[a-z0-9][a-z0-9-]{10,}-[A-Z0-9]{7,8})"')


def _uuid_goc(clip_id: str) -> str:
    """envato:<uuid>[#trim] -> uuid (khúc trim dùng file sạch của clip MẸ)."""
    return clip_id.split(":", 1)[1].split("#", 1)[0]


def thu_muc_sach() -> Path:
    d = sdb.goc_so_tra() / "ban_sach"
    d.mkdir(parents=True, exist_ok=True)
    return d


def tim_url_item(conn, uuid: str, tu_khoa: str, log=None) -> str:
    """URL item THẬT từ trang search (thuật toán img -> href-sau, có verify)."""
    for trang in (1, 2):
        q = urllib.parse.quote_plus(tu_khoa)
        url = (f"https://elements.envato.com/stock-video/{q}"
               + (f"?page={trang}" if trang > 1 else ""))
        try:
            h = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": UA}),
                timeout=60).read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        vt = [m.start() for m in re.finditer(re.escape(uuid), h)
              if m.start() > 100_000]                 # bỏ vùng preload ở <head>
        if not vt:
            continue
        sau = [m.group(1) for m in _MAU_ITEM.finditer(h) if m.start() > vt[0]]
        for duong in sau[:2]:
            item = "https://elements.envato.com" + duong
            try:
                h2 = urllib.request.urlopen(
                    urllib.request.Request(item, headers={"User-Agent": UA}),
                    timeout=60).read().decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                continue
            if uuid in h2:                            # verify: trang chứa đúng cover
                conn.execute("UPDATE clip SET url_trang=? WHERE id LIKE ?",
                             (item, f"envato:{uuid}%"))
                conn.commit()
                if log:
                    log(f"online: tìm được trang item {duong[-30:]}")
                return item
    return ""


def tai_nhieu(conn, clip_ids: list[str], log=None) -> dict[str, Path]:
    """Tải bản sạch cho các clip envato — MỘT phiên trình duyệt, tuần tự, giãn.

    Trả {uuid: path}. Clip đã có bản sạch thì trả ngay không tải lại.
    """
    def ghi(m):
        if log:
            log(m)

    can: dict[str, str] = {}                          # uuid -> clip_id gốc
    ra: dict[str, Path] = {}
    for cid in clip_ids:
        u = _uuid_goc(cid)
        f = thu_muc_sach() / f"{u}.mp4"
        if f.is_file() and f.stat().st_size > 100_000:
            ra[u] = f                                  # đã tải từ trước — mãi mãi
        else:
            can.setdefault(u, cid)
    if not can:
        return ra

    from autoedit.sourcer.phien import co_phien, thu_muc_phien

    if not co_phien("envato"):
        ghi("online: phiên Envato CHƯA sống — bỏ qua tải bản sạch (dùng preview)")
        return ra

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(thu_muc_phien("envato") / "profile"), headless=True,
            accept_downloads=True)
        try:
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            for so, (u, cid) in enumerate(can.items(), 1):
                try:
                    c = conn.execute("SELECT url_trang, tu_khoa_hut FROM clip "
                                     "WHERE id LIKE ? LIMIT 1",
                                     (f"envato:{u}%",)).fetchone()
                    url = (c["url_trang"] or "") if c else ""
                    duong = url.replace("https://elements.envato.com", "")
                    if not _MAU_ITEM.search(f'href="{duong}"'):
                        url = ""                      # url tự chế đời cũ -> tìm lại
                    if not url:
                        url = tim_url_item(conn, u, (c["tu_khoa_hut"] or "") if c else "",
                                           log=log)
                    if not url:
                        ghi(f"online: {u[:8]} KHÔNG tìm được trang item — giữ preview")
                        continue
                    pg.goto(url, timeout=90_000)
                    pg.wait_for_timeout(2500)
                    try:
                        pg.get_by_role("button", name="Accept all").click(timeout=3000)
                    except Exception:  # noqa: BLE001
                        pass
                    if pg.locator('a:has-text("Sign in")').count():
                        ghi("online: phiên Envato HẾT HẠN giữa chừng — dừng lượt tải")
                        break
                    with pg.expect_download(timeout=300_000) as dl:
                        pg.locator('button:has-text("Download")').first.click()
                    f = thu_muc_sach() / f"{u}.mp4"
                    dl.value.save_as(str(f))
                    if f.stat().st_size < 100_000:
                        f.unlink(missing_ok=True)
                        raise RuntimeError("file tải về quá nhỏ")
                    ra[u] = f
                    # KHÔNG đổi trang_thai: tra() lọc ='song', đổi là clip biến
                    # mất khỏi khay gợi ý — path_local có mặt = đã tải bản sạch
                    conn.execute("UPDATE clip SET path_local=? WHERE id LIKE ?",
                                 (str(f), f"envato:{u}%"))
                    conn.commit()
                    ghi(f"online: {so}/{len(can)} ✔ {f.stat().st_size / 1e6:.0f}MB "
                        f"«{(dl.value.suggested_filename or '')[:36]}»")
                except Exception as exc:  # noqa: BLE001 — clip hỏng không giết lượt
                    ghi(f"online: {u[:8]} LỖI ({str(exc)[:70]}) — giữ preview")
                time.sleep(random.uniform(*GIAN_S))    # luật rón rén Envato
        finally:
            ctx.close()
    return ra
