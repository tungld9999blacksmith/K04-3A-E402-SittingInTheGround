/* Mock adapter. Same contract as adapter-http.js, backed by the fixture and timers.
   Every method returns a promise; long ones take an onEvent callback so the trace can
   stream. A real backend fills these in without any view changing.
   Pacing comes from window.PACE so reduced-motion can collapse the theatre to zero. */

window.MockAdapter = (function () {
  "use strict";

  var F = window.FIXTURE;

  /* Pacing is off by default. Real latency comes from the real backend, and a mock that
     pretends to take sixteen seconds only teaches the UI to depend on timing it will not
     have. Open with ?demo=1 to put the rehearsal pacing back for a live walkthrough. */
  function pace(ms) { return Math.round(ms * (window.PACE == null ? 0 : window.PACE)); }
  function wait(ms) { var d = pace(ms); return d ? new Promise(function (r) { setTimeout(r, d); }) : Promise.resolve(); }
  function clone(x) { return JSON.parse(JSON.stringify(x)); }

  return {
    name: "mock",

    /* ---- sessions: many people, many scripts ---- */
    listSessions: function () {
      return wait(200).then(function () { return { sessions: clone(F.sessions) }; });
    },

    openSession: function (req) {
      return wait(240).then(function () {
        var meta = F.sessions.filter(function (x) { return x.id === req.id; })[0];
        if (!meta) throw new Error("Không tìm thấy phiên " + req.id);
        /* Only the seeded session carries a full script in the fixture. The rest open at
           the point their state implies, which is what a real store would return. */
        var full = meta.id === "s-001";
        return {
          meta: clone(meta),
          brief: full ? clone(F.brief) : null,
          sources: full ? clone(F.sources) : {},
          claims: full ? clone(F.claims) : {},
          script: full ? { sections: clone(F.sections), sentences: clone(F.sentences) } : null,
          cost: full ? 0.31 : 0
        };
      });
    },

    createSession: function (req) {
      return wait(240).then(function () {
        return {
          meta: {
            id: "s-" + Date.now().toString(36),
            title: (req && req.title) || "Phiên mới",
            owner: "Việt", updated: "vừa xong", state: "nhap",
            lesson: "", seconds: 0, target: 30, sentences: 0, open: 0
          }
        };
      });
    },

    /* The agent asks until it has enough. Mock is satisfied after two answers. */
    clarify: function (req) {
      return wait(620).then(function () {
        var answers = req.answers || [];
        if ((req.askedUpTo || 0) === 0) {
          return { questions: F.clarify.questions, chips: F.clarify.chips[0], ack: null, satisfied: false, askedUpTo: 3 };
        }
        if (answers.length < 2) {
          return { questions: [F.clarify.questions[2]], chips: F.clarify.chips[1], ack: F.clarify.acks[0], satisfied: false, askedUpTo: 3 };
        }
        return { questions: [], chips: [], ack: F.clarify.acks[1], satisfied: true, askedUpTo: 3 };
      });
    },

    plan: function () {
      return wait(700).then(function () {
        return { prose: clone(F.plan), criteria: clone(F.criteria) };
      });
    },

    /* Streams the trace, then hands back the dossier. onEvent(line) per step. */
    research: function (req, onEvent) {
      var lines = clone(F.trace);
      return lines.reduce(function (chain, line) {
        return chain.then(function () {
          return wait(420).then(function () { if (onEvent) onEvent(line); });
        });
      }, Promise.resolve()).then(function () {
        return wait(300).then(function () {
          return { sources: clone(F.sources), claims: clone(F.claims), cost: 0.31 };
        });
      });
    },

    write: function (req, onEvent) {
      if (onEvent) onEvent({ t: 0, kind: "ok", text: "Viết kịch bản từ dữ kiện đã duyệt" });
      return wait(340).then(function () {
        return {
          sections: clone(F.sections),
          sentences: clone(F.sentences).map(function (s) { s.state = "new"; return s; })
        };
      });
    },

    /* Drops sentences whose claim died, renumbers, and bridges the gap.
       Everything untouched comes back byte-identical, which is the whole point. */
    rewrite: function (req, onEvent) {
      var steps = clone(F.rewriteTrace);
      return steps.reduce(function (chain, step) {
        return chain.then(function () {
          return wait(380).then(function () { if (onEvent) onEvent(step); });
        });
      }, Promise.resolve()).then(function () {
        var dead = req.killed || {};
        var kept = [];
        var changed = [];
        var shift = 0;

        req.sentences.forEach(function (s) {
          if (s.cl && dead[s.cl]) { shift++; changed.push({ n: s.n, how: "bo" }); return; }
          var o = clone(s);
          o.shown = s.n - shift;
          o.state = "keep";
          kept.push(o);
        });

        /* A dropped claim may leave a neighbour needing to bridge the gap. */
        Object.keys(dead).forEach(function (cid) {
          var r = F.rewrites[cid];
          if (!r) return;
          kept.forEach(function (o) {
            if (o.n !== r.bridge) return;
            o.was = o.loi;
            o.loi = r.loi;
            o.dur = r.dur;
            o.state = "redo";
            changed.push({ n: o.n, how: "vietlai" });
          });
        });

        return { sentences: kept, changed: changed };
      });
    },

    addSource: function (req) {
      return wait(560).then(function () {
        var s = clone(F.addSourcePreview);
        s.url = (req.url || s.url).replace(/^https?:\/\//, "");
        s.note = req.note || "";
        return { id: "n06", source: s };
      });
    },

    resolveConflict: function (req) {
      return wait(300).then(function () {
        return { claimId: req.claimId, choice: req.choice };
      });
    }
  };
})();
