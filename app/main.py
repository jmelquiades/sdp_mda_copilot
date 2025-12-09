"""FastAPI entrypoint for Criteria ServiceDesk Copilot API."""

from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="Criteria ServiceDesk Copilot API")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(health_router)
