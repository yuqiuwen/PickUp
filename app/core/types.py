from typing import TypeVar

from sqlalchemy.orm import DeclarativeBase


Model = TypeVar("Model", bound=DeclarativeBase)
