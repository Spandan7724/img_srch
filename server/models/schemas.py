# server/models/schemas.py
from pydantic import BaseModel


class Query(BaseModel):
    query: str


class SearchResult(BaseModel):
    path: str
    score: float
    full_url: str


class FilePathRequest(BaseModel):
    path: str
