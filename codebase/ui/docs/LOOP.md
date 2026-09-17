# Vòng tự kiểm — agent tự biết mình đã làm xong hay chưa

`docs/BACKEND.md` nói sản phẩm phải làm được gì. Tài liệu này nói **cách phần đã dựng
thật sự chạy**, vì nó khác một lời gọi mô hình bình thường ở một điểm: agent so kết quả
với yêu cầu, rồi tự sửa cho tới khi đạt hoặc hết hạn mức.

Hai tệp:

| Tệp | Việc |
|---|---|
| `server/agent.py` | Agent. Tavily tìm, Gemini quyết, HTTP nói với giao diện. |
| `server/validate.py` | **Quan toà máy.** Không có ý kiến, chỉ có luật. |

---

## 1. Vì sao cần vòng lặp

Yêu cầu hai mươi phút, agent viết mười sáu giây rồi báo xong. Không có gì so đầu ra với
đầu vào, nên "xong" chỉ có nghĩa là "mô hình đã trả lời".

Vòng lặp sửa đúng chỗ đó. Sau khi viết, agent **chấm chính mình bằng máy**, rồi đưa danh
sách lỗi trở lại cho mô hình như một bản đặt hàng sửa chữa.

> Lời phàn nàn của quan toà được viết dưới dạng **câu lệnh sửa**, không phải câu nhận
> xét. "Câu 12: lời đọc tự kể nguồn, nói thẳng nội dung" dùng được ngay; "câu này chưa
> tốt" thì không.

## 2. Quan toà kiểm những gì

Mười ba luật của mẫu kịch bản, cộng bốn luật mà chỉ có máy đứng ngoài mới thấy:

| Luật | Bắt lỗi gì |
|---|---|
| Tổng thời lượng | Lệch quá mười lăm phần trăm so với độ dài người đặt |
| `uncited_assertions` | Câu dài từ chín âm tiết mà không dẫn dữ kiện nào |
| `narrated_sourcing` | Lời đọc tự kể nguồn: "theo tài liệu", "sách kỹ thuật xác nhận" |
| `overused_claims` | Một dữ kiện đỡ hơn ba mươi lăm phần trăm số câu có dẫn nguồn |

Ba luật cuối đều đến từ lỗi thật gặp khi chạy, không phải từ suy đoán:

- `narrated_sourcing` sinh ra sau khi kịch bản trả về *"Sách kỹ thuật xác nhận rằng việc
  này giúp tăng hiệu suất"*, gán cho một dữ kiện không nói gì như thế. Đó là câu đệm đeo
  mặt nạ bằng chứng.
- `overused_claims` sinh ra sau khi tám trên mười chín câu cùng dẫn một dữ kiện.
- Luật tổng thời lượng sinh ra từ đúng vụ mười sáu giây trên ba mươi.

Hai luật được nới cho **có thể đạt được**, vì một luật không thể đạt sẽ đốt hết số lượt
sửa mà không cải thiện gì:

- Viết tắt chỉ bị bắt **lần đầu**, và không bị bắt nếu câu đó đã giải nghĩa tại chỗ.
  Không có ngoại lệ này thì một bài về HTTP không được phép gọi tên chính nó.
- Số phần bị **kẹp về đúng những phần đã khai báo** thay vì tin số mô hình trả về. Mô
  hình từng gán `sec: 4` cho kịch bản hai phần, quan toà bắt lỗi, và không lượt sửa nào
  chữa được.

## 3. Trình tự khi viết

```
Ước số phần theo độ dài  ->  mỗi phần một lượt viết
                             |
                             +-> chấm riêng phần đó, sai thì sửa ngay
                             |
Thiếu dữ kiện cho độ dài  ->  TÌM THÊM, không viết bù
                             |
Chấm toàn bộ kịch bản     ->  sửa, tối đa ba lượt
                             |
Còn lỗi                   ->  BÁO RA, không che
```

Chặn bởi `CALL_BUDGET = 22` lượt gọi mô hình. Hết hạn mức thì dừng và nói đã dừng.

**Thiếu dữ kiện thì đi tìm thêm.** `claim_budget()` ước một dữ kiện cho mỗi hai câu.
Thiếu thì `topup_claims()` tìm tiếp theo tên từng phần, mỗi đoạn trích mới vẫn phải khớp
nguyên văn trang gốc. Ba phút trên năm dữ kiện từng lấy thêm mười dữ kiện từ tám trang.

Viết bù cho đủ thời lượng là cách một kịch bản bắt đầu khẳng định những điều không ai
đọc. Vì vậy hệ thống chọn ngắn hơn mục tiêu và nói rõ là ngắn.

## 4. Viết lại khi người duyệt loại một dữ kiện

Đây là chỗ dễ làm sai nhất, và bản đầu đã làm sai.

Bỏ một câu làm tổng thời lượng tụt xuống, luật thời lượng kêu, và bản sửa **viết lại
toàn bộ kịch bản** — phá đúng lời hứa duy nhất mà tính năng này tồn tại để giữ, còn thêm
hai câu không ai yêu cầu.

Bản hiện tại:

- Chấm **không dùng** luật tổng thời lượng. Loại một dữ kiện thì video ngắn lại; đó là
  sự thật cần thấy, không phải lỗi cần bù.
- Chỉ những câu **quan toà gọi đúng số** mới được sửa. `rewrite_lines()` chỉ cho mô hình
  thấy những câu đó, và chỉ ghép lại đúng những câu đó.
- Câu không liên quan trả về **y nguyên từng chữ**, theo cấu trúc chứ không theo lời hứa.

Đo thật: loại một dữ kiện làm rơi một câu, **mười bốn câu còn lại giống hệt từng chữ**,
không lỗi, và nhật ký ghi bảy mươi phẩy ba giây thay vì bảy mươi bảy phẩy hai.

## 5. Phiên, và cái gì được lưu

Mọi lời gọi mang theo `session`. Backend lưu đề bài, nguồn, dữ kiện, kịch bản vào phiên
đó, nên quay lại danh sách rồi mở lại vẫn thấy hiện vật. Vẫn là bộ nhớ trong tiến trình:
tắt backend là mất.

## 6. Tiền, hay là chưa đo được

Mỗi lượt đếm token và số lần tìm thật. Chỉ khi `GEMINI_USD_PER_MTOK` được đặt thì mới
quy ra đô; không đặt thì thanh trên cùng in **đúng những gì đã đo** — "mười một phẩy bảy
nghìn token, bốn lượt tìm".

Một con số đô bịa ra tệ hơn không có con số nào.

## 7. Còn hở chỗ nào

Nói ra để người sau không phải tự tìm:

- **Quan toà không đọc được nghĩa.** Một câu dẫn dữ kiện không thật sự chống lưng cho nó
  thì máy không bắt được. `overused_claims` chỉ thấy một dữ kiện bị kéo căng, không thấy
  nó bị dùng sai.
- **Phiên sống trong bộ nhớ**, và chỉ một người duyệt một lúc (`LAST` giữ lượt tìm gần
  nhất để lượt bổ sung đối chiếu được).
- **Dữ kiện rút từ đoạn trích của máy tìm**, không phải toàn văn trang.
- **Hai mươi phút cần khoảng một trăm dữ kiện.** Lượt bổ sung bị chặn ở ba phần, nên mục
  tiêu rất dài sẽ về ngắn hơn, kèm lời nói rõ là ngắn.

---

## 8. Dựng video, và mượn cách làm từ đâu

Cả vòng kết thúc ở một tệp mp4 dựng tại máy. Không dùng mô hình sinh video: một video ba
phút bằng mô hình sinh tốn khoảng chín đến hai mươi bốn đô, còn cách này tốn không đồng
nào và chạy nhanh hơn thời lượng của chính nó.

Cách làm là cách mà các repo mã nguồn mở lớn đã chốt lại, rõ nhất là **MoneyPrinterTurbo**
(hơn một trăm nghìn sao): đọc bằng giọng máy, mỗi nhịp một khung hình, **máy ảnh Ken Burns**
đẩy chậm để khung hình luôn động, rồi ffmpeg ghép lại. Remotion là bản nghiêm túc hơn,
dựng video bằng React, nhưng nó cần cả một đường ống Node để dựng từng khung, nên chưa
đáng cho hôm nay.

Bốn tệp, mỗi tệp một việc:

| Tệp | Việc |
|---|---|
| `server/cards.py` | Chữ và bố cục một khung 1920×1080 |
| `server/motion.py` | Máy ảnh: Ken Burns, mờ dần hai đầu, ghép clip |
| `server/imagery.py` | Tìm ảnh **có giấy phép** trên Wikimedia Commons |
| `server/render.py` | Điều phối: tên nguồn, chọn ảnh, giọng đọc, lắp ráp |

Hai điều khác với một trình chiếu thường:

**Ảnh phải đúng chủ đề, hoặc không có ảnh.** Tìm theo từ khoá trên Commons rất máy móc:
"Docker container" trả về cần cẩu ở cảng Hamburg, "browser cache" trả về miệng sư tử đá ở
Venice. Nên danh sách ảnh tìm được được đưa cho mô hình xem tên, và mô hình **được phép
trả lời là không ảnh nào phù hợp**. Khi đó thẻ dùng nền tự vẽ. Một bài giảng về chuyện
kiểm nguồn thì không thể đặt cái cần cẩu lên màn hình chỉ vì trùng từ khoá.

**Lọc theo tên là không đủ, nên lọc thêm bằng điểm ảnh.** Chạy thật với chủ đề Kubernetes
thì Commons gần như chỉ có biểu đồ khảo sát của chính Wikimedia, và tên tệp là
"2023-12 DSS deployment kubernetes satisfaction" — không có chữ nào để một bộ lọc tên bắt
được. Ảnh đó lọt vào, và thẻ thành hai trang chiếu chồng lên nhau, chữ của biểu đồ đọc rõ
như chữ của mình. Nên mỗi ứng viên đều được tải về và **xem bằng điểm ảnh**: một biểu đồ
hay ảnh chụp màn hình là một vùng gần trắng rất rộng gần như không màu, điều không ảnh
chụp cảnh thật nào có. Gặp thì bỏ, thử ảnh kế tiếp, hết thì dùng nền tự vẽ.

**Lớp che phải đo, không được đoán.** Một mức che cố định đủ cho ảnh tối sẽ để ảnh gần
trắng sáng nguyên. Nên hệ thống đo độ sáng thật của ảnh rồi nâng lớp che tới khi khung hình
xuống dưới ngưỡng, tối đa chín mươi phần trăm để ảnh không bị vùi hẳn.

**Nền tự vẽ phải có vân, nếu không máy ảnh đẩy mà mắt không thấy.** Một dải màu chuyển
mượt thì ở mọi mức phóng đều là đúng một bức ảnh: clip vẫn đang chuyển động mà trông như
đứng yên, đúng cái lỗi mà cả phần này sinh ra để chữa — và thẻ không ảnh là chuyện thường,
vì ảnh có giấy phép đúng chủ đề thường không tồn tại. Nên nền tự vẽ có một lưới điểm mờ và
vài vòng cung rất nhạt. Đo được: nền trơn gần như không lệch, nền có vân lệch 3,6 điểm
giữa giây 0,7 và giây 4,3.

**Thẻ ghi tên nhà xuất bản, không ghi mã nội bộ.** "Nguồn: Stanford" là thứ người xem dùng
được; "Nguồn: n01" là ghi chú cho chính chúng ta. Mã `nXX`, giấy phép ảnh và địa chỉ đầy đủ
nằm ở thẻ cuối, đúng chỗ người muốn kiểm sẽ tìm. Tên lấy từ `org` nếu trang có ghi, không
thì lấy tên miền đăng ký được và bỏ đuôi: `stanford.edu` thành Stanford, `kubernetes.io`
thành Kubernetes. Một bảng nhỏ lo những chỗ tên miền không phải tên người ta biết, ví dụ
`ox.ac.uk` là Oxford và `ieee.org` là IEEE.

Cần thêm hai gói, đã ghi trong `server/requirements.txt`: `edge-tts` cho giọng tiếng Việt
và `imageio-ffmpeg`, gói này mang luôn bản ffmpeg vào trong môi trường ảo nên **không phải
cài gì vào máy**.
