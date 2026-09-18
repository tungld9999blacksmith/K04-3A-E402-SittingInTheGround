# ScriptScout UI — build plan

Owner: Việt · Driver: Opus (architecture, review, QA) · Grunt work: Gemini Flash via `agy-task`
Started 2026-09-17 · Target: polished mockup by 18/9, backend-pluggable.

---

## 1. Objective

A reviewer-grade interface for an agent that finds its own sources and writes a cited
lecture script. It must survive a judge driving it cold: give it a topic, watch it sift
sources, open any sentence and see the passage that proves it, reject a fact and watch only
the dependent sentences change.

**Non-negotiable:** the UI ships with a seam where a real backend plugs in without touching
a single view. Today every seam is filled by a mock. Tomorrow it is filled by HTTP.

## 2. Where I disagree with the brief, and what I propose instead

Viet asked for disagreement, so here it is. Four changes.

**2.1 The dossier is a panel mode, not a page.** The instruction was "source review is good
but place it on the side." Taken literally that means two surfaces competing for the right
rail. Instead the right rail is **one inspector with two modes** — `Bằng chứng` (follows
your cursor, per sentence) and `Hồ sơ nguồn` (the whole source list, always reachable).
The judges' required move, *open the dossier and drop a source*, becomes one click and never
leaves the script. Rationale: a reviewer's attention should never leave the artifact they
are approving.

**2.2 Add a coverage strip.** A thin band above the script, one cell per sentence, coloured
by evidence state: two-source verified, single-source, unverified, no-source-needed. The
25% criterion is "every sentence traces to a source" and right now you can only discover a
weak sentence by hovering all of them. The strip makes the weak spots findable in one look,
and doubles as a jump control. This is the single highest-value addition on the list.

**2.3 Traps belong in the flow, not in a gallery.** The three hard cases were heading for a
"here are three bad situations" page. That is a slide, not a system. Instead: the hidden
instruction and the dead link surface **as they happen in the research trace**, and both
leave a permanent flagged row in the dossier with the reason. The two-source conflict
surfaces as a claim the writer **refuses to state as a number** until the reviewer resolves
it. The judges asked to see how the system reacts. Reacting is in-flow.

**2.4 Keyboard review.** A reviewer working through forty sentences with a mouse is slow.
`j` / `k` move between sentences, `x` rejects the focused one, `u` undoes, `/` focuses the
composer. Costs an afternoon, and it is the difference between a demo and a tool.

## 3. What stays exactly as specified

Chat as the spine. Plan as prose with two actions. Hover to inspect. Buttons rationed.
Left rail for structure, right rail for detail. VinUni navy, red and gold. Noto Serif
headings. All of that was right.

## 4. Architecture

Sentence is the unit of state, and it cites a **claim**, not a source. The claim carries the
evidence and the corroboration count. This is the organisers' own three-level shape
(`nguon` → `thongTin` → `cau.nguon`) and it is what makes selective rewrite fall out for
free: kill a claim, find the sentences whose `cl` matches, regenerate only those.

### 4.1 The adapter seam

Every view talks to one object. Nothing else knows where data comes from.

```
Adapter {
  clarify({brief, answers})        -> {questions[], satisfied}
  plan({brief, answers})           -> {prose[], criteria[]}
  research({plan}, onEvent)        -> {sources[], claims[], flags[]}
  write({claims, targetSeconds})   -> {sections[], sentences[]}
  rewrite({sentences, killed}, onEvent) -> {sentences[], changed[]}
  addSource({url, note})           -> {source}
  resolveConflict({claimId, choice}) -> {claim}
}
```

- `adapter-mock.js` — fixture plus timers. What the demo runs on.
- `adapter-http.js` — same contract over `fetch`, base URL from `?api=`.
- `adapter.js` — picks one. Mock unless `?api=` is present.

`onEvent` is how the trace streams, so a real backend can push progress without the views
changing. Mock calls it on a timer; HTTP calls it from SSE or a poll.

**Honest limit:** inside a published Artifact the CSP blocks `fetch` to any other origin, so
`adapter-http.js` only works when the page is served from the same origin as the API — that
is, run locally or self-hosted. The published link stays the mock demo. This is a platform
boundary, not a design shortcut, and it goes in the README.

### 4.2 Files

No build step, no ES modules, so the page opens from `file://` and can also publish as a
multi-file artifact.

```
index.html            shell + mount points
src/tokens.css        colour, type, spacing, radius, both themes
src/app.css           components
src/fixture.js        the organisers' sample data, verbatim
src/state.js          store, derived selectors, undo stack
src/adapter*.js       the seam
src/views/*.js        thread, script, inspector, rail, composer, coverage
docs/                 DESIGN.md · ADAPTER.md · RUN.md
qa/                   screenshots and the QA log
```

## 5. Phases and exit criteria

| # | Phase | Exit criterion | Who |
|---|---|---|---|
| P1 | Tokens and design system extracted, documented in `docs/DESIGN.md` | Every colour and size is a token; no literal hex in components | Opus writes, Flash documents |
| P2 | State store, undo stack, adapter seam, mock adapter | Views read only from the store; swapping to a stub adapter changes nothing visually | Opus only |
| P3 | Surfaces: thread, plan, trace, script, coverage strip, two-mode inspector, add-source, export | Every surface renders from the store; no hardcoded markup | Opus builds, Flash does repetitive view code |
| P4 | States: empty, loading, error, conflict-unresolved, all-sources-rejected | Each reachable in the browser and screenshotted | Opus |
| P5 | Copy pass, Vietnamese audit, keyboard review, focus order | Every string reviewed; full flow drivable without a mouse | Flash drafts, Opus approves |
| P6 | QA loop: 1440 / 1024 / 400, light and dark, reduced motion | Zero console errors, no horizontal scroll, contrast checked, receipts in `qa/` | Opus |
| P7 | Package: README, cost per run, known limits, commit, publish | A teammate can clone and run it from the README alone | Opus |

Loop discipline: after every phase I drive the real flow in the headless browser, screenshot,
and fix what the screenshot shows. No phase is closed on inspection of source alone.

## 6. Division of labour

Flash gets work that is mechanical and machine-checkable: fixture transcription, repetitive
view functions against a fixed contract, copy tables, documentation drafts, audit checklists.
Every Flash output is gated by `--verify` and reviewed by me before it lands.

Flash does **not** get: the state store, the adapter contract, the undo stack, anything where
a wrong decision is invisible until the demo.

## 7. Known limits, to be stated in the README

- The mock adapter's timings are theatre. Real research takes minutes, not sixteen seconds.
- `adapter-http.js` cannot reach a foreign origin from inside a published artifact.
- Source credibility scoring is a published rubric applied by hand in the fixture, not a
  model. The real one needs the scorer wired behind `research()`.
- The script is thirty seconds of one lesson, not a full forty-sentence script.

## 8. The thing this plan does not cover

CP3 closes at 16:00 today and needs a real AI call, a golden set of at least twenty cases and
a results table with percentages. CP4 closes at 21:00 today and freezes the spec and the
quality bar. Those two gates carry 56 of the 67 graded points; this UI carries 8.

The fixture in this project is already most of a golden set, so the cheap move is to emit
`eval/golden.json` from it as a by-product of P3. That is tracked here so it does not get
lost, but it is not a substitute for the spec work, and the spec work is not in this plan.
