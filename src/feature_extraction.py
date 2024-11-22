import numpy as np
import torch
import clip
from PIL import Image
from tqdm import tqdm
# import open_clip
from torch.amp import autocast
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)




def extract_image_embedding(image_path):
    """Generate image embedding using mixed precision."""
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with autocast():
        with torch.no_grad():
            embedding = model.encode_image(image)
    return embedding.cpu().numpy().astype(np.float32)


# model, _, preprocess = open_clip.create_model_and_transforms(
#     'MobileCLIP-S2', pretrained='datacompdr'
# )

# device = "cuda" if torch.cuda.is_available() else "cpu"
# model = model.to(device)



# def extract_image_embedding(image_path):
#     """Generate image embedding using MobileCLIP-S2."""
#     image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
#     with torch.no_grad():
#         embedding = model.encode_image(image)
#     return embedding.cpu().numpy().astype(np.float32)

def index_images(image_dir, db_path="embeddings/image_embeddings.db"):
    """Index all images in the directory and store embeddings in the database."""
    from src.database import insert_embedding, init_db
    import os

    init_db(db_path)

    image_paths = [os.path.join(image_dir, img) for img in os.listdir(image_dir) if img.endswith((".png", ".jpg", ".jpeg", ".webp"))]

    for image_path in tqdm(image_paths, desc="Indexing Images"):
        embedding = extract_image_embedding(image_path)
        insert_embedding(image_path, embedding)
