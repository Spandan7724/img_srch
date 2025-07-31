# server/services/watcher.py
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import numpy as np
import torch
from PIL import Image
from services.embeddings import model, preprocess, embeddings_db, device

observers = []  # We'll store references to all observers here


class ImageFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return  # Ignore folders

        ext = os.path.splitext(event.src_path)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            print(f"[WATCHER] Detected new image: {event.src_path}")
            if event.src_path not in embeddings_db:
                try:
                    with torch.no_grad():
                        image = preprocess(Image.open(
                            event.src_path)).unsqueeze(0).to(device)
                        embedding = model.encode_image(image).cpu().numpy()
                        embedding /= np.linalg.norm(embedding, keepdims=True)
                    embeddings_db[event.src_path] = embedding
                    print(f"[WATCHER] Successfully embedded: {event.src_path}")
                except Exception as e:
                    print(f"[WATCHER] Error processing {event.src_path}: {e}")


def start_watcher(folder_path, embeddings_db):

    # Start a watchdog observer for the given folder (non-recursive).
    # If you want recursive, change recursive=True below.
    # Returns the observer so it can be stopped.

    event_handler = ImageFolderHandler()
    observer = Observer()
    # If you want subfolders, set recursive=True
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    observers.append(observer)
    print(f"[WATCHER] File system watcher started for: {folder_path}")
    return observer


def add_watcher(folder_path, embeddings_db):

    # If not already watching folder_path, start a new observer.

    return start_watcher(folder_path, embeddings_db)


def stop_all_watchers():

    # Utility to stop all watchers if needed at shutdown.

    for obs in observers:
        obs.stop()
        obs.join()
    observers.clear()
    print("[WATCHER] All watchers stopped.")
