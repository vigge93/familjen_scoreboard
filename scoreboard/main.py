from flask import (
    abort,
    g,
)

from flask_restx import Namespace, Resource

from scoreboard import database
from scoreboard.auth import login_required
from scoreboard.enums import ClearanceEnum
from scoreboard.api_models.scores import score_list_model, score_model
from scoreboard.api_models.common import error_response, success_response
from scoreboard.api_models.user import public_user_model
from scoreboard.parsers.common_parsers import id_parser
from scoreboard.parsers.score_parsers import score_parser
from scoreboard.model.scores import ScoreLog

ns = Namespace("scoreboard", path="/", title="Scoreboard", description="Main endpoints for interacting with the scoreboard.", default="Scoreboard", default_label="Scoreboard")
ns.models[score_list_model.name] = score_list_model
ns.models[score_model.name] = score_model
ns.models[error_response.name] = error_response
ns.models[success_response.name] = success_response
ns.models[public_user_model.name] = public_user_model


@ns.route("/scores")
class Scores(Resource):

    @ns.marshal_with(score_list_model)
    def get(self):
        return database.get_scores_aggregated()


@ns.route("/score")
class Score(Resource):
    method_decorators = [login_required]

    @ns.expect(id_parser)
    @ns.response(400, "Validation error")
    @ns.response(401, "Unauthorized")
    @ns.response(404, "Not found")
    @ns.marshal_with(score_model)
    def get(self):
        args = id_parser.parse_args(strict=True)
        id = args.id

        score = database.get_score(id)
        if not score:
            abort(404, "Poäng hittades ej!")
        return score

    @ns.expect(score_parser)
    @ns.response(400, "Validation error")
    @ns.response(401, "Unauthorized")
    @ns.response(403, "Forbidden")
    @ns.response(404, "Not found")
    @ns.marshal_with(score_model)
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

    @ns.expect(id_parser)
    @ns.response(204, "Success")
    @ns.response(400, "Validation error")
    @ns.response(401, "Unauthorized")
    @ns.response(403, "Forbidden")
    @ns.response(404, "Not found")
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


@ns.route("/<int:id>/scores")
class UserScore(Resource):
    method_decorators = [login_required]

    @ns.marshal_with(score_model)
    @ns.response(401, "Unauthorized")
    def get(self, id: int):
        return database.get_user_scores(id)
