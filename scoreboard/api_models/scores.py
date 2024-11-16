from flask_restx import fields, Model

from scoreboard.api_models.user import public_user_model

score_model = Model(
    "Score",
    {
        "id": fields.Integer,
        "time": fields.DateTime,
        "user": fields.Nested(public_user_model),
        "addedBy": fields.Nested(public_user_model),
        "score": fields.Integer,
        "description": fields.String,
    },
)

score_list_model = Model(
    "ScoreList",
    {
        "user": fields.Nested(public_user_model),
        "score": fields.Integer,
    },
)
