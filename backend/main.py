from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import tasks, annotations, qc, stats, images


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Medical Imaging Annotation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(annotations.router, prefix="/api/annotations", tags=["annotations"])
app.include_router(qc.router, prefix="/api/qc", tags=["qc"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(images.router, prefix="/api/images", tags=["images"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
