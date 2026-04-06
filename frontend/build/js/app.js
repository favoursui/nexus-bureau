//  STATE 
const state = {
  currentPage: "workspace",
  totalSpent:  0,
  dailyLimit:  10,
  polling:     null
};

//  NAVIGATION 
function navigateTo(page) {
  state.currentPage = page;
  ui.setActivePage(page);
  if (page === "wallet")      loadWalletPage();
  if (page === "marketplace") ui.renderMarketplace();
}

//  THEME 
function toggleTheme() {
  const isDark = document.documentElement.classList.contains("dark");
  ui.setTheme(isDark ? "light" : "dark");
}

//  SIDEBAR 
function toggleSidebar() {
  ui.toggleSidebar();
}

//  SETTINGS 
function toggleSetting(btn) {
  btn.classList.toggle("active");
}

//  INPUT 
function handleInputKeydown(e) {
  if (e.key === "Enter") submitCommand();
}

//  SUBMIT COMMAND 
async function submitCommand() {
  const input   = document.getElementById("agent-input");
  const command = input.value.trim();
  if (!command) return;

  input.value    = "";
  input.disabled = true;

  ui.addCommandMessage(command, true);
  ui.addLogEntry("Agent initialized. Processing command...", "info");
  ui.addLogEntry("Searching for relevant sources...", "search");

  try {
    ui.addCommandMessage("On it! Searching and fetching data...", false);

    const result = await api.createTask(command);

    if (result.transactions && result.transactions.length > 0) {
      result.transactions.forEach(tx => {
        ui.addLogEntry(`Found source: ${tx.api_url}`, "search");
        ui.addLogEntry("API requires x402 payment. Preparing transaction...", "info");
        ui.addLogEntry(null, "payment", {
          amount:   tx.amount.toFixed(2),
          currency: tx.currency,
          hash:     tx.stellar_hash
        });
        ui.addLogEntry("Payment confirmed. Fetching data...", "success");
        state.totalSpent += tx.amount;
        ui.updateGasTank(state.totalSpent, state.dailyLimit);
      });
    } else {
      ui.addLogEntry("Task completed. No payments required.", "success");
    }

    ui.addLogEntry("Task completed successfully.", "success");
    ui.addCommandMessage(result.answer, false);
    loadWalletInfo();

  } catch (err) {
    let msg = "Something went wrong. Please try again.";
    try {
      const parsed = JSON.parse(err.message);
      msg = parsed.detail || msg;
      if (msg.startsWith("Agent run failed:")) msg = msg.replace("Agent run failed: ", "");
      const m = msg.match(/'message': '([^']+)'/);
      if (m) msg = m[1];
    } catch { msg = err.message; }

    ui.addLogEntry(`Error: ${msg}`, "error");
    ui.addCommandMessage(`❌ ${msg}`, false);

  } finally {
    input.disabled = false;
    input.focus();
  }
}

//  WALLET 
async function loadWalletInfo() {
  try {
    const info = await api.getWalletInfo();
    ui.updateWalletDisplay(info);
  } catch (e) {
    console.error("Wallet info error:", e);
  }
}

async function loadWalletPage() {
  try {
    const [info, txs] = await Promise.all([
      api.getWalletInfo(),
      api.getAllTransactions()
    ]);

    ui.updateWalletDisplay(info);
    ui.renderWalletTransactions(txs);

    const spent = txs.reduce((s, t) => s + t.amount, 0);
    state.totalSpent = spent;
    ui.updateGasTank(spent, state.dailyLimit);

    const pct = Math.min((spent / state.dailyLimit) * 100, 100);
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    const bar = document.getElementById("spend-bar");

    if (bar) bar.style.width = `${pct}%`;
    set("spend-used",      `${spent.toFixed(2)} / ${state.dailyLimit.toFixed(2)} USDC used today`);
    set("spend-remaining", `${(state.dailyLimit - spent).toFixed(2)} USDC remaining`);

  } catch (e) {
    console.error("Wallet page error:", e);
  }
}

//  POLLING 
function startPolling() {
  state.polling = setInterval(() => {
    if (state.currentPage === "wallet") loadWalletPage();
  }, 5000);
}

//  INIT 
async function init() {
  const theme = localStorage.getItem("theme") || "dark";
  ui.setTheme(theme);

  const now = ui.formatTime();
  const wt  = document.getElementById("welcome-time");
  const it  = document.getElementById("init-time");
  if (wt) wt.textContent = now;
  if (it) it.textContent = now;

  await loadWalletInfo();
  ui.renderMarketplace();
  startPolling();
}

document.addEventListener("DOMContentLoaded", init);