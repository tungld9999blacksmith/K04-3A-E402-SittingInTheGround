# Adapter Backend Contract

> This file is the endpoint and payload reference. For what the backend must actually
> **do** — the research pipeline, credibility scoring, the citation self-audit,
> corroboration, conflicts, and the eleven guarantees the interface relies on — read
> [BACKEND.md](BACKEND.md) first. It is written in Vietnamese, for the team.

The application interface communicates with backend services exclusively through an adapter object (`window.Adapter`). Views never fetch data directly.

Two implementations share this contract:
- `src/adapter-mock.js`: Uses fixture data and timed delays for local testing and demos.
- `src/adapter-http.js`: Makes HTTP calls to an external REST and Server-Sent Events API.

When initialized with `?api=<base-url>`, `src/adapter.js` loads `window.HttpAdapter`. If the server omits any method, the adapter falls back to `window.MockAdapter` for that specific method so the interface remains functional.

## Adapter Methods

The adapter defines seven methods. Every method returns a Promise.

### 1. clarify

Refines the initial user brief through iterative clarification questions.

- HTTP Endpoint: `POST /clarify`
- Request shape:
  ```json
  {
    "brief": {
      "topic": "string",
      "goal": "string",
      "learners": "string",
      "duration": "string",
      "targetSeconds": 30
    },
    "answers": ["string"],
    "askedUpTo": 0
  }
  ```
- Response shape:
  ```json
  {
    "questions": ["string"],
    "ack": "string or null",
    "satisfied": true,
    "askedUpTo": 3
  }
  ```

### 2. plan

Generates the research outline and rubric scoring criteria before searching begins.

- HTTP Endpoint: `POST /plan`
- Request shape:
  ```json
  {
    "brief": {
      "topic": "string",
      "goal": "string",
      "learners": "string",
      "duration": "string",
      "targetSeconds": 30
    },
    "answers": ["string"]
  }
  ```
- Response shape:
  ```json
  {
    "prose": ["string"],
    "criteria": [
      {
        "id": "string",
        "label": "string",
        "weight": 1
      }
    ]
  }
  ```

### 3. research

Searches for sources, extracts claims, and assesses credibility. Supports live progress streaming.

- HTTP Endpoint: `POST /research`
- Streaming Endpoint: `GET /research/stream` (optional Server-Sent Events stream)
- Invocation: `adapter.research(req, onEvent)`
- Request shape:
  ```json
  {
    "plan": {
      "prose": ["string"],
      "criteria": [{ "id": "string", "label": "string", "weight": 1 }]
    }
  }
  ```
- Streaming event shape (received via `onEvent`):
  ```json
  {
    "kind": "ok",
    "t": 1.2,
    "text": "Đang tìm kiếm tài liệu..."
  }
  ```
  Valid `kind` values include `ok`, `stop`, `skip`, and `caution`.
- Response shape:
  ```json
  {
    "sources": {
      "n01": {
        "title": "string",
        "org": "string",
        "url": "string",
        "published": "string",
        "fetched": "string",
        "kind": "string",
        "lang": "vi",
        "trust": "cao",
        "score": { "author": 1, "date": 1, "fresh": 1, "cites": 1, "primary": 1, "record": 1 },
        "why": "string",
        "state": "dung"
      }
    },
    "claims": {
      "c01": {
        "text": "string",
        "kind": "Khái niệm",
        "state": "daxacminh",
        "evidence": [
          {
            "src": "n01",
            "quote": "string",
            "hit": "string",
            "at": "string"
          }
        ]
      }
    },
    "cost": 0.31
  }
  ```

### 4. write

Drafts the lecture script based on verified claims and a target duration.

- HTTP Endpoint: `POST /write`
- Request shape:
  ```json
  {
    "claims": {},
    "targetSeconds": 30
  }
  ```
- Response shape:
  ```json
  {
    "sections": [
      {
        "no": 1,
        "name": "string"
      }
    ],
    "sentences": [
      {
        "n": 1,
        "sec": 1,
        "kieu": "ke",
        "loi": "string",
        "chu": "string",
        "hinh": "string",
        "cl": "c01",
        "dur": 2.8,
        "state": "new"
      }
    ]
  }
  ```

### 5. rewrite

Regenerates sentences impacted by rejected claims or sources, keeping unaffected sentences identical. Supports live progress streaming.

- HTTP Endpoint: `POST /rewrite`
- Streaming Endpoint: `GET /rewrite/stream` (optional Server-Sent Events stream)
- Invocation: `adapter.rewrite(req, onEvent)`
- Request shape:
  ```json
  {
    "sentences": [
      {
        "n": 1,
        "sec": 1,
        "kieu": "ke",
        "loi": "string",
        "cl": "c01",
        "dur": 2.8
      }
    ],
    "killed": {
      "c02": true
    }
  }
  ```
- Streaming event shape (received via `onEvent`):
  ```json
  {
    "kind": "ok",
    "t": 0.5,
    "text": "Đang loại bỏ câu phụ thuộc..."
  }
  ```
- Response shape:
  ```json
  {
    "sentences": [
      {
        "n": 1,
        "shown": 1,
        "sec": 1,
        "kieu": "ke",
        "loi": "string",
        "cl": "c01",
        "dur": 2.8,
        "state": "keep",
        "was": null
      },
      {
        "n": 3,
        "shown": 2,
        "sec": 1,
        "kieu": "ke",
        "loi": "string replacement",
        "cl": "c03",
        "dur": 3.1,
        "state": "redo",
        "was": "original text before rewrite"
      }
    ],
    "changed": [
      { "n": 2, "how": "bo" },
      { "n": 3, "how": "vietlai" }
    ]
  }
  ```

### 6. addSource

Appends a user-provided source to the dossier for verification.

- HTTP Endpoint: `POST /sources`
- Request shape:
  ```json
  {
    "url": "https://example.com/source",
    "note": "string"
  }
  ```
- Response shape:
  ```json
  {
    "id": "n06",
    "source": {
      "title": "string",
      "org": "string",
      "url": "example.com/source",
      "published": "string",
      "fetched": "string",
      "kind": "string",
      "lang": "vi",
      "trust": "dangthamdinh",
      "why": "string",
      "note": "string",
      "state": "thamdinh"
    }
  }
  ```

### 7. resolveConflict

Records the reviewer choice when two sources present contradictory claims.

- HTTP Endpoint: `POST /conflict`
- Request shape:
  ```json
  {
    "claimId": "c03",
    "choice": "opt-a"
  }
  ```
- Response shape:
  ```json
  {
    "claimId": "c03",
    "choice": "opt-a"
  }
  ```

## Streaming Behaviour and the onEvent Callback

Both `research` and `rewrite` support streaming status updates to display live progress bars and trace logs in the interface.

- In `src/adapter-mock.js`, simulation steps iterate over fixture arrays using sequential timers (`pace` and `wait`). For each step, `onEvent(item)` is called before resolving the final response object.
- In `src/adapter-http.js`, the `withStream(streamPath, work, onEvent)` helper opens an `EventSource` connection to the matching stream endpoint (`/research/stream` or `/rewrite/stream`).
- Incoming events trigger `es.onmessage`, which parses each JSON line and forwards the payload to `onEvent(parsedEvent)`.
- When the primary HTTP POST request finishes or throws an error, the `EventSource` connection is closed cleanly.
- If the streaming connection fails or `EventSource` is unsupported, the error is caught silently. The primary HTTP POST request continues and resolves normally, delivering the complete response without live streaming.

## Content Security Policy Boundary

When the application is embedded inside a sandboxed iframe or a published artifact platform, the browser Content Security Policy forbids network requests (`fetch`) to external or foreign origins. Under those conditions, `adapter-http.js` cannot reach a different domain.

To use the HTTP adapter with a real backend server, the application and the API must be served from the same origin, such as when hosting locally or running behind a reverse proxy. When viewed as an isolated published demo, the interface stays on `adapter-mock.js`. This restriction is an intentional platform sandbox constraint rather than an application defect.

## Backend Integrity Guarantees

A compliant backend implementation must satisfy three strict rules:

1. Evidence presence: Every claim returned by the backend must carry at least one valid evidence entry in its `evidence` array (`bangChung`), specifying `src`, `quote`, and `at`.
2. Verbatim excerpt match: For every evidence entry, the highlighted segment (`hit`) must occur word-for-word inside the cited passage (`quote`).
3. Dual-source verification for numbers: Any claim categorized as numerical data (`Số liệu`) must not be marked verified (`daxacminh`) unless backed by at least two independent domains. If fewer than two independent sources exist, the claim must be marked unverified (`chuaxacminh`) with an explanation in `unverified`, or conflicting (`mauthuan`) with options in `conflict`.
