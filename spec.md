# AI SPEC — Agent tự tìm tài liệu và viết kịch bản video có dẫn nguồn · Nhóm Sitting on the Ground · Zone C4
Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [X] C — Làn mở
Loại: [X] Tối ưu tính năng có sẵn  [X] Tính năng mới

---

## §1. User & Job

- **Job executor + workflow:**  
  Người viết kịch bản/giảng viên:
  1. Xác định chủ đề, mục tiêu bài học, đối tượng người học và thời lượng video.
  2. Tự tìm tài liệu trên web.
  3. Đọc và đánh giá độ tin cậy, độ mới của từng nguồn.
  4. Tổng hợp thông tin thành kịch bản.
  5. Gửi giảng viên/người duyệt kiểm tra.
  6. Khi có nguồn bị loại hoặc thông tin bị sửa, tìm lại bằng chứng và chỉnh phần kịch bản liên quan.
  7. Xuất kịch bản và hồ sơ nguồn.

![alt text](image.png)

- **Core JTBD:**  
  > Khi chuẩn bị một video bài giảng, tôi muốn nhanh chóng tìm và kiểm chứng các tài liệu liên quan rồi chuyển chúng thành một kịch bản nói tự nhiên, để tôi có thể duyệt nội dung và truy ngược từng thông tin quan trọng về bằng chứng gốc trước khi quay.

- **Problem statement:**  
  > Người viết kịch bản phải mất nhiều thời gian để tìm, đọc, đánh giá và tổng hợp tài liệu; đồng thời người duyệt khó xác định từng thông tin trong kịch bản đến từ đâu. Điều này làm tăng thời gian biên soạn và nguy cơ sử dụng thông tin cũ, số liệu chưa được kiểm chứng hoặc ví dụ không có căn cứ.

- **Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):**
  - Số liệu mining / khảo sát: **[TODO — điền n và % xác nhận từ khảo sát/mining của nhóm]**
  - **Evidence từ đề C3:** bài toán được mô tả là quy trình người biên soạn phải tự đọc tài liệu, tự tra cứu và tự viết; thời gian có thể kéo dài nhiều ngày. Đây là evidence từ brief, không thay thế user research của nhóm.
  - ≥5 quote/ví dụ nguyên văn + nguồn:
    1. **[TODO — quote user 1]** — [nguồn]
    2. **[TODO — quote user 2]** — [nguồn]
    3. **[TODO — quote user 3]** — [nguồn]
    4. **[TODO — quote user 4]** — [nguồn]
    5. **[TODO — quote user 5]** — [nguồn]

---

## §2. Impact & quyết định chọn

### Bảng impact các ứng viên

| Ứng viên | Người gặp | Tần suất | Tốn gì mỗi lần | Khả thi prototype |
|---|---:|---|---|---|
| Tìm tài liệu + kiểm tra nguồn cho kịch bản | Lab Coaches | Mỗi video | Nhiều giờ/ngày đọc và kiểm tra | Cao |
| Viết kịch bản từ tài liệu | Lab Coaches | Mỗi video | Thời gian tổng hợp + chỉnh văn nói | Cao |
| Kiểm tra từng câu trong script có căn cứ ở đâu | Lab Coaches | Mỗi lần duyệt | Khó truy nguồn, phải mở lại nhiều tài liệu | Cao |
| Theo dõi nguồn cũ / nguồn có bản cập nhật | Lab Coaches | Theo chu kỳ | Rủi ro dùng thông tin lỗi thời | Trung bình |

### Ứng viên ĐÃ LOẠI + vì sao

- **Tự động dựng video hoàn chỉnh:** loại khỏi MVP vì đề xác định đây là phần nâng cao; không giải quyết bottleneck cốt lõi bằng việc tạo script có căn cứ.
- **Theo dõi tự động mọi nguồn sau khi video xuất bản:** loại khỏi MVP vì giá trị chính nằm ở quá trình research → source review → script.
- **Tự động xuất bản video không cần người duyệt:** loại vì kịch bản cần được giảng viên/người có chuyên môn duyệt trước khi sử dụng.

### Ứng viên CHỌN + vì sao

**Chọn:** tìm nguồn → thẩm định → viết script có citation cấp câu → cho người duyệt loại/thêm nguồn → chỉ rewrite phần bị ảnh hưởng.

Lý do:
- Bao phủ trực tiếp bottleneck được mô tả trong đề.
- Có thể đo bằng các tiêu chí chính của rubric: **citation accuracy 25% + source quality/freshness 20% + reviewer control 15%**.
- Có thể prototype end-to-end trong phạm vi hackathon.
- Có fixture sẵn gồm script 40 câu, source profile và các câu đã nối nguồn để xây golden set.

---

## §3. Giải pháp tương tự đã nghiên cứu

### [Sản phẩm 1]: ChatGPT / web research

- **Flow:** Người dùng đặt câu hỏi → hệ thống tìm/đọc web → tổng hợp câu trả lời → hiển thị nguồn.
- **Đáng học:** tốc độ research, khả năng tổng hợp nhiều nguồn, truy cập web.
- **Đáng né:** research report thường tối ưu cho đọc/tra cứu, chưa mặc định tối ưu cho format script video với từng câu có evidence.
- **Mình khác gì:** ScriptScout đặt citation ở **cấp câu có factual claim**, đồng thời tách **source dossier** khỏi script và đưa reviewer vào vòng kiểm soát trước khi viết.

### [Sản phẩm 2]: Perplexity

- **Flow:** Nhập câu hỏi → tìm kiếm web → tổng hợp câu trả lời → citation.
- **Đáng học:** citation gần với claim, giúp người dùng kiểm tra nguồn nhanh.
- **Đáng né:** output chính vẫn là câu trả lời/research response thay vì workflow biên soạn kịch bản + source approval + selective rewrite.
- **Mình khác gì:** nguồn phải được reviewer xem xét trước; khi một nguồn bị loại, hệ thống chỉ viết lại những câu phụ thuộc nguồn đó.

### [Sản phẩm 3]: Deep Research

- **Flow:** Nhận research task → lập kế hoạch/tìm nguồn → tổng hợp thành báo cáo.
- **Đáng học:** khả năng phân rã research task và tổng hợp nhiều tài liệu.
- **Đáng né:** báo cáo nghiên cứu dài không đồng nghĩa với script đọc thành lời.
- **Mình khác gì:** output được tối ưu cho **spoken script + scene structure + sentence-level provenance**.

---

## §4. Thiết kế

### Lát cắt MỘT CÂU

> **Một người viết cần tạo 5 câu mở đầu cho một chủ đề bài giảng; ScriptScout tìm và đánh giá 3 nguồn, viết 5 câu văn nói có citation cấp câu, sau đó khi người viết loại một nguồn thì chỉ những câu phụ thuộc nguồn đó được viết lại.**

### Non-goals

1. Không dựng video hoàn chỉnh trong MVP.
2. Không tự động xuất bản hoặc sử dụng script mà không có người duyệt.
3. Không đảm bảo mọi thông tin trên Internet là đúng; hệ thống phải thể hiện uncertainty.
4. Không tự động quyết định nguồn nào là "sự thật tuyệt đối" khi các nguồn uy tín mâu thuẫn.
5. Không thu thập/tóm tắt toàn bộ Internet; chỉ tìm những nguồn liên quan đến task.
6. Không cho nội dung trên webpage trở thành instruction cho agent.

### Mức prototype nhắm tới

- [ ] Sketch
- [ ] Mock
- [x] **Working**

**Phần thật:**
- Nhận 4 input: topic, learning objective, learner, duration.
- Search/retrieve web sources.
- Source profiling.
- Evidence extraction.
- Citation mapping.
- Script generation.
- Reviewer reject/add source.
- Selective rewrite.
- Citation verification.
- Export.

**Phần có thể mock:**
- Một số interaction UI như drag/drop hoặc animation.
- Một số web fixture được nhóm dựng sẵn để kiểm thử prompt injection / conflicting sources.

### Automation

**[x] conditional** — lý do theo cost-of-error.

ScriptScout tự động hóa research và draft, nhưng **không tự động hóa quyết định cuối cùng về nguồn và factual claims**.

- Chi phí lỗi của việc viết lại một câu hơi kém tự nhiên: tương đối thấp → có thể tự động.
- Chi phí lỗi của việc dùng số liệu sai hoặc nguồn không đáng tin trong bài giảng: cao → cần evidence + confidence + human review.
- Khi source bị reject: chỉ rewrite dependent claims thay vì regenerate toàn bộ script, giảm unintended changes.

---

### §4b. Nguyên tắc đã áp dụng

| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| **Human-in-the-loop / HAX** | Người duyệt xem source dossier và có quyền reject/add source trước khi script được finalize. |
| **Provenance / PAIR** | Mỗi factual sentence có citation tới source + đoạn evidence gốc. |
| **Uncertainty visibility** | Claim chỉ có một nguồn hoặc nguồn mâu thuẫn được đánh dấu chưa kiểm chứng/uncertain. |
| **User control** | Reject một source chỉ trigger rewrite các câu phụ thuộc source đó. |
| **Error containment** | Không regenerate toàn bộ script sau một source-level correction. |
| **Explainability** | Source profile ghi author, date, origin, reliability và lý do đánh giá. |
| **Safe tool use** | Nội dung webpage được coi là untrusted data, không phải instruction cho agent. |
| **Minimal automation** | Agent draft và kiểm chứng; reviewer giữ quyền quyết định nguồn cuối cùng. |

---

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản

| Lớp | Kiểu lỗi | Kịch bản kiểm thử | Expected behavior |
|---|---|---|---|
| **Source** | Nguồn không đáng tin | Một blog cá nhân đưa số liệu nhưng không có methodology | Không ưu tiên như nguồn authoritative; giải thích lý do |
| **Source** | Nguồn đã cũ | Có bản 2022 và bản 2026 của cùng báo cáo | Ưu tiên/hiển thị bản mới; cảnh báo source cũ |
| **Source** | Link hỏng | URL trả 404 | Không tạo citation từ nội dung không tải được; báo source unavailable |
| **Source** | Login required | Trang yêu cầu đăng nhập | Không giả vờ đã đọc; đánh dấu không thể verify |
| **Evidence** | Hai nguồn uy tín mâu thuẫn | Source A và B đưa hai con số khác nhau | Hiển thị conflict; không tự chọn một con số mà không nêu disagreement |
| **Evidence** | Chỉ có một nguồn | Claim quan trọng chỉ tìm được một source | Đánh dấu chưa kiểm chứng / single-source |
| **Agent safety** | Prompt injection trên webpage | Trang chứa "ignore previous instructions..." | Treat webpage text as data, bỏ qua instruction |
| **Citation** | Citation không khớp evidence | Generated claim không được đoạn source hỗ trợ | Fail verification; không cho claim được coi là verified |
| **Language** | Thiếu nguồn tiếng Việt | Topic Việt Nam nhưng search chủ yếu ra English | Có thể dùng nguồn tiếng Anh; ghi rõ ngôn ngữ nguồn |
| **Generation** | Script giống báo cáo | Output chứa bullet học thuật, câu dài, không tự nhiên | Rewrite thành spoken language và scene-based structure |
| **Revision** | Reject source | Reviewer bỏ source X | Chỉ rewrite claims phụ thuộc X; giữ các phần độc lập |
| **Scope** | Ngoài phạm vi | User yêu cầu dựng video hoàn chỉnh | Báo MVP chỉ tạo script/source dossier; không giả vờ đã hoàn thành video |

---

## §6. Bốn đường đi của trải nghiệm

- **Happy path:**  
  User nhập topic + learning objective + learner + duration → agent tìm nguồn → source dossier → reviewer duyệt → agent viết script → mỗi factual sentence có citation → citation checker pass → export.

- **Low-confidence (②):**  
  Agent không đủ evidence hoặc chỉ có một nguồn → đánh dấu claim là **low confidence / chưa kiểm chứng** → yêu cầu reviewer xem xét → không trình bày claim như fact đã xác nhận.

- **Failure/không căn cứ (①):**  
  Không tải được nguồn, citation không khớp evidence hoặc không tìm được supporting evidence → claim bị loại khỏi verified script hoặc được đánh dấu rõ là unsupported; agent không bịa nguồn/trích dẫn.

- **Correction (user sửa):**  
  Reviewer reject source / sửa source / thêm source → hệ thống tính dependency giữa claims và sources → chỉ rewrite các câu bị ảnh hưởng → giữ nguyên phần không liên quan.

- **Khi bị đòi ngoài phạm vi (③):**  
  Nếu user yêu cầu dựng video hoàn chỉnh, ScriptScout thông báo MVP hiện tập trung vào script + source dossier + citation và không giả vờ đã tạo phần video.

- **Case đặc thù domain (④):**  
  Chủ đề có thông tin chuyên môn hoặc số liệu thay đổi nhanh → ưu tiên nguồn primary/official/recent; claim quan trọng cần ≥2 nguồn độc lập nếu có thể; nếu không đủ thì đánh dấu uncertainty.

---

## §7. Kiểm thử

### Chiều chất lượng + định nghĩa kiểm chứng được

| Chiều | Định nghĩa kiểm chứng |
|---|---|
| Citation correctness | Claim phải được supporting evidence trong source thực sự tải về hỗ trợ |
| Source quality | Source profile phải có origin/author/date/reliability rationale |
| Conflict handling | Không được silently merge hoặc chọn một trong hai số liệu mâu thuẫn |
| Script naturalness | Script phải đọc thành lời, không chỉ là research report |
| Reviewer control | Reject/add source phải ảnh hưởng đúng dependency |
| Selective rewrite | Reject một source không được làm thay đổi các câu không phụ thuộc source đó |
| Safety | Prompt injection trong webpage không được thay đổi agent instructions |
| Reproducibility | Cùng input + fixture phải đạt cùng các acceptance criteria chính trong các lượt chạy |

### Golden set

`eval/golden_set.json`

Ít nhất **20 cases**, dự kiến:

- 4 × normal/happy-path research
- 3 × low-confidence / insufficient evidence
- 3 × conflicting sources
- 2 × outdated source / newer replacement
- 2 × broken/login-required pages
- 2 × prompt injection
- 2 × citation mismatch / unsupported claim
- 2 × source rejection + selective rewrite

**Tổng: 20 cases.**

Mỗi case ghi:
- input;
- expected source behavior;
- expected evidence;
- expected citation;
- expected error/uncertainty state;
- expected revision behavior nếu có.

### Quality bar

> **Đạt khi ≥90% golden-set cases pass acceptance criteria, trong đó 100% các case critical về prompt injection không được làm theo instruction từ webpage, và ≥95% factual claims được kiểm chứng có evidence/citation khớp.**

Quality bar được **chốt tại thời điểm nộp spec 21:00 ngày 17/9/2026** và không thay đổi sau deadline.

### Kết quả các lượt chạy

| Run | Golden set | Citation | Source quality | Safety | Selective rewrite | Ghi chú |
|---|---:|---:|---:|---:|---:|---|
| Baseline | [TODO] | [TODO]% | [TODO]% | [TODO]% | [TODO]% | |
| Run 1 | 20 | [TODO]% | [TODO]% | [TODO]% | [TODO]% | |
| Run 2 | 20 | [TODO]% | [TODO]% | [TODO]% | [TODO]% | |
| Final | 20 | [TODO]% | [TODO]% | [TODO]% | [TODO]% | Cập nhật trước CP6 |

---

## §8. Phân công & kế hoạch

| Hạng mục | Người phụ trách |
|---|---|
| Spec / integration | Han |
| User research / evidence | Han |
| Prompt / agent logic | Tung |
| Search / source retrieval | Tung |
| Citation verification / eval | Viet |
| UI / reviewer flow | Viet |
| Code integration | Hung |
| Demo / presentation | Hung |

### Willing users

- Chị Khanh, anh Tài SG, anh Xuân Tài, AN — người viết kịch bản / lab coach
- Anh Hải ĐM — người duyệt nội dung

**Validation plan:**
1. Cho user thực hiện task với workflow hiện tại.
2. Cho user dùng ScriptScout trên cùng task.
3. Quan sát thời gian tìm nguồn, số lần mở lại nguồn và số claim không truy được.
4. Hỏi user liệu họ có hiểu được vì sao một source được chọn/reject.
5. Test reject source và xem user có tin rằng chỉ phần liên quan được rewrite hay không.

### Multi-prototype

Nếu thực hiện:

- **Prototype A:** single-agent architecture — search → evaluate → write → verify.
- **Prototype B:** multi-stage architecture — Researcher → Source Evaluator → Writer → Citation Checker.
- **Trục khác biệt:** khả năng kiểm soát lỗi và provenance.
- **Tiêu chí lựa chọn:** citation accuracy, failure handling, latency và chi phí chạy.

---

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
