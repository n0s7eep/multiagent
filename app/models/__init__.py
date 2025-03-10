from .base import db
from .agent import Agent
from .chat import ChatRoom, ChatMessage, chat_room_manager

__all__ = [
    'db',
    'Agent',
    'ChatRoom',
    'ChatMessage',
    'chat_room_manager'
]

from datetime import datetime
from typing import Dict, List, Set
import json

# 在这里导入具体的模型类

class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'

    id = db.Column(db.String(36), primary_key=True)
    agent_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联消息
    messages = db.relationship('ChatMessage', backref='room', lazy=True, cascade='all, delete-orphan')

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages]
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }

# 内存中的活动连接管理
class ChatRoomManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        # room_id -> Set[websocket]
        self.connections: Dict[str, Set] = {}
        # websocket -> room_id
        self.socket_rooms: Dict = {}

    def add_connection(self, room_id: str, websocket) -> None:
        """添加新的 WebSocket 连接到房间"""
        if room_id not in self.connections:
            self.connections[room_id] = set()
        self.connections[room_id].add(websocket)
        self.socket_rooms[websocket] = room_id

    def remove_connection(self, websocket) -> None:
        """移除 WebSocket 连接"""
        room_id = self.socket_rooms.get(websocket)
        if room_id:
            if room_id in self.connections:
                self.connections[room_id].discard(websocket)
                if not self.connections[room_id]:
                    del self.connections[room_id]
            del self.socket_rooms[websocket]

    def broadcast_to_room(self, room_id: str, message: Dict) -> None:
        """向房间内的所有连接广播消息"""
        if room_id not in self.connections:
            return

        message_str = json.dumps(message)
        dead_sockets = set()

        for websocket in self.connections[room_id]:
            try:
                websocket.send(message_str)
            except Exception:
                dead_sockets.add(websocket)

        # 清理断开的连接
        for websocket in dead_sockets:
            self.remove_connection(websocket)

    def get_room_connections(self, room_id: str) -> Set:
        """获取房间内的所有连接"""
        return self.connections.get(room_id, set())

    def get_connection_room(self, websocket) -> str:
        """获取连接所在的房间 ID"""
        return self.socket_rooms.get(websocket)

# 创建全局聊天室管理器实例
chat_room_manager = ChatRoomManager()
