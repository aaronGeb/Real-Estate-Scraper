# Real Estate Scraper

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-REST_API-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Playwright](https://img.shields.io/badge/Playwright-Web_Scraping-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)




## Overview

This project automates the collection and management of residential property listings from multiple real estate platforms.

The pipeline:

<ol type="1">
<li>Scrapes listings from Zillow and Redfin</li>
<li>Extracts and normalizes property information</li>
<li>Stores records in PostgreSQL</li>
<li>Tracks every observed price change</li>
<li>Exposes data through a REST </li>
<li>Supports scheduled scraping and reporting exports</li>
</ol>

## Features

| Feature                    | Details                                                         |
| -------------------------- | --------------------------------------------------------------- |
| **Multi-source scraping**  | Zillow + Redfin with Playwright (handles JS-rendered pages)     |
| **Price history tracking** | Every price change is recorded with timestamp and event type    |
| **Automated scheduling**   | APScheduler runs scrapes on a configurable cron schedule        |
| **REST API**               | FastAPI with filtering, pagination, and price summary endpoints |
| **CSV / Excel export**     | One-command data export for reporting                           |
| **Robust error handling**  | Tenacity retry logic, per-source error isolation                |
| **Structured logging**     | Loguru with file rotation                                       |

---

## Project Structure

```
real_estate_scraper/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
│
├── scraper/
│   ├── zillow.py
│   ├── redfin.py
│   └── runner.py
│
├── db/
│   ├── models.py
│   ├── database.py
│   └── crud.py
│
├── api/
│   ├── routes.py
│   └── schemas.py
│
├── scheduler/
│   └── scheduler.py
│
└── exports/
    └── exporter.py
```


##  Quick Start

### 1. Clone and install

```bash
git clone https://github.com/aarongeb/real-estate-scraper.git
cd real-estate-scraper

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials and target cities
```

### 3. Set up PostgreSQL

```bash
createdb real_estate_db
# Tables are created automatically on first run
```

### 4. Run a manual scrape

```bash
python scraper/runner.py
```

### 5. Start the API

```bash
python main.py
# Visit http://localhost:8000/docs for interactive API docs
```

### 6. Start the scheduler

```bash
python scheduler/scheduler.py
```

### 7. Export data

```bash
python exports/exporter.py --format excel --city "New York"
python exports/exporter.py --format csv --state CA
```

---

##  API Endpoints

| Method | Endpoint                      | Description                             |
| ------ | ----------------------------- | --------------------------------------- |
| `GET`  | `/api/v1/properties`          | List all properties with filters        |
| `GET`  | `/api/v1/properties/{id}`     | Property detail with full price history |
| `GET`  | `/api/v1/stats`               | Overall scrape run statistics           |
| `GET`  | `/api/v1/stats/cities`        | Property counts by city                 |
| `GET`  | `/api/v1/stats/price-summary` | Avg/min/max price for a city            |
| `POST` | `/api/v1/scrape/trigger`      | Manually trigger a scrape               |
| `GET`  | `/health`                     | Health check                            |

### Example Queries

```bash
# Properties in Austin under $500k with 3+ beds
GET /api/v1/properties?city=Austin&state=TX&max_price=500000&min_beds=3

# Price summary for Los Angeles
GET /api/v1/stats/price-summary?city=Los+Angeles&state=CA

# Full history for property ID 42
GET /api/v1/properties/42
```

---

## Database Schema

```
properties          — core listing data (one row per unique property)
price_history       — every price observation with timestamp
scrape_logs         — audit log for every scrape run
```

---

## Configuration

All settings are controlled via `.env`:

| Variable                | Default                      | Description                    |
| ----------------------- | ---------------------------- | ------------------------------ |
| `TARGET_CITIES`         | `New York NY,Los Angeles CA` | Cities to scrape               |
| `SCRAPE_CRON`           | `0 2 * * *`                  | Cron schedule                  |
| `REQUEST_DELAY_MIN/MAX` | `2` / `5`                    | Seconds between requests       |
| `DB_*`                  | —                            | PostgreSQL connection settings |

---

## Tech Stack

- **Python 3.11+**
- **Playwright**
- **BeautifulSoup4**
- **SQLAlchemy 2.0**
- **PostgreSQL**
- **FastAPI**
- **APScheduler**
- **Tenacity**
- **Loguru**
- **Pandas**

---

## Legal & Ethical Notes

- Respects `robots.txt` intent — uses configurable delays between requests
- For **personal/educational use** only
- Do not use to collect PII or re-sell data
- Check each site's Terms of Service before production use

---
