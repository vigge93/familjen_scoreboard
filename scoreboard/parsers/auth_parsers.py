from flask_restx.reqparse import RequestParser
from scoreboard.validators.string_validators import str_length_validator


change_password_parser = RequestParser(bundle_errors=True)
change_password_parser.add_argument(
    "old_password",
    type=str_length_validator(max=250),
    case_sensitive=True,
    required=True,
)
change_password_parser.add_argument(
    "new_password",
    type=str_length_validator(max=250),
    case_sensitive=True,
    required=True,
)
change_password_parser.add_argument(
    "password_confirm",
    type=str_length_validator(max=250),
    case_sensitive=True,
    required=True,
)

login_parser = RequestParser(bundle_errors=True)
login_parser.add_argument(
    "email", type=str_length_validator(), case_sensitive=False, required=True
)
login_parser.add_argument(
    "password", type=str_length_validator(max=250), case_sensitive=True, required=True
)
