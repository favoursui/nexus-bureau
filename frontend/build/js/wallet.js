// ===== RABET WALLET =====
// Rabet extension injects window.rabet directly into the page

var wallet = {

  isInstalled: function() {
    return typeof window.rabet !== "undefined";
  },

  connect: async function() {
    try {
      if (!this.isInstalled()) {
        throw new Error("No Stellar wallet detected. Please install Freighter or Rabet.");
      }

      // Connect using Rabet
      var result = await window.rabet.connect();
      console.log("Rabet connect result:", result);

      if (!result || !result.publicKey) {
        throw new Error("Could not get public key from Rabet.");
      }

      var publicKey = result.publicKey;
      var network   = result.network || "testnet";

      localStorage.setItem("wallet_public_key", publicKey);
      localStorage.setItem("wallet_network", network);

      return { publicKey: publicKey, network: network };

    } catch(err) {
      console.error("Wallet connect error:", err);
      throw new Error(err.message || "Failed to connect wallet");
    }
  },

  disconnect: function() {
    try {
      if (window.rabet && window.rabet.disconnect) {
        window.rabet.disconnect();
      }
    } catch(e) {}
    localStorage.removeItem("wallet_public_key");
    localStorage.removeItem("wallet_network");
  },

  getStoredKey: function() {
    return localStorage.getItem("wallet_public_key");
  },

  isWalletConnected: function() {
    return !!localStorage.getItem("wallet_public_key");
  },

  formatKey: function(key) {
    if (!key) return "N/A";
    return key.slice(0, 4) + "..." + key.slice(-4);
  }

};