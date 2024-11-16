import datetime
from typing import Sequence

from sqlalchemy import exc

from scoreboard import db
from scoreboard.enums import ClearanceEnum
from scoreboard.model.user import User
from scoreboard.model.scores import ScoreLog


def commit():
    db.session.commit()


def rollback():
    db.session.rollback()


def get_user(id: int) -> User | None:
    return db.session.get(User, id)


def get_users() -> Sequence[User]:
    users = db.session.execute(db.select(User).where(User.id > 0)).scalars().all()
    return users


def get_user_by_email(email: str) -> User | None:
    return db.session.execute(db.select(User).filter_by(email=email)).scalars().first()


def update_user_last_login(id: int) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.lastLogin = datetime.datetime.now(datetime.UTC)
    db.session.commit()
    return True


def update_user_password(id: int, hashed_password: str) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.password = hashed_password
    user.needs_password_change = False
    db.session.commit()
    return True


def add_user(user: User) -> bool:
    try:
        db.session.add(user)
        db.session.commit()
        return True
    except exc.SQLAlchemyError:
        db.session.rollback()
        return False


def update_user(id: int, name: str, email: str) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.name = name
    user.email = email
    try:
        db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        return False
    return True


def reset_user_password(id: int, hashed_temp_password: str) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.password = hashed_temp_password
    user.needs_password_change = True
    db.session.commit()
    return True


def add_user_role(id: int, new_role: ClearanceEnum) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.userTypeId = user.userTypeId | new_role
    db.session.commit()
    return True


def remove_user_role(id: int, role: ClearanceEnum) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.userTypeId = user.userTypeId & ~role
    db.session.commit()
    return True


def delete_user(id: int) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    db.session.execute(
        db.update(ScoreLog).where(ScoreLog.addedById == user.id).values(addedById=0)
    )
    db.session.delete(user)
    db.session.commit()
    return True


def get_score(id: int) -> ScoreLog | None:
    return db.session.get(ScoreLog, id)


def add_score(score: ScoreLog) -> bool:
    try:
        db.session.add(score)
        db.session.commit()
        return True
    except exc.SQLAlchemyError:
        db.session.rollback()
        return False


def get_user_scores(user_id: int) -> Sequence[ScoreLog]:
    scores = (
        db.session.execute(
            db.select(ScoreLog).filter_by(userId=user_id).order_by(ScoreLog.time.desc())
        )
        .scalars()
        .all()
    )
    return scores


def get_scores_aggregated() -> Sequence[ScoreLog]:
    scores = db.session.execute(
        db.select(ScoreLog.userId, db.func.sum(ScoreLog.score).label("score"))
        .group_by(ScoreLog.userId)
        .order_by(db.func.sum(ScoreLog.score).desc())
    ).all()
    scores_dict = []
    for score in scores:
        score_dict = {
            "score": score.score,
            "user": get_user(score.userId),
        }
        scores_dict.append(score_dict)
    print(scores_dict)
    return scores_dict


def delete_score(id: int) -> bool:
    score = db.session.get(ScoreLog, id)
    if not score:
        return False
    db.session.delete(score)
    db.session.commit()
    return True
