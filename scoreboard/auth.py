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
from flask_restx import Api, Resource
from scoreboard.enums import ClearanceEnum
from scoreboard.model.user import User
from scoreboard.api_models.user import user_model, user_type_model
from scoreboard.api_models.common import error_response, success_response
from scoreboard.parsers.auth_parsers import login_parser, change_password_parser

bp = Blueprint("auth", __name__, url_prefix="/auth")
api = Api(bp)
api.models[user_model.name] = user_model
api.models[user_type_model.name] = user_type_model
api.models[error_response.name] = error_response
api.models[success_response.name] = success_response


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return abort(401, "Du är ej inloggad!")
        if g.user.needs_password_change and request.path != url_for(
            "auth.change_password"
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


@api.route("/login")
class Login(Resource):

    @api.response(400, "Validation error")
    @api.marshal_with(user_model)
    @api.expect(login_parser)
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


@api.route("/change_password")
class ChangePassword(Resource):
    method_decorators = [login_required]

    @api.expect(change_password_parser)
    @api.response(204, "Success")
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
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


@api.route("/logout")
class Logout(Resource):

    @api.response(204, "Success")
    def get(self):
        session.clear()
        g.user = None
        return "", 204


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_user(user_id)
        if g.user is None:
            return
