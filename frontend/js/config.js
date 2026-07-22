window.APP_CONFIG = Object.freeze({
  apiBaseUrl: "http://192.168.1.131:8000/api",
});

(function () {
  var origin = new URL(window.APP_CONFIG.apiBaseUrl).origin;
  var link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = origin + "/static/fonts/material-symbols/material-symbols.css";
  document.head.appendChild(link);
})();
