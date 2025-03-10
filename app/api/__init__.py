from flask import Blueprint

bp = Blueprint('api', __name__)

from health import health
from chat import chat

def init_app(app):
    health.init_app(app)
    chat.init_app(app)
