from src.feature_extraction import index_images

if __name__ == "__main__":
    image_dir = "data/"  # Folder containing images
    index_images(image_dir)
    print("Image embeddings indexed successfully!")
