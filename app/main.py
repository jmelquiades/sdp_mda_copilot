"""FastAPI entrypoint for Criteria ServiceDesk Copilot API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.ia import router as ia_router
from app.api.me import router as me_router
from app.api.tickets import router as tickets_router
from app.api.experience import router as experience_router
from app.core.config import settings

app = FastAPI(title="Criteria ServiceDesk Copilot API")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(me_router)
app.include_router(tickets_router)
app.include_router(ia_router)
app.include_router(experience_router)
