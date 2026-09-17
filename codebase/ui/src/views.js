/* Views. Pure functions of store state to HTML strings. No data access except through Store. */

window.View = (function () {
  "use strict";

  var S = window.Store;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function vn(n) { return n.toFixed(1).replace(".", ","); }
  function money(n) { return n.toFixed(2).replace(".", ","); }

  var I = {
    ok: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M3 8.4l3.2 3.1L13 4.8"/></svg>',
    x: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8"/></svg>',
    warn: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M8 2.6l5.6 10.2H2.4z"/><path d="M8 6.6v3M8 11.5v.2"/></svg>',
    skip: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="8" cy="8" r="5.2"/><path d="M4.4 4.4l7.2 7.2"/></svg>',
    mark: '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="var(--on-navy)" stroke-width="1.8" aria-hidden="true"><circle cx="7.2" cy="7.2" r="4.4"/><path d="M10.6 10.6L14 14"/></svg>'
  };

  var GRADE = {
    verified: { label: "hai nguồn độc lập", cls: "k" },
    single: { label: "một nguồn", cls: "n" },
    unverified: { label: "chưa xác minh", cls: "g" },
    conflict: { label: "nguồn mâu thuẫn", cls: "g" },
    dead: { label: "đã loại", cls: "r" },
    none: { label: "không cần nguồn", cls: "o" }
  };

  /* Schema stores the code; the reader sees the word. Export keeps the code. */
  var KIEU = { ke: "kể", giang: "giảng", nhe: "thân mật", hoi: "hỏi", nhan: "chốt" };

  var BEATS = ["Đề bài", "Làm rõ", "Kế hoạch", "Tìm nguồn", "Kịch bản"];
  function beatIndex(st) {
    return { clarify: 1, planned: 2, researching: 3, script: 4 }[st.phase] || 0;
  }

  /* ---------- session list ---------- */
  function sessionList(st) {
    var rows = S.visibleSessions();
    var ST = window.FIXTURE.sessionStates;

    var h = '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:var(--s3);flex-wrap:wrap">' +
      '<h1 style="font:var(--t-display)">Kịch bản đang làm</h1>' +
      '<button class="btn pri" data-act="new">Kịch bản mới</button></div>' +
      '<p class="sub" style="margin:0">Mỗi người một kịch bản. Bấm vào một dòng để mở, hoặc dùng mũi tên lùi của trình duyệt để quay lại đây.</p>';

    if (!rows.length) {
      h += '<div class="panel pad" style="border:1px solid var(--line);border-radius:var(--r-panel);background:var(--surface);padding:var(--s5)">' +
        '<p style="margin:0">Chưa có kịch bản nào ở nhóm này.</p>' +
        '<p class="sub" style="margin:var(--s2) 0 0">Bấm <b>Kịch bản mới</b> để bắt đầu từ một câu mô tả.</p></div>';
      return h;
    }

    h += '<div style="border:1px solid var(--line);border-radius:var(--r-panel);background:var(--surface);overflow:hidden">';
    rows.forEach(function (x, i) {
      var st2 = ST[x.state] || { label: x.state, tone: "o" };
      var over = x.seconds > x.target + 0.05;
      h += '<div class="s" data-open="' + esc(x.id) + '" style="grid-template-columns:minmax(0,1fr) 130px 120px;' +
        (i ? "" : "border-top:0;") + '">' +
        '<span style="display:flex;flex-direction:column;gap:var(--s1);min-width:0">' +
        '<span style="font-weight:500">' + esc(x.title) + "</span>" +
        '<span class="sub num">' + esc(x.owner) + (x.lesson ? " · " + esc(x.lesson) : "") + " · " + esc(x.updated) + "</span>" +
        "</span>" +
        '<span style="display:flex;flex-direction:column;gap:var(--s1)">' +
        '<span class="tag ' + st2.tone + '">' + esc(st2.label) + "</span>" +
        (x.open ? '<span class="tag g">' + x.open + " cần quyết</span>" : "") + "</span>" +
        '<span class="sub num" style="text-align:right">' +
        (x.sentences ? x.sentences + " câu<br>" : "chưa có câu<br>") +
        (x.seconds ? '<span style="color:' + (over ? "var(--caution)" : "var(--ok)") + '">' + vn(x.seconds) + " / " + x.target + " giây</span>" : "") +
        "</span></div>";
    });
    return h + "</div>";
  }

  function listRail(st) {
    var counts = {
      all: st.sessions.length,
      mine: st.sessions.filter(function (x) { return x.owner === "Việt"; }).length,
      duyet: st.sessions.filter(function (x) { return x.state === "duyet"; }).length
    };
    var opts = [["all", "Tất cả"], ["mine", "Của tôi"], ["duyet", "Chờ duyệt"]];
    var h = '<div><h2>Lọc</h2><ol>';
    opts.forEach(function (o) {
      h += '<li><button data-filter="' + o[0] + '"' + (st.filter === o[0] ? ' aria-current="true"' : "") + ">" +
        '<span class="t">' + esc(o[1]) + '</span><span class="k num" style="margin-left:auto">' + counts[o[0]] + "</span></button></li>";
    });
    return h + "</ol></div>";
  }

  /* ---------- left rail ---------- */
  function rail(st) {
    if (st.view === "list") return listRail(st);
    var at = beatIndex(st);
    var h = '<div><h2>Tiến trình</h2><ol>';
    BEATS.forEach(function (b, i) {
      h += '<li><span class="beat ' + (i <= at ? "" : "off") + '"><span class="k">' +
        (i <= at ? I.ok : i + 1) + "</span>" + esc(b) + "</span></li>";
    });
    h += "</ol></div>";

    if (st.script) {
      var rows = S.rows();
      h += '<div><h2>Cấu trúc kịch bản</h2>';
      st.script.sections.forEach(function (sec) {
        var mine = rows.filter(function (r) { return r.sec === sec.no; });
        if (!mine.length) return;
        h += '<div class="sec">' + esc(sec.name) + "</div><ol>";
        mine.forEach(function (r) {
          h += '<li' + (r.dead ? ' class="gone"' : "") + '><button data-jump="' + r.n + '"' +
            (st.focus === r.n ? ' aria-current="true"' : "") + '>' +
            '<span class="k num">Câu ' + (r.shown || r.n) + '</span>' +
            '<span class="t">' + esc(r.loi.slice(0, 24)) + "…</span></button></li>";
        });
        h += "</ol>";
      });
      var cut = S.pendingCuts();
      if (cut) h += '<div class="sec">' + cut + " câu đang bị loại</div>";
      h += "</div>";
    }

    h += '<div class="foot"><span>Chi phí lượt này</span><b class="num">' +
      (st.cost ? money(st.cost) + " đô" : st.cost === null ? "chưa đo" : "chưa chạy") + "</b>" +
      "<span>" + S.liveSources() + " nguồn đang dùng</span></div>";
    return h;
  }

  /* ---------- thread ---------- */
  function agent(body) {
    return '<div class="msg agent"><div class="who"><span class="av">' + I.mark +
      '</span><span class="nm">ScriptScout</span></div><div class="body">' + body + "</div></div>";
  }
  function user(body) {
    return '<div class="msg user"><div class="body">' + body + "</div></div>";
  }

  function planBlock(st, live) {
    var h = '<div class="plan"><h3>Kế hoạch trước khi đi tìm tài liệu</h3>';
    st.plan.prose.forEach(function (p) { h += "<p>" + esc(p) + "</p>"; });
    h += '<div class="lbl" style="margin-top:var(--s3)">Tiêu chí chấm nguồn, công bố trước</div><div class="crit">';
    st.criteria.forEach(function (c) {
      h += "<div><b>" + esc(c.label) + '</b><span class="num">hệ số ' + c.weight + "</span></div>";
    });
    h += "</div>";
    h += '<p class="sub" style="margin-top:var(--s3)">Chưa có lời gọi tìm kiếm nào được chạy. Anh duyệt thì tôi mới bắt đầu.</p>';
    if (live) {
      h += '<div class="acts"><button class="btn pri" data-act="approve">Duyệt kế hoạch, bắt đầu tìm</button>' +
        '<button class="btn quiet" data-act="edit-plan">Sửa kế hoạch</button></div>';
    }
    return h + "</div>";
  }

  function traceBlock(lines, pct) {
    var h = '<div class="trace">';
    lines.forEach(function (l) {
      var kind = l.kind || "ok";
      var ic = kind === "ok" ? I.ok : kind === "stop" ? I.x : kind === "skip" ? I.skip : I.warn;
      var col = kind === "ok" ? "var(--ok)" : kind === "stop" ? "var(--stop)" : kind === "skip" ? "var(--muted)" : "var(--caution)";
      h += '<div class="tr ' + esc(kind) + '"><span style="color:' + col + '">' + ic + "</span>" +
        '<span class="t num">' + (l.t != null ? vn(l.t) + " giây" : "") + "</span>" +
        "<span>" + esc(l.text) + "</span></div>";
    });
    h += "</div>";
    if (pct != null) h += '<div class="pbar"><i style="width:' + pct + '%"></i></div>';
    return h;
  }

  function covKey() {
    return '<div class="covkey">' +
      '<span><i style="background:var(--ok)"></i>hai nguồn</span>' +
      '<span><i style="background:var(--navy)"></i>một nguồn</span>' +
      '<span><i style="background:var(--caution-mark)"></i>chưa xác minh</span>' +
      '<span><i style="background:var(--stop)"></i>đã loại</span>' +
      '<span><i style="background:var(--line-strong)"></i>không cần nguồn</span></div>';
  }

  function scriptBlock(st, old) {
    var rows = S.rows();
    var t = rows.reduce(function (a, r) { return a + r.dur; }, 0);
    var target = (st.brief && st.brief.targetSeconds) || 30;
    var over = t > target + 0.05;
    var cut = S.pendingCuts();

    var h = '<div class="art' + (old ? " old" : "") + '">' +
      '<div class="arth"><span class="ttl">Kịch bản, ba mươi giây mở đầu</span>' +
      '<span class="dur num ' + (over ? "over" : "ok") + '">' + vn(t) + " giây / mục tiêu " + target + " giây</span></div>";

    if (!old) {
      h += '<div class="cov" role="group" aria-label="Mức bằng chứng từng câu">';
      rows.forEach(function (r) {
        h += '<button data-jump="' + r.n + '" data-g="' + r.grade + '"' +
          (st.focus === r.n ? ' aria-current="true"' : "") +
          ' title="Câu ' + (r.shown || r.n) + ": " + esc(GRADE[r.grade].label) + '">' +
          '<span class="sr">Câu ' + (r.shown || r.n) + ", " + esc(GRADE[r.grade].label) + "</span></button>";
      });
      h += "</div>" + covKey();
    }

    rows.forEach(function (r) {
      var g = GRADE[r.grade];
      var chip = !r.cls.length
        ? '<span class="tag o">' + esc(g.label) + "</span>"
        : r.cls.map(function (cid) {
            var cg = S.gradeOne(cid);
            return '<span class="tag ' + GRADE[cg].cls + '">' +
              (cg === "unverified" || cg === "conflict" ? I.warn + " " : "") + esc(cid) + "</span>";
          }).join(" ");
      var mark = r.state === "keep" ? '<span class="tag o">giữ nguyên</span>'
        : r.state === "redo" ? '<span class="tag n">viết lại</span>' : "";
      h += '<div class="s' + (r.dead ? " cut" : "") + (st.focus === r.n ? " on" : "") + '" data-row="' + r.n + '">' +
        '<span class="k"><span class="num">Câu ' + (r.shown || r.n) + "</span>" +
        '<span class="tag o">' + esc(KIEU[r.kieu] || r.kieu) + "</span>" + mark + "</span>" +
        '<span><span class="loi">' + esc(r.loi) + "</span> " + chip +
        (r.was ? '<span class="was">Trước: <s>' + esc(r.was) + "</s></span>" : "") + "</span>" +
        '<span class="right">' +
        (r.cls.length === 1 && !old
          ? '<button class="cut-act" data-' + (r.dead ? "revive" : "kill") + '="' + esc(r.cls[0]) + '">' +
            (r.dead ? "Nhận lại" : "Loại dữ kiện") + "</button>"
          : r.cls.length > 1 && !old
            ? '<button class="cut-act" data-row="' + r.n + '">Soi ' + r.cls.length + " dữ kiện</button>"
            : "") +
        '<span class="dur num">' + vn(r.dur) + " giây</span></span></div>";
    });

    if (old) {
      h += '<div class="artf"><span class="sub">Bản trước khi viết lại</span></div>';
    } else if (cut) {
      h += '<div class="artf"><span class="sub num">' + cut + " dữ kiện bị loại, " + cut +
        " câu sẽ viết lại, " + (rows.length - cut) + " câu giữ nguyên</span>" +
        '<span class="acts" style="margin:0"><button class="btn quiet" data-act="undo">Hoàn tác</button>' +
        '<button class="btn pri" data-act="rewrite">Viết lại kịch bản</button></span></div>';
    } else if (st.rewritten) {
      h += '<div class="artf"><span class="sub num">' + (rows.length - 1) +
        ' câu giữ nguyên từng ký tự, 1 câu viết lại</span>' +
        '<button class="btn quiet" data-act="undo">Hoàn tác</button></div>';
    } else {
      h += '<div class="artf"><span class="sub">Trỏ vào một câu để soi nguồn. ' +
        '<kbd>j</kbd> <kbd>k</kbd> chuyển câu, <kbd>x</kbd> loại dữ kiện, <kbd>u</kbd> hoàn tác.</span></div>';
    }
    return h + "</div>";
  }

  function thread(st) {
    if (!st.thread.length) {
      return '<div class="msg agent"><div class="who"><span class="av">' + I.mark +
        '</span><span class="nm">ScriptScout</span></div><div class="body">' +
        "<p>Mô tả sơ chủ đề và người học. Chưa cần chuẩn, chưa cần đủ.</p>" +
        '<p class="sub">Tôi sẽ hỏi lại vài câu, rồi trình kế hoạch trước khi đi tìm tài liệu.</p>' +
        "</div></div>";
    }
    return st.thread.map(function (m) {
      var body;
      if (m.kind === "text") body = m.html;
      else if (m.kind === "plan") body = planBlock(st, !m.retired);
      else if (m.kind === "trace") body = esc(m.lead) + traceBlock(m.lines || [], m.pct);
      else if (m.kind === "script") body = scriptBlock(st, !!m.retired);
      else body = "";
      if (m.kind === "plan" || m.kind === "trace" || m.kind === "script") {
        return agent(m.lead && m.kind !== "trace" ? "<p>" + esc(m.lead) + "</p>" + body : body);
      }
      return m.role === "user" ? user(body) : agent(body);
    }).join("");
  }

  /* ---------- inspector ---------- */
  function briefCard(st) {
    if (!st.brief) return "";
    return '<div><div class="lbl">Đề bài</div><dl class="dl" style="margin-top:var(--s2)">' +
      "<dt>Chủ đề</dt><dd>" + esc(st.brief.topic) + "</dd>" +
      "<dt>Mục tiêu</dt><dd>" + esc(st.brief.goal) + "</dd>" +
      "<dt>Người học</dt><dd>" + esc(st.brief.learners) + "</dd>" +
      "<dt>Thời lượng</dt><dd>" + esc(st.brief.duration) + "</dd></dl></div>";
  }

  function meter(trust) {
    var on = trust === "cao" ? 3 : trust === "trungbinh" ? 2 : 1;
    var cls = trust === "cao" ? "" : trust === "trungbinh" ? "mid" : "low";
    var b = "";
    for (var i = 0; i < 3; i++) b += "<i" + (i < on ? ' class="on"' : "") + "></i>";
    return '<span class="meter ' + cls + '">' + b + "</span>";
  }
  var TRUST = { cao: "Cao", trungbinh: "Trung bình", thap: "Thấp", chan: "Đã chặn", khongdoc: "Không đọc được", dangthamdinh: "Đang thẩm định" };

  function evidencePane(st) {
    var n = st.hover || st.focus;
    var rows = S.rows();
    var row = null;
    rows.forEach(function (r) { if (r.n === n) row = r; });
    if (!row) {
      return briefCard(st) + '<div class="sub">' +
        (st.script ? "Trỏ chuột vào một câu trong kịch bản để xem nguồn chống lưng cho câu đó. Bấm để ghim."
          : "Agent dựng kế hoạch trước, và chỉ đi tìm tài liệu sau khi anh duyệt.") + "</div>";
    }
    if (!row.cls.length) {
      return briefCard(st) +
        '<div><div class="lbl">Câu ' + (row.shown || row.n) + '</div>' +
        '<p style="margin-top:var(--s2)">Câu này chỉ dẫn dắt, không chứa thông tin, con số hay ví dụ thực tế.</p>' +
        '<p><span class="tag o">không cần nguồn</span></p>' +
        '<p class="sub">Theo mẫu kịch bản, câu chuyển ý thì không gắn mã nguồn. Đây là câu trả lời đúng khi giám khảo chỉ vào nó.</p></div>';
    }

    var h = briefCard(st);
    if (row.cls.length > 1) {
      h += '<div class="note n">' + I.warn + "<span>Câu này dựa trên " + row.cls.length +
        " dữ kiện. Loại bất kỳ dữ kiện nào cũng buộc phải viết lại câu.</span></div>";
    }

    row.cls.forEach(function (cid) {
      var c = st.claims[cid];
      if (!c) return;
      var cg = S.gradeOne(cid);
      var ind = S.independence(cid);
      var badge = cg === "dead" ? '<span class="tag r">đã loại</span>'
        : cg === "conflict" ? '<span class="tag g">' + I.warn + " nguồn mâu thuẫn</span>"
          : cg === "unverified" ? '<span class="tag g">' + I.warn + " chưa xác minh</span>"
            : '<span class="tag k">' + I.ok + " " + ind + (ind > 1 ? " nguồn độc lập" : " nguồn") + "</span>";

      h += '<div style="display:flex;flex-direction:column;gap:var(--s3);border-top:1px solid var(--line);padding-top:var(--s3)">' +
        '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:var(--s2)">' +
        '<span class="lbl num">' + esc(cid) + " · " + esc(c.kind) + "</span>" + badge + "</div>" +
        '<p style="font-weight:500;margin:0">' + esc(c.text) + "</p>";

      if (c.unverified) h += '<div class="note g">' + I.warn + "<span>" + esc(c.unverified) + "</span></div>";

      if (c.conflict) {
        var chosen = st.conflictChoice[cid];
        h += '<div class="note g">' + I.warn + "<span>" + esc(c.conflict.note) + "</span></div>";
        c.conflict.options.forEach(function (o) {
          h += '<label class="radio"><input type="radio" name="conf-' + esc(cid) + '" data-conflict="' + esc(cid) +
            '" data-choice="' + esc(o.id) + '"' + (chosen === o.id ? " checked" : "") + "><span>" + esc(o.label) + "</span></label>";
        });
        if (!chosen) h += '<p class="sub" style="margin:0">Chưa chọn thì kịch bản nói vòng: ' + esc(c.conflict.hedge) + "</p>";
      }

      h += '<div class="lbl">Đoạn trích làm bằng chứng</div>';
      c.evidence.forEach(function (e) {
        var src = st.sources[e.src];
        if (!src) return;
        var usable = S.sourceUsable(e.src);
        h += '<div style="display:flex;flex-direction:column;gap:var(--s2)">' +
          '<div class="quote' + (usable ? "" : " mute") + '">' +
          esc(e.quote).replace(esc(e.hit), "<mark>" + esc(e.hit) + "</mark>") + "</div>" +
          '<dl class="dl"><dt>Nguồn</dt><dd class="num">' + esc(e.src) + " · " + esc(src.title) + "</dd>" +
          "<dt>Ai viết</dt><dd>" + esc(src.org) + "</dd>" +
          '<dt>Đăng ngày</dt><dd class="num">' + esc(src.published) + "</dd>" +
          "<dt>Loại</dt><dd>" + esc(src.kind) + (src.lang === "en" ? ", tiếng Anh" : "") + "</dd>" +
          '<dt>Vị trí</dt><dd class="num">' + esc(e.at) + "</dd>" +
          "<dt>Tin cậy</dt><dd>" + esc(TRUST[src.trust] || src.trust) + " " + meter(src.trust) + "</dd></dl>" +
          '<p class="sub" style="margin:0">' + esc(src.why) + "</p>" +
          (src.warn ? '<div class="note g">' + I.warn + "<span>" + esc(src.warn) + "</span></div>" : "") +
          (usable ? "" : '<div class="note r">' + I.x + "<span>Nguồn này không còn được dùng.</span></div>") +
          "</div>";
      });

      h += S.claimDead(cid)
        ? '<button class="btn quiet" data-revive="' + esc(cid) + '" style="align-self:flex-start">Nhận lại dữ kiện này</button>'
        : '<button class="btn quiet stop" data-kill="' + esc(cid) + '" style="align-self:flex-start">' + I.x + " Loại dữ kiện này</button>";
      h += "</div>";
    });

    return h;
  }

  /* Claims the agent refuses to state on its own. Surfacing these is the whole point of a
     review screen: a conflict the reviewer never sees is a conflict the script hides. */
  function decisionQueue(st) {
    var open = Object.keys(st.claims).filter(function (cid) {
      var c = st.claims[cid];
      if (c.state === "mauthuan") return !st.conflictChoice[cid];
      return c.state === "chuaxacminh" && !S.claimDead(cid);
    });
    if (!open.length) return "";

    var h = '<div><div class="lbl">Cần anh quyết (' + open.length + ")</div>";
    open.forEach(function (cid) {
      var c = st.claims[cid];
      h += '<div class="src"><div class="row"><span class="t">' + esc(c.text) + "</span></div>";
      if (c.state === "mauthuan") {
        h += '<div class="note g">' + I.warn + "<span>" + esc(c.conflict.note) + "</span></div>";
        c.evidence.forEach(function (e) {
          h += '<div class="row"><span class="sub num">' + esc(e.src) + " · " + esc(st.sources[e.src].published) +
            '</span><span style="font-weight:600">' + esc(e.value || "") + "</span></div>";
        });
        c.conflict.options.forEach(function (o) {
          h += '<label class="radio"><input type="radio" name="q-' + esc(cid) + '" data-conflict="' + esc(cid) +
            '" data-choice="' + esc(o.id) + '"><span>' + esc(o.label) + "</span></label>";
        });
        h += '<p class="sub" style="margin:0">Chưa chọn thì kịch bản nói vòng: ' + esc(c.conflict.hedge) + "</p>";
      } else {
        h += '<div class="note g">' + I.warn + "<span>" + esc(c.unverified) + "</span></div>" +
          '<div class="row"><span class="sub num">' + S.independence(cid) + " nguồn độc lập</span>" +
          '<button class="btn quiet stop" data-kill="' + esc(cid) + '" style="padding:2px 6px">Loại dữ kiện</button></div>';
      }
      h += "</div>";
    });
    return h + '</div><div style="border-top:1px solid var(--line)"></div>';
  }

  function exportPane(st) {
    if (!st.script) return '<div class="sub">Chưa có kịch bản để xuất.</div>';
    var a = JSON.stringify(window.Exporter.script(st), null, 2);
    var b = JSON.stringify(window.Exporter.sources(st), null, 2);
    function block(name, body, key) {
      return '<div style="display:flex;flex-direction:column;gap:var(--s2)">' +
        '<div class="row" style="display:flex;justify-content:space-between;align-items:baseline">' +
        '<span class="lbl num">' + esc(name) + '</span>' +
        '<button class="btn quiet" data-copy="' + key + '" style="padding:2px 6px">Chép</button></div>' +
        '<pre id="out-' + key + '" style="background:var(--navy-tint);border-radius:var(--r-ctl);padding:var(--s3);overflow-x:auto;font:var(--t-meta);margin:0;max-height:260px">' +
        esc(body) + "</pre></div>";
    }
    return '<p class="sub" style="margin:0">Đúng hai schema ban tổ chức cấp, nên đội C4 và C5 dùng lại được ngay.</p>' +
      block("kich-ban.json", a, "script") + block("ho-so-nguon.json", b, "sources") +
      '<div class="note n">' + I.warn + '<span>Trình duyệt trong khung nhúng chặn tải file, nên ở đây là chép tay. ' +
      'Chạy bản chính ở máy thì xuất ra file bình thường.</span></div>';
  }

  function dossierPane(st) {
    var ids = Object.keys(st.sources);
    if (st.added) ids.push(st.added.id);
    var h = decisionQueue(st);

    ids.forEach(function (id) {
      var s = id === (st.added && st.added.id) ? st.added.source : st.sources[id];
      var state = S.sourceState(id);
      var out = state !== "dung" && state !== "thamdinh";
      var deps = S.dependants(id);
      var pill = state === "dung" ? '<span class="tag k">đang dùng</span>'
        : state === "thamdinh" ? '<span class="tag n">đang thẩm định</span>'
          : state === "chan" ? '<span class="tag r">' + I.x + " đã chặn</span>"
            : state === "khongdoc" ? '<span class="tag o">không đọc được</span>'
              : '<span class="tag r">bị loại</span>';

      h += '<div class="src' + (out ? " out" : "") + '">' +
        '<div class="row"><span class="t">' + esc(s.title) + "</span>" + pill + "</div>" +
        '<span class="sub num">' + esc(id) + " · " + esc(s.org) + " · " + esc(s.url) + "</span>" +
        '<div class="row"><span class="sub num">Đăng ' + esc(s.published) + " · " + esc(s.kind) +
        (s.lang === "en" ? " · tiếng Anh" : "") + "</span>" + meter(s.trust) + "</div>" +
        '<p class="sub" style="margin:0">' + esc(out && s.removedWhy ? s.removedWhy : s.why) + "</p>" +
        (s.warn && !out ? '<div class="note g">' + I.warn + "<span>" + esc(s.warn) + "</span></div>" : "") +
        (s.injected ? '<div class="note r">' + I.x + "<span>Chữ ẩn trên trang: “" + esc(s.injected) + "”. Đã bỏ qua.</span></div>" : "") +
        '<div class="row"><span class="deps num">' + (deps ? deps + " câu phụ thuộc" : "chưa câu nào dùng") + "</span>" +
        (state === "chan" || state === "khongdoc" ? "" :
          '<button class="btn quiet' + (out ? "" : " stop") + '" data-src="' + esc(id) + '" style="padding:2px 6px">' +
          (out ? "Dùng lại" : "Loại nguồn") + "</button>") +
        "</div></div>";
    });

    h += '<form id="addsrc" style="display:flex;flex-direction:column;gap:var(--s2);border-top:1px solid var(--line);padding-top:var(--s4)">' +
      '<div class="lbl">Thêm nguồn của anh</div>' +
      '<label class="field" for="srcurl"><span class="sub">Đường dẫn</span>' +
      '<input type="url" id="srcurl" name="url" value="https://arxiv.example.test/1706.03762" required></label>' +
      '<label class="field" for="srcnote"><span class="sub">Ghi chú cho agent</span>' +
      '<textarea class="f" id="srcnote" name="note" placeholder="Chèn vào chỗ nói về kiến trúc nếu phù hợp."></textarea></label>' +
      '<button class="btn pri" type="submit" style="align-self:flex-start">Thêm vào hồ sơ</button>' +
      '<p class="sub" style="margin:0">Nguồn của người duyệt vẫn đi qua bước soát trích dẫn.</p></form>';
    return h;
  }

  function inspector(st) {
    var live = S.liveSources();
    var open = Object.keys(st.claims).filter(function (cid) {
      var c = st.claims[cid];
      if (c.state === "mauthuan") return !st.conflictChoice[cid];
      return c.state === "chuaxacminh" && !S.claimDead(cid);
    }).length;
    var pane = st.inspect === "dossier" ? dossierPane(st)
      : st.inspect === "export" ? exportPane(st) : evidencePane(st);
    return '<div class="tabs" role="tablist">' +
      '<button role="tab" data-tab="evidence" aria-selected="' + (st.inspect === "evidence") + '">Bằng chứng</button>' +
      '<button role="tab" data-tab="dossier" aria-selected="' + (st.inspect === "dossier") + '"' +
      (open ? ' title="' + open + ' việc cần anh quyết"' : "") + ">Hồ sơ nguồn" +
      '<span class="count num' + (open ? " due" : "") + '">' + (open || live) + "</span></button>" +
      '<button role="tab" data-tab="export" aria-selected="' + (st.inspect === "export") + '">Xuất</button></div>' +
      '<div class="ipad">' + pane + "</div>";
  }

  function chips(st) {
    if (st.phase !== "clarify" || st.busy || !st.chips || !st.chips.length) return "";
    return st.chips.map(function (c) {
      return '<button class="chip" data-chip="' + esc(c) + '">' + esc(c) + "</button>";
    }).join("");
  }

  return { rail: rail, thread: thread, inspector: inspector, chips: chips, sessionList: sessionList,
    esc: esc, vn: vn, money: money, icons: I };
})();
