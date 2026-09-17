# ScriptScout

Giao diện cho một agent tự tìm tài liệu và viết kịch bản video bài giảng, trong đó mỗi câu
có thông tin đều truy được về đoạn tài liệu chứng minh cho nó.

Đề C3 của Mini Hackathon AI, Batch 04, lớp 3A.

## Chạy cả agent thật

Hai tiến trình. Backend cần `GEMINI_API_KEY` và `TAVILY_API_KEY` trong biến môi trường
(không có bước đọc tệp `.env`).

```bash
python server/agent.py        # agent, cổng 8787
python -m http.server 8000    # giao diện
```

Mở `http://localhost:8000` — giao diện tự tìm backend ở cổng 8787, không cần thêm gì vào
địa chỉ. Góc trên phải cho biết đang nối vào cái gì. Không có backend thì mọi lời gọi tự
lùi về dữ liệu mẫu, từng lời gọi một.

**Người làm backend đọc [docs/BACKEND.md](docs/BACKEND.md) trước.** Đó là bản mô tả sản phẩm phải
làm được gì: mười việc backend phải làm, cách chấm tín cậy, cách tự kiểm dẫn nguồn, và mười một
điều giao diện đang tin là đúng. `docs/ADAPTER.md` chỉ là bảng endpoint, và
[docs/LOOP.md](docs/LOOP.md) nói vòng tự kiểm đã dựng chạy thế nào.

## Chạy

Không có bước build, không có phụ thuộc. Mở `index.html` bằng trình duyệt, hoặc phục vụ thư
mục này bằng một static server bất kỳ. Chi tiết trong [docs/RUN.md](docs/RUN.md).

```bash
node fixtures/check.mjs     # 13 luật của mẫu kịch bản, phải exit 0
node build-artifact.mjs     # dựng bản đem publish
```

## Cái gì nằm ở đâu

| Đường dẫn | Là gì |
|---|---|
| `index.html` | Vỏ trang, nạp mọi thứ theo thứ tự |
| `src/tokens.css` | Màu, chữ, khoảng cách, bo góc, cả hai theme |
| `src/state.js` | Kho trạng thái, các selector suy ra, ngăn xếp hoàn tác |
| `src/adapter*.js` | Chỗ cắm backend. `?api=<url>` là đổi sang máy chủ thật |
| `src/views.js` | Hàm render thuần từ trạng thái ra HTML |
| `src/fixture.js` | Dữ liệu mẫu, lấy từ gói của ban tổ chức |
| `fixtures/check.mjs` | Bộ kiểm 13 luật, cũng là cổng gác cho mọi sửa đổi |
| `docs/BACKEND.md` | **Sản phẩm phải làm được gì.** Viết cho người làm backend |
| `docs/LOOP.md` | Vòng tự kiểm: quan toà máy, viết theo phần, viết lại đúng chỗ |
| `server/agent.py` | Agent thật: Tavily tìm, Gemini quyết |
| `server/validate.py` | Quan toà máy, mười bảy luật |
| `docs/` | Cách chạy, bảng endpoint, hệ thống thiết kế |
| `qa/` | Ảnh chụp màn hình của các lượt chạy thật |

## Ba điều nên biết trước khi đọc code

**Câu là đơn vị trạng thái, và câu trỏ về *thông tin*, không trỏ thẳng về *nguồn*.** Ba tầng
`nguon` → `thongTin` → `cau.nguon` là mô hình của ban tổ chức. Nhờ tầng giữa mà bỏ một nguồn
sẽ tự động biết câu nào phải viết lại, và đếm được một số liệu có mấy nguồn độc lập xác nhận.

**Một câu có thể dựa trên nhiều thông tin.** Thông tin yếu nhất quyết định mức của cả câu, và
mất bất kỳ thông tin nào cũng buộc viết lại câu đó.

**Không có gì trong `src/views.js` biết dữ liệu từ đâu ra.** Mọi thứ đi qua `window.Adapter`.

## Giới hạn, nói thẳng

- Thời gian trong bản mô phỏng là diễn. Chạy thật mất vài phút, không phải mười sáu giây.
- Con số chi phí là dữ liệu mẫu, chưa phải đo thật.
- `adapter-http.js` không gọi được sang origin khác khi trang chạy trong khung nhúng của
  Artifact. Muốn nối máy chủ thật thì chạy ở máy hoặc tự host. Đây là hàng rào của nền tảng.
- Điểm tin cậy trong `fixture.js` do người chấm tay theo bộ tiêu chí, chưa phải model chấm.
- Kịch bản là ba mươi giây mở đầu của một bài, không phải kịch bản bốn mươi câu đầy đủ.
