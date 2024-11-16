from sqlalchemy.orm import Mapped, mapped_column

from scoreboard import db


class UserType(db.Model):
    __tablename__ = "Usertype"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
