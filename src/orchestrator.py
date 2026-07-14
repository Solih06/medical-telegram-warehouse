import subprocess
from dagster import op, job, Definitions

@op [cite: 3059]
def scrape_telegram_data():
    """Runs the Telegram Scraper[cite: 3060]."""
    result = subprocess.run(["python", "src/scraper.py"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Scraper failed: {result.stderr}")

@op(ins={}) [cite: 3059]
def load_raw_to_postgres(context, start):
    """Loads raw JSON datasets into PostgreSQL[cite: 3061]."""
    result = subprocess.run(["python", "scripts/load_to_postgres.py"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Postgres raw loader failed: {result.stderr}")

@op(ins={}) [cite: 3059]
def run_yolo_enrichment(context, start):
    """Executes YOLO object detection on downloaded graphics[cite: 3063]."""
    result = subprocess.run(["python", "src/yolo_detect.py"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"YOLO script failed: {result.stderr}")

@op(ins={}) [cite: 3059]
def run_dbt_transformations(context, start_loader, start_yolo):
    """Executes dbt seed, run, and test[cite: 3062]."""
    # Seed YOLO csv first 
    subprocess.run(["dbt", "seed"], cwd="medical_warehouse")
    # Run models [cite: 3062]
    result = subprocess.run(["dbt", "run"], cwd="medical_warehouse", capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")

@job [cite: 3058, 3064]
def medical_warehouse_elt_pipeline():
    """Define dependencies between ops[cite: 3064, 3065]."""
    scraped = scrape_telegram_data()
    loaded = load_raw_to_postgres(scraped)
    enriched = run_yolo_enrichment(scraped)
    run_dbt_transformations(loaded, enriched)

defs = Definitions(
    jobs=[medical_warehouse_elt_pipeline]
)