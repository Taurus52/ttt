"""Team related models."""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database.engine import Base


class Team(Base):
    """Team model."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    
    # Relationships
    members = relationship("UserTeam", back_populates="team", cascade="all, delete-orphan")
    leader = relationship("TeamLeader", back_populates="team", uselist=False, cascade="all, delete-orphan")
    review_cycle = relationship("ReviewCycle", back_populates="team", uselist=False, cascade="all, delete-orphan")
    review_requests = relationship("ReviewRequest", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name})>"


class UserTeam(Base):
    """Many-to-many relationship between users and teams."""
    __tablename__ = "user_teams"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="teams")
    team = relationship("Team", back_populates="members")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "team_id", name="unique_user_team"),
    )
    
    def __repr__(self):
        return f"<UserTeam(user_id={self.user_id}, team_id={self.team_id})>"


class TeamLeader(Base):
    """Team leader assignment."""
    __tablename__ = "team_leaders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="led_team")
    team = relationship("Team", back_populates="leader")
    
    def __repr__(self):
        return f"<TeamLeader(user_id={self.user_id}, team_id={self.team_id})>"