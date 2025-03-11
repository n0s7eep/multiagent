from metagpt.environment.base_env import Environment
from metagpt.schema import Message
from metagpt.const import AGENT, IMAGES, MESSAGE_ROUTE_TO_ALL, TEAMLEADER_NAME

class BaseEnv(Environment):
    """基础环境类"""


    direct_chat_roles: set[str] = set()  # record direct chat: @role_name
    is_public_chat: bool = True

    def move_message_info_to_content(self, message: Message) -> Message:
        """Two things here:
        1. Convert role, since role field must be reserved for LLM API, and is limited to, for example, one of ["user", "assistant", "system"]
        2. Add sender and recipient info to content, making TL aware, since LLM API only takes content as input
        """
        converted_msg = message.model_copy(deep=True)
        if converted_msg.role not in ["system", "user", "assistant"]:
            converted_msg.role = "assistant"
        sent_from = converted_msg.metadata[AGENT] if AGENT in converted_msg.metadata else converted_msg.sent_from
        # When displaying send_to, change it to those who need to react and exclude those who only need to be aware, e.g.:
        # send_to={<all>} -> Mike; send_to={Alice} -> Alice; send_to={Alice, <all>} -> Alice.
        if converted_msg.send_to == {MESSAGE_ROUTE_TO_ALL}:
            send_to = TEAMLEADER_NAME
        else:
            send_to = ", ".join({role for role in converted_msg.send_to if role != MESSAGE_ROUTE_TO_ALL})
        converted_msg.content = f"[Message] from {sent_from or 'User'} to {send_to}: {converted_msg.content}"
        return converted_msg

    def _publish_message(self, message: Message, peekable: bool = True) -> bool:
        if self.is_public_chat:
            message.send_to.add(MESSAGE_ROUTE_TO_ALL)
        message = self.move_message_info_to_content(message)
        return super().publish_message(message, peekable)

    def publish_message(self, message: Message, peekable: bool = True, user_defined_recipient: str = "", publicer: str = "") -> bool:
        """发布消息，只在发送给用户（human）的消息前添加"测试消息"前缀"""
        # 打印调试信息
        print(f"[DEBUG] 消息详情 | 内容: {message.content} | 发送者: {message.role} | 接收者: {message.send_to} | 可查看: {peekable} | 其他属性: {message.additional_kwargs if hasattr(message, 'additional_kwargs') else '{}'}")

        # if isinstance(message.content, str) and "human" in message.send_to:
        #     message.content = f"测试消息: {message.content}"
        """let the team leader take over message publishing"""

        tl = self.get_role('TeamLeader')  # TeamLeader's name is Mike

        if user_defined_recipient:
            # human user's direct chat message to a certain role
            print("user_defined_recipient: ", user_defined_recipient)
            # human user's direct chat message to a certain role
            for role_name in message.send_to:
                if self.get_role(role_name).is_idle:
                    # User starts a new direct chat with a certain role, expecting a direct chat response from the role; Other roles including TL should not be involved.
                    # If the role is not idle, it means the user helps the role with its current work, in this case, we handle the role's response message as usual.
                    self.direct_chat_roles.add(role_name)

            self._publish_message(message)
            # # bypass team leader, team leader only needs to know but not to react (commented out because TL doesn't understand the message well in actual experiments)
            # tl.rc.memory.add(self.move_message_info_to_content(message))

        elif message.sent_from in self.direct_chat_roles:
            # if chat is not public, direct chat response from a certain role to human user, team leader and other roles in the env should not be involved, no need to publish
            self.direct_chat_roles.remove(message.sent_from)
            if self.is_public_chat:
                self._publish_message(message)

        elif publicer == tl.profile:
            if message.send_to == {"no one"}:
                # skip the dummy message from team leader
                return True
            # message processed by team leader can be published now
            self._publish_message(message)

        else:
            # every regular message goes through team leader
            message.send_to.add(tl.name)
            self._publish_message(message)

        self.history.add(message)

        return True

    def __repr__(self):
        return "BaseEnv()"
