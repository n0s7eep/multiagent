import os
from dotenv import load_dotenv

# 获取项目根目录路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(ROOT_DIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API配置
    API_PREFIX = '/api/v1'

    # 代理配置
    AGENT_TIMEOUT = 30  # 代理超时时间（秒）
    MAX_AGENTS = 10     # 最大代理数量

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(ROOT_DIR, 'logs', 'app.log')

config = Config()
