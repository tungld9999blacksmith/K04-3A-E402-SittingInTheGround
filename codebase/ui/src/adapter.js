/* Picks the adapter. Mock unless the page was opened with ?api=<base-url>.
   Nothing else in the app knows which one it got. */

window.Adapter = (function () {
  "use strict";

  var api = null;
  try {
    api = new URLSearchParams(window.location.search).get("api");
  } catch (err) {
    api = null;                       /* file:// in an old engine, or a blocked location */
  }

  if (api && window.HttpAdapter) {
    var http = window.HttpAdapter(api);
    var wrapped = { name: http.name };

    /* Two ways a backend lets you down, and neither should brick a demo:
       it has not implemented a method yet, or it is not answering at all. Either way the
       mock takes over for that call and the page says so instead of showing a dead screen. */
    Object.keys(window.MockAdapter).forEach(function (k) {
      if (typeof window.MockAdapter[k] !== "function") return;
      if (typeof http[k] !== "function") { wrapped[k] = window.MockAdapter[k]; return; }
      wrapped[k] = function (req, onEvent) {
        return http[k](req, onEvent).catch(function (err) {
          window.API_DOWN = err && err.message || String(err);
          return window.MockAdapter[k](req, onEvent);
        });
      };
    });
    return wrapped;
  }

  return window.MockAdapter;
})();
