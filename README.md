<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=220&section=header&text=Inventory%20Management%20System&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Real-time%20Stock%20Tracking%20%7C%20Smart%20Alerts%20%7C%20Barcode%20Powered&descAlignY=58&descSize=18" width="100%"/>

<br/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24&duration=3000&pause=800&color=2E8A7F&center=true&vCenter=true&width=650&lines=Track+every+product+in+real+time;Never+run+out+of+stock+again;Barcode%2FQR+powered+stock+entry;Built+with+Django+%2B+PostgreSQL" alt="Typing SVG" />

<br/><br/>

<img src="https://img.shields.io/badge/status-in%20development-C9A227?style=for-the-badge&labelColor=1B2A4A"/>
<img src="https://img.shields.io/badge/python-3.11-2E5C8A?style=for-the-badge&logo=python&logoColor=white&labelColor=1B2A4A"/>
<img src="https://img.shields.io/badge/django-backend-2E8A7F?style=for-the-badge&logo=django&logoColor=white&labelColor=1B2A4A"/>
<img src="https://img.shields.io/badge/postgresql-database-336791?style=for-the-badge&logo=postgresql&logoColor=white&labelColor=1B2A4A"/>
<img src="https://img.shields.io/badge/license-MIT-C9A227?style=for-the-badge&labelColor=1B2A4A"/>
<br/>
<img src="https://img.shields.io/github/stars/Zlmaoooo/inventory-management-system?style=for-the-badge&color=C9A227&labelColor=1B2A4A"/>
<img src="https://img.shields.io/github/forks/Zlmaoooo/inventory-management-system?style=for-the-badge&color=2E8A7F&labelColor=1B2A4A"/>
<img src="https://img.shields.io/github/issues/Zlmaoooo/inventory-management-system?style=for-the-badge&color=2E5C8A&labelColor=1B2A4A"/>

</div>

<br/>

<p align="center">
  <img src="https://raw.githubusercontent.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/main/images/blue-star-break.gif" width="100%"/>
</p>

## 📖 About The Project

> A **web-based Inventory Management System** built to replace manual, error-prone stock tracking with a real-time, automated, and auditable digital workflow — for any business, anywhere in the world.

Small and medium businesses everywhere still run inventory off paper registers or scattered spreadsheets. That means stock-outs get discovered too late, nobody has one single source of truth, and pulling a sales report eats up an entire afternoon. This project fixes that with **live stock visibility, barcode-powered data entry, automated low-stock alerts, and role-based dashboards** — all in one clean, self-hostable web app that anyone can spin up.

Whether you're a corner shop owner tired of counting boxes by hand, or a developer looking for a solid open-source inventory system to build on — this is for you.

<br/>

## ✨ Key Features

<table>
<tr>
<td width="50%" valign="top">

### 📦 Core Inventory
- Product catalog with categories & SKUs
- Real-time stock-in / stock-out tracking
- Automated low-stock & reorder alerts
- Supplier records & purchase order history

</td>
<td width="50%" valign="top">

### ⚡ Smart & Modern
- 📷 Barcode / QR scanning for fast stock entry
- 🔐 Role-based access (Admin, Staff, Auditor)
- 📊 Exportable inventory & sales reports (PDF/Excel)
- 📱 Responsive, mobile-friendly dashboard

</td>
</tr>
</table>

<br/>

## 🧱 Tech Stack

<div align="center">

<img src="https://skillicons.dev/icons?i=html,css,js,django,python,postgres,git,github,vscode&theme=dark" />

</div>

<div align="center">

| Layer | Technology |
|---|---|
| **Frontend** | HTML5 · CSS3 · JavaScript (AJAX) |
| **Backend** | Python — Django |
| **Database** | PostgreSQL |
| **Scanning** | Barcode / QR JS library (html5-qrcode) |
| **Version Control** | Git & GitHub |

</div>

<br/>

## 🏗️ System Architecture

<div align="center">
<img src="/Architecture diagram/architecture_diagram.png" width="80%" alt="System Architecture Diagram"/>
<br/>
<sub><i>Layered 3-tier architecture — Presentation → Application → Data</i></sub>
</div>

<br/>

<details>
<summary>📐 <b>Click to view Use Case & Data Flow Diagrams</b></summary>
<br/>
<div align="center">
<img src="Architecture diagram/dfd_diagram.png" width="80%" alt="Use Case Diagram"/>
<br/><br/>
<img src="Architecture diagram/usecase_diagram.png" width="80%" alt="Data Flow Diagram"/>
</div>
</details>

<br/>

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.11+
PostgreSQL 14+
Node.js (for frontend tooling, optional)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Zlmaoooo/inventory-management-system.git
cd inventory-management-system

# 2. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your database in settings.py, then migrate
python manage.py migrate

# 5. Run the development server
python manage.py runserver
```

Then open **`http://127.0.0.1:8000`** in your browser. 🎉

<br/>

## 📂 Project Structure

```
inventory-management-system/
├── inventory/            # Core app: models, views, templates
│   ├── models.py         # Product, Stock, Supplier, Transaction
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── static/                # CSS, JS, images
├── docs/                  # Diagrams & architecture assets
├── manage.py
├── requirements.txt
└── README.md
```

<br/>

## 🗺️ Roadmap

- [x] Product catalog & stock tracking
- [x] Barcode / QR stock entry
- [x] Low-stock alerts
- [ ] Multi-warehouse support
- [ ] Expiry date tracking
- [ ] AI-based demand forecasting
- [ ] Stripe payment gateway integration
- [ ] Auto-generated customer invoices

Got an idea for a feature? Open an issue — this roadmap is shaped by the community, not just me.

<br/>

## 🤝 Contributing

Contributions, issues, and feature requests are genuinely welcome — this project is built in the open for anyone to use, fork, or improve.

```bash
1. Fork the project
2. Create your feature branch   (git checkout -b feature/AmazingFeature)
3. Commit your changes          (git commit -m 'Add some AmazingFeature')
4. Push to the branch           (git push origin feature/AmazingFeature)
5. Open a Pull Request
```

<br/>

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

<br/>

## 👤 Author

<div align="center">

<img src="https://avatars.githubusercontent.com/u/172844403?v=4" width="100" style="border-radius:50%"/>

### Sajidul Ahmed

*CSE student · builder · always shipping something new*

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=16&duration=3000&pause=1000&color=8A8A8A&center=true&vCenter=true&width=500&lines=DevOps+%7C+Java+%26+Python+Developer;Data+Science+%2B+Tech+Enthusiast;Building+cool+stuff%2C+breaking+some+of+it" alt="Typing SVG" />

<br/><br/>

<a href="https://github.com/Zlmaoooo"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white"/></a>
<a href="https://www.linkedin.com/in/sajidul-ahmed-b5177a312/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white"/></a>
<a href="https://leetcode.com/u/Z_lmaoooo/"><img src="https://img.shields.io/badge/LeetCode-FFA116?style=for-the-badge&logo=leetcode&logoColor=black"/></a>
<a href="https://discord.gg/8kGabWKpMB"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>

</div>

<br/>

<div align="center">

### ⭐ If this project helped you, consider giving it a star — it genuinely helps!

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer" width="100%"/>

</div>
