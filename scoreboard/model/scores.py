from datetime import datetime

from sqlalchemy import Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scoreboard import db
from scoreboard.model.user import User


class ScoreLog(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[datetime] = mapped_column(server_default=func.now())
    userId: Mapped[int] = mapped_column(db.ForeignKey(User.id))
    addedById: Mapped[int] = mapped_column(db.ForeignKey(User.id))
    score: Mapped[int]
    description: Mapped[str]

    addedBy: Mapped["User"] = relationship(foreign_keys=[addedById])
    user: Mapped["User"] = relationship(foreign_keys=[userId])

    __table_args__ = (Index("idx_userId_score", "userId", "score"),)
