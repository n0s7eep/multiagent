from flask import Blueprint, jsonify, request
from flask_sock import Sock
from app.models import ChatRoom, ChatMessage, Agent, chat_room_manager, db
from datetime import datetime
import json
from uuid import uuid4

def create_room():
    """创建新的聊天室"""
    data = request.get_json()
    agent_type = data.get('agent_type')

    if not agent_type:
        return jsonify({'error': '缺少 agent_type 参数'}), 400

    # 检查 agent 是否存在
    agent = Agent.query.filter_by(type=agent_type).first()
    if not agent:
        return jsonify({'error': f'不支持的 agent 类型: {agent_type}'}), 400

    room = ChatRoom(
        id=str(uuid4()),
        agent_type=agent_type,
        agent_id=agent.id
    )
    db.session.add(room)
    db.session.commit()

    return jsonify({'roomId': room.id}), 201

def get_room(room_id):
    """获取聊天室信息"""
    room = ChatRoom.query.get_or_404(room_id)
    return jsonify(room.to_dict())

def delete_room(room_id):
    """删除聊天室"""
    room = ChatRoom.query.get_or_404(room_id)

    # 关闭所有WebSocket连接
    chat_room_manager.close_room(room_id)

    # 删除相关消息
    ChatMessage.query.filter_by(room_id=room_id).delete()

    # 删除房间
    db.session.delete(room)
    db.session.commit()

    return jsonify({'success': True})

def get_agent(agent_type):
    """获取指定类型的Agent信息"""
    agent = Agent.query.filter_by(type=agent_type).first_or_404()
    return jsonify(agent.to_dict())

def get_all_agents():
    """获取所有可用的Agent列表"""
    agents = Agent.query.all()
    return jsonify([agent.to_dict() for agent in agents])

def create_message(room_id: str, msg_type: str, content: str, role: str) -> dict:
    """创建标准格式的消息"""
    message = ChatMessage(
        id=str(uuid4()),
        room_id=room_id,
        type=msg_type,
        content=content,
        role=role,
        timestamp=datetime.utcnow()
    )
    db.session.add(message)
    db.session.commit()

    return {
        'id': message.id,
        'type': msg_type,
        'content': content,
        'role': role,
        'timestamp': message.timestamp.isoformat()
    }

def init_routes(bp):
    """注册聊天相关路由"""
    bp.add_url_rule('/chat/rooms', 'create_room', create_room, methods=['POST'])
    bp.add_url_rule('/chat/rooms/<room_id>', 'get_room', get_room, methods=['GET'])
    bp.add_url_rule('/chat/rooms/<room_id>', 'delete_room', delete_room, methods=['DELETE'])
    bp.add_url_rule('/chat/agents/<agent_type>', 'get_agent', get_agent, methods=['GET'])
    bp.add_url_rule('/chat/agents', 'get_all_agents', get_all_agents, methods=['GET'])
