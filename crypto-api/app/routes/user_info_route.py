from flask import Blueprint, jsonify, request
from app.initialize_logging import logger
from app.libs.database.database import insert_user


user_info_blueprint = Blueprint("user_info_blueprint", __name__)


@user_info_blueprint.route("/add_user", methods = ["POST"])
def route_add_user():
    req = request.get_json()

    if 'user_name' not in req or 'user_id' not in req:
        return jsonify({
            'error': "Need user_name and user_id in POST request."
            }), 500

    user_name = req['user_name']
    user_id = req['user_id']

    result = insert_user(
            user_name=user_name,
            user_id=user_id
        )

    logger.debug(f"User inserted: {result}")

    return jsonify({
        'result': 'user_added'
        }), 200

