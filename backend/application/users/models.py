import bcrypt
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    and_,
    case,
)
from sqlalchemy.sql import func

from application.database import Base
from application.models import TimeStampMixin


class User(Base, TimeStampMixin):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(LargeBinary, nullable=False)
    username = Column(String(150), nullable=False, unique=True, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())

    is_active = Column(Boolean, nullable=False, default=True)
    is_staff = Column(Boolean, nullable=False, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    async def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self.password)


class Follow(Base):
    __table_args__ = (UniqueConstraint('user_id', 'author_id'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))
    author_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))

    async def is_subscribed(cls, pk):
        return case(
            (
                and_(pk != None, Follow.user_id == pk),
                "True",
            ),
            else_="False",
        ).label("is_subscribed")
