"""FastAPI entrypoint for Criteria ServiceDesk Copilot API."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.ia import router as ia_router
from app.api.me import router as me_router
from app.api.tickets import router as tickets_router

app = FastAPI(title="Criteria ServiceDesk Copilot API")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(health_router)
app.include_router(me_router)
app.include_router(tickets_router)
app.include_router(ia_router)
