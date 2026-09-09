# LỘ TRÌNH 8 VẤN ĐỀ — user nêu 09/09/2026

> **Vì sao có file này:** user chốt *"công việc này sẽ rất dài và tốn thời gian nên
> tôi không muốn anh mắc sai lầm"*. Mỗi vấn đề giải quyết **từng cái một, hoặc cụm
> liên quan**. File này là sổ cái: hiện trạng đã ĐO, quyết định đã CHỐT, việc đã XONG.
>
> **Luật làm việc (user nhắc nhiều lần):** kiểm thử trước → trình bày → user duyệt →
> mới code. Không đoán, không tự quyết luật nghiệp vụ.

---

## Bảng 8 vấn đề

| # | Vấn đề | Hiện trạng | Đợt |
|---|---|---|---|
| 1 | Video Envato hỏng/không tải được | cơ chế CÓ, thủng 3 lỗ | **đang làm** |
| 2 | 17 chương → gộp 1 timeline | `merge-drafts` CÓ, thiếu nút web | — |
| 3 | Trùng clip xuyên chương | **chưa từng viết** | — |
| 4 | Nhạc mỗi chương 1 bài, ghép thế nào | 17 lần fade, chưa xử lý mối nối | — |
| 5 | Khối 5s / source 4s → tự chia | chưa có; preview loop gây hiểu nhầm | — |
| 6 | Voice trùm hơn 1 khối | voice KHÔNG trùm; khối thiếu trần dài | — |
| 7 | Kéo thả nhận video team tìm được | nền CÓ (`trim`), thiếu đường nhận file | — |
| 8 | Timeline Premiere | code CÓ, nút Export không gọi | — |

---

## VẤN ĐỀ 1 — Envato hỏng

### Đo thật 09/09/2026 (đọc DB, không sửa)

Kho `clip`:

| nguồn | trạng thái | số dòng | có file |
|---|---|---|---|
| ref | song | 8.263 | 8.263 |
| **envato** | **song** | **5.148** | **102** |
| pexels | song | 2.718 | 2.718 |
| ref | loai_tru | 517 | 517 |
| pixabay | song | 427 | 427 |
| kho | song | 64 | 64 |
| envato | loai_tru | 41 | 0 |
| envato | link_chet | 20 | 0 |

**Envato: 5.209 dòng, chỉ 102 có file thật (2%).** 94 dòng `giay_phep`, tất cả trỏ
vào clip CÓ file — không giấy phép nào trỏ clip rỗng.

Khay hợp đồng thật (33 chương trên production):

| | số |
|---|---|
| tổng ô khay | 13.270 |
| envato trong khay | 1.248 |
| **envato trong khay KHÔNG có file** | **892** |
| miếng đang được CHỌN | 928 |
| chọn envato | 94 |
| **chọn envato KHÔNG có file** | **43** |
| chọn envato đã `link_chet` | 9 |

### Ba lỗ (có file:line)

**Lỗ A — điều kiện đánh dấu hỏng không bao giờ đúng.**
`offline/thay_mau.py:185` kiểm `"không tồn tại" in str(exc)`. Không luồng nào ném
chuỗi đó; preview chết trả `"HTTP Error 404: Not Found"`. → clip 404 KHÔNG bị đánh
dấu, lần dựng sau lại chọn, lại hỏng, lặp mãi. Đây là lỗ làm hỏng luôn tác dụng của
cơ chế `link_chet` vốn đã có.

**Lỗ B — clip chết vẫn nằm trong khay đã lưu.**
`offline/dung.py:338` `_hong()` chỉ kiểm `nguon == "ref"`. Clip envato `link_chet`
nằm sẵn trong `uv[]` hợp đồng cũ không bị quét ra. **Đo thật: 9 miếng đang chọn clip
đã `link_chet`.**

**Lỗ C — lỗi mạng/timeout không ghi gì.**
`sourcer/tai_sach.py:230` bắt mọi exception rồi chỉ log. Không đếm lần, không ghi DB.

### XUNG ĐỘT phát hiện được khi kiểm (QUAN TRỌNG)

User đề xuất: *"không nên trữ video envato hd preview. Chỉ trữ video đã được sử dụng
vì đã download và có license"*.

**Xung đột 1 — 21 clip đã LÊN TIMELINE nhưng KHÔNG có file.**
Truy vấn `su_kien.loai='len_final'` giao với `path_local=''`: **21 clip**, thuộc các
tập `c1-20260908-112236`, `c3-20260907-050623`, `h-20260907-042837`,
`h-20260905-104130`, `h-20260908-114413` — tức **LI106 của Hải**.

Nghĩa là: chúng đã vào draft thật ở dạng **preview WATERMARK** (đường xuống cấp ở
`thay_mau.py:161-174`: bản sạch không có thì tải preview watermark + cảnh báo).
Luật "chỉ trữ cái đã tải + có license" mà áp thẳng sẽ **xoá mất dấu vết 21 clip đang
nằm trong timeline đã giao** → mở draft ra không còn tra được clip đó là gì, ở đâu,
license nào. Sổ nguồn gốc (`nguon_footage.json`) mất đối chiếu.

**Xung đột 2 — 43 miếng đang CHỌN clip envato không file.**
Xoá dòng là 43 miếng mất ứng viên đang chọn. Người dựng mở lại chương thấy khay đổi.

**Xung đột 3 — 892 ô khay sẽ rỗng đi.**
Không giết draft (khay chỉ là gợi ý) nhưng người dựng đang quen khay nào có gì.

**Xung đột 4 — 8 clip CÓ file nhưng KHÔNG có giấy phép.**
Luật "chỉ trữ cái có license" mà hiểu chặt sẽ xoá cả 8 clip đã tải thật. Cần phân
biệt "đã tải" và "có chứng từ" — hai điều kiện khác nhau.

### Yêu cầu user (09/09) + trạng thái kiểm

| # | User yêu cầu | Kiểm |
|---|---|---|
| 1a | Video chết xoá luôn khỏi khay | ✅ làm được, KHÔNG xung đột |
| 1b | Không trữ envato HD preview, chỉ trữ cái đã tải + có license | ⚠️ **xung đột 1-4** ở trên |
| 2 | Fail 1 lần bỏ qua luôn | ✅ làm được |
| 2b | Sau mỗi video người dựng chọn thì check sống/chết ngay | ✅ làm được, cần bàn cách (xem dưới) |
| 3 | Check thấy chết là gỡ luôn | ✅ cùng cơ chế 1a |

### Chưa chốt — chờ user

- Cách xử 21 clip đã lên timeline nhưng không file (giữ dòng? chuyển kho lưu trữ?).
- Check sống/chết ngay lúc chọn: chạy đồng bộ (chậm ~1-3s/lần bấm) hay chạy nền?
- 8 clip có file mà không giấy phép: giữ hay xoá?

---

## Nhật ký

- **09/09/2026** — Khảo sát 8 vấn đề bằng 4 agent đọc code + đo DB thật. Lập file này.
  Vấn đề 3 xác định: `tap` ở `sotra/tra.py:59-64` ép mọi chương cùng tập tra CÙNG một
  rổ ref → 17 chương giống nhau là tất yếu. Vấn đề 5: draft KHÔNG loop (xuống cấp
  0.9x → freeze), preview có `loop` cứng ở `web/static/index.html:778-779` và không mô
  phỏng speed/freeze. Vấn đề 6: voice bị kẹp cứng trong ô khối
  (`thay_mau.py:316-327`), không thể trùm; thứ trùm là dải HÌNH và là thiết kế user
  chốt 08/09. User chọn: vấn đề 3 dùng **trừ điểm nặng, không cấm hẳn**; vấn đề 5
  **chưa sửa, bàn thêm** (loop thấy trên preview, trong chính khối đó).

### Vòng 2 — user trả lời 09/09 + kiểm thử

**Ý 1 — placeholder có link + thông báo "tải tay".**
Máy móc ĐÃ CÓ: `packager/assembler.py:616` `_slug_image()` render ảnh 1920x1080 nền
tối, `_fill_holes_with_slug` (assembler.py:370) lấp mọi ô trống. Lý do bắt buộc phải
lấp: main track CapCut là track NAM CHÂM — để hở là CapCut tự dồn segment, mọi footage
sau lỗ lệch voice tích luỹ.
**NHƯNG đường Offline KHÔNG dùng nó**: `offline/thay_mau.py:188` chỉ ghi warning
`"KHÔNG lấy được nguồn nào — timeline hở, editor đắp"`, không đặt slug.
→ Việc cần làm: đường Offline gọi slug, và slug in được **link + câu hướng dẫn**
(hiện `_slug_image` chỉ vẽ chữ cố định "EDITOR: ĐẮP FOOTAGE Ở ĐÂY").

**Ý 2 — bấm Export thì check 1 lượt, có link chết thì CHẶN + tô đỏ.**
Điểm nối: `web/server.py:1183` `api_offline_thay_mau` — hiện bắn thẳng thread `_chay`.
Chèn bước kiểm TRƯỚC khi bắn thread, trả 409 kèm danh sách miếng hỏng để UI tô đỏ.
Đo thật: **9 miếng đang chọn clip đã `link_chet`** trên 33 chương production → chặn
được ngay 9 lỗi trước khi ráp.
Lưu ý: kiểm 43 miếng envato không file bằng HTTP mất ~1-3s/link → cần chạy song song
hoặc chỉ kiểm miếng ĐANG CHỌN (928 miếng toàn bộ, ~94 envato/chương thì rất nhanh).

**Ý 3 — user: "video lưu trữ do tool suggest cho từng khối chứ user không có công cụ
để tra cứu".**
KIỂM: **trang tra cứu ĐÃ CÓ** — menu "Library" (`index.html:475`, `man-sotra`
:676-720). Có: ô tìm gõ tiếng Việt được, lọc 7 nguồn, hover phát preview thật, nhãn
"đã dùng ở tập X", nhãn "+N bản", cờ ⚑ có neo, phân trang, nút "Hút thêm theo từ khóa".
Ảnh chết tự đánh dấu `link_chet` (index.html:2730-2733).
→ Không phải "không có công cụ". Cần user xem lại tab Library rồi nói **thiếu gì**.
Cái tôi thấy thiếu khi đọc code: từ Library **không kéo được clip vào khối đang dựng**
(`stMo` popup chỉ có xem + link gốc, index.html:2767-2783). Đây trùng với **vấn đề 7**.
→ Vấn đề 3 (lưu trữ) và vấn đề 7 (kéo thả) là MỘT CỤM.

**Chốt về xoá kho:** user nói *"nếu lưu trữ envato không mất quá nhiều dung lượng thì
cũng không cần phải xóa"*. 5.107 dòng rỗng chỉ là text trong SQLite (~vài MB), không
phải file. → **KHÔNG XOÁ**. Xung đột 1-4 ở trên tự tan.

### Vòng 3 — user phản biện 09/09 (ĐÚNG) + phát hiện lớn

**User phản biện: "không hề có nút hút thêm theo từ khóa này".**
KIỂM: nút CÓ trong HTML (`index.html:705`) nhưng ẩn theo HAI điều kiện
(`index.html:2698`): `ME.nghien_cuu_kenh` **VÀ** `ST_Q.trim()` khác rỗng.
→ Ô tìm trống thì nút không hiện. Ảnh user gửi ô tìm đang trống. User không sai.

**User chỉ ra lỗi thiết kế thật: tra cứu TÁCH KHỎI nơi sử dụng.**
Tab Library tra được nhưng dùng không được; tab Sequence dựng được nhưng tra không
được. Người dựng thấy clip hay ở Library thì phải nhớ tên, sang Sequence, tra lại.

#### PHÁT HIỆN LỚN: phương án 2 của user ĐÃ TỒN TẠI MỘT NỬA — nhưng bị CHẾT

`index.html:2148-2158` có sẵn `ofTimDebounce()`: gõ vào `#of-tim` → gọi
`/api/sotra?q=...&limit=40` → kết quả thay khay ứng viên của miếng đang chọn
(`index.html:2169-2172`, nhãn "N kq Library cho «...»").
`index.html:2222-2231` xử lý click: clip tra được **chèn thẳng vào đầu khay**
(`k.uv = [{...u, lop:'L2', diem:0}, ...]`), `k.chon = 0`, `nguoi_sua = true`.
Tức TOÀN BỘ logic "tra cứu ngay trong Sequence rồi dùng luôn" ĐÃ VIẾT XONG.

**Nhưng phần tử `#of-tim` KHÔNG TỒN TẠI trong HTML.** grep `of-tim`:
chỉ 3 chỗ, cả 3 đều là `getElementById` trong JS (2152, 2170, 2230). Không có
`<input id="of-tim">` nào. Mọi lời gọi đều `if (_oti)` / `if (_ot2)` nên **thất bại
âm thầm**, không báo lỗi. `OF_TIM_KQ` vĩnh viễn `null` → nhánh tra cứu chết.

→ Việc cần làm cho PA2 nhỏ hơn nhiều so với tưởng: **thêm ô input + nhãn vào giao
diện Sequence**, phần logic đã có sẵn và đã xử lý cả quyền (`OF_KHOA_SUA`),
autosave (`ofLuu`), chụp undo (`ofChup`).

#### So sánh 2 phương án user nêu

| | PA1 — kéo từ Library sang Sequence | PA2 — tra cứu + hút NGAY trong Sequence |
|---|---|---|
| Nền đã có | `trim` chèn khay (server.py:1281) | **logic hoàn chỉnh, thiếu mỗi ô input** |
| Việc phải làm | kéo-thả liên tab, giữ ngữ cảnh "khối nào đang mở" | thêm `<input id="of-tim">` + nhãn |
| Rủi ro | kéo-thả giữa 2 tab khó, phải nhớ khối đích | thấp |
| Đúng luồng làm việc | phải rời chỗ dựng | ở nguyên chỗ dựng |

→ **PA2 rẻ hơn hẳn và đúng như user nhận định "đây mới là logic hợp lý".**
Còn thiếu so với mô tả user: nút **HÚT THÊM** ngay trong Sequence (khi kho không có
gì) — cái này chưa có, phải làm mới; endpoint `/api/sotra/hut` đã sẵn.

**Chưa chốt:** nút Hút trong Sequence có nên giới hạn quyền như tab Library
(`nghien_cuu_kenh` = manager trở lên) hay mở cho người dựng (level 2)?

---

## CHI PHÍ 1 LƯỢT HÚT — đo thật 09/09/2026

Câu hỏi user: *"Chi phí của 1 lượt hút thêm là bao nhiêu?"*

### Một lượt hút gồm gì

`sotra/hut.py:130` `phien_hut(conn, tu_khoas, nguons, so_trang)` — vòng lặp
**từ khóa × nguồn × trang**, mỗi vòng 1 HTTP request rồi `sleep` ngẫu nhiên
`GIAN_NHIP = (2.5, 5.0)` giây (`hut.py:28`). Một luồng tuần tự (luật rón rén,
`hut.py:5-6`: bài học YouTube ~9 lượt bị chặn IP + Envato cấm tải song song).

Nút ở tab Library gửi `nguon: ['envato','pexels','pixabay'], so_trang: 1`
(`index.html:2793-2794`) → **3 request, ~10-15 giây**.

### Chi phí từng nguồn

| Nguồn | Cách lấy | Tiền | Hạn mức |
|---|---|---|---|
| **Envato** | scraping trang search công khai (`hut.py:39`) | **0đ** | không có hạn mức; rủi ro là bị chặn IP nếu dồn dập → đã có `GIAN_NHIP` |
| **Pexels** | API chính thức (`hut.py:80`) | **0đ** (free tier) | 200 req/giờ, 20.000/tháng |
| **Pixabay** | API chính thức (`hut.py:106`) | **0đ** (free tier) | 100 req/phút |

**KHÔNG có lượt LLM/GLM nào trong đường hút.** `hut.py:8` ghi rõ: *"Hút CHỈ lấy
metadata + URL — không tải file nào về"*. Tag sinh bằng `tag_tu_tieu_de` (regex thuần).

### Đo thật từ DB (bảng `phien_hut`, 32 lượt đã chạy 06/09)

| | |
|---|---|
| lượt đã chạy | 32 (toàn envato) |
| kết quả/lượt | **48,7 clip** |
| clip MỚI/lượt | **23,5** (phần còn lại trùng, `them_clip` tự upsert) |
| thời gian | 32 lượt trong ~3 phút → **~5,6 giây/lượt** |

### KẾT LUẬN CHI PHÍ

**Một lượt hút = 0 đồng, ~10-15 giây, đem về ~24 clip mới.** Nó KHÔNG giống
`nap-ref` (server.py:1670 — *"~5 phút/tập, tốn tiền LLM thật"*) và cũng không giống
`nhac/hut`. Ba thứ này đang dùng CHUNG một cửa quyền `_duoc_nghien_cuu_kenh`
(server.py:1618, 1678, 1739) nhưng chi phí khác nhau hoàn toàn.

→ Lý do ghi trong code để hạn chế quyền hút (*"đo tốn tải YouTube + lượt GLM"*,
server.py:128-129) **đúng cho `nap-ref`, SAI cho `hut`**. Đây là cùng loại lỗi đã sửa
09/09 với `LEVEL_DUNG_TOI_THIEU` (server.py:141-147): một cửa quyền viết cho việc A
bị dùng nhờ cho việc B rẻ hơn nhiều.

**Lưu ý vận hành:** `F:\RenderY\autoedit\.env` hiện **rỗng 0 byte** → không có
`PEXELS_API_KEY`/`PIXABAY_API_KEY`. Hút hiện chỉ chạy được Envato. User từng nói có
sẵn 2 key Pexels + 2 key Pixabay nhưng chưa nạp.

---

## BA VIỆC ĐÃ CHỐT (chờ user cho phép code)

### Việc A — placeholder có link, thay vì để timeline hở
- Nối `_slug_image`/`_fill_holes_with_slug` (assembler.py:370, 616) vào đường Offline;
  hiện `thay_mau.py:188` chỉ ghi warning rồi bỏ khối.
- Slug in thêm: link Envato + câu *"Tool đang cập nhật, vui lòng tải bằng tay theo link"*.
- Lý do bắt buộc: main track CapCut là track NAM CHÂM — hở là dồn segment, lệch voice.

### Việc B — bấm Export thì kiểm 1 lượt, có link chết thì CHẶN + tô đỏ
- Chèn bước kiểm trước `threading.Thread` ở `server.py:1183`; trả danh sách miếng hỏng.
- **Chỉ kiểm miếng ĐANG CHỌN** (~30-90/chương), **gọi song song** → vài giây.
- Đo thật: 9 miếng đang chọn clip đã `link_chet` trên 33 chương production.
- Kèm: vá Lỗ A (`thay_mau.py:185` điều kiện chuỗi không bao giờ đúng) và
  Lỗ B (`dung.py:338` chỉ quét `ref`).

### Việc C — tra cứu + hút NGAY trong tab Sequence (PA2 của user)
- Thêm `<input id="of-tim">` + nhãn `#of-tim-nhan` vào giao diện Sequence.
  **Logic đã viết xong từ trước** (index.html:2148-2158, 2222-2231) nhưng chết vì
  thiếu phần tử DOM — mọi lời gọi bọc `if (_oti)` nên hỏng âm thầm.
- Thêm nút **Hút thêm** trong Sequence (endpoint `/api/sotra/hut` đã sẵn).
- **Quyền:** mở cho người dựng (level 2) — hút tốn 0đ, ~12 giây; cửa quyền hiện tại
  viết cho `nap-ref` (tốn LLM), không đúng cho `hut`. → cần cửa quyền RIÊNG, đúng
  khuôn `LEVEL_DUNG_TOI_THIEU` đã làm 09/09.
- PA1 (kéo thả từ Library sang Sequence) **không làm** — đắt hơn, dễ lạc ngữ cảnh
  khối đích, và PA2 đã giải quyết đúng nhu cầu ngay tại chỗ dựng.

### Vòng 4 — "Hút thêm thì hút từ đâu?" (user hỏi 09/09)

**Trả lời: 3 nguồn cùng lúc** — `index.html:2793-2794` gửi
`nguon: ['envato','pexels','pixabay'], so_trang: 1`; mặc định server giống hệt
(`server.py:1471-1474`). KHÔNG hút YouTube, KHÔNG hút ref (ref nạp riêng bằng
`nap-ref` từ file trên NAS).

| Nguồn | Cách lấy | Hiện chạy được? |
|---|---|---|
| Envato | đọc trang search công khai (`hut.py:39`) | ✅ |
| Pexels | API chính thức (`hut.py:80`) | ❌ thiếu `PEXELS_API_KEY` |
| Pixabay | API chính thức (`hut.py:106`) | ❌ thiếu `PIXABAY_API_KEY` |

`.env` production (`F:\RenderY\autoedit\.env`) **rỗng 0 byte** → hút hiện chỉ ra
Envato, mà Envato là nguồn watermark phải tải tay. **Nạp 2 key stock là điều kiện để
nút Hút có giá trị thật** (user đã nói có sẵn 2 key Pexels + 2 key Pixabay).

**Phát hiện kèm — `ma_tap` chưa được nối (việc user hoãn 08/09):**
`phien_hut(..., ma_tap="")` (`hut.py:131`) đánh dấu clip mới là HÀNG TẠM của tập, để
`dong_job` (`db.py:257`) dọn khi đóng tập — giữ lại clip đã tải hoặc đã lên timeline.
Nhưng `server.py:1635` gọi `phien_hut` **không truyền `ma_tap`** → mọi clip hút từ web
vào kho VĨNH VIỄN. Đó là một phần lý do envato phình 5.209 dòng.
→ Nút Hút trong Sequence **phải truyền `ma_tap`** của chương đang dựng (hợp đồng có
sẵn `hd["ma_tap"]`, `runner.py:295`). Không thì càng dùng kho càng phình.

**Chưa chốt:** nút Hút hiện luôn hay chỉ hiện khi ít kết quả; bề rộng cột 208→248px.

### Vòng 5 — user 09/09: "pexels/pixabay xấu, không có preview mà phải download → nặng máy"

**ĐO THẬT — user đúng về hiện tượng, nhưng nguyên nhân KHÁC:**

| nguồn | số dòng | `url_video` (hotlink xem, KHÔNG tải) | file trên máy |
|---|---|---|---|
| ref | 8.781 | 0 | 8.781 |
| **envato** | 5.209 | **5.209** | 102 |
| **pexels** | 2.719 | **0** | **2.719** |
| **pixabay** | 427 | **0** | **427** |

`hut.py:80-102` (Pexels) và `hut.py:106-124` (Pixabay) **CÓ lấy `url_video` preview**
(`prev = file >= 360p`). Vậy sao trong kho là 0?

**Vì 2.719 clip pexels + 427 pixabay KHÔNG do hút mà vào.** Cột `tu_khoa_hut` chỉ
envato có (5.201 dòng); pexels/pixabay **rỗng 100%**. `path_local` của chúng trỏ vào
`projects\c7-20260831-062744\assets\b000_....mp4` — tức là **đường ONLINE cũ**
(`sourcer/`, tải thẳng vào assets của project), không phải đường Sổ Tra.

→ **Kết luận: kho pexels/pixabay hiện nay là XÁC của các tập đã dựng bằng đường cũ,
không phải kết quả hút.** Chưa từng có lượt hút Pexels/Pixabay nào (thiếu API key).
Nhận xét "phải download luôn, nặng máy" là mô tả đúng ĐƯỜNG CŨ; đường hút mới thì
hotlink preview y như Envato, KHÔNG tải gì.

**Chất lượng:** `dai_s` TB — pexels 10,0s · envato 1,6s (envato là khúc preview ngắn).
Không đủ dữ liệu để kết luận "pexels xấu hơn"; nhưng đó là NHẬN ĐỊNH NGHIỆP VỤ của
user, ghi nhận và tôn trọng.

**Logic đề xuất (chờ user duyệt):**
1. Nạp key → hút Pexels/Pixabay đi qua `hut.py` (hotlink preview, **không tải file**).
   Nặng máy sẽ hết vì không còn tải lúc hút.
2. **Xếp hạng nguồn trong khay tra cứu:** ref → envato → pexels → pixabay (user đánh
   giá pexels/pixabay chất lượng thấp hơn). Không loại bỏ — chỉ đẩy xuống dưới.
3. Chỉ tải file khi **Import vào khối** (đường `thay_mau` đã làm đúng vậy sẵn).

### Quyết định user vòng 5

| # | Chốt |
|---|---|
| 1 | User sẽ nạp key Pexels/Pixabay. Cần logic tránh nặng máy → xem 3 điểm trên |
| 2 | Clip envato hút trong Sequence: **vẫn nạp vào kho** (không đánh hàng tạm) |
| 3 | Nút Hút: **luôn hiện** |
| 4 | **UI khay: bản mẫu 1 CHƯA ĐẠT** — danh sách dọc 1 cột không xem nổi khi nhiều video |

### Vòng 6 — 4 key stock: USER ĐÚNG, và tìm ra BUG THẬT

User: *"tôi nghĩ anh ko tìm được key chứ không phải key đã chết"*. **User đúng.**

Sai lầm của tôi vòng 5: đọc `F:\RenderY\autoedit\.env` thấy rỗng 0 byte rồi kết luận
"chưa có key". Nhưng `web/ket_v3.py:1-6` ghi rõ luật V3: *"khoá API do Owner nhập ở
General › API Keys, app phụ hỏi qua gateway. App KHÔNG giữ sổ khoá riêng, KHÔNG đọc
`.env`"*. **`.env` rỗng là ĐÚNG THIẾT KẾ**, không phải thiếu sót.

**Đo thật qua gateway** (`ket_v3.doc_ket(force=True)` trên production):

| việc | số khoá | nhà |
|---|---|---|
| chia_beat | 1 | glm |
| cham_footage | 1 | glm |
| **tim_footage** | **4** | **pexels, pixabay, pexels, pixabay** |
| gen_canh | 1 | seedream |
| tim_tu_lieu | 3 | serpapi ×2, serper |
| tai_ban_sach | 1 | envato |

Đúng 4 key stock user nói. **Cả 4 test LIVE đều SỐNG**: mỗi key trả 40 clip,
**40/40 có `url_video`** (hotlink xem trước — xác nhận vòng 5: hút KHÔNG tải file).

#### BUG: `nap_env` gộp nhiều key thành 1 chuỗi, `hut.py` gửi nguyên chuỗi

```
PEXELS_API_KEY : len=113 = 2 khoá 56 ký tự nối bằng dấu phẩy
PIXABAY_API_KEY: len=69  = 2 khoá 34 ký tự nối bằng dấu phẩy
```
`hut.py:81` `key = os.getenv("PEXELS_API_KEY","").strip()` rồi gửi thẳng vào header
`Authorization` → Pexels trả **401 Unauthorized**; Pixabay trả **400 Bad Request**.

Tách ra thử từng khoá → **cả 4 đều OK 40 clip**. Vậy lỗi KHÔNG ở khoá mà ở chỗ
`hut.py` chưa biết dạng nhiều-khoá. Đã có sẵn `collect_pexels_keys` /
`collect_pixabay_keys` (dùng ở `server.py:499-500`) làm đúng việc tách — `hut.py`
không dùng.

→ **Sửa 1 dòng mỗi hàm**: lấy khoá đầu (hoặc xoay vòng khi 429) thay vì gửi cả chuỗi.
Sau đó Pexels/Pixabay hút được, và hút bằng **hotlink preview, không tải file** —
đúng thứ user cần để hết "nặng máy".

**Ghi nhận:** vòng 5 tôi nói "thiếu API key" là SAI. Key có đủ, chỉ là đường hút gửi sai.

---

## VẤN ĐỀ 1 — BẢNG VIỆC CHỐT (09/09/2026, sau 6 vòng bàn)

> Chốt UI: **PA B — lưới lớn**, phân trang **21 clip/trang**.
> API đã sẵn phân trang (`server.py:1477-1499`: `limit`, `offset`, trả `het` +
> `offset_tiep`) → không phải xây mới, chỉ nối vào.

### Việc A — Placeholder có link thay vì để timeline hở

| | |
|---|---|
| Vì sao | `thay_mau.py:188` hết ứng viên thì bỏ khối, chỉ ghi warning. Main track CapCut là track NAM CHÂM: hở là CapCut dồn segment, footage sau lệch voice tích luỹ |
| Đã có sẵn | `assembler.py:616` `_slug_image()` + `:370` `_fill_holes_with_slug()` — đường Auto dùng rồi, đường Offline chưa gọi |
| Làm | 1. Đường Offline gọi slug thay vì bỏ khối<br>2. Slug in **link Envato + câu "Tool đang cập nhật, vui lòng tải bằng tay theo link"** (hiện chỉ vẽ chữ cố định "EDITOR: ĐẮP FOOTAGE Ở ĐÂY") |
| Verify | dựng 1 chương có clip chết → mở draft CapCut, ô đó có slug đọc được link, timeline không lệch |

### Việc B — Kiểm trước khi Export, có link chết thì CHẶN + tô đỏ

| | |
|---|---|
| Điểm nối | `server.py:1183` `api_offline_thay_mau` — chèn bước kiểm TRƯỚC `threading.Thread` |
| Phạm vi kiểm | **chỉ miếng ĐANG CHỌN** (~30-90/chương), **gọi song song** → vài giây. KHÔNG kiểm cả khay (13.270 ô) |
| Trả về | 409 + danh sách chỉ số miếng hỏng → UI tô đỏ đúng miếng đó trên timeline |
| Đo thật | 9 miếng đang chọn clip đã `link_chet` trên 33 chương production |
| Verify | tạo 1 clip `link_chet` giả trong khay → bấm Export → phải bị chặn, đúng miếng đỏ |

### Việc C — Vá 3 lỗ của cơ chế link_chet

| Lỗ | Chỗ | Sửa |
|---|---|---|
| **A** | `thay_mau.py:185` kiểm `"không tồn tại" in str(exc)` — KHÔNG luồng nào ném chuỗi đó; 404 trả `"HTTP Error 404: Not Found"` | bắt theo mã lỗi HTTP (404/410) thay vì so chuỗi tiếng Việt |
| **B** | `dung.py:338` `_hong()` chỉ kiểm `nguon == "ref"` → clip envato chết trong khay cũ vẫn được chọn | mở rộng cho mọi nguồn, quét theo `trang_thai='link_chet'` |
| **C** | `thay_mau.py:185` `conn.execute` thiếu `commit()` ngay chỗ đó | commit tại chỗ |
| — | Lỗi mạng/timeout (`tai_sach.py:230`) chỉ log | **KHÔNG vá** — user chốt "fail 1 lần bỏ qua luôn"; đánh `link_chet` vì mạng đứt là giết oan, mà không có đường gỡ cờ |

### Việc D — Sửa bug 4 key stock (nhiều khoá nối bằng dấu phẩy)

| | |
|---|---|
| Bug | Két V3 trả `PEXELS_API_KEY = <56 ký tự>,<56 ký tự>`; `hut.py:81` gửi nguyên chuỗi → **401**. Pixabay `hut.py:107` → **400** |
| Bằng chứng | tách riêng từng khoá: **cả 4 đều OK, mỗi khoá 40 clip, 40/40 có `url_video`** |
| Đã có sẵn | `collect_pexels_keys` / `collect_pixabay_keys` (dùng ở `server.py:499-500`) làm đúng việc tách — `hut.py` không dùng |
| Làm | `hut.py` dùng hàm tách đó; lấy khoá đầu, gặp 429 thì xoay sang khoá kế |
| Verify | gọi thật `hut_pexels` + `hut_pixabay` qua két → mỗi bên ≥ 1 trang kết quả |

### Việc E — Khay tra cứu trong popup (PA B)

| | |
|---|---|
| Phát hiện | Logic **đã viết xong** (`index.html:2148-2158` gọi `/api/sotra`, `:2222-2231` chèn clip vào khay + `chon=0` + `nguoi_sua`) nhưng **`#of-tim` KHÔNG tồn tại trong HTML** → mọi `getElementById` bọc `if(_oti)` nên **hỏng âm thầm**, nhánh tra cứu chưa từng chạy |
| Làm | 1. Sắp lại thân popup theo PA B: khung xem trên (236px) + bảng thông tin phải (254px) + lưới dưới<br>2. Ô tìm + đếm kết quả + nút Hút thêm (luôn hiện)<br>3. Nút lọc nguồn `Ref/Envato/Pexels/Pixabay` + `⚑ có neo` + `≥ 5s` + `chưa dùng`<br>4. Nhãn thẻ: nguồn · độ dài giây · đã dùng ở tập nào<br>5. **Phân trang 21 clip/trang** — dùng `offset`/`het`/`offset_tiep` API đã có<br>6. Bảng phải: Import + Cắt khúc |
| Quyền | nút Hút mở cho **người dựng (level 2)** — hút tốn **0đ, ~12s**; cửa `_duoc_nghien_cuu_kenh` viết cho `nap-ref` (tốn LLM thật), không đúng cho `hut` → cần cửa riêng, đúng khuôn `LEVEL_DUNG_TOI_THIEU` |
| `ma_tap` | **KHÔNG truyền** — user chốt: *"Clip trong sequence đối với envato thì vẫn cứ nạp"* (vào kho thường trực, không đánh hàng tạm) |
| Verify | Playwright + Chrome thật (BH9): gõ từ khoá → có kết quả; bấm lọc nguồn → đúng nguồn; sang trang 2 → clip khác |

### Việc F — Xếp hạng nguồn trong khay

User đánh giá pexels/pixabay chất lượng thấp hơn. **Không loại, chỉ đẩy xuống**:
thứ tự ref → envato → pexels → pixabay. Nút lọc nguồn (việc E) đã cho user tự gạt.

### KHÔNG LÀM (chốt, ghi để không ai làm lại)

| Việc | Lý do |
|---|---|
| Xoá 5.107 dòng envato rỗng | user: *"lưu trữ không mất nhiều dung lượng thì không cần xoá"*. Chỉ là text SQLite, vài MB. Xoá còn mất dấu vết 21 clip watermark đã lên timeline LI106 |
| PA1 — kéo thả từ Library sang Sequence | đắt hơn PA B, dễ lạc ngữ cảnh khối đích; PA B giải quyết đúng nhu cầu ngay tại chỗ dựng |
| Vá lỗ C (ghi DB khi lỗi mạng) | giết oan clip sống; không có đường gỡ cờ `link_chet` |
| Đánh hàng tạm clip hút trong Sequence | user chốt vẫn nạp vào kho thường trực |

### Thứ tự đề xuất

1. **D** (2 dòng, mở khoá 2 nguồn stock) → 2. **C** (vá 3 lỗ, nền cho B)
→ 3. **B** (chặn Export) → 4. **A** (placeholder) → 5. **E** (khay PA B) → 6. **F** (xếp hạng)

Mỗi bước: test xanh trước → code → suite đầy đủ → đẩy production.

---

## LUẬT THI CÔNG (user chốt 09/09) — áp cho MỌI việc còn lại

1. **Test xanh trước, code sau.** Viết test mô tả đúng hành vi mong muốn, chạy để
   thấy nó ĐỎ (chứng minh test có tác dụng), sửa code, chạy lại xanh.
2. **Không còn bug mới được code tiếp** — mỗi việc đóng gọn, không chồng lấn.
3. **Code xong chạy thử mẫu nhỏ để nghiệm thu** — không tự nhận xong khi chưa chạy thật.
4. **Phần UI: đặt mockup CẠNH code thật, so từng chi tiết** để không rơi mất thứ gì.
   Mockup chốt: `scratchpad/ui_o_tra_cuu.html` (PA B).
5. **Icon tối giản + nguyên tắc thiết kế** — xem mục dưới.

### Nguyên tắc thiết kế UI (áp cho việc E)

| Nguyên tắc | Cụ thể trong RenderY |
|---|---|
| Icon tối giản | ký tự đơn sắc có sẵn (`⚑ ✂ ⛏ ⧉ ♪ 🔍`), KHÔNG emoji nhiều màu, KHÔNG thư viện icon ngoài (CSP chặn + nặng) |
| Một việc một chỗ | mỗi nút một hành động rõ; không nút nào làm 2 việc tuỳ ngữ cảnh |
| Trạng thái nói thật | nút Hút ghi rõ `~12s`; đang chạy thì đổi chữ, không để user đoán |
| Không giấu chức năng | nút KHÔNG ẩn theo điều kiện ngầm — bài học `st-hut-nut` ẩn khi ô trống khiến user tưởng không có (vòng 3) |
| Đặt cạnh nơi dùng | ô nhập nằm cạnh nút nó phục vụ — bài học `of-noi-xuat` đặt xa nút Export (08/09) |
| Màu có nghĩa cố định | ref lục · envato lam · pexels cam · pixabay tím; cảnh báo dùng `--warn`, không dùng đỏ cho việc thường |
| Chữ Việt, không thuật ngữ | "đã dùng ở tập", "chưa dùng" — không "used/unused" |
| Đủ tương phản | chữ phụ `--muted` trên nền `--panel2`; không chữ xám nhạt trên nền tối |

**Verify UI (BH9):** Playwright + Chrome thật, trích JS từ file đã ship, không viết lại.
