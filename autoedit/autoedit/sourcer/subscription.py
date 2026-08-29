"""Nguồn subscription (Envato Elements, Vecteezy Pro) — tải qua trình duyệt CÓ PHANH.

User đã trả tiền cho các nguồn này nên footage hoàn toàn hợp pháp. Nhưng chúng KHÔNG
có API tải, phải điều khiển trình duyệt — và đó là rủi ro thật: tải dồn dập dễ bị coi
là bot, hậu quả là **mất tài khoản đang trả tiền**. Đánh đổi không đối xứng: tiết kiệm
vài phút, đổi lấy nguy cơ mất subscription.

Nên module này đặt PHANH lên trước tốc độ (user chốt 2026-08-30 "tự động nhưng có phanh"):

- Trần số clip mỗi giờ (`RateLimiter`) — mặc định 20, đếm theo cửa sổ trượt.
- Nghỉ NGẪU NHIÊN giữa 2 lần tải (6-18s) — nhịp đều là dấu hiệu bot rõ nhất.
- Gặp captcha/challenge -> DỪNG NGAY cả phiên, không thử lại (thử tiếp = tự tố cáo).
- Dùng Chrome THẬT + profile đã đăng nhập sẵn, không phải Chromium đóng gói.

Artlist bị BỎ khỏi RenderY: Auto Editing của user đã kết luận "chỉ tải tay" và raise
lỗi ngay trong `download()` — port sang cũng vậy, không đáng.

Playwright dùng SYNC API vì padoma chạy đồng bộ hoàn toàn — khỏi bọc asyncio.run().
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── PHANH: mọi hằng số kiểm soát nhịp tải gom ở đây ──────────────────────────
MAX_PER_HOUR = 20          # trần clip tải mỗi giờ, mỗi nguồn
PAUSE_MIN, PAUSE_MAX = 6.0, 18.0   # nghỉ ngẫu nhiên giữa 2 lần tải (giây)
NAV_TIMEOUT_MS = 45_000
MIN_VIDEO_BYTES = 50_000   # nhỏ hơn = bị chặn / dính bản preview
_MAX_CONSECUTIVE_FAIL = 3  # fail liên tiếp -> nghi bị chặn mềm, dừng nguồn

PROFILES_DIRNAME = ".browser_profiles"

SITES = {
    "envato": {
        "search": "https://elements.envato.com/stock-video/{q}?orientation=horizontal",
        "login": "https://account.envato.com/sign_in",
        "env": "ENVATO_EMAIL",
    },
    "vecteezy": {
        "search": "https://www.vecteezy.com/free-videos/{q}",
        "login": "https://www.vecteezy.com",
        "env": "VECTEEZY_EMAIL",
    },
}


class BlockedError(RuntimeError):
    """Gặp captcha/challenge — DỪNG cả phiên nguồn này, không thử lại."""


class RateLimitError(RuntimeError):
    """Chạm trần clip/giờ — nghỉ rồi chạy lại, không phải lỗi."""


@dataclass
class RateLimiter:
    """Phanh tốc độ: trần N lần mỗi giờ + nghỉ ngẫu nhiên giữa các lần.

    Cửa sổ TRƯỢT (không phải reset theo giờ tròn) để không bị dồn cục đầu giờ.
    """

    max_per_hour: int = MAX_PER_HOUR
    pause_range: tuple[float, float] = (PAUSE_MIN, PAUSE_MAX)
    _stamps: list[float] = field(default_factory=list)

    def check(self, now: Optional[float] = None) -> None:
        """Raise RateLimitError nếu đã chạm trần trong 1 giờ qua."""
        now = now if now is not None else time.monotonic()
        self._stamps = [t for t in self._stamps if now - t < 3600]
        if len(self._stamps) >= self.max_per_hour:
            wait = 3600 - (now - self._stamps[0])
            raise RateLimitError(
                f"Chạm trần {self.max_per_hour} clip/giờ — nghỉ {wait / 60:.0f} phút rồi chạy lại"
            )

    def record(self, now: Optional[float] = None) -> None:
        self._stamps.append(now if now is not None else time.monotonic())

    def pause(self, sleep=time.sleep) -> float:
        """Nghỉ NGẪU NHIÊN — nhịp đều đặn là dấu hiệu bot dễ nhận nhất."""
        secs = random.uniform(*self.pause_range)
        sleep(secs)
        return secs

    @property
    def used(self) -> int:
        now = time.monotonic()
        return len([t for t in self._stamps if now - t < 3600])


def profiles_dir(root: Optional[Path] = None) -> Path:
    """Thư mục profile trình duyệt. Ưu tiên profile Auto Editing đã đăng nhập sẵn."""
    if root is not None:
        return Path(root) / PROFILES_DIRNAME
    env = os.getenv("BROWSER_PROFILES_DIR", "").strip()
    if env:
        return Path(env)
    return Path.cwd() / PROFILES_DIRNAME


def profile_exists(site: str, root: Optional[Path] = None) -> bool:
    d = profiles_dir(root) / site
    return d.is_dir() and any(d.iterdir())


def is_challenge(page) -> bool:
    """Cloudflare/captcha đang chặn? (giống Auto Editing: soi title + iframe turnstile)"""
    try:
        title = (page.title() or "").lower()
        if any(x in title for x in ("just a moment", "attention required",
                                    "verify", "checking")):
            return True
        return page.query_selector('iframe[src*="challenges.cloudflare.com"]') is not None
    except Exception:
        return False


def search_url(site: str, query: str) -> str:
    """Link search sẵn query — dùng cả khi tự tải lẫn khi user muốn mở tay."""
    from urllib.parse import quote_plus

    cfg = SITES.get(site)
    if cfg is None:
        raise ValueError(f"Nguồn lạ: {site} (chỉ có {', '.join(SITES)})")
    return cfg["search"].format(q=quote_plus(query.strip()))


class SubscriptionClient:
    """Tải footage từ nguồn subscription qua Chrome thật + profile đã login.

    Mỗi lần tải đều đi qua phanh. Gặp challenge là dừng hẳn nguồn (self.blocked),
    mọi lần gọi sau trả rỗng ngay — KHÔNG thử lại.
    """

    def __init__(self, site: str, profiles_root: Optional[Path] = None,
                 limiter: Optional[RateLimiter] = None, headless: bool = False) -> None:
        if site not in SITES:
            raise ValueError(f"Nguồn lạ: {site} (chỉ có {', '.join(SITES)})")
        self.site = site
        self.SOURCE_NAME = site
        self.profiles_root = profiles_root
        self.limiter = limiter or RateLimiter()
        self.headless = headless
        self.blocked = False       # gặp challenge -> đóng nguồn cả phiên
        self.consecutive_fail = 0
        self._pw = None
        self._ctx = None

    # ------------------------------ trình duyệt -----------------------------
    def _context(self):
        """Persistent context dùng Chrome THẬT — fingerprint vượt Cloudflare tốt hơn."""
        if self._ctx is not None:
            return self._ctx
        from playwright.sync_api import sync_playwright

        pdir = profiles_dir(self.profiles_root) / self.site
        pdir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        kw = dict(
            user_data_dir=str(pdir), headless=self.headless, accept_downloads=True,
            viewport={"width": 1440, "height": 900}, locale="en-US",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        try:
            self._ctx = self._pw.chromium.launch_persistent_context(channel="chrome", **kw)
        except Exception:
            self._ctx = self._pw.chromium.launch_persistent_context(**kw)
        self._ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        return self._ctx

    def close(self) -> None:
        for obj, meth in ((self._ctx, "close"), (self._pw, "stop")):
            try:
                if obj is not None:
                    getattr(obj, meth)()
            except Exception:
                pass
        self._ctx = self._pw = None

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------ tải -------------------------------------
    def download(self, page_url: str, dest: Path) -> Path:
        """Mở trang clip, bấm Download, lưu file. Raise BlockedError nếu gặp challenge."""
        if self.blocked:
            raise BlockedError(f"{self.site}: đã dừng phiên này (gặp challenge trước đó)")
        self.limiter.check()

        page = self._context().new_page()
        try:
            page.goto(page_url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            if is_challenge(page):
                self.blocked = True
                raise BlockedError(
                    f"{self.site}: gặp captcha/challenge — DỪNG nguồn này cả phiên. "
                    f"Mở trình duyệt đăng nhập lại rồi chạy sau."
                )
            dest.parent.mkdir(parents=True, exist_ok=True)
            with page.expect_download(timeout=NAV_TIMEOUT_MS) as info:
                self._click_download(page)
            info.value.save_as(str(dest))
        except BlockedError:
            raise
        except Exception as exc:
            self.consecutive_fail += 1
            if self.consecutive_fail >= _MAX_CONSECUTIVE_FAIL:
                self.blocked = True
                raise BlockedError(
                    f"{self.site}: {_MAX_CONSECUTIVE_FAIL} lần tải hỏng liên tiếp — "
                    f"nghi bị chặn mềm, DỪNG nguồn. Lỗi cuối: {exc}"
                ) from exc
            raise RuntimeError(f"{self.site}: tải hỏng ({exc})") from exc
        finally:
            try:
                page.close()
            except Exception:
                pass

        if not dest.is_file() or dest.stat().st_size < MIN_VIDEO_BYTES:
            dest.unlink(missing_ok=True)
            self.consecutive_fail += 1
            raise RuntimeError(f"{self.site}: file quá nhỏ — bị chặn hoặc dính bản preview")

        self.consecutive_fail = 0
        self.limiter.record()
        self.limiter.pause()      # nghỉ NGẪU NHIÊN trước lần sau
        return dest

    def _click_download(self, page) -> None:
        """Bấm nút Download. Selector theo text nên site đổi giao diện là phải sửa."""
        sel = ('[data-testid="download-button"], button[aria-label*="download" i], '
               'a[href*="download" i], button:has-text("Download")')
        btn = page.query_selector(sel)
        if btn is None:
            raise RuntimeError("không thấy nút Download (site đổi giao diện?)")
        btn.click()
        # Envato hỏi lại "Add & Download" ở hộp thoại thứ hai
        page.wait_for_timeout(1200)
        confirm = page.query_selector('button:has-text("Add & Download"), '
                                      'button:has-text("Download")')
        if confirm is not None:
            try:
                confirm.click()
            except Exception:
                pass


def available_sites(env: Optional[dict] = None,
                    profiles_root: Optional[Path] = None) -> list[str]:
    """Nguồn dùng được: có khai email trong .env VÀ đã đăng nhập (có profile)."""
    env = env if env is not None else os.environ
    out = []
    for site, cfg in SITES.items():
        if env.get(cfg["env"], "").strip() and profile_exists(site, profiles_root):
            out.append(site)
    return out
