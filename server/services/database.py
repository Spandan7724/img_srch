import sqlite3
import pickle
import hashlib
import os
from typing import Optional, Iterator, Tuple
from datetime import datetime
import numpy as np
from pathlib import Path


class EmbeddingStore:
    def __init__(self, db_path: str = "embeddings/embeddings.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    file_path TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    file_hash TEXT NOT NULL,
                    last_modified TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash 
                ON embeddings(file_hash)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_modified 
                ON embeddings(last_modified)
            """)
            
            conn.commit()
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for change detection."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, IOError):
            # If we can't read the file, return a timestamp-based hash
            return hashlib.md5(str(datetime.now()).encode()).hexdigest()
    
    def _get_file_mtime(self, file_path: str) -> datetime:
        """Get file modification time."""
        try:
            return datetime.fromtimestamp(os.path.getmtime(file_path))
        except (OSError, IOError):
            return datetime.now()
    
    def store_embedding(self, file_path: str, embedding: np.ndarray) -> bool:
        try:
            file_hash = self._get_file_hash(file_path)
            last_modified = self._get_file_mtime(file_path)
            embedding_blob = pickle.dumps(embedding)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO embeddings 
                    (file_path, embedding, file_hash, last_modified)
                    VALUES (?, ?, ?, ?)
                """, (file_path, embedding_blob, file_hash, last_modified))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error storing embedding for {file_path}: {e}")
            return False
    
    def get_embedding(self, file_path: str) -> Optional[np.ndarray]:
        """
        Retrieve an embedding from the database.
        
        Args:
            file_path: Full path to the image file
            
        Returns:
            NumPy array containing the embedding, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT embedding FROM embeddings WHERE file_path = ?
                """, (file_path,))
                
                row = cursor.fetchone()
                if row:
                    return pickle.loads(row[0])
                return None
        except Exception as e:
            print(f"Error retrieving embedding for {file_path}: {e}")
            return None
    
    def get_all_embeddings(self) -> Iterator[Tuple[str, np.ndarray]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_path, embedding FROM embeddings
                """)
                
                for row in cursor:
                    file_path, embedding_blob = row
                    try:
                        embedding = pickle.loads(embedding_blob)
                        yield file_path, embedding
                    except Exception as e:
                        print(f"Error unpickling embedding for {file_path}: {e}")
                        continue
        except Exception as e:
            print(f"Error retrieving all embeddings: {e}")
    
    def embedding_exists(self, file_path: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 1 FROM embeddings WHERE file_path = ? LIMIT 1
                """, (file_path,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking embedding existence for {file_path}: {e}")
            return False
    
    def needs_reindexing(self, file_path: str) -> bool:
        if not self.embedding_exists(file_path):
            return True
        
        try:
            current_hash = self._get_file_hash(file_path)
            current_mtime = self._get_file_mtime(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_hash, last_modified FROM embeddings 
                    WHERE file_path = ?
                """, (file_path,))
                
                row = cursor.fetchone()
                if not row:
                    return True
                
                stored_hash, stored_mtime_str = row
                stored_mtime = datetime.fromisoformat(stored_mtime_str.replace('Z', '+00:00')) if isinstance(stored_mtime_str, str) else stored_mtime_str
                
                # Check if file has been modified
                return (current_hash != stored_hash or 
                       current_mtime > stored_mtime)
                
        except Exception as e:
            print(f"Error checking if {file_path} needs reindexing: {e}")
            return True  # If in doubt, re-index
    
    def remove_embedding(self, file_path: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM embeddings WHERE file_path = ?
                """, (file_path,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error removing embedding for {file_path}: {e}")
            return False
    
    def clear_embeddings(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM embeddings")
                conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing embeddings: {e}")
            return False
    
    def cleanup_missing_files(self) -> int:
        removed_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT file_path FROM embeddings")
                all_paths = [row[0] for row in cursor.fetchall()]
                
                for file_path in all_paths:
                    if not os.path.exists(file_path):
                        conn.execute("DELETE FROM embeddings WHERE file_path = ?", (file_path,))
                        removed_count += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        return removed_count
    
    def get_stats(self) -> dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
                total_embeddings = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM embeddings 
                    WHERE created_at >= datetime('now', '-1 day')
                """)
                recent_embeddings = cursor.fetchone()[0]
                
                return {
                    "total_embeddings": total_embeddings,
                    "recent_embeddings": recent_embeddings,
                    "database_path": str(self.db_path),
                    "database_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {"error": str(e)}
    