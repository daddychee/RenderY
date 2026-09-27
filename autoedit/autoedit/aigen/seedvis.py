r"""Client Seedvis — ảnh (Nano Banana) + video i2v (Omni Flash / Veo 3.1).

Vì sao có (user chốt 27/09): *"Hãy đấu nối hạ tầng với seedvis. Tôi không dùng
seedance nữa."* Đo cùng ngày (trang seedvis.html): ảnh có mặt người mà ModelArk
từ chối ngay khi nộp thì Seedvis nhận và chạy; 4 ảnh tham chiếu (master + 3
asset) Nano Banana Pro neo đủ nhận dạng và tái hiện căn phòng của master sát
hơn Seedream; 2752×1536 khi upscale 2k. Giá ~1/10 ModelArk.

CÙNG HÌNH DẠNG với `ArkClient` ở đúng bốn hàm treatment gọi — `gen_anh`,
`gen_video_i2v`, `trang_thai_video`, `tai_video` — để app chọn nhà theo
`base_url` trong két mà không đổi dòng nào ở tầng treatment.

Khác ModelArk ở ba chỗ, đều theo tài liệu Seedvis API v2.0:
- Mọi lượt đều bất đồng bộ: 202 + `next.url`, poll tới `is_final`. `queued`/
  `processing` là THÀNH CÔNG, không được gửi lại — gửi lại là job mới, trừ
  credit lần nữa. Gửi kèm `Idempotency-Key` để retry mạng không đẻ job thứ hai.
- Video tối đa 8 giây (4/6/8) — không phải 15. Độ dài phải theo model, nên
  `self.giay` là thứ app hỏi thay vì hằng số.
- Endpoint Google (Nano Banana) trả thân KHÔNG bọc trong `data`; endpoint
  native thì bọc. `_du_lieu()` san bằng.
"""

from __future__ import annotations

import base64
import time
import uuid
from pathlib import Path
from typing import Optional

import requests

from autoedit.aigen.client import AigenError
from autoedit.httpx_ma import nen_thu_lai

BASE_MAC_DINH = "https://seedvis.com/api/v1"
MODEL_ANH_MAC_DINH = "GEM_PIX_2"          # Nano Banana Pro — đo 27/09, 4 ref neo đủ
MODEL_VIDEO_MAC_DINH = "Omni-Flash"       # Veo-3.1 cùng tham số, đổi ở két khi hết bảo trì
GIAY_HOP_LE = (4, 6, 8)                   # Omni Flash / Veo: "4s" | "6s" | "8s"
# Độ dài tối đa theo MODEL (tài liệu Seedvis v2.0). Lệnh LLM, prompt video và cảnh
# báo trên trang ăn theo model video HIỆU LỰC của cảnh. Model lạ -> 8 (an toàn).
GIAY_THEO_MODEL = {"Omni-Flash": 8, "Veo-3.1": 8, "seedance_2.0_fast": 15, "seedance_2.5": 30}


def giay_theo_model(model: str) -> int:
    return GIAY_THEO_MODEL.get((model or "").strip(), GIAY_HOP_LE[-1])
_UA = "RenderY-treatment/1.0"


def _mime(p: Path) -> str:
    s = p.suffix.lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(s, "image/png")


def _data_url(p: Path) -> str:
    p = Path(p)
    return f"data:{_mime(p)};base64," + base64.b64encode(p.read_bytes()).decode()


def giay_hop_le(giay: int) -> int:
    """Ép về mức model nhận: 15 -> 8, 7 -> 6, 3 -> 4."""
    ok = [g for g in GIAY_HOP_LE if g <= max(int(giay or 0), GIAY_HOP_LE[0])]
    return ok[-1] if ok else GIAY_HOP_LE[0]


class SeedvisClient:
    GIAY = GIAY_HOP_LE[-1]

    def __init__(self, api_key: Optional[str], base_url: str = BASE_MAC_DINH,
                 model_anh: Optional[str] = None, model_video: Optional[str] = None,
                 timeout: int = 180, retries: int = 3) -> None:
        if not api_key:
            raise AigenError("Chưa có khoá Seedvis — Owner cấp ở General › API Keys › "
                             "Theo app › Treatment › gen_canh.")
        self._key = api_key
        self.base = (base_url or BASE_MAC_DINH).rstrip("/")
        self.model_anh = model_anh or MODEL_ANH_MAC_DINH
        self.model_video = model_video or MODEL_VIDEO_MAC_DINH
        self.timeout, self.retries = timeout, retries
        # Độ dài clip theo MODEL video đang cấp (Omni/Veo 8, Seedance 15/30):
        # lệnh LLM, prompt video và trang đọc qua `_VeVideo.giay`.
        self.giay = giay_theo_model(self.model_video)
        self._session = requests.Session()     # test thay bằng phiên giả

    # ------------------------------------------------------------- HTTP
    def _headers(self, them: Optional[dict] = None) -> dict:
        h = {"Authorization": f"Bearer {self._key}", "User-Agent": _UA}
        h.update(them or {})
        return h

    def _goi(self, method: str, path: str, body: Optional[dict] = None,
             idem: Optional[str] = None) -> dict:
        """Ghi SỔ GỌI NỀN quanh lời gọi thật, như ArkClient: một dòng sổ = một
        lượt việc, sổ chết không hỏng việc."""
        from autoedit import so_goi_nen

        t0 = time.time()
        try:
            r = self._goi_that(method, path, body, idem)
        except Exception as e:  # noqa: BLE001 — ghi sổ rồi ném nguyên vẹn
            so_goi_nen.ghi("llm", duoi=self._key[-4:], ok=False, ma_loi=str(e)[:200],
                           viec="gen_canh", ms=(time.time() - t0) * 1000)
            raise
        so_goi_nen.ghi("llm", duoi=self._key[-4:], ok=True, viec="gen_canh",
                       ms=(time.time() - t0) * 1000)
        return r

    def _goi_that(self, method: str, path: str, body: Optional[dict],
                  idem: Optional[str]) -> dict:
        url = path if path.startswith("http") else self.base + path
        them = {"Content-Type": "application/json"} if body is not None else {}
        if idem:
            them["Idempotency-Key"] = idem        # retry cùng key = cùng job
        loi: Exception | None = None
        for lan in range(self.retries):
            try:
                r = self._session.request(method, url, json=body, headers=self._headers(them),
                                          timeout=self.timeout)
            except Exception as exc:  # noqa: BLE001 — mạng
                loi = exc
                time.sleep(1.5 * (lan + 1))
                continue
            if r.status_code < 400:
                try:
                    return r.json()
                except ValueError as exc:
                    raise AigenError(f"Seedvis trả về không phải JSON: {r.text[:200]}") from exc
            loi = AigenError(f"Seedvis HTTP {r.status_code}: {r.text[:300]}")
            if not nen_thu_lai(r.status_code):
                raise loi
            time.sleep(float(r.headers.get("Retry-After") or 1.5 * (lan + 1)))
        raise AigenError(f"Seedvis: gọi hỏng sau {self.retries} lần ({loi})")

    @staticmethod
    def _du_lieu(j: dict) -> dict:
        """Native bọc trong `data`; endpoint Google trả trần. San bằng."""
        d = j.get("data") if isinstance(j, dict) else None
        return d if isinstance(d, dict) else (j if isinstance(j, dict) else {})

    def _cho(self, d: dict, cho_toi_da: int = 900) -> dict:
        """Đi theo `next.url` tới `is_final`. KHÔNG gửi lại request."""
        t0 = time.time()
        while not d.get("is_final") and time.time() - t0 < cho_toi_da:
            nx = d.get("next") or {}
            url = nx.get("url") or f"{self.base}/developer/generations/{d.get('id')}?wait=30"
            time.sleep(min(float(nx.get("after_seconds") or 5), 30))
            d = self._du_lieu(self._goi("GET", url))
        if not d.get("is_final"):
            raise AigenError(f"Seedvis: job {d.get('id')} chưa xong sau {cho_toi_da}s")
        if d.get("status") == "failed":
            e = d.get("error") or {}
            raise AigenError(f"Seedvis: job hỏng — {e.get('code')}: {e.get('message')}")
        return d

    # ------------------------------------------------------------- ảnh
    # ------------------------------------------------------------- bảng chọn
    def ds_model(self) -> list[dict]:
        """`GET /models` — nguồn sự thật duy nhất về model đang mở. Trả gọn cho
        bảng chọn trong UI: id · label · type (image/video) · status."""
        j = self._goi("GET", "/models")
        ds = j.get("data") if isinstance(j, dict) else j
        return [{"id": m.get("id"), "label": m.get("label") or m.get("id"),
                 "type": m.get("type"), "status": m.get("status") or "active"}
                for m in (ds or []) if isinstance(m, dict) and m.get("id")]

    def tai_khoan(self) -> dict:
        d = self._du_lieu(self._goi("GET", "/account/info"))
        return {"credit": d.get("credit_balance"), "goi": (d.get("plan") or {}).get("code"),
                "luong": d.get("concurrency_limit")}

    def gen_anh(self, prompt: str, dich: Path, size: str = "2560x1440",
                ref: "list[Path] | None" = None, model: Optional[str] = None) -> Path:
        """Nano Banana qua endpoint Google. `size` chỉ để cùng chữ ký với
        ArkClient: Seedvis nhận tỉ lệ + upscale, 16:9 + 2k = 2752×1536."""
        anh_ref = [Path(p) for p in (ref or []) if Path(p).exists()]
        than = {"model": model or self.model_anh, "input": prompt, "aspect_ratio": "16:9",
                "upscale_image": "2k", "count": 1,
                "mode": "image-to-image" if anh_ref else "text-to-image"}
        if anh_ref:
            than["reference_images"] = [_data_url(p) for p in anh_ref]
        d = self._du_lieu(self._goi("POST", "/google/v1beta/interactions", than,
                                    idem=str(uuid.uuid4())))
        d = self._cho(d)
        outs = d.get("outputs") or []
        if not outs or not outs[0].get("url"):
            raise AigenError("Seedvis: xong mà không có ảnh trong `outputs`.")
        dich = Path(dich)
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(self._tai(outs[0]["url"]))
        return dich

    def _tai(self, url: str) -> bytes:
        r = self._session.get(url, headers={"User-Agent": _UA}, timeout=300)
        if r.status_code >= 400:
            raise AigenError(f"Seedvis: tải kết quả hỏng HTTP {r.status_code}")
        return r.content

    # ------------------------------------------------------------- video i2v
    def gen_video_i2v(self, prompt: str, anh: Path, giay: int = 8,
                      am: bool = True, model: Optional[str] = None) -> str:
        """Nộp task, trả id. `am` không có tham số tương ứng ở Omni/Veo — bỏ qua.
        Seedance (nếu ai chọn) nhận `duration` là số 5..30, còn Omni/Veo nhận "4s"."""
        _ = am
        m = model or self.model_video
        if m.startswith("seedance"):
            cho_phep = (5, 10, 15) if "fast" in m else (5, 10, 15, 20, 25, 30)
            d = max([g for g in cho_phep if g <= max(int(giay or 5), 5)] or [5])
            than = {"model": m, "mode": "image-to-video", "prompt": prompt,
                    "reference_images": [_data_url(Path(anh))], "aspect_ratio": "16:9",
                    "duration": d}
        else:
            than = {"model": m, "mode": "image-to-video", "prompt": prompt,
                    "image": _data_url(Path(anh)), "aspect_ratio": "16:9",
                    "duration": f"{giay_hop_le(giay)}s", "upscale_video": "none"}
        d = self._du_lieu(self._goi("POST", "/developer/generations", than,
                                    idem=str(uuid.uuid4())))
        if not d.get("id"):
            raise AigenError(f"Seedvis: nộp video không trả id ({str(d)[:200]})")
        return str(d["id"])

    def trang_thai_video(self, task_id: str) -> dict:
        """Một lần hỏi (máy chủ giữ tới 30 s). Trả hình dạng phẳng như ArkClient:
        {status: succeeded|failed|queued|processing, video_url, loi}."""
        d = self._du_lieu(self._goi("GET", f"/developer/generations/{task_id}?wait=30"))
        tt = str(d.get("status") or "")
        if tt == "completed":
            outs = d.get("outputs") or []
            return {"status": "succeeded", "video_url": (outs[0].get("url") if outs else "")}
        if tt == "failed":
            e = d.get("error") or {}
            return {"status": "failed", "loi": f"{e.get('code')}: {e.get('message')}"}
        return {"status": tt or "queued"}

    def tai_video(self, url: str, dich: Path) -> Path:
        dich = Path(dich)
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(self._tai(url))
        return dich
