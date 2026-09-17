/* Picks the adapter. Nothing else in the app knows which one it got.

   Served from localhost, it looks for the local backend on its default port without
   being asked. Requiring a ?api= query string meant the plain URL quietly ran on mock
   data and looked broken to anyone who had a server running. If nothing answers there,
   every call falls back to the mock per call, so this costs one refused connection. */

window.LOCAL_API = "http://127.0.0.1:8787";

window.Adapter = (function () {
  "use strict";

  var api = null;
  try {
    api = new URLSearchParams(window.location.search).get("api");
    if (!api && /^(localhost|127\.0\.0\.1|\[::1\])$/.test(window.location.hostname)) {
      api = window.LOCAL_API;
    }
  } catch (err) {
    api = null;                       /* file:// in an old engine, or a blocked location */
  }

  if (api && window.HttpAdapter) {
    var http = window.HttpAdapter(api);
    var wrapped = { name: http.name, base: http.base };

    /* Two ways a backend lets you down, and neither should brick a demo:
       it has not implemented a method yet, or it is not answering at all. Either way the
       mock takes over for that call and the page says so instead of showing a dead screen. */
    Object.keys(window.MockAdapter).forEach(function (k) {
      if (typeof window.MockAdapter[k] !== "function") return;
      if (typeof http[k] !== "function") { wrapped[k] = window.MockAdapter[k]; return; }
      wrapped[k] = function (req, onEvent) {
        return http[k](req, onEvent).catch(function (err) {
          window.API_DOWN = err && err.message || String(err);
          /* If the mock cannot stand in either, the reviewer needs the SERVER's reason,
             not the mock's. Reporting "cần máy chủ thật" when the server answered and
             failed sent me hunting the wrong bug. */
          return Promise.resolve()
            .then(function () { return window.MockAdapter[k](req, onEvent); })
            .catch(function () { throw err; });
        });
      };
    });
    return wrapped;
  }

  return window.MockAdapter;
})();
