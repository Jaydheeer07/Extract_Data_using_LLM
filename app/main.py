import logging
import logging.config

from fastapi import FastAPI

from app.config import settings
from app.logging_settings import default_settings
from app.routes import extract_llm

logging.config.dictConfig(default_settings)
app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(extract_llm.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
