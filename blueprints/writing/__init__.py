from flask import Blueprint

writing_bp = Blueprint('writing', __name__)

from blueprints.writing import routes
