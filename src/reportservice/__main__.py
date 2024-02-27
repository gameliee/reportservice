import uvicorn
from src.reportservice.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.reportservice.app:app",
        host=settings.HOST,
        reload=settings.DEBUG_MODE,
        port=settings.PORT,
        workers=settings.WORKERS,
    )
