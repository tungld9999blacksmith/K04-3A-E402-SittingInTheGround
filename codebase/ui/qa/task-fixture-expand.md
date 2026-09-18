# Task: expand the demo fixture

You are editing exactly one file: `src/fixture.js`. Do not touch any other file.

## Context

`src/fixture.js` is mock data for a Vietnamese UI that shows an AI agent finding its own
sources and writing a lecture-video script where every factual sentence is traceable to a
source. The data follows a three-level model: `sources` (a web page) → `claims` (a fact,
with the quoted passage that proves it) → `sentences` (spoken lines that cite a claim id).

`fixtures/check.mjs` enforces 13 rules over this file. **It must exit 0 when you are done.**
Run `node fixtures/check.mjs` yourself, repeatedly, until it is clean. That is the only
definition of done.

## What to add

The script currently has 6 sentences in 2 sections and stops at machine learning. Extend it
so the demo has more to show, while keeping the existing 6 sentences **byte-identical**.

1. **Add a third section** `{ no: 3, name: "Tạo sinh và mô hình ngôn ngữ lớn" }`.

2. **Add 5 new sentences**, `n` 7 through 11, all `sec: 3`, covering in this order:
   - generative AI makes new content: text, images, sound
   - a large language model is a generative model specialised in language
   - an everyday example a first-year student would recognise
   - where the four concepts sit relative to each other
   - a closing line that sends the viewer into the rest of the lesson

3. **Add 2 new claims** `t06` and `t07` for the two definitional sentences above.
   - `t06` is about generative AI producing new content. Evidence from `n05`, and also from
     `n01` so it has two independent sources. Use these two real passages from the
     organisers' sample data, quoted exactly:
     - `n05`: "Khác với các hệ thống chỉ phân loại hay dự đoán, nhóm mô hình sinh tạo ra nội dung mới: văn bản, hình ảnh, âm thanh." at "mục 2, đoạn 1"
     - `n01`: "Một số mô hình học máy được huấn luyện để sinh dữ liệu mới thay vì gán nhãn dữ liệu có sẵn." at "mục 3.4"
   - `t07` is about a large language model being a generative model for language. One source,
     `n05`. You write the quote and the location; keep it plausible and keep `hit` a phrase
     that appears verbatim inside your own `quote` string.

4. **Add 2 new sources** `n10` and `n11`, both `state: "dung"`, following the existing record
   shape exactly (every key that `n01` has). Make one a Vietnamese university document and
   one an English-language primary paper with `lang: "en"`. URLs must end in `.test`. Give
   each a `score` object over the six criteria and a `why` sentence explaining the score.
   Wire at least one of them into `t07` as a second piece of evidence.

## Hard rules the checker enforces

- `loi` (the spoken line) **must contain no digits at all**. Write "ba khái niệm", never "3".
- `loi` must contain no all-caps abbreviations. No "AI", no "LLM". Spell them out in
  Vietnamese: "trí tuệ nhân tạo", "mô hình ngôn ngữ lớn".
- `chu` (on-screen text) is at most 40 characters.
- Every sentence needs `chu` and `hinh`. `hinh` describes what is *seen*, not what is heard.
- Every `hit` must appear verbatim inside its own `quote`.
- A claim of `kind: "Số liệu"` with fewer than two independent domains may not be
  `state: "daxacminh"`.
- `dur` must be within 35% of `word count / 2.9`. Count the words in your `loi` and divide.

## Style

Vietnamese, natural spoken register, one idea per sentence, aimed at a first-year student
who has never programmed. Read each line aloud in your head: if it is hard to say, rewrite
it. Do not use em-dashes anywhere.

## Done means

`node fixtures/check.mjs` exits 0, reports 11 sentences, 8 claims, 9 sources, and zero
errors. Do not edit `fixtures/check.mjs` to make it pass.
