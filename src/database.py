import sqlite3
import numpy as np

def init_db(db_path="embeddings/image_embeddings.db"):
    """Initialize the database and create embeddings table if not exists."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT UNIQUE,
            embedding BLOB
        )
    ''')
    conn.commit()
    conn.close()

def insert_embedding(image_path, embedding, db_path="embeddings/image_embeddings.db"):
    """Insert image embedding into the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO embeddings (image_path, embedding)
        VALUES (?, ?)
    ''', (image_path, embedding.tobytes()))
    conn.commit()
    conn.close()

def fetch_all_embeddings(db_path="embeddings/image_embeddings.db"):
    """Fetch all embeddings from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT image_path, embedding FROM embeddings')
    rows = cursor.fetchall()
    conn.close()

    # Decode the embeddings
    results = [(row[0], np.frombuffer(row[1], dtype=np.float32)) for row in rows]
    return results
