import os
import numpy as np
import torch
import open_clip
from PIL import Image
from fastapi import Request
import state as state
from urllib.parse import quote
import asyncio
import time
from typing import List
from .database import EmbeddingStore

device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
model = model.to(device)
tokenizer = open_clip.get_tokenizer('ViT-B-32')

IMAGE_DIR = "data/"
embedding_store = EmbeddingStore()

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
            except Exception as e:
                self.active_connections.remove(connection)
                print(f"Error sending message to connection: {e}")

manager = ConnectionManager()

async def process_image_batch(file_paths: list, store: EmbeddingStore) -> int:
    if not file_paths:
        return 0
    
    indexed_count = 0
    batch_images = []
    valid_paths = []
    
    for file_path in file_paths:
        try:
            image = Image.open(file_path)
            processed_image = preprocess(image)
            batch_images.append(processed_image)
            valid_paths.append(file_path)
        except Exception as e:
            print(f"Error loading image {file_path}: {e}")
            continue
    
    if not batch_images:
        return 0
    
    try:
        # Stack images into a batch tensor
        batch_tensor = torch.stack(batch_images).to(device)
        
        # Process entire batch with CLIP model
        with torch.no_grad():
            batch_embeddings = model.encode_image(batch_tensor).cpu().numpy()
        
        # Store embeddings in database
        for i, (file_path, embedding) in enumerate(zip(valid_paths, batch_embeddings)):
            try:
                embedding_reshaped = embedding.reshape(1, -1)
                if store.store_embedding(file_path, embedding_reshaped):
                    indexed_count += 1
                    print(f"Indexed: {file_path}")
            except Exception as e:
                print(f"Error storing embedding for {file_path}: {e}")
    
    except Exception as e:
        print(f"Error processing batch: {e}")
        for file_path in valid_paths:
            try:
                image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)
                with torch.no_grad():
                    embedding = model.encode_image(image).cpu().numpy()
                if store.store_embedding(file_path, embedding):
                    indexed_count += 1
                    print(f"Indexed (fallback): {file_path}")
            except Exception as fallback_e:
                print(f"Error in fallback processing {file_path}: {fallback_e}")
    
    return indexed_count

def extract_and_store_embeddings():
    start_time = time.time()
    
    image_paths = [
        os.path.join(IMAGE_DIR, img)
        for img in os.listdir(IMAGE_DIR)
        if img.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
    
    indexed_count = 0
    skipped_count = 0
    
    for image_path in image_paths:
        # Check if we need to reindex this file
        if not embedding_store.needs_reindexing(image_path):
            skipped_count += 1
            continue
            
        try:
            image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
            with torch.no_grad():
                embedding = model.encode_image(image).cpu().numpy()
            
            if embedding_store.store_embedding(image_path, embedding):
                indexed_count += 1
                print(f"Indexed: {image_path}")
            
        except Exception as e:
            print(f"Error embedding {image_path}: {e}")

    elapsed_time = time.time() - start_time
    print(f"Embeddings extracted for default folder. Added: {indexed_count}, Skipped: {skipped_count} (already in database) - Time taken: {elapsed_time:.2f}s")

def count_images_in_folder(folder_path: str) -> int:
    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                count += 1
    return count

async def index_folder_async(folder_path: str):
    start_time = time.time()  
    try:
        state.set_indexing_status(True, folder_path)
        state.reset_indexing_progress()
        # Notify WebSocket clients that indexing has started
        await manager.broadcast({
            "type": "indexing_started",
            "folder": folder_path,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        print(f"Indexing folder: {folder_path}")
    
        total_images = count_images_in_folder(folder_path)
        processed_count = 0
        indexed_count = 0
        skipped_count = 0
        files_to_process = [] 
        
        # First pass: collect all files that need processing
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    full_path = os.path.join(root, file_name)
                    state.update_indexing_progress(full_path, processed_count, total_images)
                    if processed_count % 10 == 0 or processed_count == total_images - 1:
                        await manager.broadcast({
                            "type": "indexing_progress",
                            "folder": folder_path,
                            "current_file": os.path.basename(full_path),
                            "processed": processed_count,
                            "total": total_images,
                            "percentage": round((processed_count / total_images * 100), 2) if total_images > 0 else 0
                        })
                    if embedding_store.needs_reindexing(full_path):
                        files_to_process.append(full_path)
                    else:
                        skipped_count += 1
                    
                    processed_count += 1
        
        # Second pass: batch process collected files
        batch_size = 16  
        print(f"Found {len(files_to_process)} files to index, processing in batches of {batch_size}")
        
        for i in range(0, len(files_to_process), batch_size):
            batch = files_to_process[i:i + batch_size]
            batch_indexed = await process_image_batch(batch, embedding_store)
            indexed_count += batch_indexed
            
            # Update progress
            batch_end = min(i + batch_size, len(files_to_process))
            await manager.broadcast({
                "type": "indexing_progress",
                "folder": folder_path,
                "current_file": f"Batch {i//batch_size + 1}",
                "processed": batch_end,
                "total": len(files_to_process),
                "percentage": round((batch_end / len(files_to_process) * 100), 2) if len(files_to_process) > 0 else 0
            })
    
            await asyncio.sleep(0.01)
        
        # Set indexing status to completed
        state.set_indexing_status(False, folder_path)
        
        elapsed_time = time.time() - start_time
        
        # Broadcast completion notification
        await manager.broadcast({
            "type": "indexing_completed",
            "folder": folder_path,
            "total_indexed": indexed_count,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "message": f"Indexing complete for {os.path.basename(folder_path)}. Added: {indexed_count}, Skipped: {skipped_count} (already in database). You can now search for images."
        })
        
        print(f"Indexing completed for {folder_path}. Added: {indexed_count}, Skipped: {skipped_count} (already in database) - Time taken: {elapsed_time:.2f}s")
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error indexing folder {folder_path}: {str(e)} - Time taken: {elapsed_time:.2f}s"
        print(error_msg)
        state.set_indexing_status(False, folder_path, error_msg)
        await manager.broadcast({
            "type": "indexing_error",
            "folder": folder_path,
            "error": error_msg,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        raise

def process_image_batch_sync(file_paths: list, store: EmbeddingStore) -> int:
    if not file_paths:
        return 0
    
    indexed_count = 0
    batch_images = []
    valid_paths = []
    
    # Load all images in the batch
    for file_path in file_paths:
        try:
            image = Image.open(file_path)
            processed_image = preprocess(image)
            batch_images.append(processed_image)
            valid_paths.append(file_path)
        except Exception as e:
            print(f"Error loading image {file_path}: {e}")
            continue
    
    if not batch_images:
        return 0
    
    try:
        # Stack images into a batch tensor
        batch_tensor = torch.stack(batch_images).to(device)
        
        # Process entire batch with CLIP model
        with torch.no_grad():
            batch_embeddings = model.encode_image(batch_tensor).cpu().numpy()
        
        # Store embeddings in database
        for i, (file_path, embedding) in enumerate(zip(valid_paths, batch_embeddings)):
            try:
                # Reshape embedding to match expected format
                embedding_reshaped = embedding.reshape(1, -1)
                if store.store_embedding(file_path, embedding_reshaped):
                    indexed_count += 1
                    print(f"Indexed: {file_path}")
            except Exception as e:
                print(f"Error storing embedding for {file_path}: {e}")
    
    except Exception as e:
        print(f"Error processing batch: {e}")
        # Fallback to individual processing if batch fails
        for file_path in valid_paths:
            try:
                image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)
                with torch.no_grad():
                    embedding = model.encode_image(image).cpu().numpy()
                if store.store_embedding(file_path, embedding):
                    indexed_count += 1
                    print(f"Indexed (fallback): {file_path}")
            except Exception as fallback_e:
                print(f"Error in fallback processing {file_path}: {fallback_e}")
    
    return indexed_count

def index_folder(folder_path: str):
    start_time = time.time()
    print(f"Indexing folder: {folder_path}")
    indexed_count = 0
    skipped_count = 0
    files_to_process = []
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                full_path = os.path.join(root, file_name)
                
                if embedding_store.needs_reindexing(full_path):
                    files_to_process.append(full_path)
                else:
                    skipped_count += 1
    batch_size = 16
    print(f"Found {len(files_to_process)} files to index, processing in batches of {batch_size}")
    
    for i in range(0, len(files_to_process), batch_size):
        batch = files_to_process[i:i + batch_size]
        batch_indexed = process_image_batch_sync(batch, embedding_store)
        indexed_count += batch_indexed
    
    elapsed_time = time.time() - start_time
    print(f"Indexing completed. Added: {indexed_count}, Skipped: {skipped_count} (already in database) - Time taken: {elapsed_time:.2f}s")

def search_images(query_text: str, request: Request):
    # Given a query text, compute its embedding, then find the top 5 most
    # similar images from our persistent embeddings store.
    try:
        # Quick check - try to get first embedding to see if store is empty
        has_embeddings = any(True for _ in embedding_store.get_all_embeddings())
        if not has_embeddings:
            return []
    except Exception as e:
        print(f"Error checking embeddings: {e}")
        return []

    # Encode the query text
    with torch.no_grad():
        text_tokens = tokenizer([query_text]).to(device)
        text_features = model.encode_text(text_tokens).cpu().numpy()

    # Calculate cosine similarity
    similarities = {}
    try:
        for image_path, embedding in embedding_store.get_all_embeddings():
            # embedding shape: (1, 512); text_features shape: (1, 512)
            cosine_sim = np.dot(text_features, embedding.T) / (
                np.linalg.norm(text_features) * np.linalg.norm(embedding)
            )
            similarities[image_path] = cosine_sim[0][0]
    except Exception as e:
        print(f"Error calculating similarities: {e}")
        return []

    # Sort and take top 5
    sorted_results = sorted(similarities.items(),
                            key=lambda x: x[1], reverse=True)[:5]

    # Format results
    results = []
    for path, score in sorted_results:
        # Convert cosine (−1…+1) → percentile (0…1)
        percentile = (score + 1.0) / 2.0
        try:
            if os.path.isabs(path):
                if state.current_image_dir and os.path.exists(state.current_image_dir):
                    try:
                        relative_path = os.path.relpath(path, state.current_image_dir)
                        if relative_path.startswith('..'):
                            relative_path = os.path.basename(path)
                    except (ValueError, OSError):
                        relative_path = os.path.basename(path)
                else:
                    relative_path = os.path.basename(path)
            else:
                full_test_path = os.path.join(state.current_image_dir or "", path)
                if os.path.exists(full_test_path):
                    relative_path = path
                else:
                    filename = os.path.basename(path)
                    full_test_path = os.path.join(state.current_image_dir or "", filename)
                    if os.path.exists(full_test_path):
                        relative_path = filename
                    else:
                        relative_path = path
                        print(f"WARNING: Cannot resolve path - Original: {path}, Current dir: {state.current_image_dir}")
                        
        except Exception as e:
            print(f"ERROR: Path resolution failed for {path}: {e}")
            relative_path = os.path.basename(path)
        
        unix_path = relative_path.replace(os.sep, "/")
        safe_path = quote(unix_path)
        full_url = f"{request.base_url}images/{safe_path}"
        results.append({
            "path": path,
            "score": float(percentile),
            "full_url": full_url
        })
    return results
