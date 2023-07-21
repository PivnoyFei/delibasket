from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from application.database import Base


def generate_uuid() -> str:
    return str(uuid4().hex)


class AuthToken(Base):
    key = Column(String, primary_key=True, unique=True, index=True, default=generate_uuid)
    created = Column(DateTime())
    user_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))
