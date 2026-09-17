# Task: write the three docs

Write exactly these three files. Do not touch anything else.

- `docs/RUN.md`
- `docs/ADAPTER.md`
- `docs/DESIGN.md`

Read these first, and describe only what is actually in them: `index.html`, `PLAN.md`,
`src/tokens.css`, `src/app.css`, `src/state.js`, `src/adapter.js`, `src/adapter-mock.js`,
`src/adapter-http.js`, `src/export.js`, `fixtures/check.mjs`.

## docs/RUN.md
How to run it. There is no build step and no dependencies: open `index.html` in a browser,
or serve the folder with any static server. Note that `?api=<base-url>` switches to the HTTP
adapter. Document `node fixtures/check.mjs` as the rule checker and list what it enforces by
reading the rule ids and messages out of that file. Add a short "what this costs to run"
section: the mock costs nothing; the figure shown in the UI is fixture data, not measured.
Add a "what it does not do yet" list, taken from section 7 of `PLAN.md`.

## docs/ADAPTER.md
The backend contract. For each of the seven methods on the adapter, give the exact request
shape and response shape by reading `src/adapter-mock.js` and `src/adapter-http.js`. Include
the streaming behaviour of `research` and `rewrite` and the `onEvent` callback. State the
Content Security Policy limit that is written in the header comment of `adapter-http.js`,
in your own words, plainly. Finish with a short section on what a backend must guarantee:
every claim carries at least one evidence passage, every `hit` appears verbatim inside its
`quote`, and a figure with fewer than two independent sources must not be marked verified.

## docs/DESIGN.md
The design system, read out of `src/tokens.css` and `src/app.css`. Cover the three brand
colours and what each is allowed to mean, the semantic colours, the two typefaces and the
type scale, the 4px spacing scale, the single radius system, and the three theme states
light, dark and unstamped. Include the rule that components may not carry literal hex
values. Describe the coverage strip and what each of its six states means, reading the
grade names out of `src/views.js`.

## Style

Vietnamese or English, pick one and stay in it. Plain sentences. No em-dashes. No marketing
language. Tables where a table is clearer than prose. Do not invent features that are not in
the code. If something is unclear from the code, say so in one line rather than guessing.
