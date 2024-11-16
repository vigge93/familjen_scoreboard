from functools import reduce
from itertools import combinations_with_replacement

from werkzeug.security import generate_password_hash

from scoreboard.enums import ClearanceEnum
from scoreboard.model.user import User
from scoreboard.model.usertype import UserType
from scoreboard.model.scores import ScoreLog


def init_db(app, db):
    try:
        with app.app_context():
            db.create_all()
            clearances = combinations_with_replacement(
                ClearanceEnum, len(ClearanceEnum)
            )
            clearances = [
                reduce(lambda curr, next: curr | next, clearance)
                for clearance in clearances
            ]
            clearances = set(clearances)
            for clearance in clearances:
                db.session.add(UserType(id=clearance.value, name=clearance.name))
            db.session.add(
                User(
                    email=app.config["SCOREBOARD_ADMIN_USER_EMAIL"],
                    name=app.config["SCOREBOARD_ADMIN_USER_NAME"],
                    password=generate_password_hash(
                        app.config["SCOREBOARD_ADMIN_USER_PASSWORD"]
                    ),
                    userTypeId=(ClearanceEnum.User | ClearanceEnum.Admin),
                )
            )
            db.session.commit()

    except Exception as ex:
        print(ex)
