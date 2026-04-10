// ===== STATE =====
const state = {
  currentPage: "workspace",
  totalSpent:  0,
  dailyLimit:  10,
  polling:     null
};

// ===== NAVIGATION =====
function navigateTo(page) {
  state.currentPage = page;
  ui.setActivePage(page);
  if (page === "wallet")      loadWalletPage();
  if (page === "marketplace") ui.renderMarketplace();
}

// ===== THEME =====
function toggleTheme() {
  const isDark = document.documentElement.classList.contains("dark");
  ui.setTheme(isDark ? "light" : "dark");
}

// ===== SIDEBAR =====
function toggleSidebar() {
  ui.toggleSidebar();
}

// ===== SETTINGS =====
function toggleSetting(btn) {
  btn.classList.toggle("active");
  const settings = {
    autoApprove:   document.querySelectorAll(".toggle-btn")[0]?.classList.contains("active"),
    notifications: document.querySelectorAll(".toggle-btn")[1]?.classList.contains("active"),
    requirePin:    document.querySelectorAll(".toggle-btn")[2]?.classList.contains("active")
  };
  localStorage.setItem("nexus_settings", JSON.stringify(settings));
}

// ===== INPUT =====
function handleInputKeydown(e) {
  if (e.key === "Enter") submitCommand();
}

// ===== WALLET CONNECTION =====
async function connectWallet() {
  try {
    const { publicKey, network } = await wallet.connect();
    const balance = await api.getHorizonBalance(publicKey);
    ui.showWalletConnected(publicKey, balance);
    console.log(`✅ Wallet connected: ${publicKey} on ${network}`);
  } catch (err) {
    alert(err.message);
  }
}

function disconnectWallet() {
  wallet.disconnect();
  ui.showWalletDisconnected();
}

// ===== SUBMIT COMMAND =====
async function submitCommand() {
  const input   = document.getElementById("agent-input");
  const command = input.value.trim();
  if (!command) return;

  input.value    = "";
  input.disabled = true;

  // Show user message in command panel
  ui.addCommandMessage(command, true);

  // Initial log entries
  ui.addLogEntry("Agent initialized. Processing command...", "info");
  ui.addLogEntry("Searching for relevant sources...", "search");

  try {
    ui.addCommandMessage("On it! Searching and fetching data...", false);

    const result = await api.createTask(command);

    if (result.transactions && result.transactions.length > 0) {
      for (const tx of result.transactions) {
        const amount = parseFloat(tx.amount);

        // Check PIN requirement
        try {
          await requirePin(amount);
        } catch(e) {
          ui.addLogEntry("❌ Transaction cancelled — PIN rejected.", "error");
          ui.addCommandMessage("❌ Transaction cancelled.", false);
          return;
        }

        ui.addLogEntry(`🔍 Found paywalled source: ${tx.api_url}`, "search");

        // Auto-approve check
        if (getSetting("autoApprove") && amount <= 0.10) {
          ui.addLogEntry(`⚡ Auto-approved payment: ${amount.toFixed(3)} ${tx.currency}`, "info");
        } else {
          ui.addLogEntry(`💳 Payment required: ${amount.toFixed(3)} ${tx.currency}`, "info");
        }

        ui.addLogEntry(`⏳ Signing Stellar transaction...`, "info");
        ui.addLogEntry(null, "payment", {
          amount:       amount.toFixed(3),
          currency:     tx.currency,
          hash:         tx.stellar_hash,
          explorer_url: tx.explorer_url || `https://stellar.expert/explorer/testnet/tx/${tx.stellar_hash}`
        });
        ui.addLogEntry(`✅ Access granted. Fetching data...`, "success");

        // Send notification
        sendNotification(
          "Payment Confirmed ✅",
          `${amount.toFixed(3)} ${tx.currency} paid · Tx: ${tx.stellar_hash.slice(0, 8)}...`
        );

        state.totalSpent += amount;
        ui.updateGasTank(state.totalSpent, state.dailyLimit);
      }
    } else {
      ui.addLogEntry("No paywalled sources encountered.", "success");
    }

    ui.addLogEntry("Task completed successfully.", "success");
    ui.addCommandMessage(result.answer, false);

    if (wallet.isWalletConnected()) {
      try {
        const balance = await api.getHorizonBalance(wallet.getStoredKey());
        ui.showWalletConnected(wallet.getStoredKey(), balance);
      } catch(e) {}
    }

    loadAgentWalletInfo();

  } catch (err) {
    let msg = "Something went wrong. Please try again.";
    try {
      const parsed = JSON.parse(err.message);
      msg = parsed.detail || msg;
      if (msg.startsWith("Agent run failed:")) msg = msg.replace("Agent run failed: ", "");
      const m = msg.match(/'message': '([^']+)'/);
      if (m) msg = m[1];
    } catch(e) { msg = err.message; }

    ui.addLogEntry(`❌ Error: ${msg}`, "error");
    ui.addCommandMessage(`❌ ${msg}`, false);
  }
}

// ===== AGENT WALLET =====
async function loadAgentWalletInfo() {
  try {
    const info = await api.getWalletInfo();
    const xlm  = parseFloat(info.balances?.native || 0);
    const usdc = parseFloat(info.balances?.USDC || info.balances?.usdc || 0);
    console.log(`Agent wallet — XLM: ${xlm.toFixed(3)}, USDC: ${usdc.toFixed(3)}`);
  } catch (e) {
    console.error("Agent wallet error:", e);
  }
}

// ===== WALLET PAGE =====
async function loadWalletPage() {
  try {
    const txs = await api.getAllTransactions();
    ui.renderWalletTransactions(txs);

    // Calculate total spent
    const spent = txs.reduce((s, t) => s + parseFloat(t.amount), 0);
    state.totalSpent = spent;
    ui.updateGasTank(spent, state.dailyLimit);

    // Update spending bar
    const pct = Math.min((spent / state.dailyLimit) * 100, 100);
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    const bar = document.getElementById("spend-bar");
    if (bar) bar.style.width = `${pct}%`;
    set("spend-used",      `${spent.toFixed(3)} / ${state.dailyLimit.toFixed(2)} USDC used today`);
    set("spend-remaining", `${(state.dailyLimit - spent).toFixed(3)} USDC remaining`);

    // Refresh user wallet balance if connected
    if (wallet.isWalletConnected()) {
      try {
        const balance = await api.getHorizonBalance(wallet.getStoredKey());
        ui.showWalletConnected(wallet.getStoredKey(), balance);
      } catch(e) {}
    }

  } catch (e) {
    console.error("Wallet page error:", e);
  }
}

// ===== POLLING =====
function startPolling() {
  state.polling = setInterval(() => {
    if (state.currentPage === "wallet") loadWalletPage();
  }, 5000);
}

// ===== LOAD SETTINGS =====
function loadSettings() {
  try {
    const saved = localStorage.getItem("nexus_settings");
    if (!saved) return;
    const settings = JSON.parse(saved);
    const toggles  = document.querySelectorAll(".toggle-btn");
    if (toggles[0] && settings.autoApprove)   toggles[0].classList.add("active");
    if (toggles[1] && settings.notifications)  toggles[1].classList.add("active");
    if (toggles[2] && settings.requirePin)     toggles[2].classList.add("active");
  } catch(e) {}
}

// ===== INIT =====
async function init() {
  // Set theme
  const theme = localStorage.getItem("theme") || "dark";
  ui.setTheme(theme);

  // Set timestamps
  const now = ui.formatTime();
  const wt  = document.getElementById("welcome-time");
  const it  = document.getElementById("init-time");
  if (wt) wt.textContent = now;
  if (it) it.textContent = now;

  // Check if wallet was previously connected
  if (wallet.isWalletConnected()) {
    try {
      const publicKey = wallet.getStoredKey();
      const balance   = await api.getHorizonBalance(publicKey);
      ui.showWalletConnected(publicKey, balance);
    } catch(e) {
      wallet.disconnect();
      ui.showWalletDisconnected();
    }
  } else {
    ui.showWalletDisconnected();
  }

  // Load today's spending for gas tank
  try {
    const txs        = await api.getAllTransactions();
    const today      = new Date().toDateString();
    const todaySpent = txs
      .filter(tx => new Date(tx.created_at).toDateString() === today)
      .reduce((sum, tx) => sum + parseFloat(tx.amount), 0);
    state.totalSpent = todaySpent;
    ui.updateGasTank(todaySpent, state.dailyLimit);
  } catch(e) {
    console.error("Gas tank init error:", e);
  }

  // Load saved settings
  loadSettings();
  // Request browser notification permission
  await requestNotificationPermission();

  function getSetting(key) {
    try {
      const saved = localStorage.getItem("nexus_settings");
      if (!saved) return false;
      return JSON.parse(saved)[key] || false;
    } catch(e) { return false; }
  }

  //
  // ===== TOAST NOTIFICATIONS =====
  function showToast(title, message, icon = "✅") {
    const toast   = document.getElementById("toast");
    const toastTitle = document.getElementById("toast-title");
    const toastMsg   = document.getElementById("toast-message");
    const toastIcon  = document.getElementById("toast-icon");

    if (!toast) return;
    toastTitle.textContent = title;
    toastMsg.textContent   = message;
    toastIcon.textContent  = icon;

    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 4000);
  }

  // ===== BROWSER NOTIFICATIONS =====
  async function requestNotificationPermission() {
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
  }

  function sendNotification(title, body) {
    if (!getSetting("notifications")) return;

    // Browser notification
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(title, {
        body: body,
        icon: "/favicon.ico"
      });
    }

    // Always show toast
    showToast(title, body, "💳");
  }

  // ===== PIN =====
  let pinResolve = null;
  let pinReject  = null;

  function requirePin(amount) {
    return new Promise((resolve, reject) => {
      if (!getSetting("requirePin") || parseFloat(amount) <= 1.0) {
        resolve(true);
        return;
      }

      // Show PIN modal
      const modal = document.getElementById("pin-modal");
      const input = document.getElementById("pin-input");
      if (modal) modal.classList.remove("hidden");
      if (input) { input.value = ""; input.focus(); }

      pinResolve = resolve;
      pinReject  = reject;
    });
  }

  function handlePinKeydown(e) {
    if (e.key === "Enter") confirmPin();
    if (e.key === "Escape") cancelPin();
  }

  function confirmPin() {
    const input = document.getElementById("pin-input");
    const pin   = input ? input.value.trim() : "";

    if (!pin || pin.length < 4) {
      alert("Please enter a valid PIN (minimum 4 digits)");
      return;
    }

    // In production you'd verify against a stored hash
    // For demo — any 4+ digit PIN works
    const modal = document.getElementById("pin-modal");
    if (modal) modal.classList.add("hidden");

    if (pinResolve) { pinResolve(true); pinResolve = null; pinReject = null; }
  }

  function cancelPin() {
    const modal = document.getElementById("pin-modal");
    if (modal) modal.classList.add("hidden");
    if (pinReject) { pinReject(new Error("PIN cancelled")); pinResolve = null; pinReject = null; }
  }

  //
  // Render marketplace
  ui.renderMarketplace();

  // Start polling
  startPolling();
}

document.addEventListener("DOMContentLoaded", init);