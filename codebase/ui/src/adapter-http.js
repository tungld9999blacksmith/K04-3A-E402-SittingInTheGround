/* HTTP adapter. Identical contract to MockAdapter, over fetch.
   Selected when the page is opened with ?api=<base-url>.

   Platform limit, stated plainly: inside a published Artifact the content policy allows
   fetch only to the page's own origin, so this adapter works when the page is served from
   the same origin as the API (run locally, or self-host). The published demo link runs on
   the mock. That is a sandbox boundary, not a missing feature.

   Expected endpoints. The session routes are GET or POST as marked; the rest are POST with
   a JSON body. All return the same shapes the mock returns:
     GET  {base}/sessions                                          -> {sessions:[meta]}
     GET  {base}/sessions/{id}                                     -> {meta, brief, sources, claims, script, cost}
     POST {base}/sessions          {title}                         -> {meta}
     POST {base}/clarify          {brief, answers, askedUpTo}     -> {questions, chips, ack, satisfied, askedUpTo}
     POST {base}/plan             {brief, answers}                -> {prose, criteria}
     POST {base}/research         {plan, brief}                   -> {sources, claims, cost}
     POST {base}/write            {claims, brief, targetSeconds}  -> {sections, sentences}
     POST {base}/rewrite          {sentences, killed}             -> {sentences, changed}
     POST {base}/sources          {url, note}                     -> {id, source}
     POST {base}/conflict         {claimId, choice}                -> {claimId, choice}

   Progress for research and rewrite streams from:
     GET  {base}/research/stream  text/event-stream, one JSON line per trace entry
     GET  {base}/rewrite/stream   same
   If the stream is unavailable the call still resolves; the trace simply arrives at once.

   Errors: any non-2xx answer whose body carries {error: "<cau tieng Viet>"} surfaces that
   sentence to the reviewer; otherwise the status code stands in. See docs/BACKEND.md. */

window.HttpAdapter = function (base) {
  "use strict";

  base = String(base).replace(/\/+$/, "");

  /* The server may explain itself in the body as {error: "<cau tieng Viet>"}. That sentence
     reaches the screen, so prefer it over a bare status code. */
  function unwrap(r, path) {
    if (r.ok) return r.json();
    return r.json().then(
      function (b) { throw new Error((b && b.error) || fallback(r, path)); },
      function () { throw new Error(fallback(r, path)); }
    );
  }

  function fallback(r, path) { return "Máy chủ trả về " + r.status + " cho " + path; }

  function get(path) {
    return fetch(base + path, { headers: { accept: "application/json" } })
      .then(function (r) { return unwrap(r, path); });
  }

  function post(path, body) {
    return fetch(base + path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body || {})
    }).then(function (r) { return unwrap(r, path); });
  }

  /* Opens an SSE stream and forwards each parsed event, then resolves when the POST does.
     A failed stream is not fatal: the request still completes without live progress. */
  function withStream(streamPath, work, onEvent) {
    var es = null;
    if (onEvent && typeof window.EventSource === "function") {
      try {
        es = new EventSource(base + streamPath);
        es.onmessage = function (ev) {
          try { onEvent(JSON.parse(ev.data)); } catch (err) { /* a malformed line is skipped */ }
        };
        es.onerror = function () { if (es) { es.close(); es = null; } };
      } catch (err) { es = null; }
    }
    return work().then(
      function (v) { if (es) es.close(); return v; },
      function (e) { if (es) es.close(); throw e; }
    );
  }

  return {
    name: "http:" + base,

    listSessions: function () { return get("/sessions"); },
    openSession: function (req) { return get("/sessions/" + encodeURIComponent(req.id)); },
    createSession: function (req) { return post("/sessions", req); },

    clarify: function (req) { return post("/clarify", req); },
    plan: function (req) { return post("/plan", req); },

    research: function (req, onEvent) {
      return withStream("/research/stream", function () { return post("/research", req); }, onEvent);
    },

    write: function (req) { return post("/write", req); },

    rewrite: function (req, onEvent) {
      return withStream("/rewrite/stream", function () { return post("/rewrite", req); }, onEvent);
    },

    addSource: function (req) { return post("/sources", req); },
    resolveConflict: function (req) { return post("/conflict", req); }
  };
};
