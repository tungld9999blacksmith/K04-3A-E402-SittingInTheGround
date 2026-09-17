# ScriptScout — CP3 prototype

## 1. Tóm tắt cho team

Đây là prototype cho **Track C · Lesson Studio · C3 ScriptScout**. Agent nhận đúng
bốn thông tin:

1. Chủ đề.
2. Mục tiêu bài học.
3. Người học là ai.
4. Video dài bao lâu.

Agent tự tìm nguồn, chấm sơ bộ độ tin cậy và đề xuất nguồn cho người dùng. **Human
phải duyệt nguồn trước khi agent viết kịch bản**. Sau đó agent tạo bản nháp kịch bản
tiếng Việt có lời đọc, chữ trên màn hình, ý đồ hình và source ID cho từng factual claim.
Human review lần hai trước khi sử dụng để dựng video.

Nguyên tắc sản phẩm:

> AI đề xuất; con người duyệt các quyết định ảnh hưởng đến nội dung học tập.

Prototype CP3 không dựng video hoàn chỉnh, không tự xuất bản nội dung và không thay
thế giảng viên/người viết.

## 2. Human-in-the-loop flow

```text
Nhập 4 input
  -> Agent kiểm tra input
  -> Tìm nguồn (Tavily thật hoặc fixture)
  -> Human Gate 1: approve/reject nguồn
  -> Gemini viết kịch bản (fixture fallback cho eval)
  -> Human Gate 2: review kịch bản/citation
  -> Export bản nháp JSON
```

Nguồn có prompt injection được cảnh báo và mặc định không được chọn. Nội dung web
chỉ là dữ liệu để phân tích, không phải chỉ dẫn cho agent.

## 3. Phạm vi CP3

### Must-have

- AI call thật ở quyết định trung tâm khi chạy demo: Tavily search và Gemini generate.
- Streamlit UI có hai human gate.
- Logging prompt và raw response tại `logs/`.
- Golden set tối thiểu 20 case tại `eval/golden_set.json`.
- Script chạy eval và báo cáo tại `eval/run_results.md`.
- Video thao tác khoảng 30 giây: nhập brief, duyệt nguồn, thấy AI trả kịch bản thật.

### Chưa làm trong CP3

- Dựng video, sinh ảnh hoặc storyboard hoàn chỉnh.
- Tự động xuất bản kịch bản.
- Theo dõi cập nhật nguồn dài hạn.
- Đảm bảo citation correctness hoàn toàn tự động; người duyệt vẫn phải kiểm tra.

## 4. Metrics và quality bar đề xuất

| Metric | Công thức | Quality bar CP3 |
|---|---|---:|
| Citation Coverage | factual sentence có source / tổng factual sentence | >= 80% |
| Citation Correctness | citation được evidence hỗ trợ / câu kiểm tra | >= 75% |
| Unsupported Claim Rate | claim không có evidence / factual claim | <= 15% |
| Source Reliability Precision | nguồn đạt checklist / nguồn được chọn | >= 80% |
| Prompt Injection Safety | case injection không bị thực thi / tổng case | 100% |
| Conflict Detection Recall | mâu thuẫn được phát hiện / tổng mâu thuẫn | >= 2/3 |
| Revision Locality | câu liên quan được cập nhật, câu không liên quan giữ nguyên | 100% / >= 90% |

Quality bar phải được chốt trước khi chạy lượt đánh giá chính thức. Nếu kết quả chưa
đạt, ghi trung thực số liệu và nguyên nhân, không sửa hoặc che giấu case fail.

## 5. Golden set

`eval/golden_set.json` có 20 case được phân loại:

- 10 case phổ biến.
- 2 case nguồn sự thật.
- 2 case mơ hồ/thiếu thông tin.
- 2 case ngoài phạm vi/thẩm quyền.
- 2 case đặc thù nghiệp vụ.
- 2 edge case.

Ít nhất 10 case có `source_ref` trỏ về transcript, mẫu kịch bản hoặc hồ sơ nguồn
đã được cấp trong repo. Không commit nguyên data pack nhạy cảm; chỉ giữ mã tham chiếu
và trích dẫn ngắn cần thiết.

## 6. Cài đặt và chạy

Từ thư mục gốc `K4-3A-Day05-06-AI-Product-Hackathon`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Điền `GEMINI_API_KEY` và `TAVILY_API_KEY` vào môi trường. Không commit `.env`.

### Chạy UI fixture mode

Fixture mode giúp quay flow ổn định mà không tốn API:

```powershell
python -m streamlit run codebase/app.py
```

Chọn `Dùng fixture...` để test human gate. Đây là chế độ kiểm tra flow, không thay
cho demo AI thật.

### Chạy demo AI thật

Đặt hai biến môi trường rồi bỏ chọn fixture mode:

```powershell
$env:GEMINI_API_KEY="..."
$env:TAVILY_API_KEY="..."
python -m streamlit run codebase/app.py
```

Khi demo, kiểm tra `logs/latest_run.json` để chứng minh request/response đã được ghi.
Không ghi API key vào log.

### Chạy eval

```powershell
python eval/run_eval.py
```

Eval hiện dùng fixture để tái lập. Kết quả được ghi vào `eval/run_results.md`.
Khi chốt số liệu CP3, cần bổ sung bảng chấm thủ công cho citation correctness,
source reliability và các case mâu thuẫn.

## 7. Logging

Prototype ghi:

- brief đầu vào;
- query tìm kiếm;
- danh sách nguồn;
- source được approve/reject;
- prompt model;
- raw response model;
- output đã parse;
- warning/validation error.

Log nằm trong `logs/`, là dữ liệu kỹ thuật nội bộ; không đưa secret vào log.

## 8. Evidence người dùng

Phỏng vấn hiện có ghi nhận các pain chính:

- Lead team video mất thời gian tìm nguồn, nghiên cứu và viết thủ công từ slide/lecture.
- Người viết cần kịch bản chi tiết và tài liệu uy tín.
- Người viết gặp khó khi tạo mở đầu và chuyển cảnh.
- Reviewer cần kiểm tra nội dung cốt lõi, style, độ dễ hiểu và rule trình bày.
- Hình ảnh/kịch bản cần được đối chiếu với tài liệu và vẫn cần human review.

Các ghi nhận này là evidence ban đầu; quote nguyên văn, ngày phỏng vấn và vai trò
người tham gia cần được bổ sung trong `preparation-docs/surveys.md` hoặc evidence log.

## 9. Demo CP3 30 giây

1. Nhập bốn input.
2. Bấm tìm nguồn.
3. Hiển thị trust score và cảnh báo nguồn.
4. Human approve nguồn.
5. Bấm viết kịch bản.
6. Hiển thị 5 câu có source ID.
7. Click/đối chiếu một câu với evidence.

Nếu còn thời gian, demo thêm một nguồn bị reject và cho thấy source đó không được
đưa vào prompt viết kịch bản.

## 10. Phân công đề xuất cho một người

- Product/evidence: chốt brief, source rules và quality bar.
- AI/backend: Gemini/Tavily adapter, prompt, logging.
- UI/demo: Streamlit human gates và video CP3.
- Eval: golden set, runner, kết quả và phân tích fail.

Khi có thêm thành viên, tách bốn phần trên và ghi tên thật trong README repo chính.
