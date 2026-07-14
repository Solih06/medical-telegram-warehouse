import os
import subprocess
import logging
from dagster import asset, Definitions, AssetExecutionContext

# Setup logging inside Dagster's execution context
logging.basicConfig(level=logging.INFO)

@asset(group_name="extract_and_load")
def scrape_telegram_data(context: AssetExecutionContext):
    """Asset 1: Scrapes public medical channels on Telegram and saves raw JSON partitions."""
    context.log.info("Starting Telegram Scraping Asset...")
    
    # Execute our scraper script in a subprocess
    result = subprocess.run(
        ["python", "src/scraper.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        context.log.error(f"Scraper failed: {result.stderr}")
        raise Exception("Telegram scraper failed execution.")
        
    context.log.info("Telegram scraper completed successfully.")
    context.log.info(result.stdout)


@asset(deps=[scrape_telegram_data], group_name="extract_and_load")
def load_raw_data_to_postgres(context: AssetExecutionContext):
    """Asset 2: Loads the scraped JSON partitions into raw staging tables in PostgreSQL."""
    context.log.info("Starting database load stage...")
    
    result = subprocess.run(
        ["python", "scripts/load_to_postgres.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        context.log.error(f"Database loading failed: {result.stderr}")
        raise Exception("Database raw loader failed execution.")
        
    context.log.info("Raw data loaded to PostgreSQL staging warehouse.")
    context.log.info(result.stdout)


@asset(deps=[load_raw_data_to_postgres], group_name="enrichment")
def enrich_images_yolo(context: AssetExecutionContext):
    """Asset 3: Uses YOLOv8 to detect objects inside downloaded pharmaceutical images and saves the metadata."""
    context.log.info("Starting YOLOv8 image detection enrichment...")
    
    result = subprocess.run(
        ["python", "scripts/enrich_images.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        context.log.error(f"Image enrichment failed: {result.stderr}")
        raise Exception("Computer vision enrichment failed execution.")
        
    context.log.info("Image object detection enrichment task complete.")
    context.log.info(result.stdout)


@asset(deps=[load_raw_data_to_postgres], group_name="transformations")
def run_dbt_transformations(context: AssetExecutionContext):
    """Asset 4: Runs dbt models to materialize our clean Star Schema (Marts) in PostgreSQL."""
    context.log.info("Initiating dbt SQL transformations inside warehouse...")
    
    # Run dbt compile and run commands targeting our dbt_project folder
    result = subprocess.run(
        ["dbt", "run"],
        cwd="dbt_project",
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        context.log.error(f"dbt run failed: {result.stderr}")
        raise Exception("dbt transformation execution failed.")
        
    context.log.info("dbt models compiled and materialized successfully.")
    context.log.info(result.stdout)


# Wrap our assets in a unified Dagster Definitions container
defs = Definitions(
    assets=[
        scrape_telegram_data,
        load_raw_data_to_postgres,
        enrich_images_yolo,
        run_dbt_transformations
    ]
)