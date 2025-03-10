from typing import Generator
from ...agent import Agent
import time
from uuid import uuid4
from ...base import db

class WeatherAgent(Agent):
    """天气Agent 查询天气信息"""

    __mapper_args__ = {
        'polymorphic_identity': 'weather'
    }

    @classmethod
    def create(cls):
        """创建一个天气Agent实例"""
        agent = cls(
            id=str(uuid4()),
            name="天气Agent",
            type="weather",
            description="我是一个天气Agent，我会查询天气信息",
            capabilities=["weather", "stream"]
        )
        return agent

    @classmethod
    def init_app(cls, app):
        """初始化天气Agent"""
        with app.app_context():
            # 检查是否已存在
            existing = Agent.query.filter_by(type="weather").first()
            if not existing:
                # 创建新的天气Agent
                weather = cls.create()
                db.session.add(weather)
                db.session.commit()
                print("天气Agent已创建")

    def generate_response(self, message: str) -> str:
        """生成回复 - 简单重复用户的消息"""
        return message

    def generate_response_stream(self, message: str) -> Generator[str, None, None]:
        """生成流式回复 - 带开场白和延时的逐字返回"""
        # 先发送开场白
        intro = "开始查询天气："
        # for char in intro:
        #     yield char
        yield intro

        # 发送换行
        yield "\n"

        # 等待1秒
        time.sleep(1)

        yield message

        # # 逐字返回消息
        # for char in message:
        #     yield char
