# server/services/embeddings.py
import os
import numpy as np
import torch
import open_clip
from PIL import Image
from fastapi import Request
import state as state
from urllib.parse import quote
import asyncio
from typing import List

device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
model = model.to(device)
tokenizer = open_clip.get_tokenizer('ViT-B-32')

IMAGE_DIR = "data/"
embeddings_db = {}

# Connection manager for WebSocket notifications
class ConnectionManager:
    def __init__(self):
        self.active_connections: List = []

    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

def extract_and_store_embeddings():
    # Scans the default data/ folder for images (non-recursive),
    # encodes them, and stores in embeddings_db.

    global embeddings_db
    image_paths = [
        os.path.join(IMAGE_DIR, img)
        for img in os.listdir(IMAGE_DIR)
        if img.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
    for image_path in image_paths:
        if image_path not in embeddings_db:
            try:
                image = preprocess(Image.open(image_path)
                                   ).unsqueeze(0).to(device)
                with torch.no_grad():
                    embedding = model.encode_image(image).cpu().numpy()
                embeddings_db[image_path] = embedding
            except Exception as e:
                print(f"Error embedding {image_path}: {e}")

    print("Embeddings extracted for default folder.")

def count_images_in_folder(folder_path: str) -> int:
    """Count total number of images in a folder recursively."""
    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                count += 1
    return count

async def index_folder_async(folder_path: str):
    """Asynchronously index a folder with progress tracking and notifications."""
    global embeddings_db
    
    try:
        # Set indexing status to started
        state.set_indexing_status(True, folder_path)
        state.reset_indexing_progress()
        
        # Broadcast start notification
        await manager.broadcast({
            "type": "indexing_started",
            "folder": folder_path,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        print(f"Clearing embeddings and indexing new folder: {folder_path}")
        embeddings_db.clear()
        
        # Count total images first
        total_images = count_images_in_folder(folder_path)
        processed_count = 0
        
        # Index images with progress tracking
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    full_path = os.path.join(root, file_name)
                    
                    # Update progress
                    state.update_indexing_progress(full_path, processed_count, total_images)
                    
                    # Broadcast progress update every 10 files or on the last file
                    if processed_count % 10 == 0 or processed_count == total_images - 1:
                        await manager.broadcast({
                            "type": "indexing_progress",
                            "folder": folder_path,
                            "current_file": os.path.basename(full_path),
                            "processed": processed_count,
                            "total": total_images,
                            "percentage": round((processed_count / total_images * 100), 2) if total_images > 0 else 0
                        })
                    
                    if full_path not in embeddings_db:
                        try:
                            image = preprocess(Image.open(full_path)).unsqueeze(0).to(device)
                            with torch.no_grad():
                                embedding = model.encode_image(image).cpu().numpy()
                            embeddings_db[full_path] = embedding
                            print(f"Indexed: {full_path}")
                        except Exception as e:
                            print(f"Error embedding {full_path}: {e}")
                    
                    processed_count += 1
                    
                    # Allow other tasks to run
                    await asyncio.sleep(0.001)
        
        # Set indexing status to completed
        state.set_indexing_status(False, folder_path)
        
        # Broadcast completion notification
        await manager.broadcast({
            "type": "indexing_completed",
            "folder": folder_path,
            "total_indexed": processed_count,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "message": f"Indexing complete for {os.path.basename(folder_path)}. You can now search for images."
        })
        
        print(f"Indexing completed for {folder_path}. Total images indexed: {processed_count}")
        
    except Exception as e:
        error_msg = f"Error indexing folder {folder_path}: {str(e)}"
        print(error_msg)
        
        # Set error status
        state.set_indexing_status(False, folder_path, error_msg)
        
        # Broadcast error notification
        await manager.broadcast({
            "type": "indexing_error",
            "folder": folder_path,
            "error": error_msg,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        raise

def index_folder(folder_path: str):
    """Synchronous wrapper for backward compatibility."""
    # This is kept for any existing synchronous calls
    # For new implementations, use index_folder_async
    global embeddings_db
    print(f"Clearing embeddings and indexing new folder: {folder_path}")
    
    embeddings_db.clear() 

    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                full_path = os.path.join(root, file_name)
                if full_path not in embeddings_db:
                    try:
                        image = preprocess(Image.open(
                            full_path)).unsqueeze(0).to(device)
                        with torch.no_grad():
                            embedding = model.encode_image(image).cpu().numpy()
                        embeddings_db[full_path] = embedding
                        print(f"Indexed: {full_path}")
                    except Exception as e:
                        print(f"Error embedding {full_path}: {e}")

def search_images(query_text: str, request: Request):

    # Given a query text, compute its embedding, then find the top 5 most
    # similar images from our in-memory embeddings_db.

    if not embeddings_db:
        return []

    # Encode the query text
    with torch.no_grad():
        text_tokens = tokenizer([query_text]).to(device)
        text_features = model.encode_text(text_tokens).cpu().numpy()

    # Calculate cosine similarity
    similarities = {}
    for image_path, embedding in embeddings_db.items():
        # embedding shape: (1, 512); text_features shape: (1, 512)
        cosine_sim = np.dot(text_features, embedding.T) / (
            np.linalg.norm(text_features) * np.linalg.norm(embedding)
        )
        similarities[image_path] = cosine_sim[0][0]

    # Sort and take top 5
    sorted_results = sorted(similarities.items(),
                            key=lambda x: x[1], reverse=True)[:5]

    # Format results

    results = []
    for path, score in sorted_results:
        # Convert cosine (−1…+1) → percentile (0…1)
        percentile = (score + 1.0) / 2.0
        relative_path = os.path.relpath(path, state.current_image_dir)
        unix_path = relative_path.replace(os.sep, "/")
        safe_path = quote(unix_path)
        full_url = f"{request.base_url}images/{safe_path}"
        results.append({
            "path": path,
            "score": float(percentile),
            "full_url": full_url
        })
    return results
