from uuid import uuid4
from typing import Generator
import time
from ..base import db
from ..agent import Agent

class RepeaterAgent(Agent):
    """复读机Agent - 简单重复用户的消息"""

    __mapper_args__ = {
        'polymorphic_identity': 'repeater'
    }

    @classmethod
    def create(cls):
        """创建一个复读机Agent实例"""
        agent = cls(
            id=str(uuid4()),
            name="复读机",
            type="repeater",
            description="我是一个复读机，我会重复你说的话",
            capabilities=["repeat", "stream"]
        )
        return agent

    def generate_response(self, message: str) -> str:
        """生成回复 - 简单重复用户的消息"""
        return message

    def generate_response_stream(self, message: str) -> Generator[str, None, None]:
        """生成流式回复 - 带开场白和延时的逐字返回"""
        # 先发送开场白
        intro = "开始重复："
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

def init_app(app):
    """初始化复读机Agent"""
    with app.app_context():
        # 检查是否已存在
        existing = Agent.query.filter_by(type="repeater").first()
        if not existing:
            # 创建新的复读机Agent
            repeater = RepeaterAgent.create()
            db.session.add(repeater)
            db.session.commit()
            print("复读机Agent已创建")
