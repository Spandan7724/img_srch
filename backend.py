import platform
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import numpy as np
import torch
import clip
from PIL import Image
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
import subprocess

from fastapi.staticfiles import StaticFiles
# Initialize FastAPI app
app = FastAPI()

# Load the CLIP model and preprocessing pipeline
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Directory where images are stored
IMAGE_DIR = "data/"

# Dummy database of embeddings for testing
embeddings_db = {}


current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "data")
# Mount static files to serve images
app.mount("/images", StaticFiles(directory="data"), name="images")
# Define input structure
class Query(BaseModel):
    query: str

# Define response structure
class SearchResult(BaseModel):
    path: str
    score: float
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL(s) in production
    allow_credentials=True,
    allow_methods=["*"],  # e.g., ["GET", "POST"]
    allow_headers=["*"],  # e.g., ["Content-Type", "Authorization"]
)
# Function to extract embeddings for all images
def extract_and_store_embeddings():
    global embeddings_db
    image_paths = [
        os.path.join(IMAGE_DIR, img) 
        for img in os.listdir(IMAGE_DIR) 
        if img.endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]

    for image_path in image_paths:
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = model.encode_image(image).cpu().numpy()
        embeddings_db[image_path] = embedding
        
        # Logging
        #     for image_path in image_paths:
        # try:
        #     image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
        #     with torch.no_grad():
        #         embedding = model.encode_image(image).cpu().numpy()
        #     embeddings_db[image_path] = embedding
        #     print(f"Successfully processed: {image_path}")
        # except Exception as e:
        #     print(f"Error processing {image_path}: {e}"

# Perform the search
@app.post("/search/", response_model=List[SearchResult])
async def search_images(query: Query) -> List[SearchResult]:
    # Tokenize and embed the query text
    with torch.no_grad():
        text_features = model.encode_text(clip.tokenize([query.query]).to(device)).cpu().numpy()

    # Compute cosine similarity
    similarities = {}
    for image_path, embedding in embeddings_db.items():
        cosine_sim = np.dot(text_features, embedding.T) / (
            np.linalg.norm(text_features) * np.linalg.norm(embedding)
        )
        similarities[image_path] = cosine_sim[0][0]  # First and only value

    # Sort and get top 5 results
    sorted_results = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:5]

    # Convert scores to float
    return [{"path": path, "score": float(score)} for path, score in sorted_results]

class FilePathRequest(BaseModel):
    path: str

# Update the open_file endpoint in your FastAPI backend
@app.post("/open-file/")
async def open_file(request: FilePathRequest):
    try:
        path = request.path
        # Log the received path
        print(f"Received request to open path: {path}")
        
        # Verify the path exists    
        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")

        system = platform.system()
        print(f"Operating system: {system}")

        try:
            if system == "Windows":
                # Use normalized path for Windows
                normalized_path = os.path.normpath(path)
                print(f"Opening directory: {os.path.dirname(normalized_path)}")
                os.startfile(os.path.dirname(normalized_path))
            elif system == "Darwin":  # macOS
                print(f"Opening file with 'open -R {path}'")
                subprocess.run(["open", "-R", path], check=True)
            elif system == "Linux":
                print(f"Opening directory with 'xdg-open {os.path.dirname(path)}'")
                subprocess.run(["xdg-open", os.path.dirname(path)], check=True)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported operating system: {system}")

            return {"status": "success", "message": f"Successfully opened {path}"}
        except subprocess.CalledProcessError as e:
            print(f"Subprocess error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to execute command: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        print(f"Error in open_file endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
# Populate embeddings on startup
@app.on_event("startup")
async def startup_event():
    print("Extracting embeddings...")
    extract_and_store_embeddings()
    print("Embeddings ready.")
