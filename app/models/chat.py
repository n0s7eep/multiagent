from datetime import datetime
from typing import Dict, Set, Any
from flask_sock import Sock
import json
from .base import db

class ChatRoom(db.Model):
    """聊天室模型"""
    __tablename__ = 'chat_rooms'

    id = db.Column(db.String(36), primary_key=True)
    agent_type = db.Column(db.String(50), nullable=False)
    agent_id = db.Column(db.String(36), db.ForeignKey('agents.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('ChatMessage', backref='room', lazy=True)
    agent = db.relationship('Agent', backref='rooms')

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'agent': self.agent.to_dict() if self.agent else None,
            'created_at': self.created_at.isoformat()
        }

class ChatMessage(db.Model):
    """聊天消息模型"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.String(36), primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # message, response, error, system
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'role': self.role,
            'timestamp': self.timestamp.isoformat()
        }

class ChatRoomManager:
    """聊天室连接管理器"""
    def __init__(self):
        self.room_connections: Dict[str, Set[Sock]] = {}

    def add_connection(self, room_id: str, ws: Sock) -> None:
        """添加WebSocket连接到房间"""
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(ws)

    def remove_connection(self, room_id: str, ws: Sock) -> None:
        """从房间移除WebSocket连接"""
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(ws)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]

    def broadcast_to_room(self, room_id: str, message: Any) -> None:
        """向房间内所有连接广播消息"""
        if room_id not in self.room_connections:
            return

        message_str = message if isinstance(message, str) else json.dumps(message)
        dead_connections = set()

        for ws in self.room_connections[room_id]:
            try:
                ws.send(message_str)
            except Exception:
                dead_connections.add(ws)

        # 清理断开的连接
        for ws in dead_connections:
            self.remove_connection(room_id, ws)

    def close_room(self, room_id: str) -> None:
        """关闭房间的所有连接"""
        if room_id not in self.room_connections:
            return

        for ws in self.room_connections[room_id].copy():
            try:
                ws.close()
            except:
                pass
            self.remove_connection(room_id, ws)

# 创建全局聊天室管理器实例
chat_room_manager = ChatRoomManager()
