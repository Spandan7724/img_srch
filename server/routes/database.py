from fastapi import APIRouter
from services.embeddings import embedding_store

router = APIRouter()

@router.get("/database/stats", tags=["Database"], summary="Get database statistics")
async def get_database_stats():
    stats = embedding_store.get_stats()
    return {
        "status": "success",
        **stats
    }

@router.post("/database/cleanup", tags=["Database"], summary="Clean up missing files")
async def cleanup_database():
    removed_count = embedding_store.cleanup_missing_files()
    return {
        "status": "success",
        "removed_embeddings": removed_count,
        "message": f"Cleaned up {removed_count} embeddings for missing files"
    }

@router.post("/database/clear", tags=["Database"], summary="Clear all embeddings from database")
async def clear_database():
    try:
        success = embedding_store.clear_embeddings()
        if success:
            return {
                "status": "success",
                "message": "All embeddings cleared from database",
                "warning": "Database is now empty. You will need to re-index your folders."
            }
        else:
            return {
                "status": "error",
                "message": "Failed to clear database"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to clear database: {str(e)}"
        }
