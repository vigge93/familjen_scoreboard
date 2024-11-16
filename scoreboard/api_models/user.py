from flask_restx import fields, Model

user_type_model = Model("UserType", {"id": fields.Integer, "name": fields.String})

user_model = Model(
    "User",
    {
        "id": fields.Integer,
        "name": fields.String,
        "email": fields.String,
        "needs_password_change": fields.Boolean,
        "userType": fields.Nested(user_type_model),
        "last_login": fields.DateTime,
    },
)

public_user_model = Model(
    "User",
    {
        "id": fields.Integer,
        "name": fields.String,
    },
)
