# Medical Telegram Data Warehouse Pipeline

[cite_start]An end-to-end ELT data pipeline built for **Kara Solutions** to scrape, clean, enrich, and expose insights from public Ethiopian medical Telegram channels[cite: 5, 8, 9]. [cite_start]This platform leverages a modern data stack consisting of **Telethon** (Scraping) [cite: 41][cite_start], **PostgreSQL** (Data Warehousing) [cite: 18][cite_start], **dbt** (Transformations) [cite: 45][cite_start], **YOLOv8** (Computer Vision Enrichment) [cite: 46][cite_start], **FastAPI** (Data API Serving) [cite: 47][cite_start], and **Dagster** (Orchestration)[cite: 48].

---

## 🏗️ Project Architecture & Data Flow

```text
[Telegram Public Channels]
        │ (Telethon Scraper Script)
        ▼
 📁 [Raw Data Lake] (JSON files partitioned by date + raw images)
        │ 
        ▼ (PostgreSQL Raw Loader)
 🛢️ [PostgreSQL: `raw` schema]
        │
        ├───► (YOLOv8 Computer Vision) ───► 🛢️ [PostgreSQL: `raw.image_detections`]
        │
        ▼ (dbt Models & SQL Transformations)
 🛢️ [PostgreSQL: `analytics` schema] ──► (Dimensional Star Schema: dim_dates, dim_channels, fct_messages)
        │
        ▼ (Serving Layer)
 🚀 [FastAPI REST Endpoints]
 ```

 ## 📂 Project Structure
Following enterprise standards, the repository is organized as follows:
```text
medical-telegram-warehouse/
├── .env                          # Local secrets (API keys, DB credentials) - [DO NOT COMMIT]
├── .gitignore                    # Prevents local datasets and venv tracking 
├── requirements.txt              # Standard Python library manifest 
├── README.md                     # Project documentation (this file) 
├── data/                         # Local Data Lake
│   └── raw/
│       ├── images/               # Raw downloaded product images 
│       └── telegram_messages/    # Daily-partitioned raw JSON files
├── dbt_project/                  # dbt configuration & SQL models folder 
│   ├── dbt_project.yml           # dbt project configurations
│   ├── profiles.yml              # Database profile and target outputs
│   └── models/
│       ├── staging/              # Cleaning and casting raw inputs
│       └── marts/                # Core analytical Star Schema
├── src/                          # System core source files
│   ├── scraper.py                # Telethon Telegram crawler 
│   └── orchestrator.py           # Dagster pipeline definitions
├── api/                          # Serving Layer
│   └── main.py                   # FastAPI Application 
├── scripts/                      # Independent helper automation scripts 
│   ├── load_to_postgres.py       # JSON database staging loader 
│   └── enrich_images.py          # YOLOv8 Computer Vision enrichment task 
├── logs/                         # Logging directory tracking scraper pipeline activity
└── notebooks/                    # Analytical and exploration notebooks 
```
## 🛠️ Tech Stack & Dependencies
Scraping & Ingestion: Telethon   
Warehouse Database: PostgreSQL   
Transformations Layer: dbt (Data Build Tool)  
Neural Network Enrichment: Ultralytics YOLOv8 (nano model)   
Serving API: FastAPI & Uvicorn   
Orchestrator: Dagster  

## 🚀 Setup and Installation
1. Prerequisite Environments
Python 3.10 to 3.12 installed on your machine.

PostgreSQL database instance running locally on port 5432.

2. Clone and Install Dependencies
```bash
# Clone the repository
git clone <your-repository-url>
cd medical-telegram-warehouse

# Set up and activate python virtual environment
python -m venv .venv
& .venv\Scripts\Activate.ps1

# Install system libraries
pip install --upgrade pip
pip install -r requirements.txt
```
3. Environment Variables (.env)
Create a .env file in the root directory to manage your Telegram credentials and local database passwords:
```bash
# Telegram API Credentials (from my.telegram.org) [cite: 116]
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here

# Database Configuration (PostgreSQL) [cite: 158]
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medical_dwh
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_SCHEMA=raw
```
## 📖 Pipeline Components & Execution
Task 1: Scrape Telegram Data
The ingestion script connects to Ethiopian medical Telegram channels (CheMed18, Lobeliacosmetics, and Tikvahpharma), downloads text metadata, downloads any product images attached to messages, and writes them partition-by-partition to your local files.
```bash
python src/scraper.py
```
Task 2: Load and Transform (dbt)
The loading stage takes raw JSON partitions and saves them to your database staging layer. Once staged, dbt takes over to run data cleansing, casting, testing, and materialized dimensional modeling in the warehouse.
```bash
# Load raw JSON files into raw.telegram_messages inside Postgres
python scripts/load_to_postgres.py

# Navigate to the dbt project directory
cd dbt_project

# Compile and execute the analytics star schema models (dim_channels, dim_dates, fct_messages)
dbt run

# Run schema validation and quality tests
dbt test
```
Task 3: Image Enrichment (YOLOv8)
The computer vision step scans your downloaded media, detects objects like bottles, packages, and pills, and saves the output to raw.image_detections in PostgreSQL to unlock deep analytical insights on imagery.
```bash
python scripts/enrich_images.py
```
Task 4: Expose Data via FastAPI
Start the serving layer to expose your transformed and enriched dimensional data to external users or dashboards:
```bash
uvicorn api.main:app --reload
```
Once started, you can access the interactive visual Swagger API documentation at: http://127.0.0.1:8000/docs.

Task 5: Automation & Orchestration (Dagster)
Rather than executing scripts sequentially by hand, trigger Dagster to monitor, schedule, and orchestrate dependencies among our pipeline assets dynamically:
```bash
dagster dev -f src/orchestrator.py
```
Open your web browser and navigate to http://localhost:3000 to inspect the interactive execution graph and run materialization pipelines with a single click.
## 📈 Analytical Star Schema Details
The transformed analytical models conform to a Star Schema pattern optimized for high-performance reporting queries: 
1. dim_channels (Dimension): Captures distinct properties of monitored channels, labeling their specific target category (e.g. Cosmetics & Aesthetics vs. Pharma & Medicine). 
 2. dim_dates (Dimension): Dynamic time breakdown mapping calendar entries down to year, quarter, month, calendar week, day of week, and weekend flags.  
 3. fct_messages (Fact): Central transaction table that brings together metric volumes (views, forwards) alongside product metadata, image storage paths, and visual product category mappings.  

 ## 🤝 Contribution & Task Tracking
We track system feature additions, environment fixes, and dbt developments using GitHub Issues and GitHub Projects. Please follow the Conventional Commits standards (e.g. feat(api): add endpoint) when submitting code reviews or pushing edits.
