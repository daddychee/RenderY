r"""Phiên đăng nhập Envato / Epidemic — id+mật khẩu trong két (user chốt 06/09).

Thăm dò 06/09: cả hai nhà đều có reCAPTCHA ở cửa đăng nhập -> request thuần
KHÔNG vào được. Cách làm: trình duyệt tự động (Playwright) chạy NGAY TRÊN
SERVER — máy tự điền email|mật_khẩu từ két; captcha đòi người thì cửa sổ
trình duyệt hiện trên desktop server (cả team RDP vào đây) để bấm một lần.
Phiên lưu trong profile bền <data_root>/phien/<nha>/ — lần sau thường không
bị đòi lại (thiết bị quen), và mật khẩu trong két cho máy TỰ đăng nhập lại
khi phiên chết.

Luật dùng: chỉ lúc THAY MÁU/khóa sổ; tải 1 luồng giãn 2-5s (luật Envato).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from autoedit.packager.machine import resolve_data_root

NHA = {
    "envato": {
        "viec": "tai_ban_sach",
        "url_login": "https://account.envato.com/sign_in",
        "url_kiem": "https://elements.envato.com/",
        # đăng nhập thành công khi cookie phiên của account.envato xuất hiện
        "cookie_phien": ("_elements_session", "auth_token", "_session_id"),
        "o_email": 'input[name="username"], input[type="email"]',
        "o_mk": 'input[name="password"], input[type="password"]',
    },
    "epidemic": {
        "viec": "tai_nhac_sach",
        "url_login": "https://www.epidemicsound.com/login/",
        "url_kiem": "https://www.epidemicsound.com/music/featured/",
        "cookie_phien": ("sessionid", "es_session", "KEYCLOAK_IDENTITY"),
        "o_email": 'input[name="username"], input[type="email"], input[name="email"]',
        "o_mk": 'input[name="password"], input[type="password"]',
    },
}


def thu_muc_phien(nha: str) -> Path:
    d = resolve_data_root() / "phien" / nha
    d.mkdir(parents=True, exist_ok=True)
    return d


def doc_tai_khoan(nha: str) -> tuple[str, str]:
    """(email, mật khẩu) từ két General. Chuẩn 06/09: 2 TRƯỜNG RIÊNG — email ở
    `tai_khoan` (metadata), mật khẩu ở `key` (ngăn bí mật). Khoá kiểu cũ
    `email|mật_khẩu` nhét một ô vẫn đọc được (tương thích ngược)."""
    from autoedit.web.ket_v3 import doc_ket

    viec = NHA[nha]["viec"]
    for k in ((doc_ket() or {}).get(viec) or {}).get("khoa") or []:
        email = (k.get("tai_khoan") or "").strip()
        mk = (k.get("key") or "").strip()
        if email and mk:
            return email, mk
        if "|" in mk:                       # khuôn cũ một ô
            e, m = mk.split("|", 1)
            return e.strip(), m.strip()
    return "", ""


def _cookies(nha: str) -> list[dict]:
    f = thu_muc_phien(nha) / "state.json"
    if not f.is_file():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("cookies") or []
    except Exception:  # noqa: BLE001
        return []


def co_phien(nha: str) -> bool:
    """Có cookie phiên còn hạn trong profile không (kiểm nhanh, không mạng)."""
    ten = NHA[nha]["cookie_phien"]
    nay = time.time()
    return any(c.get("name") in ten and (c.get("expires", -1) in (-1, None)
                                         or c["expires"] > nay)
               for c in _cookies(nha))


def dang_nhap(nha: str, cho_captcha_s: int = 300, log=None) -> dict:
    """Tự điền email|mật_khẩu từ két; captcha thì hiện cửa sổ trên desktop server.

    Trả {"ok": bool, "ghi_chu": ...}. Chạy trong luồng nền của server.
    """
    def ghi(m):
        if log:
            log(f"phien[{nha}]: {m}")

    email, mk = doc_tai_khoan(nha)
    if not email:
        return {"ok": False, "ghi_chu": "Chưa có tài khoản trong két "
                                        "(General › API Keys › rendery, dạng email|mật_khẩu)"}
    cfg = NHA[nha]
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # headless=False: captcha cần người — cửa sổ hiện trên desktop server
        ctx = p.chromium.launch_persistent_context(
            str(thu_muc_phien(nha) / "profile"), headless=False,
            viewport={"width": 1100, "height": 800})
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(cfg["url_login"], timeout=60_000)
            time.sleep(2)
            # đã đăng nhập sẵn từ lần trước? (bị redirect khỏi trang login)
            if "sign_in" not in page.url and "login" not in page.url:
                ghi("phiên cũ còn sống — khỏi đăng nhập")
            else:
                try:
                    page.fill(cfg["o_email"], email, timeout=15_000)
                    page.fill(cfg["o_mk"], mk, timeout=15_000)
                    page.keyboard.press("Enter")
                    ghi("đã điền tài khoản, chờ đăng nhập / captcha...")
                except Exception:  # noqa: BLE001 — form lạ: để người tự thao tác
                    ghi("không tìm thấy ô đăng nhập — chờ người thao tác trên cửa sổ")
                # chờ tới khi rời trang login (captcha do NGƯỜI bấm trên cửa sổ)
                het = time.time() + cho_captcha_s
                while time.time() < het:
                    time.sleep(2)
                    if "sign_in" not in page.url and "login" not in page.url \
                            and "auth" not in page.url:
                        break
                else:
                    return {"ok": False,
                            "ghi_chu": f"Quá {cho_captcha_s}s chưa qua cửa đăng nhập "
                                       "(captcha chưa được bấm trên desktop server?)"}
            ctx.storage_state(path=str(thu_muc_phien(nha) / "state.json"))
            ghi("đã lưu phiên")
            return {"ok": True, "ghi_chu": "Phiên sống — đã lưu vào profile server"}
        finally:
            ctx.close()


def giu_am(log=None) -> dict:
    """Ping nhẹ mỗi nhà đang có phiên — cookie được dùng thì sống lâu hơn."""
    import urllib.request

    ra = {}
    for nha, cfg in NHA.items():
        if not co_phien(nha):
            ra[nha] = "chua_co"
            continue
        chuoi = "; ".join(f"{c['name']}={c['value']}" for c in _cookies(nha))
        try:
            req = urllib.request.Request(cfg["url_kiem"], headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Cookie": chuoi})
            urllib.request.urlopen(req, timeout=30).read(2048)
            ra[nha] = "song"
        except Exception:  # noqa: BLE001
            ra[nha] = "loi"
        if log:
            log(f"phien[{nha}]: giữ ấm -> {ra[nha]}")
    return ra


def trang_thai() -> dict:
    """Cho UI: mỗi nhà {co_tai_khoan, co_phien}."""
    ra = {}
    for nha in NHA:
        email, _ = doc_tai_khoan(nha)
        ra[nha] = {"co_tai_khoan": bool(email), "co_phien": co_phien(nha)}
    return ra
