"""
TrueShift - Conversation History Model

Detailed persistence for chat interactions.
Supports:
- Full conversation history (scrolling back)
- Context hydration for agents (memory)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class ConversationLog(BaseModel):
    """
    Log of a single message in a conversation.
    """
    __tablename__ = "conversation_logs"

    # We index user_id for fast retrieval of history
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    session_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    role: Mapped[str] = mapped_column(String(20), nullable=False) # "user", "model"
    agent_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # e.g. "CoachingAgent"
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "agent_name": self.agent_name
        }
