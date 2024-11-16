import smtplib
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    g,
    request,
)

from werkzeug.security import generate_password_hash

from scoreboard import database
from scoreboard.auth import admin_required, login_required
from scoreboard.database import (
    add_user_role,
    get_user,
    get_users,
    remove_user_role,
    reset_user_password,
)
from flask_restx import Api, Resource
from scoreboard.enums import ClearanceEnum
from scoreboard.model.user import User
from scoreboard.util import send_email
from scoreboard.api_models.user import user_model, user_type_model
from scoreboard.api_models.common import error_response, success_response
from scoreboard.parsers.admin_parsers import insert_user_parser, update_user_parser
from scoreboard.parsers.common_parsers import id_parser

bp = Blueprint("admin", __name__, url_prefix="/admin")
api = Api(bp)
api.models[user_model.name] = user_model
api.models[user_type_model.name] = user_type_model
api.models[error_response.name] = error_response
api.models[success_response.name] = success_response


@api.route("/users")
class Users(Resource):
    method_decorators = [login_required, admin_required]

    @api.marshal_with(user_model)
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    def get(self):
        users = get_users()
        return users


@api.route("/user")
class User(Resource):
    method_decorators = [login_required, admin_required]

    @api.expect(id_parser)
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.marshal_with(user_model)
    def get(self):
        args = id_parser.parse_args(strict=True)
        id = args.id

        user = database.get_user(id)
        if not user:
            abort(404, "Användare hittades ej!")
        return user

    @api.expect(insert_user_parser)
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.marshal_with(user_model)
    def post(self):
        args = insert_user_parser.parse_args(strict=True)

        name = args.name
        email = args.email

        user = add_user(name, email)
        if not user:
            abort(400, "Något gick fel!")
        return user

    @api.expect(update_user_parser)
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.marshal_with(user_model)
    def put(self):
        args = update_user_parser.parse_args(strict=True)

        id = args.id
        user = get_user(id)
        if not user:
            abort(404, "Användare hittades inte!")

        name = args.name
        email = args.email

        if not database.update_user(id, name, email):
            abort(400, "Något gick fel!")

        return user

    @api.expect(id_parser)
    @api.response(204, "Success")
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    def delete(self):
        args = id_parser.parse_args(strict=True)
        id = args.id

        validate_user_id(id)
        if id == g.user.id:
            abort(403, "Du kan inte radera dig själv!")

        if not database.delete_user(id):
            abort(404, "Användare hittades inte!")
        return "", 204


@api.route("/reset_password")
class ResetPassword(Resource):
    method_decorators = [login_required, admin_required]

    @api.expect(id_parser)
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.response(500, "Internal error")
    @api.marshal_with(user_model)
    def post(self):
        args = id_parser.parse_args(strict=True)
        id = args.id

        validate_user_id(id)
        user = get_user(id)

        temp_password = str(uuid4())

        if not user or not reset_user_password(
            id, generate_password_hash(temp_password)
        ):
            abort(404, "Användare hittades inte!")

        email = user.email

        try:
            send_email(
                email,
                "Lösenord för kvittoredovisning nollställt!",
                f"""Hej

Ditt lösenord för kvittoredovisningar har nollställts. Ditt temporära lösenord anges nedan.

Lösenord: {temp_password}
Länk: {request.url_root}

Ovanstående lösenord är temporärt och vid första inloggning kommer du behöva byta ditt lösenord.
""",
            )
        except smtplib.SMTPException:
            abort(
                500,
                f"Fel vid skickande av email till {user.name}, nollställ användarens lösenord för att skicka ett nytt mejl, eller kontakta en administratör.",
            )
        return user


@api.route("/<int:id>/admin")
class Admin(Resource):
    method_decorators = [login_required, admin_required]

    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.marshal_with(user_model)
    def put(self, id: int):
        validate_user_id(id)
        if not add_user_role(id, ClearanceEnum.Admin):
            abort(404, "Användare hittades inte!")
        return get_user(id)

    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.marshal_with(user_model)
    def delete(self, id: int):
        validate_user_id(id)
        if id == g.user.id:
            abort(400, "Du kan inte plocka bort admin från dig själv!")
        if not remove_user_role(id, ClearanceEnum.Admin):
            abort(404, "Användare hittades inte!")
        return get_user(id)


@api.route("/<int:id>/wannabe")
class Wannabe(Resource):
    method_decorators = [login_required, admin_required]

    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.marshal_with(user_model)
    def put(self, id: int):
        validate_user_id(id)
        if not add_user_role(id, ClearanceEnum.Wannabe):
            abort(404, "Användare hittades inte!")
        return get_user(id)

    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.marshal_with(user_model)
    def delete(self, id: int):
        validate_user_id(id)
        if not remove_user_role(id, ClearanceEnum.Wannabe):
            abort(404, "Användare hittades inte!")
        return get_user(id)


def validate_user_id(id: int):
    is_protected_user = id < 1
    if is_protected_user:
        return abort(403)


def add_user(name: str, email: str) -> User | None:
    temp_password = str(uuid4())

    user = User(
        email=email.lower(),
        name=name,
        password=generate_password_hash(temp_password),
        userTypeId=ClearanceEnum.User.value,
    )  # type: ignore

    if not database.add_user(user):
        return None

    try:
        send_email(
            email,
            "Konto för poänglista skapat!",
            f"""Hej

Det har skapats ett konto åt dig för att kunna hantera poänglistan. Inloggningsuppgifter står nedan.

Länk: {request.root_url}
Användarnamn: {email}
Lösenord: {temp_password}

Ovanstående lösenord är temporärt och vid första inloggning kommer du behöva byta ditt lösenord.
""",
        )
    except smtplib.SMTPException:
        return None
    return user
