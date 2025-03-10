from flask import Blueprint, jsonify, request
from flask_sock import Sock
from app.models import ChatRoom, ChatMessage, Agent, chat_room_manager, db
from datetime import datetime
import json
from uuid import uuid4
from api import bp

bp = bp.route('/chat')
sock = Sock()

@bp.route('/rooms', methods=['POST'])
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

@bp.route('/rooms/<room_id>', methods=['GET'])
def get_room(room_id):
    """获取聊天室信息"""
    room = ChatRoom.query.get_or_404(room_id)
    return jsonify(room.to_dict())

@bp.route('/rooms/<room_id>', methods=['DELETE'])
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

@bp.route('/agents/<agent_type>', methods=['GET'])
def get_agent(agent_type):
    """获取Agent信息"""
    agent = Agent.query.filter_by(type=agent_type).first_or_404()
    return jsonify(agent.to_dict())

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

@sock.route('/chat/<room_id>')
def chat_socket(ws, room_id):
    """WebSocket 聊天处理"""
    room = ChatRoom.query.get(room_id)
    if not room:
        ws.send(json.dumps({
            'type': 'error',
            'content': '聊天室不存在',
            'role': 'system',
            'timestamp': datetime.utcnow().isoformat()
        }))
        return

    # 添加连接到房间
    chat_room_manager.add_connection(room_id, ws)

    try:
        # 发送欢迎消息
        welcome_msg = create_message(
            room_id=room_id,
            msg_type='system',
            content=f'欢迎加入聊天室 {room_id}',
            role='system'
        )
        ws.send(json.dumps(welcome_msg))

        while True:
            data = ws.receive()
            try:
                message_data = json.loads(data)

                # 处理心跳消息
                if message_data.get('type') == 'system' and message_data.get('content') == 'ping':
                    ws.send(json.dumps({
                        'type': 'system',
                        'content': 'pong',
                        'role': 'system',
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                    continue

                if message_data.get('type') == 'message':
                    # 创建并保存用户消息
                    user_message = create_message(
                        room_id=room_id,
                        msg_type='message',
                        content=message_data['content'],
                        role='user'
                    )

                    # 发送用户消息给所有连接
                    chat_room_manager.broadcast_to_room(room_id, user_message)

                    # 获取agent并生成回复
                    agent = Agent.query.get(room.agent_id)
                    ai_response = agent.generate_response(message_data['content'])

                    # 创建并保存AI响应
                    ai_message = create_message(
                        room_id=room_id,
                        msg_type='response',
                        content=ai_response,
                        role='assistant'
                    )

                    # 发送AI响应
                    chat_room_manager.broadcast_to_room(room_id, ai_message)

            except json.JSONDecodeError:
                error_msg = create_message(
                    room_id=room_id,
                    msg_type='error',
                    content='无效的消息格式',
                    role='system'
                )
                ws.send(json.dumps(error_msg))
            except Exception as e:
                error_msg = create_message(
                    room_id=room_id,
                    msg_type='error',
                    content=str(e),
                    role='system'
                )
                ws.send(json.dumps(error_msg))

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        chat_room_manager.remove_connection(room_id, ws)

def init_app(app):
    """初始化聊天功能"""
    app.register_blueprint(bp)
    sock.init_app(app)
