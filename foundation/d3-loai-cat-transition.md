# D3 — LOẠI CẮT & TRANSITION (ngữ pháp nối hai shot)

> **Vị trí:** ngữ pháp dựng cấp RANH GIỚI SHOT — nằm dưới [[d1-pacing]] (pacing quyết
> KHI NÀO cắt; d3 quyết cắt KIỂU GÌ). Gộp D2 cũ (loại cắt) + F4 cũ (transition).
> Không có nguyên văn user riêng — chưng cất từ FOUNDATION.md cũ (§3, §9) + code thật.
> **Trạng thái phần 3: DỰ KIẾN 🔸.**

---

## 1. Là gì

**Loại cắt** — cách hai shot nối nhau:
- **Hard cut** — cắt thẳng, mặc định, **90–95% mọi trường hợp**;
- **J-cut / L-cut** — âm thanh cảnh sau vào trước hình / âm cảnh trước kéo sang hình sau
  → mượt, chuyên nghiệp (thường ở ranh giới chương);
- **Cutaway** — chèn cảnh phụ bổ nghĩa/che vết (chính là beat chêm `visual_anchor=false`);
- **Montage** — chuỗi cảnh ngắn nén thời gian (chính là multi-shot F6);
- **Smash cut** — cắt đột ngột tương phản (ồn→im lặng) — hiếm, chủ đích;
- **Match cut** — nối bằng hình dạng/chuyển động tương đồng — đẳng cấp, hiếm.

**Transition (hiệu ứng chuyển):** luật sắt của editor giỏi — **95% hard cut; whip/blur/
glitch CHỈ khi đổi chương hoặc đổi năng lượng. Lạm transition = dấu hiệu nghiệp dư.**

**Khi nào cắt (Walter Murch):** cảm xúc > câu chuyện > nhịp — cắt khi một ý đã trọn.
Trong tool: ranh giới beat đặt tại TỪ kết thúc mệnh đề (cut on word) + mép cắt hút về
khoảng lặng gần nhất (snap to silence).

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Vị trí ranh giới** | Trong lòng chương → hard cut gần như tuyệt đối; ranh giới chương → được phép "sang" hơn (J/L-cut, 1 transition nhẹ, đổi nhạc đã có sẵn). |
| **Năng lượng 2 bên mép cắt** | Đổi năng lượng mạnh (calm→climax) là chỗ hợp lệ hiếm hoi cho transition/smash cut. |
| **Nhịp thoại thật** | Mép cắt rơi vào khoảng lặng của voice thì mượt tự nhiên — không cần hiệu ứng che. |
| **Mood/tone** | Video trầm → không whip/glitch; transition (nếu dùng) phải cùng tone ([[b1-mood-tone]]). |
| **Niche** | Tần suất + loại transition mỗi niche khác nhau; nhiều niche viral 100% hard cut → DNA quyết. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Hiện trạng code: 100% hard cut — VÀ ĐÓ LÀ ĐÚNG LUẬT

- Cắt tại ranh giới beat = **cut on word** (ranh giới đặt ở từ có dấu câu — a1/NT4);
- Mép cắt voice **hút về khoảng lặng** (`cutter/silence.py`, dò -35dB) — cắt "êm tai";
- **Chưa từng chèn transition effect nào** — trùng khớp luật 95%: trạng thái hôm nay
  không phải thiếu tính năng, mà là mặc định ĐÚNG của thể loại;
- Ranh giới chương đã có "chuyển" TỰ NHIÊN: đổi bài nhạc + crossfade 3s
  ([[e1-sound-design-nhac]]) + thường kèm hình thở — khán giả CẢM được sang chương
  mà không cần hiệu ứng hình nào.

### Hướng dự kiến 🔸 (thứ tự chỉ mở khi có nhu cầu thật từ cổng mắt/DNA)

1. **Giữ nguyên hard cut toàn tuyến** cho tới khi DNA niche chứng minh niche cần khác.
2. Nếu mở: **J/L-cut ở ranh giới chương** (kéo/đẩy audio vài trăm ms quanh mép) — chạm
   timeline nên phải qua CỔNG DUYỆT VẬN HÀNH riêng trước khi code.
3. Transition hình (whip/blur) tại ranh giới chương: kiểm pycapcut hỗ trợ transition
   của CapCut tới đâu rồi mới bàn — có thể để editor tự thêm ở 20% cuối (rẻ nhất).
4. Match cut: kỹ thuật NÃO thuần (chọn cặp footage tương đồng hình dạng ở 2 beat kề) —
   để rất sau, cần vision + DNA.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Hard cut mặc định 95% | assembler đặt segment kề nhau, không effect | (a) | ✅ đã có — mặc định đúng |
| Cut on word (cắt khi ý trọn) | ranh giới beat tại từ có dấu câu (a1) | (a) | ✅ đã có |
| Cắt tại chỗ nghỉ voice | `cutter/silence.py` snap mép về khoảng lặng | (a) | ✅ đã có |
| Cutaway | beat chêm `visual_anchor=false` | (a) | ✅ đã có |
| Montage/chuỗi cắt nhanh | multi-shot `shot_count` (F6) | (a) | ✅ vừa xong |
| "Chuyển chương cảm được" | đổi nhạc + crossfade + hình thở cuối chương | (a) | ✅ đã có |
| J/L-cut ranh giới chương | kéo audio quanh mép — chạm timeline, cần mô tả vận hành riêng | (b treo) | ⏸ CHƯA mở — chờ nhu cầu thật |
| Transition hình whip/blur | kiểm pycapcut trước; có thể nhường editor 20% cuối | (b treo) | ⏸ CHƯA mở |
| Smash cut / match cut | NÃO chủ đích, hiếm | (c treo) | ⏸ để sau cùng |
| Niche dùng transition gì, tần suất | đo từ video viral | (d) | ❌ Phase B — quyết có mở (b) nào không |

**→ Backlog code rút ra: KHÔNG mở mục nào đợt này.** d3 chủ yếu là luật "ĐỪNG LÀM" —
giá trị lớn nhất của nó là chặn ý định thêm transition bừa trong tương lai.

## 4. Cạm bẫy / ranh giới

- **Thêm transition vì "trông cho có edit".** Lạm transition = nghiệp dư — luật sắt.
  Mặc định hard cut không phải thiếu sót cần sửa.
- **Transition lệch tone** — whip/glitch trong video trầm = giả trân (b1).
- **Che vết cắt xấu bằng hiệu ứng.** Cắt xấu là do mép cắt sai chỗ (không rơi vào lặng,
  cắt giữa cụm) — sửa GỐC ở a1/snap, không dán transition đè lên.
- **J/L-cut đụng timeline mà làm ẩu** — audio lệch mép video là vùng dễ sinh bug
  overlap/hở (bài học SegmentOverlap 1µs). Chỉ mở qua CỔNG DUYỆT VẬN HÀNH.
- **Bịa luật transition cho phễu footage.** d3 là chuyện RANH GIỚI shot lúc assemble,
  không phải tiêu chí chấm/loại ứng viên — không thêm gì vào phễu c5.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| % hard cut vs transition trong video viral niche | quyết có mở J/L-cut, whip/blur không — bằng số, không bằng cảm giác |
| Transition (nếu có) xuất hiện Ở ĐÂU (ranh giới chương? đổi năng lượng?) | luật vị trí nếu mở |
| Niche có smash cut / im lặng đột ngột không | mồi cho NÃO + e1 (im lặng là công cụ âm thanh) |
