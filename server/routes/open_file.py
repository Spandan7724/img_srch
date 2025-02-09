# server/routes/open_file.py
import os
import platform
import subprocess
from fastapi import APIRouter, HTTPException

from server.models.schemas import FilePathRequest

router = APIRouter()


@router.post("/open-file/")
async def open_file(request: FilePathRequest):
    try:
        path = request.path
        print(f"Received request to open path: {path}")

        if not os.path.exists(path):
            print(f"Path does not exist: {path}")
            raise HTTPException(
                status_code=404, detail=f"Path not found: {path}")

        system = platform.system()
        print(f"Operating system: {system}")

        try:
            if system == "Windows":
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

    except Exception as e:
        print(f"Error in open_file endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/open-image/")
async def open_image(request: FilePathRequest):
    import os
    import platform
    import subprocess
    from fastapi import HTTPException

    path = request.path
    absolute_path = os.path.abspath(path)
    print(f"[DEBUG] Attempting to open: {absolute_path}")

    if not os.path.exists(absolute_path):
        raise HTTPException(
            status_code=404, detail=f"Path not found: {absolute_path}")

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(absolute_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", absolute_path], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", absolute_path], check=True)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported operating system: {system}"
            )
        return {"status": "success", "message": f"Opened image: {absolute_path}"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to open image: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
