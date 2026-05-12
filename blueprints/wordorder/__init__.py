from flask import Blueprint

wordorder_bp = Blueprint('wordorder', __name__)

from blueprints.wordorder import routes
