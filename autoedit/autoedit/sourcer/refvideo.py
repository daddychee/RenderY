r"""Nguồn footage từ VIDEO CÓ SẴN của user + transcript .srt đi kèm.

Nhân sự đặt thẳng video vào thư mục chương, kèm .srt cùng số thứ tự:

```
RenderY/C1/
├── script.txt        ← kịch bản chương (như cũ)
├── voice.mp3         ← voice chương (như cũ)
├── Ref 1.mp4         ← video có sẵn
├── Ref 1.srt         ← transcript của video đó
└── Ref 2.mp4 / Ref 2.srt
```

Ghép video↔transcript theo SỐ CUỐI trong tên — quy ước của tool ME, đã chạy thật
trên nhiều job nên không bịa quy ước mới.

Cách khớp: câu beat ↔ segment transcript (~14 từ ≈ 1 câu) bằng cosine bge-small.
Đây là khớp LỜI-VỚI-LỜI: transcript nói gì thì coi như hình đang có cái đó. Với
kênh faceless (user chốt 02/09) giả định này đúng — không có người dẫn xuất hiện
để mà cắt nhầm vào mặt người. Phễu c5 + vision gate vẫn soi lại như mọi nguồn khác.

CẮT MUỘN: chỉ cắt clip THẮNG phễu, không cắt sẵn hàng loạt như ME. Một chương có
~400 segment ứng viên nhưng chỉ ~20 clip được dùng — cắt hết là phí 95% công ffmpeg
và rác đĩa.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from autoedit.align.srt_file import parse_srt

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".webm", ".m4v")
SEG_WORDS = 14        # ~1 câu — hằng số của ME, đã hiệu chỉnh qua job thật
MAX_CLIP = 10.0       # clip không quá 10s (ME)
MIN_CLIP = 3.0        # ngắn hơn 3s thì đoạn ref không đủ nghĩa (ME)
# Cosine tối thiểu. ME dùng 0.70; đo thật 02/09 trên chương C9 (22 beat) cho thấy
# bge-small nén MỌI điểm vào dải hẹp 0.71-0.84 — 0.70 nhận 100% beat, 0.80 nhận 9%,
# không ngưỡng nào tách được đúng/sai. Nên ngưỡng ở đây chỉ để LỌC RÁC RÕ RÀNG, còn
# việc phán đúng/sai giao cho phễu c5 + vision gate (đúng kiến trúc sẵn có).
# 0.72 = bỏ phần đáy dải, giữ đủ ứng viên cho phễu chọn.
NGUONG = 0.72
TOI_DA_UNG_VIEN = 6   # mỗi beat lấy tối đa ngần này ứng viên ref vào pool

# Tên file KHÔNG phải ref (kịch bản/voice của chính chương).
_KHONG_PHAI_REF = re.compile(r"^(script|target|voice|kich ?ban|l1|l3)", re.IGNORECASE)


class RefVideoError(RuntimeError):
    """Lỗi đọc/cắt video ref — caller quyết bỏ qua nguồn này hay dừng."""


@dataclass
class Seg:
    """1 đoạn transcript ref kèm mốc thời gian THẬT trong video."""

    text: str
    vao: float
    ra: float
    video: Path
    ten_ref: str

    @property
    def keo_dai(self) -> float:
        return max(0.0, self.ra - self.vao)


@dataclass
class RefVideo:
    """1 cặp video + transcript đã ghép."""

    video: Path
    srt: Path
    ten: str                    # nhãn ngắn để ghi sổ: "Ref 1"
    segments: list[Seg]
    thoi_luong: float = 0.0     # giây; 0 = chưa đo


def _so_cuoi(ten: str) -> Optional[int]:
    """Số cuối trong tên file — khoá ghép video↔srt (quy ước ME)."""
    m = re.findall(r"(\d+)", Path(ten).stem)
    return int(m[-1]) if m else None


def _la_ref(p: Path) -> bool:
    return not _KHONG_PHAI_REF.match(p.stem.strip())


def chia_segment(captions: list[tuple[float, float, str]], video: Path,
                 ten_ref: str, chunk: int = SEG_WORDS) -> list[Seg]:
    """Transcript -> segment ~1 câu, giữ mốc thời gian thật.

    Gom theo TỪ nhưng CẮT TẠI DẤU CÂU. ME gom 14 từ liên tục vì transcript của nó
    không có dấu câu đáng tin; .srt thì có, và cắt mù theo số từ trộn hai chủ đề vào
    một đoạn — đo thật: đoạn "...prayer wheel every morning at dawn GDP grew six
    percent..." lẫn cảnh chùa với cảnh kinh tế, cosine khớp sai cả hai.

    Đoạn quá ngắn (< `chunk`/2 từ) được gộp với đoạn sau: một mảnh 3 từ không đủ
    nghĩa để so sánh.
    """
    tu: list[tuple[str, float, float]] = []
    for vao, ra, text in captions:
        chu = (text or "").split()
        if not chu:
            continue
        buoc = (ra - vao) / len(chu) if ra > vao else 0.0
        for i, c in enumerate(chu):
            tu.append((c, vao + i * buoc, vao + (i + 1) * buoc))

    nhom: list[list[tuple[str, float, float]]] = []
    hien_tai: list[tuple[str, float, float]] = []
    for t in tu:
        hien_tai.append(t)
        het_cau = t[0].rstrip('"\')]').endswith((".", "!", "?", "…"))
        if het_cau or len(hien_tai) >= chunk:
            nhom.append(hien_tai)
            hien_tai = []
    if hien_tai:
        nhom.append(hien_tai)

    # Gộp mảnh quá ngắn vào đoạn trước. Ngưỡng THẤP (4 từ) là có chủ đích: gộp rộng
    # tay thì lại trộn chủ đề — đúng thứ vừa tránh ở trên. Câu 7 từ như "An old woman
    # turns her prayer wheel." đủ nghĩa để so cosine, không được gộp.
    toi_thieu = 4
    gon: list[list[tuple[str, float, float]]] = []
    for g in nhom:
        if gon and len(g) < toi_thieu:
            gon[-1].extend(g)
        else:
            gon.append(list(g))

    return [Seg(text=" ".join(x[0] for x in g), vao=g[0][1], ra=g[-1][2],
                video=video, ten_ref=ten_ref)
            for g in gon if g]


def doc_ref_tap(thu_muc_chuong: Path) -> tuple[list[RefVideo], list[str]]:
    """Ref dùng được cho MỘT chương = ref của CẢ TẬP + ref riêng của chương đó.

    Video ref thường phủ cả tập chứ không riêng chương nào (user chốt 02/09), nên
    đặt một lần ở `RenderY/` là mọi chương đều thấy:

    ```
    RenderY/
    ├── Ref 1.mp4 + Ref 1.srt   ← CẢ TẬP dùng chung
    ├── H/
    ├── C1/
    │   └── Ref 2.mp4 + .srt    ← chỉ riêng C1 (tuỳ chọn)
    └── E/
    ```

    Ref riêng của chương đứng TRƯỚC ref chung: cùng điểm khớp thì cái cụ thể hơn
    thắng. Trùng tên (cả hai cấp đều có "Ref 1") thì bản của CHƯƠNG được giữ.
    """
    chuong = Path(thu_muc_chuong)
    rieng, cb1 = doc_ref(chuong)
    chung, cb2 = doc_ref(chuong.parent)
    ten_rieng = {r.ten for r in rieng}
    return rieng + [r for r in chung if r.ten not in ten_rieng], cb1 + cb2


def doc_ref(thu_muc: Path) -> tuple[list[RefVideo], list[str]]:
    """Quét MỘT thư mục -> (danh sách ref đã ghép, cảnh báo).

    Không có video nào -> trả rỗng, chương chạy y như trước. Có video mà THIẾU .srt
    thì cảnh báo rõ tên file: phải bắt ở bước Kiểm tra, không để chạy 20 phút rồi
    mới biết (bài học 30/08).
    """
    thu_muc = Path(thu_muc)
    if not thu_muc.is_dir():
        return [], []

    videos = [p for p in sorted(thu_muc.iterdir())
              if p.is_file() and p.suffix.lower() in VIDEO_EXTS and _la_ref(p)]
    srts = [p for p in sorted(thu_muc.iterdir())
            if p.is_file() and p.suffix.lower() == ".srt" and _la_ref(p)]
    if not videos:
        return [], []

    srt_theo_so = {}
    for s in srts:
        so = _so_cuoi(s.name)
        if so is not None:
            srt_theo_so.setdefault(so, s)

    refs: list[RefVideo] = []
    canh_bao: list[str] = []
    for v in videos:
        so = _so_cuoi(v.name)
        s = srt_theo_so.get(so) if so is not None else None
        if s is None and len(videos) == 1 and len(srts) == 1:
            s = srts[0]          # 1 video + 1 srt: ghép luôn dù tên không có số
        if s is None:
            canh_bao.append(f"{v.name}: thiếu transcript .srt cùng số — bỏ qua video này")
            continue
        try:
            caps = parse_srt(s.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            canh_bao.append(f"{s.name}: đọc lỗi ({exc}) — bỏ qua")
            continue
        if not caps:
            canh_bao.append(f"{s.name}: không đọc được dòng nào — bỏ qua")
            continue
        ten = v.stem
        # Đo thời lượng NGAY ĐÂY (1 lần/video). Cần để biết cắt từ mốc X còn lấy
        # được bao lâu — ffprobe mỗi beat thì 20 beat = 20 lần gọi vô ích.
        try:
            from autoedit.project import ffprobe_duration

            dai = float(ffprobe_duration(v) or 0.0)
        except Exception:
            dai = 0.0          # không đo được -> coi như không giới hạn, phễu tự lo
        refs.append(RefVideo(video=v, srt=s, ten=ten,
                             segments=chia_segment(caps, v, ten),
                             thoi_luong=dai))
    return refs, canh_bao


def _asset_key(ten_ref: str, vao: float, ra: float) -> str:
    """Khoá truy ngược: nguồn + video + mốc thời gian gốc (cùng khuôn ytref:)."""
    return f"refvid:{ten_ref}@t={vao:.1f}-{ra:.1f}"


def _do_dai_can(beat) -> float:
    """Ô beat cần bao nhiêu giây. Ô neo theo VOICE — không co giãn (user chốt)."""
    keo = float(getattr(beat, "timeline_end", 0) or 0) - \
        float(getattr(beat, "timeline_start", 0) or 0)
    if keo <= 0:
        keo = float(getattr(beat, "end", 0) or 0) - float(getattr(beat, "start", 0) or 0)
    return max(keo, 0.0)


def tim_ung_vien(beat, refs: list[RefVideo], matcher, used_keys=(),
                 nguong: float = NGUONG,
                 toi_da: int = TOI_DA_UNG_VIEN) -> list[dict]:
    """Ứng viên ref cho 1 beat, ĐÚNG shape candidate của các nguồn khác.

    Trả rỗng khi: không có ref, matcher chưa sẵn sàng, hoặc không segment nào vượt
    ngưỡng. Rỗng là bình thường — beat đó dùng Pexels/kho như cũ.
    """
    if not refs or matcher is None or not getattr(matcher, "san_sang", False):
        return []
    pool: list[Seg] = [s for r in refs for s in r.segments]
    if not pool:
        return []
    r_thoi_luong = {r.ten: r.thoi_luong for r in refs if r.thoi_luong > 0}

    cau = (getattr(beat, "text", "") or "").strip()
    if not cau:
        return []

    from autoedit.sourcer.refembed import do_tuong_dong

    diem = do_tuong_dong(matcher, [cau], [s.text for s in pool])[0]
    can = _do_dai_can(beat)
    da_dung = set(used_keys or ())

    thu_tu = sorted(range(len(pool)), key=lambda i: -float(diem[i]))
    ra: list[dict] = []
    for i in thu_tu:
        sc = float(diem[i])
        if sc < nguong:
            break                      # đã sắp giảm dần -> phần sau càng thấp
        seg = pool[i]
        # Độ dài LẤY THEO Ô BEAT (voice là mốc bất di bất dịch), kẹp trong khung
        # MIN/MAX của ME.
        keo = max(min(can if can > 0 else seg.keo_dai, MAX_CLIP), MIN_CLIP)
        # Video ref là file LIÊN TỤC: cắt từ seg.vao lấy được bao lâu là do phần
        # CÒN LẠI của video quyết, không phải độ dài segment transcript. Segment
        # cuối cách hết video 2s mà ô cần 6s -> clip hụt hình. Báo đúng độ dài lấy
        # được để cửa kỹ thuật của phễu (MIN_DURATION_RATIO) loại giúp.
        if r_thoi_luong:
            con_lai = max(0.0, r_thoi_luong.get(seg.ten_ref, 0.0) - seg.vao)
            if con_lai > 0:
                keo = min(keo, con_lai)
        # CẮT SẠCH (editor Hải + user 05/09: "dư vài chục frame, minh hoạ sai
        # người/sai nước"): độ dài lấy theo Ô BEAT từng tràn qua ranh đoạn
        # transcript -> dính cảnh/người của câu SAU. Kẹp về ranh đoạn + 0.5s đệm;
        # clip thành ngắn thì cửa kỹ thuật phễu tự loại, KHÔNG lấy bẩn cho đủ.
        keo = min(keo, seg.keo_dai + 0.5)
        if keo < 1.5:
            continue                   # đoạn quá cụt — cắt sạch cũng không đủ hình
        key = _asset_key(seg.ten_ref, seg.vao, seg.vao + keo)
        if key in da_dung:
            continue
        ra.append({
            "asset_key": key,
            "url": str(seg.video),          # file local, không phải URL mạng
            "media_type": "video",
            "duration": keo,
            "width": 0, "height": 0,        # runner probe lại khi cần
            "description": seg.text[:160],  # câu transcript = mô tả cho phễu chấm
            "source": "refvideo",
            "source_video": seg.ten_ref,
            "src_in": seg.vao,
            "src_out": seg.vao + keo,
            "sim": sc,
            "relevance": sc,                # B1 dùng để xếp trước khi vào phễu
        })
        if len(ra) >= toi_da:
            break
    return ra


# ------------------------------------------------------------------ cắt clip
def cat_clip(video: Path, vao: float, keo: float, dich: Path,
             timeout: int = 300) -> Path:
    """Cắt 1 clip BỎ TIẾNG (-an) — chỉ gọi khi clip đã THẮNG phễu.

    `-ss` đặt TRƯỚC `-i` để ffmpeg nhảy thẳng tới mốc thay vì giải mã từ đầu:
    video 20 phút thì khác nhau vài giây với vài phần trăm giây mỗi clip.
    """
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-ss", f"{max(vao, 0.0):.3f}", "-i", str(video),
           "-t", f"{max(keo, 0.1):.3f}", "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", str(dich)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RefVideoError(f"cắt clip lỗi ({video.name} @{vao:.1f}s): {exc}") from exc
    if r.returncode != 0 or not dich.is_file():
        loi = (r.stderr or "")[-200:]
        raise RefVideoError(f"cắt clip lỗi ({video.name} @{vao:.1f}s): {loi}")
    # ffmpeg trả mã 0 nhưng ra file RỖNG khi mốc cắt vượt quá video thật — gặp thật
    # 02/09 với video ghép bằng `concat -c copy` (timestamp lệch: ffprobe báo 131s
    # nhưng chỉ có 79s hình). Không bắt ở đây thì clip rỗng lọt vào timeline.
    if dich.stat().st_size < 10_000:
        dich.unlink(missing_ok=True)
        raise RefVideoError(
            f"cắt ra clip rỗng ({video.name} @{vao:.1f}s +{keo:.1f}s) — "
            f"mốc cắt có thể vượt quá độ dài thật của video")
    return dich
