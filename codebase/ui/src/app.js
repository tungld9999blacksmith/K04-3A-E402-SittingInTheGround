/* Controller. Wires the adapter to the store, the store to the DOM, and the keyboard to both. */

(function () {
  "use strict";

  var S = window.Store, V = window.View, A = window.Adapter, F = window.FIXTURE;
  var $ = function (id) { return document.getElementById(id); };

  /* Pacing is opt-in. ?demo=1 restores rehearsal timing for a live walkthrough;
     reduced motion always wins. Default is instant, because real latency comes from the
     real backend and the UI must not depend on timing it will not have. */
  var q = new URLSearchParams(location.search);
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  window.PACE = q.get("demo") === "1" && !reduced ? 1 : 0;

  /* ---------- render ---------- */
  var raf = null;
  function render() {
    if (raf) return;
    raf = requestAnimationFrame(function () {
      raf = null;
      var st = S.get();
      var inSession = st.view === "session";

      $("rail").innerHTML = V.rail(st);
      $("list").hidden = inSession;
      $("thread").hidden = !inSession;
      document.querySelector(".composer").hidden = !inSession;
      $("inspect").hidden = !inSession;
      $("back").hidden = !inSession;
      document.querySelector(".cols").classList.toggle("listing", !inSession);
      $("crumb").textContent = inSession && st.meta ? st.meta.title : "";

      if (inSession) {
        $("thread").innerHTML = V.thread(st);
        $("inspect").innerHTML = V.inspector(st);
        $("chips").innerHTML = V.chips(st);
      } else {
        $("list").innerHTML = V.sessionList(st);
      }
      /* null means a real run that did not measure its own cost, which is not the same
         thing as never having run. Do not let one read as the other. */
      var used = shownUsage(st.usage);
      $("cost").textContent = st.cost ? "Chi phí lượt này " + V.money(st.cost) + " đô"
        : used ? used
          : st.cost === null ? "Chưa đo chi phí" : "Bản mô phỏng";
      $("mode").textContent = window.API_DOWN ? "máy chủ không trả lời, đang chạy dữ liệu mẫu"
        : A.name === "mock" ? "dữ liệu mẫu" : "đang nối máy chủ";
      $("mode").title = window.API_DOWN || "";
      $("say").disabled = !!st.busy;
    });
  }
  function sid() { var m = S.get().meta; return m && m.id; }

  /* Each phase reports only what it spent, so the totals add up across the run. */
  function addUsage(a, b) {
    if (!b) return a || null;
    a = a || { tokens: 0, calls: 0, searches: 0 };
    return { tokens: (a.tokens || 0) + (b.tokens || 0),
             calls: (a.calls || 0) + (b.calls || 0),
             searches: (a.searches || 0) + (b.searches || 0) };
  }

  /* Tokens and searches are what a run actually measured. Money needs a rate the
     backend was given, so without one the bar reports the measurement, not a guess. */
  function shownUsage(u) {
    if (!u || !u.tokens) return null;
    var t = u.tokens >= 1000 ? V.vn(u.tokens / 1000) + " nghìn token" : u.tokens + " token";
    return t + (u.searches ? " · " + u.searches + " lượt tìm" : "");
  }

  function toBottom() {
    var m = $("mid");
    m.scrollTop = m.scrollHeight;
  }
  S.subscribe(render);

  function fail(err) {
    S.set({ busy: false });
    S.push({ role: "agent", kind: "text", html: '<div class="note r">' + V.icons.x +
      "<span>Không chạy được bước này: " + V.esc(err && err.message || err) +
      ". Anh thử lại, hoặc kiểm tra máy chủ nếu đang nối thật.</span></div>" });
    toBottom();
  }

  /* ---------- conversation ---------- */
  function say(text) {
    var st = S.get();
    if (st.busy || !text || !text.trim()) return;
    S.push({ role: "user", kind: "text", html: V.esc(text.trim()) });

    S.set({ chips: [] });                  /* a suggestion used is a suggestion spent */

    /* The first thing the reviewer types IS the brief. Nothing is preloaded. */
    if (!st.brief) {
      S.set({ brief: {
        topic: text.trim().slice(0, 120), goal: "", learners: "", duration: "",
        targetSeconds: (st.meta && st.meta.target) || 30, raw: text.trim()
      } });
      /* The session was named before anyone said what it was about. Now we know. */
      var m0 = S.get().meta;
      if (m0) {
        var named = Object.assign({}, m0, { title: text.trim().slice(0, 90), state: "tim" });
        S.set({ meta: named, sessions: S.get().sessions.map(function (x) {
          return x.id === named.id ? named : x;
        }) });
      }
      st = S.get();
    } else {
      st.answers.push(text.trim());
    }
    S.set({ busy: true });
    toBottom();

    A.clarify({ session: sid(), brief: st.brief, answers: st.answers, askedUpTo: st.askedUpTo })
      .then(function (r) {
        S.set({ busy: false, askedUpTo: r.askedUpTo, chips: r.chips || [] });

        /* The agent heard a duration, so the brief must carry it. Without this the script
           is written against the session default and ignores what was actually asked. */
        if (r.targetSeconds && S.get().brief && r.targetSeconds !== S.get().brief.targetSeconds) {
          S.set({ brief: Object.assign({}, S.get().brief, {
            targetSeconds: r.targetSeconds,
            duration: r.targetSeconds >= 60
              ? Math.round(r.targetSeconds / 60) + " phút"
              : Math.round(r.targetSeconds) + " giây"
          }) });
          var mt = S.get().meta;
          if (mt) S.set({ meta: Object.assign({}, mt, { target: r.targetSeconds }) });
        }
        if (r.ack) S.push({ role: "agent", kind: "text", html: "<p>" + V.esc(r.ack) + "</p>" });
        if (r.questions && r.questions.length) {
          S.push({ role: "agent", kind: "text", html: questionList(r.questions) });
        }
        toBottom();
        if (r.satisfied) return drawPlan();
      })
      .catch(fail);
  }

  function questionList(qs) {
    return '<ul class="qs">' + qs.map(function (q) { return "<li>" + V.esc(q) + "</li>"; }).join("") + "</ul>";
  }

  function drawPlan() {
    S.set({ busy: true });
    return A.plan({ session: sid(), brief: S.get().brief, answers: S.get().answers })
      .then(function (p) {
        S.set({ busy: false, phase: "planned", plan: p, criteria: p.criteria });
        S.push({ role: "agent", kind: "plan" });
        toBottom();
      })
      .catch(fail);
  }

  /* Describes what actually came back. This line used to be a fixed string that claimed
     five sentences and four sources whatever the result was, which made a real run look
     rehearsed. Nothing here is allowed to be a guess. */
  function summarise(w) {
    var st = S.get();
    var rows = w.sentences || [];
    var total = 0, cited = {};
    rows.forEach(function (r) {
      total += r.dur || 0;
      (r.cls || []).forEach(function (c) {
        (st.claims[c] && st.claims[c].evidence || []).forEach(function (e) { cited[e.src] = true; });
      });
    });
    var target = st.brief && st.brief.targetSeconds;
    var bits = [rows.length + " câu", Object.keys(cited).length + " nguồn",
                V.vn(total) + " giây"];
    if (target) {
      var drift = total - target;
      bits.push(Math.abs(drift) / target <= 0.15 ? "đúng mục tiêu"
        : (drift < 0 ? "ngắn hơn" : "dài hơn") + " mục tiêu "
          + Math.round(Math.abs(drift)) + " giây");
    }
    if (w.passes) bits.push("sau " + w.passes + " lượt tự kiểm");
    var open = Object.keys(st.claims).filter(function (c) {
      var x = st.claims[c];
      return x.state === "mauthuan" || x.state === "chuaxacminh";
    }).length;
    if (open) bits.push(open + " dữ kiện còn phải quyết");
    if (w.remaining && w.remaining.length) {
      bits.push("còn " + w.remaining.length + " điểm chưa đạt");
    }
    return "Xong. " + bits.join(", ") + ".";
  }

  /* ---------- research ---------- */
  function approve() {
    var st = S.get();
    st.thread.forEach(function (m) { if (m.kind === "plan") m.retired = true; });
    S.set({ phase: "researching", busy: true });

    var msg = S.push({ role: "agent", kind: "trace", lead: "Bắt đầu tìm.", lines: [], pct: 0 });
    toBottom();

    A.research({ session: sid(), plan: st.plan, brief: st.brief }, function (line) {
      msg.lines.push(line);
      /* A real run does not announce how many steps it will take, so the bar approaches
         the end without ever claiming to have arrived. It used to divide by the fixture's
         step count, which is meaningless against any other backend. */
      msg.pct = Math.min(95, Math.round(100 - 100 / (1 + msg.lines.length / 4)));
      S.set({});
      toBottom();
    })
      .then(function (r) {
        S.set({ sources: r.sources, claims: r.claims, usage: addUsage(null, r.usage),
                cost: r.cost == null ? null : r.cost });
        /* Writing is the part that iterates, so it reports into the same trace the
           search was reporting into. Silence here read as a hang. */
        return A.write({ session: sid(), claims: r.claims, brief: st.brief,
            targetSeconds: st.brief.targetSeconds },
          function (line) {
            msg.lines.push(line);
            msg.pct = Math.min(98, Math.round(100 - 100 / (1 + msg.lines.length / 4)));
            S.set({});
            toBottom();
          });
      })
      .then(function (w) {
        msg.pct = 100;
        if (w.usage) S.set({ usage: addUsage(S.get().usage, w.usage) });
        /* The backend may have gone back for more sources while writing. */
        if (w.claims) S.set({ claims: Object.assign({}, S.get().claims, w.claims) });
        if (w.sources) S.set({ sources: Object.assign({}, S.get().sources, w.sources) });
        S.set({ busy: false, phase: "script", script: w, baseline: JSON.parse(JSON.stringify(w)), focus: 3 });
        S.push({ role: "agent", kind: "script", lead: summarise(w) });
        toBottom();
      })
      .catch(fail);
  }

  /* Stepping the queue focuses the sentence the decision is about. A counter that moves
     while the script sits still would tell the reviewer nothing. */
  function queueStep(delta) {
    var st = S.get();
    var open = Object.keys(st.claims).filter(function (cid) {
      var c = st.claims[cid];
      if (c.state === "mauthuan") return !st.conflictChoice[cid];
      return c.state === "chuaxacminh" && !S.claimDead(cid);
    });
    if (!open.length) return;
    var at = Math.max(0, Math.min((st.queueAt || 0) + delta, open.length - 1));
    /* The queue lives in the dossier pane, so stepping must not switch away from it. */
    S.set({ queueAt: at, inspect: "dossier" });
    var cid = open[at];
    var row = S.rows().filter(function (r) { return r.cls.indexOf(cid) >= 0; })[0];
    if (row) S.set({ focus: row.n });
  }

  /* The end of the cycle. Unresolved decisions do not block it: the reviewer is told
     what is still open and chooses, which is the whole point of a human gate. */
  function finish(force) {
    var st = S.get();
    if (!st.script) return;
    var open = Object.keys(st.claims).filter(function (cid) {
      var c = st.claims[cid];
      if (c.state === "mauthuan") return !st.conflictChoice[cid];
      return c.state === "chuaxacminh" && !S.claimDead(cid);
    });
    if (open.length && !force) {
      S.push({ role: "agent", kind: "text", html:
        '<div class="note g">' + V.icons.warn + "<span>Còn " + open.length +
        " dữ kiện chưa quyết. Chốt luôn thì những câu dựa vào chúng vẫn vào video, " +
        "kèm dấu cảnh báo trong hồ sơ nguồn.</span></div>" +
        '<div class="acts"><button class="btn pri" data-act="finish-force">Chốt luôn</button>' +
        '<button class="btn quiet" data-act="q-next">Xem việc cần quyết</button></div>' });
      toBottom();
      return;
    }

    S.set({ busy: true });
    var msg = S.push({ role: "agent", kind: "trace", lead: "Chốt kịch bản. Dựng video tại máy.", lines: [], pct: 0 });
    toBottom();

    A.render({ session: sid(), script: st.script, claims: st.claims, sources: st.sources,
               brief: st.brief, voice: "nu" }, function (line) {
      msg.lines.push(line);
      msg.pct = Math.min(96, Math.round(100 - 100 / (1 + msg.lines.length / 3)));
      S.set({});
      toBottom();
    })
      .then(function (r) {
        msg.pct = 100;
        S.set({ busy: false, video: r, phase: "done" });
        var m = S.get().meta;
        if (m) {
          var done = Object.assign({}, m, { state: "xong" });
          S.set({ meta: done, sessions: S.get().sessions.map(function (x) {
            return x.id === done.id ? done : x;
          }) });
        }
        S.push({ role: "agent", kind: "video", url: r.url, bytes: r.bytes,
                 cards: r.cards, seconds: r.seconds, voice: r.voice });
        toBottom();
      })
      .catch(fail);
  }

  /* ---------- review ---------- */
  function kill(cid) {
    var k = JSON.parse(JSON.stringify(S.get().killed));
    k[cid] = true;
    S.set({ killed: k, rewritten: false }, { undoable: true });
  }
  function revive(cid) {
    var k = JSON.parse(JSON.stringify(S.get().killed));
    delete k[cid];
    S.set({ killed: k, rewritten: false }, { undoable: true });
  }
  function toggleSource(id) {
    var o = JSON.parse(JSON.stringify(S.get().sourceOverride));
    o[id] = S.sourceState(id) === "dung" ? "loai" : "dung";
    S.set({ sourceOverride: o, rewritten: false }, { undoable: true });
  }

  function rewrite() {
    var st = S.get();
    st.thread.forEach(function (m) { if (m.kind === "script") m.retired = true; });
    S.set({ busy: true });

    /* st.killed IS the set of rejected claims. This used to be rebuilt from r.cl, the
       single-claim field from before a sentence could cite several, so with real data it
       was always empty and the rewrite silently did nothing at all. */
    var dead = {};
    Object.keys(st.killed).forEach(function (cid) { if (st.killed[cid]) dead[cid] = true; });

    var msg = S.push({ role: "agent", kind: "trace", lead: "Viết lại phần phụ thuộc dữ kiện bị loại.", lines: [] });
    toBottom();

    A.rewrite({
      session: sid(), sentences: st.script.sentences, killed: dead,
      claims: st.claims, brief: st.brief, sections: st.script.sections,
      targetSeconds: st.brief && st.brief.targetSeconds
    }, function (step) {
      msg.lines.push({ text: step, kind: "ok" });
      S.set({});
      toBottom();
    })
      .then(function (r) {
        S.set({
          busy: false,
          rewritten: true,
          script: { sections: st.script.sections, sentences: r.sentences }
        });
        S.push({ role: "agent", kind: "script", lead: "Đã viết lại. Các câu không liên quan giữ nguyên từng ký tự." });
        toBottom();
      })
      .catch(fail);
  }

  function undo() {
    if (!S.undo()) return;
    var st = S.get();
    /* Rewinding past a rewrite also removes what that rewrite said and printed, so the
       thread matches the script again instead of showing a stale "previous version". */
    if (!st.rewritten) {
      for (var i = 0; i < st.thread.length; i++) {
        if (st.thread[i].kind !== "script") continue;
        st.thread[i].retired = false;
        st.thread.length = i + 1;
        break;
      }
    }
    S.set({});
  }

  /* ---------- keyboard ---------- */
  function move(delta) {
    var rows = S.rows();
    if (!rows.length) return;
    var idx = rows.findIndex(function (r) { return r.n === S.get().focus; });
    idx = idx < 0 ? 0 : Math.min(rows.length - 1, Math.max(0, idx + delta));
    S.set({ focus: rows[idx].n, hover: null });
    var el = document.querySelector('.art:not(.old) [data-row="' + rows[idx].n + '"]');
    if (el) el.scrollIntoView({ block: "nearest", behavior: window.PACE ? "smooth" : "auto" });
  }

  document.addEventListener("keydown", function (e) {
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "textarea" || tag === "input") {
      if (e.key === "Escape") e.target.blur();
      return;
    }
    if (e.key === "Escape" && S.get().view === "session") { e.preventDefault(); loadList(); return; }
    if (S.get().view !== "session") return;
    if (e.key === "j") { e.preventDefault(); move(1); }
    else if (e.key === "k") { e.preventDefault(); move(-1); }
    else if (e.key === "u") { e.preventDefault(); undo(); }
    else if (e.key === "/") { e.preventDefault(); $("say").focus(); }
    else if (e.key === "x") {
      var st = S.get();
      var row = S.rows().filter(function (r) { return r.n === st.focus; })[0];
      if (!row || !row.cls.length) return;
      e.preventDefault();
      /* One claim is unambiguous. Several, and the reviewer picks which, in the inspector. */
      if (row.cls.length === 1) { row.dead ? revive(row.cls[0]) : kill(row.cls[0]); }
      else { S.set({ inspect: "evidence" }); }
    }
  });

  /* ---------- pointer ---------- */
  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-act],[data-kill],[data-revive],[data-chip],[data-jump],[data-row],[data-src],[data-tab],[data-copy],[data-open],[data-filter],#send,#back");
    if (!t) return;
    var d = t.dataset;
    if (t.id === "back") { loadList(); return; }
    if (d.open) { openSession(d.open); return; }
    if (d.filter) { S.set({ filter: d.filter }); return; }
    if (d.act === "new") { newSession(); return; }
    if (d.act === "q-next") { queueStep(1); return; }
    if (d.act === "q-prev") { queueStep(-1); return; }
    if (d.act === "finish") { finish(false); return; }
    if (d.act === "finish-force") { finish(true); return; }
    if (t.id === "send") { say($("say").value); $("say").value = ""; return; }
    if (d.chip) { say(d.chip); return; }
    if (d.tab) { S.set({ inspect: d.tab }); return; }
    if (d.act === "approve") { approve(); return; }
    if (d.act === "edit-plan") { S.push({ role: "agent", kind: "text", html: "<p>Được, anh muốn sửa chỗ nào trong kế hoạch?</p>" }); toBottom(); return; }
    if (d.act === "rewrite") { rewrite(); return; }
    if (d.act === "undo") { undo(); return; }
    if (d.copy) {
      var pre = $("out-" + d.copy);
      if (!pre) return;
      try {
        navigator.clipboard.writeText(pre.textContent).then(function () { t.textContent = "Đã chép"; },
          function () { t.textContent = "Bôi đen rồi chép tay"; });
      } catch (err) { t.textContent = "Bôi đen rồi chép tay"; }
      return;
    }
    if (d.kill) { kill(d.kill); return; }
    if (d.revive) { revive(d.revive); return; }
    if (d.src) { toggleSource(d.src); return; }
    if (d.jump || d.row) {
      var n = +(d.jump || d.row);
      S.set({ focus: S.get().focus === n && d.row ? null : n, hover: null, inspect: "evidence" });
      if (d.jump) {
        var el = document.querySelector('.art:not(.old) [data-row="' + n + '"]');
        if (el) el.scrollIntoView({ block: "center", behavior: window.PACE ? "smooth" : "auto" });
      }
    }
  });

  document.addEventListener("mouseover", function (e) {
    var r = e.target.closest(".art:not(.old) [data-row]");
    var n = r ? +r.dataset.row : null;
    if (n !== S.get().hover) S.set({ hover: n });
  });

  document.addEventListener("change", function (e) {
    var el = e.target;
    if (!el.dataset || !el.dataset.conflict) return;
    var cid = el.dataset.conflict, choice = el.dataset.choice;
    A.resolveConflict({ session: sid(), claimId: cid, choice: choice }).then(function () {
      var c = JSON.parse(JSON.stringify(S.get().conflictChoice));
      c[cid] = choice;
      S.set({ conflictChoice: c }, { undoable: true });
    }).catch(fail);
  });

  document.addEventListener("submit", function (e) {
    if (e.target.id !== "addsrc") return;
    e.preventDefault();
    var url = e.target.elements.url.value, note = e.target.elements.note.value;
    S.set({ busy: true });
    A.addSource({ session: sid(), url: url, note: note })
      .then(function (r) { S.set({ busy: false, added: r }); })
      .catch(fail);
  });

  $("say").addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); say(this.value); this.value = ""; }
  });

    /* ---------- sessions ---------- */
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
          cost: r.cost == null ? null : r.cost,
          phase: r.script ? "script" : "clarify",
          focus: null
        });
        /* A stored session shows its artifact, not a replayed conversation. */
        if (r.script) S.push({ role: "agent", kind: "script", lead: "Ban kich ban dang luu cua phien nay." });
        else S.set({ chips: [] });
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
  render();
})();
