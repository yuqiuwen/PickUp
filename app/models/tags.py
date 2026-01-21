import time

from app.models.module import *


class TagModel(ULIDModel, TSModel, StateModel):
    __tablename__ = "tag"

    name = Column(String(50), unique=True, nullable=False)
    create_by = Column(BigInteger, nullable=False)
