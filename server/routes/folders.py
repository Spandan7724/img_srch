# server/routes/folders.py
import os
from fastapi import APIRouter, HTTPException, Request  # Import Request
from pydantic import BaseModel
from typing import List

from server.services.embeddings import index_folder
from server.services.watcher import add_watcher
from server.state import watched_folders
from server.services.embeddings import embeddings_db
router = APIRouter()

# Dynamically determine the base directory
BASE_DIRECTORIES = [
    # User home directory (Windows: C:/Users/username)
    os.path.expanduser("~"),
    # Current working directory (C:/Users/span/Code/img_srch)
    os.path.abspath(os.getcwd())
]


class FoldersRequest(BaseModel):
    folders: List[str]


router = APIRouter()



@router.post("/folders", tags=["Folder Management"], summary="Add folders to index and watch")
async def set_folders(request: Request, body: FoldersRequest):
    global watched_folders
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
                status_code=400, detail=f"Folder does not exist: {folder}")

        try:
            print(f"Indexing folder: {full_path}")
            index_folder(full_path)

            if full_path not in watched_folders:
                add_watcher(full_path, embeddings_db)
                watched_folders.append(full_path)
                print(f"Watcher started on: {full_path}")

            added_folders.append(full_path)
        except Exception as e:
            print(f"Error processing folder {full_path}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error processing folder {full_path}: {e}")

    return {"status": "success", "added_folders": added_folders, "watched_folders": list(watched_folders)}



@router.post("/reindex/", tags=["Folder Management"], summary="Reindex all watched folders")
async def reindex_all_folders(request: Request):

    # Re-indexes all known folders.

    global watched_folders
    global embeddings_db
    embeddings_db.clear()

    # Re-index all watched folders (recursive)
    for folder in watched_folders:
        index_folder(folder)

    return {"status": "success", "message": "Re-indexing complete."}
