// ===== STATE =====
const state = {
  currentPage: "workspace",
  totalSpent: 0,
  dailyLimit: 10,
  pollingInterval: null
};

// ===== NAVIGATION =====
function navigateTo(page) {
  state.currentPage = page;
  ui.setActivePage(page);

  if (page === "wallet") loadWalletPage();
  if (page === "marketplace") ui.renderMarketplace();
}

// ===== THEME =====
function toggleTheme() {
  const current = document.documentElement.classList.contains("dark") ? "dark" : "light";
  ui.setTheme(current === "dark" ? "light" : "dark");
}

// ===== SIDEBAR =====
function toggleSidebar() {
  ui.toggleSidebar();
}

// ===== SETTINGS TOGGLE =====
function toggleSetting(btn) {
  btn.classList.toggle("active");
}

// ===== AGENT INPUT =====
function handleInputKeydown(e) {
  if (e.key === "Enter") submitCommand();
}

async function submitCommand() {
  const input = document.getElementById("agent-input");
  const command = input.value.trim();
  if (!command) return;

  input.value = "";
  input.disabled = true;

  // Show user message
  ui.addCommandMessage(command, true);

  // Log start
  ui.addLogEntry("Agent initialized. Processing command...", "info");
  ui.addLogEntry(`Searching for relevant sources...`, "search");

  try {
    // Show thinking message
    ui.addCommandMessage("On it! Searching and fetching data...", false);

    // Call backend
    const result = await api.createTask(command);

    // Log transactions if any
    if (result.transactions && result.transactions.length > 0) {
      result.transactions.forEach(tx => {
        ui.addLogEntry(`Found source: ${tx.api_url}`, "search");
        ui.addLogEntry(`API requires x402 payment. Preparing transaction...`, "info");
        ui.addLogEntry(null, "payment", {
          amount: tx.amount.toFixed(2),
          currency: tx.currency,
          hash: tx.stellar_hash
        });
        ui.addLogEntry(`Payment confirmed. Fetching data...`, "success");

        // Update gas tank
        state.totalSpent += tx.amount;
        ui.updateGasTank(state.totalSpent, state.dailyLimit);
      });
    }

    // Log completion
    ui.addLogEntry("Task completed successfully.", "success");

    // Show answer in command panel
    ui.addCommandMessage(result.answer, false);

    // Refresh wallet
    loadWalletInfo();

  } catch (err) {
    ui.addLogEntry(`Error: ${err.message}`, "error");
    ui.addCommandMessage(`Sorry, something went wrong: ${err.message}`, false);
  } finally {
    input.disabled = false;
    input.focus();
  }
}

// ===== WALLET =====
async function loadWalletInfo() {
  try {
    const info = await api.getWalletInfo();
    ui.updateWalletDisplay(info);
  } catch (err) {
    console.error("Failed to load wallet info:", err);
  }
}

async function loadWalletPage() {
  try {
    const [info, transactions] = await Promise.all([
      api.getWalletInfo(),
      api.getAllTransactions()
    ]);

    ui.updateWalletDisplay(info);
    ui.renderWalletTransactions(transactions);

    // Update spending bar
    const totalSpent = transactions.reduce((sum, tx) => sum + tx.amount, 0);
    state.totalSpent = totalSpent;
    ui.updateGasTank(totalSpent, state.dailyLimit);

    const spendBar = document.getElementById("spend-bar");
    const spendUsed = document.getElementById("spend-used");
    const spendRemaining = document.getElementById("spend-remaining");
    const percent = Math.min((totalSpent / state.dailyLimit) * 100, 100);

    if (spendBar) spendBar.style.width = `${percent}%`;
    if (spendUsed) spendUsed.textContent = `${totalSpent.toFixed(2)} / ${state.dailyLimit.toFixed(2)} USDC used today`;
    if (spendRemaining) spendRemaining.textContent = `${(state.dailyLimit - totalSpent).toFixed(2)} USDC remaining`;

  } catch (err) {
    console.error("Failed to load wallet page:", err);
  }
}

// ===== POLLING =====
// Poll transactions every 5 seconds when on wallet page
function startPolling() {
  state.pollingInterval = setInterval(() => {
    if (state.currentPage === "wallet") loadWalletPage();
  }, 5000);
}

// ===== INIT =====
async function init() {
  // Load saved theme
  const savedTheme = localStorage.getItem("theme") || "dark";
  ui.setTheme(savedTheme);

  // Set timestamps
  const now = ui.formatTime();
  const welcomeTime = document.getElementById("welcome-time");
  const initTime = document.getElementById("init-time");
  if (welcomeTime) welcomeTime.textContent = now;
  if (initTime) initTime.textContent = now;

  // Load wallet info
  await loadWalletInfo();

  // Render marketplace
  ui.renderMarketplace();

  // Start polling
  startPolling();
}

// ===== BOOTSTRAP =====
document.addEventListener("DOMContentLoaded", init);