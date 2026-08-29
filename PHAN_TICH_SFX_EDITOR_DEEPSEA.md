# PHÂN TÍCH — Sheet SFX editor deepsea ↔ kho asset trên máy (2026-07-13)

> Nguồn: user đưa Google Sheet 41 dòng "Hành động → SFX" editor thật dùng ở niche deepsea
> (https://docs.google.com/spreadsheets/d/1YaiUH6WByPLXBOpK_tcvd5bAEGQ_j01sZyY9Szce9JE).
> Mục tiêu: link từng SFX về nơi lưu trên máy → làm nền cho tính năng "SFX theo chủ thể
> mức LOÀI/HÀNH ĐỘNG" (nâng S2). **TRẠNG THÁI: USER DUYỆT A/B/C 2026-07-13 → Milestone A
> ĐÃ LÀM XONG cùng ngày (`MO_TA_VAN_HANH_SFX_LOAI.md`, pytest 481/481): kho nạp 28 file
> + re-kind 2, subject_rules.yaml per-niche chạy thật. Mật độ user chốt: thân bài = 50%
> hook (milestone C, chưa làm). Folder `D:\Sounds Edit` user sẽ copy sau.**

## 1. Kết quả link 41 dòng sheet (đối chiếu norm-name, script scratchpad match_sfx.py)

**Tổng: 31/41 có trên máy** (5 kho ambient + 5 SFX staging + 21 hold) **+ 3 trên đĩa
draft chưa nạp + ~8 thiếu thật** (nằm máy editor / NAS).

### 1a. Đã trong KHO ambient chính thức (`F:\AutoEdit\ambient\deepsea\`) — 5 dòng, đều bị gộp kind thô

| Hành động (sheet) | SFX | File kho | Kind hiện tại |
|---|---|---|---|
| Cá lớn lao lên mặt nước · phun nước mũi | Unrealsfx Marine Mammals — Whale Blowing Air Ocean Waves | `ocean_14.wav` (bản (1): `ocean_21.wav`) | ocean |
| Chim trên mặt biển | Sea wave seagull 11 / 15 | `ocean_23.wav` / `ocean_17.wav` | ocean |
| Bão, sóng biển | Unrealsfx Extreme Climate — Tsunami Waves | `rumble_3.wav` | rumble |

### 1b. Đã trong SFX STAGING (`C:\Users\NBPC\AutoEdit\sfx\tu_editor\`) — 5 dòng

Vồ/lao vào cắn: `Sound Surgeon - Alien Monster Whoosh 01/02.aac`, `JBoB - Screamy Sci fi
Whoosh Creature Flyby.aac` · Whoosh nước: `Whoosh water.aac`, `whoosh water 2.aac`.

### 1c. Trong HOLD chưa phân loại (`F:\AutoEdit\ambient\deepsea\raw\tu_editor_chua_phan_loai\`) — 21 dòng, **toàn bộ tiếng cá voi đắt nhất**

| Nhóm | File trong hold |
|---|---|
| Cá nhà táng (6) | `ANMLAqua-sperm_whale_clicking/-sonar/-Sperm_whale-Elevenlabs.mp3`, `cá nhà táng.mp3`, `cá nhà táng2.mp3`, `mã Morse.mp3` |
| Cá voi lưng gù (8) | `Céline Woodburn - Whale Cry Long/Cry/Sigh/Sign Deep.aac`, `tiếng kêu cá voi lưng gù.aac`, `Unrealsfx Humpback Distant Call/Song/Song Guttural Moans.aac` (+bonus ngoài sheet: `Whale Sonar.aac`) |
| Cá voi xanh (2) | `cá voi xanh kêu.aac`, `Artlist - Whale Call Distant.aac` |
| Mặt nước (5) | `Whale Surfacing Blowing Air Water Splash.aac`, `Killer_Whale_Blasts_Spout_Air_Bursts_OCP-1317-043-01.wav`, `Rơi xuống nước mạnh.aac`, `Selkor - Water Splash Bright.aac`, `vồ trên mặt nước.aac` |

### 1d. Có trên đĩa nhưng CHƯA nạp — 3 file

- `Artlist - Whale Call Low Pitch.aac` → `E:\PROJECT NHAN BAN\DEEP SEA 5\DS1_074\materials\` (draft Clip ghép — đã hoãn editor-learn)
- `Water Whoosh.aac` → `E:\PROJECT NHAN BAN\DEEP SEA 3\DS3_008\materials\`
- `dưới nước 4.aac` → bị classify NHẠC (>40s, `MUSIC_SEG_MIN_S=40`) → đang ở staging nhạc `F:\AutoEdit\music_editor\DS1_046\` chờ cổng tai; bản gốc trong `materials/` của 19 draft

### 1e. THIẾU thật trên máy này — 8 file (đường dẫn trong draft_meta_info trỏ máy editor/NAS)

| File | Path gốc (chết) |
|---|---|
| `tieng ca voi sat thu` + `tieng ca voi sat thu 1` | không thấy cả trong media pool — chắc máy editor |
| `Whale High Pitched Clicks.aac` · `Orca Underwater High Pitch Call.aac` (+bonus `Orca Underwater Moan.aac`) | `\\192.168.1.213\padoma 8\Project DS 3\Bài 7\CÁ VOI SÁT THỦ\` |
| `Phun nước.aac` · `Water Whoosh2.aac` | `D:\Sounds Edit\Deep sea\SFX\...` (ổ D máy editor) |
| `DB studios - Beach ocean waves atmosphere.aac` · `OG SoundFX - Big Ocean Wave.aac` | không rõ |

> 💡 **`D:\Sounds Edit\Deep sea\SFX\` = kho SFX master của editor** (nhiều path trỏ về đó).
> Xin editor copy nguyên folder này (+ folder NAS `CÁ VOI SÁT THỦ`) là vá hết phần thiếu,
> khỏi truy từng file.

## 2. Vì sao bài máy ít SFX hiện trường hơn editor — 3 nguyên nhân

1. **Kho có tiếng nhưng không dùng được:** 21/41 tiếng đắt nhất nằm hold (chưa kind);
   kind hiện tại sinh cho space (`SUBJECT_KINDS = fire/rocket/explosion/rumble/water/ocean/signal`,
   `ambient/library.py:32`) — mọi tiếng biển gộp `ocean` (27 file lẫn sóng vỗ + hải cẩu +
   cá voi thở) → beat orca không gọi được "tiếng orca".
2. **Trần S2 chặt cho cả video:** `SUBJ_CAP=6` tiếng/video, ≤2 lần/kind, không 2 beat kề
   (`ambient/schedule.py:39-40`) — editor làm DÀY ở hook + 3 phút đầu; máy không có khái
   niệm vị trí.
3. **Bảng từ khóa match thiếu từ vựng loài:** orca/humpback/sperm whale/breach/lunge...
   có trong tag GLM của kho 8.981 asset deepsea nhưng bảng match không nhận.

## 3. Phương án đề xuất (CHƯA CODE — chờ user chốt)

- **A — Nạp:** phân loại 21 hold + 3 file trên đĩa vào **kind mới mức loài/hành động**
  cho deepsea (vd `whale_sperm`, `whale_humpback`, `whale_blue`, `whale_orca`, `splash`,
  giữ `ocean` cho sóng/seagull). Sheet user = ground truth. `SUBJECT_KINDS` đang là tuple
  cứng → mở thành cấu hình theo niche (vd trong `niche_profile.yaml`). Xin editor folder
  `D:\Sounds Edit` vá 8 file thiếu.
- **B — Bảng hành động→tiếng thành DATA:** mã hóa sheet thành yaml per-niche
  (keywords vision EN → kind). Đây là đường "học từ editor" lặp lại được: niche mới =
  editor điền 1 sheet.
- **C — Mật độ theo vị trí:** hook+3′ đầu dày như editor; cả bài đặt theo match thật
  (chủ thể lên hình mới kêu), trần per-chapter thay per-video. Mức nới do cổng tai
  video kiểm quyết.

### Rà chồng chéo (P5)

- **C1 ambient ô thở** (`choose_files` ưu tiên subject-kind > scene_type > default):
  kind mới tự được ưu tiên ở ô thở → CÙNG CHIỀU, không sửa thêm.
- **S2 volume** SUBJECT_VOL 0.18 (voice) / 0.32 (ô thở) giữ nguyên; chỉ đổi TRẦN + TỪ VỰNG.
- **Music-sync M-VOL hook to (deepsea 0.30 chưa qua cổng tai):** hook vừa nhạc to vừa
  dày tiếng chủ thể → tầng có thể ÂM THẦM che nhau. PHẢI kiểm chung 1 cổng tai.
- **editor-learn classify** (`mine.py`): thêm kind mới phải thêm rule route tương ứng,
  không thì lần học sau hold lại phình đúng nhóm này.
- **Track sfx UI/overlay + drone S1 + portable/pack:** không đụng.

## 4. Việc còn ngỏ

- User chốt: danh sách kind loài · mật độ cả bài · xin editor folder `D:\Sounds Edit`.
- Hold còn ~300 file khác chưa phân loại (ngoài 21 file sheet) — sheet chỉ phủ phần cá voi/mặt nước.
