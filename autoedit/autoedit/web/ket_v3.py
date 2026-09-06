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

        # TOKEN NỘI BỘ (CRM 05/09, nen/common/token_noi_bo.py): route phát khoá
        # đòi header X-Noi-Bo khớp OUTLIERY_TOKEN_NOI_BO — start-all đặt ở tiến
        # trình cha, cả cụm kế thừa CÙNG một giá trị (nên phải restart cả cụm,
        # không restart lẻ). Máy dev không có biến -> không gửi, gateway không
        # siết thì vẫn qua (đúng khuôn token_noi_bo.header()).
        tnb = os.getenv("OUTLIERY_TOKEN_NOI_BO", "").strip()
        r = requests.get(f"{GATEWAY}/api/cau-hinh/api-khoa/{SLUG}",
                         headers={"X-Noi-Bo": tnb} if tnb else {},
                         timeout=_TIMEOUT)
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
                # Mọi code GLM trong repo (director/glm_client, library/vision,
                # ranker/visiongate, library/stock_tags) đọc GLM_API_KEY chứ KHÔNG
                # đọc LLM_API_KEY — thiếu dòng này thì két có khoá mà job vẫn báo
                # "Thiếu GLM_API_KEY" rồi lặng lẽ TẮT vision gate (sự cố 30/08).
                os.environ["GLM_API_KEY"] = key
                dat.append("GLM_API_KEY")
                # Nhiều khoá GLM = nhiều luồng song song (vision/tag chạy
                # 3 luồng/khoá — quá thì bigmodel cắt kết nối). Khoá phụ đi
                # GLM_API_KEY_2..9 đúng khuôn library/vision.glm_api_keys().
                for i, phu in enumerate(ds[1:9], start=2):
                    kp = phu.get("key") or ""
                    if kp and (phu.get("nha") or "").lower() == nha:
                        os.environ[f"GLM_API_KEY_{i}"] = kp
                        dat.append(f"GLM_API_KEY_{i}")
            elif "deepseek" in nha:
                os.environ.setdefault("LLM_PROVIDER", "deepseek")
        if muc.get("model"):
            os.environ[bien_model] = muc["model"]
            dat.append(bien_model)

    # gen_canh: sinh cảnh AI (Seedream ảnh + Seedance video) — một khoá ARK dùng
    # chung cả hai model (aigen/client.py đọc ARK_API_KEY).
    for k in ((ket.get("gen_canh") or {}).get("khoa") or []):
        if k.get("key"):
            os.environ["ARK_API_KEY"] = k["key"]
            dat.append("ARK_API_KEY")
            break

    # tim_footage: kho ảnh/video. NHIỀU khoá cùng nhà = nhân hạn mức (Pexels ~200
    # query/giờ/khoá) — pipeline nhận danh sách ngăn bằng dấu phẩy.
    for k in ((ket.get("tim_footage") or {}).get("khoa") or []):
        nha = (k.get("nha") or "").lower()
        key = k.get("key") or ""
        if not key:
            continue
        bien = {"pexels": "PEXELS_API_KEY", "pixabay": "PIXABAY_API_KEY"}.get(nha)
        if not bien:
            continue
        cu = os.environ.get(bien, "")
        # Khoá thứ 2 trở đi NỐI vào, không đè — collect_*_keys tách theo dấu phẩy
        os.environ[bien] = f"{cu},{key}" if cu and bien in dat else key
        if bien not in dat:
            dat.append(bien)

    # tim_tu_lieu: tư liệu thật cho beat entity — sourcer/entity.py đọc
    # SERPER_API_KEY (Serper.dev, Google Images). Nhà khác (serpapi/searchapi)
    # chưa có client trong pipeline nên bỏ qua, không nhét nhầm biến.
    for k in ((ket.get("tim_tu_lieu") or {}).get("khoa") or []):
        if k.get("key") and (k.get("nha") or "").lower() == "serper":
            os.environ["SERPER_API_KEY"] = k["key"]
            dat.append("SERPER_API_KEY")
            break
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
