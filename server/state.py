watched_folders: list[str] = []
current_image_dir: str = ""

def get_watched_folders():
    return list(watched_folders)


def add_watched_folder(folder):
    watched_folders.add(folder)
