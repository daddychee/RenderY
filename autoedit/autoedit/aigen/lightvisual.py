"""Lightvisual.studio — video Grok Imagine qua REST /v1 (Owner chốt 29/10: "mặc định dùng ncc
này để gen video"; ảnh vẫn GPT Image 2 ở Seedvis). Cùng hình dạng với SeedvisClient phần video
(`gen_video_i2v`, `gen_video_ref`, `trang_thai_video`, `tai_video`, `ds_model`) để `_VeVideo`
đổi nhà mà nơi gọi giữ nguyên.

Đo thật 29/10 (gói "Grok vô hạn", key của Owner):
  * I2V 720p 6 s xong 37–45 s; 3 job gửi cùng lúc chạy song song, xong cùng lúc.
  * Lượt đầu có lúc 502 "Hệ thống đang xử lý lượng lớn yêu cầu… thử lại 5–10 giây (Không mất
    Credits)" -> thử lại.
  * File ra 1264×720 và kèm một luồng ảnh bìa mjpeg -> bỏ bằng chép luồng (không encode lại).
  * `/balance` báo 0đ / PAYG cả khi gói đang chạy: không dùng làm số dư.
Mã task bắt đầu `lv_job_` — `_VeVideo` nhận nhà theo tiền tố đó.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests

from autoedit.aigen.client import AigenError
from autoedit.aigen.seedvis import _data_url_jpeg, giay_grok
from autoedit.httpx_ma import nen_thu_lai

BASE_MAC_DINH = "https://lightvisual.studio/v1"
MODEL_GROK = "xai/grok-imagine-video-1.5"
TIEN_TO_TASK = "lv_job_"
_UA = "RenderY-treatment/1.0"


def _model(m: Optional[str]) -> str:
    """Mã model app dùng (của Seedvis, `grok-imagine-video-1.5`) -> mã lightvisual (`xai/…`)."""
    m = (m or "").strip() or MODEL_GROK
    return m if "/" in m else "xai/" + m


def _the(prompt: str) -> str:
    """Prompt app gọi ảnh tham chiếu là "Image 1, Image 2…"; lightvisual dùng <IMAGE_0>…"""
    return re.sub(r"\bImage ([1-9])\b", lambda k: f"<IMAGE_{int(k.group(1)) - 1}>", prompt)


def _ffmpeg() -> Optional[str]:
    p = shutil.which("ffmpeg") or r"C:\OutlierY\tools\ffmpeg\bin\ffmpeg.exe"
    return p if os.path.exists(p) or shutil.which(p) else None


class LightvisualClient:
    GIAY = 15

    def __init__(self, api_key: Optional[str], base_url: str = BASE_MAC_DINH,
                 timeout: int = 180, retries: int = 4) -> None:
        if not api_key:
            raise AigenError("Chưa có khoá Lightvisual — Owner cấp ở General › API Keys › "
                             "Theo app › Treatment › gen_video.")
        self._key = api_key
        self.base = (base_url or BASE_MAC_DINH).rstrip("/")
        self.timeout, self.retries = timeout, retries
        self.giay = self.GIAY
        self._session = requests.Session()     # test thay bằng phiên giả

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._key}", "User-Agent": _UA}

    def _goi(self, method: str, path: str, body: Optional[dict] = None, thu_lai_429: bool = True) -> dict:
        """Sổ gọi nền như SeedvisClient: một dòng sổ = một lượt việc, sổ chết không hỏng việc."""
        from autoedit import so_goi_nen

        t0 = time.time()
        try:
            r = self._goi_that(method, path, body, thu_lai_429)
        except Exception as e:  # noqa: BLE001 — ghi sổ rồi ném nguyên vẹn
            so_goi_nen.ghi("llm", duoi=self._key[-4:], ok=False, ma_loi=str(e)[:200],
                           viec="gen_video", ms=(time.time() - t0) * 1000)
            raise
        so_goi_nen.ghi("llm", duoi=self._key[-4:], ok=True, viec="gen_video",
                       ms=(time.time() - t0) * 1000)
        return r

    def _goi_that(self, method: str, path: str, body: Optional[dict], thu_lai_429: bool = True) -> dict:
        loi: Exception | None = None
        for lan in range(self.retries):
            try:
                r = self._session.request(method, self.base + path, json=body, headers=self._headers(),
                                          timeout=self.timeout)
            except Exception as exc:  # noqa: BLE001 — mạng
                loi = exc
                time.sleep(3 * (lan + 1))
                continue
            if r.status_code < 400:
                try:
                    return r.json()
                except ValueError as exc:
                    raise AigenError(f"Lightvisual trả về không phải JSON: {r.text[:200]}") from exc
            loi = AigenError(f"Lightvisual HTTP {r.status_code}: {r.text[:300]}")
            loi.ma = r.status_code
            if not nen_thu_lai(r.status_code) or (r.status_code == 429 and not thu_lai_429):
                raise loi
            # Quá tải họ báo "thử lại sau 5–10 giây (không mất credit)".
            time.sleep(float(r.headers.get("Retry-After") or 8 * (lan + 1)))
        raise AigenError(f"Lightvisual: gọi hỏng sau {self.retries} lần ({loi})")

    def _nop(self, than: dict) -> str:
        d = self._goi("POST", "/videos", than)
        tid = d.get("id") or d.get("job_id")
        if not tid:
            raise AigenError(f"Lightvisual: nộp video không trả id ({str(d)[:200]})")
        return str(tid)

    # ------------------------------------------------------------- video
    def gen_video_i2v(self, prompt: str, anh: Path, giay: int = 6, am: bool = True,
                      model: Optional[str] = None) -> str:
        """Shot drama: khung đầu là ảnh đã duyệt. `am` không có tham số tương ứng — Grok tự ra tiếng."""
        _ = am
        return self._nop({"model": _model(model), "prompt": prompt, "seconds": giay_grok(giay),
                          "resolution": "720p", "image": {"url": _data_url_jpeg(Path(anh))}})

    def gen_video_ref(self, prompt: str, anh: "list[Path]", giay: int = 15,
                      model: Optional[str] = None) -> str:
        """Clip drama dựng từ ẢNH THAM CHIẾU (R2V, Grok 1.5 nhận tới 15 ảnh), không khung đầu."""
        return self._nop({"model": _model(model), "prompt": _the(prompt), "seconds": giay_grok(giay),
                          "resolution": "720p",
                          "reference_images": [{"url": _data_url_jpeg(Path(p))} for p in anh]})

    def trang_thai_video(self, task_id: str) -> dict:
        """Một lần hỏi. Hình dạng như SeedvisClient: {status: succeeded|failed|queued|processing,
        video_url, loi}. `video_url` là đường /content có khoá — đường /api/tenants họ trả là của web."""
        # 429 không thử lại (30/10): trang hỏi lại sau 20 s; ngủ 8/16/24 s ở đây chỉ giữ luồng và dồn
        # thêm lượt vào lúc nhà đang giới hạn tốc độ. Lỗi mang `ma` = 429 để route trả "đang dựng".
        d = self._goi("GET", f"/videos/{task_id}", thu_lai_429=False)
        tt = str(d.get("status") or "")
        if tt == "completed":
            return {"status": "succeeded", "video_url": f"{self.base}/videos/{task_id}/content"}
        if tt == "failed":
            e = d.get("error") or {}
            return {"status": "failed", "loi": e.get("message") if isinstance(e, dict) else str(e)}
        return {"status": tt or "queued"}

    def tai_video(self, url: str, dich: Path) -> Path:
        dich = Path(dich)
        dich.parent.mkdir(parents=True, exist_ok=True)
        r = self._session.get(url, headers=self._headers(), timeout=300)
        if r.status_code >= 400:
            raise AigenError(f"Lightvisual: tải video hỏng HTTP {r.status_code}")
        tho = dich.with_name(dich.stem + ".lv-tho" + dich.suffix)
        tho.write_bytes(r.content)
        ff = _ffmpeg()
        # Bỏ ảnh bìa mjpeg: chép đúng một luồng hình + tiếng, không encode. Hỏng / không có
        # ffmpeg thì giữ file gốc — bước phụ không được làm mất clip đã trả tiền.
        if ff and subprocess.run([ff, "-v", "error", "-y", "-i", str(tho), "-map", "0:V:0", "-map", "0:a?",
                                  "-c", "copy", "-movflags", "+faststart", str(dich)],
                                 capture_output=True).returncode == 0 and dich.stat().st_size > 0:
            tho.unlink(missing_ok=True)
        else:
            tho.replace(dich)
        return dich

    def ds_model(self) -> list[dict]:
        """Model VIDEO đang mở (catalog công khai), cùng hình dạng SeedvisClient.ds_model."""
        d = self._goi("GET", "/catalog")
        return [{"id": m.get("canonical_id"), "label": m.get("display_name"), "type": "video",
                 "status": "active" if (m.get("maintenance") or "operational") == "operational" else "maintenance"}
                for m in d.get("data") or [] if (m.get("capabilities") or {}).get("video")]
