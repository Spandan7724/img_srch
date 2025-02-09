# server/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from server.routes import folders, search, open_file
from server.services.embeddings import extract_and_store_embeddings, embeddings_db
from server.services.watcher import start_watcher
from server.state import watched_folders

app = FastAPI()

# Ensure a base directory exists
# Default to the user's home directory
BASE_IMAGE_DIR = os.path.expanduser("~")

# Function to dynamically determine the image serving directory


def get_image_directory():
    if watched_folders:
        # Serve the most recently selected folder
        return list(watched_folders)[-1]
    return BASE_IMAGE_DIR  # Fallback to the home directory

# Dynamically mount the latest image directory


def remount_static_files():
    global app
    image_dir = get_image_directory()

    if "images" in app.routes:
        # Remove existing mount
        app.routes = [route for route in app.routes if route.path != "/images"]
    app.mount("/images", StaticFiles(directory=image_dir),
              name="images")  # Mount new directory
    print(f"Serving images from: {image_dir}")


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routes
app.include_router(search.router, tags=["Search"])
app.include_router(open_file.router, tags=["File Operations"])
app.include_router(folders.router, tags=["Folder Management"])

observer = None  # Store the file system watcher for default folder


@app.on_event("startup")
async def startup_event():
    global watched_folders
    print("Extracting embeddings for existing images in default folder...")

    extract_and_store_embeddings()
    watched_folders.add(BASE_IMAGE_DIR)  # Start with base directory

    print("Starting filesystem watcher for default folder...")
    global observer
    # Watch base directory
    observer = start_watcher(BASE_IMAGE_DIR, embeddings_db)

    remount_static_files()  # Ensure correct folder is mounted
    print("Embeddings and default watcher are ready.")


@app.on_event("shutdown")
def shutdown_event():
    global observer
    if observer:
        observer.stop()
        observer.join()
        print("File system watcher stopped.")

# Endpoint to update image directory dynamically


@app.post("/update-images/")
async def update_images():
    remount_static_files()
    return {"status": "success", "image_directory": get_image_directory()}
