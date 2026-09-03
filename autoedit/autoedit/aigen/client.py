r"""Client BytePlus ModelArk — Seedream (ảnh) + Seedance (video i2v).

Đợt 2 (user chốt 03/09): beat thiếu hình → Seedream sinh ẢNH cho editor duyệt
trên UI, ảnh chốt rồi mới Seedance image-to-video — tiền video chỉ đốt sau cổng
duyệt. Một key ARK dùng chung cả hai model.

Giá (tra 03/09/2026): ảnh ~$0.03/tấm · video ~$0.03/giây (Pro thường).
Model ID xác nhận từ docs BytePlus: seedream-3-0-t2i-250415 / seedream-4-5-251128
/ seedream-5-0-260128. THU_MODEL thử lần lượt — ID hết hạn thì rơi bậc kế,
không chết cứng vào một ID.

Khuôn lỗi/retry: dùng chung httpx_ma (bài học 504 ngày 31/08).
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from autoedit.httpx_ma import nen_thu_lai

ARK_URL = os.getenv("ARK_API_URL", "https://ark.ap-southeast.bytepluses.com/api/v3")
# Thử theo thứ tự chất lượng/giá hợp lý; ID nào key không có quyền thì bỏ qua.
THU_MODEL_ANH = ("seedream-4-5-251128", "seedream-4-0-250828", "seedream-3-0-t2i-250415")
THU_MODEL_VIDEO = ("seedance-1-0-pro-250528", "seedance-1-0-lite-i2v-250428")


class AigenError(RuntimeError):
    """Lỗi gọi ModelArk — thông điệp tiếng Việt, caller in thẳng."""


class ArkClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 180,
                 retries: int = 3) -> None:
        key = api_key or os.getenv("ARK_API_KEY", "")
        if not key:
            # .env của V2 (worktree) — python-dotenv chỉ nạp khi CLI gọi load_dotenv
            from dotenv import load_dotenv

            load_dotenv()
            key = os.getenv("ARK_API_KEY", "")
        if not key:
            raise AigenError("Thiếu ARK_API_KEY (.env V2 hoặc két General › generate).")
        self._key = key
        self.timeout = timeout
        self.retries = retries
        self.model_anh: str | None = None      # ID đầu tiên chạy được, cache lại

    # ------------------------------------------------------------- HTTP
    def _goi(self, path: str, body: dict, method: str = "POST") -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        loi: Exception | None = None
        for lan in range(self.retries):
            req = urllib.request.Request(
                f"{ARK_URL}{path}", data=data, method=method,
                headers={"Authorization": f"Bearer {self._key}",
                         "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                chi_tiet = exc.read().decode("utf-8", "replace")[:300]
                loi = AigenError(f"ModelArk HTTP {exc.code}: {chi_tiet}")
                if not nen_thu_lai(exc.code):
                    raise loi from exc
            except Exception as exc:  # noqa: BLE001 — mạng
                loi = exc
            if lan < self.retries - 1:
                time.sleep(2 ** lan)
        raise AigenError(f"ModelArk lỗi sau {self.retries} lần: {loi}")

    # ------------------------------------------------------------- ảnh
    def gen_anh(self, prompt: str, dich: Path, size: str = "2560x1440") -> Path:
        """Sinh 1 ảnh -> ghi file. 2560x1440 (16:9): seedream-4-5 đòi ảnh
        ≥3,69M pixel (probe 03/09 nhận 400 InvalidParameter với 2048x1152).

        Trả b64 thay vì URL: URL ModelArk có hạn dùng, tải ngay tránh bẫy
        assetUrl-hết-hạn kiểu Epidemic (đo 18/07).
        """
        cac_model = (self.model_anh,) if self.model_anh else THU_MODEL_ANH
        loi_cuoi: Exception | None = None
        for model in cac_model:
            try:
                r = self._goi("/images/generations", {
                    "model": model, "prompt": prompt, "size": size,
                    "response_format": "b64_json", "watermark": False})
                b64 = r["data"][0]["b64_json"]
                dich = Path(dich)
                dich.parent.mkdir(parents=True, exist_ok=True)
                dich.write_bytes(base64.b64decode(b64))
                self.model_anh = model
                return dich
            except AigenError as exc:
                loi_cuoi = exc
                # model không tồn tại/không quyền -> thử ID kế; lỗi khác -> ném
                if "HTTP 404" in str(exc) or "ModelNotOpen" in str(exc) \
                        or "InvalidParameter" in str(exc) and "model" in str(exc):
                    continue
                raise
        raise AigenError(f"Không model ảnh nào chạy được ({loi_cuoi})")

    # ------------------------------------------------------------- video i2v
    def gen_video_i2v(self, prompt: str, anh: Path, giay: int = 5) -> str:
        """Tạo TASK sinh video từ ảnh đã duyệt. Trả task_id — video sinh bất đồng
        bộ, poll bằng cho_video(). Ảnh gửi dạng data URL b64."""
        b64 = base64.b64encode(Path(anh).read_bytes()).decode()
        mime = "image/png" if str(anh).lower().endswith("png") else "image/jpeg"
        loi_cuoi: Exception | None = None
        for model in THU_MODEL_VIDEO:
            try:
                r = self._goi("/contents/generations/tasks", {
                    "model": model,
                    "content": [
                        {"type": "text", "text": f"{prompt} --duration {giay}"},
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ]})
                return r["id"]
            except AigenError as exc:
                loi_cuoi = exc
                if "HTTP 404" in str(exc) or "ModelNotOpen" in str(exc):
                    continue
                raise
        raise AigenError(f"Không model video nào chạy được ({loi_cuoi})")

    def cho_video(self, task_id: str, dich: Path, cho_toi_da: int = 600) -> Path:
        """Poll task tới khi xong -> tải video về `dich`."""
        t0 = time.time()
        while time.time() - t0 < cho_toi_da:
            r = self._goi(f"/contents/generations/tasks/{task_id}", None, method="GET")
            tt = r.get("status")
            if tt == "succeeded":
                url = r["content"]["video_url"]
                dich = Path(dich)
                dich.parent.mkdir(parents=True, exist_ok=True)
                with urllib.request.urlopen(url, timeout=300) as vr:
                    dich.write_bytes(vr.read())
                return dich
            if tt in ("failed", "cancelled"):
                raise AigenError(f"Task video {tt}: {str(r)[:200]}")
            time.sleep(5)
        raise AigenError(f"Task video quá {cho_toi_da}s chưa xong — thử lại sau")
