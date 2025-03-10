from flask import Flask
from flask_cors import CORS
from .models import db
from .api import init_app
from .models.agents import repeater

def create_app(config=None):
    app = Flask(__name__)

    # 配置数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get('DATABASE_URI', 'sqlite:///multiagent.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化扩展
    CORS(app)
    db.init_app(app)

    # 注册路由
    init_app(app)

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化 agents
        repeater.init_app(app)

    return app
