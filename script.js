const grid = document.getElementById("grid");
const tabs = document.getElementById("tabs");
const sourceSelect = document.getElementById("sourceSelect");
const countLabel = document.getElementById("count");
const state = { q: "", category: "", source: "" };

/* ---------- Light / Dark mode ---------- */
const themeBtn = document.getElementById("themeBtn");
function setTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  themeBtn.textContent = t === "dark" ? "☀️" : "🌙";
  localStorage.setItem("theme", t);
}
themeBtn.onclick = () =>
  setTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
setTheme(localStorage.getItem("theme") || "light");

/* ---------- Helpers ---------- */
function timeAgo(iso) {
  const mins = Math.floor((Date.now() - new Date(iso)) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return mins + " min ago";
  if (mins < 1440) return Math.floor(mins / 60) + " h ago";
  return Math.floor(mins / 1440) + " d ago";
}

function showMessage(text) {
  grid.innerHTML = "";
  const p = document.createElement("p");
  p.className = "msg";
  p.textContent = text;
  grid.appendChild(p);
}

/* ---------- Draw one news card (textContent = safe from XSS) ---------- */
function makeCard(a) {
  const card = document.createElement("article");
  card.className = "card";
  card.style.setProperty("--cat", `var(--c-${a.category})`);

  const thumb = document.createElement("div");
  thumb.className = "thumb";
  if (a.image) thumb.style.backgroundImage = `url("${encodeURI(a.image)}")`;

  const body = document.createElement("div");
  body.className = "body";

  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = a.category;

  const h3 = document.createElement("h3");
  const link = document.createElement("a");
  link.href = a.link; link.target = "_blank"; link.rel = "noopener";
  link.textContent = a.headline;
  h3.appendChild(link);

  const meta = document.createElement("div");
  meta.className = "meta";
  const src = document.createElement("strong");
  src.textContent = a.source;
  const time = document.createElement("span");
  time.textContent = timeAgo(a.published);
  meta.append(src, time);

  body.append(badge, h3, meta);
  card.append(thumb, body);
  return card;
}

/* ---------- Load news from the backend ---------- */
async function loadNews() {
  showMessage("Loading news…");
  try {
    const res = await fetch("/api/news?" + new URLSearchParams(state));
    if (res.status === 429) throw new Error("Too many searches. Please wait a minute.");
    if (!res.ok) throw new Error("Server problem. Please try again later.");
    const articles = await res.json();
    countLabel.textContent = articles.length + " articles";
    if (!articles.length) return showMessage("No news found for this search 😕");
    grid.innerHTML = "";
    articles.forEach(a => grid.appendChild(makeCard(a)));
  } catch (err) {
    countLabel.textContent = "";
    showMessage("⚠️ " + err.message);   // fallback message instead of a crash
  }
}

/* ---------- Category tabs + source dropdown ---------- */
async function loadFilters() {
  const cats = await (await fetch("/api/categories")).json();
  ["All", ...cats].forEach(name => {
    const b = document.createElement("button");
    b.className = "tab" + (name === "All" ? " active" : "");
    b.textContent = name;
    if (name !== "All") b.style.setProperty("--tab", `var(--c-${name})`);
    b.onclick = () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      b.classList.add("active");
      state.category = name === "All" ? "" : name;
      loadNews();
    };
    tabs.appendChild(b);
  });

  const sources = await (await fetch("/api/sources")).json();
  sources.forEach(s => {
    const o = document.createElement("option");
    o.value = s.name;
    o.textContent = `${s.name} (${s.type})`;
    sourceSelect.appendChild(o);
  });
}

sourceSelect.onchange = () => { state.source = sourceSelect.value; loadNews(); };

loadFilters().then(loadNews);