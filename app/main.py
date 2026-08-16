import asyncio

from fastapi import FastAPI

from .database import client
from .rules import router as rules_router
from .stats import router as stats_router
from .webhook import router as webhook_router
from .worker import worker_loop


app = FastAPI(
    title="LinkPlease Automation API",
    version="1.0.0",
)


app.include_router(rules_router)
app.include_router(webhook_router)
app.include_router(stats_router)


@app.on_event("startup")
async def startup():
    asyncio.create_task(worker_loop())


@app.get("/")
def root():
    try:
        client.admin.command("ping")

        return {
            "status": "ok",
            "mongodb": "connected",
        }

    except Exception as e:
        return {
            "status": "error",
            "mongodb": str(e),
        }