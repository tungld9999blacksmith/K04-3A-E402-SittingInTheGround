# Chạy thử, ba phút

Repo này có **hai** thứ chạy được, không phải một.

| Cái gì | Ở đâu | Là gì |
|---|---|---|
| Prototype Streamlit | `codebase/app.py` | Form bốn ô, hai cửa duyệt. AI thật. |
| Agent + giao diện chat | `codebase/ui/` | Agent hỏi lại, tự tìm nguồn, viết kịch bản dẫn nguồn. |

## Chuẩn bị, một lần

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

Hai khoá cần có trong biến môi trường. **Không có bước đọc tệp `.env`** — repo không cài
`python-dotenv`, nên copy `.env.example` thành `.env` sẽ không có tác dụng. Export thẳng:

```bash
export GEMINI_API_KEY=...      # PowerShell: $env:GEMINI_API_KEY="..."
export TAVILY_API_KEY=...
```

Khoá Tavily và Gemini là khoá dùng chung của nhóm. Đừng commit, đừng dán vào chat nhóm.

## Cách một, prototype Streamlit

```bash
.venv/Scripts/python -m streamlit run codebase/app.py
```

Mở `http://localhost:8501`. Bỏ trống ô fixture để dùng AI thật. Nhập chủ đề, bấm tìm
nguồn, mở một nguồn ra và tick duyệt, **chờ một nhịp**, rồi bấm viết kịch bản. Streamlit
nạp lại trang mỗi lần tick, và cú bấm rơi vào giữa nhịp nạp lại sẽ bị bỏ qua.

Trên Windows, `streamlit.exe` có thể bị Application Control chặn. Gọi qua module như trên
thì không gặp.

## Cách hai, agent nói chuyện được

Cần hai tiến trình. Cửa sổ thứ nhất, backend:

```bash
.venv/Scripts/python codebase/ui/server/agent.py
```

Cửa sổ thứ hai, giao diện:

```bash
cd codebase/ui && python -m http.server 8000
```

Mở `http://localhost:8000` — giao diện tự tìm backend ở cổng 8787, không cần thêm gì vào
địa chỉ. Gõ một câu mô tả buổi học, agent sẽ hỏi lại, đưa kế hoạch, chờ duyệt rồi mới đi
tìm nguồn.

Góc trên phải cho biết đang nối vào cái gì: *đang nối máy chủ* là backend thật, *dữ liệu
mẫu* là đang chạy mô phỏng.

## Kiểm nhanh

```bash
node codebase/ui/fixtures/check.mjs    # 13 luật của mẫu kịch bản, phải exit 0
python eval/run_eval.py                # 20 case golden set
```

Lưu ý về `run_eval.py`: nó gọi `generate_script` **không truyền provider**, nên hai mươi
case đang chấm đoạn văn mẫu cứng trong code, không chấm mô hình. Con số hiện ra không nói
được gì về chất lượng AI. Muốn số liệu thật thì phải truyền `GeminiProvider()` vào và chấm
tay phần citation correctness.

## Ai đọc gì

- Người làm backend: `codebase/ui/docs/BACKEND.md` — sản phẩm phải làm được gì, mười việc,
  cách chấm nguồn, cách tự kiểm đoạn trích, mười một điều giao diện đang tin là đúng.
- Người sửa giao diện: `codebase/ui/README.md`.
- Người viết spec: số liệu và giới hạn thật nằm trong hai tệp trên, đừng chép quality bar
  từ README nếu chưa chạy lại eval.
