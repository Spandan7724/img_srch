# server/routes/folders.py
import os
import asyncio
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List

from services.embeddings import index_folder_async
from services.watcher import add_watcher
from state import watched_folders, get_indexing_status
from services.embeddings import embeddings_db

# Dynamically determine the base directory
BASE_DIRECTORIES = [
    os.path.expanduser("~"),            # User home directory
    os.path.abspath(os.getcwd())        # Current working directory
]


class FoldersRequest(BaseModel):
    folders: List[str]


router = APIRouter()


@router.post("/folders", tags=["Folder Management"], summary="Add folders to index and watch")
async def set_folders(request: Request, body: FoldersRequest, background_tasks: BackgroundTasks):
    global watched_folders
    
    # Check if already indexing
    status = get_indexing_status()
    if status["is_indexing"]:
        raise HTTPException(
            status_code=409,
            detail=f"Already indexing folder: {status['current_folder']}. Please wait for completion."
        )
    
    added_folders = []

    for folder in body.folders:
        full_path = None

        # Try resolving the folder using different base directories
        for base in BASE_DIRECTORIES:
            possible_path = os.path.join(base, folder)
            if os.path.isdir(possible_path):
                full_path = possible_path
                break

        if full_path is None:
            raise HTTPException(
                status_code=400,
                detail=f"Folder does not exist: {folder}"
            )

        try:
            print(f"Starting indexing for folder: {full_path}")
            
            # Start async indexing in background
            background_tasks.add_task(index_folder_async, full_path)

            if full_path not in watched_folders:
                add_watcher(full_path, embeddings_db)
                watched_folders.append(full_path)
                print(f"Watcher started on: {full_path}")

            added_folders.append(full_path)
        except Exception as e:
            print(f"Error processing folder {full_path}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing folder {full_path}: {e}"
            )

    return {
        "status": "success",
        "added_folders": added_folders,
        "watched_folders": list(watched_folders),
        "message": f"Indexing started for {len(added_folders)} folder(s). Check status or connect to WebSocket for progress updates."
    }


@router.get("/indexing-status", tags=["Folder Management"], summary="Get current indexing status")
async def get_indexing_status_endpoint():
    """Get the current indexing status including progress information."""
    return get_indexing_status()


@router.post("/reindex/", tags=["Folder Management"], summary="Reindex all watched folders")
async def reindex_all_folders(request: Request, background_tasks: BackgroundTasks):
    global watched_folders, embeddings_db
    
    # Check if already indexing
    status = get_indexing_status()
    if status["is_indexing"]:
        raise HTTPException(
            status_code=409,
            detail=f"Already indexing folder: {status['current_folder']}. Please wait for completion."
        )
    
    embeddings_db.clear()

    # Re-index all watched folders (recursive)
    for folder in watched_folders:
        background_tasks.add_task(index_folder_async, folder)

    return {"status": "success", "message": "Re-indexing started for all watched folders. Check status for progress."}
