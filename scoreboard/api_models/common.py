from flask_restx import fields, Model

success_response = Model("SucessResponse", {"status": fields.Integer})

error_response = Model(
    "ErrorResponse", {"status": fields.Integer, "message": fields.String}
)
