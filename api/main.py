import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="Kara Solutions Medical Telegram Data API",
    description="An analytical API serving transformed Telegram messaging metrics and computer vision drug/product detections.",
    version="1.0.0"
)

def get_db_connection():
    """Establish connection to PostgreSQL using RealDictCursor for JSON-like output."""
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "medical_dwh"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        logging.error(f"Failed to connect to PostgreSQL database: {e}")
        raise HTTPException(status_code=500, detail="Database connection failure")

# Pydantic Schemas for validation
class ChannelSummary(BaseModel):
    channel_name: str
    channel_friendly_name: str
    channel_category: str

class MessageResponse(BaseModel):
    message_id: int
    channel_name: Optional[str] = None
    cleaned_text: Optional[str] = None
    has_media: bool
    image_path: Optional[str] = None
    visual_product_type: str
    views_count: int
    forwards_count: int

class DetectionResponse(BaseModel):
    detection_id: int
    channel_name: str
    image_path: str
    detected_class: str
    confidence_score: float
    processed_at: str

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "message": "Welcome to Kara Solutions Medical Analytics API",
        "endpoints": {
            "/api/channels": "List all active monitored channels",
            "/api/messages": "Get transformed analytical messages (supports filtering by channel and product type)",
            "/api/detections": "Get YOLOv8 enriched object detections from product images"
        }
    }

@app.get("/api/channels", response_model=List[ChannelSummary])
def get_channels():
    """Fetch all channel descriptions from the analytical dbt dimension table."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT channel_name, channel_friendly_name, channel_category FROM analytics.dim_channels;")
        channels = cur.fetchall()
        return channels
    except Exception as e:
        logging.error(f"Error fetching channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve channels from analytical warehouse")
    finally:
        cur.close()
        conn.close()

@app.get("/api/messages", response_model=List[MessageResponse])
def get_messages(
    channel: Optional[str] = Query(None, description="Filter by channel username"),
    product_type: Optional[str] = Query(None, description="Filter by visual product type (Pill, Cream, Other/Unspecified)"),
    limit: int = Query(50, ge=1, le=200, description="Limit output results")
):
    """Retrieve messages with views, forwards, and text analytics from the Fact table."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT 
            m.message_id, 
            c.channel_name, 
            m.cleaned_text, 
            m.has_media, 
            m.image_path, 
            m.visual_product_type, 
            m.views_count, 
            m.forwards_count 
        FROM analytics.fct_messages m
        JOIN analytics.dim_channels c ON m.channel_key = c.channel_key
        WHERE 1=1
    """
    params = []
    
    if channel:
        query += " AND c.channel_name = %s"
        params.append(channel)
    if product_type:
        query += " AND m.visual_product_type = %s"
        params.append(product_type)
        
    query += " LIMIT %s;"
    params.append(limit)

    try:
        cur.execute(query, tuple(params))
        messages = cur.fetchall()
        return messages
    except Exception as e:
        logging.error(f"Error retrieving analytics messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages from analytical warehouse")
    finally:
        cur.close()
        conn.close()

@app.get("/api/detections", response_model=List[DetectionResponse])
def get_detections(
    detected_class: Optional[str] = Query(None, description="Filter by object type detected (e.g., bottle, pill)"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence score threshold")
):
    """Fetch YOLOv8 object detection metadata directly from the enriched images table."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT 
            detection_id, 
            channel_name, 
            image_path, 
            detected_class, 
            confidence_score, 
            TO_CHAR(processed_at, 'YYYY-MM-DD HH24:MI:SS') as processed_at
        FROM raw.image_detections
        WHERE confidence_score >= %s
    """
    params = [min_confidence]
    
    if detected_class:
        query += " AND LOWER(detected_class) = LOWER(%s)"
        params.append(detected_class)
        
    query += " ORDER BY confidence_score DESC LIMIT 100;"

    try:
        cur.execute(query, tuple(params))
        detections = cur.fetchall()
        return detections
    except Exception as e:
        logging.error(f"Error retrieving image detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve computer vision results")
    finally:
        cur.close()
        conn.close()