/* Store. Views read from here and never from the adapter or the fixture directly.
   One mutation path (set), one subscription, one undo stack. Classic script, no modules,
   so the page opens from file:// without a build step. */

window.Store = (function () {
  "use strict";

  var listeners = [];
  var undoStack = [];
  var UNDO_MAX = 40;

  /* Everything a reviewer can change lives in REVIEW. Only these keys are snapshotted for
     undo, so an undo never rewinds the conversation, only the review decisions. */
  var REVIEW = ["killed", "sourceOverride", "conflictChoice", "added", "rewritten", "script"];

  var state = {
    view: "list",              /* list | session */
    sessions: [],              /* [meta] from the backend */
    meta: null,                /* the open session's meta */
    filter: "all",             /* all | mine | duyet */
    loading: false,

    phase: "clarify",          /* clarify | planned | researching | script */
    busy: false,
    thread: [],                /* {id, role, kind, ...} */
    answers: [],
    askedUpTo: 0,
    chips: [],                 /* suggested replies, supplied by clarify() */

    brief: null,
    plan: null,
    criteria: [],

    sources: {},
    claims: {},
    script: null,              /* {sections, sentences} — the live script */
    baseline: null,            /* the first script the agent produced, for diffing */

    killed: {},                /* claimId -> true, rejected by the reviewer */
    sourceOverride: {},        /* sourceId -> 'loai' | 'dung' */
    conflictChoice: {},        /* claimId -> optionId */
    added: null,               /* a source the reviewer supplied */
    rewritten: false,

    focus: null,               /* sentence n, set by click or keyboard */
    hover: null,               /* sentence n, set by pointer */
    inspect: "evidence",       /* evidence | dossier */
    cost: 0,
    usage: null,               /* tokens and searches a real run actually spent */
    error: null,
    seq: 0
  };

  function snapshot() {
    var o = {};
    REVIEW.forEach(function (k) { o[k] = JSON.parse(JSON.stringify(state[k] === undefined ? null : state[k])); });
    return o;
  }

  function emit() { listeners.forEach(function (fn) { fn(state); }); }

  function set(patch, opts) {
    if (opts && opts.undoable) {
      undoStack.push(snapshot());
      if (undoStack.length > UNDO_MAX) undoStack.shift();
    }
    for (var k in patch) state[k] = patch[k];
    emit();
  }

  function undo() {
    var prev = undoStack.pop();
    if (!prev) return false;
    for (var k in prev) state[k] = prev[k];
    emit();
    return true;
  }

  function canUndo() { return undoStack.length > 0; }

  function push(msg) {
    msg.id = "m" + (++state.seq);
    state.thread.push(msg);
    emit();
    return msg;
  }

  /* patch a thread message in place, by id */
  function patchMsg(id, patch) {
    for (var i = 0; i < state.thread.length; i++) {
      if (state.thread[i].id !== id) continue;
      for (var k in patch) state.thread[i][k] = patch[k];
      emit();
      return state.thread[i];
    }
    return null;
  }

  /* ---------- derived ---------- */

  function sourceState(id) {
    if (state.sourceOverride[id]) return state.sourceOverride[id];
    var s = state.sources[id];
    return s ? s.state : "dung";
  }

  /* A source can back evidence only if it is in use. Blocked, unreadable and rejected
     sources cannot, which is the rule that makes a dropped source propagate. */
  function sourceUsable(id) {
    var st = sourceState(id);
    return st === "dung" || st === "thamdinh";
  }

  function claimDead(id) {
    if (!id) return false;
    if (state.killed[id]) return true;
    var c = state.claims[id];
    if (!c) return true;
    for (var i = 0; i < c.evidence.length; i++) {
      if (sourceUsable(c.evidence[i].src)) return false;
    }
    return true;                        /* every source behind it is gone */
  }

  /* Independent corroboration counts distinct registrable domains, not distinct records:
     two pages on one site are one source. */
  function independence(id) {
    var c = state.claims[id];
    if (!c) return 0;
    var seen = {};
    c.evidence.forEach(function (e) {
      if (!sourceUsable(e.src)) return;
      var host = (state.sources[e.src] && state.sources[e.src].url || "").split("/")[0];
      seen[host] = true;
    });
    return Object.keys(seen).length;
  }

  /* A sentence may rest on several claims. Legacy single `cl` still works. */
  function claimsOf(sentence) {
    if (Array.isArray(sentence.cls) && sentence.cls.length) return sentence.cls;
    return sentence.cl ? [sentence.cl] : [];
  }

  /* The sentence asserts all of its claims, so the weakest one sets its grade, and losing
     any one of them means the sentence has to be rewritten. */
  var RANK = ["dead", "conflict", "unverified", "single", "verified", "none"];
  function gradeOne(cid) {
    if (claimDead(cid)) return "dead";
    var c = state.claims[cid];
    if (!c) return "dead";
    if (c.state === "mauthuan" && !state.conflictChoice[cid]) return "conflict";
    if (c.state === "chuaxacminh") return "unverified";
    return independence(cid) >= 2 ? "verified" : "single";
  }

  /* Evidence grade for one sentence, which is what the coverage strip paints. */
  function grade(sentence) {
    var ids = claimsOf(sentence);
    if (!ids.length) return "none";                    /* transition, needs no source */
    var worst = "none";
    ids.forEach(function (cid) {
      var g = gradeOne(cid);
      if (RANK.indexOf(g) < RANK.indexOf(worst)) worst = g;
    });
    return worst;
  }

  function rows() {
    if (!state.script) return [];
    return state.script.sentences.map(function (s) {
      var o = {};
      for (var k in s) o[k] = s[k];
      o.cls = claimsOf(s);
      o.dead = o.cls.some(claimDead);
      o.grade = grade(s);
      return o;
    });
  }

  function coverage() {
    var out = { verified: 0, single: 0, unverified: 0, conflict: 0, dead: 0, none: 0 };
    rows().forEach(function (r) { out[r.grade]++; });
    return out;
  }

  function totalSeconds() {
    return rows().reduce(function (a, r) { return a + (r.dead && state.rewritten ? 0 : r.dur); }, 0);
  }

  /* How many live sentences lean on a source. This is what makes dropping one feel costly. */
  function dependants(sourceId) {
    var n = 0;
    rows().forEach(function (r) {
      var hit = r.cls.some(function (cid) {
        var c = state.claims[cid];
        return c && c.evidence.some(function (e) { return e.src === sourceId; });
      });
      if (hit) n++;
    });
    return n;
  }

  function pendingCuts() {
    return rows().filter(function (r) { return r.dead; }).length;
  }

  /* Reset everything that belongs to one script, so opening another session cannot inherit
     the last one's rejections. */
  function resetSession() {
    state.thread = [];
    state.answers = [];
    state.askedUpTo = 0;
    state.plan = null;
    state.criteria = [];
    state.sources = {};
    state.claims = {};
    state.script = null;
    state.baseline = null;
    state.killed = {};
    state.sourceOverride = {};
    state.conflictChoice = {};
    state.added = null;
    state.rewritten = false;
    state.focus = null;
    state.hover = null;
    state.inspect = "evidence";
    state.cost = 0;
    state.usage = null;
    state.phase = "clarify";
    undoStack.length = 0;
  }

  function visibleSessions() {
    if (state.filter === "mine") return state.sessions.filter(function (x) { return x.owner === "Việt"; });
    if (state.filter === "duyet") return state.sessions.filter(function (x) { return x.state === "duyet"; });
    return state.sessions;
  }

  function liveSources() {
    return Object.keys(state.sources).filter(function (k) { return sourceState(k) === "dung"; }).length
      + (state.added ? 1 : 0);
  }

  return {
    get: function () { return state; },
    set: set,
    subscribe: function (fn) { listeners.push(fn); return function () { listeners = listeners.filter(function (f) { return f !== fn; }); }; },
    push: push,
    patchMsg: patchMsg,
    undo: undo,
    canUndo: canUndo,
    resetSession: resetSession,
    visibleSessions: visibleSessions,
    /* selectors */
    rows: rows,
    grade: grade,
    coverage: coverage,
    totalSeconds: totalSeconds,
    dependants: dependants,
    pendingCuts: pendingCuts,
    liveSources: liveSources,
    claimDead: claimDead,
    claimsOf: claimsOf,
    gradeOne: gradeOne,
    independence: independence,
    sourceState: sourceState,
    sourceUsable: sourceUsable
  };
})();
