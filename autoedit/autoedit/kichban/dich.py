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


class DichLoi(RuntimeError):
    """Không dịch được — cột tiếng Anh giữ nguyên, người dùng bấm lại sau."""


class DichGLM:
    """Bộ dịch thật (GLM). Tiêm được nên test không chạm mạng.

    Không dùng `director.glm_client` để `kichban` khỏi kéo cả tầng dựng vào —
    đường gọi là một lượt HTTP, chép 20 dòng rẻ hơn là buộc hai tầng vào nhau.
    """

    def __init__(self, url: str | None = None, key: str | None = None,
                 model: str = "glm-5.3") -> None:
        import os
        self.url = url or os.getenv("GLM_API_URL",
                                    "https://api.z.ai/api/paas/v4/chat/completions")
        self.key = key or os.getenv("GLM_API_KEY", "")
        self.model = model

    def dich(self, cau: list[str]) -> list[str]:
        import urllib.error
        import urllib.request

        if not self.key:
            raise DichLoi("Thiếu GLM_API_KEY — chưa dịch được.")
        than = "\n".join(f"[{i}] {c}" for i, c in enumerate(cau))
        goi = json.dumps({
            "model": self.model,
            "reasoning_effort": "low",
            "messages": [{"role": "system", "content": _CAU_LENH},
                         {"role": "user", "content": than}],
        }).encode("utf-8")
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
