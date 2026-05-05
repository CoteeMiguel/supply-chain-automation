## Supply Chain Automation

> RPA bots and data pipelines for a Fortune 500 Technology Leader Latin America supply chain operations. Built and deployed in production in Chile, with replicas running in Peru and Colombia.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-150458?style=flat&logo=pandas&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=flat&logo=selenium&logoColor=white)
![SAP](https://img.shields.io/badge/SAP_S%2F4HANA-0FAAFF?style=flat&logo=sap&logoColor=white)
![Power Automate](https://img.shields.io/badge/Power_Automate-0066FF?style=flat&logo=powerautomate&logoColor=white)

---

## Impact

| Automation | Result |
|---|---|
| Customs overtime alerts | **100% elimination of overstay penalties** |
| Container capacity analysis | **USD 1.3M saved** in the first year of operation |
| Delivery control RPA (Hola Chao) | **Reduced delivery lead times** in the metro region + improved POD compliance |

---

## Problem

This Fortune 500 Technology Leader supply chain team was manually tracking hundreds of daily deliveries across three disconnected systems: SAP S/4 (ERP), Global Logistics provider's TMS (transport management), and email threads between teams. This caused:

- Recurring fines for cargo held at the airport past the free storage window
- Underutilized maritime containers sailing toward Latin America (Mexico → Argentina)
- Hours of daily manual work to cross-reference data between systems
- Delays and errors in coordinating with the LSP

This repository contains the Python scripts that automate those processes end to end.

---

## System Architecture

```
Power Automate  (orchestrator — scheduled daily execution)
│
├── marisun.py              → Authenticates to DHL TMS via HTTP session
│                             Downloads 100-day delivery report
│                             Deduplicates, adds aggregated status column
│                             Output: Chile.xlsx → OneDrive
│
├── dlv_control.py          → Downloads SAP S/4 report via Selenium RPA
│                             Joins SAP × TMS data, applies business rules
│                             Classifies each delivery with required action
│                             Sends result automatically to LSP by email
│
├── alerta_aeropuerto.py    → Filters AIR shipments at risk of overtime penalty
│                             Calculates days since ATA per shipment
│                             Sends urgent pickup list to customs broker
│
└── tarros_capacity.py      → Queries SQL Server for SKU volume data
                              Calculates utilization % per container and route
                              Flags containers below 60% before departure
                              Output: Excel report with 4 analysis sheets

Power BI Dashboard  (consumes OneDrive Excel files — not included in this repo)
```

---

## Scripts

### `dlv_control.py` — Delivery tracking and action control
RPA that automates the full daily delivery follow-up cycle: extracts all open order statuses from SAP S/4 via Selenium, joins the result with the LSP's TMS report, applies 8 business rules to determine the required action for each unique delivery, and automatically emails the result to the LSP team.

**Stack:** Python · Selenium · pandas · win32com (Outlook) · SAP S/4 Fiori  
**Frequency:** Daily, orchestrated by Power Automate  
**Business rules applied:** `ok` / `not ok` / `delete dlv` / `assign incident` / `csr escalation` / `check`

---

### `marisun.py` — Global Logistics Provider TMS ETL pipeline
Authenticates to the LSP's TMS via HTTP session (no browser automation needed), downloads the last 100 days of delivery data, removes duplicates keeping only the latest status per delivery, and enriches the report with an aggregated status column based on business-defined criteria.

**Stack:** Python · requests · pandas  
**Output:** Excel file consumed by `dlv_control.py`

---

### `alerta_aeropuerto.py` — Customs overtime alert
Processes the daily import report, filters by AIR modal and business unit, calculates days since arrival (ATA), and generates the list of dispatches that must be picked up urgently to avoid overstay fines. The result is sent directly to the customs broker.

**Stack:** Python · pandas  
**Result:** Zero overtime penalties after implementation

---

### `tarros_capacity.py` — Container utilization analysis
Queries a SQL Server database for per-SKU volumetric data, joins it with the DMR (maritime shipment report), calculates utilization percentage per container grouped by product line, and identifies containers below 60% occupancy before departure. Enables cargo consolidation across containers.

**Stack:** Python · pandas · pyodbc · SQL Server · numpy  
**Result:** USD 1.3M saved in year one through cargo consolidation

---

### `released.py` — SAP S/4 release report extractor
Selenium bot that logs into SAP S/4, filters deliveries by sales organization and date range, bulk-selects the results, and extracts the report to a local Excel file for further processing.

**Stack:** Python · Selenium · pyautogui · pyperclip

---

## Setup

```bash
git clone https://github.com/CoteeMiguel/supply-chain-automation
cd supply-chain-automation
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
# TMS credentials
TMS_USER=your_username
TMS_PASSWORD=your_password

# URLs
TTURL_login=https://tmstracking.dhl.com/.../login_clientes.asp
TTURL_filter=https://tmstracking.dhl.com/.../reporte.asp?...
URL_S4=https://your-sap-instance/FioriLaunchpad.html#Shell-home

# Local paths
PATH_DRIVER=path/to/chromedriver.exe
PATH_ZNETCO=path/to/znetco.xlsx
PATH_OUTPUT=path/to/output.xlsx
PATH_STATUS=path/to/statusagregado.xlsx
PATH_BBDD=path/to/BBDD.xlsx

# Email recipients
EMAIL_LSP=contact@lsp.com
EMAIL_HP=person1@hp.com;person2@hp.com

# SQL Server (TarrosCapacity)
DB_SERVER=your_server
DB_DATABASE=your_database
PATH_DMR=path/to/dmr.xlsx
PATH_SEGMENTOS=path/to/segmentos.xlsx
```

> The `.env` file is in `.gitignore` and must **never** be committed to the repository.

---

## Dependencies

```
pandas>=1.3
openpyxl
requests
selenium
workdays
python-dotenv
pywin32
pyodbc
numpy
```

---

## Portfolio Note

These scripts are the Python layer of a broader system. Other components (not included here as they are the Fortune 500 Technology Leader proprietary configurations) are:

- **Power Automate** — orchestrates daily execution and sends additional notifications
- **Power BI** — regional dashboards consuming the processed Excel files
- **SAP S/4** — source of order and delivery data
- **Global Logistics Provider TMS** — source of transport status data

---

## Author

**Jose Miguel Varas*  
Supply Chain & Operations Automation 
[linkedin.com/in/your-profile](https://linkedin.com/in/jmvaras/) · [github.com/your-username](https://github.com/CoteeMiguel)
