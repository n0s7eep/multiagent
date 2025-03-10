from datetime import datetime
from .base import db

class Agent(db.Model):
    """Agent基类模型"""
    __tablename__ = 'agents'

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    capabilities = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __mapper_args__ = {
        'polymorphic_identity': 'agent',
        'polymorphic_on': type
    }

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'capabilities': self.capabilities
        }

    def generate_response(self, message: str) -> str:
        """生成回复"""
        raise NotImplementedError("Agent子类必须实现generate_response方法")
