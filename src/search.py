import clip
from sklearn.metrics.pairwise import cosine_similarity
import torch
from src.database import fetch_all_embeddings
import numpy as np
from src.feature_extraction import device

def search_by_text(query_text, model, preprocess, db_path="embeddings/image_embeddings.db"):
    """Search for images by text query."""
    embeddings = fetch_all_embeddings(db_path)
    image_paths, stored_embeddings = zip(*embeddings)
    stored_embeddings = np.vstack(stored_embeddings)

    # Encode query text
    with torch.no_grad():
        query_embedding = model.encode_text(clip.tokenize([query_text]).to(device)).cpu().numpy()

    similarities = cosine_similarity(query_embedding, stored_embeddings).flatten()
    top_indices = np.argsort(similarities)[::-1][:10]

    results = [(image_paths[i], similarities[i]) for i in top_indices]
    return results
