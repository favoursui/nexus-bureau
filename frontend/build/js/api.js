const API_BASE = "http://127.0.0.1:8000/api";

const api = {

  // ===== TASKS =====
  async createTask(userInput) {
    const res = await fetch(`${API_BASE}/tasks/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_input: userInput })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getTasks() {
    const res = await fetch(`${API_BASE}/tasks/`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getTask(taskId) {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getWalletInfo() {
    const res = await fetch(`${API_BASE}/tasks/wallet/info`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // ===== TRANSACTIONS =====
  async getAllTransactions() {
    const res = await fetch(`${API_BASE}/transactions/`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getTransactionsByTask(taskId) {
    const res = await fetch(`${API_BASE}/transactions/${taskId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};