r"""BEAT — đơn vị GÁN NGHĨA của video ref (đợt 1, user duyệt 06/09).

Vì sao có lớp này: tag lấy từ pixel chỉ tả VẬT ("boat", "city"), không tả Ý.
Ba cảnh đầu ref Ecuador là bằng chứng: hình = boat/city/cityscape, còn lời nói
lúc đó = "cửa sông Guayas có thành phố Guayaquil / thủ phủ kinh tế Ecuador 2,5
triệu dân". Shot ẩn dụ càng vỡ: cánh chim tag "bird" không bao giờ khớp câu
"tự do tài chính".

Thiết kế chốt sau phản biện 06/09: KHÔNG đổi đơn vị cắt (khối voice của ta
trung vị 3.7s — xuất segment 12-20s là editor lại phải trim tay, quay về đúng
vấn đề "ref là khối lớn"). Thay vào đó:

    BEAT = đơn vị GÁN NGHĨA (gom câu liền mạch, 8-25s)
    SHOT = đơn vị DÙNG (giữ nguyên 871 cảnh cắt theo cú máy)
    shot.beat_id -> thừa hưởng lớp Nghĩa của beat

Ngưỡng NGUONG_KHE_S=2.0 chọn từ ĐO THẬT trên ref 1 (694 câu): khe giữa câu
trung vị 0.46s, p75 2.18s; ngưỡng 2.0 cho 176 beat (TB 17.7s) và khớp ngữ
nghĩa 8/8 câu đầu — không phải số bịa.
"""
from __future__ import annotations

from dataclasses import dataclass, field

NGUONG_KHE_S = 2.0      # khe giữa 2 câu > mức này = ranh beat
TOI_DA_S = 30.0         # beat dài hơn -> cắt tại khe lớn nhất bên trong
TOI_THIEU_S = 1.5       # beat ngắn hơn -> gộp vào beat kề gần nhất


@dataclass
class Beat:
    t0: float
    t1: float
    cau: list = field(default_factory=list)      # [(t0, t1, lời)]

    @property
    def loi(self) -> str:
        return " ".join(c[2] for c in self.cau).strip()

    @property
    def dai(self) -> float:
        return round(self.t1 - self.t0, 2)


def cat_beat(cau: list[tuple[float, float, str]],
             nguong: float = NGUONG_KHE_S,
             toi_da: float = TOI_DA_S) -> list[Beat]:
    """[(t0,t1,lời)] từ .srt -> [Beat]. Gom câu liền mạch, cắt beat quá dài."""
    if not cau:
        return []
    cau = sorted(cau, key=lambda c: c[0])
    nhom: list[list] = [[cau[0]]]
    for truoc, nay in zip(cau, cau[1:]):
        if nay[0] - truoc[1] > nguong:
            nhom.append([nay])
        else:
            nhom[-1].append(nay)

    ra: list[Beat] = []
    for g in nhom:
        b = Beat(t0=g[0][0], t1=g[-1][1], cau=list(g))
        if b.dai <= toi_da or len(g) < 2:
            ra.append(b)
            continue
        # beat quá dài -> cắt tại KHE LỚN NHẤT bên trong (đệ quy tới khi vừa)
        cho, khe_max = 0, -1.0
        for j in range(len(g) - 1):
            khe = g[j + 1][0] - g[j][1]
            if khe > khe_max:
                khe_max, cho = khe, j + 1
        ra.extend(cat_beat(g[:cho], nguong, toi_da))
        ra.extend(cat_beat(g[cho:], nguong, toi_da))

    # beat vụn -> gộp vào beat kề gần hơn (giữ nghĩa, tránh beat 1 từ)
    gon: list[Beat] = []
    for b in sorted(ra, key=lambda x: x.t0):
        if gon and b.dai < TOI_THIEU_S and (b.t0 - gon[-1].t1) < nguong * 2:
            gon[-1].t1 = b.t1
            gon[-1].cau.extend(b.cau)
        else:
            gon.append(b)
    return gon


def lam_id(tap: str, video: str, b: Beat) -> str:
    return f"beat:{tap}-{video}:{b.t0:.2f}-{b.t1:.2f}"


def luu_beats(conn, tap: str, video: str, beats: list[Beat]) -> int:
    """Ghi beat vào kho. Trả số beat MỚI."""
    from datetime import datetime, timezone

    moi = 0
    for b in beats:
        bid = lam_id(tap, video, b)
        co = conn.execute("SELECT 1 FROM beat WHERE id=?", (bid,)).fetchone()
        if co:
            conn.execute("UPDATE beat SET loi_goc=?, so_cau=? WHERE id=?",
                         (b.loi, len(b.cau), bid))
            continue
        conn.execute(
            "INSERT INTO beat(id, tap, video, t0, t1, loi_goc, so_cau, ngay) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (bid, tap, video, b.t0, b.t1, b.loi, len(b.cau),
             datetime.now(timezone.utc).isoformat()))
        moi += 1
    conn.commit()
    return moi


def gan_beat_cho_shot(conn, tap: str, video: str, beats: list[Beat]) -> dict:
    """Mỗi shot ref -> beat chứa TÂM của nó. Trả {gan, mo_coi, tong}.

    Shot mồ côi (không rơi vào beat nào) là CHUYỆN BÌNH THƯỜNG, không phải lỗi:
    36% thời lượng ref không có ai nói (đo 06/09) — b-roll thuần. Chúng vẫn
    sống bằng lớp Hình. Nhưng phải ĐẾM và báo, không nuốt im (bài học vision=0).
    """
    # CHỈ shot SỐNG (cắt theo cảnh). Bẫy 06/09: shot rác đời cũ (cắt theo phụ
    # đề sai, đã loại trừ) mang timecode của phim khác -> làm mọi phép kiểm mù.
    rows = conn.execute(
        "SELECT id, t0, t1 FROM clip WHERE nguon='ref' AND tap=? "
        "AND trang_thai='song' AND path_local LIKE ?",
        (tap, f"%{video}%")).fetchall()
    moc = sorted(((b.t0, b.t1, lam_id(tap, video, b)) for b in beats),
                 key=lambda x: x[0])
    gan = 0
    for r in rows:
        tam = (float(r["t0"]) + float(r["t1"])) / 2
        bid = next((m[2] for m in moc if m[0] <= tam <= m[1]), "")
        if bid:
            conn.execute("UPDATE clip SET beat_id=? WHERE id=?", (bid, r["id"]))
            gan += 1
    conn.commit()
    return {"gan": gan, "mo_coi": len(rows) - gan, "tong": len(rows)}
