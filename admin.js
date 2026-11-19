const rows = document.getElementById("rows");
const msg = document.getElementById("msg");

// --- 1. LOGIN FUNCTIONS ---
async function manualLogin() {
  const u = document.getElementById("username").value;
  const p = document.getElementById("password").value;
  msg.textContent = "Logging in...";
  
  const res = await fetch("/api/admin/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: u, password: p })
  });

  if (res.ok) {
    showDashboard();
  } else {
    const error = await res.json();
    msg.textContent = "⚠️ " + error.detail;
  }
}

async function logout() {
  await fetch("/api/admin/logout", { method: "POST" });
  document.getElementById("loginPanel").style.display = "flex";
  document.getElementById("dashboardControls").style.display = "none";
  document.getElementById("metricsPanel").style.display = "none";
  document.getElementById("tablePanel").style.display = "none";
  document.getElementById("username").value = "";
  document.getElementById("password").value = "";
  msg.textContent = "Logged out successfully.";
}

function showDashboard() {
  document.getElementById("loginPanel").style.display = "none";
  document.getElementById("dashboardControls").style.display = "flex";
  document.getElementById("metricsPanel").style.display = "grid";
  document.getElementById("tablePanel").style.display = "block";
  msg.textContent = "✅ Authenticated securely.";
  loadData();
}

// --- 2. DASHBOARD DATA FUNCTIONS ---
async function loadData() {
  msg.textContent = "Loading data... ⏳";
  
  // Fetch Stats (Metrics)
  const statsRes = await fetch("/api/admin/stats");
  if (!statsRes.ok) {
    msg.textContent = "⚠️ Session expired. Please login again.";
    logout();
    return;
  }
  const stats = await statsRes.json();
  document.getElementById("totSources").textContent = stats.sources;
  document.getElementById("actSources").textContent = `${stats.active} / ${stats.failing}`;
  document.getElementById("totArticles").textContent = stats.articles;

  // Fetch Sources Table
  const sourcesRes = await fetch("/api/admin/sources");
  const sources = await sourcesRes.json();
  
  rows.innerHTML = "";
  sources.forEach(s => {
    const tr = document.createElement("tr");
    
    let statusClass = String(s.last_status).startsWith("OK") ? "status-badge status-ok" : "status-badge status-fail";
    let statusHTML = `<span class="${statusClass}">${s.last_status}</span>`;
    let btnText = s.active ? "Disable" : "Enable";
    let btnColor = s.active ? "var(--muted)" : "var(--purple)";

    tr.innerHTML = `
      <td><strong>${s.name}</strong></td>
      <td>${s.type}</td>
      <td>${statusHTML}</td>
      <td>${s.last_checked || "-"}</td>
      <td><strong>${s.articles}</strong></td>
      <td>
        <button onclick="toggleSource(${s.id}, ${!s.active})" style="padding: 5px 10px; background: ${btnColor}; color: white; border: none; border-radius: 4px; cursor: pointer;">
          ${btnText}
        </button>
      </td>
    `;
    rows.appendChild(tr);
  });
  msg.textContent = ""; 
}

async function toggleSource(id, newState) {
  await fetch(`/api/admin/sources/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ active: newState })
  });
  loadData(); // Reload table
}

async function fetchNewsNow() {
  msg.textContent = "Fetching… this takes about 20 seconds ⏳";
  const res = await fetch("/api/admin/refresh", { method: "POST" });
  msg.textContent = res.ok ? "✅ Refresh finished" : "⚠️ Error refreshing data.";
  if (res.ok) loadData();
}

// Auto-check if already logged in (Checks if cookie is valid)
window.onload = async () => {
  const res = await fetch("/api/admin/me");
  if (res.ok) showDashboard();
};