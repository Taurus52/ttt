"""Service for managing review cycles and reviewer selection."""
import random
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.models import User, Team, UserTeam, TeamLeader, ReviewCycle
from src.logger import get_logger

logger = get_logger(__name__)


class ReviewCycleService:
    """Service for managing review cycles."""
    
    @staticmethod
    async def get_next_reviewer(
        session: AsyncSession,
        team_id: int,
        author_id: int
    ) -> Optional[User]:
        """
        Get next reviewer from the team's review cycle.
        
        Args:
            session: Database session
            team_id: Team ID
            author_id: Author user ID (to exclude from selection)
            
        Returns:
            Selected reviewer User or None if no one available
        """
        # Get or create review cycle
        result = await session.execute(
            select(ReviewCycle).where(ReviewCycle.team_id == team_id)
        )
        cycle = result.scalar_one_or_none()
        
        if not cycle:
            cycle = ReviewCycle(team_id=team_id, current_cycle=[], current_index=0)
            session.add(cycle)
            await session.commit()
        
        # Get active team members (excluding team leader)
        result = await session.execute(
            select(User)
            .join(UserTeam)
            .outerjoin(TeamLeader, and_(
                TeamLeader.user_id == User.id,
                TeamLeader.team_id == team_id
            ))
            .where(
                and_(
                    UserTeam.team_id == team_id,
                    User.is_active == True,
                    User.id != author_id,
                    TeamLeader.id.is_(None)  # Exclude team leader
                )
            )
        )
        eligible_users = result.scalars().all()
        
        if not eligible_users:
            logger.warning(f"No eligible reviewers found for team {team_id}")
            return None
        
        eligible_user_ids = [user.id for user in eligible_users]
        
        # Check if we need to create/refresh the cycle
        need_new_cycle = (
            not cycle.current_cycle or
            cycle.current_index >= len(cycle.current_cycle) or
            not all(uid in eligible_user_ids for uid in cycle.current_cycle)
        )
        
        if need_new_cycle:
            # Create new randomized cycle
            new_cycle = eligible_user_ids.copy()
            random.shuffle(new_cycle)
            cycle.current_cycle = new_cycle
            cycle.current_index = 0
            logger.info(f"Created new review cycle for team {team_id}: {new_cycle}")
        
        # Get next reviewer from current cycle
        reviewer_id = None
        attempts = 0
        max_attempts = len(cycle.current_cycle)
        
        while attempts < max_attempts:
            if cycle.current_index < len(cycle.current_cycle):
                potential_reviewer_id = cycle.current_cycle[cycle.current_index]
                
                # Check if this reviewer is still eligible (not the author)
                if potential_reviewer_id != author_id and potential_reviewer_id in eligible_user_ids:
                    reviewer_id = potential_reviewer_id
                    cycle.current_index += 1
                    break
                else:
                    # Skip this reviewer
                    cycle.current_index += 1
                    if cycle.current_index >= len(cycle.current_cycle):
                        # Reached end of cycle, create new one
                        new_cycle = eligible_user_ids.copy()
                        random.shuffle(new_cycle)
                        cycle.current_cycle = new_cycle
                        cycle.current_index = 0
            
            attempts += 1
        
        if not reviewer_id:
            logger.error(f"Could not find reviewer for team {team_id} after {max_attempts} attempts")
            return None
        
        # Save updated cycle
        await session.commit()
        
        # Get reviewer user object
        result = await session.execute(
            select(User).where(User.id == reviewer_id)
        )
        reviewer = result.scalar_one()
        
        logger.info(f"Selected reviewer {reviewer.tg_id} for team {team_id}, author {author_id}")
        return reviewer
    
    @staticmethod
    async def reset_team_cycle(session: AsyncSession, team_id: int) -> None:
        """
        Reset review cycle for a team.
        
        Args:
            session: Database session
            team_id: Team ID
        """
        result = await session.execute(
            select(ReviewCycle).where(ReviewCycle.team_id == team_id)
        )
        cycle = result.scalar_one_or_none()
        
        if cycle:
            cycle.current_cycle = []
            cycle.current_index = 0
            await session.commit()
            logger.info(f"Reset review cycle for team {team_id}")