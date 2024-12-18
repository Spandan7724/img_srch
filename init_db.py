from src.database import init_db
import os 
db_dir = 'embeddings'
db_path = os.path.join(db_dir, 'image_embeddings.db')

# Check if the directory exists; if not, create it
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Directory '{db_dir}' created.")
if __name__ == "__main__":
    init_db("embeddings/image_embeddings.db")
    print("Database initialized successfully!")
