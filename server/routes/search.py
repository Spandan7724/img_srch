# server/routes/search.py
from fastapi import APIRouter, HTTPException, Request
from typing import List

from server.models.schemas import Query, SearchResult
from server.services.embeddings import search_images

router = APIRouter()


@router.post("/search/", response_model=List[SearchResult])
async def search_images_endpoint(query: Query, request: Request):
    try:
        results = search_images(query.query, request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
