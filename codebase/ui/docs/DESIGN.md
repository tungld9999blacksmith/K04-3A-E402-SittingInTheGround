# ScriptScout Design System

The ScriptScout design system is implemented in `src/tokens.css` (variables and tokens) and `src/app.css` (components and layout).

All style values are driven by CSS custom properties. Components in `src/app.css` never use literal hex color codes.

## Brand Colors

ScriptScout uses three VinUniversity brand colors defined in `src/tokens.css`. Each brand color has a dedicated role:

| Color Token | Hex Value | Allowed Meaning and Usage |
| --- | --- | --- |
| `--brand-navy` | `#0A3B75` | Primary brand identity. Used for structural hierarchy, top header, left navigation rail background, primary action buttons, active navigation states, and single-source evidence indicators. |
| `--brand-red` | `#A31D24` | Stopping and destructive actions (`--stop`). Used for rejected claims, dropped sentences, blocked prompt injection attempts, removal reasons, and critical errors. It is never used as decorative accent trim. |
| `--brand-gold` | `#D6A21E` | Caution and attention marks (`--caution-mark`). Used for unverified claims, conflicting data points awaiting human decision, and timing warnings. It is never used as general ornamental styling. |

## Semantic Colors

Semantic tokens express state rather than decorative styling:

| Token | Light Theme | Dark Theme | Purpose |
| --- | --- | --- | --- |
| `--ok` / `--ok-tint` | `#1C6B4B` / `#ECF4F0` | `#6FC79E` / `#142520` | Verified evidence state, successful actions, valid duration timing. |
| `--caution` / `--caution-tint` | `#8A6410` / `#FDF7E8` | `#E3BA57` / `#2A2313` | Warnings, unverified claims, duration overages. |
| `--caution-mark` | `#D6A21E` | `#D6A21E` | Highlighting unverified or conflicting tags and meter levels. |
| `--stop` / `--stop-tint` | `#A31D24` / `#FCF2F2` | `#F19BA3` / `#2B1A1D` | Rejected claims, deleted sentences, blocked sources. |

### Primary Ramp and Neutrals

- Navy ramp: `--navy`, `--navy-strong`, `--navy-hover`, `--navy-tint`, `--navy-line`, and `--on-navy` provide high-contrast foreground and interactive button states.
- Neutrals: Tuned with a cool blue cast to harmonize with navy. Includes `--ink` (primary text), `--ink-2` (secondary text), `--muted` (subtext and captions), `--canvas` (page background), `--surface` (card background), `--surface-2` (secondary cards), and `--line` / `--line-strong` (structural borders).
- Navigation rail: `--rail-bg`, `--rail-fg`, `--rail-dim`, `--rail-hover`, and `--rail-active` maintain a consistent dark navy background in both themes.
- Focus outline: `--focus` (`#2C6FD1` in light, `#83B2F0` in dark) provides accessible focus rings with a 2px offset.

## Typography

ScriptScout pairs two type families:

1. Serif: `'Noto Serif', Georgia, 'Times New Roman', serif`. Used for document titles, section headers, lecture script text (`--t-script`), and quoted source excerpts.
2. Sans: `'Be Vietnam Pro', 'Segoe UI', system-ui, -apple-system, sans-serif`. Used for UI chrome, conversational messages, buttons, labels, and metadata.

### Type Scale

| Token | Specification | Font Family | Usage |
| --- | --- | --- | --- |
| `--t-display` | 600 23px / 1.28 | Serif | Large titles and main headings |
| `--t-title` | 600 17px / 1.35 | Serif | Section headers and artifact titles |
| `--t-script` | 400 16px / 1.52 | Serif | Spoken script dialogue sentences |
| `--t-body` | 400 14px / 1.6 | Sans | Standard body copy and chat messages |
| `--t-body-sm` | 400 12.5px / 1.55 | Sans | Compact descriptions and criteria lists |
| `--t-label` | 600 10.5px / 1.3 | Sans | Uppercase category headings (tracking: 0.1em) |
| `--t-meta` | 400 11.5px / 1.45 | Sans | Timestamps, sentence numbers, and metadata |

## Spacing Scale

Layout spacing uses a strict 4px modular scale:

| Token | Value | Common Usage |
| --- | --- | --- |
| `--s1` | 4px | Micro gaps, button icon spacing, tight badges |
| `--s2` | 8px | Button padding, list item gaps, chips |
| `--s3` | 12px | Card padding, message gaps, definition lists |
| `--s4` | 16px | Container padding, standard margins |
| `--s5` | 20px | Section vertical spacing, rail spacing |
| `--s6` | 26px | Thread padding, block separations |
| `--s7` | 34px | Inspector bottom clearance |

## Radius System

ScriptScout uses a three-tier border radius system:

| Token | Value | Target Components |
| --- | --- | --- |
| `--r-panel` | 10px | Content containers, artifact cards, composer box, chat bubbles |
| `--r-ctl` | 7px | Buttons, input fields, textareas, radio wrappers, quote blocks |
| `--r-pill` | 999px | Filter chips, status tags, mode badges, pill indicators |

## Theme States

The interface supports three theme states:

1. Light theme: The default state declared on `:root`.
2. Dark theme: An explicit dark mode activated when the document element has `[data-theme="dark"]`.
3. Unstamped state: When no explicit theme attribute is set, `@media (prefers-color-scheme: dark)` applies dark tokens to `:root:not([data-theme="light"])`.

Explicit attributes (`[data-theme="light"]` and `[data-theme="dark"]`) override operating system preferences.

## Prohibition of Literal Hex Values

All styling rules in `src/app.css` reference CSS custom properties. Hardcoded hex colors are prohibited in component declarations. This ensures consistent theming across light and dark modes, preserves contrast compliance, and enforces brand standards across the interface.

## Coverage Strip

The coverage strip sits above the script artifact in `src/views.js`. It renders a horizontal bar with one segment per sentence, giving reviewers an immediate visual audit of citation backing. Each cell also acts as a jump button to focus that sentence.

The strip evaluates each sentence into one of six evidence grades:

| Grade Name | Display Label | Token / Color | Meaning |
| --- | --- | --- | --- |
| `verified` | hai nguồn độc lập | `--ok` (`#1C6B4B`) | The claim is corroborated by two or more independent domain origins. |
| `single` | một nguồn | `--navy` (`#0A3B75`) | The claim is backed by a single valid source. |
| `unverified` | chưa xác minh | `--caution-mark` (`#D6A21E`) | The claim lacks sufficient corroboration or relies on an unverified source. |
| `conflict` | nguồn mâu thuẫn | `--caution-mark` (opacity 0.55) | Sources provide contradictory data that requires reviewer resolution. |
| `dead` | đã loại | `--stop` (`#A31D24`) | The claim or its backing source was rejected by the reviewer. |
| `none` | không cần nguồn | `--line-strong` (`#CFD7E2`) | Transitional sentence without factual assertions; requires no citation. |
