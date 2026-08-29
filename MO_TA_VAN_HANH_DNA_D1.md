# MÔ TẢ VẬN HÀNH — NỐI SỐ DNA VÀO d1 PACING (consumer DNA đầu tiên)

> **TRẠNG THÁI: ✅ ĐÃ DUYỆT 2026-07-07 — 4 câu hỏi §5 đã chốt (câu 1-2 user trả lời,
> câu 3-4 user ủy quyền Claude quyết). Đợt code 1 = §2a + Mảnh B ✅ ĐÓNG (cổng mắt
> 2026-07-08). Mảnh A: §6 user DUYỆT (kèm điểm lệch §6b) + ✅ CODE XONG 2026-07-08
> (pytest 286/286, smoke OK) — ⏸ cổng mắt đi ké video mới fresh direct.**
> **Điều kiện kích hoạt đề xuất: kho space ≥3 draft** (DNA hiện từ n=1 draft SP1 - 003 —
> mọi con số trong đây là PLACEHOLDER minh họa, chốt số khi đủ mẫu).
> Nguồn: foundation `d1-pacing.md` phần 5 + backlog mục 2 · số đo `PB5_DNA_SPACE.txt`.

---

## 1. Mục tiêu

DNA niche (PB5 đo được, đang nằm chết trong bảng đọc tay) bắt đầu LÀM VIỆC ở 2 chỗ mà
foundation d1 đã định danh sẵn:

- **Mảnh A — NÃO đọc DNA trước khi direct:** direct-context (L2b sâu) nạp thêm chữ ký
  pacing của niche → NÃO chọn độ dài beat / shot_count / chỗ hold ĐÚNG CHUẨN NICHE thay
  vì heuristic chung.
- **Mảnh B — pacing validator sau direct:** thống kê phân bố độ dài shot của video vừa
  dựng, SO với DNA niche → **CẢNH BÁO trong report, KHÔNG CHẶN** (luật
  filter-overload-guard: không đẻ cửa loại mới).

## 2. Cách chạy

### 2a. DNA ghi file máy-đọc (điều kiện chung cho A+B)
- `library-dna` thêm bước cuối: ghi `~\AutoEdit\library\<niche>\dna.json` (chính dict
  `compute_dna` trả về + ngày đo + danh sách draft nguồn). Vì sao ghi file: lúc dựng
  video, draft nguồn (ổ E:) có thể không cắm — DNA phải sống độc lập trong thư viện.
- Đây là mục "còn ngỏ (4)" của §PB5 — kích hoạt đúng lúc có consumer đầu tiên.

### 2b. Mảnh A — nạp vào direct-context (L2b sâu)
- Khi dựng video có `--niche` và tồn tại `dna.json`: direct-context chèn 1 khối
  "CHỮ KÝ PACING NICHE <x> (đo từ N draft)" gồm 5-7 con số đọc được: cut/phút, trung vị
  + lệch chuẩn shot, % hold ≥5s, shot 45s đầu, ô thở/phút + trung vị. KHÔNG chèn cả bảng.
- Không có dna.json → không chèn gì, direct chạy y như hôm nay (fail-open).

### 2c. Mảnh B — pacing validator (code nhỏ, chỉ đọc project.json + dna.json)
- Sau assemble, đo các shot thật của video vừa dựng rồi so 2 tín hiệu với DNA:
  (i) **đều tăm tắp**: lệch chuẩn shot < ½ lệch chuẩn DNA (placeholder — space: 3,11s/2)
  (ii) **mật độ lệch**: cut/phút ra ngoài [½×, 2×] DNA (placeholder — space 8,3 → [4,2; 16,6])
- Kết quả = 1-2 dòng cảnh báo trong report.html + project.json. KHÔNG fail pipeline.

## 3. RÀ CHỒNG CHÉO (P5) — pacing hiện có 5 tầng cùng quản

| Tầng đang quản pacing | Luật mới có ngược chiều? | Ai lật ai âm thầm? |
|---|---|---|
| `director/prompts.py` pass 1-2 (sóng, beat 2-8s nghịch energy) | **CÓ 1 MÂU THUẪN THẬT phải chốt:** heuristic chung nói "hook nhanh" nhưng DNA space đo hook shot DÀI HƠN (8,75s vs 6,98s toàn video). Đề xuất: khối DNA ghi rõ "số đo thật của niche NÀY thắng heuristic chung khi vênh" — đúng chữ foundation d1 §2 "phải xem DNA trước khi dựng". *(CẬP NHẬT PB9 2026-07-07: DNA 3-draft đo lại hook trung vị **4,8s (n=25)** — NHANH hơn thân, mâu thuẫn TỰ TAN; số 8,75s cũ là mẫu mỏng n=6. Luật "DNA niche thắng" user đã chốt VẪN GIỮ cho các lần vênh sau.)* | NÃO vẫn quyết cuối (Level 2); DNA chỉ là tri thức thêm, không sửa prompt cứng |
| L2b sâu direct-context (12 foundation) | không — DNA là khối tri thức thứ 13, cùng cơ chế | không |
| `director/validator.py` (beat hợp lệ) | không — validator mới CHỈ cảnh báo, không thêm cửa chặn | validator cũ vẫn chặn lỗi cấu trúc như cũ |
| Phễu c5 + shot_count F6 (`MIN_SHOT_DUR`, clamp) | không đổi 1 dòng — DNA không đụng phễu | phễu vẫn có thể chọn clip làm shot dài/ngắn hơn NÃO xin → validator B đo SAU assemble nên bắt được cả lệch này (đúng vai trò) |
| `cutter`/assembler (timestamp từ alignment, NT4) | không — DNA không bao giờ sinh timestamp | không |

## 4. Cổng kiểm (P4)

- pytest: dna.json ghi/đọc round-trip · direct-context có/không dna.json · validator 2
  tín hiệu (case đều tăm tắp + case mật độ lệch + case sạch không cảnh báo).
- Cổng mắt user: dựng 1 video space thật → đọc khối DNA trong direct-context log + 2 dòng
  cảnh báo trong report — user phán "số này giúp hay nhiễu".

## 5. CÂU HỎI CHỐT CHO USER (trả lời rồi mới code)

1. Kích hoạt khi kho space đủ **3 draft** hay đợi 5? (đề xuất: 3 — đủ thấy số nào ổn định)
   → ✅ **USER CHỐT 2026-07-07: kích hoạt khi đủ 3 draft.**
2. Khi DNA vênh heuristic chung (vụ hook ở §3): đồng ý luật **"số đo thật của niche thắng"**?
   → ✅ **USER CHỐT 2026-07-07: đồng ý — DNA của niche thắng heuristic chung.**
3. Mảnh B ngưỡng cảnh báo dùng placeholder ở §2c hay anh muốn số khác?
   → ✅ **CHỐT 2026-07-07 (user ủy quyền Claude quyết): GIỮ ngưỡng §2c** — cảnh báo chỉ là
   chữ trong report, đặt lỏng trước, siết/nới sau khi dựng video space thật (đổi 1 hằng số).
4. Làm cả A+B một đợt, hay B trước (nhỏ, 0 rủi ro chồng chéo) rồi A sau?
   → ✅ **CHỐT 2026-07-07 (user ủy quyền Claude quyết): B TRƯỚC, A SAU.** Đợt 1 = §2a
   (dna.json) + Mảnh B validator (chỉ đọc, 0 chồng chéo). Mảnh A (đụng prompt NÃO) làm đợt
   riêng sau khi B qua cổng mắt + có dna.json 3-draft thật.

---

## 6. MẢNH A — CHI TIẾT THI CÔNG (viết 2026-07-08, cả 2 điều kiện kích hoạt đã đạt)

> Điều kiện §5.4 đã đủ: Mảnh B qua cổng mắt (SPACE-E2E, user duyệt 2026-07-08) +
> dna.json 3-draft thật (PB9, đo 2026-07-07: SP1-001/003/004, 82,6 phút, 643 shot).
> Khung §2b đã duyệt — mục này chỉ chốt CÁI GÌ in ra, CHÈN Ở ĐÂU, và 1 ĐIỂM LỆCH
> so với §2b cần user gật.

### 6a. Khối chèn vào direct_context.md — "CHỮ KÝ PACING NICHE"

Hàm mới `dna_block(niche, library_root=None)` trong `director/live.py`, **cùng khuôn
`vocab_block` của C4**: in LIVE từ `<library>/<niche>/dna.json` (qua `load_dna` có sẵn —
tự cập nhật sau mỗi lần `library-dna` chạy lại), fail-open 3 nấc (không niche / không
dna.json / JSON hỏng → trả `""`, context y như hôm nay). Chèn trong `build_direct_context`
NGAY SAU khối TỪ VỰNG KHO, trước "## OUTPUT". **0 đổi CLI** — `direct-context --niche`
đã có từ C4, dùng chung `eff_niche`.

Nội dung khối (số dưới = số THẬT space hiện tại, in động):

```
## CHỮ KÝ PACING NICHE 'space' (DNA đo từ 3 draft editor — 82,6 phút · 643 shot)

Số đo THẬT của niche — khi vênh heuristic chung, số này THẮNG (luật đã chốt 2026-07-07).
Dùng khi chọn độ dài beat + shot_count (shot con ≈ trung vị shot). KHÔNG chỉnh hình thở
theo khối này — nhịp nghỉ đã có lớp máy lo riêng theo DNA nghỉ của editor.

- Mật độ cắt: 9,4 cut/phút (validator sau assemble cảnh báo nếu ra ngoài [4,7; 18,8])
- Độ dài shot: trung vị 6,2s · lệch chuẩn 3,1s — xen kẽ dài/ngắn, đừng đều tăm tắp
- Hold ≥5s: 67% số shot, trung vị 7,5s — niche này KHÔNG ngại shot dài
- Hook 45s đầu: trung vị 4,8s — cắt NHANH hơn thân
```

4 dòng số + 3 câu luật. KHÔNG chèn cả bảng by_quarter/shot_grammar (P2 — NÃO không có
chỗ dùng: BeatDraft không chọn cỡ cảnh).

### 6b. MỘT ĐIỂM LỆCH so với §2b đã duyệt — cần user gật

§2b (viết 2026-07-07) liệt kê cả "**ô thở/phút + trung vị**" trong khối. Nay đề xuất **BỎ
dòng ô thở**, vì phát hiện khi rà chồng chéo (P5): DNA đếm ô thở = MỌI khoảng voice trống
≥1s (1,81 ô/phút thoại, trung vị 1,55s — phần lớn là vi nghỉ kết câu), trong khi:

- **Vi nghỉ** đã do máy hình thở 3.0 TỰ giãn theo pause_dna.json (quantile mapping, đóng
  cổng TAI 2026-07-08) — NÃO không cần và không nên can thiệp;
- **Ô thở chủ động** (breathing_after_sec) đã có luật "ÍT nhưng SÂU ~1 ô/45-90s" trong
  BẢNG RÀNG BUỘC CỨNG ngay phía trên khối này.

In "1,81 ô/phút" cho NÃO đọc sẽ NGƯỢC CHIỀU luật "ÍT nhưng SÂU" (xúi đặt gần 2 ô/phút —
gấp ~2 lần luật) — đúng loại mâu thuẫn 2-tầng-cùng-quản mà P5 bắt phải chặn từ mô tả.
Thay bằng 1 câu cấm rõ trong khối (đã có ở 6a): "KHÔNG chỉnh hình thở theo khối này."

### 6c. Rà chồng chéo Mảnh A (cập nhật bảng §3 với hiện trạng 2026-07-08)

| Tầng | Đụng? |
|---|---|
| BẢNG RÀNG BUỘC CỨNG (hình thở ÍT nhưng SÂU) | **đã xử lý ở 6b** — bỏ dòng ô thở + câu cấm |
| Máy hình thở 3.0 / shot thở 2.0 (pause_dna, ô 4,5-10,5s) | không — khối không nói gì về nghỉ/ô thở |
| Validator Mảnh B (check_pacing sau assemble) | CÙNG CHIỀU, cùng đọc 1 dna.json: NÃO được lái TRƯỚC bằng đúng số mà validator đo SAU — khối còn ghi rõ ngưỡng cảnh báo để NÃO biết máy sẽ soi gì |
| Khối TỪ VỰNG KHO (C4) | độc lập, đứng cạnh nhau, fail-open riêng từng khối |
| Đường `autoedit direct` cũ (prompts.py) | không đụng — vẫn thiếu cả vocab lẫn DNA (còn ngỏ đã ghi từ C4, chung số phận fallback L1) |
| Phễu c5 / shot_count F6 / cutter NT4 | không đổi 1 dòng — DNA không sinh timestamp, không đụng phễu |

### 6d. Cổng kiểm (P4)

- **pytest** (~3 test mới): `dna_block` in đủ 4 dòng số từ dict mẫu · fail-open 3 nấc ·
  `build_direct_context` chứa cả 2 khối đúng thứ tự (vocab → DNA → OUTPUT). Chạy FULL suite.
- **Cổng mắt**: đi ké video MỚI (việc 3) — user đọc khối trong direct_context.md + xem
  video ra, phán "số này giúp hay nhiễu". Claude không tự báo đạt.
