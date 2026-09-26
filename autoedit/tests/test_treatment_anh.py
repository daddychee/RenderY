"""Treatment — ĐỢT 2: sinh ẢNH cho từng cảnh bằng Seedream, có CỔNG DUYỆT.

User chốt 24/09: "Làm tiếp giai đoạn 2 sinh ảnh và video bằng API seedance có
sẵn trong kho" · "ảnh lưu trong ổ F tạm thời".

Luật ghim từ `aigen/duyet.py` (đợt 2 của padoma, user chốt 03/09): **tiền video
chỉ đốt SAU cổng duyệt ảnh**. Ảnh rẻ (~$0,03/tấm), video đắt gấp năm (~$0,03/giây
× 5 giây). Sinh video cho một cảnh chưa ai nhìn là đốt tiền vào thứ sẽ bị bỏ.

File ảnh neo vào MÃ RIÊNG của cảnh (`canh[i].id`), không neo vào vị trí: chèn
một cảnh phía trên là mọi số thứ tự dịch hết.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class VeGia:
    """Thay Seedream: ghi thẳng ra file như client thật vẫn làm.

    Giữ lại cả `ref` — từ 26/09 ảnh tham chiếu của asset đi KÈM lượt vẽ, nên
    test phải soi được nó chứ không chỉ soi prompt.
    """

    def __init__(self, hong=False):
        self.goi = []
        self.ref = []
        self.hong = hong

    def gen_anh(self, prompt, dich, ref=None):
        self.goi.append(prompt)
        self.ref.append(list(ref or []))
        if self.hong:
            raise RuntimeError("ARK ngã")
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(PNG)
        return dich


def _bo(tmp_path, ve=None, canh=("Cận bàn tay", "Sonar nhấp nháy")):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    kho.luu_so("SE001", [{"ma": "nuoc", "loai": "tong", "ten": "dưới nước",
                          "chu": "underwater boilerplate"}])
    c = TestClient(tao_app(kho, ve_anh=ve or VeGia()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "Voice.", "vi": "", "het": 0,
         "canh": [{"t": t, "pa": "EN " + t, "tong": "nuoc"} for t in canh]}]})
    return c, kho


def _ma(kho, k=0):
    return kho.doc("SE001", "H")["dong"][0]["canh"][k]["id"]


def _canh(kho, k=0):
    return kho.doc("SE001", "H")["dong"][0]["canh"][k]


# ------------------------------------------------------------ sinh ảnh
def test_sinh_anh_cho_mot_canh(tmp_path):
    c, kho = _bo(tmp_path)
    r = c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert r.status_code == 200, r.text
    assert c.get(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh").content == PNG


def test_prompt_gui_di_la_prompt_DAY_DU(tmp_path):
    """Gửi đúng cái người dùng thấy trong hộp: nội dung EN + mô tả tài sản +
    đoạn tông. Gửi mỗi `pa` thì ảnh mất tông, khác hẳn bản họ duyệt."""
    ve = VeGia()
    c, kho = _bo(tmp_path, ve)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "EN Cận bàn tay" in ve.goi[0]
    assert "underwater boilerplate" in ve.goi[0]


def test_canh_chua_co_prompt_EN_thi_TU_CHOI(tmp_path):
    """Gửi chữ Việt cho Seedream là ra ảnh sai — chặn ở đây, đừng đốt tiền."""
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    c = TestClient(tao_app(kho, ve_anh=VeGia()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "V", "vi": "", "het": 0, "canh": [{"t": "Chưa dịch"}]}]})
    ma = kho.doc("SE001", "H")["dong"][0]["canh"][0]["id"]
    assert c.post(f"/api/tap/SE001/H/canh/{ma}/anh").status_code == 400


def test_ma_canh_la_thi_404(tmp_path):
    c, _ = _bo(tmp_path)
    assert c.post("/api/tap/SE001/H/canh/khong-co/anh").status_code == 404


def test_sinh_lai_thi_DE_len_ban_cu(tmp_path):
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    moi = b"\x89PNG\r\n\x1a\n" + b"\xff" * 32

    class Khac(VeGia):
        def gen_anh(self, prompt, dich, ref=None):
            dich.parent.mkdir(parents=True, exist_ok=True)
            dich.write_bytes(moi)
            return dich

    c2 = TestClient(tao_app(kho, ve_anh=Khac()))
    c2.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c2.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert c2.get(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh").content == moi


# ------------------------------------------------------------ cổng duyệt
def test_anh_moi_sinh_CHUA_duoc_duyet(tmp_path):
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert not _canh(kho).get("duyet")


def test_duyet_anh(tmp_path):
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet").status_code == 200
    assert _canh(kho)["duyet"]


def test_khong_duyet_duoc_canh_CHUA_CO_ANH(tmp_path):
    c, kho = _bo(tmp_path)
    assert c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet").status_code == 400


def test_sinh_lai_anh_thi_BO_DUYET(tmp_path):
    """Ảnh đổi thì con dấu duyệt cũ không còn nghĩa — giữ nó lại là video sẽ
    dựng từ tấm chưa ai nhìn."""
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert not _canh(kho).get("duyet")


# ------------------------------------------------------------ cả chương
def test_KHONG_con_duong_sinh_ca_chuong(tmp_path):
    """User chốt 25/09: nút tạo ảnh/video CHỈ ở từng cảnh. Bỏ nút mà để đường
    API lại là một tab cũ vẫn gọi được và đốt tiền cho cả chương — rút hẳn."""
    c, _ = _bo(tmp_path)
    assert c.post("/api/tap/SE001/H/anh").status_code == 404


# ------------------------------------------------------------ cửa gác
def test_L2_khong_sinh_duoc_anh(tmp_path):
    c, kho = _bo(tmp_path)
    xem = TestClient(tao_app(kho, ve_anh=VeGia()))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh").status_code == 403
    assert xem.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet").status_code == 403


def test_L2_van_XEM_duoc_anh(tmp_path):
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    xem = TestClient(tao_app(kho, ve_anh=VeGia()))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.get(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh").status_code == 200


def test_chua_bat_bo_ve_thi_503(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    c = TestClient(tao_app(kho))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "V", "vi": "", "het": 0, "canh": [{"t": "A", "pa": "EN A"}]}]})
    ma = kho.doc("SE001", "H")["dong"][0]["canh"][0]["id"]
    assert c.post(f"/api/tap/SE001/H/canh/{ma}/anh").status_code == 503


# ═══════════ máy chủ CHUẨN HOÁ cảnh ở đường ghi ═════════════════════════════
def test_luu_qua_API_thi_canh_duoc_DAT_MA(tmp_path):
    """Đường PUT ghi thẳng cái client gửi lên nên cảnh không bao giờ có mã —
    và ảnh thì neo vào mã. Chuẩn hoá phải nằm ở BIÊN GHI của máy chủ, không
    trông vào trang tự làm đúng."""
    c, kho = _bo(tmp_path)
    assert all(x.get("id") for x in kho.doc("SE001", "H")["dong"][0]["canh"])


def test_khoa_RAC_tu_client_khong_lot_vao_kho(tmp_path):
    """Một tab hỏng đẩy rác lên là kho phình. Lọc ở biên ghi."""
    c, kho = _bo(tmp_path)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["rac"] = "x" * 3000
    c.put("/api/tap/SE001/H", json={"dong": d, "outline": ""})
    assert "rac" not in kho.doc("SE001", "H")["dong"][0]["canh"][0]


def test_nap_kich_ban_moi_KHONG_lam_mat_ma_canh_cu(tmp_path):
    """Nạp lại kịch bản là thay hết dòng — cảnh cũ mất theo là đúng, nhưng
    không được để lại cảnh không mã."""
    c, kho = _bo(tmp_path)
    c.post("/api/tap/SE001/H/nap", json={"text": "A one." + chr(10) + "B two."})
    for dg in kho.doc("SE001", "H")["dong"]:
        assert all(x.get("id") for x in dg.get("canh", []))


def test_doc_chuong_bao_canh_nao_DA_CO_ANH(tmp_path):
    """Trang không tự biết cảnh nào có ảnh — máy chủ phải nói. Giá trị lấy theo
    GIỜ SỬA FILE nên vừa là cờ, vừa là mã chống cache: vẽ lại ảnh cùng tên mà
    không đổi mã thì trình duyệt vẫn hiện tấm cũ."""
    c, kho = _bo(tmp_path)
    truoc = c.get("/api/tap/SE001/H").json()["dong"][0]["canh"][0]
    assert not truoc.get("anh")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    sau = c.get("/api/tap/SE001/H").json()["dong"][0]["canh"][0]
    assert sau.get("anh"), "phải báo là đã có ảnh"


def test_co_anh_KHONG_bi_luu_xuong_kho(tmp_path):
    """`anh` là thứ suy ra từ đĩa, không phải dữ liệu — lưu xuống là sớm muộn
    lệch với file thật."""
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    d = c.get("/api/tap/SE001/H").json()["dong"]
    c.put("/api/tap/SE001/H", json={"dong": d, "outline": ""})
    assert "anh" not in kho.doc("SE001", "H")["dong"][0]["canh"][0]


def test_bo_ve_hoi_KET_BANG_SLUG_CUA_CHINH_MINH():
    """Bài học 23/09 đã phải sửa một lần cho `dich.py`: `web/ket_v3` ghi cứng
    SLUG = "rendery" nên cấp phát của Treatment không bao giờ thấy. Bộ vẽ ảnh
    KHÔNG được đi qua module đó."""
    import inspect

    from autoedit.treatment import app as mapp

    nguon = inspect.getsource(mapp._VeAnh)
    nhap = [d for d in nguon.splitlines()
            if d.strip().startswith(("import ", "from "))]
    assert not any("ket_v3" in d for d in nhap),         "phải hỏi két bằng slug của Treatment, không đi qua ket_v3 của RenderY"
    assert "khoa_cua_viec" not in nguon
    assert "gen_canh" in nguon and "api_key=" in nguon


def test_chua_cap_khoa_thi_bao_CHO_BAM(tmp_path):
    """Lỗi phải chỉ thẳng chỗ bấm, không bắt người ta đi dò."""
    from autoedit.treatment.app import _VeAnh

    import autoedit.treatment.dich as mdich

    cu = mdich.doc_ket_viec
    mdich.doc_ket_viec = lambda viec="dich": {}
    try:
        import pytest as _p

        with _p.raises(Exception) as e:
            _VeAnh().gen_anh("x", tmp_path / "a.png")
        assert "General" in str(e.value) and "gen_canh" in str(e.value)
    finally:
        mdich.doc_ket_viec = cu


def test_nguoi_khac_giu_chuong_thi_409_KHONG_phai_500(tmp_path):
    """Đo thật 24/09: bấm Sinh ảnh khi chương đang bị người khác giữ -> 500
    Internal Server Error, trang chỉ hiện "HTTP 500". Mọi đường ghi khác đều
    trả 409 kèm tên người đang giữ; đường này bỏ sót."""
    c, kho = _bo(tmp_path)
    kho.giu("SE001", "H", "nguoi_khac")
    r = c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert r.status_code == 409
    assert "nguoi_khac" in r.json()["detail"]


def test_duyet_cung_tra_409(tmp_path):
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    kho.giu("SE001", "H", "nguoi_khac")
    assert c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet").status_code == 409


# ─────────────────────────────────────────────────────────── tông đi vào prompt
# Đo trên production 25/09: bảng `so` TRỐNG 0 dòng ở mọi tập, 0/83 cảnh chọn
# `tong`, 0/83 cảnh gán asset. Prompt máy chủ thật sự gửi Seedream chỉ là
# "16:9 ratio. <pa>" — không một chữ nào về mood. Trong khi hộp cảnh trên màn
# hình vẫn hiện đoạn tông ở cuối, vì `boiler()` bên JS có đường lui còn
# `_prompt_anh` bên Python thì không.
#
# `_bo` ở trên dựng sổ đã có tông SẴN và cảnh đã chọn `tong` — tức đúng cái
# production KHÔNG có — nên `test_prompt_gui_di_la_prompt_DAY_DU` xanh suốt
# trong lúc mọi ảnh sinh ra đều trần. Dữ liệu thử sai thì xanh cũng vô nghĩa.


def _bo_tran(tmp_path, ve=None):
    """Đúng hình dạng PRODUCTION: sổ trống, cảnh không chọn tông, không asset."""
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    c = TestClient(tao_app(kho, ve_anh=ve or VeGia()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "Voice.", "vi": "", "het": 0,
         "canh": [{"t": "Cận bàn tay", "pa": "EN can ban tay"}]}]})
    return c, kho


def test_so_TRONG_van_phai_ghep_tong_vao_prompt(tmp_path):
    """Tập chưa lập sổ là trạng thái của MỌI tập lúc mới mở. Nếu lúc đó prompt
    ra trần thì mọi ảnh đầu tiên của mọi tập đều lệch mood."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "Mood and tone" in ve.goi[0], (
        "sổ trống thì máy chủ vẫn phải dùng tông mặc định — đúng như trang làm")


def test_prompt_may_chu_dung_DUNG_cai_so_ma_TRANG_nhan(tmp_path):
    """Gốc rễ của lỗi: `GET /so` chêm tông mặc định nên TRANG thấy, còn
    `_prompt_anh` gọi thẳng `kho.ds_so()` nên MÁY CHỦ không thấy. Hai bên phải
    đọc cùng một sổ, không thì cái người ta duyệt khác cái máy gửi đi."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    tong = [x for x in c.get("/api/tap/SE001/so").json() if x["loai"] == "tong"]
    assert tong, "endpoint sổ phải có tông mặc định"
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert tong[-1]["chu"] in ve.goi[0], (
        "đoạn tông trang hiện phải là đoạn máy chủ gửi, từng chữ một")


def test_canh_khong_chon_tong_thi_VAN_CO_tong(tmp_path):
    """Cảnh quên chọn tông thì KHÔNG BAO GIỜ được ra prompt cụt — đo thật:
    0/83 cảnh có chọn, tức đây là đường đi của mọi cảnh chứ không phải ngoại lệ.

    Tập chưa chỉ định tông mặc định thì lấy tông ĐẦU sổ. Không lấy tông cuối:
    cuối là theo thứ tự gõ vào, thêm một mood mới là cả tập đổi mặt."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [
        {"ma": "toi", "loai": "tong", "ten": "Tối", "chu": "DARK LOOK"},
        {"ma": "sang", "loai": "tong", "ten": "Sáng", "chu": "BRIGHT LOOK"}])
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "DARK LOOK" in ve.goi[0]


def test_mo_ta_asset_van_di_kem_khi_canh_co_gan(tmp_path):
    """Nửa kia của cùng lỗi: `ds_so()` trống thì mô tả asset cũng rơi mất."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "ca_map", "loai": "nhan_vat", "ten": "cá mập",
                          "chu": "scarred old great white shark"}])
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["ca_map"]
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "scarred old great white shark" in ve.goi[0]


def test_canh_khong_chon_tong_thi_theo_TONE_CUA_TAP(tmp_path):
    """Đường lui phải là tone MẶC ĐỊNH CỦA TẬP, không phải tông cuối sổ. Lấy
    tông cuối là lấy theo thứ tự gõ vào — thêm một mood mới là cả tập đổi mặt
    mà không ai bấm gì."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    c.put("/api/tap/SE001/so", json={"tong": "toi", "so": [
        {"ma": "toi", "loai": "tong", "ten": "Tối", "chu": "DARK LOOK"},
        {"ma": "sang", "loai": "tong", "ten": "Sáng", "chu": "BRIGHT LOOK"}]})
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "DARK LOOK" in ve.goi[0]
    assert "BRIGHT LOOK" not in ve.goi[0]


def test_canh_chon_tong_rieng_thi_THANG_tone_cua_tap(tmp_path):
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    c.put("/api/tap/SE001/so", json={"tong": "toi", "so": [
        {"ma": "toi", "loai": "tong", "ten": "Tối", "chu": "DARK LOOK"},
        {"ma": "sang", "loai": "tong", "ten": "Sáng", "chu": "BRIGHT LOOK"}]})
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["tong"] = "sang"
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "BRIGHT LOOK" in ve.goi[0]


def test_THIET_BI_cua_tone_di_vao_prompt(tmp_path):
    """User 25/09: "Prompt video đang thiếu hẳn … Thiết bị: Ống kính/Máy quay".
    Thiết bị là quyết định look của CẢ TẬP nên nằm ở tone, và phải đi vào
    prompt — để ở sổ mà không ghép thì cũng như không có."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    c.put("/api/tap/SE001/so", json={"tong": "toi", "so": [
        {"ma": "toi", "loai": "tong", "ten": "Tối", "chu": "DARK LOOK",
         "tb": "Shot on ARRI Alexa 35, 40mm anamorphic prime"}]})
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "ARRI Alexa 35" in ve.goi[0]
    assert "40mm anamorphic prime" in ve.goi[0]


# ────────────────────────────────────── cột kỹ thuật phải ĐI VÀO prompt
# Đo trên SE001 ngày 25/09: 49/49 cảnh có prompt EN đều đã có đủ `co` (cỡ cảnh),
# `goc` (góc máy), `cd` (chuyển động máy) và `sfx`. LLM điền, người dùng nhìn
# thấy trên thẻ và trong hộp cảnh — nhưng KHÔNG cột nào đi vào prompt. Cùng một
# họ lỗi với đoạn tông: dữ liệu có sẵn, không bao giờ tới nơi cần tới.


def test_prompt_anh_mang_CO_CANH_va_GOC_MAY(tmp_path):
    """Cỡ cảnh là thứ user duyệt trên bảng. Không gửi thì Seedream tự chọn cỡ,
    và luật "không 3 cảnh liền nhau cùng cỡ" mà LLM vừa tuân thủ thành vô ích."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0].update({"co": "CU", "goc": "eye level, straight-on"})
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "close-up" in ve.goi[0].lower(), "cỡ cảnh phải ra chữ, không để mã CU"
    assert "eye level, straight-on" in ve.goi[0]


def test_ma_co_canh_dich_ra_CHU_khong_gui_tat(tmp_path):
    """Gửi "ECU" trần cho nhà AI là gửi một mã nội bộ — nó đoán."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["co"] = "ECU"
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "extreme close-up" in ve.goi[0].lower()


def test_canh_khong_co_cot_ky_thuat_thi_prompt_van_sach(tmp_path):
    """Cảnh chưa sinh prompt kỹ thuật thì đừng chèn dấu chấm hay dấu phẩy lạc."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.goi[0].startswith("16:9 ratio. EN can ban tay")


# ─────────────────────── ẢNH REF đi vào lượt vẽ cảnh (user chốt 26/09)
# User bắt được lỗi trên hai cảnh liền nhau 10.1 và 10.2 — cùng một cái thang
# máy, hai hình khác hẳn. Gốc: mỗi cảnh sinh ảnh ĐỘC LẬP, CHỈ TỪ CHỮ. Mô tả dù
# hay đến đâu cũng chỉ THU HẸP vùng chọn chứ không chỉ vào một điểm, nên hai
# lượt gọi ra hai vật khác nhau — không viết văn nào chữa được.
#
# Đo trên ARK 26/09: `/images/generations` NHẬN `image` (data URL), cả chuỗi
# đơn lẫn mảng nhiều ảnh, và giữ đúng danh tính — thử hai ref (tàu K-129 +
# thuyền trưởng Kobzar) thì ảnh ra đúng khuôn mặt ấy đứng cạnh đúng con tàu ấy.


def test_ref_cua_ASSET_DI_VAO_luot_ve(tmp_path):
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "thang_may", "loai": "dao_cu", "ten": "Thang máy",
                          "chu": "old industrial cage elevator"}])
    r = kho.duong_ref("SE001", "thang_may", ".png")
    r.parent.mkdir(parents=True, exist_ok=True)
    r.write_bytes(PNG)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["thang_may"]
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.ref[0] == [r], "ảnh ref của asset phải đi kèm lượt vẽ"


def test_NHIEU_asset_thi_gui_NHIEU_ref(tmp_path):
    """Đo thật: ARK nhận mảng và giữ được cả hai danh tính cùng lúc."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [
        {"ma": "a", "loai": "nhan_vat", "ten": "A", "chu": "a"},
        {"ma": "b", "loai": "dao_cu", "ten": "B", "chu": "b"}])
    for m in ("a", "b"):
        p = kho.duong_ref("SE001", m, ".png")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(PNG)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["a", "b"]
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert len(ve.ref[0]) == 2


def test_asset_CHUA_CO_REF_thi_bo_qua_chu_KHONG_chet(tmp_path):
    """Gán asset nhưng chưa vẽ ref là chuyện thường giữa chừng. Lúc đó rơi về
    đúng hành vi cũ — chỉ chữ — chứ không được chặn người ta vẽ ảnh."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "x", "loai": "dao_cu", "ten": "X", "chu": "x"}])
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["x"]
    kho.luu("SE001", "H", d, "", "thu")
    r = c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert r.status_code == 200
    assert ve.ref[0] == []


def test_canh_khong_gan_asset_thi_khong_co_ref(tmp_path):
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.ref[0] == []


# ═══════════════ việc 3 — ĐO THẬT 26/09: ref thay được khối chữ ═══════════════
# Gen bốn biến thể trên cùng một cảnh thật (thang máy Liên Xô, cỡ CU, đã có ref):
#   A  pa đầy đủ + khối mô tả 77 từ + ref  (165 từ) -> vẫn ra khuôn hình RỘNG
#   B  bỏ khối mô tả, giữ ref              ( 86 từ) -> danh tính GIỮ NGUYÊN,
#                                                       khuôn hình chặt lại
#   D  giữ khối mô tả, BỎ ref              (165 từ) -> thang máy KHÁC HẲN,
#                                                       ra ảnh dựng 3D
# Kết luận: ảnh ref giữ danh tính, khối chữ KHÔNG giữ — nó chỉ tranh chỗ với
# khuôn hình. Vậy asset nào ĐÃ có ref thì thôi chêm chữ. Asset chưa có ref thì
# giữ nguyên đường cũ, vì lúc đó chữ là thứ duy nhất neo được nó.
def _co_ref(kho, ma):
    t = kho.duong_ref("SE001", ma, ".png")
    t.parent.mkdir(parents=True, exist_ok=True)
    t.write_bytes(PNG)
    return t


def _gan(kho, ma_asset):
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = [ma_asset]
    kho.luu("SE001", "H", d, "", "thu")


def test_asset_CO_REF_thi_KHONG_chem_khoi_mo_ta_chu(tmp_path):
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "thang_may", "loai": "boi_canh", "ten": "Thang Máy",
                          "chu": "cramped Soviet-era industrial elevator car"}])
    _gan(kho, "thang_may")
    _co_ref(kho, "thang_may")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "cramped Soviet-era industrial elevator car" not in ve.goi[0], (
        "asset đã có ref thì khối chữ chỉ tranh khuôn hình — đo 26/09 tấm A vs B")
    assert "Thang Máy" not in ve.goi[0], (
        "tên tiếng Việt đứng trơ một mình còn vô nghĩa hơn với Seedream")


def test_asset_co_ref_VAN_dinh_anh_ref_vao_luot_ve(tmp_path):
    """Bỏ CHỮ, không bỏ ẢNH. Bỏ nhầm ảnh là quay lại đúng tấm D: thang máy khác."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "thang_may", "loai": "boi_canh", "ten": "Thang Máy",
                          "chu": "cramped Soviet-era industrial elevator car"}])
    _gan(kho, "thang_may")
    t = _co_ref(kho, "thang_may")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.ref[0] == [t], "ảnh ref phải đi kèm lượt vẽ"


def test_asset_CHUA_co_ref_thi_VAN_chem_mo_ta_chu(tmp_path):
    """Đường lui giữ nguyên: chưa vẽ ref thì chữ là thứ duy nhất neo được."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [{"ma": "thang_may", "loai": "boi_canh", "ten": "Thang Máy",
                          "chu": "cramped Soviet-era industrial elevator car"}])
    _gan(kho, "thang_may")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "cramped Soviet-era industrial elevator car" in ve.goi[0]


def test_mot_asset_co_ref_MOT_khong_thi_chem_dung_cai_khong(tmp_path):
    """Cảnh trộn hai loại là chuyện thường. Lọc phải theo TỪNG asset."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    kho.luu_so("SE001", [
        {"ma": "thang_may", "loai": "boi_canh", "ten": "Thang Máy",
         "chu": "cramped Soviet elevator car"},
        {"ma": "kobzar", "loai": "nhan_vat", "ten": "Kobzar",
         "chu": "weathered Soviet captain in dark coat"}])
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["thang_may", "kobzar"]
    kho.luu("SE001", "H", d, "", "thu")
    _co_ref(kho, "thang_may")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "cramped Soviet elevator car" not in ve.goi[0]
    assert "weathered Soviet captain in dark coat" in ve.goi[0]


# ═════════════ việc 1 — PROMPT SỬA TAY (user chốt 26/09) ═════════════
# "Prompt sinh ảnh không đúng, đã sinh lại nhiều lần nhưng vẫn sai. Để tiết kiệm
# chi phí, tôi cần cho tính năng tự sửa prompt trước khi gen ảnh hoặc video."
#
# Ô prompt trên màn hình là bản GHÉP (16:9 + máy quay + pa + mô tả asset + tông).
# Sửa một phần rồi ghép lại thì không tách ngược ra được, nên bản sửa tay lưu
# NGUYÊN VĂN vào `pat`/`pvt` và ĐÈ HẲN bản ghép. Thấy gì gửi nấy.
#
# Cái giá phải trả, đã nói rõ với user và hiện thành nhãn trên màn hình: đã đè
# thì đổi tông / gán thêm asset / sửa nội dung Việt KHÔNG chảy vào prompt nữa.
def test_prompt_SUA_TAY_de_len_ban_tu_ghep(tmp_path):
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["pat"] = "TAY VIET HAN"
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert ve.goi[0] == "TAY VIET HAN", (
        "thấy gì gửi nấy — còn ghép thêm chữ nào là lại lệch với ô người ta sửa")


def test_prompt_sua_tay_RONG_thi_van_tu_ghep_nhu_cu(tmp_path):
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["pat"] = "   "
    kho.luu("SE001", "H", d, "", "thu")
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert "Mood and tone" in ve.goi[0]


def test_canh_CHUA_co_pa_nhung_co_prompt_tay_thi_VAN_ve_duoc(tmp_path):
    """Cổng chặn "chưa có prompt tiếng Anh" không được chặn người đã tự viết
    tay — họ đang đi đường vòng qua LLM, đó là cả mục đích của tính năng."""
    ve = VeGia()
    c, kho = _bo_tran(tmp_path, ve)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["pa"] = ""
    d[0]["canh"][0]["pat"] = "EN tay viet"
    kho.luu("SE001", "H", d, "", "thu")
    r = c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    assert r.status_code == 200, r.text


def test_prompt_tay_LUU_XUONG_KHO_va_doc_lai_duoc(tmp_path):
    """`pat`/`pvt` phải nằm trong danh sách khoá của cảnh. Thiếu là gõ xong,
    tải lại trang thì mất trắng — kiểu hỏng tệ nhất vì im lặng."""
    c, kho = _bo_tran(tmp_path)
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["pat"] = "AAA"
    d[0]["canh"][0]["pvt"] = "BBB"
    kho.luu("SE001", "H", d, "", "thu")
    x = kho.doc("SE001", "H")["dong"][0]["canh"][0]
    assert x.get("pat") == "AAA" and x.get("pvt") == "BBB"
