"""User command handlers."""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database.engine import async_session
from src.database.models import User, UserTeam, Team
from src.logger import get_logger

logger = get_logger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.tg_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            # Create new user
            db_user = User(
                tg_id=user.id,
                tg_username=user.username
            )
            session.add(db_user)
            await session.commit()
            logger.info(f"New user registered: {user.id} (@{user.username})")
        else:
            # Update username if changed
            if db_user.tg_username != user.username:
                db_user.tg_username = user.username
                await session.commit()
        
        # Get user's teams
        result = await session.execute(
            select(Team)
            .join(UserTeam)
            .where(UserTeam.user_id == db_user.id)
            .options(selectinload(Team.leader))
        )
        teams = result.scalars().all()
        
        if not teams:
            await update.message.reply_text(
                "👋 Добро пожаловать в CodeReview Bot!\n\n"
                "❌ Вы не добавлены ни в одну команду. "
                "Обратитесь к администратору для добавления в команду.\n\n"
                "Используйте /help для просмотра доступных команд."
            )
        else:
            team_list = []
            for team in teams:
                is_leader = team.leader and team.leader.user_id == db_user.id
                status = " (Тимлид)" if is_leader else ""
                team_list.append(f"• {team.name}{status}")
            
            await update.message.reply_text(
                f"👋 Добро пожаловать в CodeReview Bot, @{user.username}!\n\n"
                f"Вы состоите в следующих командах:\n"
                f"{chr(10).join(team_list)}\n\n"
                f"Используйте:\n"
                f"• /request_review - запросить ревью кода\n"
                f"• /my_teams - посмотреть свои команды\n"
                f"• /help - справка по командам"
            )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
🤖 **CodeReview Bot - Справка**

**Основные команды:**
/start - Начать работу с ботом
/help - Показать эту справку
/my_teams - Показать ваши команды
/request_review - Запросить ревью кода

**Процесс запроса ревью:**
1. Введите команду /request_review
2. Выберите команду (если вы в нескольких)
3. Отправьте ссылки на Merge Request в GitLab
4. Бот автоматически выберет ревьюера

**Действия ревьюера:**
• ✅ Approve - Одобрить MR
• 🔄 Request Changes - Запросить изменения
• ➡️ Escalate to TL - Эскалировать тимлиду

По всем вопросам обращайтесь к администратору.
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def my_teams_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /my_teams command."""
    user = update.effective_user
    
    async with async_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.tg_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            await update.message.reply_text(
                "❌ Вы не зарегистрированы в системе. "
                "Используйте /start для регистрации."
            )
            return
        
        # Get user's teams with member count
        result = await session.execute(
            select(Team)
            .join(UserTeam)
            .where(UserTeam.user_id == db_user.id)
            .options(
                selectinload(Team.leader),
                selectinload(Team.members).selectinload(UserTeam.user)
            )
        )
        teams = result.scalars().all()
        
        if not teams:
            await update.message.reply_text(
                "❌ Вы не состоите ни в одной команде."
            )
            return
        
        message = "👥 **Ваши команды:**\n\n"
        
        for team in teams:
            is_leader = team.leader and team.leader.user_id == db_user.id
            active_members = len([m for m in team.members if m.user.is_active])
            
            message += f"**{team.name}**\n"
            if is_leader:
                message += "📌 Вы тимлид этой команды\n"
            message += f"👤 Участников: {active_members}\n\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")