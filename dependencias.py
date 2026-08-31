from typing import Annotated

import asyncpg
from fastapi import Depends

from database import get_connection

ConnectionDep = Annotated[asyncpg.Connection, Depends(get_connection)]