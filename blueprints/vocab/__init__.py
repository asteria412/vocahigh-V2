from flask import Blueprint

vocab_bp = Blueprint('vocab', __name__)

from blueprints.vocab import routes
