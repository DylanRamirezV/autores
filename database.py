from typing import AsyncGenerator

import asyncpg
from loguru import logger


class PoolNotReadyError(RuntimeError):
    """Se lanza cuando se intenta obtener una conexión antes de inicializar el pool."""


class Db:
    pool: asyncpg.Pool | None = None

    async def connect(
        self,
        db_url: str,
        min_size: int = 1,
        max_size: int = 10,
        acquire_timeout: float = 10.0,
        command_timeout: float = 30.0,
    ):
        if self.pool is not None:
            logger.debug("Pool ya conectado, se omite")
            return
        self.pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=min_size,
            max_size=max_size,
            timeout=acquire_timeout,
            command_timeout=command_timeout,
            max_inactive_connection_lifetime=300.0,
        )
        logger.info("Pool de conexiones a la base de datos establecido")

    async def close(self):
        if self.pool is not None:
            try:
                await self.pool.close()
                logger.info("Pool de conexiones a la base de datos cerrado")
            except Exception:
                logger.exception("Error al cerrar el pool de la base de datos")
            finally:
                self.pool = None


db = Db()


async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Dependencia de FastAPI: cede una conexión del pool."""
    if db.pool is None:
        raise PoolNotReadyError(
            "El pool de la base de datos no está inicializado. Llama a connect() primero."
        )
    async with db.pool.acquire() as conn:
        yield conn