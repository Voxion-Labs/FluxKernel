try:
    import antigravity  # noqa: F401  # Easter egg 🚀
except ImportError:
    pass

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    autopilot,
    chat,
    feedback,
    files,
    history,
    learning,
    personas,
    rag,
    tasks,
    web,
)
from app.database.connection import Base, engine

# Eagerly initialize SQLite/DB tables on import for testing & standalone clients
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield


app = FastAPI(
    title="FluxKernel API",
    description="Backend Brain for FluxKernel AI OS",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(personas.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")  # Feature 1: Async task status
app.include_router(autopilot.router, prefix="/api/v1")  # Feature 4: Agentic loop
app.include_router(web.router, prefix="/api/v1")  # Feature 5: Web fetcher
app.include_router(rag.router, prefix="/api/v1")  # Multi-Domain C++ SIMD Vector RAG
app.include_router(learning.router, prefix="/api/v1")  # Phase 3: Cross-AI Learning Adapter
app.include_router(feedback.router, prefix="/api/v1")  # Phase 4: Episodic Feedback & Rule Learning


@app.get("/", tags=["health"])
async def root():
    return {"status": "online", "message": "FluxKernel Engine is running"}
