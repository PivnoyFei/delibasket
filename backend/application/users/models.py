import bcrypt
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    and_,
    case,
)
from sqlalchemy.sql.expression import Label

from application.database import Base
from application.models import TimeStampMixin


class User(Base, TimeStampMixin):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(LargeBinary, nullable=False)
    username = Column(String(150), nullable=False, unique=True, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    is_staff = Column(Boolean, nullable=False, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)

    async def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self.password)


class Follow(Base, TimeStampMixin):
    __table_args__ = (UniqueConstraint('user_id', 'author_id'),)

    id = Column(Integer, primary_key=True, index=True)

    author_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))  # Подписались
    user_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))  # Подписался

    @classmethod
    def is_subscribed(cls, pk: int | None = None, user_id: int | None = None) -> Label:
        if user_id:
            return case(
                (
                    and_(cls.user_id == user_id, cls.user_id != User.id),
                    "True",
                ),
                else_="False",
            ).label("is_subscribed")
        return case(
            (
                and_(pk != None, cls.user_id == pk, cls.user_id != User.id),
                "True",
            ),
            else_="False",
        ).label("is_subscribed")
