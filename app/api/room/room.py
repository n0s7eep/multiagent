import logging
from flask_sock import Sock
from app.models import ChatRoom, ChatMessage, Agent, chat_room_manager, db
from datetime import datetime
import json
from uuid import uuid4
logger = logging.getLogger(__name__)

sock = Sock()

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
                    logger.info(f"收到心跳消息 room_id: {room_id} : {message_data}");
                    continue

                if message_data.get('type') == 'message':
                    # 创建并保存用户消息
                    user_message = create_message(
                        room_id=room_id,
                        msg_type='message',
                        content=message_data['content'],
                        role='user'
                    )

                    # # 发送用户消息给所有连接
                    # chat_room_manager.broadcast_to_room(room_id, user_message)

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
    """初始化 WebSocket"""
    sock.init_app(app)
