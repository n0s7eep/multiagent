import logging
from flask_sock import Sock
from app.models import ChatRoom, ChatMessage, Agent, chat_room_manager, db
from datetime import datetime
import json
from uuid import uuid4
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from flask import current_app
import atexit
import signal

logger = logging.getLogger(__name__)

sock = Sock()
# 创建线程池和状态标志
thread_pool = None
thread_pool_lock = threading.Lock()
is_shutting_down = threading.Event()

def get_thread_pool():
    """获取线程池实例，如果不存在则创建"""
    global thread_pool
    if is_shutting_down.is_set():
        return None

    with thread_pool_lock:
        if thread_pool is None and not is_shutting_down.is_set():
            thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="agent_worker")
        return thread_pool

def shutdown_thread_pool():
    """关闭线程池"""
    global thread_pool
    if is_shutting_down.is_set():
        return

    is_shutting_down.set()  # 设置关闭标志
    with thread_pool_lock:
        if thread_pool is not None:
            logger.info("正在关闭线程池...")
            try:
                # 通知所有房间服务器正在关闭
                for room_id in chat_room_manager.rooms:
                    try:
                        shutdown_msg = {
                            'type': 'system',
                            'content': '服务器正在关闭维护，请稍后重新连接...',
                            'role': 'system',
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        chat_room_manager.broadcast_to_room(room_id, shutdown_msg)
                    except Exception as e:
                        logger.error(f"发送关闭通知到房间 {room_id} 失败: {e}")

                # 等待现有任务完成
                thread_pool.shutdown(wait=True, cancel_futures=True)
                thread_pool = None
                logger.info("线程池已关闭")
            except Exception as e:
                logger.error(f"关闭线程池时出错: {e}")

# 注册信号处理
def signal_handler(signum, frame):
    """处理进程信号"""
    logger.info(f"收到信号 {signum}，开始关闭服务...")
    shutdown_thread_pool()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 注册应用退出时的清理函数
atexit.register(shutdown_thread_pool)

def create_message(room_id: str, msg_id: str, msg_type: str, content: str, role: str) -> dict:
    """创建标准格式的消息"""
    message = ChatMessage(
        id=msg_id,
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

def create_stream_message(msg_id: str, msg_type: str, content: str, role: str, is_end: bool = False, is_thinking: bool = False) -> dict:
    """创建流式消息格式"""
    return {
        'id': msg_id,
        'type': msg_type,
        'content': content,
        'role': role,
        'timestamp': datetime.utcnow().isoformat(),
        'is_stream': True,
        'is_end': is_end,
        'is_thinking': is_thinking
    }

def process_agent_response(app, room_id: str, agent: Agent, message_content: str, msg_id: str):
    """在线程池中处理 agent 响应"""
    with app.app_context():
        try:
            full_response = []

            # 创建并保存用户消息
            user_message = create_message(
                room_id=room_id,
                msg_type='message',
                msg_id=str(uuid4()),
                content=message_content,
                role='user'
            )
            # 广播用户消息给所有客户端
            chat_room_manager.broadcast_to_room(room_id, user_message)

            # 使用流式生成回复
            for chunk in agent.generate_response_stream(message_content):
                try:
                    # 解析 JSON 消息
                    msg_data = json.loads(chunk)
                    msg_type = msg_data.get('type', '')
                    msg_content = msg_data.get('content', '')

                    # 根据消息类型处理
                    if msg_type == 'thinking':
                        # 思考过程消息
                        stream_msg = create_stream_message(
                            msg_id=msg_id,
                            msg_type='response',
                            content=msg_content,
                            role='assistant',
                            is_end=False,
                            is_thinking=True
                        )
                    elif msg_type == 'result':
                        # 最终结果消息
                        stream_msg = create_stream_message(
                            msg_id=msg_id,
                            msg_type='response',
                            content=msg_content,
                            role='assistant',
                            is_end=False,
                            is_thinking=False
                        )
                        # 只将结果消息添加到最终响应
                        full_response.append(msg_content)
                    elif msg_type == 'start':
                        # 开始消息
                        stream_msg = create_stream_message(
                            msg_id=msg_id,
                            msg_type='response',
                            content=msg_content,
                            role='assistant',
                            is_end=False,
                            is_thinking=True
                        )
                    else:
                        # 未知类型消息，保持原样发送
                        stream_msg = create_stream_message(
                            msg_id=msg_id,
                            msg_type='response',
                            content=chunk,
                            role='assistant',
                            is_end=False,
                            is_thinking=False
                        )

                    chat_room_manager.broadcast_to_room(room_id, stream_msg)
                except json.JSONDecodeError:
                    # 如果不是 JSON 格式，按普通消息处理
                    stream_msg = create_stream_message(
                        msg_id=msg_id,
                        msg_type='response',
                        content=chunk,
                        role='assistant',
                        is_end=False,
                        is_thinking=False
                    )
                    full_response.append(chunk)
                    chat_room_manager.broadcast_to_room(room_id, stream_msg)

            # 发送流式响应结束标记
            final_content = ''.join(full_response)
            end_msg = create_stream_message(
                msg_id=msg_id,
                msg_type='response',
                content=final_content,
                role='assistant',
                is_end=True,
                is_thinking=False
            )
            chat_room_manager.broadcast_to_room(room_id, end_msg)

            # 保存完整的响应到数据库
            create_message(
                msg_id=msg_id,
                room_id=room_id,
                msg_type='response',
                content=final_content,
                role='assistant'
            )
        except Exception as e:
            logger.error(f"处理 agent 响应时出错: {e}")
            error_msg = create_message(
                msg_id=msg_id,
                room_id=room_id,
                msg_type='error',
                content=str(e),
                role='system'
            )
            chat_room_manager.broadcast_to_room(room_id, error_msg)
        finally:
            # 清理数据库会话
            db.session.remove()

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
    futures = []  # 存储所有提交的任务

    try:
        # 发送欢迎消息
        welcome_msg = create_message(
            msg_id=str(uuid4()),
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
                    logger.info(f"收到心跳消息 room_id: {room_id} : {message_data}")
                    continue

                if message_data.get('type') == 'message':

                    try:
                        # 获取线程池实例
                        pool = get_thread_pool()
                        if pool is None or pool._shutdown:
                            raise RuntimeError("服务器正在维护中")

                        # 获取agent并在线程池中处理响应
                        agent = Agent.query.get(room.agent_id)
                        msg_id = str(uuid4())

                        # 提交任务到线程池
                        future = pool.submit(
                            process_agent_response,
                            current_app._get_current_object(),
                            room_id,
                            agent,
                            message_data['content'],
                            msg_id
                        )
                        futures.append(future)

                        # 清理已完成的任务
                        futures = [f for f in futures if not f.done()]
                    except RuntimeError as e:
                        logger.error(f"提交任务失败: {e}")
                        error_msg = create_message(
                            msg_id=msg_id,
                            room_id=room_id,
                            msg_type='error',
                            content="服务器正在关闭，无法处理新消息",
                            role='system'
                        )
                        ws.send(json.dumps(error_msg))

            except json.JSONDecodeError:
                error_msg = create_message(
                    msg_id=msg_id,
                    room_id=room_id,
                    msg_type='error',
                    content='无效的消息格式',
                    role='system'
                )
                ws.send(json.dumps(error_msg))
            except Exception as e:
                error_msg = create_message(
                    msg_id=msg_id,
                    room_id=room_id,
                    msg_type='error',
                    content=str(e),
                    role='system'
                )
                ws.send(json.dumps(error_msg))

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # 等待所有正在进行的任务完成
        for future in futures:
            try:
                future.result(timeout=1)  # 等待任务完成，最多等待1秒
            except Exception as e:
                logger.error(f"等待任务完成时出错: {e}")
        chat_room_manager.remove_connection(room_id, ws)

def init_app(app):
    """初始化 WebSocket"""
    sock.init_app(app)
