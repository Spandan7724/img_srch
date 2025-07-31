# Copyright (c) 2025 Spandan Chavan
# All rights reserved.
# Unauthorized copying of this file, via any medium, is strictly prohibited.
# Proprietary and confidential.

# server/main.py

import os
import asyncio
import state as state
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.routing import Mount

from routes import folders, search, open_file, websocket, database
from services.embeddings import extract_and_store_embeddings, embedding_store, index_folder_async
from services.watcher import start_watcher
from state import watched_folders, current_image_dir

app = FastAPI()

# ─── Helpers ──────────────────────────────────────────────────────────────

BASE_IMAGE_DIR = os.path.expanduser("~")          # user's home dir fallback


def get_image_directory() -> str:
    return list(watched_folders)[-1] if watched_folders else BASE_IMAGE_DIR


def remount_static_files() -> None:
    """
    Unmount any existing StaticFiles routes and re-mount the latest folder
    at /images so URLs like /images/foo.jpg work consistently.
    """
    # 1) Remove old StaticFiles mounts
    app.router.routes = [
        r for r in app.router.routes
        if not (isinstance(r, Mount) and isinstance(r.app, StaticFiles))
    ]

    # 2) Pick the new folder
    image_dir = get_image_directory()
    state.current_image_dir = image_dir

    # 3) Mount at fixed prefix /images
    app.mount("/images", StaticFiles(directory=image_dir), name="images")
    print(f"Serving images from: {image_dir}   (mounted at /images)")


# ─── CORS ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────

app.include_router(search.router,   tags=["Search"])
app.include_router(open_file.router, tags=["File Operations"])
app.include_router(folders.router,  tags=["Folder Management"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(database.router, tags=["Database"])

# ─── Startup / Shutdown ──────────────────────────────────────────────────
observer = None  # file-system watcher handle


@app.on_event("startup")
async def startup_event():
    global observer
    
    # Only index default folder if no embeddings exist yet
    stats = embedding_store.get_stats()
    if stats["total_embeddings"] == 0:
        print("No embeddings found. Extracting embeddings for default folder...")
        extract_and_store_embeddings()
    else:
        print(f"Found {stats['total_embeddings']} existing embeddings. Skipping default folder indexing.")

    if BASE_IMAGE_DIR not in watched_folders:
        watched_folders.append(BASE_IMAGE_DIR)

    print("Starting watcher for default folder...")
    observer = start_watcher(BASE_IMAGE_DIR, embedding_store)

    remount_static_files()
    print("Startup complete.")


@app.on_event("shutdown")
def shutdown_event():
    if observer:
        observer.stop()
        observer.join()
        print("Watcher stopped.")


# ─── Manual re-mount endpoint ────────────────────────────────────────────
@app.post("/update-images/")
async def update_images():
    remount_static_files()
    current_folder = get_image_directory()
    return {"status": "success", "image_directory": current_folder, "message": "Static files remounted. Use /folders endpoint for indexing."}

