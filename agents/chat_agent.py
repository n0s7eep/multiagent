from typing import Dict, Any

class ChatAgent:
    def __init__(self):
        self.name = "Chat Agent"
        self.description = "一个喜欢聊天的机器人"

    def greet(self) -> str:
        return "你好！我是 Chat Agent，让我们开始聊天吧！"

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": "chat"
        }
