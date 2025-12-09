# Criteria ServiceDesk Copilot – API (V1)

Esqueleto FastAPI + Alembic para el Hito 1 (conexión a PostgreSQL y `/health`).

## Configuración rápida
1) Copia `.env.example` a `.env` y ajusta si es necesario.
2) Usa la URL de Render en formato async (`postgresql+asyncpg://...`). Si tu URL trae `?sslmode=require`, no pasa nada: el backend la limpia y fuerza SSL con contexto por defecto. El `DB_SCHEMA` por defecto es `Copilot`.

## Ejecutar local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check:
```bash
curl -v http://localhost:8000/health
```

## Migraciones
```bash
alembic upgrade head
```
- La migración inicial crea el esquema `Copilot` (no toca otras tablas).
- El versionado de Alembic se almacena en el mismo esquema `Copilot`.
