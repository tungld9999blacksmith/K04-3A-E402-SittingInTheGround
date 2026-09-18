# ScriptScout — bản mô tả cho người làm backend

Tài liệu này nói **sản phẩm phải làm được gì**, không chỉ nói gọi endpoint nào.
Phần endpoint và kiểu dữ liệu nằm ở `docs/ADAPTER.md`; đọc tài liệu này trước.

Người đọc mục tiêu: người viết backend. Không cần đọc code giao diện.

---

## 1. Ý tưởng, gọn trong một đoạn

Giảng viên đưa một câu mô tả buổi học. Hệ thống **tự đi tìm nguồn trên web**, tự
**chấm độ tin cậy** của từng nguồn, rút ra các **dữ kiện** từ nguồn, rồi viết một
**kịch bản video bài giảng** trong đó *mọi câu có nội dung sự thật đều truy được về
một đoạn văn cụ thể trong một nguồn cụ thể*.

Giá trị nằm ở câu cuối. Một mô hình ngôn ngữ viết kịch bản trong ba mươi giây; cái
không ai làm sẵn cho giảng viên là **bằng chứng**. Vì vậy điều backend phải bảo vệ
không phải "kịch bản hay", mà là:

> **Mỗi câu khẳng định trong kịch bản đều chỉ được ra một đoạn trích có thật, và
> người duyệt có thể loại đoạn trích đó đi rồi nhận lại kịch bản đã sửa đúng chỗ.**

Nếu backend không giữ được câu trên thì sản phẩm không còn lý do tồn tại, dù văn
có mượt đến đâu.

### Nói rõ ba việc hệ thống *không* làm

- Không tự quyết một nguồn đáng tin thay cho người. Nó chấm, nó giải thích, người
  duyệt chốt.
- Không viết thay khi thiếu bằng chứng. Thiếu bằng chứng thì câu đó phải bị đánh
  dấu, hoặc bị bỏ, không phải viết lấp cho đủ.
- Không dựng video. Đầu ra là kịch bản cộng hồ sơ nguồn, đúng hai tệp JSON mà ban
  tổ chức quy định.

---

## 2. Mô hình dữ liệu ba tầng, và vì sao phải là ba tầng

```
nguồn (source)  ──nhiều──>  thông tin (claim)  ──nhiều──>  câu (sentence)
   n01                          t01                          câu 3
```

Một câu **không** trỏ thẳng vào nguồn. Câu trỏ vào **mã dữ kiện** (`t01`), dữ kiện
mới giữ các đoạn trích từ nguồn. Lớp trung gian này không phải cho đẹp; nó là thứ
làm được ba việc sau, mà mô hình hai tầng câu→nguồn không làm được:

1. **Đếm đối chiếu.** "Ba nguồn độc lập cùng nói điều này" là thuộc tính của *dữ
   kiện*, không của câu. Một dữ kiện có nhiều đoạn trích từ nhiều nguồn.
2. **Viết lại đúng chỗ.** Người duyệt loại một *dữ kiện*. Hệ thống biết chính xác
   những câu nào dựa vào dữ kiện đó, và chỉ những câu ấy bị sửa.
3. **Một câu tựa vào nhiều dữ kiện.** Câu 10 trong dữ liệu mẫu tựa vào `t04`, `t06`,
   `t07`. Loại một trong ba là đủ để câu đó phải sửa lại.

Đây là mô hình của ban tổ chức, không phải của nhóm. Giữ nguyên tên trường.

### Trường của một nguồn

| Trường | Ý nghĩa |
|---|---|
| `title` | tiêu đề trang |
| `org` | đơn vị hoặc tác giả đứng sau trang |
| `url` | địa chỉ, đã bỏ `https://` |
| `published` | ngày đăng, `dd/mm/yyyy`; rỗng nếu bóc không ra |
| `fetched` | thời điểm hệ thống tải trang, `dd/mm/yyyy hh:mm` |
| `kind` | loại trang: tài liệu chính thức, bài báo, blog, diễn đàn… |
| `lang` | `vi` hoặc `en` |
| `trust` | `cao` \| `trungbinh` \| `thap`, suy ra từ `score` (mục 5); nguồn bị chặn hay không đọc được thì mang luôn `chan` / `khongdoc` |
| `score` | điểm sáu tiêu chí, xem mục 5; nguồn `chan` và `khongdoc` **không có** trường này |
| `why` | **một câu tiếng Việt** giải thích vì sao mức tin cậy như vậy |
| `state` | `dung` \| `loai` \| `chan` \| `khongdoc` (mục 8) |
| `removedWhy` | bắt buộc khi `state` khác `dung` |
| `warn` | cảnh báo khi nguồn dùng được nhưng chỉ dùng được một phần |
| `injected` | nguyên văn khúc lệnh ẩn; bắt buộc khi `state: "chan"` |

`why` không phải trang trí. Người duyệt đọc nó để quyết trong ba giây. Câu này phải
nêu bằng chứng cụ thể ("có tên tác giả và năm xuất bản, khớp với hai nguồn độc lập
khác"), không nêu cảm tính ("nguồn này khá uy tín").

### Trường của một dữ kiện

| Trường | Ý nghĩa |
|---|---|
| `kind` | `Định nghĩa` \| `Ví dụ` \| `Số liệu` \| `Quan hệ` \| `Khuyến nghị` |
| `text` | phát biểu dữ kiện, một câu, tiếng Việt |
| `state` | `daxacminh` \| `chuaxacminh` \| `mauthuan` |
| `evidence[]` | `{src, quote, hit, at}` — xem mục 6 |
| `soNguonXacNhan` | số **tên miền độc lập** đang chống lưng (mục 7) |
| `unverified` | bắt buộc khi `state: "chuaxacminh"` — nói rõ thiếu gì |
| `conflict` | bắt buộc khi `state: "mauthuan"` — hai phương án để người duyệt chọn |

### Trường của một câu kịch bản

| Trường | Ý nghĩa |
|---|---|
| `n` | số thứ tự, liên tục từ 1 |
| `sec` | số phần (`sections[].no`) |
| `kieu` | cách đọc: `ke` \| `giang` \| `nhe` \| `hoi` \| `nhan` |
| `loi` | lời đọc |
| `chu` | chữ trên màn hình, tối đa 40 ký tự |
| `hinh` | ý đồ hình |
| `cls` | mảng mã dữ kiện câu này tựa vào; `[]` nếu là câu chuyển đoạn |
| `dur` | thời lượng dự kiến, giây |

`cl` (một mã, dạng cũ) vẫn được giao diện đọc nhưng **đừng sinh ra nữa**. Luôn trả
`cls`.

---

## 3. Vòng đời một phiên

Nhiều người làm nhiều kịch bản song song. Mỗi kịch bản là một **phiên** (session),
có chủ, có trạng thái.

```
nhap ──> tim ──> duyet ──> xong
 │                 │
 └─── người sửa đề bài ──┘
```

| Trạng thái | Nghĩa | Backend đang giữ gì |
|---|---|---|
| `nhap` | mới mở, chưa có đề bài rõ | chưa có nguồn |
| `tim` | đang tìm nguồn | có kế hoạch, chưa có kịch bản |
| `duyet` | có kịch bản, còn việc phải quyết | đủ nguồn, dữ kiện, kịch bản |
| `xong` | người duyệt đã chốt | như trên, thêm dấu chốt |

`open` trong thông tin phiên là **số việc còn phải quyết**: số dữ kiện đang
`mauthuan` chưa được chọn, cộng số dữ kiện `chuaxacminh` chưa bị loại hay xác nhận.
Giao diện in con số này lên danh sách, nên nó phải đúng.

Mở lại một phiên đã lưu **không** phát lại đoạn hội thoại cũ. Trả về hiện vật: đề
bài, nguồn, dữ kiện, kịch bản. Hội thoại là chuyện của phiên đang diễn ra.

---

## 4. Mười việc backend phải làm

Thứ tự dưới đây là thứ tự người dùng gặp. Mỗi mục nói **phải làm gì**, không chỉ
nói trả về gì.

### 4.1 `listSessions` — danh sách kịch bản

Trả mọi phiên người này được xem, mới nhất trước. Rẻ, gọi mỗi lần mở trang. Không
kèm nguồn hay kịch bản; chỉ phần thông tin đầu phiên cộng `open`.

### 4.2 `openSession` — mở một phiên

Trả toàn bộ hiện vật của phiên. Phiên chưa có kịch bản thì `script: null`, và giao
diện tự mở ở bước hỏi lại.

### 4.3 `createSession` — mở phiên mới

Tạo phiên rỗng, `state: "nhap"`, chủ là người đang đăng nhập. Tiêu đề tạm; **câu
đầu tiên người dùng gõ chính là đề bài**, và tiêu đề phiên nên được đặt lại từ đó.

### 4.4 `clarify` — hỏi lại cho đủ

Đầu vào là đề bài thô cộng những câu trả lời đã có. Việc của bước này là **bù những
chỗ trống khiến việc tìm nguồn đi sai hướng**, không phải phỏng vấn cho đủ lệ.

Bốn chỗ trống đáng hỏi, theo đúng thứ tự ảnh hưởng:

1. **Người học đã biết gì** — quyết định được dùng thuật ngữ nào mà không cần giải
   thích lại.
2. **Kết quả cần đạt** — người học sau video làm được gì. Quyết định dữ kiện nào là
   cốt lõi, dữ kiện nào là trang trí.
3. **Độ dài** — quyết định số câu (mục 4.7).
4. **Giới hạn nguồn** — chỉ tiếng Việt, hay được dùng nguồn tiếng Anh; có phải né
   nguồn thương mại.

Quy tắc: **hỏi tối đa ba câu mỗi lượt**. Nếu đã đoán được từ đề bài thì đừng hỏi.
Trả `satisfied: true` ngay khi đủ để lập kế hoạch, không cần trả lời hết.

`chips` là những câu trả lời gợi ý, hai đến ba cái, ngắn. Đây là việc của backend vì
gợi ý phải phụ thuộc câu vừa hỏi. Không có gợi ý thì trả mảng rỗng.

`ack` là một câu xác nhận đã nghe, tiếng Việt, không nhắc lại nguyên văn.

### 4.5 `plan` — kế hoạch viết dưới dạng văn xuôi

Trả **văn xuôi**, hai đến bốn đoạn, không phải danh sách gạch đầu dòng. Người duyệt
đọc để hiểu hệ thống định làm gì rồi bấm đồng ý; đây là nơi rẻ nhất để chặn một
hướng đi sai, trước khi tiêu tiền gọi mô hình và tải trang.

Kế hoạch phải nói rõ bốn thứ:

- các phần của video và ý mỗi phần đảm nhiệm;
- những câu hỏi sẽ tìm, bằng tiếng nào;
- loại nguồn sẽ ưu tiên và loại sẽ tránh, vì sao;
- những gì sẽ **không** nói tới trong video này.

Kèm `criteria` — sáu tiêu chí chấm nguồn cùng trọng số (mục 5). Trả về ở đây để
người duyệt biết thước đo *trước khi* nhìn điểm, không phải sau.

### 4.6 `research` — đi tìm, đi chấm, đi đối chiếu

Đây là phần nặng nhất, và là phần giao diện chỉ hiển thị chứ không hiểu. Chín bước,
theo đúng thứ tự:

1. **Sinh câu truy vấn.** Từ kế hoạch, sinh câu tìm cho từng phần, cả tiếng Việt và
   tiếng Anh nếu đề bài cho phép. Nhiều góc hỏi khác nhau chứ không phải một câu
   viết lại năm lần: định nghĩa, ví dụ, số liệu, phản biện.
2. **Tải trang.** Bóc nội dung chính, bỏ menu và quảng cáo.
3. **Bóc dữ liệu đầu trang.** Tác giả, ngày đăng, đơn vị. Bóc không ra thì để rỗng
   và để tiêu chí tương ứng ăn 0 điểm — **không suy đoán**.
4. **Chấm sáu tiêu chí** cho từng nguồn (mục 5).
5. **Rút dữ kiện.** Mỗi dữ kiện một phát biểu, kèm đoạn trích **nguyên văn** từ
   trang đã tải.
6. **Tự kiểm dẫn nguồn** (mục 6). Đoạn trích không khớp trang thì bỏ dữ kiện, không
   phải sửa đoạn trích cho khớp.
7. **Đếm đối chiếu độc lập** (mục 7), rồi đặt `state` cho từng dữ kiện.
8. **Phát hiện mâu thuẫn** (mục 9).
9. **Xử nguồn xấu** — chặn, không đọc được, có lệnh ẩn (mục 8).

`onEvent` phát từng dòng nhật ký trong lúc chạy. Mỗi dòng có `kind`:

| `kind` | Khi nào | Giao diện hiển thị |
|---|---|---|
| `ok` | một bước xong bình thường | chữ thường |
| `caution` | có chuyện người cần biết | dấu vàng |
| `stop` | đã chặn một nguồn | dấu đỏ |
| `skip` | bỏ qua một nguồn, không đọc được | dấu xám |

Dòng nhật ký viết cho **người duyệt**, không phải cho người sửa lỗi hệ thống. Viết
được số thì viết số: "chặn ai-tips.example-farm.test, trang chèn lệnh ẩn, đã hạ mức
tin cậy và ghi lại" chứ không phải "injection detected in source 7".

`cost` là tiền thật đã tiêu cho lần chạy này, đơn vị đô, hai chữ số thập phân. Nếu
chưa đo được thì trả `null`, đừng trả số bịa.

### 4.7 `write` — viết kịch bản

Sinh kịch bản theo **đúng mẫu của ban tổ chức**. Kiểm máy được bằng
`node fixtures/check.mjs`, mười ba luật. Những luật hay sai nhất:

- **Không chữ số trong `loi`.** "hai nghìn" chứ không phải "2000". Lời đọc là lời
  đọc.
- **Không viết tắt chưa giải thích.** Nghĩa tiếng Việt đi trước, thuật ngữ tiếng Anh
  nhắc một lần sau đó.
- **`chu` tối đa 40 ký tự**, và câu nào cũng phải có `chu` với `hinh`.
- **Một câu một dòng.**
- **Không mã thời gian** trong lời. Thời lượng nằm ở `dur`.
- **`dur` phải khớp chữ.** Tiếng Việt đọc **2,9 âm tiết một giây**. Đếm âm tiết
  `loi`, chia 2,9, lệch quá 35 phần trăm là sai.
- Tổng `dur` phải nằm gần độ dài người dùng đặt.

Về nội dung: câu chuyển đoạn được để `cls: []`, nhưng **chỉ khi nó thật sự không
khẳng định gì**. "Bây giờ ta xem thử" là câu chuyển. "Cái sau nằm trong cái trước"
là một khẳng định về quan hệ và phải có dữ kiện chống lưng. Lỗi hay gặp nhất của mô
hình là để trống `cls` ở loại câu thứ hai.

Câu tựa vào dữ kiện `chuaxacminh` hoặc `mauthuan` **vẫn được viết ra**, nhưng phải
đúng trạng thái đó để giao diện tô màu cảnh báo. Với dữ kiện `mauthuan` mang số liệu
thì lời đọc **không được nêu con số** cho tới khi người duyệt chọn; viết theo hướng
định tính, hoặc nêu cả hai con số kèm nguồn.

### 4.8 `rewrite` — viết lại đúng chỗ, và đây là phần khó nhất

Đầu vào: kịch bản hiện tại cộng danh sách dữ kiện bị loại. Đầu ra: kịch bản mới cộng
danh sách những gì đã đổi.

**Bảo đảm phải giữ:** câu không tựa vào dữ kiện bị loại thì **trả về y nguyên từng
chữ**. Không "cải thiện" thêm. Người duyệt đã đọc và đồng ý những câu đó; sửa chúng
là phá lòng tin, và làm người ta phải duyệt lại từ đầu.

Ba việc phải làm:

1. **Bỏ** câu mà mọi dữ kiện của nó đều bị loại.
2. **Viết lại** câu còn dữ kiện khác đỡ, hoặc câu nằm cạnh chỗ vừa bị bỏ và giờ mất
   mạch. Câu viết lại mang `was` (lời cũ) để giao diện chỉ được chỗ đổi.
3. **Đánh số lại** liên tục và cập nhật `dur`.

`changed[]` ghi `{n, how}` với `how` là `bo` hoặc `vietlai`. Giao diện dựa vào đây để
nói cho người duyệt biết vừa xảy ra gì, nên đừng bỏ trống.

Sau khi viết lại, chạy lại toàn bộ luật ở mục 4.7. Bỏ một câu rất dễ làm tổng thời
lượng tụt ra ngoài khoảng cho phép.

### 4.9 `addSource` — người duyệt tự thêm nguồn

Người duyệt dán một địa chỉ, kèm ghi chú. Hệ thống tải, bóc, chấm sáu tiêu chí **y
như nguồn tự tìm** — không vì người ta tự thêm mà cho điểm cao hơn — rồi trả về bản
xem trước để người ta xác nhận.

Sau khi nhận, nguồn mới có thể đưa một dữ kiện `chuaxacminh` lên `daxacminh`, nếu nó
là tên miền độc lập thứ hai. Đây là đường thoát chính cho trường hợp "tôi vừa thấy
bài báo này, thêm vào đúng chỗ".

### 4.10 `resolveConflict` — người duyệt chốt bên nào đúng

Người duyệt chọn một trong các số liệu đang mâu thuẫn. Ghi lại lựa chọn **cùng với
người chọn** (`nguoiDuyetChon` trong tệp xuất). Dữ kiện chuyển sang `daxacminh`, và
những câu tựa vào nó được viết lại để nêu đúng con số đã chọn.

Không tự chọn thay. Một hệ thống tự chọn bên nào đúng là một hệ thống vừa xoá mất
thứ nó có mà mô hình ngôn ngữ thường không có: dấu vết ai chịu trách nhiệm.

---

## 5. Sáu tiêu chí chấm nguồn

Sáu tiêu chí này là của ban tổ chức. Trọng số ghi kèm.

| Mã | Tiêu chí | Trọng số |
|---|---|---|
| `author` | Có tên tác giả | 1 |
| `date` | Có ngày đăng | 1 |
| `fresh` | Còn mới so với chủ đề | **2** |
| `cites` | Tự dẫn nguồn | 1 |
| `primary` | Là nguồn gốc, không thuật lại | 1 |
| `record` | Có bề dày về đúng chủ đề | **2** |

`score` là điểm 0 hoặc 1 cho từng mã. Tổng có trọng số tối đa là 8.

| Tổng | `trust` |
|---|---|
| 6–8 | `cao` |
| 4–5 | `trungbinh` |
| 0–3 | `thap` |

Nguồn `chan` và `khongdoc` không được chấm: chưa đọc được nội dung thì không có gì
để chấm. Chúng mang `trust` bằng chính tên trạng thái và không có `score`.

Hai tiêu chí ăn trọng số hai vì hai lý do khác nhau. `fresh` nặng vì chủ đề này
biến động nhanh; một trang đúng năm 2021 có thể sai bây giờ. `record` nặng vì nó là
thứ khó làm giả nhất trong sáu tiêu chí — một trang nội dung rác dựng trong một buổi
chiều vẫn có thể bịa tên tác giả và ngày đăng, nhưng không thể bịa ra bề dày.

`fresh` phải chấm **theo chủ đề**, không theo mốc cố định. Một định nghĩa toán học
từ 1998 vẫn mới; một bài về mô hình tốt nhất hiện nay từ 2023 thì không.

Ba điều cấm khi chấm:

- **Không suy đoán để lấp điểm.** Bóc không ra tác giả thì `author: 0`, dù trang
  trông có vẻ chính thống.
- **Không cho điểm theo tên miền.** `.edu` không tự động được `primary`. Chấm theo
  trang, không theo bảng tên miền có sẵn.
- **Điểm phải dẫn về được `why`.** Câu giải thích và điểm không được nói hai chuyện
  khác nhau.

---

## 6. Tự kiểm dẫn nguồn

Đây là luật cứng nhất trong toàn hệ thống. Mỗi đoạn bằng chứng có bốn trường:

```js
{ src: "n01",
  quote: "Khác với hệ thống dựa trên quy tắc do con người viết ra, học máy rút các quy luật từ chính dữ liệu được cung cấp.",
  hit:   "rút các quy luật từ chính dữ liệu được cung cấp",
  at:    "mục 1.2, đoạn 3" }
```

- `quote` là **nguyên văn** một đoạn của trang. Không rút gọn, không sửa chính tả,
  không dịch.
- `hit` là **khúc nằm trong `quote`** mang đúng ý của dữ kiện. Giao diện tô sáng
  khúc này, nên nó phải xuất hiện **từng ký tự** trong `quote`.
- `at` là chỗ tìm thấy trong trang, cho người muốn tự kiểm.

Bước tự kiểm chạy hai lần đối chiếu:

1. `hit` có nằm nguyên văn trong `quote` không.
2. `quote` có nằm nguyên văn trong nội dung trang đã tải về không.

Sai một trong hai thì **bỏ đoạn bằng chứng đó**. Dữ kiện mất hết bằng chứng thì bỏ
luôn dữ kiện, và câu tựa vào nó phải được viết lại. Tuyệt đối không sửa `quote` cho
khớp với `hit`; đó là làm giả bằng chứng, và nó đúng là thứ hệ thống này tồn tại để
chống.

Cho phép một chút mềm khi so: chuẩn hoá khoảng trắng, chuẩn hoá Unicode dấu tiếng
Việt về một dạng, bỏ phân biệt kiểu nháy. Không cho phép mềm về từ ngữ.

Luật R9 trong `fixtures/check.mjs` kiểm đúng việc này trên dữ liệu mẫu. Chạy nó với
dữ liệu thật của backend là cách rẻ nhất để biết mô hình có đang bịa đoạn trích hay
không.

---

## 7. Đối chiếu độc lập

`soNguonXacNhan` là **số tên miền đăng ký được khác nhau** trong các đoạn bằng chứng
của một dữ kiện, chỉ đếm nguồn `state: "dung"`.

Đếm theo tên miền đăng ký được, không theo địa chỉ máy chủ. `vi.example-edu.test` và
`en.example-edu.test` là **một** nguồn, không phải hai. Ba trang cùng đăng lại một
bản tin cũng là một nguồn nếu chúng dẫn về cùng một chỗ; nếu phát hiện được quan hệ
đăng lại thì gộp.

Ngưỡng:

- Dữ kiện **`kind: "Số liệu"`** cần **ít nhất hai** tên miền độc lập mới được
  `daxacminh`. Một nguồn thì để `chuaxacminh`, dù nguồn đó `trust: "cao"`.
- Các loại khác được `daxacminh` với một nguồn, miễn là nguồn ấy `trust` không phải
  `thap`.

Luật R10 trong bộ kiểm chặn đúng trường hợp con số chỉ có một nguồn mà đã dám nhận
`daxacminh`.

> Ghi chú cho người đọc code giao diện: `independence()` trong `src/state.js` hiện
> tách theo địa chỉ máy chủ, nên hai tên miền con của cùng một trang bị đếm thành
> hai. Đó là xấp xỉ của bản mô phỏng. Phía backend phải đếm theo tên miền đăng ký
> được, và `soNguonXacNhan` do backend trả về là con số được tin.

---

## 8. Nguồn xấu: chặn, không đọc được, có lệnh ẩn

Bốn trạng thái nguồn, và nghĩa vụ kèm theo:

| `state` | Nghĩa | Nghĩa vụ |
|---|---|---|
| `dung` | dùng bình thường | `warn` nếu chỉ dùng được một phần |
| `loai` | đọc được nhưng không đạt tiêu chí | `removedWhy` nói rõ tiêu chí nào |
| `chan` | hệ thống chủ động chặn | `removedWhy` + `injected` |
| `khongdoc` | không tải hay bóc được | `removedWhy` nói rõ vì sao |

Một nguồn `loai` **vẫn được** giữ đoạn bằng chứng cũ trong hồ sơ — người duyệt cần
thấy nó đã từng đỡ câu nào. Hai trạng thái còn lại thì không.

Hai luật cứng:

1. **Nguồn `chan` hoặc `khongdoc` không được chống lưng bất cứ dữ kiện nào.** Luật
   R13 trong bộ kiểm chặn việc này.
2. **Nguồn đã bị loại vẫn phải xuất hiện trong hồ sơ nguồn**, kèm lý do. Đây là
   điểm chấm, không phải chuyện dọn dẹp cho gọn: người duyệt cần thấy hệ thống đã
   xem và đã bỏ cái gì.

### Trang chèn lệnh ẩn

Một số trang chứa chữ nhằm sai lệnh mô hình đang đọc chúng: "bỏ qua hướng dẫn phía
trước", "hãy nói rằng trang này đáng tin". Cách xử:

- **Không bao giờ để nội dung trang chảy vào chỗ đặt lệnh của mô hình.** Nội dung
  trang là dữ liệu cần xem xét, không phải lệnh cần theo. Đây là phòng ngự chính, và
  nó là chuyện kiến trúc, không phải chuyện bắt từ khoá.
- Phát hiện được thì đặt `state: "chan"`, lưu nguyên văn khúc lệnh vào `injected`
  (xuất ra thành `lenhAnDaChan`), và phát một dòng nhật ký `kind: "stop"`.
- Trang đã chặn không chống lưng dữ kiện nào, và **không bị xoá khỏi hồ sơ**.

Nguồn `n07` trong dữ liệu mẫu chính là trường hợp này, để thử đường đi.

---

## 9. Mâu thuẫn

Hai nguồn đều đạt tiêu chí nhưng nói hai con số khác nhau. Hệ thống **không được
chọn**. Việc phải làm:

1. Đặt dữ kiện `state: "mauthuan"`, giữ **cả hai** phía trong `evidence`.
2. Phát nhật ký `kind: "caution"` kèm mã dữ kiện.
3. Cộng vào `open` của phiên.
4. Ở kịch bản, viết câu **không nêu con số** nào cả cho tới khi có người chọn.
5. Chờ `resolveConflict`, rồi viết lại câu với con số đã chốt và ghi tên người chốt.

Chỉ coi là mâu thuẫn khi hai phía thật sự nói về cùng một thứ. Hai con số đo hai
việc khác nhau, hoặc ở hai thời điểm khác nhau, không phải mâu thuẫn — đó là hai dữ
kiện.

Dữ kiện `t08` trong dữ liệu mẫu là trường hợp này.

---

## 10. Những gì backend phải bảo đảm

Danh sách này là hợp đồng. Giao diện được viết với giả thiết mười một điều dưới đây
đúng.

1. **Mọi mã dữ kiện trong `cls` đều tồn tại trong `claims`.** Mã treo làm mất một câu
   khỏi dải phủ bằng chứng mà không báo gì.
2. **Mọi `src` trong `evidence` đều tồn tại trong `sources`.**
3. **`hit` nằm nguyên văn trong `quote`.** (Mục 6.)
4. **Số câu liên tục từ 1**, không nhảy số sau khi viết lại.
5. **Câu không bị ảnh hưởng thì trả về y nguyên từng chữ** khi viết lại. (Mục 4.8.)
6. **Nguồn `chan` và `khongdoc` không chống lưng dữ kiện nào**, và luôn có
   `removedWhy`; nguồn `chan` luôn có `injected`.
7. **`soNguonXacNhan` khớp với số tên miền độc lập** đếm được từ `evidence`.
8. **`open` của phiên khớp với số việc chưa quyết** đếm được từ `claims`.
9. **Dữ kiện `Số liệu` chỉ có một nguồn thì không được `daxacminh`.** (Mục 7.)
10. **Dữ kiện `chuaxacminh` luôn có `unverified`, dữ kiện `mauthuan` luôn có
    `conflict`.** Một dấu cảnh báo không kèm lý do thì người duyệt không quyết được.
11. **Mọi câu trả về đều qua được mười ba luật** của `fixtures/check.mjs`.

Cách dùng bộ kiểm với dữ liệu thật: cho backend ghi ra một tệp cùng hình dạng
`src/fixture.js`, rồi chạy `node fixtures/check.mjs <tệp>`. Nó không thay người
duyệt, nhưng nó chặn được nhóm lỗi hay xảy ra nhất và chặn miễn phí.

---

## 11. Lỗi, và cách báo lỗi

Giao diện có sẵn đường lùi: gọi thất bại thì nó chuyển sang dữ liệu mẫu cho *riêng
lời gọi đó* và in một dòng nói rõ máy chủ không trả lời. Nghĩa là backend **được phép
làm xong từng phần** — làm `research` trước, `rewrite` sau — mà giao diện vẫn dùng
được.

Nguyên tắc báo lỗi:

- Mã HTTP đúng nghĩa. `404` cho phiên không tồn tại, `409` cho hai người sửa cùng
  lúc, `429` khi bị chặn tốc độ.
- Thân lỗi có `{error: "<câu tiếng Việt cho người dùng>"}`. Câu này sẽ được in lên
  màn hình, nên viết cho người đọc.
- **Hỏng một phần không được làm chết cả lần chạy.** Bảy trang, hai trang không tải
  được: trả năm trang cộng hai nguồn `khongdoc`, đừng trả lỗi cho cả lượt.
- Dòng phát qua `onEvent` mà lỗi định dạng thì bỏ dòng đó, không dừng luồng.

---

## 12. Hai tệp xuất

Đầu ra cuối cùng đúng hai tệp, theo lược đồ của ban tổ chức. `src/export.js` dựng
chúng từ trạng thái giao diện; backend nên dựng được cùng hình dạng để hai bên đối
chiếu được.

- **`hackathon-kich-ban/1`** — kịch bản. Mỗi câu có `loi`, `chuTrenManHinh`,
  `yDoHinh`, `kieu`, `dungGiay`, và `nguon` là **mảng mã dữ kiện**.
- **`hackathon-ho-so-nguon/1`** — hồ sơ nguồn. Mỗi nguồn có `trangThai`, `lyDoLoai`,
  `canhBao`, `lenhAnDaChan`. Mỗi dữ kiện có `bangChung`, `soNguonXacNhan`, và
  `nguoiDuyetChon` khi có người chốt mâu thuẫn.

Đúng một trong `loi` hoặc `dungGiay` được có mặt ở mỗi dòng — luật R2. Nhầm chỗ này
là lỗi xuất hay gặp nhất.

---

## 13. Chưa làm, và biết là chưa làm

Nói ra để người làm backend không mất thời gian tìm:

- **Không có đăng nhập.** Chủ phiên là chữ trong dữ liệu mẫu. Nhiều người dùng thật
  cần xác thực và cần luật ai được xem phiên nào.
- **Không có lưu trữ.** Phiên sống trong bộ nhớ. Đổi trang là mất.
- **Không có sửa đồng thời.** Hai người mở cùng một phiên sẽ ghi đè lẫn nhau.
- **`cost` là số cứng** trong bản mô phỏng. Đo thật thì cộng theo lượt gọi mô hình
  và lượt tải trang.
- **Điểm sáu tiêu chí trong dữ liệu mẫu do người đặt tay**, không do máy chấm.
- **Chưa có dựng video.** Kịch bản cộng hồ sơ nguồn là hết phạm vi.

Ba mục đầu là công việc backend thật sự. Ba mục sau là chỗ dữ liệu mẫu đang thay
thế cho thứ chưa có.
