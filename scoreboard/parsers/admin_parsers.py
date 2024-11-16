from flask_restx.reqparse import RequestParser
from scoreboard.validators.string_validators import str_length_validator

insert_user_parser = RequestParser(bundle_errors=True)
insert_user_parser.add_argument(
    "email", type=str_length_validator(), case_sensitive=False, required=True
)
insert_user_parser.add_argument(
    "name", type=str_length_validator(max=50), case_sensitive=True, required=True
)

update_user_parser = insert_user_parser.copy()
update_user_parser.add_argument("id", type=int, required=True)
