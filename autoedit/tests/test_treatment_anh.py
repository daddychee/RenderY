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
    """Thay Seedream: ghi thẳng ra file như client thật vẫn làm."""

    def __init__(self, hong=False):
        self.goi = []
        self.hong = hong

    def gen_anh(self, prompt, dich):
        self.goi.append(prompt)
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
        def gen_anh(self, prompt, dich):
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
def test_sinh_ca_chuong_bo_qua_canh_DA_CO_ANH(tmp_path):
    ve = VeGia()
    c, kho = _bo(tmp_path, ve)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    ve.goi.clear()
    r = c.post("/api/tap/SE001/H/anh").json()
    assert r["xong"] == 1 and len(ve.goi) == 1


def test_mot_canh_hong_thi_GIU_phan_da_xong(tmp_path):
    class Lung:
        def __init__(self):
            self.n = 0

        def gen_anh(self, prompt, dich):
            self.n += 1
            if self.n > 1:
                raise RuntimeError("ARK ngã")
            dich.parent.mkdir(parents=True, exist_ok=True)
            dich.write_bytes(PNG)
            return dich

    c, kho = _bo(tmp_path, Lung())
    r = c.post("/api/tap/SE001/H/anh").json()
    assert r["xong"] == 1 and r["loi"]
    assert c.get(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh").status_code == 200


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
    assert c.post("/api/tap/SE001/H/anh").status_code == 503


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


def test_sinh_ca_chuong_cung_tra_409(tmp_path):
    c, kho = _bo(tmp_path)
    kho.giu("SE001", "H", "nguoi_khac")
    assert c.post("/api/tap/SE001/H/anh").status_code == 409


def test_duyet_cung_tra_409(tmp_path):
    c, kho = _bo(tmp_path)
    c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/anh")
    kho.giu("SE001", "H", "nguoi_khac")
    assert c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/duyet").status_code == 409
