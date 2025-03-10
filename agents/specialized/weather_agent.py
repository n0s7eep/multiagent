from typing import Dict, Any
from agents.base.base_agent import BaseAgent

class WeatherAgent(BaseAgent):
    def __init__(self):
        self.name = "Weather Agent"
        self.description = "一个关心天气的机器人"

    def greet(self) -> str:
        return "你好！我是 Weather Agent，今天天气真不错！"

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": "weather"
        }
