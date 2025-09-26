"""Review related models."""
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, JSON, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.engine import Base


class ReviewCycle(Base):
    """Review cycle for team member rotation."""
    __tablename__ = "review_cycles"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_cycle = Column(JSON, nullable=False, default=list)  # List of user_ids
    current_index = Column(Integer, nullable=False, default=0)
    
    # Relationships
    team = relationship("Team", back_populates="review_cycle")
    
    def __repr__(self):
        return f"<ReviewCycle(team_id={self.team_id}, index={self.current_index})>"


class ReviewRequest(Base):
    """Review request model."""
    __tablename__ = "review_requests"
    
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    mr_links = Column(JSON, nullable=False)  # List of merge request links
    status = Column(String(20), nullable=False)  # 'assigned', 'approved', 'rework', 'escalated'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", foreign_keys=[author_id], back_populates="authored_reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="assigned_reviews")
    team = relationship("Team", back_populates="review_requests")
    
    def __repr__(self):
        return f"<ReviewRequest(id={self.id}, author={self.author_id}, reviewer={self.reviewer_id}, status={self.status})>"