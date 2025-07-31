import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import numpy as np
import torch
from PIL import Image
from services.embeddings import model, preprocess, embedding_store, device

observers = []  


class ImageFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return  

        ext = os.path.splitext(event.src_path)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            print(f"[WATCHER] Detected new image: {event.src_path}")
            # Check if we need to reindex this file
            if embedding_store.needs_reindexing(event.src_path):
                try:
                    with torch.no_grad():
                        image = preprocess(Image.open(event.src_path)).unsqueeze(0).to(device)
                        embedding = model.encode_image(image).cpu().numpy()
                        embedding /= np.linalg.norm(embedding, keepdims=True)
                    
                    if embedding_store.store_embedding(event.src_path, embedding):
                        print(f"[WATCHER] Successfully embedded: {event.src_path}")
                except Exception as e:
                    print(f"[WATCHER] Error processing {event.src_path}: {e}")


def start_watcher(folder_path, embedding_store):

    event_handler = ImageFolderHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)
    observer.start()
    observers.append(observer)
    print(f"[WATCHER] File system watcher started for: {folder_path}")
    return observer


def add_watcher(folder_path, embedding_store):
    return start_watcher(folder_path, embedding_store)


def stop_all_watchers():
    for obs in observers:
        obs.stop()
        obs.join()
    observers.clear()
    print("[WATCHER] All watchers stopped.")
