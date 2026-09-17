# Các điểm chính cần lưu ý cho Agnet tự tìm tài liệu và viết kịch bản video có dẫn nguồn 

## Teck Stacks
- LangGraph
- Python 3.11+
- AI Provider: Gemini 
- Web Search: Tavily 
- UI, interactive-ui: Streamlit
- pytest 

## Yêu cầu của check-point 3: 
- Mục tiêu của giai đoạn này là chuyển hóa thiết kế thành một nguyên mẫu có khả năng thực thi thực tế và thiết lập thước đo định lượng cho sản phẩm. Một dự án AI có giá trị không thể chỉ dừng lại ở giao diện tĩnh hoặc phản hồi được gán cứng sẵn; sản phẩm bắt buộc phải có ít nhất một lệnh gọi mô hình ngôn ngữ lớn (LLM) hoặc giải thuật AI thật tại mắt xích quyết định trung tâm. Đồng thời, nhóm phải đối mặt với số liệu kiểm thử thực tế để đánh giá năng lực giải pháp một cách khách quan.

- Thước đo chất lượng của sản phẩm được cụ thể hóa bằng bộ kiểm thử mẫu (Golden set). Golden set phải bao gồm tối thiểu 20 trường hợp kiểm thử độc lập do nhóm tự xây dựng, phản ánh đa dạng các tình huống sử dụng: tối thiểu 2 trường hợp cho mỗi lớp trong 4 lớp chỗ khó (① Nguồn sự thật, ② Mơ hồ/thiếu thông tin, ③ Ngoài phạm vi/thẩm quyền, ④ Đặc thù nghiệp vụ), 8 đến 10 trường hợp phổ biến hàng ngày, và 2 đến 4 trường hợp hiếm gặp (edge cases). Trong đó, ít nhất 10 trường hợp phải được trích xuất trực tiếp từ các cuộc hội thoại hoặc dữ liệu thực tế đã được cung cấp. Tỷ lệ kiểm thử đạt chuẩn được tính bằng số trường hợp đầu ra đáp ứng tiêu chí nghiệm thu chia cho tổng số trường hợp thử nghiệm.

1. Lập trình module quyết định trung tâm trong thư mục codebase/, tích hợp API gọi mô hình AI thật (OpenAI, Gemini, Anthropic hoặc mô hình mã nguồn mở cục bộ). Thiết lập cơ chế ghi vết (logging) rõ ràng cho prompt đầu vào và phản hồi thô của mô hình để phục vụ việc xác minh kỹ thuật.
1. Xây dựng tệp dữ liệu kiểm thử eval/golden_set.json (hoặc định dạng .csv tương đương) chứa đủ 20 ca kiểm thử đã phân loại theo taxonomy 4 lớp chỗ khó. Viết tài liệu hoặc script chạy kiểm thử toàn bộ 20 ca này qua prototype.
1. Tổng hợp kết quả thực thi lượt đầu vào tệp eval/run_results.md, lập bảng thống kê số lượng ca đạt, số lượng ca thất bại, tỷ lệ phần trăm đạt được và phân tích chi tiết nguyên nhân dẫn đến các trường hợp sai lệch.
1. Thực hiện quay video màn hình thời lượng khoảng 30 giây thể hiện thao tác trực tiếp trên sản phẩm: người dùng nhập dữ liệu, hệ thống gửi yêu cầu và mô hình AI trả về kết quả xử lý thực tế theo thời gian thực. Không cần cắt ghép kỹ xảo hay lồng tiếng phức tạp.
1. Đẩy toàn bộ mã nguồn, dữ liệu kiểm thử và kết quả đánh giá lên repository:



## Tài liệu tham chiếu trong repo 

- Tài liệu mô tả bài toán `../tracks/track-c-lesson-studio.md` phần C3
    - Phần này nêu lên bài toán, bài toán gốc 
- Survey: `./surveys.md`
- Data: `../data/studio-pack/c3-scriptscout`
- Mẫu kịch bản cần tạo ra: `../data/studio-pack/c3-scriptscout/vi-du/mau-kich-ban.md`
- Mẫu kịch bản với trường hợp cụ thê `../data/studio-pack/c3-scriptscout/vi-du/kich-ban-d1.md`
- Mẫu input của ai-agent-product: 
    1. Chủ đề
    2. Mục tiêu bài học 
    3. Người học 
    4. Thời lượng

## Phát biểu của bài toán
Bài toán gốc. Hãy xây dựng một agent chỉ cần nhận bốn thông tin: chủ đề, mục tiêu bài học, người học là ai và video dài bao lâu — không đưa sẵn tài liệu nào. Agent tự đi tìm tài liệu trên mạng, tự đánh giá tài liệu nào đáng tin, rồi viết kịch bản.

Kết quả trả về gồm hai phần. Phần một là hồ sơ tài liệu: mỗi nguồn ghi rõ lấy ở đâu, ai viết, đăng ngày nào, đáng tin ở mức nào và vì sao, kèm đoạn trích được dùng làm bằng chứng; chỗ nào các nguồn nói khác nhau thì phải nêu ra. Phần hai là kịch bản viết đúng mẫu ban tổ chức đưa, trong đó mỗi câu có chứa thông tin, con số hay ví dụ thực tế đều bấm được để xem đoạn tài liệu gốc. Người duyệt xem hồ sơ tài liệu trước, bỏ nguồn nào thấy không ổn hoặc thêm nguồn của mình, rồi agent mới viết. Khi một nguồn bị bỏ, chỉ những câu dựa vào nguồn đó được viết lại, phần còn lại giữ nguyên.

Chỗ khó nhất của đề này là phân biệt "tìm được tài liệu" với "tài liệu đáng tin". Hệ thống phải nói rõ vì sao tin một nguồn, dựa trên những tiêu chí công bố trước. Số liệu quan trọng cần ít nhất hai nguồn độc lập xác nhận, nếu không thì phải đánh dấu là chưa kiểm chứng. Kịch bản phải là văn nói, đọc lên nghe tự nhiên, mỗi ý một cảnh, chứ không phải bản tóm tắt báo cáo. Ngoài các yêu cầu đó, đội thi tự chọn công cụ tìm kiếm, model AI và cách dựng agent.

Phạm vi. Đội thi chỉ cần làm ra kịch bản, không phải dựng thành video. Đội nào giải xong bài toán chính mà còn thời gian thì có thể dựng luôn một video từ chính kịch bản mình vừa tạo — đây là phần nâng cao, hoàn toàn không bắt buộc và không ảnh hưởng tới điểm của các tiêu chí chính.