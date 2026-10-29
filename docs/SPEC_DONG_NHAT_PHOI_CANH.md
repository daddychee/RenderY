# Spec: đồng nhất phối cảnh giữa các shot drama (giữ trục, giữ phòng)

> **Trạng thái: SPEC TỪ ĐO THẬT, CHƯA CODE vào app.** Lập 29/10/2026 theo yêu cầu user:
> *"tốt hơn nhiều rồi. tạo thử video. ghi lại spec đồng nhất phối cảnh này"*.
> Đo trên **1 clip** (DM001 P031, 4 shot, hai người ngồi). Phần "Chưa đo" ở cuối là chỗ chưa được suy rộng.
> Số liệu và ảnh: `scratchpad/phim-padoma-28-10/DO_DOT0.md` (mục "P031 lần 2", "P031 lần 3–4"),
> script thử `ghep_dm4.py` / `gen_dm4.py` (scratchpad phiên 9d36690e), kết quả `scratchpad/dm001/shot4/`.

## Vấn đề

Mỗi shot một video (Grok i2v từ ảnh khung đầu). Mỗi ảnh khung đầu vẽ riêng thì phòng, chỗ ngồi và hướng nhìn nhảy giữa các shot. User báo hai lần:
1. *"người đang ngồi trên ghế nhưng khi nói lại bay ra bàn"*
2. *"vẫn sai vị trí. Nia ngồi sát cửa sổ và ở bên phải bà Hattie"*

Sau lần 2 là cửa sổ hiện sau lưng Hattie, trong khi ở shot dàn cảnh chỗ đó là tường treo tranh.

## Đã thử và kết quả

| Lần | Cách | Kết quả |
|---|---|---|
| 1 | Mỗi shot vẽ riêng: tấm nhân vật + tấm nơi chốn | Chỗ ngồi đúng 2/4; Hattie đứng dậy bên bàn |
| 2 | Image 1 = **cả ảnh dàn cảnh**, kèm câu giữ chỗ | Chỗ ngồi đúng 4/4. **Phông sau lưng đúng 0/3, hướng nhìn đúng 1/3**, có người thừa ở hậu cảnh: model giữ hướng máy và bố cục của ảnh dàn cảnh |
| 3 | Vẽ ảnh toàn cảnh **nhìn ngược** | Lấy ảnh dàn cảnh làm ref thì model không quay máy. Lấy tấm nơi chốn làm ref thì ra căn phòng khác. **User bác:** *"đổi hẳn một bối cảnh thay vì giải quyết trục và góc máy"* |
| **4** | **Luật 180° + mảnh cắt ảnh dàn cảnh** (dưới đây) | **Phông đúng 3/3, hướng nhìn đúng 3/3, chỗ ngồi đúng 3/3**, phòng và ánh sáng giữ như shot dàn cảnh. User: *"tốt hơn nhiều rồi"* |

## Luật

**L1. Ảnh dàn cảnh trước, duyệt trước.**
- Mỗi trường đoạn có một ảnh dàn cảnh (WS) thấy đủ mọi người và phông nền sau lưng từng người. Đây là `ref` của bản ghi `truong_doan` trong kho, ô `td` của clip.
- Mọi shot khác của trường đoạn đều bám theo ảnh này. Ảnh dàn cảnh sai thì sửa ảnh dàn cảnh, không sửa ở từng shot.

**L2. Luật trục 180°: mọi máy đứng cùng phía với máy của ảnh dàn cảnh.**
- Người bên trái ảnh dàn cảnh luôn ở bên trái và nhìn sang phải; người bên phải luôn ở bên phải và nhìn sang trái.
- **Không** vẽ ảnh toàn cảnh nhìn ngược. **Không** dùng tấm nơi chốn cho shot sau ảnh dàn cảnh, vì nó vẽ lại phòng.
- Kịch bản cần thấy bức tường đối diện (cửa ra vào chẳng hạn) thì đó là một **trường đoạn mới** có ảnh dàn cảnh mới, không phải việc của từng shot.

**L3. Image 1 của mỗi shot = mảnh cắt ảnh dàn cảnh quanh người mà máy hướng tới.**
- Mảnh cắt chứa người đó cùng phông sau lưng họ.
- Không đưa cả ảnh dàn cảnh: model sẽ giữ bố cục toàn cảnh (lần 2).
- Shot qua vai thì cắt quanh **người ở xa, quay mặt về máy**. Người ở tiền cảnh lấy từ tấm nhân vật.
- Mảnh cắt phải tránh viền đen: ảnh dàn cảnh P031 có viền đen từ x≈2665/2752.
- Ở P031 hai mảnh cắt có tỉ lệ 16:9, cùng dải dọc y 0,30–0,70 của ảnh. Mảnh trái lấy x 0,115–0,515, mảnh phải lấy x 0,56–0,96.

**L4. Ảnh 2… = tấm nhân vật** của những người có mặt trong khung, dùng lời dặn `LOI_REF["nhan_vat"]` như hiện nay.

**L5. Năm câu Python ghép, theo vị trí trái/phải trong ảnh dàn cảnh** (S = người máy hướng tới, O = người kia; chữ đúng như đã chạy):

| Câu | Mẫu |
|---|---|
| Lời dặn Image 1 | `Image 1 is a crop of the master wide shot of this scene: {S ở đâu, theo đồ đạc}. Keep this exact room, background and light; it is the same moment.` |
| Máy đứng đâu | Một người: `Camera position: on the same side of the room as the master shot, near {O}'s {chỗ ngồi}, angled toward {S}.` · Qua vai: `… just behind {O}'s {left\|right} shoulder, angled toward {S}.` (vai phía máy dàn cảnh: O bên trái nhìn sang phải thì vai **phải**, O bên phải thì vai **trái**. Bản đo P031 ghi ngược; sửa 29/10, đo DM002 thấy model bỏ qua chữ vai) |
| Sau lưng là gì | `Behind {S}: {phông}, exactly as in Image 1.` cộng câu phủ định thứ model hay vẽ nhầm (`No window behind Hattie.`) |
| Chỗ ngồi | Theo **đồ đạc và theo nhau**, không theo khung hình: `Nia on the low wooden bench by the windows, Hattie at the right end of the cream sofa, to Nia's right; they face each other across the round coffee table. Seated people stay seated.` |
| Hướng nhìn | O ngoài khung: `{S} looks toward {O}, just off the {right\|left} edge of the frame, not at the camera.` · O trong khung (qua vai): `{S} looks at {O}, toward the {left\|right} of the frame, not at the camera.` · Kèm `{O} is off-screen to the {left\|right} and does not appear.` |

Phía phải/trái trong câu hướng nhìn được suy ra: S ở bên trái ảnh dàn cảnh thì nhìn về bên phải, và ngược lại.

**L6. Bỏ chữ LLM viết sai không gian.**
- Câu `pd.truc` không vào prompt ảnh của shot sau ảnh dàn cảnh. LLM viết câu này theo khung hình ("Hattie sits on the sofa **on the right side of the frame**"), nên ở lần 2 shot cận Nia vẽ thêm Hattie vào hậu cảnh.
- Cụm phông trong `lap` cũng bỏ, ví dụ *"a soft blur of the sofa and window light behind her"*: sau lưng Nia là cửa sổ, sofa là chỗ Hattie ngồi. Phông lấy từ mảnh cắt và câu L5.
- → Luật Breakdown: `lap` chỉ tả khung và người, **không tả phông**. Python soát: `lap` có chữ `behind` thì cảnh báo.

**L7. Prompt video** (Grok i2v, từ ảnh đã duyệt): giữ prompt hiện có, bỏ cụm phông như L6, và chèn **câu hướng nhìn** L5 ngay sau dòng mặt/thân.

**L8. Model ảnh lấy theo cài đặt General, không ghi cứng.** Lần 4 đo bằng **GPT Image 2**:
- 3/3 lần nộp ra ảnh, 0 hỏng, 55–102 s một ảnh, **5 credit/ảnh**.
- Nano Banana Pro chưa thử theo cách này.

## Ai làm gì (luật cứng 4: Python đo, LLM hiểu/sinh)

| Phần | Ai | Ghi chú |
|---|---|---|
| Ảnh dàn cảnh | Model ảnh, user duyệt | Luồng Gen Image → Duyệt hiện có |
| Ai trái, ai phải trong ảnh dàn cảnh | **Chưa chốt**: user đánh dấu hoặc LLM ghi lúc Breakdown | Python suy ra hướng nhìn và vai từ dữ liệu này |
| Khung cắt | Python, mặc định nửa trái/nửa phải (L3) và tự cắt viền đen | **Chưa chốt** có cho user kéo khung trên trang không |
| Máy hướng tới ai (S) | Python: người nói (`noi`) nếu có trong `co_mat`, không thì `co_mat` một người. Qua vai: bỏ người tiền cảnh ("Qua vai X" trong chữ shot) ra trước | Người dựng vẫn sửa tay được (ô Máy hướng tới) |
| Câu phông sau lưng, câu chỗ ngồi | **Chưa chốt**: LLM viết một lần cho trường đoạn từ prompt ảnh dàn cảnh, hoặc user viết | Lần 4 viết tay |
| Ghép prompt, chèn câu, bỏ cụm sai | Python | Như `ghep_dm4.py` |

## Chưa đo (không suy rộng khi chưa chạy)

- Người **đứng hoặc di chuyển** (P022, P051), **ba người trở lên**, người đổi chỗ giữa trường đoạn.
- Shot máy dời chỗ (tilt, track): ảnh khung đầu từng vẽ khung CUỐI (đo 28/10).
- Câu phông **chung chung** (`the same background as in Image 1`) thay cho câu tả cụ thể.
- Cỡ cận: mã CU vẫn ra MCU (mặt cao khoảng 0,44 khung).
- Tóc đổi kiểu giữa các shot: ở shot qua vai, tóc Nia buộc đuôi bằng dây chun, các shot khác tóc thả.
- Nano Banana Pro theo cách mảnh cắt.

## Kết quả video lần 4 (29/10 00:28–00:30, Grok i2v, 324 credit)

Nháp: `scratchpad/dm001/dung_P031_v4.mp4` (14,4 s). Lưới khung: `luoi_P031_v4.jpg`. Khung theo giây: `soi_P031_v4.jpg`.

| Shot | Phông suốt clip | Hướng nhìn suốt clip | Thoại |
|---|---|---|---|
| 2 · MCU qua vai, đẩy vào, 10 s | **Trôi** từ khoảng 5 s: tranh thực vật bên trái thành ảnh chân dung, một cây đèn hiện ở góc trên trái. Máy giống lia sang trái hơn là đẩy vào (số phóng 1,36 nhưng sai số 29, không tin được) | Phần lớn nhìn về Nia; lúc nói có đoạn nhìn gần ống kính | đúng 18/18 từ |
| 3 · CU, 6 s | Giữ: cửa sổ, rèm, sofa | **Sai lúc nói:** ảnh khung đầu nhìn sang phải, nhưng suốt câu thoại (2,3–3,5 s) Nia nhìn thẳng ống kính. Prompt *"glances down then back up"* kéo mắt về ống kính | đúng 6/6 |
| 4 · MCU, 6 s | Giữ: kệ, tranh, tấm ốp | Nhìn sang trái suốt clip ✓ | đúng 5/5 |

- Phông giữ đúng 2/3 clip, hướng nhìn giữ đúng 2/3 clip (ảnh khung đầu 3/3/3).
- Nối cứng, không chồng mờ. Mỗi clip 63–103 s.
- **→ Ảnh khung đầu giải được trục và góc máy, nhưng video i2v vẫn có thể trôi**, nhất là clip dài có máy động.
- Hướng sửa (chưa chạy):
  - (a) Gắn câu hướng nhìn vào chính câu hành động: *"glances down then back up **toward Hattie, off the right edge of the frame**"*.
  - (b) Shot đẩy vào: thêm câu *"the background stays exactly as in the first frame"*, hoặc dùng 6 s thay cho 10 s.

---

## Thiết kế code (29/10, user chốt: "1 LLM tự đánh dấu · 2 có · 3 LLM làm · 4 không cần chạy · code luôn")

Luồng mới: **mỗi shot một video** (Grok i2v từ ảnh khung đầu đã duyệt), ảnh khung đầu cắt từ **ảnh dàn cảnh** của cảnh.
Đường cũ (một video nhiều shot cho cả clip) **giữ nguyên ở máy chủ** (Karpathy #3), trang drama thôi hiện nút đó.

### Chia file (ba phiên làm song song, KHÔNG sửa file của nhau)

| Phiên | File được sửa |
|---|---|
| bb (điều phối) | `treatment/app.py`, `treatment/kho.py`, `treatment/dong.py`, `tests/test_treatment_drama_shot_api.py` (mới) |
| trợ lý A | `treatment/drama.py`, `treatment/dich.py`, `tests/test_treatment_drama_shot.py` (mới) |
| trợ lý B | `treatment/static/treatment.html`, `tests/test_treatment_drama_shot_chrome.py` (mới) |

### Dữ liệu

- **`sh[k]`** (người dựng sửa qua PATCH `sh`), thêm khoá:
  - `sid`: mã shot bất biến, máy chủ đặt lúc Breakdown, dạng `s` + 6 hex. PATCH phải giữ nguyên.
  - `co_mat`: danh sách tên người TRONG KHUNG, Breakdown LLM viết.
  - `huong`: tên người máy hướng tới. Rỗng thì Python tự suy.
  - `gi`: `"6"` / `"10"` / `"15"`. Rỗng thì Python tự tính.
- **canh `ss`** (CHỈ máy chủ viết, nằm trong `TRUONG_MAY`): JSON `{sid: {"duyet": "1", "vid": "<task>"}}`.
- **File:** ảnh `kho.duong_anh(tap, f"{id}-{sid}")`, video `kho.duong_video(tap, f"{id}-{sid}")`.
- **`pd`**, phần chung của cảnh: mỗi clip mang một bản như `look`/`truc_canh`/`nen`. Thêm các khoá:
  - `ben` `{Tên: "trai"|"phai"|"giua"}`: vị trí trong ảnh dàn cảnh (LLM đánh dấu).
  - `phong` `{Tên: "<tiếng Anh: phông sau lưng người đó, kèm câu phủ định nếu cần>"}`.
  - `cho`: câu chỗ ngồi/đứng theo đồ đạc và theo nhau, không theo khung hình.
  - `dan`: tả ảnh dàn cảnh (WS, ai ở đâu, khớp `ben`).
  - `cat` `{Tên: [x0, y0, x1, y1]}`, tỉ lệ 0–1. Chỉ có khi người dựng kéo khung; vắng thì dùng `khung_cat(ben)`.
- **Ảnh dàn cảnh** = ref của mục sổ `td_<id clip đầu dòng>` (loại `truong_doan`). Mọi clip của dòng có `td` = mã đó.
  - Duyệt = `vet(td, "dan_duyet")` bằng mtime file ảnh. Vẽ lại ảnh là tự hết duyệt.

### `drama.py` (trợ lý A), hàm thuần

- `BEN = ("trai", "phai", "giua")`.
- `khung_cat(ben) -> (x0, y0, x1, y1)`:
  - trai `(0.115, 0.30, 0.515, 0.70)`;
  - phai `(0.56, 0.30, 0.96, 0.70)`;
  - giua `(0.30, 0.30, 0.70, 0.70)`.
- `cat_master(master: Path, hop, dich: Path) -> Path`: bỏ viền đen trước (cột/hàng trung bình < 12), rồi cắt theo tỉ lệ của ảnh đã bỏ viền.
- `chu_the(s, lt) -> str`, theo thứ tự ưu tiên:
  1. `s["huong"]` nếu có trong `co_mat`;
  2. người nói của shot nếu có trong `co_mat`;
  3. `co_mat` chỉ một người thì lấy người đó;
  4. còn lại trả `""`.
  - Shot qua vai: bước 2–3 chỉ xét người KHÔNG ở tiền cảnh. Người tiền cảnh `nguoi_tien_canh(s)` là X trong "Qua vai X" của `s["t"]`; máy đứng sau vai người đó. Đọc được X thì luật trên áp, không đọc được thì giữ luật cũ.
  - Vì sao: ngày 29/10, DM002 C1 có 8/13 shot qua vai chọn trúng người nói đang quay lưng, hoặc rỗng (shot im, app gửi nguyên ảnh dàn cảnh). P004 shot 4 vì thế kéo Evelyn ra tiền cảnh.
  - `nhac_qua_vai(s, lt)` nhắc người dựng khi chưa rõ máy hướng tới ai. Không chặn.
- `nhac_khung(pd, s, lt)` nhắc khi mảnh cắt quanh S có thể dính người KHÔNG có trong shot, mà shot lại có từ 2 người trong khung. Không chặn.
  - Vì sao: P004 shot 4 đo ngày 29/10. Khung Hattie dính Brooke đứng giữa, model biến Brooke thành Evelyn đứng cạnh Hattie. Kéo khung Hattie x 0–0,335 thì ảnh đạt.
  - Shot một người không nhắc: 7/7 ảnh Hattie một mình vẫn sạch.
  - Chỗ đứng là ước lượng, lấy theo thứ tự:
    1. tâm khung người dựng đã kéo;
    2. chưa kéo thì theo `hang`: tâm `(i + 0,5)/n`, áp cho cảnh từ 3 người;
    3. không có `hang` thì `TAM_BEN` (trái 0,2 · giữa 0,5 · phải 0,8).
    Cả ba đều tính ± 0,08.
  - Khung của S lấy từ `khung_cua(pd, ten)`. Đây cũng là hàm app dùng để cắt thật (`_hop`), nên nhắc luôn khớp mảnh cắt.
  - Đo trên DM002: nhắc 2/76 shot, cả 2 đúng (kiểm bằng ảnh thật).
- `ca_canh(s) -> bool`: dùng NGUYÊN ảnh dàn cảnh khi có từ 2 người trong khung trở lên và `goc != "ots"`.
- `giay_shot(s, lt) -> int`: lấy `s["gi"]` nếu hợp lệ. Không có thì 10 khi `số từ / 3 + 1 > 5`, ngược lại 6.
- `nhac_lap(lap) -> list[str]`: `lap` tả phông (chữ `behind`) thì trả câu nhắc. Chỉ nhắc, không chặn (luật cứng 5).
- `prompt_dan_canh(pd, nguoi: list[dict], noi: dict | None) -> str`. Ảnh gửi theo thứ tự `[noi nếu có] + nguoi`.
- `prompt_anh_shot(pd, s, k, t, nguoi: dict[str, dict], do: list[dict], kh: str) -> str`:
  - `kh` = câu khung KHÔNG có máy; app ghép bằng `khung_shot(dict(s, cd=""))`.
  - Ảnh gửi theo thứ tự:
    1. Image 1: mảnh cắt quanh `chu_the`, hoặc nguyên ảnh dàn cảnh khi `ca_canh`;
    2. tấm nhân vật theo ĐÚNG thứ tự `s["co_mat"]`;
    3. `do`.
- `prompt_video_shot(pd, s, k, t, nguoi, tieng: dict[str, str], do, kh: str, may: str, giay: int) -> str`: khuôn `ghep_dm.py` (DM001) cộng câu hướng nhìn gắn vào câu hành động (L7).
- `dich.py`:
  - `LENH_DRAMA_CANH` trả thêm `ben`/`phong`/`cho`/`dan`.
  - `LENH_DRAMA_CLIP`: `lap` không tả phông.

### Route mới (bb), JSON

| Route | Việc |
|---|---|
| `GET  /api/tap/{tap}/{chuong}/dong/{i}/dan-canh` | `{td, co_anh, duyet, ref_v, nguoi: [tên], ben, cat (khung đang dùng), san (đã có pd.dan), prompt}` |
| `POST /api/tap/{tap}/{chuong}/dong/{i}/dan-canh` | vẽ ảnh dàn cảnh (nơi chốn + tấm mọi người có mặt) → `{ok}` |
| `POST /api/tap/{tap}/{chuong}/dong/{i}/dan-canh/duyet` | `{ok}` |
| `PUT  /api/tap/{tap}/{chuong}/dong/{i}/dan-canh/cat` | thân `{cat: {Tên: [x0, y0, x1, y1]}}`, kiểm 0 ≤ x0 < x1 ≤ 1, cạnh ≥ 0,1 → `{ok}` |
| `GET  /api/tap/{tap}/so/{td}/ref` | (đã có) ảnh dàn cảnh |
| `GET  /api/tap/{tap}/{chuong}/canh/{ma}/shot` | `[{sid, k, co_anh, duyet, dang (có task), co_video, giay, chu_the, anh_v, video_v, nhac: []}]` |
| `POST /api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/anh` | cần ảnh dàn cảnh đã duyệt + `pd` → `{ok}` |
| `GET  /api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/anh` | PNG |
| `POST /api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/duyet` | `{ok}` |
| `POST /api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/video` | cần duyệt → `{ok, vid}` |
| `POST /api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/video-kiem` | `{trang_thai: xong\|dang\|hong\|chua, loi?}` |
| `GET  /api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/video` | MP4 |
| `GET  /api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/prompt` | `{anh, video}` đúng chuỗi sẽ gửi |

### Quyết định lúc code (29/10)

- **`vi_tri`** `{Tên: cụm bắt đầu bằng giới từ}` (LLM viết ở lượt phần chung). Dùng cho câu Image 1 ("…of this scene: {S} {vi_tri}") và câu máy ("near {O}'s place {vi_tri[O]}"), để chữ giữ sát bản đo. Vắng thì dùng "around X" / "near X".
- **Toạ độ khung cắt** là tỉ lệ trên ẢNH GỐC, như người dựng thấy trên trang. Máy chủ cắt xong thì kẹp vào vùng không viền đen.
- **Người kia (O)** ở shot một người: lấy người nói của shot nếu khác S, không thì người đầu tiên khác S trong clip. Cảnh 3 người trở lên **chưa đo**, có thể chọn sai.
- **Shot nhiều người không qua vai** gửi nguyên ảnh dàn cảnh, không có câu máy và câu hướng nhìn.
- **Đồ vật** đi theo shot nào nhắc tên nó trong chữ `t` của shot (tiếng Việt, đúng tên trong sổ). Prompt video i2v không gửi ảnh đồ vật, vì Grok i2v chỉ nhận một ảnh.
- **Đường cũ** (một video nhiều shot cho cả clip) không gửi ảnh dàn cảnh, vì prompt cũ đánh số ảnh theo `ts`.
- **Breakdown lại** thì shot nhận mã mới; dấu duyệt và task của shot cũ bị bỏ.
- **Duyệt ảnh dàn cảnh** gắn với giờ sửa file: vẽ lại là tự hết duyệt. Viết lại phần chung sau khi đã vẽ thì trang nhắc (`cu`), không chặn.
- **Chưa làm:** dấu "cũ" từng shot (prompt/ảnh/video đổi sau lần gen); prompt sửa tay từng shot (`pat`/`pvt`).
- **Cảnh từ 3 người** (29/10, sau lần chạy thật C005; user duyệt): LLM ghi thêm `hang` là thứ tự trái → phải trong ảnh dàn cảnh. Khung mặc định chia bề ngang theo thứ tự đó: tâm `(i + 0,5)/n`, rộng `1/n + 0,04` (tối đa 0,4), tâm dọc 0,5, rộng = cao.
  - Cảnh 2 người giữ hộp đã đo.
  - Lề chọn theo vị trí thật của C005: lề rộng hơn thì khung người sát mép trùm sang người bên cạnh.
  - Người đứng cách đều nhau thì khớp; đứng không đều thì người dựng kéo khung.
  - Đã thử trên hai cảnh: C005 (DM001) và DM002 C1 dòng 1 (4 người). Ở dòng 1, khung `ben` "giua" của Nia trùm Brooke; khung theo `hang` thì mỗi khung chỉ chứa tâm người đó.
  - **Dải dọc giữ tâm 0,5, kể cả khi mất đầu người đứng** (đo 29/10; user giao Claude tự quyết, Claude chọn không làm dải dọc theo đứng/ngồi):
    - 5/5 mảnh cắt Brooke đứng ở prod mất đầu, nhưng ảnh ra vẫn đúng mặt và đúng phông, vì mặt lấy từ tấm nhân vật.
    - Shot qua vai hướng Nia đứng (`s7a1cbc`, 10 cr, 1 ảnh mỗi bản): mảnh cắt mất đầu và có đầu đều ra ảnh đúng.
- **Khung người dựng kéo (`pd.cat`) đi theo ẢNH dàn cảnh, không theo chữ:**
  - Bấm "Viết prompt cảnh" lại (`_phan_chung`) thì giữ khung của người còn trong cảnh. Trước đây nút này xoá khung mà không báo.
  - Vẽ lại ảnh dàn cảnh (`_ve_dan`) thì bỏ hết khung. Thẻ shot sẽ nhắc nếu khung mặc định dính người ngoài shot.
