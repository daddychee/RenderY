"""Lấy khoá API từ két OUTLIERY-V3 — một cửa duy nhất, không đọc .env.

Luật V3 (`docs/APPS.md` bước 5): khoá API do Owner nhập ở **General › API Keys**,
app phụ hỏi qua `GET /api/cau-hinh/api-khoa/<slug>` trên loopback. App KHÔNG giữ
sổ khoá riêng, KHÔNG đọc `.env` (`start-all.ps1`: *"app con KHÔNG tự gọi
load_dotenv() — mọi app khác phải được bơm biến qua đây"*).

Két trả theo VIỆC (`viec_api` khai trong `apps.json`):
    {"chia_beat":   {"khoa": [{"id","key","loai","nha"}], "che_do", "model"},
     "cham_footage": {...}}

Fail-open: gateway tắt / chưa cấp phát khoá -> trả rỗng, caller rơi về `.env`.
Chạy trực tiếp ngoài V3 (dev) cũng đi đường đó, nên một mã chạy được cả hai nơi.
"""

from __future__ import annotations

import os
import time
from typing import Optional

SLUG = "rendery"
GATEWAY = os.getenv("RENDERY_GATEWAY", "http://127.0.0.1:9000")
_TIMEOUT = 5
_TTL = 60          # giây — Owner đổi khoá trên UI thì trong 1 phút app thấy


_cache: dict = {"luc": 0.0, "data": {}}


def doc_ket(force: bool = False) -> dict:
    """Đọc cấp phát khoá từ két. {} nếu không hỏi được (fail-open)."""
    now = time.monotonic()
    if not force and _cache["data"] and now - _cache["luc"] < _TTL:
        return _cache["data"]
    try:
        import requests

        r = requests.get(f"{GATEWAY}/api/cau-hinh/api-khoa/{SLUG}", timeout=_TIMEOUT)
        # Gọi .json() ĐÚNG MỘT LẦN — gọi hai lần là hai lượt parse (và với response
        # giả trong test là hai lượt gọi mạng).
        data = r.json() if r.ok else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}                      # gateway tắt / mạng lỗi — rơi về .env
    if data:
        _cache.update(luc=now, data=data)
    return data


def khoa_cua_viec(viec: str) -> tuple[str, str]:
    """(khoá đầu tiên, model) của một việc. ('','') nếu chưa cấp phát."""
    muc = doc_ket().get(viec) or {}
    ds = muc.get("khoa") or []
    return (ds[0].get("key", "") if ds else ""), (muc.get("model") or "")


def nap_env() -> list[str]:
    """Đổ khoá từ két vào os.environ theo tên biến pipeline đang dùng.

    Gọi lúc khởi động job. Khoá lấy được ĐÈ giá trị cũ (két là nguồn sự thật);
    việc nào két chưa có thì giữ nguyên `.env` — nên máy dev không cần gateway.

    Trả danh sách biến đã đặt (KHÔNG chứa giá trị — không bao giờ log khoá).
    """
    dat: list[str] = []
    ket = doc_ket()
    if not ket:
        return dat

    # chia_beat = đạo diễn chia beat (stage direct). Nhà cung cấp quyết tên biến:
    # Anthropic -> ANTHROPIC_API_KEY; còn lại đi đường OpenAI-compatible.
    for viec, bien_model in (("chia_beat", "L3_MODEL"), ("cham_footage", "RANK_MODEL")):
        muc = ket.get(viec) or {}
        ds = muc.get("khoa") or []
        if not ds:
            continue
        k = ds[0]
        nha = (k.get("nha") or "").lower()
        key = k.get("key") or ""
        if not key:
            continue
        if "anthropic" in nha or "claude" in nha:
            os.environ["ANTHROPIC_API_KEY"] = key
            dat.append("ANTHROPIC_API_KEY")
        else:
            # GLM/DeepSeek/OpenAI — pipeline đọc LLM_API_KEY + LLM_BASE_URL
            os.environ["LLM_API_KEY"] = key
            dat.append("LLM_API_KEY")
            if "glm" in nha or "z.ai" in nha or "zhipu" in nha:
                os.environ.setdefault("LLM_PROVIDER", "glm")
            elif "deepseek" in nha:
                os.environ.setdefault("LLM_PROVIDER", "deepseek")
        if muc.get("model"):
            os.environ[bien_model] = muc["model"]
            dat.append(bien_model)
    return dat


def trang_thai() -> dict:
    """Cho UI: két có nối được không, việc nào đã có khoá (KHÔNG lộ giá trị)."""
    ket = doc_ket()
    return {
        "noi_duoc": bool(ket),
        "gateway": GATEWAY,
        "viec": {v: {"co_khoa": bool((m or {}).get("khoa")),
                     "model": (m or {}).get("model", "")}
                 for v, m in ket.items()},
    }
