import functools

from flask import (
    Blueprint,
    abort,
    g,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from scoreboard.database import (
    get_user,
    get_user_by_email,
    update_user_last_login,
    update_user_password,
)
from flask_restx import Resource, Namespace
from scoreboard.enums import ClearanceEnum
from scoreboard.model.user import User
from scoreboard.api_models.user import user_model, user_type_model
from scoreboard.api_models.common import error_response, success_response
from scoreboard.parsers.auth_parsers import login_parser, change_password_parser

ns = Namespace("auth", description="Authentication endpoints. Handles login, logout, and change of password.", default="Auth", default_label="Authentication")
ns.models[user_model.name] = user_model
ns.models[user_type_model.name] = user_type_model
ns.models[error_response.name] = error_response
ns.models[success_response.name] = success_response


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return abort(401, "Du är ej inloggad!")
        if g.user.needs_password_change and request.path != url_for(
            "auth_change_password"
        ):
            abort(403, "Du måste byta lösenord!")

        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user and (g.user.userTypeId & ClearanceEnum.Admin) != 0:
            return view(**kwargs)

        abort(403, "Du har ej tillgång till den här resursen!")

    return wrapped_view


@ns.route("/login")
class Login(Resource):

    @ns.response(400, "Validation error")
    @ns.marshal_with(user_model)
    @ns.expect(login_parser)
    def post(self):
        if g.user is not None:
            return g.user

        args = login_parser.parse_args(strict=True)

        email = args.email
        password = args.password
        error = None
        user: User | None = get_user_by_email(email)

        if user is None or not check_password_hash(user.password, password):  # type: ignore
            error = "Felaktigt användarnamn eller lösenord."

        if error is not None:
            abort(400, error)

        session.clear()
        session["user_id"] = user.id  # type: ignore
        update_user_last_login(user.id)  # type: ignore
        session.permanent = True
        return user


@ns.route("/change_password")
class ChangePassword(Resource):
    method_decorators = [login_required]

    @ns.expect(change_password_parser)
    @ns.response(204, "Success")
    @ns.response(400, "Validation error")
    @ns.response(401, "Unauthorized")
    @ns.response(403, "Forbidden")
    def post(self):
        args = change_password_parser.parse_args(strict=True)

        old_password = args.old_password
        new_password = args.new_password
        password_confirm = args.password_confirm

        if new_password != password_confirm:
            abort(400, "'Nytt Lösenord' och 'Bekräfta lösenord' matchar ej!")

        error = None
        user = get_user(g.user.id)

        if not user or not check_password_hash(user.password, old_password):
            error = "Felaktigt lösenord."

        if error is not None:
            abort(400, error)

        if not update_user_password(g.user.id, generate_password_hash(new_password)):
            abort(404, "Användare hittades ej.")
        return "", 204


@ns.route("/logout")
class Logout(Resource):

    @ns.response(204, "Success")
    def get(self):
        session.clear()
        g.user = None
        return "", 204
