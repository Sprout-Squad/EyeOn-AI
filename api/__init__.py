from flask import Blueprint

api_blueprint = Blueprint('api', __name__)

from . import scan, predict_create, predict_modify