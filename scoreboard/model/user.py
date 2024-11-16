from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from scoreboard import db
from scoreboard.enums import ClearanceEnum
from scoreboard.model.usertype import UserType


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    password: Mapped[str]
    needs_password_change: Mapped[bool] = mapped_column(default=True)
    userTypeId: Mapped[int] = mapped_column(
        db.ForeignKey(UserType.id), default=ClearanceEnum.User.value
    )
    lastLogin: Mapped[datetime | None]

    userType: Mapped["UserType"] = relationship()
