const ui = {

  // ===== NAVIGATION =====
  setActivePage(page) {
    // Hide all pages
    document.querySelectorAll(".page").forEach(p => p.classList.add("hidden"));

    // Show target page
    const target = document.getElementById(`page-${page}`);
    if (target) target.classList.remove("hidden");

    // Update nav active state
    document.querySelectorAll(".nav-link").forEach(link => {
      link.classList.remove("active-nav");
    });
    const activeLink = document.getElementById(`nav-${page}`);
    if (activeLink) activeLink.classList.add("active-nav");

    // Update page title
    const titles = {
      workspace: "WORKSPACE",
      wallet: "WALLET / FUNDS",
      marketplace: "API MARKETPLACE",
      settings: "SETTINGS"
    };
    document.getElementById("page-title").textContent = titles[page] || page.toUpperCase();
  },

  // ===== SIDEBAR TOGGLE =====
  toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const labels = document.querySelectorAll(".nav-label");
    const logo = document.getElementById("logo-text");
    const walletInfo = document.getElementById("wallet-info");
    const gasInfo = document.getElementById("gas-info");
    const navLabel = document.getElementById("nav-label");
    const themeLabel = document.getElementById("theme-label");
    const isCollapsed = sidebar.classList.contains("collapsed");

    if (isCollapsed) {
      sidebar.classList.remove("collapsed");
      sidebar.style.width = "176px";
      labels.forEach(l => l.classList.remove("hidden"));
      if (logo) logo.classList.remove("hidden");
      if (walletInfo) walletInfo.classList.remove("hidden");
      if (gasInfo) gasInfo.classList.remove("hidden");
      if (navLabel) navLabel.classList.remove("hidden");
      if (themeLabel) themeLabel.classList.remove("hidden");
    } else {
      sidebar.classList.add("collapsed");
      sidebar.style.width = "56px";
      labels.forEach(l => l.classList.add("hidden"));
      if (logo) logo.classList.add("hidden");
      if (walletInfo) walletInfo.classList.add("hidden");
      if (gasInfo) gasInfo.classList.add("hidden");
      if (navLabel) navLabel.classList.add("hidden");
      if (themeLabel) themeLabel.classList.add("hidden");
    }
  },

  // ===== THEME =====
  setTheme(theme) {
    const html = document.documentElement;
    html.classList.remove("dark", "light");
    html.classList.add(theme);
    localStorage.setItem("theme", theme);

    const darkIcon = document.getElementById("theme-icon-dark");
    const lightIcon = document.getElementById("theme-icon-light");
    const label = document.getElementById("theme-label");

    if (theme === "dark") {
      darkIcon.classList.remove("hidden");
      lightIcon.classList.add("hidden");
      if (label) label.textContent = "Dark Mode";
    } else {
      darkIcon.classList.add("hidden");
      lightIcon.classList.remove("hidden");
      if (label) label.textContent = "Light Mode";
    }
  },

  // ===== WALLET =====
  updateWalletDisplay(info) {
    const short = info.public_key
      ? info.public_key.slice(0, 4) + "..." + info.public_key.slice(-4)
      : "N/A";

    const xlm = info.balances?.native || "0";
    const usdc = info.balances?.USDC || info.balances?.usdc || "0";
    const display = parseFloat(usdc) > 0 ? `${parseFloat(usdc).toFixed(2)} USDC` : `${parseFloat(xlm).toFixed(2)} XLM`;

    // Sidebar
    const walletShort = document.getElementById("wallet-short");
    const walletBal = document.getElementById("wallet-balance");
    if (walletShort) walletShort.textContent = short;
    if (walletBal) walletBal.textContent = display;

    // Wallet page
    const walletTotal = document.getElementById("wallet-total");
    const walletAddrFull = document.getElementById("wallet-address-full");
    if (walletTotal) walletTotal.textContent = parseFloat(usdc) > 0 ? parseFloat(usdc).toFixed(2) : parseFloat(xlm).toFixed(2);
    if (walletAddrFull) walletAddrFull.textContent = `${short} · Stellar Network`;
  },

  // ===== TRANSACTIONS =====
  renderWalletTransactions(transactions) {
    const container = document.getElementById("wallet-transactions");
    if (!container) return;

    if (!transactions.length) {
      container.innerHTML = `<p class="text-xs text-muted text-center py-4">No transactions yet.</p>`;
      return;
    }

    container.innerHTML = transactions.map(tx => `
      <div class="flex items-center justify-between py-2 border-b border-subtle last:border-0">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-red-500/10 flex items-center justify-center">
            <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17L17 7M17 7H7M17 7v10"/>
            </svg>
          </div>
          <div>
            <p class="text-sm text-primary">${tx.api_url.replace(/^https?:\/\//, '').slice(0, 30)}...</p>
            <p class="text-xs text-muted font-mono">${ui.timeAgo(tx.created_at)}</p>
          </div>
        </div>
        <span class="text-sm font-mono text-red-400">-${tx.amount.toFixed(2)} ${tx.currency}</span>
      </div>
    `).join("");
  },

  // ===== EXECUTION LOG =====
  addLogEntry(message, type = "info", extraData = null) {
    const log = document.getElementById("execution-log");
    if (!log) return;

    const time = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit", minute: "2-digit", second: "2-digit"
    });

    const icons = {
      info: `<div class="w-6 h-6 rounded-full bg-purple-600/20 flex items-center justify-center">
               <div class="w-2 h-2 rounded-full bg-purple-400"></div>
             </div>`,
      search: `<div class="w-6 h-6 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-400 text-xs">🔍</div>`,
      payment: `<div class="w-6 h-6 rounded-full bg-green-600/20 flex items-center justify-center text-green-400 text-xs">💳</div>`,
      success: `<div class="w-6 h-6 rounded-full bg-green-600/20 flex items-center justify-center text-green-400 text-xs">✅</div>`,
      error: `<div class="w-6 h-6 rounded-full bg-red-600/20 flex items-center justify-center text-red-400 text-xs">❌</div>`
    };

    let entryHTML = "";

    if (type === "payment" && extraData) {
      entryHTML = `
        <div class="log-payment border rounded-xl px-4 py-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-green-400 text-xs">✅</span>
              <span class="text-sm font-semibold text-primary">Payment Authorized</span>
            </div>
            <a href="https://stellar.expert/explorer/testnet/tx/${extraData.hash}"
               target="_blank"
               class="text-xs text-purple-400 hover:underline">
              View on Stellar Expert ↗
            </a>
          </div>
          <p class="text-2xl font-mono font-bold text-primary mt-1">
            ${extraData.amount} <span class="text-muted text-lg">${extraData.currency}</span>
          </p>
          <p class="text-xs text-muted font-mono mt-1">${time}</p>
        </div>`;
    } else {
      entryHTML = `
        <div class="log-entry border border-subtle rounded-xl px-4 py-3">
          <div class="flex items-center gap-2">
            ${icons[type] || icons.info}
            <p class="text-sm text-primary">${message}</p>
          </div>
          <p class="text-xs text-muted font-mono mt-1">${time}</p>
        </div>`;
    }

    log.insertAdjacentHTML("beforeend", entryHTML);
    log.scrollTop = log.scrollHeight;
  },

  // ===== COMMAND MESSAGES =====
  addCommandMessage(text, isUser = false) {
    const container = document.getElementById("command-messages");
    if (!container) return;

    const time = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit", minute: "2-digit", second: "2-digit"
    });

    const html = isUser
      ? `<div class="flex justify-end">
           <div class="bg-purple-600/20 border border-purple-600/30 rounded-xl px-3 py-2 max-w-xs">
             <p class="text-sm text-primary">${text}</p>
             <p class="text-xs text-muted font-mono mt-1">${time}</p>
           </div>
         </div>`
      : `<div class="bg-surface-2 rounded-xl p-3">
           <div class="flex items-center gap-2 mb-1">
             <div class="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center text-xs text-white font-bold">N</div>
           </div>
           <p class="text-sm text-primary">${text}</p>
           <p class="text-xs text-muted font-mono mt-1">${time}</p>
         </div>`;

    container.insertAdjacentHTML("beforeend", html);
    container.scrollTop = container.scrollHeight;
  },

  // ===== GAS TANK =====
  updateGasTank(used, limit) {
    const percent = Math.min((used / limit) * 100, 100).toFixed(0);
    const bar = document.getElementById("gas-bar");
    const pct = document.getElementById("gas-percent");
    const usedEl = document.getElementById("gas-used");
    const limitEl = document.getElementById("gas-limit");
    if (bar) bar.style.width = `${percent}%`;
    if (pct) pct.textContent = `${percent}%`;
    if (usedEl) usedEl.textContent = `${used.toFixed(2)} USDC used`;
    if (limitEl) limitEl.textContent = `${limit} limit`;
  },

  // ===== MARKETPLACE =====
  renderMarketplace() {
    const apis = [
      { name: "OpenWeather", desc: "Real-time weather data", price: "0.05", category: "Weather", icon: "🌤️" },
      { name: "Geocoding Pro", desc: "Address to coordinates", price: "0.02", category: "Location", icon: "🌐" },
      { name: "NewsWire", desc: "Breaking news aggregation", price: "0.08", category: "News", icon: "⚡" },
      { name: "VectorDB", desc: "Semantic search endpoints", price: "0.10", category: "AI", icon: "🗄️" },
      { name: "FinanceAPI", desc: "Real-time stock & crypto", price: "0.07", category: "Finance", icon: "📈" },
      { name: "ScrapeAPI", desc: "Web scraping service", price: "0.03", category: "Data", icon: "🕷️" }
    ];

    const grid = document.getElementById("api-grid");
    if (!grid) return;

    grid.innerHTML = apis.map(api => `
      <div class="api-card">
        <div class="flex justify-between items-start mb-3">
          <div class="w-10 h-10 rounded-xl border border-subtle flex items-center justify-center text-xl" style="background-color: var(--color-bg-subtle); filter: saturate(1.4) brightness(0.85);">${api.icon}</div>
          <span class="text-xs px-2 py-0.5 rounded-full bg-subtle text-muted">${api.category}</span>
        </div>
        <p class="text-sm font-semibold text-primary">${api.name}</p>
        <p class="text-xs text-muted mt-0.5 mb-3">${api.desc}</p>
        <p class="text-xs font-mono text-purple-400">${api.price} USDC / call</p>
      </div>
    `).join("");
  },

  // ===== HELPERS =====
  timeAgo(dateStr) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hr ago`;
    return `${Math.floor(hrs / 24)} days ago`;
  },

  formatTime() {
    return new Date().toLocaleTimeString("en-US", {
      hour: "2-digit", minute: "2-digit", second: "2-digit"
    });
  }
};