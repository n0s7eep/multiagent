from typing import Dict, Any

class HelloAgent:
    def __init__(self):
        self.name = "Hello Agent"
        self.description = "一个简单的打招呼机器人"

    def greet(self) -> str:
        return "你好！我是 Hello Agent，很高兴见到你！"

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": "greeting"
        }
