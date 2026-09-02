"""GLM làm đạo diễn chia beat — chốt hai điều BẮT BUỘC đã tìm ra bằng đo thật.

Đo 30/08/2026 trên đúng prompt ChapterBeats của job LI093 (6090 token vào):
  claude -p ~120s/lần · GLM-5.3 7.8s/lần, 5/5 hợp lệ.
Bỏ một trong hai điều dưới là hỏng ngay, nên test canh cả hai.
"""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from autoedit.director.glm_client import GLMDirectorClient


class Beat(BaseModel):
    id: int
    text: str


class KetQua(BaseModel):
    beats: list[Beat]


def _client(monkeypatch, tra_ve, ghi=None):
    """GLMDirectorClient với _goi bị thay — không chạm mạng."""
    c = GLMDirectorClient(api_key="k", model="glm-5.3")

    def gia_goi(messages):
        if ghi is not None:
            ghi["messages"] = messages
        return tra_ve

    monkeypatch.setattr(c, "_goi", gia_goi)
    return c


def _dap(noi_dung, **u):
    return {"choices": [{"message": {"content": noi_dung}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": u.get("i", 10), "completion_tokens": u.get("o", 5)}}


def test_thieu_khoa_bao_loi_ro_rang(monkeypatch):
    for b in ("GLM_API_KEY", "LLM_API_KEY"):
        monkeypatch.delenv(b, raising=False)
    with pytest.raises(RuntimeError, match="Thiếu khoá GLM"):
        GLMDirectorClient()


def test_doc_khoa_tu_env(monkeypatch):
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "tu-ket")
    assert GLMDirectorClient()._key == "tu-ket"


def test_reasoning_effort_low_luon_duoc_gui(monkeypatch):
    """GLM-5.3 LUÔN bật thinking; không tắt thì nó nuốt trọn max_tokens vào phần
    suy nghĩ -> 88s và JSON CỤT. `reasoning_effort` là cách DUY NHẤT tắt được
    (API từ chối thinking={"type":"disabled"} lẫn low/high/max mà nó tự gợi ý)."""
    body = {}
    c = GLMDirectorClient(api_key="k")

    def gia_urlopen(req, timeout=None):
        body.update(json.loads(req.data.decode("utf-8")))
        raise RuntimeError("dung o day")

    monkeypatch.setattr("urllib.request.urlopen", gia_urlopen)
    with pytest.raises(RuntimeError):
        c._goi([{"role": "user", "content": "x"}])
    assert body["reasoning_effort"] == "low"
    assert body["temperature"] == 0


def test_schema_duoc_nhoi_vao_prompt(monkeypatch):
    """GLM NHẬN response_format=json_schema nhưng KHÔNG ép theo — đo 10 lần đều
    0/10 hợp lệ (thiếu energy/visual_level/search_queries). Dán schema vào prompt: 5/5."""
    ghi = {}
    c = _client(monkeypatch, _dap('{"beats":[{"id":1,"text":"a"}]}'), ghi)
    c.complete("luật đạo diễn", "chia chương 1", KetQua)
    system = ghi["messages"][0]["content"]
    assert "luật đạo diễn" in system
    assert '"beats"' in system and "properties" in system   # schema thật, không phải mô tả suông


def test_go_rao_markdown(monkeypatch):
    """GLM hay bọc ```json — _clean_json phải gỡ trước khi validate."""
    c = _client(monkeypatch, _dap('```json\n{"beats":[{"id":2,"text":"b"}]}\n```'))
    kq, _ = c.complete("s", "u", KetQua)
    assert kq.beats[0].id == 2


def test_context_dat_truoc_user(monkeypatch):
    ghi = {}
    c = _client(monkeypatch, _dap('{"beats":[]}'), ghi)
    c.complete("s", "phần chương", KetQua, context="TOÀN VĂN SCRIPT")
    user = ghi["messages"][1]["content"]
    assert user.index("TOÀN VĂN SCRIPT") < user.index("phần chương")


def test_noi_dung_rong_bao_loi_ro(monkeypatch):
    """Trả rỗng là có thật (đo được) — phải báo rõ chứ không vỡ bằng JSONDecodeError."""
    c = _client(monkeypatch, _dap("   "))
    with pytest.raises(ValueError, match="RỖNG"):
        c.complete("s", "u", KetQua)


def test_json_sai_schema_bao_ro_ten_model(monkeypatch):
    c = _client(monkeypatch, _dap('{"khong_phai_beats": 1}'))
    with pytest.raises(ValueError, match="KetQua"):
        c.complete("s", "u", KetQua)


def test_usage_lay_dung_tu_glm(monkeypatch):
    c = _client(monkeypatch, _dap('{"beats":[]}', i=6090, o=781))
    _, usage = c.complete("s", "u", KetQua)
    assert usage.input_tokens == 6090 and usage.output_tokens == 781


def test_log_ghi_ra_file(monkeypatch, tmp_path):
    c = GLMDirectorClient(api_key="k", log_dir=tmp_path)
    monkeypatch.setattr(c, "_goi", lambda m: _dap('{"beats":[{"id":9,"text":"z"}]}'))
    c.complete("s", "u", KetQua)
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    d = json.loads(files[0].read_text(encoding="utf-8"))
    assert d["engine"] == "glm" and d["response"]["beats"][0]["id"] == 9


def test_khong_thu_lai_khi_loi_4xx(monkeypatch):
    """400 = yêu cầu sai, thử lại cũng vậy — chỉ tổ chậm."""
    import urllib.error

    lan = {"n": 0}

    def gia_urlopen(req, timeout=None):
        lan["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 400, "Bad", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", gia_urlopen)
    c = GLMDirectorClient(api_key="k", retries=3)
    with pytest.raises(RuntimeError, match="HTTP 400"):
        c._goi([{"role": "user", "content": "x"}])
    assert lan["n"] == 1


def test_co_thu_lai_khi_loi_mang(monkeypatch):
    lan = {"n": 0}

    def gia_urlopen(req, timeout=None):
        lan["n"] += 1
        raise OSError("mạng chập chờn")

    monkeypatch.setattr("urllib.request.urlopen", gia_urlopen)
    monkeypatch.setattr("time.sleep", lambda s: None)
    c = GLMDirectorClient(api_key="k", retries=3)
    with pytest.raises(RuntimeError, match="sau 3 lần"):
        c._goi([{"role": "user", "content": "x"}])
    assert lan["n"] == 3


def test_bao_dung_gia_glm_khong_lay_gia_claude(monkeypatch):
    """Usage.usd phải theo giá GLM. 30/08: hook chạy GLM hết $0.046 mà log ghi
    $0.2488 vì Usage hard-code giá Claude — sai gần 6 lần, dự trù chi phí đi tong."""
    from autoedit.director.glm_client import PRICE_INPUT_PER_M, PRICE_OUTPUT_PER_M

    c = _client(monkeypatch, _dap('{"beats":[]}', i=1_000_000, o=1_000_000))
    _, usage = c.complete("s", "u", KetQua)
    assert usage.usd == pytest.approx(PRICE_INPUT_PER_M + PRICE_OUTPUT_PER_M)
    assert usage.usd < 3.0        # giá Claude cho cùng lượng token là $18


def test_glm_client_du_giao_dien_cho_stage_rank():
    """Stage rank (phễu c5) bọc brain trong _TimedBrain — chỉ cần .complete() và
    .model. 31/08: két ghi RANK_MODEL nhưng không nơi nào đọc, nên cấu hình
    'cham_footage = glm-5.3' bị bỏ qua và rank vẫn chạy Claude Code."""
    c = GLMDirectorClient(api_key="k", model="glm-5.3")
    assert callable(getattr(c, "complete", None))
    assert c.model == "glm-5.3"

    import inspect
    sig = inspect.signature(c.complete)
    assert list(sig.parameters) == ["system", "user", "output_model", "context"]


def test_rank_doc_RANK_MODEL_tu_ket(monkeypatch):
    """Rào chặn: RANK_MODEL phải được ĐỌC ở cli.py, không chỉ được két GHI ra."""
    import inspect

    from autoedit import cli

    src = inspect.getsource(cli.source.__wrapped__)
    assert 'RANK_MODEL' in src, "stage source không đọc RANK_MODEL — cấu hình két bị bỏ qua"


def test_rank_model_khong_gui_ten_claude_sang_glm():
    """02/09: --rank-model mặc định cứng 'claude-sonnet-4-6' CHE cấu hình két
    (RANK_MODEL=glm-5.3) -> gửi tên model Claude sang endpoint GLM, HTTP 400
    'modelCode: does not exist' giết stage source sau 3 phút."""
    import inspect

    from autoedit import cli

    src = inspect.getsource(cli.source.__wrapped__)
    # mặc định phải TRỐNG để két quyết
    sig = inspect.signature(cli.source.__wrapped__)
    mac_dinh = sig.parameters["rank_model"].default
    assert getattr(mac_dinh, "default", mac_dinh) == "", \
        "rank_model phải mặc định rỗng — đặt cứng là che cấu hình két"
    # và tên model phải hợp nhà cung cấp
    assert 'startswith("glm")' in src


# ------------- GLM chèn phần tử rác vào danh sách (đo thật 02/09) -------------
def test_don_phan_tu_rac_trong_danh_sach(monkeypatch):
    """GLM trả `verdicts[7] = ''` giữa các object hợp lệ -> giết cả lượt chấm 20
    beat. Lỗi HÌNH THỨC: dọn rồi validate lại còn hơn vứt 19 phán quyết đúng."""
    c = _client(monkeypatch, _dap('{"beats":[{"id":1,"text":"a"},"",null,'
                                  '{"id":2,"text":"b"}]}'))
    kq, _ = c.complete("s", "u", KetQua)
    assert [b.id for b in kq.beats] == [1, 2]


def test_khong_dung_toi_du_lieu_that():
    """Chỉ bỏ phần tử VÔ NGHĨA trong LIST — chuỗi rỗng là GIÁ TRỊ của trường thì giữ,
    nếu không là che mất lỗi nội dung thật."""
    from autoedit.director.glm_client import _don_rac

    x = {"verdicts": [{"alias": "a", "note": ""}], "tong": 0, "ten": ""}
    assert _don_rac(x) == x


def test_json_sai_that_van_bao_loi(monkeypatch):
    """Dọn rác KHÔNG được nuốt lỗi thật: thiếu trường bắt buộc vẫn phải nổ."""
    c = _client(monkeypatch, _dap('{"khong_phai_beats": 1}'))
    with pytest.raises(ValueError, match="KetQua"):
        c.complete("s", "u", KetQua)
