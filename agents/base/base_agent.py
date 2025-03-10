from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseAgent(ABC):
    """基础代理类，所有专门化代理都应该继承这个类"""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = "initialized"
        self.context: Dict[str, Any] = {}

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据的抽象方法，必须由子类实现"""
        pass

    def set_context(self, key: str, value: Any) -> None:
        """设置代理上下文"""
        self.context[key] = value

    def get_context(self, key: str) -> Optional[Any]:
        """获取代理上下文"""
        return self.context.get(key)

    def clear_context(self) -> None:
        """清除代理上下文"""
        self.context.clear()

    @property
    def is_busy(self) -> bool:
        """检查代理是否正在处理任务"""
        return self.status == "processing"

    def __str__(self) -> str:
        return f"{self.name} (ID: {self.agent_id})"
