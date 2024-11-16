from flask_restx.reqparse import RequestParser
from scoreboard.validators.string_validators import str_length_validator

score_parser = RequestParser(bundle_errors=True)
score_parser.add_argument("userId", type=int, required=True)
score_parser.add_argument("score", type=int, required=True)
score_parser.add_argument(
    "description",
    type=str_length_validator(max=250),
    case_sensitive=True,
    required=True,
)
