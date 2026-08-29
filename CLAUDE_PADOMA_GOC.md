# CLAUDE.md — TOOL EDIT PADOMA (dựng video mới từ đầu)

> Tài liệu chỉ dẫn cho Claude Code. ĐỌC TRƯỚC KHI CODE. Nguyên tắc ở đây ưu tiên hơn
> mọi mặc định. Người dùng vibe-code: giải thích tiếng Việt ngắn gọn khi có quyết định
> kỹ thuật, đề xuất phương án kèm trade-off, ưu tiên **code chạy + có test** hơn "đẹp".
> Khi kẹt: đưa 3 giả thuyết nguyên nhân → thử từng cái.

---

## 0. Dự án này là gì

Tool **DỰNG VIDEO MỚI TỪ ĐẦU**: nhận script + voice (và brief sáng tạo) → tự động
align, chia beat, chọn/tải footage, cắt, ghép motion graphics/nhạc/SFX → xuất **draft
CapCut hoàn chỉnh** cho editor tinh chỉnh phần cuối.

> 🔸 **LOGIC CHI TIẾT: ĐANG BÀN.** Phần 0 này là khung — mục tiêu, input/output, thứ tự
> pipeline sẽ chốt dần trong `PRD.md`. KHÔNG đoán logic khi chưa bàn (xem P1).

**Khác với project anh em `code tool edit nhan ban` (AutoClone):** cái đó **BIẾN ĐỔI một
draft có sẵn** (mutate). Tool này **DỰNG MỚI từ số 0** — giống project gốc `code tool edit`
(package `autoedit`). Đó là khác biệt kiến trúc quan trọng nhất (xem NT2).

**Bối cảnh:** PADOMA MEDIA, ~200 video/tháng, nhiều kênh/thị trường. Máy **Windows**.
CapCut draft path: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\` (donor/register-machine).
**Draft MỚI của tool xuất ra `E:\CapCut Drafts`** (user chốt 2026-07-13; `machine.json::draft_out_root`,
lệnh `set-draft-root`) và **tự PORTABLE** — path placeholder, copy nguyên folder sang máy editor mở được
không relink (`MO_TA_VAN_HANH_PORTABLE.md`).

---

## 1. HAI NGUỒN TRI THỨC — TRA `BAN_DO_TRI_THUC.md` TRƯỚC KHI VIẾT (bắt buộc)

**KHÔNG đọc lại cả project cũ.** Mở `BAN_DO_TRI_THUC.md` → tra đúng năng lực cần → nhảy
thẳng tới file nguồn (đường dẫn tuyệt đối) → copy/adapt/learn theo verdict đã ghi.

| Nguồn | Vai trò | Ở đâu |
|---|---|---|
| `code tool edit\autoedit\` | **Xương sống dựng-từ-đầu** (align→direct→cut→source→assemble→report) | Nhiều module dùng lại gần như nguyên |
| `code tool edit nhan ban\` | Luật CapCut C1–C5 + bài học API mới + hệ thống ghi chép | Bê luật + bài học, không bê pipeline |

Khi làm feature mới: **luôn tra bản đồ trước** → nếu có sẵn thì copy/adapt, đừng viết lại
từ đầu. Nếu bản đồ chưa có mục cần → thêm dòng mới vào bản đồ sau khi tìm ra.

---

## 2. NĂM NGUYÊN TẮC HÀNH ĐỘNG

### P1 — Đọc trước, code sau
**Không giả định. Không che giấu mơ hồ. Đưa trade-off trước khi viết một dòng code.**
- Tra `BAN_DO_TRI_THUC.md` — tìm module đã có, copy/adapt thay vì viết lại.
- Với bất kỳ thứ gì liên quan CapCut draft: đọc **luật C1–C5 (§4)** trước.
- Yêu cầu nhiều cách hiểu → đưa cả hai, nêu trade-off, **không tự chọn im lặng**.
- Behavior CapCut chưa rõ → dựng draft test nhỏ, bisect (mỗi bản đổi đúng 1 biến), nhờ
  user mở mắt xem. Không suy đoán một mình.
- Prompt thiếu thông tin quan trọng → dừng, nêu cái thiếu, hỏi. Đừng đoán.

### P2 — Tối giản: code vừa đủ, không thêm gì
**Minimum code giải quyết đúng bài. Không speculative. Không "phòng khi sau này cần".**
- Không thêm tính năng ngoài yêu cầu. Không abstraction cho code dùng 1 nơi (≥3 nơi mới cần helper).
- Không error handling cho scenario không thể xảy ra — trust CapCut schema đã biết, trust internal API.
- 200 dòng viết được 50 dòng → viết lại. "Senior engineer có nói cái này quá phức tạp không?"

### P3 — Phẫu thuật: chỉ sửa đúng chỗ cần
**Đụng đúng file, đúng dòng. Không "cải thiện" code bên cạnh. Không refactor khi không hỏng.**
- Mỗi diff truy ngược về đúng 1 yêu cầu. Khớp style hiện tại kể cả khác cách mình viết.
- Dead code không liên quan → nhắc user, đừng tự xóa. Orphan do mình tạo → xóa đúng cái đó.
- **PRESERVE-BY-DEFAULT** cho donor template CapCut: copy toàn bộ dict gốc, chỉ patch key
  cần. Field không hiểu → đi qua nguyên vẹn, KHÔNG rebuild từ schema.

### P4 — Thực thi có đích: xác định thành công TRƯỚC
**Biến task thành mục tiêu xác minh được. Loop đến khi đạt — không tự báo xong khi chưa kiểm.**
> TUYỆT ĐỐI không nhảy cóc nhiều milestone một lúc. Xong 1 bước → test → báo cáo →
> chờ user xác nhận → mới sang bước tiếp.
- **Cổng pytest** — Claude Code chạy + báo kết quả. Mỗi stage mới ≥1 happy-path pytest.
- **Cổng mắt CapCut** — user xác nhận bằng mắt. Claude Code **KHÔNG TỰ BÁO ĐẠT** cổng mắt.
- pytest fail → dừng, 3 giả thuyết nguyên nhân, thử từng cái.
- **Git LOCAL đã bật (D5, 2026-07-09):** sau mỗi milestone đạt → `git commit` làm mốc khôi phục (cùng lúc cập nhật NHAT_KY). **KHÔNG remote, KHÔNG push GitHub** — user chỉ muốn backup trên máy. `.gitignore` đã loại `.env`/`.venv`/`autoedit/projects/`.

### P5 — Rà chồng chéo & vùng ảnh hưởng: mọi thay đổi trả lời "ĐỤNG AI?" trước khi code
**Hệ thống nhiều tầng quyết định: luật mới dễ ngược chiều luật cũ; fix bug cũ dễ đẻ bug
mới.** (User chốt 2026-07-04 sau đợt rà tìm ra 4 mâu thuẫn thật — mẫu chuẩn:
`MO_TA_VAN_HANH_L2B_SAU.md §4b`.)
- **Thêm tính năng/luật mới → mô tả vận hành BẮT BUỘC có mục "Rà chồng chéo":** liệt kê
  các tầng hiện có CÙNG QUẢN thứ sắp đụng (prompt/foundation → validator chặn → hậu xử lý
  âm thầm → phễu source → assembler) và trả lời 2 câu: luật mới có NGƯỢC CHIỀU tầng nào
  không? tầng nào có thể ÂM THẦM LẬT quyết định của tầng mới (và ngược lại)? Ghi kết quả
  kể cả khi là "không đụng gì".
- **Sửa code/fix bug → rà VÙNG ẢNH HƯỞNG trước khi sửa:** grep MỌI nơi tiêu thụ cái sắp
  đổi (caller của hàm, chỗ đọc field/schema, chỗ đọc format file/tên file) → từng nơi trả
  lời "hành vi ở đây có đổi không?". Quét luôn chỗ CÙNG PATTERN với bug (bug `int()` luôn
  có anh em) — sửa cùng hoặc ghi "còn ngỏ" vào nhật ký, KHÔNG im lặng bỏ qua. (Bằng chứng
  lịch sử của lỗi quên-consumer: bug B2 `run` gọi direct thiếu `engine`; bug F6 đè tên file.)
- **Cổng hồi quy:** mỗi bug fix ≥1 regression test TÁI HIỆN bug trước-fix; xong mọi thay
  đổi chạy FULL pytest suite, không chỉ test của module vừa sửa. Báo cáo milestone có
  1–3 dòng "vùng ảnh hưởng đã rà: ...".

---

## 3. NĂM NGUYÊN TẮC KIẾN TRÚC (đã thích nghi cho dựng-từ-đầu)

**NT1 — `project.json` là nguồn sự thật duy nhất.** Mọi stage đọc/ghi vào đó. Resume được
từ bất kỳ stage. (Y như `autoedit/project.py`.)

**NT2 — DONOR TEMPLATE + CHÈN PHẦN TỬ MỚI, KHÔNG REBUILD BẰNG TAY.** Dựng video mới bằng
cách: lấy **donor draft CapCut** (template hợp lệ trên máy), rồi build track/segment/material
MỚI bằng **pycapcut** → chèn vào cây draft. TUYỆT ĐỐI không viết tay toàn bộ schema
`draft_content.json` từ số 0 (dễ sai key → relink/crash). Tham khảo
`autoedit/packager/assembler.py`. *(Đây là điểm khác NT2 của AutoClone: bên đó mutate draft
có sẵn; bên này build mới trên khung donor.)*

**NT3 — PRESERVE-BY-DEFAULT.** Donor template giữ trọn mọi trường lạ; chỉ đụng trường
chủ động sửa. Field không hiểu → đi qua nguyên vẹn.

**NT4 — LLM KHÔNG BAO GIỜ SINH TIMESTAMP.** LLM chỉ trả word index / quyết định nghĩa /
concept. Mọi timestamp tính từ alignment (faster-whisper). Pydantic validator cho mọi output LLM.

**NT5 — Mỗi job sinh draft TÊN MỚI**, không đè bản cũ. Mọi biến đổi ghi log vào `project.json`
để Report + editor kiểm. Khôi phục được.

---

## 4. LUẬT CAPCUT SỐNG CÒN (bê nguyên từ AutoClone — vẫn đúng 100%)

> Bài học debug đầy đủ: `code tool edit nhan ban\KINH_NGHIEM_CHUNG.md` PHẦN B.

**C1. `content["id"]` — KHÔNG BAO GIỜ ĐỔI.** CapCut neo id timeline này ở registry TOÀN CỤC
ngoài folder draft. Đổi → mở được nhưng preview đen, click footage = CapCut TẮT. Phân biệt
draft: chỉ đổi `draft_meta_info.json::draft_id`.

**C2. Path media — luôn TUYỆT ĐỐI.** ĐÚNG: `C:\...\materials\x.mp4` hoặc placeholder
`##_draftpath_placeholder_<GUID>_##/materials/<name>`. SAI: `./materials/x.mp4` → CapCut
8.8.0 không resolve → relink hết. Dùng `package_inplace` (path tuyệt đối), KHÔNG `package_embedded`.

**C3. Ghi `draft_content.json` compact.**
```python
json.dump(content_dict, f, ensure_ascii=False, separators=(",", ":"))
# CHỈ ghi draft_content.json (CapCut 8.8.0 không đọc draft_info.json)
# draft_meta_info.json::draft_fold_path = đường dẫn tuyệt đối thật của folder draft
```

**C4. Chuẩn hóa media trước khi vào draft.** Video: H.264 CFR, yuv420p, 30fps. Audio: WAV
PCM 16-bit 48kHz. Ảnh: JPEG bỏ EXIF. Không chuẩn → CapCut relink bắt buộc. Dùng
`transcode.py` (tra bản đồ).

**C5. KHÔNG đè folder draft đã có** — CapCut cache draft_id theo folder. Luôn sinh tên mới.

---

## 5. CHỌN PROVIDER AI (bê từ AutoClone)

| Task | Provider | Lý do |
|---|---|---|
| director (beat/concept), rewrite ngôn ngữ, validate | **Claude Sonnet** | chất lượng cao; GLM không đủ tin cho logic |
| vision tagging footage | **GLM-4V** native | ~½ giá Haiku, chính xác tương đương |
| gen voice | **ai33.pro** | ElevenLabs wrapper async: POST→poll→mp3 (72h) |

**GLM vision — 3 quy tắc bắt buộc:**
- Endpoint NATIVE dạng `/api/paas/v4/chat/completions` (KHÔNG Anthropic-compat — nó NUỐT ẢNH
  → bịa kết quả).
- **Server QUỐC TẾ `https://api.z.ai` là MẶC ĐỊNH** (user chốt 2026-07-10: CÙNG key, đo thật
  nhanh ~3x + ít lỗi đứt kết nối hơn hẳn server TQ `open.bigmodel.cn`); cần quay về TQ →
  env `GLM_API_URL` (code: `library/vision.py::glm_api_url`).
- Thêm `"extra_body": {"thinking": {"type": "disabled"}}` (reasoning ăn max_tokens → rỗng).

Chi tiết: `BAN_DO_TRI_THUC.md` nhóm B (memory `glm-api-lessons.md`, `ai33-voice-api.md`).

---

## 6. HỆ THỐNG GHI CHÉP (bắt buộc — mục tiêu chính của dự án)

Mỗi tính năng mới / fix bug / nâng cấp PHẢI được ghi lại để theo dõi + chuyển giao:

1. **`NHAT_KY_BUILD.md`** — nhật ký + bảng milestone. Sau mỗi milestone đạt: cập nhật bảng
   (Nội dung | Trạng thái ✅/🔄/⏸ | Test | Ngày) + entry (Cái gì đổi / Vì sao / Verify / Số pytest).
   Đây là NGUỒN SỰ THẬT tiến độ mới nhất — chỗ lệch PRD thì tin nhật ký.
2. **Memory files** — mỗi quyết định/bug sâu ghi 1 file ở
   `~\.claude\projects\c--...-tool-edit-padoma\memory\` (frontmatter YAML: name/description/type)
   + 1 dòng index vào `MEMORY.md`. Cross-link `[[tên]]`. Ghi root cause + fix + verify.
3. **`BAN_DO_TRI_THUC.md`** — khi tìm ra nguồn kiến thức mới, thêm dòng vào bản đồ.

> Docs đọc theo thứ tự: **CLAUDE.md** (file này) → `BAN_DO_TRI_THUC.md` (tra nguồn) →
> `PRD.md` (scope) → `NHAT_KY_BUILD.md` (tiến độ thực tế).

---

## 7. MÁY EDITOR (chỉ hiệu lực khi tồn tại file `BAN_GIAO\MAY_EDITOR.flag`)

Máy này là máy VẬN HÀNH của editor; máy gốc của user PADOMA là CHUẨN tri thức. Cài đặt /
sự cố: `HUONG_DAN_CAI_DAT_MAY_EDITOR.md`. Mỗi bug fix / luật mới, NGOÀI bộ ghi chép §6
còn PHẢI (kênh DUY NHẤT đưa tri thức về máy gốc — thiếu là tri thức MẤT khi user gộp):
1. Mirror memory file mới/sửa vào `BAN_GIAO\memory_moi\` (copy nguyên file `.md`).
2. Thêm entry `BAN_GIAO\NHAT_KY_MAY_EDITOR.md` (khuôn trong file, mới nhất trên cùng).
3. `git commit` rồi `git bundle create BAN_GIAO/padoma_editor.bundle --all`.

KHÔNG remote/push GitHub. **Dựng video SONG SONG nhiều máy: ĐƯỢC** (G2-M4 2026-07-16 — sổ
PostgreSQL máy gốc ghi đồng thời an toàn; GLM key RIÊNG từng editor, Pexels ×10 chung).
Khuyến cáo nhẹ còn lại: tránh 2 mẻ NẠP kho vào CÙNG niche đúng cùng lúc (vì file kho trên F:,
không phải vì sổ — HUONG_DAN A4.3).
