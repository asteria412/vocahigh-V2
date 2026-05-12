from flask import Blueprint

dictionary_bp = Blueprint('dictionary', __name__)

from blueprints.dictionary import routes
