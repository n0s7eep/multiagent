from typing import Dict, Any
from ..base.base_agent import BaseAgent

class HelloAgent(BaseAgent):
    """问候代理，负责基本的问候交互"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id=agent_id, name="Hello Agent")
        self.greetings = {
            "morning": "早上好！",
            "afternoon": "下午好！",
            "evening": "晚上好！",
            "default": "你好！"
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理问候请求

        Args:
            input_data: 包含问候信息的字典
                {
                    "time_of_day": str,  # morning/afternoon/evening/default
                    "user_name": str (optional)
                }

        Returns:
            Dict[str, Any]: 问候消息
        """
        self.status = "processing"
        try:
            time_of_day = input_data.get("time_of_day", "default")
            user_name = input_data.get("user_name", "")

            greeting = self.greetings.get(time_of_day, self.greetings["default"])

            if user_name:
                greeting = f"{greeting} {user_name}！"

            return {
                "message": greeting,
                "agent_id": self.agent_id,
                "time_of_day": time_of_day
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            self.status = "initialized"

    def add_greeting(self, time_of_day: str, greeting: str) -> None:
        """添加新的问候语"""
        self.greetings[time_of_day] = greeting
