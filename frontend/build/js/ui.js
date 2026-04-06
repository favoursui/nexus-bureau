const ui = {

  //  NAVIGATION 
  setActivePage(page) {
    document.querySelectorAll(".page").forEach(p => p.classList.add("hidden"));
    const target = document.getElementById(`page-${page}`);
    if (target) target.classList.remove("hidden");

    document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active-nav"));
    const active = document.getElementById(`nav-${page}`);
    if (active) active.classList.add("active-nav");

    const titles = {
      workspace:   "WORKSPACE",
      wallet:      "WALLET / FUNDS",
      marketplace: "API MARKETPLACE",
      settings:    "SETTINGS"
    };
    const el = document.getElementById("page-title");
    if (el) el.textContent = titles[page] || page.toUpperCase();
  },

  //  SIDEBAR 
  toggleSidebar() {
    const sidebar  = document.getElementById("sidebar");
    const labels   = document.querySelectorAll(".nav-label");
    const logo     = document.getElementById("logo-text");
    const wallet   = document.getElementById("wallet-info");
    const gas      = document.getElementById("gas-info");
    const navLabel = document.getElementById("nav-label");

    const collapsed = sidebar.classList.contains("collapsed");

    if (collapsed) {
      sidebar.classList.remove("collapsed");
      sidebar.style.width    = "176px";
      sidebar.style.minWidth = "176px";
      labels.forEach(l => l.classList.remove("hidden"));
      [logo, wallet, gas, navLabel].forEach(el => el && el.classList.remove("hidden"));
    } else {
      sidebar.classList.add("collapsed");
      sidebar.style.width    = "56px";
      sidebar.style.minWidth = "56px";
      labels.forEach(l => l.classList.add("hidden"));
      [logo, wallet, gas, navLabel].forEach(el => el && el.classList.add("hidden"));
    }
  },

  //  THEME 
  setTheme(theme) {
    const html = document.documentElement;
    html.classList.remove("dark", "light");
    html.classList.add(theme);
    localStorage.setItem("theme", theme);

    const dark  = document.getElementById("theme-icon-dark");
    const light = document.getElementById("theme-icon-light");
    const label = document.getElementById("theme-label");

    if (theme === "dark") {
      dark  && dark.classList.remove("hidden");
      light && light.classList.add("hidden");
      label && (label.textContent = "Dark Mode");
    } else {
      dark  && dark.classList.add("hidden");
      light && light.classList.remove("hidden");
      label && (label.textContent = "Light Mode");
    }
  },

  //  WALLET 
  updateWalletDisplay(info) {
    const key   = info.public_key || "";
    const short = key ? key.slice(0, 4) + "..." + key.slice(-4) : "N/A";
    const xlm   = parseFloat(info.balances?.native  || 0);
    const usdc  = parseFloat(info.balances?.USDC || info.balances?.usdc || 0);
    const bal   = usdc > 0 ? `${usdc.toFixed(2)} USDC` : `${xlm.toFixed(2)} XLM`;
    const num   = usdc > 0 ? usdc.toFixed(2) : xlm.toFixed(2);

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set("wallet-short",        short);
    set("wallet-balance",      bal);
    set("wallet-total",        num);
    set("wallet-address-full", `${short} · Stellar Network`);
  },

  //  TRANSACTIONS 
  renderWalletTransactions(txs) {
    const c = document.getElementById("wallet-transactions");
    if (!c) return;
    if (!txs.length) {
      c.innerHTML = `<p class="text-xs text-muted text-center py-4">No transactions yet.</p>`;
      return;
    }
    c.innerHTML = txs.map(tx => `
      <div class="flex items-center justify-between py-2.5 border-b border-subtle last:border-0">
        <div class="flex items-center gap-3 overflow-hidden min-w-0">
          <div class="w-8 h-8 min-w-8 rounded-full flex items-center justify-center" style="background:rgba(239,68,68,0.1)">
            <svg class="w-4 h-4" style="color:#f87171" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17L17 7M17 7H7M17 7v10"/>
            </svg>
          </div>
          <div class="overflow-hidden min-w-0">
            <p class="text-sm text-primary truncate">${tx.api_url.replace(/^https?:\/\//, '').slice(0, 35)}</p>
            <p class="text-xs text-muted font-mono">${ui.timeAgo(tx.created_at)}</p>
          </div>
        </div>
        <span class="text-sm font-mono ml-3 flex-shrink-0" style="color:#f87171">-${tx.amount.toFixed(2)} ${tx.currency}</span>
      </div>
    `).join("");
  },

  //  EXECUTION LOG 
  addLogEntry(message, type = "info", extra = null) {
    const log = document.getElementById("execution-log");
    if (!log) return;

    const time = new Date().toLocaleTimeString("en-US", { hour:"2-digit", minute:"2-digit", second:"2-digit" });

    const dotColor = {
      info:    "var(--color-accent)",
      search:  "#60a5fa",
      success: "#4ade80",
      error:   "#f87171",
      payment: "#4ade80"
    }[type] || "var(--color-accent)";

    let html = "";

    if (type === "payment" && extra) {
      html = `
        <div class="log-payment">
          <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="color:#4ade80; font-size:12px;">✅</span>
              <span class="text-sm font-semibold text-primary">Payment Authorized</span>
            </div>
            <a href="https://stellar.expert/explorer/testnet/tx/${extra.hash}" target="_blank"
               style="font-size:11px; color:var(--color-accent); text-decoration:none; white-space:nowrap;">
              View on Stellar Expert ↗
            </a>
          </div>
          <p style="font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:700; color:var(--color-text-primary);">
            ${extra.amount} <span style="font-size:14px; color:var(--color-text-muted);">${extra.currency}</span>
          </p>
          <p class="text-xs text-muted font-mono" style="margin-top:4px;">${time}</p>
        </div>`;
    } else {
      html = `
        <div class="log-entry">
          <div style="display:flex; align-items:flex-start; gap:10px;">
            <div style="width:8px; height:8px; min-width:8px; border-radius:50%; background:${dotColor}; margin-top:5px;"></div>
            <p class="text-sm text-primary" style="word-break:break-word; overflow-wrap:break-word; line-height:1.5;">${message}</p>
          </div>
          <p class="text-xs text-muted font-mono" style="margin-top:6px; padding-left:18px;">${time}</p>
        </div>`;
    }

    log.insertAdjacentHTML("beforeend", html);
    log.scrollTop = log.scrollHeight;
  },

  //  COMMAND MESSAGES 
  addCommandMessage(text, isUser = false) {
    const c = document.getElementById("command-messages");
    if (!c || !text || !text.trim()) return;

    const time    = new Date().toLocaleTimeString("en-US", { hour:"2-digit", minute:"2-digit", second:"2-digit" });
    const cleaned = text.replace(/- https?:\/\/\S+/g, "").replace(/\n/g, "<br>").trim();

    const html = isUser
      ? `<div class="msg-bubble-user">
           <p class="text-sm text-primary" style="word-break:break-word; overflow-wrap:break-word;">${cleaned}</p>
           <p class="text-xs text-muted font-mono" style="margin-top:6px;">${time}</p>
         </div>`
      : `<div class="msg-bubble-agent">
           <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
             <div class="agent-avatar">N</div>
             <span class="text-xs text-muted" style="font-weight:500;">Nexus Bureau</span>
           </div>
           <p class="text-sm text-primary" style="word-break:break-word; overflow-wrap:break-word; line-height:1.6;">${cleaned}</p>
           <p class="text-xs text-muted font-mono" style="margin-top:6px;">${time}</p>
         </div>`;

    c.insertAdjacentHTML("beforeend", html);
    c.scrollTop = c.scrollHeight;
  },

  //  GAS TANK 
  updateGasTank(used, limit) {
    const pct = Math.min((used / limit) * 100, 100).toFixed(0);
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    const bar = document.getElementById("gas-bar");
    if (bar) bar.style.width = `${pct}%`;
    set("gas-percent", `${pct}%`);
    set("gas-used",    `${used.toFixed(2)} USDC used`);
    set("gas-limit",   `${limit} limit`);
  },

  //  MARKETPLACE 
  renderMarketplace() {
    const apis = [
      { name:"OpenWeather",  desc:"Real-time weather data",      price:"0.05", cat:"Weather",  icon:"🌤️" },
      { name:"Geocoding Pro",desc:"Address to coordinates",      price:"0.02", cat:"Location", icon:"🌐" },
      { name:"NewsWire",     desc:"Breaking news aggregation",   price:"0.08", cat:"News",     icon:"⚡" },
      { name:"VectorDB",     desc:"Semantic search endpoints",   price:"0.10", cat:"AI",       icon:"🗄️" },
      { name:"FinanceAPI",   desc:"Real-time stock & crypto",    price:"0.07", cat:"Finance",  icon:"📈" },
      { name:"ScrapeAPI",    desc:"Web scraping service",        price:"0.03", cat:"Data",     icon:"🕷️" }
    ];

    const grid = document.getElementById("api-grid");
    if (!grid) return;

    grid.innerHTML = apis.map(a => `
      <div class="api-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
          <div style="width:40px; height:40px; border-radius:10px; background:var(--color-bg-subtle); border:1px solid var(--color-border); display:flex; align-items:center; justify-content:center; font-size:18px;">${a.icon}</div>
          <span style="font-size:11px; padding:2px 8px; border-radius:20px; background:var(--color-bg-subtle); color:var(--color-text-muted);">${a.cat}</span>
        </div>
        <p class="text-sm font-semibold text-primary" style="margin-bottom:4px;">${a.name}</p>
        <p class="text-xs text-muted" style="margin-bottom:10px;">${a.desc}</p>
        <p class="text-xs font-mono text-accent">${a.price} USDC / call</p>
      </div>
    `).join("");
  },

  //  HELPERS 
  timeAgo(dateStr) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1)  return "just now";
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24)  return `${hrs} hr ago`;
    return `${Math.floor(hrs / 24)} days ago`;
  },

  formatTime() {
    return new Date().toLocaleTimeString("en-US", { hour:"2-digit", minute:"2-digit", second:"2-digit" });
  }
};