/**
 * Invenza — Landing Page: Animated Inventory Ticker
 *
 * Simulates a live stock monitor with scrolling rows.
 * Rows occasionally flash amber to signal a low-stock alert.
 * Uses only realistic-looking inventory data — no decorative nonsense.
 */

;(function () {
  "use strict";

  // ─── Fake inventory dataset ───────────────────────────────────────────────
  const PRODUCTS = [
    { sku: "SKU-0041",  name: "Matte Black A4 Binder",     price: 3.99,   category: "Office" },
    { sku: "SKU-0087",  name: "USB-C Hub 7-Port",           price: 24.50,  category: "Electronics" },
    { sku: "SKU-0102",  name: "Whiteboard Markers (Pk 12)", price: 8.75,   category: "Stationery" },
    { sku: "SKU-0134",  name: "Ergonomic Wrist Rest",       price: 15.00,  category: "Office" },
    { sku: "SKU-0178",  name: "Thermal Label Roll 100mm",   price: 6.20,   category: "Warehouse" },
    { sku: "SKU-0203",  name: "Heavy Duty Stapler",         price: 11.99,  category: "Office" },
    { sku: "SKU-0229",  name: "Bubble Mailer Bags (Pk 50)", price: 9.40,   category: "Shipping" },
    { sku: "SKU-0255",  name: "Barcode Scanner USB",        price: 47.00,  category: "Electronics" },
    { sku: "SKU-0271",  name: "Sticky Notes 76x76mm",       price: 2.80,   category: "Stationery" },
    { sku: "SKU-0298",  name: "Cable Ties 200mm (Pk 100)",  price: 4.15,   category: "Warehouse" },
    { sku: "SKU-0314",  name: "Laminator A4 Pouch",         price: 0.18,   category: "Office" },
    { sku: "SKU-0337",  name: "Packing Tape 48mm",          price: 2.10,   category: "Shipping" },
    { sku: "SKU-0352",  name: "Filing Cabinet Dividers",    price: 5.60,   category: "Office" },
    { sku: "SKU-0381",  name: "Desk Organiser Tray",        price: 13.25,  category: "Office" },
    { sku: "SKU-0405",  name: "AAA Batteries (Pk 24)",      price: 7.99,   category: "General" },
    { sku: "SKU-0427",  name: "Stretch Wrap Film 400mm",    price: 12.50,  category: "Warehouse" },
    { sku: "SKU-0449",  name: "Wireless Mouse Nano",        price: 19.99,  category: "Electronics" },
    { sku: "SKU-0462",  name: "Correction Tape (Pk 5)",     price: 3.45,   category: "Stationery" },
    { sku: "SKU-0479",  name: "Hand Sanitiser 500ml",       price: 4.70,   category: "General" },
    { sku: "SKU-0501",  name: "Monitor Stand Riser",        price: 22.00,  category: "Electronics" },
  ];

  // ─── Qty & status helpers ─────────────────────────────────────────────────
  function randomQty() {
    const r = Math.random();
    if (r < 0.15) return Math.floor(Math.random() * 5) + 1;          // critical
    if (r < 0.30) return Math.floor(Math.random() * 12) + 6;         // low
    return Math.floor(Math.random() * 180) + 30;                      // ok
  }

  function statusInfo(qty) {
    if (qty <= 5)  return { label: "Critical", cls: "crit" };
    if (qty <= 15) return { label: "Low",      cls: "low"  };
    return              { label: "OK",         cls: "ok"   };
  }

  function fmtPrice(p) {
    return "£" + p.toFixed(2);
  }

  // Build a row object (product + live qty)
  function makeRowData(product) {
    const qty    = randomQty();
    const status = statusInfo(qty);
    return { ...product, qty, status };
  }

  // ─── DOM helpers ─────────────────────────────────────────────────────────
  function buildRowEl(data) {
    const row = document.createElement("div");
    row.className = "lp-ticker-row row-enter" + (data.status.cls !== "ok" ? " row-alert" : "");

    row.innerHTML =
      `<span class="col-sku">${data.sku}</span>` +
      `<span class="col-name">${data.name}</span>` +
      `<span class="col-qty${data.status.cls !== "ok" ? " low" : ""}">${data.qty}</span>` +
      `<span class="col-price">${fmtPrice(data.price)}</span>` +
      `<span><span class="lp-status-tag ${data.status.cls}">${data.status.label}</span></span>`;

    return row;
  }

  // ─── Ticker engine ────────────────────────────────────────────────────────
  const MAX_ROWS     = 6;   // visible rows at once
  const TICK_MS      = 2200; // how often a new row arrives
  const FLUSH_ROWS   = 30;  // re-shuffle product order after this many rows

  let tickerBody   = null;
  let productQueue = [];
  let rowCount     = 0;

  function refillQueue() {
    // Shuffle a copy so items appear in a varied order
    productQueue = [...PRODUCTS].sort(() => Math.random() - 0.5);
  }

  function addRow() {
    if (productQueue.length === 0) refillQueue();
    const product = productQueue.shift();
    const data    = makeRowData(product);
    const rowEl   = buildRowEl(data);

    tickerBody.appendChild(rowEl);
    rowCount++;

    // Remove oldest row once we exceed the max
    while (tickerBody.children.length > MAX_ROWS) {
      tickerBody.removeChild(tickerBody.firstChild);
    }
  }

  function seedInitialRows() {
    refillQueue();
    // Fill with slightly varied intervals to look staggered
    for (let i = 0; i < MAX_ROWS; i++) {
      setTimeout(addRow, i * 80);
    }
  }

  function startTicker() {
    tickerBody = document.getElementById("tickerBody");
    if (!tickerBody) return;

    seedInitialRows();
    setInterval(addRow, TICK_MS);
  }

  // ─── Login button loading state ───────────────────────────────────────────
  function initLoginButton() {
    const btn  = document.getElementById("loginBtn");
    const form = btn ? btn.closest("form") : null;
    if (!btn || !form) return;

    form.addEventListener("submit", function () {
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Signing in…</span>';
    });
  }

  // ─── Init ─────────────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", function () {
    startTicker();
    initLoginButton();
  });

})();
