// Simple HTTPS reverse proxy for MCP SSE using mkcert certs
const fs = require("fs");
const https = require("https");
const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

// Adjust TARGET to the upstream HTTP server you want to proxy (e.g., browser agent on 8100)
const TARGET = process.env.PROXY_TARGET || "http://localhost:8100";
const PORT = process.env.PROXY_PORT || 8002;
const CERT_PATH = process.env.PROXY_CERT || "cert.pem";
const KEY_PATH = process.env.PROXY_KEY || "key.pem";
const path = require("path");
const LOG_PATH = path.join(__dirname, ".cursor", "debug.log");
const LOG_DIR = path.dirname(LOG_PATH);

function logEvt(payload) {
  const body = {
    sessionId: payload.sessionId || "debug-session",
    runId: payload.runId || "pre-fix",
    hypothesisId: payload.hypothesisId || "H0",
    location: payload.location,
    message: payload.message,
    data: payload.data || {},
    timestamp: Date.now(),
  };
  // #region agent log
  fetch("http://127.0.0.1:7242/ingest/864c6a35-2886-4c22-b0fd-7f20da149156", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).catch(() => {});
  try {
    require("fs").mkdirSync(LOG_DIR, { recursive: true });
    require("fs").appendFileSync(LOG_PATH, JSON.stringify(body) + "\n");
  } catch (e) {
    fetch("http://127.0.0.1:7242/ingest/864c6a35-2886-4c22-b0fd-7f20da149156", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId: "debug-session", runId: body.runId, hypothesisId: "H-log", location: "https-proxy.js:log-write", message: "log-write-failed", data: { error: e.message }, timestamp: Date.now() }) }).catch(() => {});
  }
  // #endregion
}

// #region agent log
logEvt({
  hypothesisId: "H1",
  location: "https-proxy.js:config",
  message: "proxy-config",
  data: { target: TARGET, port: PORT, cert: CERT_PATH, key: KEY_PATH },
});
// #endregion

const app = express();

// Proxy everything to the upstream
app.use(
  "/",
  createProxyMiddleware({
    target: TARGET,
    changeOrigin: true,
    ws: true,
    secure: false, // upstream is HTTP; TLS terminates here
  })
);

const options = {
  key: fs.readFileSync(KEY_PATH),
  cert: fs.readFileSync(CERT_PATH),
};

const server = https.createServer(options, app);

process.on("uncaughtException", (err) => {
  // #region agent log
  logEvt({ hypothesisId: "H3", location: "https-proxy.js:uncaught", message: "uncaught-exception", data: { code: err.code, message: err.message, stack: err.stack } });
  // #endregion
  throw err;
});

process.on("unhandledRejection", (reason) => {
  // #region agent log
  logEvt({ hypothesisId: "H3", location: "https-proxy.js:unhandledRejection", message: "unhandled-rejection", data: { reason: String(reason) } });
  // #endregion
});

server.on("error", (err) => {
  // #region agent log
  logEvt({
    hypothesisId: "H2",
    location: "https-proxy.js:error",
    message: "server-error",
    data: { code: err.code, message: err.message, stack: err.stack },
  });
  // #endregion
  throw err;
});

server.listen(PORT, () => {
  console.log(`HTTPS proxy on https://localhost:${PORT} -> ${TARGET}`);
  console.log(`Using cert: ${CERT_PATH}, key: ${KEY_PATH}`);
  // #region agent log
  logEvt({
    hypothesisId: "H1",
    location: "https-proxy.js:listen",
    message: "server-listening",
    data: { port: PORT, target: TARGET },
  });
  // #endregion
});

