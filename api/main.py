from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from api.database import get_db
from api import crud, schemas

app = FastAPI(
    title="Medical Telegram Analytics API",
    description="Analytical API exposing insights from the Telegram medical data warehouse",
    version="1.0.0"
)

# ------------------ ENDPOINTS ------------------

@app.get(
    "/api/reports/top-products",
    response_model=List[schemas.TopProduct],
    summary="Top mentioned products or terms"
)
def top_products(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return crud.get_top_products(db, limit)


@app.get(
    "/api/channels/{channel_name}/activity",
    response_model=List[schemas.ChannelActivity],
    summary="Channel posting activity and engagement trends"
)
def channel_activity(channel_name: str, db: Session = Depends(get_db)):
    results = crud.get_channel_activity(db, channel_name)
    if not results:
        raise HTTPException(status_code=404, detail="Channel not found")
    return results


@app.get(
    "/api/search/messages",
    response_model=List[schemas.MessageSearchResult],
    summary="Search messages by keyword"
)
def search_messages(
    query: str = Query(..., min_length=3),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return crud.search_messages(db, query, limit)


@app.get(
    "/api/reports/visual-content",
    response_model=List[schemas.VisualContentStat],
    summary="Visual content usage statistics across channels"
)
def visual_content_stats(db: Session = Depends(get_db)):
    return crud.get_visual_content_stats(db)
