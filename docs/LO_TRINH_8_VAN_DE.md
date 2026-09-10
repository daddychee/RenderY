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

---

## NGHIỆM THU NGƯỜI DÙNG 09/09 — 2 phát hiện

### Thử 1: có báo hỏng nhưng KHÔNG tô đỏ — LỖI CSS

User: *"CÓ báo 1 khối đang lỗi nhưng không có các viền đỏ, clip hỏng"*.

Server ĐÚNG (đã gọi thật trên production, trả 409 + đúng miếng + tên clip). Lỗi
nằm ở CSS: `index.html:227` đặt `.of-mieng.hong` **TRƯỚC** `:232` `.of-mieng.tho`.
Hai luật cùng độ ưu tiên (0,2,0) -> luật SAU thắng, `border-color` của `.tho`
đè lên `.hong`. Miếng nào nằm trong khoảng thở là mất viền đỏ.

**Test của tôi báo xanh vô nghĩa:** `test_UI_co_ham_to_do_mieng_hong` chỉ kiểm
`".of-mieng.hong" in h` — có chuỗi trong file là xanh, bất kể CSS có ăn hay không.
Đúng loại test tôi từng tự phê ở việc `of-noi-xuat` (kiểm tồn tại thay vì kiểm
hành vi). User đã dặn UI phải so mockup cạnh code thật + verify bằng trình duyệt
(BH9) — tôi bỏ qua bước đó ở việc B.

### Thử 2: hút 117 mới / 3 trùng — user cần cơ chế loại trùng

**Loại trùng theo ID đã có và đang chạy đúng**: `them_clip` (db.py:211) upsert
theo `id`, trả 0 nếu đã có -> "3 trùng" chính là nó làm việc.

Thứ user thật sự gặp là **TRÙNG NỘI DUNG**, đo trên kho thật:

| | |
|---|---|
| tổng clip stock (envato/pexels/pixabay) | 8.472 |
| nhóm cùng NGUỒN + cùng TIÊU ĐỀ | 714 |
| **bản thừa** | **2.093 (25% kho stock)** |
| nhóm trùng `url_video` (chắc chắn cùng file) | 7 |

Ví dụ: 13 clip envato cùng tên "Aerial view of the jungle, Ecuador.",
16 clip pexels cùng tên "the river surface drifting past at...".

**NHƯNG — kiểm sâu thì KHÔNG được xoá theo tiêu đề.** Soi 13 bản "Aerial view of
the jungle": **khác id, khác `url_video`, khác `url_anh`** -> chúng là các clip
KHÁC NHAU trong cùng một bộ, tác giả đặt trùng tên. Gộp theo tiêu đề là xoá mất
hàng thật.

Chỉ 7 nhóm trùng `url_video` mới là trùng CHẮC CHẮN (cùng một file).

**Đề xuất (chờ user duyệt):**
1. Chặn ở KHÂU HÚT: bỏ qua bản có `url_video` đã tồn tại trong kho (7 nhóm).
2. Trong KHAY tra cứu: gom clip cùng nguồn+tiêu đề thành một thẻ, ghi "+N bản"
   (nhãn `so_ban` đã có sẵn ở trang Library, `index.html:2717`) — user thấy 1
   thẻ thay vì 13, nhưng vẫn mở ra chọn được bản khác.
3. KHÔNG xoá gì khỏi kho.

### Vòng 7 — sửa sau nghiệm thu 09/09

**Tô đỏ:** đổi thứ tự `.of-mieng.hong` ra SAU `.of-mieng.tho`. Test bằng Chrome
thật (`tests/test_to_do_trinh_duyet.py`) tái hiện đúng lỗi user gặp: viền ra
`rgb(92,185,138)` (xanh lục của `.tho`) thay vì đỏ. 6 test, đỏ trước xanh sau.

**Loại trùng — user chốt 2 việc:**
1. Hút: bỏ bản trùng `url_video` (`db.them_clip`). Kho hiện có 7 nhóm/8 bản thừa.
2. Khay: gộp cùng nguồn + cùng tiêu đề (`db.gop_ban_trung` -> `tra()`), nhãn
   "+N bản", bản còn lại giữ ở `ban_khac`. Đo thật: khay `market` 12 -> 9 thẻ;
   8 từ khoá thử, khay thấp nhất còn 8 thẻ (không bị mỏng).

**HAI LỖI SUITE BẮT ĐƯỢC — cả hai đều lọt qua test riêng:**

| Lỗi | Hậu quả nếu lọt | Vá |
|---|---|---|
| Chặn trùng URL giết luôn TRIM | khúc cắt thừa kế url clip mẹ -> bị coi là trùng -> người dựng cắt xong MẤT | chừa 3 ngoại lệ: id có `#` (khúc trim), có `path_local`, url rỗng |
| `so_ban` rơi ở `do_ung_vien` | khay gộp đúng nhưng nhãn "+N bản" KHÔNG BAO GIỜ hiện — lỗi im lặng | thêm vào danh sách trắng; cố ý KHÔNG chép `ban_khac` (phình hợp đồng) |

### BÀI HỌC — bổ sung METHODOLOGY

**BH11 — Test UI kiểm CHUỖI TRONG FILE là test báo xanh vô nghĩa.**
`test_UI_co_ham_to_do_mieng_hong` chỉ kiểm `".of-mieng.hong" in h` -> xanh, trong
khi user nhìn màn hình KHÔNG thấy viền đỏ nào (luật `.tho` đứng sau đè mất).
CSS/JS phải kiểm bằng **Chrome thật + `getComputedStyle`**, CSS **trích nguyên
văn** từ file đã ship (chép tay là test một bản khác với bản đang chạy).
Đây là lần THỨ HAI mắc cùng kiểu: lần trước là `of-noi-xuat` kiểm "có tồn tại"
trong khi ô nằm sai chỗ.

**BH12 — Danh sách TRẮNG các trường là chỗ rơi dữ liệu im lặng.**
`do_ung_vien` chép khay theo danh sách trường cố định. Thêm trường mới ở tầng
dưới (`tra()`) mà quên thêm vào đây thì trường đó biến mất, KHÔNG có lỗi nào
báo. Mỗi lần thêm trường phải dò ngược mọi chỗ chép-theo-danh-sách.

---

## VÒNG 8 (10/09/2026) — VIỆC A: ô giữ chỗ có link, timeline không còn hở

User duyệt thứ tự **A → F → E** ("Đồng ý với thứ tự đó").

### Kiểm TRƯỚC khi code — đo trên production

| Đo | Kết quả |
|---|---|
| Chương từng để hở | **1/21** (`c8-20260831-064152`, `thay_mau.json` ghi *"miếng 12: KHÔNG lấy được nguồn nào"*) |
| Lỗ trong draft đã sinh | `OFF_c8-20260831-064152/draft_content.json`: **33 segment, hở 5.170s tại giây 67.020** |
| Nguyên nhân miếng đó | khay **RỖNG** (`uv` 0 ứng viên), không phải link chết |
| Độ dài `url_trang` thật | 82–86 (Envato), dài nhất **226** (Pexels) — trên **5.315 link** trong kho |

Hiếm (1/21) nhưng khi xảy ra là hỏng **cả chương**: main track CapCut là track
NAM CHÂM, hở thì lúc mở CapCut dồn 22 segment còn lại lên trước 5.17s và ghi đè
`draft_content.json`; voice nằm track khác nên đứng yên → **nửa sau chương lệch
tiếng tích luỹ**.

### Đã làm

| # | Thay đổi | File |
|---|---|---|
| 1 | `anh_giu_cho(thu_muc, link, tieu_de) -> (Path, chữ)` — ảnh 1920x1080 in câu *"Tool đang cập nhật, vui lòng tải bằng tay theo link"* + link + tên clip; khay rỗng thì in lời dặn chung | `offline/thay_mau.py` |
| 2 | `be_dong(chu, moi_dong)` — bẻ dòng thủ công | cùng file |
| 3 | `dung_draft`: `f is None` → lấp ảnh giữ chỗ thay vì `continue` | cùng file |
| 4 | `relocate`: hết ứng viên thì ghi `hinh[i]["ho_link"]`/`["ho_ten"]` lấy từ `url_trang` của clip ĐANG CHỌN | cùng file |

**KHÔNG dùng lại `assembler._fill_holes_with_slug`** (sổ vòng 6 đoán là dùng
được): hàm đó nhận `holes` theo mốc beat của đường Auto và tự cộng cờ HOLD từ
`coverage.insert_hold_flags` — đường Offline không có beat, cũng không có nhóm
HOLD. Gọi lại là phải bịa dữ liệu giả cho nó. Viết mới 40 dòng thẳng theo dải
miếng rẻ hơn và đọc được.

### Hai lỗi CHỈ NHÌN ẢNH THẬT MỚI THẤY

Test xanh 9/9 rồi, nhưng mở ảnh ra xem thì:

1. **Link dài bị vẽ TRÀN cả hai mép** — mất `https://...` ở đầu, mất ID ở đuôi
   → người dựng không tải được, tức là tính năng vô dụng đúng ở ca nó sinh ra để
   phục vụ. `wrap=True` của matplotlib chỉ bẻ ở **khoảng trắng**, mà link không
   có khoảng trắng nào.
2. **Khối chữ dồn lệch lên đỉnh** — toạ độ cứng, không tính theo số dòng thật
   (ca 226 ký tự ra 3 dòng, ca khay rỗng chỉ 2).

### Ngưỡng bẻ dòng — ĐO trên cả 5.315 link, không ước

| Ngưỡng | Dòng tràn >1728px | Link vừa TRỌN 1 dòng |
|---|---|---|
| 78 | 0 | 233 / 5.315 |
| 80 | 0 | 256 / 5.315 |
| **82** | **0** | **4.606 / 5.315 (87%)** |
| 84 | 0 | 4.635 / 5.315 |
| 86 | **3 dòng tràn** (rộng nhất 1747px) | — |

Chốt **82 ký tự/dòng ở cỡ 26**: điểm nhảy vọt (256 → 4.606) vì link Envato thật
dài 82–86, và vẫn còn biên an toàn 82px so với trần 1728px (90% của 1920).

### Nghiệm thu

- Test mới: `tests/test_lap_lo_slug.py` — **11 test**, chạy đỏ trước khi code.
- **Dựng lại bằng hợp đồng c8 THẬT** (35 miếng, 186.83s voice), bỏ file miếng 11
  đúng như ca lỗi: **35/35 segment, 0 lỗ hở** (trước: 33 segment + hở 5.170s).
- Xem tận mắt 3 ảnh: link Envato 82 ký tự (1 dòng), link Pexels 226 ký tự
  (3 dòng), khay rỗng — cả ba đọc trọn, không tràn.

### BH13 — Test xanh không thay được việc NHÌN sản phẩm

11 test xanh, nghiệm thu số liệu sạch, mà ảnh vẫn cụt link. Test kiểm được
"có chữ trong ảnh không", không kiểm được "chữ có nằm trong khung không" —
đó là thứ chỉ mắt thấy. Với mọi thứ SINH RA ĐỂ NGƯỜI NHÌN (ảnh, PDF, giao
diện), bước cuối luôn là mở ra xem, kể cả khi mọi test đã xanh. Cùng gốc với
BH11 nhưng ở tầng khác: BH11 nói *test sai cách*, BH13 nói *test đúng cách vẫn
chưa đủ*.

### Trạng thái việc A: XONG, đã lên production 10/09

Suite `1656 passed / 14 skipped / 0 failed` (trước việc A: 1645 — đúng 11 test
mới). Commit `14b50f4`, GitHub đồng bộ, server 9118 đã restart và nạp bản mới
(`anh_giu_cho` / `be_dong` / `dung_draft` gọi ô giữ chỗ — kiểm bằng venv của
production, không phải venv dev).

Lưu ý vận hành: `thay_mau` chạy trong **thread cùng tiến trình server**
(`server.py:1242`), không phải tiến trình con — nên sửa nó là **phải restart**
9118 mới ăn.

### Việc F — đo lại trước khi code, KẾT QUẢ KHÁC KỲ VỌNG

Đo khay trên **996 miếng thật** (21 chương production):

| Nguồn | Trong khay | Được chọn |
|---|---|---|
| ref | 85.2% | 81.8% |
| envato | 9.0% | 10.1% |
| kho | 5.5% | 6.8% |
| pexels | **0.2%** | 1.2% |
| pixabay | **0.1%** | 0.1% |

Kho có 2.758 pexels + 467 pixabay `song`, nhưng khay chỉ nhận **42 mục**.
Chúng gần như KHÔNG CÓ MẶT để mà đẩy xuống.

Nhưng khi lọt vào thì đúng là hay đứng đầu bảng: **16/33** pexels và **6/9**
pixabay ở vị trí ≤2, trong khi envato trung vị vị trí **4**. Đúng điều user
phàn nàn — chỉ là quy mô nhỏ.

Nguyên nhân khay toàn ref: `tra.py:162-167` thêm ref SAU vòng cân nhóm, và
vòng đó chỉ dừng khi **cả hai** điều kiện `len(ra) >= so` và
`gio_ref >= suat_ref` cùng đủ. Khối nào stock cho ít điểm thì `cham` mỏng và
ref lấp trọn khay. Đây là **thiết kế cố ý** của user 07/09 (*"cái gì nhiều hơn
thì ưu tiên đổ vào"*), KHÔNG phải lỗi — không tự đổi.

→ F vẫn làm đúng như đã chốt (vài dòng), nhưng phải nói trước với user: nó sẽ
không đổi cảm nhận về khay. Thứ chi phối khay là tỉ lệ ref/stock, và đó là
quyết định của user.

---

## VÒNG 9 (10/09/2026) — VIỆC F: xếp hạng nguồn trong khay

User 10/09: *"Tạm thời vẫn giữ luật cũ. Sau khi hoàn thiện tool thì tôi sẽ đưa
luật riêng của từng Niche."* → KHÔNG đụng tỉ lệ ref/stock.

### Mức phạt — ĐO, không ước

Khoảng cách điểm trong một khay (996 miếng production): trung vị **13.0**,
p25 **7.0**. Điểm trung vị: ref 20.5 · envato 10.0 · pixabay 12.0 · pexels 8.0.

Mô phỏng trong nhóm `cham` (KHÔNG đụng ref — ref chèn theo luật `suat_ref`):

| Phạt | Khay đổi thứ tự | Dịch envato | Dịch pexels |
|---|---|---|---|
| 2/3 | 6/31 | −0.19 | +0.52 |
| **3/4** | **8/31** | **−0.25** | **+0.70** |
| 5/6 | 14/31 | −0.42 | +1.12 |
| 8/9 | 16/31 | −0.57 | +1.42 |

Chốt **`PHAT_NGUON = {"pexels": 3.0, "pixabay": 4.0}`**.

Kèm theo: **`DIEM_UU_TIEN_NGUON` 2.5 → 6.0**. Bắt buộc, vì 2.5 không thắng nổi
phạt 4.0 — gõ `--uu-tien-nguon pexels` mà pexels vẫn nằm dưới envato là sai.
Test `test_sotra.py::test_tra_uu_tien_nguon` có sẵn từ trước sẽ bắt lỗi này.

### LỖI BẮT ĐƯỢC LÚC NGHIỆM THU — phạt điểm KHÔNG kèm giữ chỗ = XOÁ nguồn

Chạy `tra()` thật trên kho production (17.323 clip), 8 từ khoá:

- `market vendor`: `ppRRRRRRE` → `RRRRREEEEEE` — **mất sạch pexels**
- 3/8 từ khoá mất hẳn stock (`market`, `ocean`, `desert`)

Nguyên nhân: vòng cân nhóm chặn **6 mục/tầng**. Cả khay cùng tầng L1; pexels
tụt 22.0 → 19.0 nên rơi dưới 6 envato 20.0 điểm và bị cắt khỏi giỏ. Đó là
**LOẠI**, trái hẳn yêu cầu "đẩy xuống, không loại".

Vá: **1 suất giữ chỗ mỗi nguồn bị phạt** (cùng cơ chế `suat_ref` đã có). Sau vá:

| | Trước | Sau |
|---|---|---|
| Khay mất hẳn stock | 3/8 | **0/8** |
| Vị trí trung bình stock | 5.25 | **9.24** |

### TÁC DỤNG PHỤ có thật — phải nói rõ

Đẩy pexels xuống thì **envato trồi lên chiếm chỗ**, khay đầy hơn nên ref nhận
ít suất "dôi" hơn:

| Nguồn | Trước | Sau |
|---|---|---|
| ref | 46 | 34 |
| envato | 27 | 42 |
| pexels | 6 | 10 |
| pixabay | 2 | 7 |

**LUẬT ref KHÔNG vỡ**: `suat_ref` là SÀN (user chốt 07/09), sàn 2 vẫn được
tôn trọng ở cả 8 từ khoá (thấp nhất 4 ref/khay). Ref giảm vì nó vốn ăn phần
"dôi" khi nhóm `cham` mỏng — nay `cham` dày hơn nên phần dôi ít đi. Đây là hệ
quả tất yếu của việc F, không phải lỗi; đã khoá bằng
`test_san_suat_ref_van_duoc_giu`.

### Mối nối phải khoá: `do_ung_vien` cắt lại khay

`dung.py:80` cắt `khac[:so_moi_khoi - len(ref_uv)]`. Stock nằm CUỐI `khac`
(điểm thấp nhất sau phạt) nên **bị cắt trước tiên** — suất giữ chỗ đặt trong
`tra()` có thể chết ở đây mà không báo gì. Hai hàm ở hai file, sửa bên này
không ai nhắc bên kia.

Đo qua đúng đường đó trên kho thật: **3/8 khay không có stock trước phạt → 0/8
sau phạt + giữ chỗ**. Đã khoá bằng `test_suat_giu_cho_SONG_SOT_qua_do_ung_vien`.

### BH14 — Phạt điểm trong hệ có HẠN NGẠCH là xoá, không phải đẩy xuống

Trực giác "trừ vài điểm thì nó tụt vài bậc" chỉ đúng khi danh sách phẳng. Khay
RenderY có giỏ 6 mục/tầng, nên trừ điểm đủ để rơi khỏi top-6 là **biến mất
khỏi khay**. Test đơn (2 clip) không bao giờ lộ ra — chỉ chạy trên kho thật
mới thấy. Mọi thay đổi điểm số phải nghiệm thu trên kho thật, và nếu yêu cầu
là "không loại" thì phải có **suất giữ chỗ** chứ không chỉ chỉnh điểm.

### Trạng thái việc F: XONG, đã lên production 10/09

Suite `1667 passed / 14 skipped / 0 failed` (trước việc F: 1656 — đúng 11 test
mới). Commit `168b1de`, GitHub đồng bộ, server 9118 đã restart.

Kiểm bằng **venv production**, qua đúng đường `do_ung_vien` mà tool thật dùng:

```
market    EEEEEEpxRRRR      ocean     EEEEEEpRRRRR
mountain  EEEEEEpxRRRR      desert    EEEEEEpxRR
ancient   EEpppxRRRRR       snow      EEEEEExpRRR
city      EEEEEExpRRRR      forest    EExEEpRRRRR
```
(E=envato p=pexels x=pixabay R=ref) — envato trước, stock ngay sau, ref cuối.
**0/8 khay mất stock.** Tổng: envato 42 · pexels 10 · pixabay 7 · ref 32.

Lưu ý vận hành: `tra.py` chạy trong tiến trình server (không phải tiến trình
con) — sửa nó là **phải restart** 9118, giống `thay_mau.py`.

---

## VẤN ĐỀ 1 — CÒN LẠI: việc E

A ✅ · B ✅ · C ✅ · D ✅ · F ✅ · **E chưa làm**.

Việc E là phần nhiều giao diện nhất (khay tra cứu PA B trong popup: ô tìm, lọc
nguồn, phân trang 21 clip, bảng thông tin, nút Hút). Áp thêm bước bắt buộc từ
BH13: **đặt mockup `scratchpad/ui_o_tra_cuu.html` cạnh bản thật, so từng chi
tiết, rồi mở Chrome bấm nút thật trước khi báo xong.**

---

## VÒNG 10 (10/09/2026) — VÁ 2 LỖI USER BÁO (chen ngang trước việc E)

User gửi ảnh chụp màn hình + 2 câu: *"nạp đủ script r nhưng vẫn báo transcript
rỗng là lỗi rì ạ"* · *"nó vẫn chưa có Xml anh ạ"*.

### Lỗi 1 — "nạp đủ script rồi vẫn báo transcript rỗng"

Truy trên production, chương `e-20260908-115102`:

| | |
|---|---|
| `E.txt` trên NAS | **1139 byte**, sửa **15:45 ngày 10/09** — user đã nạp thật |
| `inputs/script.txt` trong chương | **0 byte**, từ 08/09 |
| `project.json` → `inputs.script_text` | rỗng |
| `transcript.json` | `match_ratio: 0.0`, `words: []` |
| Log | `POST .../e-20260908-115102/phan-tich` lặp **hơn 15 lần**, đều 200 OK |

**HAI lỗi chồng nhau:**

1. `project.py:606` copy script rồi đi tiếp, **không kiểm nội dung**. Chương
   sinh ra đã hỏng; chỗ duy nhất phàn nàn là align — báo *"transcript rỗng"*,
   tức là **đổ lỗi cho khâu SAU** chứ không chỉ khâu thật sự hỏng.
2. Script chỉ copy **một lần** lúc tạo chương (chú thích *"self-contained,
   resume độc lập file gốc"*). User sửa file gốc rồi bấm Phân tích 15 lần, tool
   vẫn dùng bản rỗng cũ.

Quét 90 chương: **1 chương dính**. Hiếm — nhưng khi dính là chặn hẳn người dùng
và không nói được vì sao.

**Vá** (user chốt: *tự đọc lại script gốc*):

| # | Thay đổi | File |
|---|---|---|
| 1 | `doc_script(project_dir)` — bản trong chương RỖNG thì đọc lại bản gốc, ghi đè cả `inputs/script.txt` lẫn `script_text`; rỗng cả hai nơi thì báo rõ file nào cần nạp | `project.py` |
| 2 | `create_project` **chặn ngay** nếu script rỗng (kiểm `.strip()`, không kiểm kích thước) | `project.py` |
| 3 | `phan_tich` khi transcript rỗng: tự nạp lại script + báo *"đã tự nạp lại từ bản gốc, chạy Align lại"*; script KHÔNG rỗng thì báo câu KHÁC (align dở / voice lệch) | `offline/runner.py` |

**Chỉ chép khi bản trong chương RỖNG** — chương đang chạy bình thường giữ
nguyên self-contained: sửa file gốc không được âm thầm đổi chương đã dựng dở.

**Đã sửa chương E thật cho user:** nạp lại 1129 ký tự → chạy align (whisper,
chương này không có `.srt`) → **188 từ, khớp 95%**. User bấm Phân tích là chạy.

### Lỗi 2 — "vẫn chưa có XML"

Mã xuất XML **đã có sẵn và đầy đủ**: `packager/xmeml.py` (`.xml`, FCP7 —
Premiere chỉ import kiểu này) · `packager/fcpxml.py` (`.fcpxml`, Resolve/FCP) ·
`web/compose.py:96-118` gọi cả hai.

Nhưng đường Offline ráp draft ở `offline/thay_mau.py`, giao giấy ở
`offline/giao.py` — **không chỗ nào gọi compose** (grep `xml` trong hai file:
0 kết quả). Thiếu đúng **một mối nối**.

**KHÔNG dùng lại `compose_chapter`**: hàm đó copy CẢ draft sang thư mục giao,
trong khi đường Offline đã chốt 09/09 là không chép draft (10 draft = 992MB).
Chỉ gọi thẳng `xuat_xmeml` / `xuat_fcpxml` trỏ vào draft tại chỗ.

**Vá:** `xuat_xml_canh_draft(draft, log)` trong `thay_mau.py`, `dung_draft` gọi
ngay sau sổ nguồn gốc. Đặt CẠNH draft như `nguon_footage.*` — editor mang cả
thư mục draft sang máy khác là có luôn. Fail-open: hỏng XML mất XML, KHÔNG
được mất draft (cùng luật sổ nguồn gốc).

User chốt 10/09: **xuất cùng lúc với draft, không thêm nút**.

**Nghiệm thu trên draft THẬT** `OFF_c2-20260907-101011` (172 file media):

```
canh bao : KHONG CO
sequence : OFF_c2-20260907-101011
  video  : 43 clip
  audio  : 43 clip
```

Khớp đúng draft gốc (43 video / 43 audio segment). Đã xoá 2 file thử khỏi draft
production sau khi kiểm — không để lại rác trên dữ liệu người dùng.

### BH15 — Thông điệp lỗi chỉ sai khâu là đẩy người dùng đi sai hướng

*"transcript rỗng — chạy align trước"* đúng về triệu chứng nhưng sai về nguyên
nhân: align **đã chạy rồi** (`stages.align = done`), nó rỗng vì kịch bản rỗng.
User làm đúng theo lời tool bảo (bấm lại) 15 lần mà không thoát được.

Luật rút ra: khi một khâu phát hiện dữ liệu vào hỏng, phải **truy ngược một
bậc** trước khi kết luận. Và nếu có hai nguyên nhân khác nhau dẫn tới cùng
triệu chứng thì phải ra **hai thông điệp khác nhau** — gộp làm một là dồn người
dùng vào ngõ cụt.

### Trạng thái vòng 10: XONG, đã lên production 10/09

Suite `1681 passed / 14 skipped / 0 failed` (trước: 1667 — đúng 14 test mới).
Commit `37aac33`, GitHub đồng bộ, server 9118 restart.

**Chạy trọn chương E qua ĐÚNG ĐƯỜNG NGƯỜI DÙNG BẤM** (POST `/phan-tich` trên
server production, không gọi hàm thẳng):

```
POST /api/offline/e-20260908-115102/phan-tich -> 200
[offline] offline: 14 khối theo hơi thở · offset 0.0s
[offline] offline-dịch: 14/14 khối có bản dịch
[offline] offline: hợp đồng ghi xong — 14 khối · AUTO · 0 lỗi lặp
[offline] e-20260908-115102: AUTO — máy tự khóa sổ + Online
thay_mau.json: 18/18 miếng, 0 cảnh báo
```

Thư mục draft `OFF_e-20260908-115102/` có đủ:
`draft_content.json` · `nguon_footage.json/.txt` · **`.xml` 62.9KB** ·
**`.fcpxml` 18KB**.

Đối chiếu draft ↔ XML: **22 video + 14 audio** ở cả hai; 2689 khung / 30fps =
89.6s, khớp đúng độ dài voice chương E (89.626s).

Chương E trước đó **chặn hẳn** người dùng (bấm Phân tích 15 lần vô ích) — nay
chạy trọn tới draft + XML.

---

## VÒNG 11 (10/09/2026) — XUẤT TIMELINE VẪN DÍNH WATERMARK

hieuvn + haint báo: *"xuất timeline vẫn dính hd preview"*.

### Nguyên nhân gốc — Playwright LỒNG NHAU, không phải lỗi vận hành

Log production `prod.log.old:1535-1551`:

```
online: phiên Envato HẾT HẠN — thử tự đăng nhập lại...
online: deb9c66d LỖI (Sync API inside the asyncio loop) — giữ preview
online: 1171e0c1 LỖI (Target page... has been closed) — giữ preview
online: 46ca7aab LỖI (...closed) — giữ preview
online: 7ec1b963 LỖI (...closed) — giữ preview
```

`tai_nhieu` mở `sync_playwright()` (`tai_sach.py:138`), rồi khi thấy phiên hết
hạn lại gọi `phien.dang_nhap()` — hàm đó **mở `sync_playwright()` lần nữa**
(`phien.py:111`). Playwright CẤM lồng. **Không dính dáng FastAPI** — tái hiện
bằng 3 dòng Python thuần, ra đúng cả hai dòng lỗi trên.

Chuỗi hỏng: phiên hết hạn → `dang_nhap` trong khối `with` → ném lỗi →
`ctx.close()` đã gọi trước đó nên context chết → `break` → **mọi clip còn lại
giữ preview watermark**.

Tức là **phiên hết hạn ĐÚNG MỘT LẦN là cả chương dính**. Và tool báo *"phiên
sống rồi bấm Online lại là sạch"* — người dựng bấm lại vẫn hỏng y hệt, vì lỗi
ở mã chứ không ở phiên.

### Đo thật 10/09

| | |
|---|---|
| Chương gần nhất dính | **5/15**, 17 miếng (đọc `thay_mau.json`) |
| Toàn bộ hợp đồng | **10/41 chương (24%)** sẽ dính |
| Tỉ lệ miếng | **42/1187 (3.5%)** |
| Phiên Envato hiện tại | **CHẾT** — kiểm bằng Chrome thật, trang hiện nút Sign in |
| Tài khoản trong két | có đủ email + mật khẩu |

### Đã vá

| # | Thay đổi | File |
|---|---|---|
| 1 | Bỏ `dang_nhap` khỏi trong khối `sync_playwright`; chỉ báo `het_phien` ra ngoài | `sourcer/tai_sach.py` |
| 2 | `tai_nhieu_tu_cuu()` — đóng phiên hẳn rồi mới đăng nhập, chạy lại **một** lượt | `sourcer/tai_sach.py` |
| 3 | `tai_nhieu(..., bao_het_phien=list)` — giữ nguyên KIỂU TRẢ (nhiều nơi gọi) | `sourcer/tai_sach.py` |
| 4 | Hai caller đổi sang bản tự cứu | `offline/thay_mau.py`, `web/server.py` |
| 5 | `se_dinh_watermark()` + `soat_truoc_pha` **chặn hẳn** (user chốt) | `offline/thay_mau.py` |
| 6 | Mỗi miếng bị chặn kèm `ly_do`; server + UI in **hai lời khác nhau** | `web/server.py`, `index.html` |

**KHÔNG gộp watermark vào `clip_hong`**: watermark không phải clip hỏng — clip
vẫn sống, chỉ chưa tải bản sạch. Gộp thì khay gợi ý tự loại nó, mà đó là clip
dùng được ngay sau khi phiên Envato sống lại.

**Hai lý do = hai cách xử lý:**

| Lý do | Người dựng phải làm |
|---|---|
| clip hỏng / hết hạn | **THAY** clip khác |
| Envato chưa có bản sạch | **đăng nhập Envato** rồi Export lại — không cần thay gì |

Gộp một câu là bắt người dựng thay 42 miếng lành trong khi chỉ cần đăng nhập
một lần. Đúng BH15 rút ra sáng nay.

### Suite bắt được 2 test cũ (đúng việc của nó)

`test_chan_export.py` và `test_dung_som_va_tai_muon.py` dựng clip envato
**không có `path_local`** — theo luật mới đó chính là watermark, nên miếng 0
bị bắt trước khi tới miếng chết thật. Sửa helper cho clip envato mặc định CÓ
bản sạch (trạng thái bình thường), giữ đúng ý định gốc của hai file đó là kiểm
đường link chết.

### CÒN LẠI — việc chỉ user làm được

Phiên Envato đang chết. Đăng nhập lại cần **bấm captcha trên desktop server**
(`dang_nhap` mở `headless=False`), không tự động được. Sau khi user đăng nhập:
chạy `tai_nhieu_tu_cuu` tải bản sạch cho 42 miếng, rồi 10 chương kia Export lại
là sạch.

### PHÁT HIỆN THỨ BA — chỉ báo phiên trên giao diện BÁO XANH DỐI

Trong lúc vá, kiểm `/api/phien` trên production:

```
{"envato":{"co_tai_khoan":true,"co_phien":true}, ...}
```

**Xanh** — trong khi mở Chrome thật thì Envato hiện nút Sign in, tức phiên
**CHẾT**. `co_phien()` chỉ kiểm cookie CÓ MẶT, không kiểm CÒN HẠN — chính
docstring của nó viết: *"Kiểm thật sự (còn hạn hay không) diễn ra lúc mở
trang"*.

Đây mới là lý do **không ai đi đăng nhập lại suốt 3 ngày**: chấm trên thanh
Sequence vẫn xanh, nhìn vào tưởng ổn.

Bằng chứng phiên từng sống nằm sẵn trong DB — sổ `giay_phep` ghi mỗi lần tải
bản sạch thành công:

```
lan cuoi tai ban sach: 2026-09-07 15:07:46 | tong 94 giay phep
```

**3 ngày trước**, khớp đúng lúc hieuvn/haint bắt đầu thấy watermark.

Vá: `phien.lan_cuoi_tai()` đọc `max(ngay)` của `giay_phep`, `trang_thai()` trả
kèm. Giao diện đổi **⚠ vàng** khi ≥2 ngày chưa tải được bản sạch, tooltip ghi
rõ *"N ngày chưa tải được bản sạch, phiên có thể đã chết: bấm để đăng nhập
lại"*. Đo được mà không tốn một lượt mở trình duyệt.

### BH16 — Chỉ báo trạng thái phải dựa trên BẰNG CHỨNG, không dựa trên sự có mặt

`co_phien` trả True vì file cookie còn nằm đó — đúng nghĩa đen "đã từng đăng
nhập", nhưng người dùng đọc chấm xanh là "dùng được bây giờ". Khoảng cách giữa
hai nghĩa đó nuốt mất 3 ngày và 10 chương.

Luật: chỉ báo sống/chết phải neo vào **lần cuối làm được việc thật** (ở đây là
tải được bản sạch), không neo vào việc file cấu hình có tồn tại. Nếu chỉ có dữ
liệu "có mặt" thì phải nói đúng chừng đó — "có phiên" chứ không phải "phiên
sống".
