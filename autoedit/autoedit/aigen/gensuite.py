"""Gensuite — video MUSE qua REST (user 30/10: người dựng chọn nhà khi bấm gen video). Cùng hình
dạng với LightvisualClient phần video (`gen_video_i2v`, `gen_video_ref`, `trang_thai_video`,
`tai_video`) để `_VeVideo` đổi nhà mà nơi gọi giữ nguyên.

Đo thật 30/10 (người giao việc):
  * Muse KHÔNG có khung đầu: chỉ nhận 1–3 ảnh tham chiếu data URL, mỗi ảnh ≤ 8 MB. Gửi một ảnh
    shot làm ảnh tham chiếu DUY NHẤT thì khung 0 gần y ảnh đó -> đường i2v = ảnh đó làm ref duy nhất.
  * Luôn 10 s: 20/30/60 s là nhiều khúc 10 s nối cứng, trôi mặt, trôi phòng.
  * Gửi hai video sát nhau -> 429 RATE_LIMITED kèm `retryAfterSeconds`: chưa tạo job, đợi rồi gửi lại.
  * KHÔNG có lệnh liệt kê job: mất id là mất video. Nên POST lỗi khác 429 không tự gửi lại (job có
    thể đã tạo), và id về kho ngay khi gửi xong (route đã làm vậy).
  * `downloadUrl` là link tạm ở fbcdn, tải không cần khoá — và KHÔNG được gửi khoá sang đó.
Mã task app giữ = `TIEN_TO_TASK` + uuid của họ — `_VeVideo` nhận nhà theo tiền tố đó.
"""

from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Optional

import requests

from autoedit.aigen.client import AigenError
from autoedit.aigen.seedvis import _mime
from autoedit.httpx_ma import nen_thu_lai

BASE_MAC_DINH = "https://supabase-staging.gensuite.site/functions/v1/api-v1"
TIEN_TO_TASK = "gs_"
GIAY = 10
PROMPT_TOI_DA = 5000
ANH_TOI_DA = 3
ANH_TOI_DA_BYTE = 8 * 1024 * 1024       # tính trên chuỗi data URL gửi đi (cách hiểu chặt hơn)
_UA = "RenderY-treatment/1.0"


def _data_url(p: Path) -> str:
    """Nguyên file (PNG như ảnh shot), đúng dạng đã đo thật; quá trần thì báo, không tự nén."""
    p = Path(p)
    s = f"data:{_mime(p)};base64," + base64.b64encode(p.read_bytes()).decode()
    if len(s) > ANH_TOI_DA_BYTE:
        raise AigenError(f"Ảnh {p.name} gửi đi {len(s) / 1048576:.1f} MB — Gensuite nhận tối đa 8 MB mỗi ảnh.")
    return s


class GensuiteClient:
    GIAY = GIAY

    def __init__(self, api_key: Optional[str], base_url: str = BASE_MAC_DINH,
                 timeout: int = 180, retries: int = 4) -> None:
        if not api_key:
            raise AigenError("Chưa có khoá Gensuite — Owner cấp ở General › API Keys › "
                             "Theo app › Treatment › gen_video.")
        self._key = api_key
        self.base = (base_url or BASE_MAC_DINH).rstrip("/")
        self.timeout, self.retries = timeout, retries
        self.giay = self.GIAY
        self._session = requests.Session()     # test thay bằng phiên giả

    def _goi(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """Sổ gọi nền như hai nhà kia: một dòng sổ = một lượt việc, sổ chết không hỏng việc."""
        from autoedit import so_goi_nen

        t0 = time.time()
        try:
            r = self._goi_that(method, path, body)
        except Exception as e:  # noqa: BLE001 — ghi sổ rồi ném nguyên vẹn
            so_goi_nen.ghi("llm", duoi=self._key[-4:], ok=False, ma_loi=str(e)[:200],
                           viec="gen_video", ms=(time.time() - t0) * 1000)
            raise
        so_goi_nen.ghi("llm", duoi=self._key[-4:], ok=True, viec="gen_video",
                       ms=(time.time() - t0) * 1000)
        return r

    def _goi_that(self, method: str, path: str, body: Optional[dict]) -> dict:
        """POST: chỉ 429 gửi lại (chắc chắn chưa tạo job). GET: lỗi tạm thì hỏi lại, trừ 429 —
        trang tự hỏi lại sau 20 s, ngủ ở đây chỉ giữ luồng (như Lightvisual 30/10)."""
        gui = method == "POST"
        loi: Exception | None = None
        for lan in range(self.retries):
            try:
                r = self._session.request(method, self.base + path, json=body, timeout=self.timeout,
                                          headers={"Authorization": f"Bearer {self._key}", "User-Agent": _UA})
            except Exception as exc:  # noqa: BLE001 — mạng
                if gui:
                    raise AigenError(f"Gensuite: gửi video đứt mạng ({exc}) — job có thể đã tạo mà mất mã; "
                                     "xem trên web Gensuite trước khi gửi lại.") from exc
                loi = exc
                time.sleep(3 * (lan + 1))
                continue
            if r.status_code < 400:
                try:
                    return r.json()
                except ValueError as exc:
                    raise AigenError(f"Gensuite trả về không phải JSON: {r.text[:200]}") from exc
            loi = AigenError(f"Gensuite HTTP {r.status_code}: {r.text[:300]}"
                             + (" — hết credit, báo Owner nạp." if r.status_code == 402 else ""))
            loi.ma = r.status_code
            if (gui and r.status_code != 429) or (not gui and (r.status_code == 429 or not nen_thu_lai(r.status_code))):
                raise loi
            if lan + 1 < self.retries:
                try:
                    cho = float((r.json() or {}).get("retryAfterSeconds") or 0)
                except (ValueError, AttributeError):
                    cho = 0
                time.sleep(min(cho or float(r.headers.get("Retry-After") or 8 * (lan + 1)), 60))
        raise loi if isinstance(loi, AigenError) else AigenError(f"Gensuite: gọi hỏng sau {self.retries} lần ({loi})")

    def _nop(self, prompt: str, anh: "list[Path]", giay: int) -> str:
        if int(giay or 0) != GIAY:
            raise AigenError(f"Gensuite (Muse) chỉ dựng 10 giây — nhận {giay} giây: prompt phải ghép cho 10 giây.")
        if len(prompt) > PROMPT_TOI_DA:
            raise AigenError(f"Prompt dài {len(prompt):,} ký tự".replace(",", ".")
                             + " — Gensuite nhận tối đa 5.000. Rút gọn prompt rồi gửi lại.")
        if not 1 <= len(anh) <= ANH_TOI_DA:
            raise AigenError(f"Muse nhận 1–3 ảnh tham chiếu — lượt này {len(anh)} ảnh.")
        d = self._goi("POST", "/videos", {"videoModel": "muse", "prompt": prompt,
                                          "ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE", "durationSeconds": GIAY,
                                          "outputCount": 1, "referenceImageUrls": [_data_url(p) for p in anh]})
        tid = ((d.get("items") or [{}])[0] or {}).get("id")
        if not tid:
            raise AigenError(f"Gensuite: nộp video không trả id ({str(d)[:200]})")
        return TIEN_TO_TASK + str(tid)

    # ------------------------------------------------------------- video
    def gen_video_i2v(self, prompt: str, anh: Path, giay: int = GIAY, am: bool = True,
                      model: Optional[str] = None) -> str:
        """Ảnh khung đầu đã duyệt làm ảnh tham chiếu DUY NHẤT (đo 30/10: khung 0 gần y ảnh đó).
        `am`, `model` chỉ để cùng chữ ký: Gensuite chỉ có Muse, Muse tự ra tiếng."""
        _ = am, model
        return self._nop(prompt, [Path(anh)], giay)

    def gen_video_ref(self, prompt: str, anh: "list[Path]", giay: int = GIAY,
                      model: Optional[str] = None) -> str:
        """Clip dựng từ ảnh tham chiếu, Muse nhận 1–3 ảnh."""
        _ = model
        return self._nop(prompt, [Path(p) for p in anh], giay)

    def trang_thai_video(self, task_id: str) -> dict:
        """Một lần hỏi. Hình dạng như hai nhà kia: {status: succeeded|failed|cancelled|queued|processing,
        video_url, loi}."""
        ma = str(task_id)[len(TIEN_TO_TASK):] if str(task_id).startswith(TIEN_TO_TASK) else str(task_id)
        d = self._goi("GET", f"/videos/{ma}")
        tt = str(d.get("status") or "")
        if tt == "success":
            url = d.get("downloadUrl") or next((o.get("downloadUrl") for o in d.get("outputs") or []
                                                if o.get("downloadUrl")), "")
            if not url:      # trả `failed` là route quên mã -> mất video; lỗi thì mã còn, hỏi lại được
                raise AigenError(f"Gensuite: job {ma} xong mà chưa có downloadUrl — hỏi lại sau.")
            return {"status": "succeeded", "video_url": url}
        if tt in ("failed", "cancelled"):
            return {"status": tt, "loi": d.get("error") or d.get("providerMessage") or tt}
        return {"status": tt or "queued"}

    def tai_video(self, url: str, dich: Path) -> Path:
        """Link tạm fbcdn: tải ngay, KHÔNG kèm khoá (bên thứ ba)."""
        dich = Path(dich)
        dich.parent.mkdir(parents=True, exist_ok=True)
        r = self._session.get(url, headers={"User-Agent": _UA}, timeout=300)
        if r.status_code >= 400:
            raise AigenError(f"Gensuite: tải video hỏng HTTP {r.status_code}")
        dich.write_bytes(r.content)
        return dich
