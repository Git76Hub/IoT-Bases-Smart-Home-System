const $ = (id) => document.getElementById(id);
let latest = null;

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => (el.hidden = true), 3500);
}

async function send(target, value) {
  try {
    const r = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target, value }),
    });
    if (!r.ok) toast((await r.json()).error || "Command failed.");
  } catch {
    toast("Cannot reach the dashboard server.");
  }
}

function setTag(el, text, cls) {
  el.textContent = text;
  el.className = "tag" + (cls ? " " + cls : "");
}

function render(data) {
  latest = data;
  const s = data.state;
  $("temp").textContent = s["livingroom/temperature"] ?? "–";
  $("hum").textContent = s["livingroom/humidity"] ?? "–";
  setTag($("conn"), data.broker ? "Broker connected" : "Broker offline", data.broker ? "good" : "bad");

  const motionAge = data.now - (data.updated["hallway/motion"] ?? 0);
  if (s["hallway/motion"] === "1") setTag($("motion"), "Motion now", "active");
  else if (s["hallway/motion"] === "0" && motionAge < 3600) setTag($("motion"), `Clear for ${Math.round(motionAge)} s`, "");
  else setTag($("motion"), "No data", "");

  document.querySelectorAll(".toggle").forEach((b) => {
    const value = s[b.dataset.key];
    const on = value === b.dataset.onState;
    b.disabled = value === undefined || !data.broker;
    b.setAttribute("aria-pressed", String(on));
    if (b.classList.contains("lock")) b.textContent = value === undefined ? "–" : on ? "Locked" : "Unlocked";
    else b.textContent = value === undefined ? "–" : on ? "On" : "Off";
  });

  const list = $("devices");
  list.replaceChildren();
  Object.entries(data.devices).sort().forEach(([id, st]) => {
    const li = document.createElement("li");
    li.className = "tag " + (st === "online" ? "good" : "bad");
    li.textContent = `${id}: ${st}`;
    list.appendChild(li);
  });
}

document.querySelectorAll(".toggle").forEach((b) =>
  b.addEventListener("click", () => {
    const on = b.getAttribute("aria-pressed") === "true";
    send(b.dataset.target, on ? b.dataset.cmdOff : b.dataset.cmdOn);
  })
);

async function poll() {
  try {
    render(await (await fetch("/api/state")).json());
  } catch {
    setTag($("conn"), "Dashboard unreachable", "bad");
  }
}

/* ---- History chart (plain canvas, works offline on the Pi) ---- */
async function drawChart() {
  const metric = $("metric").value, minutes = $("range").value;
  let points = [];
  try {
    points = (await (await fetch(`/api/history/${metric}?minutes=${minutes}`)).json()).points;
  } catch { /* leave empty */ }
  $("chart-empty").hidden = points.length > 1;

  const canvas = $("chart"), dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = 220;
  canvas.width = w * dpr; canvas.height = h * dpr;
  const g = canvas.getContext("2d");
  g.scale(dpr, dpr); g.clearRect(0, 0, w, h);
  if (points.length < 2) return;

  const css = getComputedStyle(document.documentElement);
  const ink = css.getPropertyValue("--ink"), muted = css.getPropertyValue("--muted"), lit = css.getPropertyValue("--lit");
  const pad = { l: 44, r: 12, t: 12, b: 24 };
  const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  let y0 = Math.min(...ys), y1 = Math.max(...ys);
  if (y1 - y0 < 1) { y0 -= 0.5; y1 += 0.5; }
  const X = (x) => pad.l + ((x - x0) / (x1 - x0)) * (w - pad.l - pad.r);
  const Y = (y) => h - pad.b - ((y - y0) / (y1 - y0)) * (h - pad.t - pad.b);

  g.font = "12px sans-serif"; g.fillStyle = muted; g.strokeStyle = muted; g.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const v = y0 + ((y1 - y0) * i) / 4, y = Y(v);
    g.globalAlpha = 0.25; g.beginPath(); g.moveTo(pad.l, y); g.lineTo(w - pad.r, y); g.stroke();
    g.globalAlpha = 1; g.fillText(v.toFixed(1), 4, y + 4);
  }
  const t = (x) => new Date(x * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  g.fillText(t(x0), pad.l, h - 6);
  g.textAlign = "right"; g.fillText(t(x1), w - pad.r, h - 6); g.textAlign = "left";

  g.strokeStyle = metric === "temperature" ? lit : ink; g.lineWidth = 2.5; g.beginPath();
  points.forEach((p, i) => (i ? g.lineTo(X(p[0]), Y(p[1])) : g.moveTo(X(p[0]), Y(p[1]))));
  g.stroke();
}

$("metric").addEventListener("change", drawChart);
$("range").addEventListener("change", drawChart);
window.addEventListener("resize", drawChart);
poll(); drawChart();
setInterval(poll, 1500);
setInterval(drawChart, 15000);
