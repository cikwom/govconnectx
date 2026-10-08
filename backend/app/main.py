from fastapi import FastAPI

from app.database import Base, engine
from app.routers.reports import router as reports_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="GovConnect Nigeria",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "GovConnect Nigeria API is running"
    }


app.include_router(reports_router)