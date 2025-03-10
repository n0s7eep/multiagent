"""
多智能体系统的代理模块
包含基础代理类和各种专门化代理实现
"""

from .specialized.weather_agent import WeatherAgent
from .specialized.chat_agent import ChatAgent
from .specialized.hello_agent import HelloAgent

__all__ = [
    'WeatherAgent',
    'ChatAgent',
    'HelloAgent'
]

# 版本信息
__version__ = '0.1.0'
