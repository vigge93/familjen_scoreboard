from flask_restx.reqparse import RequestParser

id_parser = RequestParser(bundle_errors=True)
id_parser.add_argument("id", type=int, required=True)
