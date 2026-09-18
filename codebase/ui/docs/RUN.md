# Running ScriptScout

## How to Run

ScriptScout has no build step and no external dependencies. You can run it in two ways:

1. Open `index.html` directly in any modern web browser.
2. Serve the repository folder with any local static HTTP server. For example:
   ```bash
   python -m http.server 8000
   ```
   or
   ```bash
   npx serve .
   ```

### Switching to the HTTP Adapter

By default, the application runs using `window.MockAdapter` backed by static fixtures. To switch to the HTTP backend adapter, append the `?api=<base-url>` query parameter to the URL:

```
http://localhost:8000/?api=http://localhost:3000
```

When this parameter is present, `src/adapter.js` instantiates `window.HttpAdapter` pointing to the specified base URL.

## Rule Checker

The repository includes a standalone rule checker in `fixtures/check.mjs`. It validates fixture data and script outputs against the project rules and constraints.

Run the rule checker with Node.js:

```bash
node fixtures/check.mjs
```

The script exits with code `0` on success, or code `1` if any validation errors are found.

### Enforced Rules

The table below lists all rules enforced by `fixtures/check.mjs`, including their rule identifiers, severity levels, and descriptions.

| Rule ID | Severity | Description and Message |
| --- | --- | --- |
| R1 | Error | Sentence numbering: Sentence IDs (`s.n`) must be unique and strictly increasing (`câu {n} bị trùng số`, `câu {n} không tăng dần`). |
| R2 | Error | Speech versus pause: A sentence must contain exactly one of `loi` (spoken text) or `dungGiay` (pause duration) (`câu {n} phải có đúng một trong loi hoặc dungGiay`). |
| R3 | Error | Reading style: Spoken sentences must declare a recognized reading style (`kieu`) from the set `ke`, `giang`, `nhe`, `hoi`, `nhan` (`câu {n} có kiểu đọc lạ: {kieu}`). |
| R4 | Error | No digits in spoken text: Spoken text (`loi`) must not contain raw digit characters (`câu {n} có chữ số trong lời đọc: {digits}`). |
| R5 | Error | No uppercase abbreviations: Spoken text (`loi`) must not contain unspoken uppercase acronyms of two or more letters (`câu {n} có viết tắt không đọc được: {abbr}`). |
| R6 | Warning | Single sentence per item: Spoken text (`loi`) should not contain multiple sentence-terminating punctuation marks (`[.!?]`), which crowd a single video scene (`câu {n} có {stops} câu trong một mục, sẽ dồn vào một cảnh`). |
| R7 | Error / Warning | On-screen text limits: On-screen text (`chu`) must not exceed 40 characters (`câu {n} chữ trên màn hình dài {len} ký tự, tối đa là bốn mươi`). Warns if spoken text lacks `chu` (`câu {n} thiếu chữ trên màn hình`) or lacks visual intent `hinh` (`câu {n} thiếu ý đồ hình`). |
| R8 | Error | Claim references: Every cited claim key (in `s.cls` or `s.cl`) must point to an existing claim in `claims` (`câu {n} trỏ tới thông tin không có: {cid}`). A sentence cannot cite duplicate claim keys (`câu {n} dẫn trùng một mã thông tin`). |
| R9 | Error | Evidence integrity: Every claim must contain at least one evidence item. Cited sources must exist in `sources`, must contain non-empty `quote` and `at` fields, and the highlighted snippet (`hit`) must exist verbatim within `quote` (`{cid} phần bôi vàng không nằm trong đoạn trích của {src}`). |
| R10 | Error | Corroboration requirements: Numeric facts (`Số liệu`) require at least two independent domains to be marked verified (`daxacminh`). Unverified claims (`chuaxacminh`) must supply an explanation string in `unverified`. Conflicting claims (`mauthuan`) must supply a `conflict` object with choices. |
| R11 | Warning | Duration plausibility: Warns if sentence duration (`s.dur`) deviates by more than 35% from the expected reading pace calculated at 2.9 syllables per second (`câu {n} thời lượng {dur} giây lệch nhiều so với {expect} giây tính từ {syl} tiếng`). |
| R12 | Error | Section declaration: The section number (`s.sec`) on each sentence must match a declared section number in `sections` (`câu {n} thuộc phần {sec} chưa khai báo`). |
| R13 | Error | Source sanitization: Sources marked `loai`, `chan`, or `khongdoc` must supply a removal explanation in `removedWhy`. Blocked (`chan`) or unreadable (`khongdoc`) sources must not back any claim. Sources blocked for prompt injection (`chan`) must preserve the intercepted string in `injected`. |

## What This Costs to Run

Running the default mock application incurs no API cost ($0.00). The cost display shown in the interface header and sidebar (for example, $0.31) is static fixture data returned by `adapter-mock.js`, not a measured expenditure.

## What It Does Not Do Yet

As documented in section 7 of `PLAN.md`, the current implementation has the following known limits:

- The mock adapter timing is simulated theatre. Real research operations take minutes rather than sixteen seconds.
- The HTTP adapter cannot connect to an external origin when running inside a sandboxed iframe or published artifact due to Content Security Policy restrictions.
- Source credibility scoring is a fixed rubric evaluated manually in fixture data, rather than by an automated model. Connecting an automated scorer requires backend implementation behind `research()`.
- The fixture script covers thirty seconds of an introductory lesson rather than a complete forty-sentence lecture script.
