from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__)

from blueprints.dashboard import routes
