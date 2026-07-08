# Inventory Management System — PRD & Roadmap

**Owner:** Sajidul Ahmed
**Stack:** Django · PostgreSQL · HTML/CSS/JS
**Status:** Pre-development → this doc is the source of truth while building

---

## 1. Problem Statement

Small businesses track inventory manually (paper/spreadsheets), which causes:
- Stock-outs discovered too late
- No single source of truth on what's in stock
- Manual, slow, error-prone reporting
- No visibility into supplier/purchase history

## 2. Goal

Build a self-hostable web app that gives real-time stock visibility, automates low-stock alerts, and speeds up data entry via barcode/QR — without overengineering it before there's a working core.

## 3. Non-Goals (v1)

Explicitly **not** building yet (see Future Work in synopsis — don't let scope creep in):
- Multi-warehouse support
- Demand forecasting
- Expiry/batch tracking
- Payment gateway / invoicing
- Native mobile app

If you catch yourself building any of these before the core loop works end-to-end, stop — that's scope creep.

---

## 4. Users & Roles

| Role | Can do |
|---|---|
| **Admin** | Everything: manage products, users, suppliers, view all reports, configure alert thresholds |
| **Staff** | Record stock-in/stock-out, view product catalog, cannot delete products or manage users |
| **Auditor** | Read-only access to all data and reports, cannot modify anything |

## 5. Core Data Model

This is the backbone — get this right before writing a single view.

```
Product
├── id
├── name
├── sku (unique)
├── category (FK → Category)
├── unit_price
├── reorder_threshold      # triggers alert when stock <= this
└── current_stock          # DERIVED — updated only via Transaction, never edited directly

Category
├── id
└── name

Supplier
├── id
├── name
├── contact_email
└── phone

Transaction
├── id
├── product (FK → Product)
├── type              # 'IN' or 'OUT'
├── quantity
├── supplier (FK → Supplier, nullable — only for stock-in)
├── created_by (FK → User)
└── timestamp

Alert
├── id
├── product (FK → Product)
├── triggered_at
└── resolved (bool)

User (Django's built-in, extended)
└── role   # Admin / Staff / Auditor
```

**Golden rule:** `Product.current_stock` is never edited by a form. It's recalculated (or incremented/decremented) only inside the logic that saves a `Transaction`. This keeps your stock number always trustworthy and auditable.

---

## 6. Functional Requirements

### Must-have (v1 — build in this order)
1. User auth + role-based permissions
2. Product CRUD (Admin only for create/delete; Staff can view)
3. Category & Supplier CRUD
4. Stock-in / stock-out transaction form → updates `current_stock`
5. Transaction history log (filterable by product/date)
6. Low-stock alert list (auto-generated when stock ≤ reorder_threshold)
7. Dashboard: total products, low-stock count, recent transactions
8. Barcode/QR scan → auto-fill product in transaction form
9. Export inventory/transactions report as CSV/PDF

### Nice-to-have (only after all of the above work)
10. Charts on dashboard (Chart.js)
11. Email notification on low-stock (not just in-app)
12. Search/filter on product catalog

---

## 7. Non-Functional Requirements

- Responsive UI (usable on tablet, since warehouse staff may use one)
- All stock-changing actions must be logged (who, when, what) — no silent edits
- Page load under ~1s for catalog/dashboard on local dev data (~500 products)

---

## 8. Success Criteria (how you know v1 is "done")

- [ ] You can create a product, scan/enter a stock-in, see stock go up
- [ ] You can record a stock-out, see stock go down, and see it hit an alert when it crosses the threshold
- [ ] A Staff-role login cannot access user management or delete products
- [ ] You can export a report and it matches what's on screen
- [ ] Nothing about stock count was ever hand-edited outside a transaction

---

# Roadmap — Step by Step

Each phase ends with something *runnable*, not just files sitting there. Don't move to the next phase until the current one's checklist is done.

## Phase 0 — Project Setup (Day 1)
- [ ] Create virtualenv, install Django + psycopg2 + python-dotenv
- [ ] `django-admin startproject inventory_system`
- [ ] Create PostgreSQL database + user, connect it in `settings.py` via `.env`
- [ ] `python manage.py runserver` — confirm the default page loads
- [ ] Push initial commit (with `.gitignore` for venv/`.env`/`__pycache__`)
- [ ] Create the `inventory` app: `python manage.py startapp inventory`

## Phase 1 — Core Models & Admin (Day 2–3)
- [ ] Write `Category`, `Supplier`, `Product` models (from Section 5)
- [ ] Register them in `admin.py` so you can add test data via Django admin
- [ ] Run migrations, create superuser, add 5–10 dummy products through admin
- [ ] Sanity check: can you see them via `python manage.py shell`?

## Phase 2 — Auth & Roles (Day 4–5)
- [ ] Extend `User` with a `role` field (custom `Profile` model with OneToOne, or `groups`)
- [ ] Build login/logout pages (Django's built-in auth views are fine)
- [ ] Create a `@role_required` decorator or use Django Groups + `permission_required`
- [ ] Test: log in as each role, confirm restricted pages actually block Staff/Auditor

## Phase 3 — Product Catalog UI (Day 6–7)
- [ ] Product list view (table: name, SKU, category, current_stock, status badge if low)
- [ ] Product create/edit form (Admin-only)
- [ ] Category & Supplier management pages
- [ ] Basic CSS pass — doesn't need to be pretty yet, just usable

## Phase 4 — Transactions: the core loop (Day 8–11)
This is the most important phase — everything else is secondary to this working correctly.
- [ ] `Transaction` model + migration
- [ ] Stock-in form (product, quantity, supplier)
- [ ] Stock-out form (product, quantity)
- [ ] On save: atomically update `Product.current_stock` (use `select_for_update` or an F-expression to avoid race conditions)
- [ ] Transaction history page, filterable by product and date range
- [ ] Manual test: do 5 stock-ins and 3 stock-outs on one product, confirm the math is right every time

## Phase 5 — Alerts (Day 12–13)
- [ ] After every transaction save, check `current_stock <= reorder_threshold`
- [ ] If true and no unresolved alert exists → create one
- [ ] Alerts list page (Admin/Staff), mark-as-resolved action
- [ ] Test: push a product below threshold, confirm alert appears; restock it, confirm it can be resolved

## Phase 6 — Dashboard (Day 14–15)
- [ ] Total products, total stock value, low-stock count, recent transactions widget
- [ ] Keep it server-rendered first — add Chart.js only once the numbers are correct

## Phase 7 — Barcode/QR Integration (Day 16–18)
- [ ] Add `html5-qrcode` (or similar) to the stock-in/out form page
- [ ] On scan, look up product by SKU/barcode value, auto-fill the form
- [ ] Fallback: manual SKU search if no camera available
- [ ] Test on both a real product barcode and a generated QR code

## Phase 8 — Reports & Export (Day 19–20)
- [ ] Inventory report (current stock per product/category)
- [ ] Transaction report (date range, filterable)
- [ ] Export both as CSV first (easy), then PDF (use a library like `xhtml2pdf` or `weasyprint`) if time allows

## Phase 9 — Testing & Polish (Day 21–24)
- [ ] Write a handful of Django tests for the transaction → stock update logic specifically (this is the part that must never break)
- [ ] Manually test every role against every page
- [ ] UI polish pass — consistent styling, mobile check
- [ ] Fix whatever breaks

## Phase 10 — Documentation & Wrap-up (Day 25–28)
- [ ] Update README with real screenshots/GIFs of the working app
- [ ] Write a short `SETUP.md` if install steps got more detailed than the README covers
- [ ] Tag a `v1.0` release on GitHub
- [ ] (If academic deadline applies) finalize synopsis/report to match what was actually built

---

## Working Agreement (so we don't drift)

- We build **one phase at a time**, in order. No jumping to barcode scanning before transactions work.
- Every phase ends with something you can click through and test, not just code that "should work."
- When you're ready for a phase, tell me which one and we'll go step by step — models first, then views, then templates, then test together.
