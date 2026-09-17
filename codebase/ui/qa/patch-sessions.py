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

# ---------------- index.html ----------------
edit("index.html", [(
    '''    <img src="src/vinuni-logo.png" alt="VinUniversity" width="24" height="24">
    <span class="nm">ScriptScout</span>''',
    '''    <button class="back" id="back" hidden aria-label="Quay lai danh sach kich ban" title="Quay lai danh sach">
      <svg width="17" height="17" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M11 3.5L5.5 9l5.5 5.5"/></svg>
    </button>
    <img src="src/vinuni-logo.png" alt="VinUniversity" width="24" height="24">
    <span class="nm">ScriptScout</span>
    <span class="crumb" id="crumb"></span>'''
), (
    '''      <main class="thread" id="thread" aria-live="polite"></main>''',
    '''      <main class="thread" id="thread" aria-live="polite"></main>
      <div class="list" id="list" hidden></div>'''
)], "index.html: back control, crumb, list mount")

# ---------------- app.css ----------------
edit("src/app.css", [(
    '''.top .right { margin-left: auto; display: flex; align-items: center; gap: var(--s4); }''',
    '''.top .right { margin-left: auto; display: flex; align-items: center; gap: var(--s4); }
.top .back { color: var(--rail-fg); border-radius: var(--r-ctl); padding: 4px; display: grid; place-items: center; }
.top .back:hover { background: var(--rail-hover); color: #fff; }
.top .crumb { font: var(--t-body-sm); color: var(--rail-dim); max-width: 44ch; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.top .crumb::before { content: "/"; margin-right: var(--s2); opacity: .5; }

.list { width: 100%; max-width: 900px; margin: 0 auto; padding: var(--s6) var(--s5) var(--s7); display: flex; flex-direction: column; gap: var(--s4); }
.list .s { cursor: pointer; }'''
)], "app.css: back, crumb, list")

# ---------------- app.js ----------------
BOOT_OLD = '''  /* ---------- boot: a session already under way ---------- */
  S.set({ brief: F.brief, phase: "clarify" });
  S.push({ role: "user", kind: "text", html: V.esc(F.brief.raw) });
  S.push({ role: "agent", kind: "text", html: "<p>Rõ rồi. Ba câu cho chắc, anh trả lọi câu nào cũng được:</p>" + questionList(F.clarify.questions) });
  S.set({ askedUpTo: 3 });
  render();'''

s = io.open("src/app.js", encoding="utf-8").read()
# locate the boot block tolerantly
i = s.find("/* ---------- boot: a session already under way ---------- */")
if i < 0:
    raise SystemExit("boot block not found")
j = s.find("render();", i)
if j < 0:
    raise SystemExit("render() after boot not found")
j = j + len("render();")

BOOT_NEW = '''  /* ---------- sessions ---------- */
  function loadList(push) {
    S.resetSession();
    S.set({ view: "list", meta: null, loading: true });
    if (push !== false) history.pushState({ view: "list" }, "", location.pathname + location.search);
    A.listSessions()
      .then(function (r) { S.set({ loading: false, sessions: r.sessions }); })
      .catch(function (e) { S.set({ loading: false }); fail(e); });
  }

  function openSession(id, push) {
    S.resetSession();
    S.set({ loading: true });
    A.openSession({ id: id })
      .then(function (r) {
        S.resetSession();
        S.set({
          view: "session", loading: false, meta: r.meta,
          brief: r.brief, sources: r.sources || {}, claims: r.claims || {},
          script: r.script, baseline: r.script ? JSON.parse(JSON.stringify(r.script)) : null,
          cost: r.cost || 0,
          phase: r.script ? "script" : "clarify",
          focus: null
        });
        /* A stored session shows its artifact, not a replayed conversation. */
        if (r.script) S.push({ role: "agent", kind: "script", lead: "Ban kich ban dang luu cua phien nay." });
        if (push !== false) history.pushState({ view: "session", id: id }, "", location.pathname + location.search + "#" + id);
        setTimeout(function () { $("say").focus(); }, 0);
      })
      .catch(function (e) { S.set({ loading: false }); fail(e); });
  }

  function newSession() {
    S.set({ loading: true });
    A.createSession({ title: "Phien moi" })
      .then(function (r) {
        S.resetSession();
        var list = S.get().sessions.slice();
        list.unshift(r.meta);
        S.set({ view: "session", loading: false, meta: r.meta, sessions: list, brief: null, phase: "clarify" });
        history.pushState({ view: "session", id: r.meta.id }, "", location.pathname + location.search + "#" + r.meta.id);
        setTimeout(function () { $("say").focus(); }, 0);
      })
      .catch(function (e) { S.set({ loading: false }); fail(e); });
  }

  window.addEventListener("popstate", function (e) {
    var st = e.state;
    if (st && st.view === "session" && st.id) openSession(st.id, false);
    else loadList(false);
  });

  /* ---------- boot ---------- */
  var deep = (location.hash || "").replace(/^#/, "");
  if (deep) {
    openSession(deep, false);
    A.listSessions().then(function (r) { S.set({ sessions: r.sessions }); }).catch(function () {});
  } else {
    loadList(false);
  }
  render();'''

s = s[:i] + BOOT_NEW + s[j:]
io.open("src/app.js", "w", encoding="utf-8").write(s)
w("app.js: boot replaced with session routing")

edit("src/app.js", [(
    '''  window.PACE = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 1;''',
    '''  /* Pacing is opt-in. ?demo=1 restores rehearsal timing for a live walkthrough;
     reduced motion always wins. Default is instant, because real latency comes from the
     real backend and the UI must not depend on timing it will not have. */
  var q = new URLSearchParams(location.search);
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  window.PACE = q.get("demo") === "1" && !reduced ? 1 : 0;'''
), (
    '''      var st = S.get();
      $("rail").innerHTML = V.rail(st);
      $("thread").innerHTML = V.thread(st);
      $("inspect").innerHTML = V.inspector(st);
      $("chips").innerHTML = V.chips(st);''',
    '''      var st = S.get();
      var inSession = st.view === "session";

      $("rail").innerHTML = V.rail(st);
      $("list").hidden = inSession;
      $("thread").hidden = !inSession;
      document.querySelector(".composer").hidden = !inSession;
      $("inspect").hidden = !inSession;
      $("back").hidden = !inSession;
      $("crumb").textContent = inSession && st.meta ? st.meta.title : "";

      if (inSession) {
        $("thread").innerHTML = V.thread(st);
        $("inspect").innerHTML = V.inspector(st);
        $("chips").innerHTML = V.chips(st);
      } else {
        $("list").innerHTML = V.sessionList(st);
      }'''
), (
    '''    S.push({ role: "user", kind: "text", html: V.esc(text.trim()) });
    st.answers.push(text.trim());''',
    '''    S.push({ role: "user", kind: "text", html: V.esc(text.trim()) });

    /* The first thing the reviewer types IS the brief. Nothing is preloaded. */
    if (!st.brief) {
      S.set({ brief: {
        topic: text.trim().slice(0, 120), goal: "", learners: "", duration: "",
        targetSeconds: (st.meta && st.meta.target) || 30, raw: text.trim()
      } });
      st = S.get();
    } else {
      st.answers.push(text.trim());
    }'''
), (
    '''    if (t.id === "send") { say($("say").value); $("say").value = ""; return; }''',
    '''    if (t.id === "back") { loadList(); return; }
    if (d.open) { openSession(d.open); return; }
    if (d.filter) { S.set({ filter: d.filter }); return; }
    if (d.act === "new") { newSession(); return; }
    if (t.id === "send") { say($("say").value); $("say").value = ""; return; }'''
), (
    '''"[data-act],[data-kill],[data-revive],[data-chip],[data-jump],[data-row],[data-src],[data-tab],[data-copy],#send"''',
    '''"[data-act],[data-kill],[data-revive],[data-chip],[data-jump],[data-row],[data-src],[data-tab],[data-copy],[data-open],[data-filter],#send,#back"'''
), (
    '''    if (e.key === "j") { e.preventDefault(); move(1); }''',
    '''    if (e.key === "Escape" && S.get().view === "session") { e.preventDefault(); loadList(); return; }
    if (S.get().view !== "session") return;
    if (e.key === "j") { e.preventDefault(); move(1); }'''
)], "app.js: pacing, render split, brief from first message, list wiring, Escape")
