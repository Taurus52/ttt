"""User model."""
from sqlalchemy import Column, Integer, BigInteger, String, Boolean
from sqlalchemy.orm import relationship
from src.database.engine import Base


class User(Base):
    """User model representing Telegram users."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)
    tg_username = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    teams = relationship("UserTeam", back_populates="user", cascade="all, delete-orphan")
    led_team = relationship("TeamLeader", back_populates="user", uselist=False, cascade="all, delete-orphan")
    authored_reviews = relationship(
        "ReviewRequest", 
        foreign_keys="ReviewRequest.author_id",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    assigned_reviews = relationship(
        "ReviewRequest",
        foreign_keys="ReviewRequest.reviewer_id", 
        back_populates="reviewer",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, tg_id={self.tg_id}, username={self.tg_username})>"