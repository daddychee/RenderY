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


_LENH_TAI_SAN = """Bạn là trợ lý dựng storyboard. Dưới đây là danh sách CẢNH \
của một video (mỗi dòng một cảnh).

Hãy liệt kê MỌI nhân vật, đạo cụ và bối cảnh xuất hiện trong các cảnh đó.

Luật:
- Chỉ liệt kê thứ THỰC SỰ có trong các cảnh. Không bịa thêm.
- Gộp các cách gọi khác nhau của cùng một thứ làm MỘT mục.
- `loai` chỉ nhận: nhan_vat | dao_cu | boi_canh
- `ten`: tiếng Việt, ngắn, đúng cách đội gọi trong cảnh.
- `chu`: mô tả nhận dạng bằng TIẾNG ANH, ngắn gọn, nêu đặc điểm giữ cho ảnh \
nhất quán (chất liệu, màu, niên đại, dáng). Đây là đoạn sẽ được đính vào MỌI \
prompt cảnh dùng nó.
- `pr`: prompt TIẾNG ANH để sinh ảnh tham chiếu, dùng một lần. Với nhân vật: \
toàn thân, 3 góc (chính diện, bên hông, sau lưng), nền trắng, photorealistic, \
đúng niên đại. Với đạo cụ/bối cảnh: một khung hình sạch, photorealistic.

Trả về JSON: {"tai_san": [{"loai": "...", "ten": "...", "chu": "...", "pr": "..."}]}"""


# Ngữ pháp cỡ cảnh và luật chống sai nghĩa lấy từ `director/prompts.py` — bộ
# đạo diễn của padoma đã chạy thật, không viết lại từ đầu.
_LENH_KY_THUAT = """Bạn là đạo diễn hình cho kênh video tư liệu (stock/AI footage + voice over).

Bạn nhận một loạt CẢNH. Mỗi cảnh có: lời đọc của phân cảnh (voice), mô tả cảnh \
bằng tiếng Việt do biên kịch viết, và vị trí của nó trong phân cảnh.

Với MỖI cảnh, trả về:
- `pa`: prompt TIẾNG ANH tả khung hình tĩnh của cảnh đó. Tả cái NHÌN THẤY: chủ \
thể, hành động, bối cảnh, ánh sáng, chất liệu. KHÔNG thêm câu về phong cách hay \
mood — phần đó hệ thống tự ghép.
- `pv`: prompt TIẾNG ANH tả CHUYỂN ĐỘNG cho một clip liền mạch 5 giây, không \
chuyển cảnh. Chuyển động ĐƠN GIẢN thôi.
- `co`: cỡ cảnh, chỉ nhận WS | MS | CU | ECU | AERIAL
- `goc`: góc máy, tiếng Anh ngắn (eye level, low angle, top down…)
- `cd`: chuyển động camera, tiếng Anh ngắn (static, slow push in, pan left…)
- `sfx`: gợi ý tiếng động, tiếng Anh ngắn
- `ts`: danh sách MÃ tài sản xuất hiện trong cảnh, lấy từ sổ được đưa bên dưới. \
Không có thì để danh sách rỗng. TUYỆT ĐỐI không bịa mã.

Luật:
- Cỡ cảnh: wide mở đầu/tả bối cảnh · medium kể chuyện · close-up nhấn cảm xúc. \
KHÔNG cho 3 cảnh liền nhau cùng một cỡ.
- Lời đọc mang ẩn dụ thì ĐỪNG quay chữ bề mặt của ẩn dụ — bám chủ thể thật của \
câu chuyện. Đây là lỗi sai nghĩa nặng nhất.
- Trả ĐÚNG số mục, ĐÚNG thứ tự như nhận vào. Không gộp, không bỏ.

Trả về JSON: {"canh": [{"id": "...", "pa": "...", "pv": "...", "co": "...", \
"goc": "...", "cd": "...", "sfx": "...", "ts": []}]}"""


class DichLoi(RuntimeError):
    """Không dịch được — cột tiếng Anh giữ nguyên, người dùng bấm lại sau."""


def doc_ket_viec(viec: str = VIEC) -> dict:
    """{key, model, base_url} mà Owner đã cấp cho việc `dich` của app NÀY.

    Hỏi thẳng két bằng SLUG CỦA CHÍNH MÌNH, không đi nhờ `web/ket_v3` của RenderY:
    module đó ghi cứng `SLUG = "rendery"` nên cấp phát của Treatment không bao giờ
    thấy (đo 23/09: cấp phát đúng rồi mà app vẫn báo "chưa cấp").

    Chưa cấp / gateway chết -> {} và người dùng nhận câu lỗi chỉ thẳng chỗ bấm.
    Không nuốt: đây là cột phụ, hỏng thì chỉ mất bản dịch.
    """
    import os

    import requests

    goc = os.getenv("TREATMENT_GATEWAY", "http://127.0.0.1:9000")
    tnb = os.getenv("OUTLIERY_TOKEN_NOI_BO", "").strip()
    try:
        r = requests.get(f"{goc}/api/cau-hinh/api-khoa/{SLUG}",
                         headers={"X-Noi-Bo": tnb} if tnb else {}, timeout=5)
        if r.status_code != 200:
            return {}
        muc = r.json().get(viec) or {}
    except Exception:  # noqa: BLE001 — gateway chết thì vẫn phải mở được bàn
        return {}
    ds = muc.get("khoa") or []
    if not ds:
        return {}
    return {"key": ds[0].get("key", ""), "base_url": ds[0].get("base_url", ""),
            "model": muc.get("model", "")}


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

    def ky_thuat(self, muc: list[dict], tai_san: list[dict]) -> list[dict]:
        """Một lô cảnh -> cột kỹ thuật + prompt tiếng Anh. Kiểm SỐ LƯỢNG trước
        khi trả: lệch một mục là lệch hết phần còn lại của chương."""
        so = "\n".join("- %s (%s): %s" % (t["ma"], t["ten"], t.get("chu", ""))
                        for t in tai_san) or "(sổ tài sản trống)"
        than = "SỔ TÀI SẢN:\n" + so + "\n\nCÁC CẢNH:\n" + json.dumps(
            muc, ensure_ascii=False, indent=1)
        # KHÔNG chốt số lượng ở đây: đo thật 24/09 trên C1, claude-sonnet-5 gửi 8
        # trả 7 — chốt số lượng thì cả chương dừng vì một mục bị nuốt. Tầng app
        # khớp theo MÃ, mục nào thiếu thì cảnh đó để trống, bấm lại chạy tiếp.
        ra = self.goi(_LENH_KY_THUAT, than).get("canh") or []
        return [x for x in ra if isinstance(x, dict)]

    def goi_y(self, canh: list[str]) -> list[dict]:
        """Một lô cảnh -> danh sách tài sản. Trả sai hình dạng thì bỏ mục đó,
        không giết cả lượt: mất một mục còn hơn mất cả bảng đề xuất."""
        than = "\n".join("- " + c for c in canh)
        ra = self.goi(_LENH_TAI_SAN, than).get("tai_san") or []
        return [x for x in ra if isinstance(x, dict) and (x.get("ten") or "").strip()]

    def dich(self, cau: list[str]) -> list[str]:
        than = "\n".join(f"[{i}] {c}" for i, c in enumerate(cau))
        ra = self.goi(_CAU_LENH, than).get("dong") or []
        if len(ra) != len(cau):
            raise DichLoi(f"{self.model} trả {len(ra)} dòng trong khi gửi {len(cau)} "
                          "— hai cột sẽ lệch hàng.")
        return [str(x) for x in ra]
