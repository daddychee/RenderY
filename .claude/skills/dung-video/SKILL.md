---
name: dung-video
description: Buồng lái dựng video (Level 2) — editor điều khiển pipeline autoedit BẰNG HỘI THOẠI. Dùng khi editor muốn dựng 1 video từ folder chứa script + voice, có cổng duyệt/chỉnh beat trước khi tải footage.
---

# Buồng lái dựng video (L2b sâu)

Bạn là **ĐẠO DIỄN phiên sống**. Editor giao 1 folder (script + voice) + mô tả ý muốn.
Bạn đọc bộ foundation → TỰ đạo diễn outline + beats → nộp cho ỐNG kiểm (`direct-ingest`).
Timestamp/cắt/ghép do ống Python lo — bạn CHỈ trả **word index + concept** (NT4),
KHÔNG BAO GIỜ tự sinh timestamp.

## Chuẩn bị (chỉ kiểm 1 lần mỗi phiên làm việc)
- Mọi lệnh chạy trong thư mục tool `autoedit/` (có `.venv`): `cd autoedit` rồi `uv run autoedit ...`.
- Nếu máy chưa đăng ký donor CapCut: chạy `uv run autoedit register-machine` (1 lần/máy).
- **Đọc 12 file foundation nhóm đạo diễn** (1 lần mỗi phiên, KHÔNG phải mỗi video), ở `foundation/`:
  `a1-chia-beat-chuong` · `a2-chuc-nang-doan` · `a3-open-loop-callback` · `b1-mood-tone` ·
  `b3-pattern-interrupt` · `c1-phan-tuyen-nguon` · `c2-an-du-veto` · `c4-tu-khoa-tim` ·
  `d1-pacing` · `d2-hinh-tho` · `d3-loai-cat-transition` · `f1-text-typo-motion-graphics`.
  **KHÔNG đọc 6 file còn lại** (`c3/c5/c6/c7` = luật phễu source ĐÃ CODE trong ranker;
  `e1` ducking/nhạc đã code trong ống; `f2` đang treo) — đọc thêm chỉ gây loạn.

## Nhận input từ editor
- Đường dẫn **folder** chứa script (`.txt`) + voice (`.mp3`/`.wav`). Tự `ls` folder để tìm 2 file.
- **Brief tự do** (tuỳ chọn): niche, tone, nhấn mạnh gì (vd "hook nhấn con số $1M", "mood ấm, hoài niệm").
- Nếu thiếu folder hoặc không thấy script/voice → hỏi lại, ĐỪNG đoán.

### LUẬT TỰ NẠP video mẫu (user chốt 2026-07-16 — áp MỌI máy: gốc + editor)
Bài có folder **video mẫu** (kèm draft CapCut editor đã tách cảnh) → **TỰ nạp kho TRƯỚC
`direct-context`, KHÔNG hỏi, KHÔNG bỏ qua** — kho công ty phải dày lên theo từng bài
(bằng chứng sót: DS084 khai `--ref` nhưng mẻ chưa nạp → REF vô tác dụng, 10 video mẫu
mất trắng khỏi kho):
1. Với TỪNG video mẫu: tìm draft CapCut tách cảnh tương ứng trong folder draft editor đưa
   (khớp theo tên) — video nào không thấy draft → hỏi ĐÚNG video đó, các video còn lại vẫn nạp.
2. `uv run autoedit library-ingest <niche> "<folder draft>" --source-class viral`
   (+ `--topic "..."` khi tên file nguồn là mã số). Video mẫu kênh khác = `viral`;
   editor nói mẫu là video CÔNG TY → `own` (own-vs-viral: class do NGƯỜI NẠP khai, máy không suy).
   Chạy lại tự resume — nạp trùng vô hại. **Kênh nguồn (ghi công 2026-07-17):** mẻ viral
   có YouTube ID thì kênh TỰ điền từ yt-dlp; editor khai tường minh → `--channel "<Tên Kênh>"`
   (thắng kênh YouTube). Kho cũ thiếu kênh → `channel-audit` soát + `channel-set` điền.
3. Nạp XONG hết → `direct-context` (thứ tự SP1-014) → PHA 2 `source` thêm `--ref "<folder mẫu>"`.
Khuyến cáo A4.3 giữ nguyên: 2 máy tránh 2 mẻ nạp CÙNG niche đúng cùng lúc — biết máy khác
đang nạp cùng niche thì so le bước nạp, không biết thì cứ chạy.

**REF THEO CHƯƠNG (user chốt 2026-07-18):** editor được phép chia folder mẫu thành folder
con `Chapter 1`, `Chapter 2`… (nhận cả `chuong/chương/ch` + số, tên folder ĐÚNG khuôn không
hậu tố) — cảnh trong đó chỉ được ưu tiên REF (chèn + bonus) ở beat ĐÚNG chương ấy; video
để ngay gốc folder mẫu = mẫu chung cả bài. Chế độ MỀM: cảnh sai chương vẫn có thể được chọn
qua search thường, trần 15% giữ cả mẻ. ⚠ Xếp video vào folder chương TRƯỚC khi editor làm
draft tách cảnh (path trong draft phải trỏ file TRONG folder chương). Vẫn khai `--ref` trỏ
folder GỐC như cũ, không thêm cú pháp. Chi tiết: `MO_TA_VAN_HANH_REF.md §6`.

## PHA 1 — đạo diễn phiên sống (đường SÂU)
1. Tạo project: `uv run autoedit new --script "<script>" --voice "<voice>" --brief "<brief>" --channel "<niche>"`
   → lấy `project_dir` từ output.
2. `uv run autoedit align <project_dir>`
3. `uv run autoedit direct-context <project_dir>` → đọc `<project_dir>/direct_context.md`:
   transcript đánh số `[i]word` + **BẢNG RÀNG BUỘC CỨNG** (in từ hằng số code).
   - **BOOST (2026-07-17):** editor nói khán giả thích cảnh dạng X ("khán giả thích phụ
     nữ đẹp", "nhiều cảnh động vật") → khai **NGAY Ở ĐÂY**:
     `--boost "beautiful woman"` (lặp được; `@hook`/`@ch3` khoanh vùng, mặc định cả bài;
     X = tiếng Anh theo từ vựng tag kho). Khai trước direct mới ăn TRỌN 2 tầng (NÃO đan
     X vào concept + phễu cộng điểm); khai muộn ở `source` chỉ còn tầng phễu. Sở thích
     BỀN của cả niche → điền `audience_bias` trong `niche_profile.yaml` 1 lần, khỏi khai
     từng bài. Context sẽ có khối **SỞ THÍCH KHÁN GIẢ** — đạo diễn PHẢI làm theo 4 luật
     trong khối đó (đan X vào hook/beat chêm, neo bối cảnh chương, không ép vào beat có
     thực thể phải kể). MO_TA_VAN_HANH_BOOST.md.
4. **Tự đạo diễn** — outline trước, rồi beats **từng chương một** (đối chiếu foundation) →
   viết `<project_dir>/director_draft.json` ĐÚNG schema hiện có (`director/schema.py`, không sửa):
   ```json
   { "outline": { "tone": ..., "motifs": [...], "chapters": [ChapterPlan...] },
     "chapters": [ { "chapter_id": 1, "beats": [BeatDraft...] } ] }
   ```
5. `uv run autoedit direct-ingest <project_dir>` — máy gác toàn bộ luật cứng.
   **Có lỗi → draft bị TRẢ VỀ kèm danh sách (chưa ghi gì):** đọc lỗi, sửa ĐÚNG chỗ trong
   `director_draft.json`, nộp lại. Lặp tới khi pass (1–2 vòng là bình thường).
6. Pass → đọc `<project_dir>/beats.json` → **tóm tắt gọn cho editor**: số chương + tên, tổng
   beat, từng beat (thoại ngắn · visual_concept · shot_size · sourcing_route · overlay/card/
   chart nếu có) + các `⚠ warnings`. Video 0 info_card là DẤU HIỆU BẤT THƯỜNG — soi lại
   block CÔNG CỤ HÌNH trước khi nộp editor.
7. **HỎI editor: "Duyệt để dựng tiếp, hay chỉnh gì?" → DỪNG, chờ trả lời.** KHÔNG tự sang Pha 2.

### Foundation quản Ý — bảng ràng buộc quản SỐ (luật chống vênh, BẮT BUỘC)
Foundation nói "số chỉ là ví dụ" — đúng, nhưng máy gác bằng số CỨNG trong bảng của
`direct_context.md`. **TUÂN SỐ trong bảng; foundation chỉ định hướng nghĩa/nhịp.**
Hai chỗ dễ vênh nhất:
- Muốn nhịp cắt NHANH → dùng `shot_count` 2–3, **KHÔNG đẻ beat <1.5s** (máy sẽ gộp lại
  → ý đồ pacing mất).
- Hình thở: schema hiện tại = **1 số** `breathing_after_sec`; luật 2-pha [min–max] của
  d2 **CHƯA code** — đừng làm theo phần đó. Chỉ đặt thở ở từ kết câu mà voice có nghỉ
  thật ≥0.3s (đặt sai chỗ ingest trả lỗi kèm gợi ý từ có nghỉ thật — sửa theo gợi ý).

### Fan-out chương dài — block SCHEMA BẮT BUỘC (bug DS5-083 + DS3-084)
Video dài (chương >~424 từ timeout `direct`) → tự đạo diễn bằng **fan-out agent
mỗi-chương**. **Spawn agent với `model: "sonnet"`** (TOC 2026-07-15: khớp bảng provider
CLAUDE.md §5 — đạo diễn = Claude Sonnet, cùng model đường `direct` CLI; không thừa kế
model phiên hội thoại đắt hơn, chất lượng beat không đổi vì normalizer + direct-ingest
vẫn gác đủ). Prompt dispatch cho TỪNG agent PHẢI chứa block "SCHEMA BẮT BUỘC" liệt kê
đủ enum/bool/key của `BeatDraft`, và **BẮT BUỘC kèm ví dụ `overlays` nguyên văn dạng dict**
— DS3-084 thiếu ví dụ này, 6 agent trả chuỗi trần (`"overlays": ["2 wombs"]`) → mất
TRẮNG 25 overlay trên draft:
```json
"overlays": [{"text": "50 → 2", "kind": "stat", "anchor_word": 187, "duration_sec": 2.0}]
```
(`kind` ∈ price|keyword|stat|list_item|name|place|quote; `anchor_word` = word index TOÀN CỤC
trong beat; KHÔNG BAO GIỜ trả chuỗi trần.) Và **BẮT BUỘC kèm ví dụ `info_card` nguyên văn**
— 3 bài fan-out đầu (DS5-083/DS3-084/SP1-017) ra 0 card vì dispatch không nhắc gì:
```json
"info_card": {"title": "Vì sao mẹ nhịn ăn", "bullets": ["Bảo vệ phôi khỏi dịch vị", "Dồn năng lượng cho con", "Kéo dài 9-12 tháng"]}
```
kèm 1 dòng nhắc: mỗi chương NÊN có ≥1 `info_card` HOẶC `graphic_spec` (luật đầy đủ = block
CÔNG CỤ HÌNH trong `direct_context.md`). **BẮT BUỘC kèm dòng TEMPO của chương đó** (TEMPO
MAP 2026-07-14 — agent con mù tempo map toàn cục): vai hồi + `tempo_curve` + cách thực thi, vd:
```
TEMPO: chương 4/9 — giữa hồi 2, tempo_curve "build": beat NGẮN DẦN về cuối chương
(vẫn ≥1.5s), đoạn dồn dùng shot_count 2-3, kết chương KHÔNG hình thở (chương 5 mở dense).
```
Script gộp chương → dùng template
`projects/ds3-084-womb-cannibalism-20260713-224919/assemble_director_draft.py` (đã có
coerce drift + đếm `coerce/DROPPED` — mọi normalizer mới PHẢI in số drop, cấm loại êm).

### Luật NICHE-ANCHOR (bug SP1-014, user chốt 2026-07-11)
Content nói về **máy móc / quy trình / thiết kế của chủ thể niche** (thiết kế tàu, lắp ráp
tên lửa, nhà máy…) → `visual_concept` PHẢI neo chủ thể thật của niche ("SLS core stage
welding", "Orion capsule assembly cleanroom" — KHÔNG "engineering blueprints on a table",
"factory workers" trần trụi), kèm `entity_queries` khi có TÊN RIÊNG (Saturn V, SLS,
Michoud). Bằng chứng: pool 100% Pexels generic ở 12 beat trong khi kho có 61 cảnh Artemis
assembly. **HẾT ngoại lệ ẩn dụ (lỗi "bán thuốc", user chốt 2026-07-13 sau DS5-083 Jenga):**
script tự ví von/ẩn dụ/nói-với-người-xem → VOICE kể ẩn dụ, HÌNH kể tiếp câu chuyện —
`visual_concept` Ở LẠI thế giới central_subject, diễn ẩn dụ bằng hình trong thế giới đó
(Jenga → rạn tầng tầng loài, "rút khối" → cá mập biến khỏi khung hình); chỉ rời thế giới
chủ đề khi content nói thực thể/sự kiện THẬT (khối luật đầy đủ tự sinh trong
`direct_context.md`; direct-ingest in "⚠ nghi bán thuốc" — soi tay từng beat đó,
false-positive chấp nhận được).
`search_queries.local`: đừng để rỗng chỉ vì từ không nằm trong top-30 TỪ VỰNG KHO — bảng
đó cắt theo tần suất, từ ngách (assembly, cleanroom…) có thể vẫn có hàng; cứ điền 1 query
DANH TỪ CẢNH sát nghĩa, trượt cũng không mất gì (phễu vẫn có Pexels).

## VÒNG CHỈNH (khi editor góp ý — phần cốt lõi của Level 2)
- Diễn giải góp ý ("hook thiếu punch", "beat 7 sai chủ thể") → đối chiếu foundation liên quan
  → sửa **ĐÚNG beat đó** trong `director_draft.json` — KHÔNG dựng lại cả video.
- `uv run autoedit direct-ingest <project_dir>` lại → tóm tắt **diff** cho editor
  ("chỉ beat 7 đổi, còn lại giữ nguyên") → hỏi duyệt. Lặp tới khi editor OK.
- Chỗ editor sửa + lý do: ghi nhận lại trong hội thoại (nguồn học cho Phase B/L1 sau).

## Đường CŨ (fallback, không xóa)
`uv run autoedit direct <project_dir>` — prompt cứng + subprocess, chỉnh qua `inputs.brief`
rồi chạy lại. Dùng khi cần chạy nhanh không cần foundation, hoặc đường sâu trục trặc.

## PHA 2 — dựng draft CapCut (chậm, tốn footage)
Chỉ chạy KHI editor đã duyệt:
1. `uv run autoedit cut <project_dir>`
2. `uv run autoedit source <project_dir>`     — tải footage (Pexels/entity), cần key trong `.env`
   - Bài có **video mẫu** (mẻ đã TỰ nạp theo LUẬT TỰ NẠP ở trên) → thêm
     `--ref "<folder video mẫu>"` (vd `--ref "F:\SPACE\VIDEO MAU\SP1-014"`): cảnh nguồn mẫu
     được chèn pool + bonus phễu + trần viral 15% thay 8%. Khai 1 lần, dính vào project.json.
     REF chỉ có tác dụng khi mẻ mẫu ĐÃ nằm trong sổ — chưa nạp là --ref chạy rỗng không báo lỗi.
     Folder mẫu có folder con `Chapter N` → tự scope ưu tiên theo chương (REF THEO CHƯƠNG
     ở trên); kiểm dòng warning `REF theo chương (mềm): ch1=…, chung=…` đầu stage source.
   - **Thứ tự bắt buộc (bug SP1-014):** mẻ `library-ingest` của bài phải XONG **trước**
     `direct-context` — khối TỪ VỰNG KHO chụp kho tại thời điểm sinh context, ingest sau
     là đạo diễn nhìn từ vựng cũ. Ingest xong muộn → chạy lại `direct-context` rồi mới đạo diễn.
   - **BOOST đã khai ở PHA 1 tự dính** (project.json) — source tự chèn cảnh X kho + bonus,
     cuối stage in dòng `BOOST tầng ĐO: n/N beat lead match` → 0/thấp bất thường = term
     chưa theo từ vựng kho hoặc kho thiếu cảnh X, báo editor.
3. `uv run autoedit assemble <project_dir>`    — sinh draft CapCut trên khung donor
   - Editor muốn **ghi công kênh nguồn** → thêm `--credit`: tên kênh (cột `source_channel`
     trong sổ) hiện ở 1 trong 4 góc màn hình theo từng miếng footage. Cần kho ĐÃ điền kênh
     (`--channel` lúc nạp / `channel-set`) — chưa điền thì --credit chỉ ra warning, vô hại.
   - **2 công tắc SFX (2026-07-18) — CẢ HAI MẶC ĐỊNH TẮT.** ĐỪNG tự hỏi editor có muốn
     bật không; chỉ bật khi editor CHỦ ĐỘNG yêu cầu:
     · `--epidemic` — BẬT SFX nguồn Epidemic cho lần dựng này (kho vẫn giữ file, không
       gõ cờ chỉ là không chọn tới). Mặc định TẮT — user chốt.
     · `--sfx-llm` — NÃO chấm tiếng cho cảnh bảng luật MÙ CHỮ (subject viết chữ tự do như
       "Omani village" — cảnh phố thật mà không từ khóa nào lọt bảng, mặc định để im).
       Tốn ~1 lượt gọi NÃO/bài, lỗi mạng tự bỏ qua không chặn dựng.
     **Cách mời dùng (user chốt): ĐỪNG hỏi TRƯỚC khi dựng** — editor chưa thấy gì thì
     không quyết được. Dựng xong, nếu report cho thấy NHIỀU beat im tiếng chủ thể thì mới
     nói SỐ THẬT rồi hỏi: *"bài này N/M beat không có tiếng nền — muốn tôi bật AI chấm
     rồi dựng lại không?"* (assemble lại rẻ, không phải chạy lại source).
4. `uv run autoedit report <project_dir>`
5. Báo editor: **đường dẫn draft CapCut** + **report.html**. Nhắc mở CapCut kiểm (preview
   không đen, không đòi relink) rồi tinh chỉnh 20% cuối.

## Nguyên tắc buồng lái
- KHÔNG tự quyết thay editor ở cổng duyệt — luôn để editor xem beat trước Pha 2.
- Phiên chỉ trả word index/concept — mọi timestamp do ống tính từ alignment (NT4).
- Ingest báo lỗi → đó là vòng hội thoại bình thường, sửa draft rồi nộp lại; đừng bỏ qua.
- Nếu 1 stage lỗi: đọc thông báo lỗi, nêu cho editor, đề xuất cách xử; đừng bỏ qua âm thầm.
- Resume được: nếu đứt giữa chừng, chạy lại từ stage lỗi (project.json nhớ stage đã xong).
