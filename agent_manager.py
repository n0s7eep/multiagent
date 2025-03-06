from typing import List, Dict, Any
from agents.hello_agent import HelloAgent
from agents.weather_agent import WeatherAgent
from agents.chat_agent import ChatAgent

class AgentManager:
    def __init__(self):
        self.agents = {
            "hello": HelloAgent(),
            "weather": WeatherAgent(),
            "chat": ChatAgent()
        }

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """获取所有agent的信息"""
        return [agent.get_info() for agent in self.agents.values()]

    def get_agent(self, agent_type: str):
        """获取指定类型的agent"""
        return self.agents.get(agent_type)

    def greet(self, agent_type: str) -> str:
        """获取指定agent的问候语"""
        agent = self.get_agent(agent_type)
        if agent:
            return agent.greet()
        return "找不到指定的agent"
