import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import db
from vistas import router as vistas_router

DATABASE_URL = os.environ["DATABASE_URL"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect(DATABASE_URL)
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)

app.include_router(vistas_router)