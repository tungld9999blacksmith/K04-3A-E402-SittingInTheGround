import io

p = "server/agent.py"
s = io.open(p, encoding="utf-8").read()

old_start = s.index("RULES = (")
old_end = s.index(")", s.index('hai lan trong cung mot cau."', old_start)) + 1

NEW = '''RULES = (
    "Luật bắt buộc, vi phạm là phải viết lại:\\n"
    "- KHÔNG chữ số trong loi. Viết bằng chữ: hai nghìn, không phải 2000.\\n"
    "- Không viết tắt chưa giải thích. Nghĩa tiếng Việt trước, thuật ngữ tiếng Anh nhắc "
    "một lần sau đó.\\n"
    "- chu tối đa 40 ký tự và không được cắt giữa từ; câu nào cũng phải có chu và hinh.\\n"
    "- Mỗi loi đúng MỘT câu, một dấu kết thúc.\\n"
    "- kieu là một trong: ke, giang, nhe, hoi, nhan.\\n"
    "- cls là mảng mã dữ kiện câu đó dựa vào, chỉ dùng mã có trong danh sách. Câu chuyển "
    "đoạn để [] và phải ngắn, dưới chín âm tiết. Câu nào khẳng định điều gì thì PHẢI có "
    "mã dữ kiện.\\n"
    "- Tiếng Việt đọc khoảng hai phẩy chín âm tiết một giây. Muốn dài hơn thì viết THÊM "
    "câu có dẫn nguồn, đừng nhồi chữ vào một câu.\\n"
    "- Không lặp lại tên chủ đề hai lần trong cùng một câu.\\n"
    "- KHÔNG tự kể nguồn trong lời đọc. Không viết 'theo tài liệu', 'sách kỹ thuật xác "
    "nhận', 'báo cáo chỉ ra', 'chuyên gia đánh giá'. Nói thẳng nội dung; phần dẫn nguồn "
    "nằm ở cls.\\n"
    "- Không viết câu chung chung cho đủ thời lượng. Mỗi câu phải nói một điều cụ thể lấy "
    "từ dữ kiện nó dẫn, và phải đúng với nội dung dữ kiện đó.\\n"
    "- Phân bổ đều các dữ kiện, đừng dồn nhiều câu vào cùng một dữ kiện."
)'''

s = s[:old_start] + NEW + s[old_end:]
io.open(p, "w", encoding="utf-8").write(s)
print("RULES rewritten in proper Vietnamese, with the two new rules")
