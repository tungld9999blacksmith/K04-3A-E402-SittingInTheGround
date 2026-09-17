/* Builds the two files the brief asks for, from live state.
   Shapes follow the organisers' schemas so a C4 or C5 team can consume them unchanged:
   hackathon-kich-ban/1 and hackathon-ho-so-nguon/1. */

window.Exporter = (function () {
  "use strict";
  var S = window.Store;

  function script(st) {
    var rows = S.rows().filter(function (r) { return !r.dead; });
    return {
      schema: "hackathon-kich-ban/1",
      id: "d1-mo-dau",
      tieuDe: st.brief.topic,
      mucTieu: st.brief.goal,
      phan: st.script.sections.map(function (s) { return { so: s.no, ten: s.name }; }),
      cau: rows.map(function (r) {
        var o = { n: r.shown || r.n, phan: r.sec, kieu: r.kieu, loi: r.loi };
        if (r.chu) o.chuTrenManHinh = r.chu;
        if (r.hinh) o.yDoHinh = r.hinh;
        if (r.cls && r.cls.length) o.nguon = r.cls.slice();
        return o;
      })
    };
  }

  function sources(st) {
    var ids = Object.keys(st.sources);
    if (st.added) ids.push(st.added.id);

    return {
      schema: "hackathon-ho-so-nguon/1",
      chuDe: st.brief.topic,
      ngayChay: new Date().toISOString(),
      nguon: ids.map(function (id) {
        var s = id === (st.added && st.added.id) ? st.added.source : st.sources[id];
        var state = S.sourceState(id);
        var o = {
          id: id,
          url: "https://" + s.url,
          tieuDe: s.title,
          toChuc: s.org,
          ngayDang: s.published,
          ngayLayVe: s.fetched || null,
          loai: s.kind,
          ngonNgu: s.lang,
          doTinCay: s.trust,
          lyDoTinCay: s.why,
          trangThai: state
        };
        if (state !== "dung" && s.removedWhy) o.lyDoLoai = s.removedWhy;
        if (s.warn) o.canhBao = [s.warn];
        if (s.injected) o.lenhAnDaChan = s.injected;
        return o;
      }),
      thongTin: Object.keys(st.claims).map(function (cid) {
        var c = st.claims[cid];
        var o = {
          id: cid,
          noiDung: c.text,
          loai: c.kind,
          bangChung: c.evidence.map(function (e) {
            return { nguonId: e.src, doanTrich: e.quote, viTri: e.at };
          }),
          soNguonXacNhan: S.independence(cid),
          trangThai: S.claimDead(cid) ? "nguoiduyetloai" : c.state
        };
        if (c.unverified) o.moTaMauThuan = c.unverified;
        if (c.conflict) {
          o.moTaMauThuan = c.conflict.note;
          o.nguoiDuyetChon = st.conflictChoice[cid] || null;
        }
        return o;
      })
    };
  }

  return { script: script, sources: sources };
})();
