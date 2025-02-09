import os
import subprocess
import platform
from fastapi import HTTPException


def open_file(path):
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    system = platform.system()
    print(f"Operating system: {system}")
    try:
        if system == "Windows":
            # Use normalized path for Windows
            normalized_path = os.path.normpath(path)
            print(f"Opening directory: {os.path.dirname(normalized_path)}")
            os.startfile(os.path.dirname(normalized_path))
        elif system == "Darwin":  # macOS
            print(f"Opening file with 'open -R {path}'")
            subprocess.run(["open", "-R", path], check=True)
        elif system == "Linux":
            print(
                f"Opening directory with 'xdg-open {os.path.dirname(path)}'")
            subprocess.run(["xdg-open", os.path.dirname(path)], check=True)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported operating system: {system}")

        return {"status": "success", "message": f"Successfully opened {path}"}
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to execute command: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
