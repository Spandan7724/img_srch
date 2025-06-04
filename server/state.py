watched_folders: list[str] = []
current_image_dir: str = ""

# Indexing status tracking
indexing_status = {
    "is_indexing": False,
    "current_folder": None,
    "progress": {
        "current_file": None,
        "processed_count": 0,
        "total_count": 0,
        "percentage": 0.0
    },
    "last_completed": None,
    "error": None
}

def get_watched_folders():
    return list(watched_folders)

def add_watched_folder(folder):
    watched_folders.append(folder)

def get_indexing_status():
    return indexing_status.copy()

def set_indexing_status(is_indexing: bool, folder: str = None, error: str = None):
    indexing_status["is_indexing"] = is_indexing
    indexing_status["current_folder"] = folder
    if error:
        indexing_status["error"] = error
    elif not is_indexing and folder:
        indexing_status["last_completed"] = folder
        indexing_status["error"] = None

def update_indexing_progress(current_file: str, processed: int, total: int):
    indexing_status["progress"]["current_file"] = current_file
    indexing_status["progress"]["processed_count"] = processed
    indexing_status["progress"]["total_count"] = total
    indexing_status["progress"]["percentage"] = (processed / total * 100) if total > 0 else 0.0

def reset_indexing_progress():
    indexing_status["progress"] = {
        "current_file": None,
        "processed_count": 0,
        "total_count": 0,
        "percentage": 0.0
    }
