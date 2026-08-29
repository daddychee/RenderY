# MÔ TẢ VẬN HÀNH — TEMPO MAP (nhịp độ theo cấu trúc hồi)

> Nguồn: feedback đạo diễn hình ảnh 2026-07-14 ("LLM nhận cấu trúc 3 hồi từng chương →
> đặt rule nhịp theo hồi, hoặc bắt LLM đề xuất shuffle tempo để video không đều đều").
> User duyệt hướng 2026-07-14: làm Tầng 1 + Tầng 2; Tầng 3 (nhịp effect/graphic/transition)
> ĐỂ SAU. Hook chương 1 GIỮ luật nhanh hiện có (không áp "mở đầu chậm rãi" cho hook).
> Trạng thái: ✅ **ĐÃ CODE 2026-07-14** (user chốt "tự suy nghĩ và code, tính toán kỹ"):
> Tầng 1 (`ChapterPlan.tempo_curve` + block TEMPO MAP direct_context + SKILL dispatch +
> prompts đường cũ + d1-pacing) commit `4aeadfc`; Tầng 2 (`check_tempo_map` warning-only
> cả 2 đường direct) cùng commit; DRIVE SCORE nhạc (§3 sửa thiết kế — xem dưới) commit
> `c13b020`. pytest 508/508.
> **CỔNG TAI NHẠC (DRIVE SCORE): ✅ user DUYỆT 2026-07-14** — dựng lại DS3-084 chỉ rerun
> music+assemble (footage/overlay _V5 giữ nguyên) → draft `..._V6`, 6/6 chương đổi bài
> (4/6 từ mẻ NHỊP NHANH), user nghe "đã ổn".
> **CỔNG MẮT tempo_curve: 🔄 CÒN CHỜ video sâu DỰNG MỚI** — outline DS3-084 cũ chưa có
> tempo_curve (6 chương đều energy "medium") nên bản _V6 KHÔNG kiểm được phần curve.
> N2 (đổi nhạc theo đoạn tempo trong chương) CHƯA code — làm sau khi tempo map qua cổng mắt.
>
> 📌 **LỆCH SO VỚI MÔ TẢ GỐC (§3, phát hiện khi hiệu chuẩn 2026-07-14):** kế hoạch gốc
> "N0 kiểm thang energy bằng tai" đã được TRẢ LỜI BẰNG SỐ khi nạp 29 bài NHỊP NHANH:
> energy librosa = `rms.mean/rms.max` (độ PHẲNG) — 29 bài user tuyển tai đo 0 bài high,
> nhạc punchy điểm THẤP hơn drone. KHÔNG hiệu chuẩn lại thang energy nữa; thay hẳn bằng
> DRIVE SCORE khi chọn bài: mood 0.6 (tai người gán) + beat_tier 0.25 (nhịp rõ) + bpm 0.15
> (yếu nhất, đã gấp về [70,150)) — và chấm bài TẠI ĐOẠN SẼ VÀO (`entry_intensity` từ
> energy_curve chuẩn-hóa-trong-bài, ý user: bpm đổi theo đoạn trong 1 bài). Bằng chứng
> hiệu chuẩn: không MỘT feature nhịp máy đo nào tách được dồn/êm (dreamy đo "beat" 118-145
> /phút vì librosa bám pulse ảo; bài dồn bị gấp nửa còn 69-85).

---

## 0. Vấn đề (vì sao video ra "đều đều" dù đã có luật sóng)

Luật "đường sóng dồn→thả→dồn" ĐÃ có chữ (foundation `d1-pacing` + prompts.py:284) nhưng:
1. **Fan-out agent mù cấu trúc hồi** — dispatch mỗi-chương chỉ có block SCHEMA, không có
   dòng nào nói "chương này là hồi mấy, tempo mục tiêu gì" → 6 agent mù nhau, mỗi agent
   ra nhịp trung bình an toàn → ghép lại phẳng (đúng bài học [[duong-sau-mu-luat-prompts-py]]).
2. **Trong chương không có luật nhịp theo vị trí** — mini-arc chỉ nói Ý (setup→payoff),
   không nói đoạn nào cắt nhanh/chậm.
3. **Không có cổng kiểm nhịp lúc nộp draft** — `check_pacing` chạy SAU assemble (footage
   đã tải, sửa đắt) và chỉ đo lệch chuẩn TOÀN video.

## 1. TẦNG 1 — TEMPO MAP (chỉ sửa context/SKILL/dispatch + 1 field schema, 0 code pipeline)

### NÃO khai tempo map ở bước outline
Mỗi chương trong outline khai thêm **`tempo_curve`** — đường nhịp trong chương, menu ĐÓNG
(enum chốt khi code, dự kiến 5 giá trị):

| curve | nghĩa (tương đối quanh trung vị DNA niche) |
|---|---|
| `slow_build_slow` | mở chậm → giữa dồn dần → kết thả (đúng nguyên văn ĐDHA — cho chương THÂN) |
| `build` | dồn dần đều tới cuối chương (chương dẫn vào cao trào) |
| `dense` | dày đặc gần suốt, kết bằng 1 hold (chương cao trào) |
| `fast_settle` | vào nhanh → lắng dần (chương HOOK, kế thừa luật hook nhanh hiện có) |
| `calm` | chậm đều, ít cắt (chương kết / chương lặng chủ đích) |

**Luật kèm (viết vào `direct_context.md` + `d1-pacing` phần 3, KHÔNG đẻ foundation mới):**
- **Shuffle chống đều:** không cho 3 chương liền kề cùng một curve; toàn video phải có
  ≥2 loại curve khác nhau (video ≥4 chương thì ≥3 loại).
- **Hook = `fast_settle` mặc định** — luật hook nhanh (DNA hook45) THẮNG, không áp
  slow-open của ĐDHA cho chương 1.
- Nhanh/chậm phát biểu TƯƠNG ĐỐI quanh trung vị shot DNA niche — không đẩy cả video
  ra ngoài ngưỡng [½; 2×] cut/phút của validator.
- Thực thi nhanh = beat ngắn (≥1.5s, máy gộp dưới sàn) + `shot_count` 2–3 khi beat đủ dài
  (sàn shot con ≥MIN_SHOT_DUR vẫn kẹp — nhắc lại trong dispatch).

### Dispatch fan-out kèm dòng tempo
Mỗi prompt agent-chương THÊM 2–3 dòng: *"Chương 4/9 — giữa hồi 2, `tempo_curve: build`:
beat ngắn dần về cuối chương, đoạn dồn dùng shot_count 2–3, KHÔNG đẻ beat <1.5s;
kết chương đặt 1 hình thở."* → ghim vào SKILL mục fan-out (cạnh block SCHEMA).

### Schema: 1 field optional
`ChapterPlan.tempo_curve: str = ""` (optional — đường cũ/draft cũ không gãy). Ingest
Tầng 2 đọc field này để kiểm khớp khai-vs-thực.

## 2. TẦNG 2 — CỔNG KIỂM TEMPO tại `direct-ingest` (code nhỏ, warning-only)

Ingest đã có alignment → tính được độ dài beat (giây) ngay khi nộp draft. Thêm 3 warning
(theo luật [[filter-overload-guard]]: KHÔNG chặn, chỉ cảnh báo — NÃO/editor sửa lúc còn rẻ):

1. **Tempo phẳng giữa chương:** trung vị độ dài beat của mọi chương xấp xỉ nhau
   (max/min < ~1.3) → "các chương cùng một nhịp — xem lại tempo map".
2. **Chương đều tăm tắp:** trong 1 chương, lệch chuẩn/trung vị độ dài beat < ngưỡng
   (~0.25, chốt khi code) → "chương X cắt đều — thiếu xen kẽ dài/ngắn".
3. **Khai một đằng làm một nẻo:** chương khai `build` nhưng nửa sau beat KHÔNG ngắn hơn
   nửa đầu (và tương tự cho từng curve) → "chương X khai build nhưng nhịp không dồn".

Cổng pytest: ≥1 test/warning tái hiện được (draft giả đều tăm tắp → phải kêu; draft có
sóng → im). `check_pacing` sau assemble GIỮ NGUYÊN (lưới cuối).

## 3. TẦNG NHẠC — trả lời "kho đủ dày để thiết kế pacing chưa?": **CHƯA đủ cho cao trào**

**Hiện trạng:** đổi nhạc theo CHƯƠNG, 1 bài/chương không lặp (`music/select.py`).
DS3-084 (19:38) = 6 chương = 6 bài (~3'16"/bài) — đúng cảm nhận "ít bài".

**Kho đo thật (music_index 128 bài):**
- ✅ tempo đủ dải: 25 slow / 40 medium / 49 medium_fast / 14 fast; 100% bài có section
  build/drop (vào nhạc đúng đoạn được); loopable 116.
- ❌ **energy: 0 bài "high"** (ngưỡng code >0.7; bài cao nhất đo 0.617; 108 low / 20 med)
  → chương `energy=high` KHÔNG BAO GIỜ có nhạc đúng năng lượng, chỉ chọn "đỡ tệ nhất".
- ⚠️ mood lệch tối (mysterious 33 · dreamy 31 · dark 21) — hợp deepsea/space; đuôi sáng
  mỏng (uplifting 6) → niche sáng (travel...) sẽ đói.

**Kế hoạch 3 nấc (N1 phải xong trước N2):**
- **N0 — kiểm thang energy (30 phút, cần tai user):** nghe 5 bài "dồn nhất theo tai" vs số
  energy trong index. 2 giả thuyết: kho thật sự thiếu nhạc dồn, HOẶC thang đo `analyze.py`
  lệch (nhạc nền vốn êm → cả kho dồn về low). Mốc tai > số đồng hồ (bài học M-LEVEL).
- **N1 — nạp 20–30 bài high-energy/fast** (+ đuôi sáng nếu sắp chạy niche sáng) qua
  `music-import`, qua cổng tai như quy trình nhạc hiện có.
- **N2 — đổi nhạc theo ĐOẠN TEMPO (code ống, làm SAU N1):** music plan nhận thêm ranh giới
  đoạn từ tempo map (ống dịch word index → giây — NT4 giữ nguyên, NÃO không sinh timestamp);
  trong chương có curve gãy khúc (vd `slow_build_slow`) được đổi bài tại điểm gãy; sàn độ
  dài đoạn nhạc ~60–90s (chống đổi nhạc loạn); crossfade + neo accent tái dùng nguyên từ
  music-sync. Không nạp kho trước mà code N2 = đổi nhạc dày nhưng toàn bài êm — vô nghĩa.

## 4. RÀ CHỒNG CHÉO (P5) — các tầng cùng quản nhịp

| Tầng hiện có | Quan hệ với tempo map | Kết luận |
|---|---|---|
| DNA niche (`dna_block`, số THẮNG heuristic) | curve phát biểu tương đối quanh trung vị DNA | cùng chiều — đã ghi luật ở §1 |
| Luật hook nhanh (hook45 + prompts) | ĐDHA nói "mở chậm" — NGƯỢC | đã chốt: hook giữ nhanh, curve `fast_settle` |
| Hình thở d2 / pause DNA (máy tự vi-nghỉ) | curve chậm cuối chương = chỗ NÃO đặt thở — cùng chiều; §6b vẫn cấm NÃO chỉnh thở theo số DNA | không đụng |
| Gộp beat <1.5s + sàn shot con MIN_SHOT_DUR | máy có thể ÂM THẦM kẹp ý đồ dồn của curve | nhắc lại 2 sàn trong dispatch; gate 3 (khai-vs-thực) sẽ lộ nếu bị kẹp |
| `check_pacing` sau assemble ([½;2×] cut/phút) | curve mạnh tay vẫn giữ trung bình toàn video trong ngưỡng | không đụng, giữ làm lưới cuối |
| Music-sync (M-VOL hook, snap accent, đổi-nhạc-neo-cut) | N2 thêm điểm đổi bài TRONG chương — điểm đổi vẫn neo cut như cũ | cùng chiều; N2 tái dùng cơ chế |
| Usage penalty nhạc (đa dạng giữa video) | N2 tăng số bài/video → tiêu kho nhanh hơn | thêm lý do phải N1 trước |

## 5. TẢI TOKEN NÃO — trả lời "có nhồi tiếp vào LLM đạo diễn không?": **có, nhưng ~<2%, và phần nặng đặt ở nơi khác**

| Mảnh | Đặt ở đâu | Tải thêm lên NÃO chính |
|---|---|---|
| Luật tempo map + menu curve | `direct_context.md` (~15 dòng ≈ 250–350 tok trên nền ~1.7k luật + 22.6k foundation) | <2% — nhỏ |
| Foundation | ghi vào `d1-pacing` ĐÃ trong 12 file phải đọc — KHÔNG đẻ file mới | 0 file thêm |
| Dòng tempo per-chương | dispatch fan-out — context RIÊNG của agent con | 0 |
| Cổng kiểm Tầng 2 | Python thuần trong ingest | 0 token — máy gác thay vì nhồi luật |
| Việc nghĩ thêm | NÃO sinh ~10 dòng tempo map ở outline | 1 việc nhỏ, chạy 1 lần/video |

**Rủi ro thật cần canh:** NÃO chính vốn đã nặng (audit 22.6k tok, đồng hồ token mù).
Trigger đã chốt trong backlog [[duong-sau-mu-luat-prompts-py]] giữ nguyên: video sâu mới
mà rơi lệnh → dừng, làm đợt rà foundation + đồng hồ token TRƯỚC khi thêm gì nữa.

## 6. CỔNG KIỂM (P4)

1. **pytest:** ≥3 test cho 3 warning Tầng 2 (tái hiện draft đều → kêu; draft sóng → im) +
   full suite.
2. **Cổng mắt:** video sâu kế tiếp dựng với tempo map — user xem draft trả lời 1 câu:
   "có cảm thấy nhịp đổi theo đoạn không?". Claude KHÔNG tự báo đạt.
3. **Cổng tai nhạc (N1):** như quy trình nhạc hiện có.
