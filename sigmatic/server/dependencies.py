"""FastAPI dependency injection helpers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.database import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
