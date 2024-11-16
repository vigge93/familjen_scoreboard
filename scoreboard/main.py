from flask import (
    Blueprint,
    abort,
    g,
)

from flask_restx import Api, Resource

from scoreboard import database
from scoreboard.auth import login_required
from scoreboard.enums import ClearanceEnum
from scoreboard.api_models.scores import score_list_model, score_model
from scoreboard.api_models.common import error_response, success_response
from scoreboard.api_models.user import public_user_model
from scoreboard.parsers.common_parsers import id_parser
from scoreboard.parsers.score_parsers import score_parser
from scoreboard.model.scores import ScoreLog

bp = Blueprint("main", __name__, url_prefix="/")
api = Api(bp)
api.models[score_list_model.name] = score_list_model
api.models[score_model.name] = score_model
api.models[error_response.name] = error_response
api.models[success_response.name] = success_response
api.models[public_user_model.name] = public_user_model


@api.route("/scores")
class Scores(Resource):

    @api.marshal_with(score_list_model)
    def get(self):
        return database.get_scores_aggregated()


@api.route("/score")
class Score(Resource):
    method_decorators = [login_required]

    @api.expect(id_parser)
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(404, "Not found")
    @api.marshal_with(score_model)
    def get(self):
        args = id_parser.parse_args(strict=True)
        id = args.id

        score = database.get_score(id)
        if not score:
            abort(404, "Poäng hittades ej!")
        return score

    @api.expect(score_parser)
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    @api.marshal_with(score_model)
    def post(self):
        if (g.user.userTypeId & ClearanceEnum.Wannabe) != 0:
            score = ScoreLog(
                userId=g.user.id,
                addedBy=g.user.id,
                score=-100,
                description="Försökte lägga till poäng.",
            )
            database.add_score(score)
            abort(403, "Wannabe. Varför försöker du lägga till poäng? -100 poäng.")

        args = score_parser.parse_args(strict=True)

        user_id = args.userId
        score = args.score
        description = args.description

        user = database.get_user(user_id)
        if not user:
            abort(404, "Användare hittades ej.")

        if (user.userTypeId & ClearanceEnum.Wannabe) == 0:
            abort(403, "Kan inte ge poäng till rock!")

        score_log = ScoreLog(
            userId=user_id,
            addedById=g.user.id,
            score=score,
            description=description,
        )

        if not database.add_score(score_log):
            abort(400, "Något gick fel!")
        return score_log

    @api.expect(id_parser)
    @api.response(204, "Success")
    @api.response(400, "Validation error")
    @api.response(401, "Unauthorized")
    @api.response(403, "Forbidden")
    @api.response(404, "Not found")
    def delete(self):
        if (g.user.userTypeId & ClearanceEnum.Wannabe) != 0:
            score = ScoreLog(
                userId=g.user.id,
                addedBy=g.user.id,
                score=-100,
                description="Försökte ta bort poäng.",
            )
            database.add_score(score)
            abort(403, "Wannabe. Varför försöker du ta bort poäng? -100 poäng.")

        args = id_parser.parse_args(strict=True)
        id = args.id

        score = database.get_score(id)

        if not score:
            abort(404, "Poäng hittades ej!")

        is_admin = g.user.userTypeId & ClearanceEnum.Admin != 0
        added_points = score.addedById == g.user.id
        if not (is_admin or added_points):
            abort(403, "Du får inte ta bort dessa poäng!")

        if not database.delete_score(id):
            abort(404, "Poäng hittades ej!")

        return "", 204


@api.route("/<int:id>/scores")
class UserScore(Resource):
    method_decorators = [login_required]

    @api.marshal_with(score_model)
    @api.response(401, "Unauthorized")
    def get(self, id: int):
        return database.get_user_scores(id)
