from flask import Blueprint

from app.api import room

bp = Blueprint('api', __name__, url_prefix='/api')

from .health import health
from .chat import chat

def init_app(app):
    # 注册所有路由后再注册蓝图

    room.init_app(app)
    health.init_routes(bp)
    chat.init_routes(bp)
    app.register_blueprint(bp)
