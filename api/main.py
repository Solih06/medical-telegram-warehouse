from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from .database import get_db

app = FastAPI(
    title="Kara Solutions Medical Telegram Data API",
    description="Serving Layer for medical and cosmetics analytical trends in Ethiopia."
)

@app.get("/")
def health_check():
    return {"status": "operational", "message": "API Online"}

# Endpoint 1 — Top Products 
@app.get("/api/reports/top-products") [cite: 3029]
def get_top_products(limit: int = Query(10, ge=1), db: Session = Depends(get_db)):
    """Returns the most frequently mentioned terms/products across all channels."""
    query = text("""
        SELECT word, count 
        FROM (
            SELECT unnest(string_to_array(lower(message_text), ' ')) AS word, count(*) as count
            FROM analytics.fct_messages
            GROUP BY word
        ) sub
        WHERE length(word) > 4 AND word NOT IN ('about', 'there', 'their', 'would', 'https', 't.me/')
        ORDER BY count DESC
        LIMIT :limit;
    """)
    result = db.execute(query, {"limit": limit}).fetchall()
    return [{"product_term": r[0], "mention_count": r[1]} for r in result]

# Endpoint 2 — Channel Activity 
@app.get("/api/channels/{channel_name}/activity") [cite: 3032]
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """Returns posting activity and trends for a specific channel."""
    query = text("""
        SELECT d.full_date, count(f.message_id) as post_count, sum(f.view_count) as total_views
        FROM analytics.fct_messages f
        JOIN analytics.dim_channels c ON f.channel_key = c.channel_key
        JOIN analytics.dim_dates d ON f.date_key = d.date_key
        WHERE c.channel_name = :channel_name
        GROUP BY d.full_date
        ORDER BY d.full_date DESC;
    """)
    result = db.execute(query, {"channel_name": channel_name}).fetchall()
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found or has no activity data")
    return [{"date": str(r[0]), "posts": r[1], "views": r[2]} for r in result]

# Endpoint 3 — Message Search 
@app.get("/api/search/messages") [cite: 3035]
def search_messages(query: str = Query(..., min_length=2), limit: int = 20, db: Session = Depends(get_db)):
    """Searches for messages containing a specific keyword."""
    sql = text("""
        SELECT f.message_id, c.channel_name, f.message_text, f.view_count
        FROM analytics.fct_messages f
        JOIN analytics.dim_channels c ON f.channel_key = c.channel_key
        WHERE f.message_text ILIKE :search_query
        LIMIT :limit;
    """)
    result = db.execute(sql, {"search_query": f"%{query}%", "limit": limit}).fetchall()
    return [{"message_id": r[0], "channel_name": r[1], "text": r[2], "views": r[3]} for r in result]

# Endpoint 4 — Visual Content Stats 
@app.get("/api/reports/visual-content") [cite: 3038]
def get_visual_content_stats(db: Session = Depends(get_db)):
    """Returns statistics about image usage and categories across channels."""
    query = text("""
        SELECT image_category, count(*) as count
        FROM analytics.fct_image_detections
        GROUP BY image_category;
    """)
    result = db.execute(query).fetchall()
    return [{"category": r[0], "image_count": r[1]} for r in result]