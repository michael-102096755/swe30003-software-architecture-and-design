    // SWE30003 - Assignment 3 - JavaScript for our System's Frontend - Michael Attardi - 102096755 //
    const API = "http://127.0.0.1:5000";

    // App state
    let currentCustomer = null;  // The logged-in customer object
    let activeOrder = null;      // The current working order

    // Tab switching
    function switchTab(name) {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
      document.getElementById("tab-" + name).classList.add("active");
      event.target.classList.add("active");

      // Reload data for the tab we just switched to
      if (name === "books")     loadBooks();
      if (name === "orders")    { loadOrders(); loadBookSelectOptions(); }
      if (name === "invoices")  loadInvoices();
    }

    // Auth bar
    function updateAuthBar() {
      const bar = document.getElementById("auth-status");
      if (currentCustomer) {
        bar.innerHTML = `<span class="logged-in">Logged in as <strong>${currentCustomer.name}</strong> (${currentCustomer.email})</span>`;
      } else {
        bar.textContent = "Not logged in";
      }
    }

    // Helpers
    // Show a message in a given element ID
    function showMsg(id, text, isError = true) {
      const el = document.getElementById(id);
      el.innerHTML = `<div class="alert ${isError ? "alert-error" : "alert-success"}">${text}</div>`;
    }

    function clearMsg(id) {
      document.getElementById(id).innerHTML = "";
    }

    // Format a date string nicely
    function fmtDate(iso) {
      if (!iso) return "-";
      return new Date(iso).toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" });
    }

    // Format a dollar amount
    function fmtMoney(n) {
      return "$" + Number(n).toFixed(2);
    }


    // Generic API call wrapper
    async function api(method, path, body = null) {
      const opts = {
        method,
        headers: { "Content-Type": "application/json" }
      };
      if (body) opts.body = JSON.stringify(body);
      const res = await fetch(API + path, opts);
      const data = await res.json();
      return { ok: res.ok, status: res.status, data };
    }

    // Books
    async function loadBooks() {
      const { ok, data } = await api("GET", "/books");
      const grid = document.getElementById("book-grid");
      if (!ok || !data.length) {
        grid.innerHTML = `<p class="empty">No books in catalogue.</p>`;
        return;
      }
      grid.innerHTML = data.map(b => `
        <div class="book-card">
          <div class="book-title">${b.title}</div>
          <div class="book-author">${b.author}</div>
          <div class="book-price">${fmtMoney(b.price)}</div>
          <div class="book-meta">${b.category || ""} ${b.year ? "· " + b.year : ""}</div>
          <div class="book-stock ${b.stock === 0 ? "out" : ""}">
            ${b.stock > 0 ? b.stock + " in stock" : "Out of stock"}
          </div>
        </div>
      `).join("");
    }



    async function registerCustomer() {
      clearMsg("register-msg");
      const body = {
        name:     document.getElementById("reg-name").value.trim(),
        email:    document.getElementById("reg-email").value.trim(),
        password: document.getElementById("reg-password").value,
        address:  document.getElementById("reg-address").value.trim(),
      };
      const { ok, data } = await api("POST", "/customers/register", body);
      if (!ok) { showMsg("register-msg", data.error); return; }
      showMsg("register-msg", `Account created for ${data.name}.`, false);
    }

    async function loginCustomer() {
      clearMsg("login-msg");
      const body = {
        email:    document.getElementById("login-email").value.trim(),
        password: document.getElementById("login-password").value,
      };
      const { ok, data } = await api("POST", "/customers/login", body);
      if (!ok) { showMsg("login-msg", data.error); return; }
      currentCustomer = data;
      showMsg("login-msg", `Welcome back, ${data.name}!`, false);
      updateAuthBar();
    }

    function logoutCustomer() {
      currentCustomer = null;
      activeOrder = null;
      updateAuthBar();
      renderActiveOrder();
      showMsg("login-msg", "Logged out.", false);
    }

    // Orders
    async function loadOrders() {
      const { ok, data } = await api("GET", "/orders");
      const tbody = document.getElementById("orders-table-body");
      if (!ok || !data.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty">No orders found.</td></tr>`;
        return;
      }

      // Calculate total from items for display
      tbody.innerHTML = data.map(o => {
        const total = o.items.reduce((sum, i) => sum + (i.unit_price * i.quantity), 0);
        const gst = total * 0.1;
        return `
          <tr>
            <td style="font-size:11px">${o.order_id}</td>
            <td style="font-size:11px; color:var(--ink-light)">${o.customer_id}</td>
            <td>${o.items.length} item${o.items.length !== 1 ? "s" : ""}</td>
            <td>${fmtMoney(total + gst)}</td>
            <td><span class="badge badge-${o.status}">${o.status}</span></td>
            <td style="font-size:11px; color:var(--ink-light)">${fmtDate(o.created_at)}</td>
          </tr>
        `;
      }).join("");
    }

    async function loadBookSelectOptions() {
      const { ok, data } = await api("GET", "/books");
      const sel = document.getElementById("order-book-select");
      if (!ok || !data.length) { sel.innerHTML = `<option>No books available</option>`; return; }
      sel.innerHTML = data.map(b => `<option value="${b.book_id}">${b.title} — ${fmtMoney(b.price)}</option>`).join("");
    }

    async function createOrder() {
      clearMsg("order-action-msg");
      if (!currentCustomer) { showMsg("order-action-msg", "Please log in first."); return; }
      const { ok, data } = await api("POST", "/orders", { customer_id: currentCustomer.customer_id });
      if (!ok) { showMsg("order-action-msg", data.error); return; }
      activeOrder = data;
      showMsg("order-action-msg", `Order ${data.order_id} created.`, false);
      renderActiveOrder();
      loadOrders();
    }

    async function addItemToOrder() {
      clearMsg("add-item-msg");
      if (!activeOrder) { showMsg("add-item-msg", "Create an order first."); return; }
      const book_id  = document.getElementById("order-book-select").value;
      const quantity = parseInt(document.getElementById("order-qty").value) || 1;
      const { ok, data } = await api("POST", `/orders/${activeOrder.order_id}/items`, { book_id, quantity });
      if (!ok) { showMsg("add-item-msg", data.error); return; }
      activeOrder = data;
      renderActiveOrder();
      loadOrders();
    }

    async function removeItemFromOrder(book_id) {
      if (!activeOrder) return;
      const { ok, data } = await api("DELETE", `/orders/${activeOrder.order_id}/items/${book_id}`);
      if (!ok) { showMsg("order-status-msg", data.error); return; }
      activeOrder = data;
      renderActiveOrder();
      loadOrders();
    }

    async function confirmOrder() {
      clearMsg("order-action-msg");
      if (!activeOrder) { showMsg("order-action-msg", "No active order."); return; }
      const { ok, data } = await api("POST", `/orders/${activeOrder.order_id}/confirm`);
      if (!ok) { showMsg("order-action-msg", data.error); return; }
      activeOrder = data.order;
      showMsg("order-action-msg", `Order confirmed. Invoice ${data.invoice.invoice_id} generated.`, false);
      renderActiveOrder();
      loadOrders();
    }

    async function payOrder() {
      clearMsg("order-action-msg");
      if (!activeOrder) { showMsg("order-action-msg", "No active order."); return; }
      const { ok, data } = await api("POST", `/orders/${activeOrder.order_id}/pay`);
      if (!ok) { showMsg("order-action-msg", data.error); return; }
      activeOrder = data.order;
      showMsg("order-action-msg", "Payment processed successfully.", false);
      renderActiveOrder();
      loadOrders();
    }

    // Renders the active order items and totals panel
    function renderActiveOrder() {
      const container = document.getElementById("active-order-content");
      clearMsg("order-status-msg");

      if (!activeOrder) {
        container.innerHTML = `<p style="color:var(--ink-light); font-style:italic; font-size:13px">Log in and create an order to get started.</p>`;
        return;
      }

      const items = activeOrder.items;
      const subtotal = items.reduce((s, i) => s + (i.unit_price * i.quantity), 0);
      const gst      = subtotal * 0.1;
      const total    = subtotal + gst;

      const itemsHtml = items.length === 0
        ? `<tr><td colspan="4" class="empty">No items yet.</td></tr>`
        : items.map(i => `
            <tr>
              <td>${i.title}</td>
              <td>${fmtMoney(i.unit_price)}</td>
              <td>${i.quantity}</td>
              <td>${fmtMoney(i.unit_price * i.quantity)}
                ${activeOrder.status === "pending" ? `<button class="btn btn-danger btn-sm" style="margin-left:8px" onclick="removeItemFromOrder('${i.book_id}')">Remove</button>` : ""}
              </td>
            </tr>
          `).join("");

      container.innerHTML = `
        <div style="font-size:12px; color:var(--ink-light); margin-bottom:10px">
          Order ID: <strong style="color:var(--ink)">${activeOrder.order_id}</strong>
          &nbsp;|&nbsp; Status: <span class="badge badge-${activeOrder.status}">${activeOrder.status}</span>
        </div>
        <table>
          <thead><tr><th>Title</th><th>Unit Price</th><th>Qty</th><th>Line Total</th></tr></thead>
          <tbody>${itemsHtml}</tbody>
        </table>
        <div class="order-totals">
          <div class="total-row"><span>Subtotal</span><span>${fmtMoney(subtotal)}</span></div>
          <div class="total-row"><span>GST (10%)</span><span>${fmtMoney(gst)}</span></div>
          <div class="total-row grand"><span>Total</span><span>${fmtMoney(total)}</span></div>
        </div>
      `;
    }

    // Invoices
    async function loadInvoices() {
      const { ok, data } = await api("GET", "/invoices");
      const tbody = document.getElementById("invoices-table-body");
      if (!ok || !data.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty">No invoices found.</td></tr>`;
        return;
      }
      tbody.innerHTML = data.map(inv => `
        <tr>
          <td style="font-size:11px">${inv.invoice_id}</td>
          <td style="font-size:11px; color:var(--ink-light)">${inv.order_id}</td>
          <td style="font-size:11px; color:var(--ink-light)">${inv.customer_id}</td>
          <td>${fmtMoney(inv.subtotal)}</td>
          <td>${fmtMoney(inv.gst)}</td>
          <td><strong>${fmtMoney(inv.total)}</strong></td>
          <td style="font-size:11px; color:var(--ink-light)">${fmtDate(inv.created_at)}</td>
          <td><button class="btn btn-secondary btn-sm" onclick="viewInvoice('${inv.invoice_id}')">View</button></td>
        </tr>
      `).join("");
    }

    async function viewInvoice(invoice_id) {
      const { ok, data } = await api("GET", `/invoices/${invoice_id}`);
      if (!ok) return;
      const container = document.getElementById("invoice-detail-container");

      const itemRows = data.items.map(i => `
        <tr>
          <td>${i.title}</td>
          <td style="text-align:right">${fmtMoney(i.unit_price)}</td>
          <td style="text-align:center">${i.quantity}</td>
          <td style="text-align:right">${fmtMoney(i.line_total || i.unit_price * i.quantity)}</td>
        </tr>
      `).join("");

      container.innerHTML = `
        <div class="invoice-detail">
          <div class="invoice-header">
            <div>
              <div class="inv-title">Invoice</div>
              <div style="font-size:13px; color:var(--ink-light); margin-top:4px">${data.invoice_id}</div>
            </div>
            <div class="inv-meta">
              <div>Order: ${data.order_id}</div>
              <div>Customer: ${data.customer_id}</div>
              <div>Date: ${fmtDate(data.created_at)}</div>
            </div>
          </div>
          <table style="margin-bottom:16px">
            <thead>
              <tr>
                <th>Title</th>
                <th style="text-align:right">Unit Price</th>
                <th style="text-align:center">Qty</th>
                <th style="text-align:right">Line Total</th>
              </tr>
            </thead>
            <tbody>${itemRows}</tbody>
          </table>
          <div class="order-totals" style="max-width:280px; margin-left:auto">
            <div class="total-row"><span>Subtotal</span><span>${fmtMoney(data.subtotal)}</span></div>
            <div class="total-row"><span>GST (10%)</span><span>${fmtMoney(data.gst)}</span></div>
            <div class="total-row grand"><span>Total</span><span>${fmtMoney(data.total)}</span></div>
          </div>
        </div>
      `;

      // Scroll to the detail view
      container.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // Init
    loadBooks();
