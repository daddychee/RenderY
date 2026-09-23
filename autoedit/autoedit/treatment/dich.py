r"""Dịch cột tiếng Việt — CHỈ để đội đọc hiểu, không đi xuống dây chuyền dựng.

Bản tiếng Anh mới là kịch bản thật (đem đi ren voice, đem đi align). Bản dịch là
cột phụ, nên ở đây fail thì báo lỗi rồi thôi — tuyệt đối không được đụng vào cột
tiếng Anh (test `test_dich_hong_thi_khong_mat_chu` khoá điều đó).

KHOÁ LẤY TỪ KÉT CỦA GENERAL, app KHÔNG giữ sổ khoá riêng (user chốt 23/09, luật
`docs/APPS.md` bước 5): Owner nhập khoá ở **General › API Keys**, cấp cho việc
`dich` của app `treatment`, chọn nhà cung cấp + model ở đó. Két trả kèm cả
`base_url` (đường A, 23/09) nên đổi nhà (glm → grok → mwapi/Claude) là app gọi
đúng địa chỉ mới, không phải sửa một dòng code nào.

Dịch THEO DÒNG, giữ đúng số dòng: hai cột phải nằm ngang hàng thì chỉ vào dòng
nào mới ra đúng nguồn/treatment của dòng đó. LLM trả thiếu/thừa dòng là hỏng cả
màn hình, nên kiểm số lượng trước khi trả.
"""

from __future__ import annotations

import json

SLUG = "treatment"
VIEC = "dich"

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36")

_CAU_LENH = """Bạn dịch kịch bản video sang tiếng Việt cho ĐỘI DỰNG ĐỌC HIỂU.

Luật:
- Dịch TỪNG DÒNG, giữ ĐÚNG số dòng và ĐÚNG thứ tự. Không gộp, không tách, không bỏ.
- Văn nói tự nhiên, giữ nguyên con số / đơn vị / tên riêng / tên nghiên cứu.
- Không thêm lời bình, không thêm chú thích.

Trả về JSON: {"dong": ["bản dịch dòng 1", "bản dịch dòng 2", ...]}"""


class DichLoi(RuntimeError):
    """Không dịch được — cột tiếng Anh giữ nguyên, người dùng bấm lại sau."""


def doc_ket_viec() -> dict:
    """{key, model, base_url} mà Owner đã cấp cho việc `dich` của app này.

    Chưa cấp / gateway chết -> {} và người dùng nhận câu lỗi chỉ thẳng chỗ bấm.
    Đây là ngoại lệ DUY NHẤT của luật cách ly: `web/ket_v3` chỉ gọi HTTP tới
    gateway, không kéo theo tầng dựng nào.
    """
    try:
        from autoedit.web.ket_v3 import doc_ket
    except ImportError:
        return {}
    try:
        ds = (doc_ket().get(VIEC) or {}).get("khoa") or []
    except Exception:  # noqa: BLE001 — gateway chết thì vẫn phải mở được bàn
        return {}
    if not ds:
        return {}
    k = ds[0]
    return {"key": k.get("key", ""), "base_url": k.get("base_url", ""),
            "model": (doc_ket().get(VIEC) or {}).get("model", "")}


def dia_chi_chat(url: str) -> str:
    """Địa chỉ gốc của nhà -> endpoint chat kiểu OpenAI.

    Két trả gốc (`https://api.mwapi.dev/v1`); ai đã dán sẵn đường đầy đủ thì giữ.
    """
    u = (url or "").strip().rstrip("/")
    if not u:
        return ""
    if u.endswith("/chat/completions"):
        return u
    return u + "/chat/completions"


def than_goi(model: str, he: str, than: str) -> dict:
    """Thân request kiểu OpenAI, kèm tham số RIÊNG của từng nhà.

    `reasoning_effort` là của GLM và với GLM là BẮT BUỘC (không đặt thì nó nuốt
    trọn max_tokens vào phần suy nghĩ rồi trả JSON cụt — bài học ghi trong
    `director/glm_client.py`). Cổng khác thì trả 400, nên chỉ gửi khi là glm.
    """
    d = {"model": model,
         "messages": [{"role": "system", "content": he},
                      {"role": "user", "content": than}]}
    if model.lower().startswith("glm"):
        d["reasoning_effort"] = "low"
    return d


class LLM:
    """Một lượt gọi LLM kiểu OpenAI, cấu hình lấy từ két mỗi lần khởi tạo."""

    def __init__(self) -> None:
        cd = doc_ket_viec() or {}
        self.key = cd.get("key", "")
        self.model = cd.get("model") or "claude-sonnet-5"
        self.url = dia_chi_chat(cd.get("base_url", ""))

    def goi(self, he: str, than: str) -> dict:
        """Đi bằng `requests`, KHÔNG phải urllib. Đo 16/09 trên máy chủ này:
        cùng khoá cùng thân, `requests` -> 200, urllib -> 403 `error code 1010`
        (Cloudflare chặn User-Agent của urllib). Trước đó máy còn chết
        `CERTIFICATE_VERIFY_FAILED` vì nằm sau lớp chặn TLS."""
        import requests

        if not self.key or not self.url:
            raise DichLoi("Chưa có khoá cho việc dịch — Owner cấp ở "
                          "General › API Keys › tab Theo app › Treatment.")
        try:
            r = requests.post(self.url, timeout=180,
                              json=than_goi(self.model, he, than),
                              headers={"Authorization": f"Bearer {self.key}",
                                       "Content-Type": "application/json",
                                       "User-Agent": _UA})
        except Exception as exc:  # noqa: BLE001
            raise DichLoi(f"Gọi {self.model} hỏng: {exc}") from exc
        if r.status_code != 200:
            raise DichLoi(f"Gọi {self.model} hỏng: HTTP {r.status_code} — {r.text[:160]}")
        try:
            noi = r.json()["choices"][0]["message"]["content"]
            return json.loads(noi[noi.index("{"):noi.rindex("}") + 1])
        except (KeyError, IndexError, ValueError) as exc:
            raise DichLoi(f"{self.model} trả về không đọc được: {exc}") from exc

    def dich(self, cau: list[str]) -> list[str]:
        than = "\n".join(f"[{i}] {c}" for i, c in enumerate(cau))
        ra = self.goi(_CAU_LENH, than).get("dong") or []
        if len(ra) != len(cau):
            raise DichLoi(f"{self.model} trả {len(ra)} dòng trong khi gửi {len(cau)} "
                          "— hai cột sẽ lệch hàng.")
        return [str(x) for x in ra]
