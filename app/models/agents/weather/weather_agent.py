from typing import Generator
import asyncio
from contextvars import ContextVar
import threading
import json
from app.models.environment.base import BaseEnv
from metagpt.roles.di.team_leader import TeamLeader
from metagpt.schema import Message
from metagpt.utils.stream_pipe import StreamPipe
from metagpt.logs import logger, set_llm_stream_logfunc
from ...agent import Agent
import time
from uuid import uuid4
from metagpt.roles import Searcher
from metagpt.tools.search_engine import SearchEngine
from metagpt.tools import SearchEngineType
from ...base import db

# 创建上下文变量来存储 StreamPipe
stream_pipe_var: ContextVar[StreamPipe] = ContextVar("stream_pipe")

def stream_pipe_log(content, is_thinking=False):
    """处理流式日志输出
    Args:
        content: 日志内容
        is_thinking: 是否为思考过程的内容
    """
    print(content, end="")
    stream_pipe = stream_pipe_var.get(None)
    if stream_pipe:
        # 根据is_thinking参数决定消息类型
        msg_type = "thinking" if is_thinking else "result"
        stream_pipe.set_message(json.dumps({
            "type": msg_type,
            "content": content
        }))

# 设置流式日志函数，传递所有参数
set_llm_stream_logfunc(lambda *args, **kwargs: stream_pipe_log(*args, **kwargs))

class WeatherAgent(Agent):
    """天气Agent 查询天气信息"""

    __mapper_args__ = {
        'polymorphic_identity': 'weather'
    }

    def __post_init__(self):
        """在 SQLAlchemy 模型初始化后执行的初始化"""
        self.env = BaseEnv()
        self.env.add_role(TeamLeader(name="TeamLeader"))
        # self.env.add_role(Searcher(name="Searcher",search_engine=SearchEngine(engine=SearchEngineType.BING)))
        # self.env.run()

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
        agent.__post_init__()  # 手动调用后初始化
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
        if not hasattr(self, 'env'):
            self.__post_init__()
        # 使用成员变量 env 发布消息
        self.env.publish_message(Message(content=message, role="user"))
        # Get the TeamLeader role instance
        tl = self.env.get_role("TeamLeader")
        # Execute the TeamLeader's tasks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(tl.run())
        loop.close()
        return str(response) if response else message

    async def _process_response(self, message: str, stream_pipe: StreamPipe):
        """异步处理响应"""
        if not hasattr(self, 'env'):
            self.__post_init__()

        # 设置流式管道到上下文
        stream_pipe_var.set(stream_pipe)

        # 发送开场白
        stream_pipe.set_message(json.dumps({
            "type": "start",
            "content": "开始查询天气：\n"
        }))

        # 使用成员变量 env 发布消息
        self.env.publish_message(Message(content=message, role="user"))

        # 获取并执行 TeamLeader 的任务
        tl = self.env.get_role("TeamLeader")
        response = await tl.run()

        # 发送最终结果
        if response:
            stream_pipe.set_message(json.dumps({
                "type": "result",
                "content": str(response)
            }))

    def generate_response_stream(self, message: str) -> Generator[str, None, None]:
        """生成流式回复"""
        def thread_run(msg: str, stream_pipe: StreamPipe):
            """在线程中运行异步函数"""
            asyncio.run(self._process_response(msg, stream_pipe))

        # 创建流式管道
        stream_pipe = StreamPipe()

        # 创建并启动处理线程
        thread = threading.Thread(
            target=thread_run,
            args=(message, stream_pipe)
        )
        thread.start()

        # 持续获取并产出消息
        while thread.is_alive():
            msg = stream_pipe.get_message()
            if msg:
                yield msg

        # 确保线程完成
        thread.join()

        # 获取最后的消息
        final_msg = stream_pipe.get_message()
        if final_msg:
            yield final_msg

