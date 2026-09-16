r"""Dịch cột tiếng Việt — CHỈ để team đọc hiểu, không đi xuống dây chuyền dựng.

Bản tiếng Anh mới là kịch bản thật (đem đi ren voice, đem đi align). Bản dịch là
cột phụ, nên ở đây fail thì báo lỗi rồi thôi — tuyệt đối không được đụng vào cột
tiếng Anh (test `test_dich_hong_thi_khong_mat_chu` khoá điều đó).

Dịch THEO DÒNG, giữ đúng số dòng: hai cột phải nằm ngang hàng nhau thì mới chỉ
vào dòng nào ra citation dòng đó. LLM trả thiếu/thừa dòng là hỏng cả màn hình,
nên `DichGLM` kiểm số lượng trước khi trả.
"""

from __future__ import annotations

import json

_CAU_LENH = """Bạn dịch kịch bản video sang tiếng Việt cho ĐỘI DỰNG ĐỌC HIỂU.

Luật:
- Dịch TỪNG DÒNG, giữ ĐÚNG số dòng và ĐÚNG thứ tự. Không gộp, không tách, không bỏ.
- Văn nói tự nhiên, giữ nguyên con số / đơn vị / tên riêng / tên nghiên cứu.
- Không thêm lời bình, không thêm chú thích.

Trả về JSON: {"dong": ["bản dịch dòng 1", "bản dịch dòng 2", ...]}"""


def than_goi(model: str, he: str, than: str) -> dict:
    """Thân request kiểu OpenAI, kèm tham số RIÊNG của từng nhà.

    `reasoning_effort` là của GLM và với GLM là BẮT BUỘC (không đặt thì nó nuốt
    trọn max_tokens vào phần suy nghĩ rồi trả JSON cụt — bài học đã ghi trong
    `director/glm_client.py`). Nhưng gửi sang cổng trung gian chạy grok/gpt thì
    nhiều cổng trả 400. Nên chỉ gửi khi model là glm.
    """
    d = {"model": model,
         "messages": [{"role": "system", "content": he},
                      {"role": "user", "content": than}]}
    if model.lower().startswith("glm"):
        d["reasoning_effort"] = "low"
    return d


class DichLoi(RuntimeError):
    """Không dịch được — cột tiếng Anh giữ nguyên, người dùng bấm lại sau."""


def _khoa_tu_ket() -> tuple[str, str]:
    """(khoá, model) GLM từ két OUTLIERY — MỘT CỬA KHOÁ của cụm.

    Luật `docs/APPS.md` bước 5: khoá do Owner nhập ở **General › API Keys**, app
    hỏi qua loopback; app KHÔNG giữ sổ khoá riêng, KHÔNG đọc `.env`. Bàn kịch bản
    dùng lại đúng cấp phát của RenderY (việc `cham_footage`, nhà glm) vì nó LÀ
    công cụ của RenderY — chép khoá sang chỗ khác là đẻ ra sổ thứ hai, đổi khoá
    một nơi thì nơi kia chết lặng.

    Đây là ngoại lệ DUY NHẤT của luật cách ly (test `test_khong_dinh_gi_toi_day
    _chuyen_dung`): `web/ket_v3` chỉ gọi HTTP, không kéo theo tầng dựng nào.
    """
    # Import ĐÚNG module con (không `from autoedit.web import ket_v3`) để test
    # cách ly còn soi được tên đầy đủ — nó chặn theo tiền tố chuỗi.
    from autoedit.web.ket_v3 import khoa_cua_viec

    return khoa_cua_viec("cham_footage")


def dia_chi_chat(url: str) -> str:
    """Địa chỉ gốc -> endpoint chat kiểu OpenAI.

    User đưa `https://api2.apisuper.cloud` — đó là GỐC. Tự nối đuôi thay vì bắt
    người dùng nhớ `/v1/chat/completions`; ai dán sẵn đường đầy đủ thì giữ nguyên.
    """
    u = (url or "").strip().rstrip("/")
    if not u:
        return ""
    if u.endswith("/chat/completions"):
        return u
    if u.endswith("/v1") or u.endswith("/v4"):
        return u + "/chat/completions"
    return u + "/v1/chat/completions"


class DichGLM:
    """Một lượt gọi LLM kiểu OpenAI. Tiêm được nên test không chạm mạng.

    Không dùng `director.glm_client` để `kichban` khỏi kéo cả tầng dựng vào —
    đường gọi là một lượt HTTP, chép 20 dòng rẻ hơn là buộc hai tầng vào nhau.

    THỨ TỰ LẤY CẤU HÌNH: cài đặt trong app -> két OUTLIERY -> biến môi trường.
    Tab cài đặt là đường TẠM (user chốt 16/09, cuối tuần ghép vào két); bỏ trống
    ô đó là tự rơi về két, không phải sửa code.
    """

    def __init__(self, url: str | None = None, key: str | None = None,
                 model: str = "", cai_dat: dict | None = None,
                 viec: str = "kiem") -> None:
        import os

        cd = cai_dat or {}
        # ĐỊA CHỈ VÀ KHOÁ ĐI CÙNG MỘT NGUỒN. Đo 16/09: khai địa chỉ nhà cung cấp
        # mới mà chưa dán khoá thì nó mượn khoá GLM của két gửi sang cổng đó ->
        # `403 Forbidden`, người dùng tưởng cổng hỏng. Đã khai địa chỉ riêng thì
        # thiếu khoá phải báo thẳng "chưa có khoá".
        rieng = bool(cd.get("llm_url") or cd.get("llm_key"))
        khoa_ket, model_ket = "", ""
        if not (key or cd.get("llm_key") or rieng):
            try:
                khoa_ket, model_ket = _khoa_tu_ket()
            except Exception:  # noqa: BLE001 — gateway chết thì vẫn phải mở được bàn
                pass
        # Dịch chạy nhiều lần và rẻ; kiểm chứng cần model khoẻ -> hai ô riêng,
        # để trống ô dịch thì dùng chung model kiểm.
        model_app = (cd.get("dich_model") if viec == "dich" else "") or cd.get("llm_model")

        self.url = (dia_chi_chat(url or cd.get("llm_url", "")) or
                    os.getenv("GLM_API_URL",
                              "https://api.z.ai/api/paas/v4/chat/completions"))
        self.key = (key or cd.get("llm_key") or
                    ("" if rieng else (khoa_ket or os.getenv("GLM_API_KEY", ""))))
        self.model = model or model_app or model_ket or "glm-5.3"

    def dich(self, cau: list[str]) -> list[str]:
        import urllib.error
        import urllib.request

        if not self.key:
            raise DichLoi("Thiếu GLM_API_KEY — chưa dịch được.")
        than = "\n".join(f"[{i}] {c}" for i, c in enumerate(cau))
        goi = json.dumps(than_goi(self.model, _CAU_LENH, than)).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=goi,
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                kq = json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise DichLoi(f"Gọi GLM hỏng: {exc}") from exc

        try:
            noi = kq["choices"][0]["message"]["content"]
            ra = json.loads(noi[noi.index("{"):noi.rindex("}") + 1])["dong"]
        except (KeyError, IndexError, ValueError) as exc:
            raise DichLoi(f"GLM trả về không đọc được: {exc}") from exc

        if len(ra) != len(cau):
            raise DichLoi(
                f"GLM trả {len(ra)} dòng trong khi gửi {len(cau)} — hai cột sẽ lệch hàng.")
        return [str(x) for x in ra]
