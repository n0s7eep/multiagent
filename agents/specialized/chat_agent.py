from typing import Dict, Any
from ..base.base_agent import BaseAgent

class ChatAgent(BaseAgent):
    """聊天代理，负责处理对话交互"""

    def __init__(self, agent_id: str, model_name: str = "gpt-3.5-turbo"):
        super().__init__(agent_id=agent_id, name="Chat Agent")
        self.model_name = model_name
        self.conversation_history = []

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理聊天请求

        Args:
            input_data: 包含用户消息的字典
                {
                    "message": str,
                    "user_id": str,
                    "clear_history": bool (optional)
                }

        Returns:
            Dict[str, Any]: 回复消息
        """
        self.status = "processing"
        try:
            message = input_data.get("message")
            user_id = input_data.get("user_id")

            if not message or not user_id:
                raise ValueError("Message and user_id are required")

            if input_data.get("clear_history"):
                self.conversation_history = []

            # 记录用户消息
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "user_id": user_id
            })

            # TODO: 实现实际的模型调用
            # 这里是一个简单的回显示例
            response = {
                "message": f"收到消息: {message}",
                "conversation_id": self.agent_id,
                "user_id": user_id
            }

            # 记录助手回复
            self.conversation_history.append({
                "role": "assistant",
                "content": response["message"],
                "user_id": user_id
            })

            return response
        except Exception as e:
            return {"error": str(e)}
        finally:
            self.status = "initialized"

    def get_conversation_history(self, user_id: str) -> list:
        """获取指定用户的对话历史"""
        return [
            msg for msg in self.conversation_history
            if msg["user_id"] == user_id
        ]
