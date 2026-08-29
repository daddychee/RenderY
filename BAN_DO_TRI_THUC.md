# BẢN ĐỒ TRI THỨC — nơi cần học cho tool edit padoma

> **Mục đích:** để AI phiên sau nhảy THẲNG tới đúng file cần đọc, KHÔNG phải đọc lại cả
> project cũ. Tra bảng → mở file nguồn (đường dẫn tuyệt đối) → làm theo verdict.
>
> **Verdict:** `copy` = bê gần nguyên (chỉnh path/import) · `adapt` = logic dùng được,
> sửa cho hợp bài toán mới · `learn` = đọc để hiểu cách làm, tự viết lại.
>
> **Quy ước:** khi tìm ra nguồn kiến thức mới → thêm dòng vào đây (đừng để tri thức trôi).

**Hai gốc đường dẫn (viết tắt bên dưới):**
- `⟪AE⟫` = `C:\Users\NBPC\Documents\Claude\Projects\code tool edit\autoedit\autoedit\`
- `⟪NB⟫` = `C:\Users\NBPC\Documents\Claude\Projects\code tool edit nhan ban\`
- `⟪MEM⟫` = `C:\Users\NBPC\.claude\projects\c--Users-NBPC-Documents-Claude-Projects-code-tool-edit-nhan-ban\memory\`

---

## NHÓM A — XƯƠNG SỐNG DỰNG-TỪ-ĐẦU (project `autoedit`)

Pipeline gốc: `new → align → direct → (enrich) → cut → source → (rank) → assemble → report`.
CLI typer: `⟪AE⟫cli.py` (`uv run autoedit <command>`).

| Cần làm việc gì | File nguồn | Dạy gì / lưu ý | Verdict |
|---|---|---|---|
| **Model dự án** (project.json, Inputs/Word/Beat/Stage) | `⟪AE⟫project.py` | Pydantic 1 nguồn sự thật + stage records (NT1). Nền cho mọi stage. | adapt |
| **Align voice↔script** | `⟪AE⟫align\matcher.py`, `⟪AE⟫align\whisper_local.py`, `align\base.py`, `align\runner.py` | faster-whisper + anchor matching, nội suy timestamp từng từ, chịu lỗi phát âm/hallucination. Không phụ thuộc CapCut. | copy |
| **Tọa độ kép source/timeline** | `⟪AE⟫cutter\timeline.py` | source_time (voice master) vs timeline_time (đã chèn nghỉ); hàm thuần, chống trôi timestamp. | copy |
| **Dò im lặng → điểm cắt sạch** | `⟪AE⟫cutter\silence.py`, `cutter\runner.py` | ffmpeg silencedetect, snap điểm cắt ±200ms quanh biên beat. | copy |
| **LLM director** (beat + concept + route + query) | `⟪AE⟫director\client.py` (client Claude + structured output + log), `schema.py` (Pydantic Outline/Beat), `prompts.py` (2-pass outline→beats), `validator.py` (beat 1.5–10s, coverage), `runner.py` | Sinh beat + visual concept + route (entity/stock/local/graphic) + query 3-tier. Temp=0. **prompts niche-riêng → phải sửa.** | adapt |
| **Enrich** (chart/infocard annotate beat) | `⟪AE⟫director\enrich.py` | Gắn chú thích chart/infocard vào beat. | adapt |
| **Footage — Pexels** | `⟪AE⟫sourcer\pexels.py` | Query 3-tier ≤4 từ, pool nhiều key chống rate-limit, cache SQLite. | copy |
| **Footage — entity ảnh thật** | `⟪AE⟫sourcer\entity.py` | Serper/Google CSE, cache per slug, cấm domain watermark, luật "người/sự kiện thật không ẩn dụ". | copy |
| **Footage — thư viện local + usage** | `⟪AE⟫sourcer\local.py`, `sourcer\usage.py`, `sourcer\runner.py` | Tìm footage đã tag; Protocol chung mỗi provider; log usage. | copy |
| **Thư viện footage niche** (index/tag/vision dedup) | `⟪AE⟫library\{db,indexer,profile,vision}.py` | SQLite index + tag + dedup bằng vision. | adapt |
| **Chuẩn hóa media** (H.264 30fps yuv420p / WAV 48k) | `⟪AE⟫packager\transcode.py` | ffmpeg wrapper chống CapCut lag/relink; skip nếu đã transcode (mtime). **Áp luật C4.** | copy |
| **Đóng gói donor + machine registry** | `⟪AE⟫packager\packager.py` (đọc donor, ghi đè key top-level), `packager\machine.py` (cache donor path/platform, `register-machine`), `packager\coverage.py` | Nền dựng draft trên donor template (NT2). **CapCut-specific → đối chiếu luật C1–C5.** | adapt |
| **Assembler 3-track** (V footage / A voice / A SFX-nhạc) | `⟪AE⟫packager\assembler.py` | Bố cục track + keyframe qua pycapcut. **Khuôn chính cho NT2 "chèn phần tử mới".** | adapt |
| **Chart / infocard render** | `⟪AE⟫packager\charts.py`, `packager\infocard.py` | Sinh chart/card đưa vào draft. | adapt |
| **Overlay text + SFX** | `⟪AE⟫overlay\text.py` (keyframe pos/scale/opacity: pop/slide/typing, không phụ thuộc preset → an toàn relink), `overlay\sfx.py` (resolve wav/mp3 theo kind), `overlay\style.py` | Toán keyframe generic; output CapCut-specific. | adapt |
| **Thư viện SFX** (phân loại + import Artlist) | `⟪AE⟫sfx\library.py`, `sfx\brief.py` | Phân loại kind (cash/impact/pop/whoosh/riser); import manifest; tránh lỗi license. | copy |
| **Nhạc nền** (BPM/energy/section) | `⟪AE⟫music\analyze.py`, `music\{brief,select,naming,library}.py` | librosa: BPM/onset/energy/loopable; fix octave error; fallback default. Editor-agnostic. | copy |
| **Report HTML checklist** | `⟪AE⟫report\runner.py` | Render project.json → HTML (beat/asset/needs_human/license). Không tốn LLM, chạy lại được. | copy |
| **CLI + thứ tự stage** | `⟪AE⟫cli.py` | typer; trình tự dựng-từ-đầu + resume. | learn |
| **Docs gốc autoedit** | `⟪AE⟫..\PRD.md`, `..\FOUNDATION.md` (ngôn ngữ hình ảnh: shot size, camera move, ẩn dụ), `..\RA_SOAT_LOGIC.md`, `..\KE_HOACH_TRIEN_KHAI.md` | Scope + tư duy visual + failure mode gốc. `FOUNDATION.md` đáng đọc khi viết prompt director. | learn |

---

## NHÓM A2 — NĂNG LỰC MỚI CỦA CHÍNH PADOMA (không có ở 2 project cũ)

| Cần làm việc gì | File nguồn | Dạy gì / lưu ý | Verdict |
|---|---|---|---|
| **Tự sinh title+chapter từ voice** (LUẬT ĐỨNG 2026-07-13: nguồn nạp thiếu TCF → tự chạy, mọi niche) | `autoedit/autoedit/library/tcf_gen.py` + lệnh `tcf-gen` | transcribe voice track (cache chung pause_scan_cache) → NÃO chọn title + chapter trong mốc block cho sẵn (NT4). Memory `tcf-gen-auto-title-chapter.md`: thứ tự ưu tiên nguồn bối cảnh + giới hạn viral/Clip ghép. | dùng thẳng |
| **Resolver path draft editor thật** (3 bẫy: name≠file đĩa · placeholder Resources/local · path chết dời máy) | `pause_scan.py::_resolve_rel` + `ingest.py::_resolve_material_path` + `mine.py::resolve_media` | Draft editor dời máy path chết hết — luôn fallback `materials/<basename path>`. Đã ăn 23 draft deepsea. | dùng thẳng |

## NHÓM B — LUẬT CAPCUT + BÀI HỌC API MỚI + GHI CHÉP (project `nhan ban`)

| Chủ đề | Nguồn | Dạy gì | Verdict |
|---|---|---|---|
| **Luật CapCut sống còn C1–C5** | `⟪NB⟫CLAUDE.md` §4 + `⟪NB⟫KINH_NGHIEM_CHUNG.md` PHẦN B | id không đổi, path tuyệt đối, ghi compact, chuẩn media, không đè folder. **Đọc trước mọi việc đụng draft.** | learn (đã bê vào CLAUDE.md §4) |
| **ROOT CAUSE preview đen/crash** | `⟪MEM⟫m10-breathing-status.md` | `package_inplace` ĐỔI `content["id"]` → CapCut không render. PHẢI giữ nguyên id; ghi compact; chỉ ghi draft_content.json. | learn |
| **Package tại-chỗ path tuyệt đối** (fix relink card/chart) | `⟪NB⟫autoclone\packager\inplace.py` + `⟪MEM⟫card-chart-cannot-download-fix.md` | `package_inplace` new_assets path TUYỆT ĐỐI; KHÔNG `package_embedded` (path ./ tương đối → relink + card đỏ). | adapt |
| **GLM vision native + tắt thinking** | `⟪MEM⟫glm-api-lessons.md` | Endpoint `/api/paas/v4/chat/completions` (KHÔNG anthropic-compat — nuốt ảnh→bịa) + `thinking:{type:disabled}`. Model `glm-4.6v`. | learn |
| **ai33.pro voice async** | `⟪MEM⟫ai33-voice-api.md` | Base `api.ai33.pro`, auth `xi-api-key`, POST `/v3/text-to-speech`→task_id→poll `/v1/task/{id}`→`output_uri` mp3 (72h). voice_id prefix `elevenlabs_`. | adapt |
| **GPU whisper align (~4-6×)** | `⟪MEM⟫gpu-whisper-align.md` | RTX 4060 Ti; thiếu cuBLAS → cài `nvidia-cublas-cu12` + PHẢI COPY `cublas64_12.dll` cạnh `ctranslate2.dll` (add_dll_directory không ăn vì delay-load). Có fallback CPU. | learn |
| **Voice gen song song** | `⟪MEM⟫voice-parallel.md` | 4 luồng (`-j`), ~35'→5-8', giữ cache/thứ tự; lỗi rate-limit thì hạ `-j`. | learn |
| **12 failure mode theo stage** | `⟪NB⟫RA_SOAT_LOGIC.md` | Phòng bug parse/align/map/retime/assemble (FM1 mất field→relink, FM6 whisper drift, FM8 lệch chương). | learn |
| **Bản đồ tái dùng module đầy đủ** | `⟪NB⟫KINH_NGHIEM_CHUNG.md` PHẦN A (A1–A9) + D | Map toàn bộ module + checklist bắt đầu feature mới. | learn |
| **Yêu cầu export draft từ editor** | `⟪NB⟫YEU_CAU_EXPORT_DRAFT.md`, `PHAT_HIEN_DRAFT_THAT.md` | Điều kiện draft hợp lệ (clip riêng, media tự chứa); golden test relink. | learn |
| **Launcher 1-bấm** | `⟪NB⟫CAI_DAT.bat` (uv + `uv sync --all-extras`), `chay_app.bat` (tự-heal), `DONG_GOI.bat` (zip ship), `⟪NB⟫loi-setup.md` (bug batch nested paren) | Mẫu .bat Windows tự-heal + `CREATE_NO_WINDOW` cho mọi subprocess. | copy khi tới bước đóng gói |
| **Setup máy mới** | `⟪NB⟫SETUP_CLAUDE.md`, `⟪MEM⟫new-machine-installer.md` | uv + Python 3.11 + `uv sync --all-extras` (BẮT BUỘC --all-extras) + ffmpeg bundled. | learn |
| **Hệ thống memory/ghi chép** | `⟪NB⟫NHAT_KY_BUILD.md` + `⟪MEM⟫MEMORY.md` | Mẫu milestone + frontmatter memory + index. (Đã tái lập ở CLAUDE.md §6.) | learn |
| **Điểm nhô YouTube (Most Replayed)** | tool ME OutlierY của user — **folder nguồn SẼ BỊ XÓA (user chốt 2026-07-10)**, tri thức đã hút về: thuật toán → `autoedit/library/ytpeaks.py`; chiến lược trọn tool (chia chương không-LLM, parse transcript đa dạng, embedding matching, budget nguồn) → memory `me-outliery-strategy.md` | yt-dlp `--dump-json` → field `heatmap`; dò đỉnh local-maxima-có-dốc-lên (foot+apex) + NMS ≥20s + primary ≥85%/secondary 55-84%/bỏ minor. Đã chạy thật trong tool ME. Phần transcript-matching ĐỂ DÀNH feature phân tích kịch bản (footage đã chốt KHÔNG dùng — vết b60). | copy — ĐÃ HÚT XONG 2026-07-10, không cần folder gốc nữa |

---

## .ENV — KEY ĐÃ BIẾT (chưa tạo file thật lần này)

| Key | Dùng cho | Nguồn |
|---|---|---|
| `ANTHROPIC_API_KEY` | director / rewrite / validate (Claude Sonnet) | cả 2 project |
| `PEXELS_API_KEY` (+ `_2`…`_10`) | footage stock; nhiều key né rate-limit 200 query/h | autoedit |
| `SERPER_API_KEY` | ảnh entity thật (thay Google Images) | cả 2 |
| `GOOGLE_CSE_KEY`, `GOOGLE_CSE_CX` | fallback ảnh entity (deprecating 2026) | cả 2 |
| `AI33_API_KEY` | gen voice ai33.pro (auth `xi-api-key`) | nhan ban |
| `GLM_API_KEY` (bigmodel) | vision tagging footage | nhan ban (memory glm) |

> Khi dựng `.env.example` thật: copy mẫu từ `⟪AE⟫..\.env.example` + bổ sung AI33/GLM.
