# MÔ TẢ VẬN HÀNH — PHỄU c5 CHẤM BATCH (PA-1+2+3, 2026-07-07)

> 📌 **LỆCH SO VỚI BẢN GỐC (TOC, 2026-07-15):** `runner._prefetch_batch` đã thay bằng
> `_plan_chunks` + `_pump_rank` + `_resolve_rank` — CÙNG luật chia chunk, nhưng 3 call
> NÃO bay SONG SONG (lookahead) + id ứng viên trong prompt/verdict rút thành mã ngắn.
> Luật phễu (2 veto, sàn 3, điểm máy) và `rank_batch/rank_beat_prescored` KHÔNG đổi.
> Chi tiết + rà chồng chéo: `MO_TA_VAN_HANH_TOC_DO_SOURCE.md`.

> **TRẠNG THÁI: ✅ USER CHỐT 2026-07-07** ("làm luôn PA 1+2+3; chỉ dùng sonnet, tắt
> thinking, không model cao hơn") sau khi đo run thật video space: 1 call NÃO/beat =
> trung vị **65s/beat** → 112 beat ≈ 2 giờ, không scale cho video dài. Code cùng ngày,
> FULL pytest 245/245. Bổ sung cho `MO_TA_VAN_HANH_PHEU_C5.md` — luật phễu (2 veto,
> sàn 3, thứ tự nghĩa>mood>nhịp) KHÔNG đổi, chỉ đổi CÁCH GỌI bước CHẤM.

## 1. Số đo dẫn tới quyết định (45 call thật, video space 112 beat)

- Chu kỳ/beat: trung vị 65s (min 40 / max 103). Prompt chỉ ~4,5k ký tự — không phải lỗi prompt.
- Output trung vị **3.906 token/call** trong khi JSON verdict thật chỉ ~700-900 token
  → ~75% là thinking + mỗi call trả thêm phí khởi động node/cli.js.

## 2. Ba thay đổi

**PA-1 — batch ~10 beat/call** (`runner._prefetch_batch` + `funnel.rank_batch/rank_beat_prescored`
+ `BatchRankResponse` + `RANK_BATCH_SYSTEM`):
- Gom beat stock/local **LIỀN NHAU, CÙNG CHƯƠNG**, tối đa `RANK_BATCH_SIZE=10` → gather
  ứng viên từng beat → **1 call NÃO** trả verdict per-beat → cache; vòng chính tiêu thụ
  tuần tự qua `rank_beat_prescored` (điểm máy + sàn 3 + chọn — y đường cũ).
- Chuỗi Kuleshov c3: NÃO nhìn CẢ CHUỖI trong 1 call (prompt dặn "top-pick beat N là
  previous footage của beat N+1") — mạch liền hơn từng call mù. Ranh giới chunk truyền
  `prev_pick_note` thật của beat trước đó.
- Chunk cắt tại: đổi chương · beat route entity/graphic · đủ 10 beat. Chunk <2 beat →
  đường 1 call/beat cũ (không batch).

**PA-2 — tắt thinking + rút lý do** (`cc_client(thinking=False)` → env `MAX_THINKING_TOKENS=0`,
chỉ đường RANK; direct/enrich giữ thinking): prompt bắt `ly_do ≤12 từ`. Model: **sonnet
là trần** (user chốt — không opus cho phễu).

**PA-3 — pool ≤1 sau cửa kỹ thuật → auto-pick, 0 call** (`rank_beat`/`rank_beat_prescored`):
1 ứng viên thì chấm là vô nghĩa; ly_do ghi "(pool 1 — auto-pick, không gọi NÃO)". Pool 0
→ needs_human như cũ.

## 3. RÀ CHỒNG CHÉO (P5)

| Tầng cùng quản | Ngược chiều? | Ai lật ai âm thầm? |
|---|---|---|
| Luật cứng P7 chống lặp asset | không — pool chunk gather TRƯỚC nên beat sau có thể chứa asset beat trước vừa lấy → **vòng tải check `used_in_video` bỏ qua** (máy gác, KHÔNG tin LLM tự tránh; test `no_repeat_in_chunk`) | không |
| Veto hẹp 3 dạng + sàn 3 + điểm máy | không đổi 1 dòng — `_finish_scoring` dùng CHUNG cho per-beat lẫn batch (test bất biến: cùng verdict → cùng kết quả) | không |
| Chuỗi c3 + `prev_shot_size` điểm máy | prev_shot_size vẫn tính TUẦN TỰ lúc tiêu thụ (sau tải thật từng beat) — đúng như cũ. Vênh nhỏ chấp nhận: NÃO giả định top-pick của nó là "previous footage", còn máy có thể chọn khác (điểm máy/tải hỏng) — spread máy 2.0 < 1 điểm nghĩa nên hiếm lật | không |
| Kill-log / rank_log / cost | schema per-beat GIỮ NGUYÊN (report + phân tích kiểu PB8 không vỡ); token batch ghi vào beat ĐẦU chunk — tổng đúng | không |
| Đường fallback | batch call lỗi → cảnh báo + cả chunk về 1 call/beat; NÃO quên 1 beat trong response → chỉ beat đó về 1 call/beat. Đường cũ nguyên vẹn | không |
| Heuristic --no-rank / route entity/graphic | không đụng | không |

**Còn ngỏ chấp nhận:** pool beat sau trong chunk có thể cạn nếu beat trước tiêu
nhiều asset trùng — hiếm (pool ~10+), có needs_human đỡ.

**✅ VERIFY RUN THẬT (2026-07-07 22:05+):** `MAX_THINKING_TOKENS=0` ăn — output
~89–91 token/verdict (trước ~195, tức ~3,9k/call cho ~20 verdict) → gần thuần JSON.
`ly_do` trung vị 11 từ. Nhịp 20 beat đầu ≈ 30s/beat (gồm tải footage) vs 65s/beat cũ.

## 4. Cổng kiểm (P4)

- pytest FULL **245/245** (4 test mới: auto-pick 0 call · batch 1 call + bất biến
  batch=per-beat · pool nhỏ/NÃO quên · runner 3 beat 1 call + P7 chunk + token 1 lần).
- Cổng số run thật: 112 beat phải xong bước CHẤM trong ≤~15 call, output/call giảm rõ.
- Cổng mắt: chất lượng chọn footage soi ở draft CapCut (chung cổng mắt video space).
