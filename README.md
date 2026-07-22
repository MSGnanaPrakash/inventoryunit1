<div align="center">

# 🧵 Textile Dyeing Inventory Management System

**A web-based inventory and production management system for textile dyeing units.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen?style=flat-square)

</div>

---

## 📖 Overview

The **Textile Dyeing Inventory Management System** is a web application built for textile dyeing units to digitize and streamline their day-to-day operations. It manages raw material and dye inventory, tracks production batches, and automates reporting — replacing error-prone manual registers with a reliable, centralized system.

This project earned direct recognition from an industry dyeing manager for its real-world impact on production tracking.

## ✨ Key Features

- 📦 **Inventory Tracking** — Real-time tracking of raw materials, dyes, and finished stock levels.
- 🏭 **Batch Management** — Create, monitor, and update production batches from start to finish.
- 🧪 **Dye Recipe Management** — Store and reuse dye formulations tied to specific batches and colours.
- 📑 **Automated Reporting** — Generate inventory and production reports without manual compilation.
- 🔐 **Secure Authentication** — Role-based login to protect sensitive production and inventory data.

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Backend Framework | Flask |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |

## 🗂️ Project Structure

```
textile-dyeing-inventory-system/
├── app/
│   ├── models.py              # Inventory, Batch, DyeRecipe models
│   ├── routes/
│   │   ├── inventory.py        # Stock add/update/remove
│   │   ├── batches.py          # Batch creation & tracking
│   │   ├── recipes.py          # Dye recipe management
│   │   ├── reports.py          # Automated report generation
│   │   └── auth.py             # Login & role-based access
│   ├── templates/              # HTML pages
│   └── static/                  # CSS, JS, images
├── config.py                    # DB & app configuration
├── app.py                       # App entry point
├── requirements.txt
└── README.md
```

> Adjust this structure to match your actual repo layout.

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/MSGnanaPrakash/textile-dyeing-inventory-system.git
cd textile-dyeing-inventory-system

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your MySQL database and update config.py with your credentials
```

## ▶️ Usage

**Start the Flask app:**
```bash
python app.py
```

Then open `http://localhost:5000` in your browser to:
- Log in with your vendor/staff credentials
- Track and update inventory levels
- Create and monitor production batches
- Manage dye recipes and generate reports

## 📋 Core Modules

| Module | Description |
|---|---|
| Inventory | Track raw materials, dyes, and stock levels in real time |
| Batches | Manage production batches through their full lifecycle |
| Dye Recipes | Store and reuse colour/dye formulations |
| Reports | Auto-generate inventory and production reports |
| Authentication | Secure, role-based login for staff and vendors |

## 🔗 Related Project

This system pairs with the **[Colour Matching](#)** module for automated dye colour matching — built as a companion tool within the same textile dyeing workflow.

## 🔭 Roadmap

- [ ] Integrate real-time low-stock alerts
- [ ] Add analytics dashboard for production trends
- [ ] Barcode/QR support for raw material tracking
- [ ] Export reports to PDF/Excel

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to open a pull request or raise an issue.

## 📄 License

This project is open source. Add your preferred license (e.g. MIT) here.

## 📬 Contact

**Gnanaprakash MS**
📧 msgnana2310564@ssn.edu.in
🔗 [GitHub](https://github.com/MSGnanaPrakash)
