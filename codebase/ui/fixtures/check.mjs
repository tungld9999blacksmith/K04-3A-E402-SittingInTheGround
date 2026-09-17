/* Rule checker for the script fixture.
   Enforces the organisers' script template (data/studio-pack/c3-scriptscout/mau-kich-ban.md)
   plus the citation and corroboration rules from the brief. Exit 0 = clean.

   Run: node fixtures/check.mjs
   This is the verify gate for any delegated edit, and it is the machine-checkable half of
   the eval's quality dimensions: a reviewer outside the team running it gets the same result.
*/

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = readFileSync(join(root, "src", "fixture.js"), "utf8");

const sandbox = { window: {} };
new Function("window", src)(sandbox.window);
const F = sandbox.window.FIXTURE;

const fail = [];
const warn = [];
const E = (rule, msg) => fail.push(`${rule}: ${msg}`);
const W = (rule, msg) => warn.push(`${rule}: ${msg}`);

const KIEU = new Set(["ke", "giang", "nhe", "hoi", "nhan"]);

/* ---- R1 sentence numbering ---- */
const seen = new Set();
let prev = 0;
for (const s of F.sentences) {
  if (seen.has(s.n)) E("R1", `câu ${s.n} bị trùng số`);
  seen.add(s.n);
  if (s.n <= prev) E("R1", `câu ${s.n} không tăng dần`);
  prev = s.n;
}

for (const s of F.sentences) {
  const id = `câu ${s.n}`;

  /* ---- R2 exactly one of loi / dungGiay ---- */
  const hasLoi = typeof s.loi === "string" && s.loi.length > 0;
  const hasPause = typeof s.dungGiay === "number";
  if (hasLoi === hasPause) E("R2", `${id} phải có đúng một trong loi hoặc dungGiay`);

  /* ---- R3 kieu from the fixed set ---- */
  if (s.kieu != null && !KIEU.has(s.kieu)) E("R3", `${id} có kiểu đọc lạ: ${s.kieu}`);

  if (hasLoi) {
    /* ---- R4 no digits in spoken text ---- */
    const digits = s.loi.match(/\d/g);
    if (digits) E("R4", `${id} có chữ số trong lời đọc: ${digits.join("")}`);

    /* ---- R5 no unspoken abbreviations ---- */
    const abbr = s.loi.match(/\b[A-Z]{2,}\b/g);
    if (abbr) E("R5", `${id} có viết tắt không đọc được: ${abbr.join(", ")}`);

    /* ---- R6 one sentence per line ---- */
    const stops = (s.loi.match(/[.!?](\s|$)/g) || []).length;
    if (stops > 1) W("R6", `${id} có ${stops} câu trong một mục, sẽ dồn vào một cảnh`);

    /* ---- R11 duration plausible at 2.9 syllables per second ---- */
    const syl = s.loi.trim().split(/\s+/).length;
    const expect = syl / F.syllablesPerSecond;
    if (Math.abs(expect - s.dur) / expect > 0.35) {
      W("R11", `${id} thời lượng ${s.dur} giây lệch nhiều so với ${expect.toFixed(1)} giây tính từ ${syl} tiếng`);
    }
  }

  /* ---- R7 on-screen text cap ---- */
  if (typeof s.chu === "string" && s.chu.length > 40) {
    E("R7", `${id} chữ trên màn hình dài ${s.chu.length} ký tự, tối đa là bốn mươi`);
  }
  if (hasLoi && !s.chu) W("R7", `${id} thiếu chữ trên màn hình`);
  if (hasLoi && !s.hinh) W("R7", `${id} thiếu ý đồ hình`);

  /* ---- R8 every cited claim exists (a sentence may cite several) ---- */
  const cited = Array.isArray(s.cls) && s.cls.length ? s.cls : (s.cl ? [s.cl] : []);
  for (const cid of cited) {
    if (!F.claims[cid]) E("R8", `${id} trỏ tới thông tin không có: ${cid}`);
  }
  if (new Set(cited).size !== cited.length) E("R8", `${id} dẫn trùng một mã thông tin`);

  /* ---- R12 sections declared ---- */
  if (!F.sections.some((x) => x.no === s.sec)) E("R12", `${id} thuộc phần ${s.sec} chưa khai báo`);
}

/* ---- R9 evidence integrity: source exists, and the highlighted phrase is really in the quote ---- */
for (const [cid, c] of Object.entries(F.claims)) {
  if (!Array.isArray(c.evidence) || c.evidence.length === 0) {
    E("R9", `${cid} không có đoạn trích nào làm bằng chứng`);
    continue;
  }
  for (const e of c.evidence) {
    if (!F.sources[e.src]) E("R9", `${cid} dẫn nguồn không có: ${e.src}`);
    if (!e.quote || !e.at) E("R9", `${cid} thiếu đoạn trích hoặc vị trí cho ${e.src}`);
    if (e.hit && e.quote && !e.quote.includes(e.hit)) {
      E("R9", `${cid} phần bôi vàng không nằm trong đoạn trích của ${e.src}`);
    }
  }

  /* ---- R10 corroboration: a figure needs two independent sources or it is flagged ---- */
  const domains = new Set(c.evidence.map((e) => (F.sources[e.src]?.url || "").split("/")[0]));
  const independent = domains.size;
  if (c.kind === "Số liệu" && independent < 2 && c.state === "daxacminh") {
    E("R10", `${cid} là số liệu chỉ có ${independent} nguồn độc lập nhưng đánh dấu đã xác minh`);
  }
  if (c.state === "chuaxacminh" && !c.unverified) E("R10", `${cid} chưa xác minh nhưng không nói vì sao`);
  if (c.state === "mauthuan" && !c.conflict) E("R10", `${cid} đánh dấu mâu thuẫn nhưng không có hai phương án`);
}

/* ---- R13 blocked and unreadable sources carry a reason and back nothing ---- */
for (const [sid, s] of Object.entries(F.sources)) {
  if (["loai", "chan", "khongdoc"].includes(s.state)) {
    if (!s.removedWhy) E("R13", `${sid} bị loại hoặc chặn nhưng không ghi lý do`);
    const used = Object.entries(F.claims).filter(([, c]) => c.evidence.some((e) => e.src === sid));
    if (s.state !== "loai" && used.length) {
      E("R13", `${sid} ở trạng thái ${s.state} nhưng vẫn làm bằng chứng cho ${used.map(([k]) => k).join(", ")}`);
    }
  }
  if (s.state === "chan" && !s.injected) E("R13", `${sid} bị chặn vì lệnh ẩn nhưng không lưu lại chữ ẩn`);
}

/* ---- report ---- */
const tick = (n) => `${n} câu, ${Object.keys(F.claims).length} thông tin, ${Object.keys(F.sources).length} nguồn`;
console.log(`fixture: ${tick(F.sentences.length)}`);
for (const w of warn) console.log(`  warn  ${w}`);
if (fail.length) {
  for (const f of fail) console.log(`  FAIL  ${f}`);
  console.log(`\n${fail.length} lỗi, ${warn.length} cảnh báo`);
  process.exit(1);
}
console.log(`  ok    13 luật, ${warn.length} cảnh báo, không lỗi`);
