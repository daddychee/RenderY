# PRD — TOOL EDIT PADOMA (dựng video mới từ đầu)

> 🔸 **SKELETON — CHỜ ĐIỀN.** Logic chi tiết bàn ở các phiên sau. Mục nào chưa chốt để
> nguyên nhãn **`🔸 ĐANG BÀN`**. KHÔNG đoán logic khi chưa bàn (CLAUDE.md P1).
> Chỗ lệch giữa PRD và thực tế → tin `NHAT_KY_BUILD.md`.

---

## 1. Mục tiêu & bối cảnh
- **Một câu:** tool tự động DỰNG VIDEO MỚI TỪ ĐẦU (script + voice → draft CapCut hoàn chỉnh),
  editor tinh chỉnh phần cuối.
- **Luận điểm cốt lõi (2026-07-01):** tool phải edit **có tư duy đạo diễn hình ảnh** (pacing,
  hình thở, mood & tone, góc máy, cỡ cảnh, âm thanh hiện trường) — không ghép cơ học. Muốn vậy,
  mỗi kỹ năng nhỏ cần một **foundation** rõ + định nghĩa **tool thực thi thế nào** (Python thuần
  hay gọi LLM). Foundation gồm 2 phần: (i) **kiến thức** — đã có `⟪AE⟫..\FOUNDATION.md`;
  (ii) **dữ liệu DNA niche** — phải build (§9).
- **HAI CHẾ ĐỘ dùng (chốt 2026-07-01):**
  1. **Edit toàn bộ** — dựng cả video chỉ từ kịch bản (+ voice).
  2. **Edit một phần** — editor chính làm tay 10–15' đầu, tool **edit nốt phần còn lại**, nối tiếp
     vào draft editor đang làm dở (lai giữa "dựng mới" của `autoedit` + "đọc/nối draft có sẵn" của
     `nhan ban`). *Chi tiết bàn ở Phase D.*
- **Bối cảnh:** PADOMA MEDIA, Windows, ~200 video/tháng, nhiều kênh/thị trường.
- 🔸 ĐANG BÀN: thị trường/ngôn ngữ đích, thể loại video, độ dài mục tiêu, mức tự động hóa.

## 2. Input / Output
- **Input (dự kiến):** 🔸 ĐANG BÀN — script (.txt?), voice (.mp3?), brief sáng tạo, donor draft CapCut.
- **Output (dự kiến):** draft CapCut tên mới (mở + render OK, không relink) + `report.html`.
- 🔸 ĐANG BÀN: contract chính xác input, ai cung cấp voice (ai33 hay editor), asset đầu vào.

## 3. Pipeline stages
- **Chốt (2026-07-01): KHỞI ĐẦU giữ NGUYÊN pipeline autoedit** — vì nó ĐÃ hoàn chỉnh + đang chạy
  (~125 pytest), là "skeleton biết đi" sẵn có. Trình tự CLI thực tế:
  `new → align → direct → [enrich] → cut → source → assemble → report` (kèm `run` resume + `make`
  1-lệnh). Ranker gộp trong source.
- **Kiến trúc chủ đạo — tách ỐNG khỏi NÃO** (ranh giới = `project.json`, NT1):
  - ỐNG (deterministic, test dễ): align · cut · assemble · package CapCut (luật C1–C5).
  - NÃO (LLM + dữ liệu, hay đổi): director · chọn footage · pacing · hình thở · mood · SFX · nhạc.
  - → Ổn định ỐNG trước (Phase A), cải tiến NÃO sau (Phase C) mà không vỡ ống.
- 🔸 ĐANG BÀN (để Phase C): đổi/bổ sung stage nào khi lên NÃO thông minh (vd stage DNA-niche
  select thay cho sourcer thuần stock).

## 4. Data model — `project.json` (NT1)
- **Tham chiếu:** `⟪AE⟫project.py` (Inputs / Word / Beat / Stage / StageRecord).
- 🔸 ĐANG BÀN: field cụ thể cho tool mới (thêm gì so với autoedit).

## 5. Kiến trúc dựng draft (NT2)
- Donor template CapCut + pycapcut chèn phần tử MỚI (KHÔNG rebuild tay). Khuôn: `⟪AE⟫packager\assembler.py`.
- Tuân luật CapCut C1–C5 (CLAUDE.md §4).
- 🔸 ĐANG BÀN: bố cục track đích (mấy track V/A? overlay/chart/nhạc ở track nào?).

## 6. Provider & cost
- **PIVOT (2026-07-01): NÃO (LLM) chạy QUA CLAUDE CODE, KHÔNG dùng API key metered.** Lý do user:
  (1) công ty đã có tài khoản Claude cho editor dùng hằng ngày (đã trả, không tốn thêm);
  (2) **tùy biến** — editor tự thêm yêu cầu riêng theo niche bằng hội thoại, không phải sửa code;
  (3) kinh nghiệm thực: phát bản fix-cứng-API cho nhiều máy editor hay lỗi vặt, lại phải vào Claude
  Code fix. Máy editor có Claude Code = tự sửa tại chỗ.
- **Hệ quả kiến trúc:** khớp tách ỐNG/NÃO (§3). NÃO (director, DNA niche) = Claude Code (subscription);
  ỐNG (align/cut/assemble/CapCut) = script Python Claude Code gọi.
- **Rủi ro phải xử lý khi thiết kế:** trần usage subscription (batch ~200 video/tháng); ép structured
  output qua `claude -p`/Agent SDK; điều khoản dùng (AUP).
- **CHỐT (2026-07-01): đi Level 2 TRƯỚC, Level 1 SAU.** Level 2 = NÃO thành skills/subagents Claude
  Code editor điều khiển hội thoại (nhạc trưởng = Claude Code, gọi ỐNG Python). Chiến lược: Level 2 =
  chế độ **HỌC/TINH CHỈNH** — editor dạy tool bằng hội thoại, sửa lỗi, chốt luật theo từng niche. Khi
  1 niche chạy trơn ~20–30 video + editor fix hết lỗi → **đóng băng** luật đã chín thành pipeline tự
  động **Level 1** (nhanh, rẻ token, tất định) cho batch. Ba trụ giữ để chuyển mượt: (1) ỐNG xây 1 lần
  dùng chung 2 level, ranh giới `project.json`; (2) mọi quyết định NÃO + chỗ editor sửa GHI vào
  `project.json` → là bản thiết kế cho director Level 1 (chuyển = đóng băng, KHÔNG viết lại); (3) NT4
  giữ cả 2 level (LLM chỉ quyết nghĩa, timestamp do ỐNG + Pydantic).
- 🔸 ĐANG BÀN: Vision GLM (§9.1) giữ hay thay Claude vision — để Phase B. Cost/video, ngân sách/tháng.

## 7. Non-goals (dự kiến)
- Không thay editor làm 20% cuối. Không tự đăng YouTube.
- **CHỐT (2026-07-02, user xác nhận): tool KHÔNG chỉnh màu (color grade)** — chỉ CHỌN footage
  sẵn màu hợp mood ([[b1-mood-tone]] C2b); chỉnh màu là việc editor ở 20% cuối.
- 🔸 ĐANG BÀN: chốt danh sách không-làm còn lại.

## 8. Roadmap & Milestone (chốt 2026-07-01 — tiến độ thực ghi ở `NHAT_KY_BUILD.md`)

**Chiến lược:** skeleton biết đi TRƯỚC → dữ liệu → NÃO → chế độ một phần → feedback loop.
Lý do skeleton trước: chỉ khi có pipeline tiêu thụ, mới kiểm chứng được foundation/DNA tốt hay rác.

**Roadmap macro (mỗi phase gồm nhiều milestone nhỏ, mỗi milestone 1 cổng test):**
- **Phase A — Skeleton biết đi trên Windows:** copy autoedit → padoma → chạy end-to-end 1 video
  ngắn thật → 1 draft CapCut mở + render OK. NÃO còn ngu (footage stock đơn giản).
- **Phase B — Foundation dữ liệu (DNA niche):** ống nạp video → tách cảnh → GLM tag → thư viện (§9.1).
- **Phase C — NÃO thông minh:** director dùng DNA → footage/pacing/hình thở/mood/SFX/nhạc đúng niche.
- **Phase D — Chế độ edit một phần:** đọc draft editor làm dở (10–15') → nối tiếp phần còn lại.
- **Phase E — Feedback loop:** học từ chỗ editor sửa lại (§9.3).

**Phase A — chi tiết (đang chạy):**
| Bước | Việc | Cổng nghiệm thu |
|---|---|---|
| A0 | Copy autoedit→padoma làm codebase mới + setup env (`uv sync`, `.env`) | **pytest:** `--help` OK + ~125 test xanh |
| A1 | Port Mac→Windows (path `machine.py`, bỏ nhánh `textutil`/`osascript`) | `register-machine` chạy trên máy này |
| A2 | `demo-draft` sinh draft mẫu; port luật C1–C5 từ `nhan ban` nếu packager chưa cứng | **cổng mắt CapCut:** user mở OK + render |
| A3 | `make` 1 video ngắn thật end-to-end | **cổng mắt:** draft đầy đủ mở được + `report.html` |

> **Rủi ro Phase A đã nhận diện:** autoedit gốc phát triển trên **Mac**; bằng chứng CapCut chạy
> Windows + luật C1–C5 nằm ở `nhan ban`. Chỗ đáng sợ nhất = packager autoedit đóng gói trên
> Windows có mở được không (A2). Đây là spike ta nhắm sớm.

## 9. Ba module khó — bàn sâu SAU (Phase B/C/E)

Đây là phần "trí tuệ" khác biệt so với autoedit gốc, đã note để không quên (chưa chốt logic):
- **9.1. Mô hình hóa DNA niche** — học từ 20–30 project editor công ty (đủ layer) + 50 video đối thủ
  (chỉ footage tách cảnh + audio gộp + transcript). Với mỗi đoạn nội dung X → biết footage/SFX/mood/
  pacing nào hợp. Video đối thủ: đếm số footage tách cảnh → GLM vision tag mô tả → map "thoại dạng
  nào ↔ footage dạng nào". **Lưu ý cứng: giới hạn token** (số call cực lớn) → cần chiến lược batch/
  cache/sample. Vision = **GLM-4.6V native** (rẻ, luật §5 CLAUDE.md).
- **9.2. Motion graphic** — ảnh layer-2 + biểu đồ + thẻ card thông tin. **Đã có nền autoedit**
  (`director\enrich.py`, `packager\charts.py`, `packager\infocard.py`) → verdict adapt, không xây mới.
- **9.3. Feedback loop** — sau khi tool edit xong, editor sửa lại → diff đó là tín hiệu "tool sai chỗ
  nào" → cơ chế học lại để lần sau thông minh hơn. **Chưa có giải pháp — cần tư vấn kỹ.**
- **Hình thở (breathing)** — user muốn làm kỹ. Đã có nền: khái niệm `⟪AE⟫..\FOUNDATION.md §4.2` +
  hiện thực M10 ở `nhan ban` (`retime\breath.py`, LLM quyết ĐÂU thở + code là trọng tài neo voice).
  **Khác biệt cần lưu:** `nhan ban` là clone/mutate (tầng shift trên warp phức tạp); padoma dựng-mới
  nên hình thở đơn giản hơn — chỉ phân bổ thêm thời lượng footage khi build timeline lần đầu.

---

> **Nguồn tra cứu code:** `BAN_DO_TRI_THUC.md`. **Nguyên tắc làm việc:** `CLAUDE.md`.
