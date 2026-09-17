import sys, io

def w(m):
    sys.stdout.buffer.write((m + "\n").encode("utf-8"))

def edit(path, pairs, label):
    s = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        if old not in s:
            raise SystemExit("MISS in %s: %r" % (path, old[:70]))
        s = s.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8").write(s)
    w(label)

# Suggestion chips are part of the clarify response, not something the view digs out of a
# fixture. A real backend that returns none simply gets no chips.
edit("src/state.js", [(
    '''    answers: [],
    askedUpTo: 0,''',
    '''    answers: [],
    askedUpTo: 0,
    chips: [],                 /* suggested replies, supplied by clarify() */'''
)], "state: chips live in state")

edit("src/adapter-mock.js", [(
    '''        var asked = req.askedUpTo || 0;
        if (asked === 0) return { questions: F.clarify.questions, ack: null, satisfied: false, askedUpTo: 3 };
        if ((req.answers || []).length < 2) {
          return { questions: [F.clarify.questions[2]], ack: F.clarify.acks[0], satisfied: false, askedUpTo: 3 };
        }
        return { questions: [], ack: F.clarify.acks[1], satisfied: true, askedUpTo: 3 };''',
    '''        var answers = req.answers || [];
        if ((req.askedUpTo || 0) === 0) {
          return { questions: F.clarify.questions, chips: F.clarify.chips[0], ack: null, satisfied: false, askedUpTo: 3 };
        }
        if (answers.length < 2) {
          return { questions: [F.clarify.questions[2]], chips: F.clarify.chips[1], ack: F.clarify.acks[0], satisfied: false, askedUpTo: 3 };
        }
        return { questions: [], chips: [], ack: F.clarify.acks[1], satisfied: true, askedUpTo: 3 };'''
)], "adapter-mock: clarify returns chips")

edit("src/adapter-http.js", [(
    '''     POST {base}/clarify          {brief, answers, askedUpTo}     -> {questions, ack, satisfied, askedUpTo}''',
    '''     POST {base}/clarify          {brief, answers, askedUpTo}     -> {questions, chips, ack, satisfied, askedUpTo}'''
)], "adapter-http: document chips")

edit("src/views.js", [(
    '''  function chips(st) {
    if (st.phase !== "clarify" || st.busy) return "";
    var sets = window.FIXTURE.clarify.chips;
    var set = sets[Math.min(st.answers.length, sets.length - 1)];
    return set.map(function (c) { return '<button class="chip" data-chip="' + esc(c) + '">' + esc(c) + "</button>"; }).join("");
  }''',
    '''  function chips(st) {
    if (st.phase !== "clarify" || st.busy || !st.chips || !st.chips.length) return "";
    return st.chips.map(function (c) {
      return '<button class="chip" data-chip="' + esc(c) + '">' + esc(c) + "</button>";
    }).join("");
  }'''
)], "views: chips read from state")

edit("src/app.js", [(
    '''        S.set({ busy: false, askedUpTo: r.askedUpTo });''',
    '''        S.set({ busy: false, askedUpTo: r.askedUpTo, chips: r.chips || [] });'''
), (
    '''    /* The first thing the reviewer types IS the brief. Nothing is preloaded. */
    if (!st.brief) {''',
    '''    S.set({ chips: [] });                  /* a suggestion used is a suggestion spent */

    /* The first thing the reviewer types IS the brief. Nothing is preloaded. */
    if (!st.brief) {'''
)], "app.js: chips from the clarify response")

# An empty session should offer an opening suggestion without a round trip.
edit("src/app.js", [(
    '''        if (r.script) S.push({ role: "agent", kind: "script", lead: "Ban kich ban dang luu cua phien nay." });''',
    '''        if (r.script) S.push({ role: "agent", kind: "script", lead: "Ban kich ban dang luu cua phien nay." });
        else S.set({ chips: [] });'''
)], "app.js: a stored session opens on its artifact")
