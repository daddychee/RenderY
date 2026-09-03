r"""Gom beat THIẾU HÌNH thành motif + sinh ảnh phương án -> phiên duyệt.

Mắt xích tự động của Đợt 2c: trước đây phiên duyệt phải tạo tay (demo 03/09);
giờ cuối stage source, beat nào vẫn needs_human (mọi thang fallback + sàn niche
đầu hàng) thì GLM gom thành MOTIF — một cảnh chủ gen MỘT lần, tái dùng nhiều
beat (user 03/09: "điểm giá trị nhất", giãn cách ≥60s) — rồi Seedream sinh
2 phương án ảnh/motif cho editor duyệt trên UI. Video (tiền lớn) chỉ gen SAU chốt.

Trần tiền (user chê $0.03/ảnh đắt, chưa chốt cách hạ — trần giữ hoá đơn nhỏ):
SO_MOTIF_TOI_DA=5 x SO_PHUONG_AN=2 = tối đa 10 ảnh ~ $0.30/job.

Fail-open: caller (run_source) bọc try/except — thiếu khoá, GLM chết, Seedream
chết đều KHÔNG hỏng stage; beat giữ needs_human như cũ, editor tự lo.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import BaseModel, Field

from autoedit.aigen.client import ArkClient
from autoedit.aigen.duyet import THU_MUC_ANH, Motif, PhienDuyet, PhuongAn

SO_MOTIF_TOI_DA = 5
SO_PHUONG_AN = 2
GIAN_CACH_S = 60.0     # user chốt 03/09: 2 lần dùng cùng clip phải cách >= 60s
DUOI_BIEN_THE = ("", "\nAlternative take of the SAME scene: different camera "
                     "angle and framing.")


class MotifDeXuat(BaseModel):
    mo_ta: str                    # 1 câu tiếng Việt cho editor
    prompt: str                   # tiếng Anh, tả cảnh quay 16:9 cinematic
    beat_ids: list[int] = Field(default_factory=list)


class KetQuaGom(BaseModel):
    motif: list[MotifDeXuat] = Field(default_factory=list)


_SYSTEM = f"""Bạn là đạo diễn hình ảnh cho video documentary/investigate faceless.
Các beat dưới đây KHÔNG tìm được footage — ta sẽ sinh cảnh bằng AI (ảnh, rồi video 5 giây).
Sinh AI tốn tiền, nên MỘT cảnh (motif) phải TÁI DÙNG được cho NHIỀU beat.

Nhiệm vụ: gom beat thành tối đa {SO_MOTIF_TOI_DA} motif. Luật:
1. Beat cùng motif phải cùng chủ thể + mood — một clip 5s dùng được cho MỌI beat đó.
2. Hai beat cùng motif phải cách nhau >= {GIAN_CACH_S:.0f} giây (cột t, giây trên timeline).
3. Beat không ghép được với ai: cho motif riêng. Vượt trần {SO_MOTIF_TOI_DA} motif thì ưu
   tiên beat sớm trong bài (hook/mở chương); beat bỏ lại người dựng tự lo, KHÔNG nhét bừa.
4. prompt: TIẾNG ANH, tả một cảnh quay 16:9 cinematic documentary — chủ thể, bối cảnh,
   ánh sáng, ống kính, chuyển động máy nhẹ (slow push-in/pan) — khớp mood beat.
   TUYỆT ĐỐI không chữ, không logo, không watermark, không bản đồ có địa danh.
5. mo_ta: một câu tiếng Việt ngắn để editor hiểu ngay cảnh này là gì."""


def _hop_le(kq: KetQuaGom, t_cua: dict[int, float]) -> list[MotifDeXuat]:
    """Máy kiểm luật, không tin GLM: beat lạ bỏ, beat trùng motif sau nhường motif
    trước, giãn cách <60s bỏ beat sau, motif rỗng bỏ, cắt trần."""
    da_dung: set[int] = set()
    ra: list[MotifDeXuat] = []
    for m in kq.motif:
        ids = [b for b in m.beat_ids if b in t_cua and b not in da_dung]
        ids.sort(key=lambda b: t_cua[b])
        giu: list[int] = []
        for b in ids:
            if not giu or t_cua[b] - t_cua[giu[-1]] >= GIAN_CACH_S:
                giu.append(b)
        if giu and m.prompt.strip():
            da_dung.update(giu)
            ra.append(MotifDeXuat(mo_ta=m.mo_ta, prompt=m.prompt, beat_ids=giu))
        if len(ra) >= SO_MOTIF_TOI_DA:
            break
    return ra


def gom_motif(project, llm=None, ark: ArkClient | None = None, log=None):
    """needs_human -> phiên duyệt cho_duyet (đã có ảnh). Trả PhienDuyet | None.

    None = không có gì để làm (0 beat thiếu hình, hoặc đã có phiên — không đè
    quyết định editor đang duyệt dở). Lỗi khoá/API thì NÉM — caller fail-open.
    """
    def ghi_log(msg: str) -> None:
        if log:
            log(msg)

    pdir = Path(project.project_dir)
    if PhienDuyet.doc(pdir) is not None:
        return None                       # chạy lại source không đè phiên đang duyệt
    thieu = {s.beat_id for s in project.shots if s.status == "needs_human"}
    beats = [b for b in project.beats if b.beat_id in thieu]
    if not beats:
        return None

    t_cua = {b.beat_id: (b.timeline_start if b.timeline_start is not None else b.start)
             for b in beats}
    dong = [f'beat {b.beat_id} | t={t_cua[b.beat_id]:.0f}s | chương {b.chapter} | '
            f'mood={b.mood} | {b.shot_size} | cần: {b.visual_concept} | '
            f'lời: "{b.text[:90]}"' for b in beats]

    if llm is None:
        from autoedit.director.glm_client import GLMDirectorClient
        llm = GLMDirectorClient(log_dir=pdir / "logs")
    kq, _ = llm.complete(_SYSTEM, "\n".join(dong), KetQuaGom)
    cac = _hop_le(kq, t_cua)
    if not cac:
        return None
    ghi_log(f"aigen: GLM gom {len(thieu)} beat thiếu hình -> {len(cac)} motif")

    # ---- sinh ảnh phương án (song song 4 luồng — ~18s/tấm đo 03/09) ----
    ark = ark or ArkClient()
    anh_dir = pdir / THU_MUC_ANH
    anh_dir.mkdir(exist_ok=True)

    def _mot_tam(ma: str, prompt: str, i: int) -> str | None:
        try:
            f = anh_dir / f"{ma}_pa{i + 1}.png"
            ark.gen_anh(prompt + DUOI_BIEN_THE[i % len(DUOI_BIEN_THE)], f)
            return f.name
        except Exception as exc:  # noqa: BLE001 — 1 tấm hỏng không giết cả phiên
            ghi_log(f"aigen: ảnh {ma} phương án {i + 1} lỗi: {exc}")
            return None

    phien = PhienDuyet(project_id=project.project_id)
    with ThreadPoolExecutor(max_workers=4) as pool:
        viec = []
        for idx, m in enumerate(cac, start=1):
            ma = f"m{idx}"
            for i in range(SO_PHUONG_AN):
                viec.append((ma, m, pool.submit(_mot_tam, ma, m.prompt, i)))
        anh_theo_ma: dict[str, list[str]] = {}
        for ma, _m, fut in viec:
            ten = fut.result()
            if ten:
                anh_theo_ma.setdefault(ma, []).append(ten)
    for idx, m in enumerate(cac, start=1):
        ma = f"m{idx}"
        ten_anh = anh_theo_ma.get(ma, [])
        if not ten_anh:
            ghi_log(f"aigen: motif {ma} không sinh được ảnh nào — bỏ, beat giữ needs_human")
            continue
        phien.motif.append(Motif(ma=ma, mo_ta=m.mo_ta, prompt=m.prompt,
                                 beat_ids=m.beat_ids,
                                 phuong_an=[PhuongAn(file=t) for t in sorted(ten_anh)]))
    if not phien.motif:
        return None
    phien.ghi(pdir)
    ghi_log(f"aigen: phiên duyệt sẵn sàng — {len(phien.motif)} motif, "
            f"{sum(len(m.phuong_an) for m in phien.motif)} ảnh")
    return phien
