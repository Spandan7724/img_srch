# server/services/embeddings.py
import os
import numpy as np
import torch
import clip
from PIL import Image
from fastapi import Request
import server.state as state
from urllib.parse import quote

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

IMAGE_DIR = "data/"
embeddings_db = {}


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



    # Recursively scans the given folder for images,
    # encodes them, and adds them to embeddings_db if not present.


def index_folder(folder_path: str):
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
        text_features = model.encode_text(
            clip.tokenize([query_text]).to(device)
        ).cpu().numpy()

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
        relative_path = os.path.relpath(path, state.current_image_dir)
        unix_path = relative_path.replace(os.sep, "/")
        safe_path = quote(unix_path)
        full_url = f"{request.base_url}images/{safe_path}"
        results.append({
            "path": path,
            "score": float(score),
            "full_url": full_url
        })
    return results
