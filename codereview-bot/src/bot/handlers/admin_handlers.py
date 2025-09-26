"""Admin command handlers."""
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from src.database.engine import async_session
from src.database.models import User, Team, UserTeam, TeamLeader
from src.logger import get_logger

logger = get_logger(__name__)


async def create_team_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_create_team command."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Использование: /admin_create_team <название_команды>"
        )
        return
    
    team_name = " ".join(context.args)
    
    async with async_session() as session:
        # Check if team exists
        result = await session.execute(
            select(Team).where(Team.name == team_name)
        )
        if result.scalar_one_or_none():
            await update.message.reply_text(
                f"❌ Команда '{team_name}' уже существует!"
            )
            return
        
        # Create team
        new_team = Team(name=team_name)
        session.add(new_team)
        await session.commit()
        
        logger.info(f"Admin {update.effective_user.id} created team: {team_name}")
        await update.message.reply_text(
            f"✅ Команда '{team_name}' успешно создана!"
        )


async def list_teams_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_list_teams command."""
    async with async_session() as session:
        result = await session.execute(
            select(Team).options(
                selectinload(Team.members),
                selectinload(Team.leader).selectinload(TeamLeader.user)
            )
        )
        teams = result.scalars().all()
        
        if not teams:
            await update.message.reply_text("📋 Нет созданных команд.")
            return
        
        message = "📋 **Список команд:**\n\n"
        for team in teams:
            message += f"**ID: {team.id} | {team.name}**\n"
            message += f"👥 Участников: {len(team.members)}\n"
            if team.leader:
                leader_username = team.leader.user.tg_username or "без username"
                message += f"👑 Тимлид: @{leader_username} (ID: {team.leader.user.tg_id})\n"
            message += "\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")


async def add_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_add_user command."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Использование: /admin_add_user <telegram_id> <название_команды>"
        )
        return
    
    try:
        tg_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID должен быть числом!")
        return
    
    team_name = " ".join(context.args[1:])
    
    async with async_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(
                f"❌ Пользователь с ID {tg_id} не найден! "
                "Пользователь должен сначала запустить бота (/start)."
            )
            return
        
        # Get team
        result = await session.execute(
            select(Team).where(Team.name == team_name)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            await update.message.reply_text(
                f"❌ Команда '{team_name}' не найдена!"
            )
            return
        
        # Check if already member
        result = await session.execute(
            select(UserTeam).where(
                and_(UserTeam.user_id == user.id, UserTeam.team_id == team.id)
            )
        )
        if result.scalar_one_or_none():
            await update.message.reply_text(
                f"❌ Пользователь уже состоит в команде '{team_name}'!"
            )
            return
        
        # Add to team
        user_team = UserTeam(user_id=user.id, team_id=team.id)
        session.add(user_team)
        await session.commit()
        
        username = f"@{user.tg_username}" if user.tg_username else f"ID: {tg_id}"
        logger.info(f"Admin {update.effective_user.id} added user {tg_id} to team {team_name}")
        await update.message.reply_text(
            f"✅ Пользователь {username} добавлен в команду '{team_name}'!"
        )


async def set_team_leader_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_set_team_leader command."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Использование: /admin_set_team_leader <telegram_id> <название_команды>"
        )
        return
    
    try:
        tg_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID должен быть числом!")
        return
    
    team_name = " ".join(context.args[1:])
    
    async with async_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(
                f"❌ Пользователь с ID {tg_id} не найден!"
            )
            return
        
        # Get team
        result = await session.execute(
            select(Team).where(Team.name == team_name)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            await update.message.reply_text(
                f"❌ Команда '{team_name}' не найдена!"
            )
            return
        
        # Check if user is team member
        result = await session.execute(
            select(UserTeam).where(
                and_(UserTeam.user_id == user.id, UserTeam.team_id == team.id)
            )
        )
        if not result.scalar_one_or_none():
            await update.message.reply_text(
                f"❌ Пользователь должен быть членом команды '{team_name}'!"
            )
            return
        
        # Remove current team leader if exists
        result = await session.execute(
            select(TeamLeader).where(TeamLeader.team_id == team.id)
        )
        current_leader = result.scalar_one_or_none()
        if current_leader:
            await session.delete(current_leader)
        
        # Set new team leader
        new_leader = TeamLeader(user_id=user.id, team_id=team.id)
        session.add(new_leader)
        await session.commit()
        
        username = f"@{user.tg_username}" if user.tg_username else f"ID: {tg_id}"
        logger.info(f"Admin {update.effective_user.id} set {tg_id} as team leader of {team_name}")
        await update.message.reply_text(
            f"✅ {username} назначен тимлидом команды '{team_name}'!"
        )


async def remove_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_remove_user command."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Использование: /admin_remove_user <telegram_id> <название_команды>"
        )
        return
    
    try:
        tg_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID должен быть числом!")
        return
    
    team_name = " ".join(context.args[1:])
    
    async with async_session() as session:
        # Get user and team
        user_result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = user_result.scalar_one_or_none()
        
        team_result = await session.execute(
            select(Team).where(Team.name == team_name)
        )
        team = team_result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(f"❌ Пользователь с ID {tg_id} не найден!")
            return
            
        if not team:
            await update.message.reply_text(f"❌ Команда '{team_name}' не найдена!")
            return
        
        # Remove from team
        result = await session.execute(
            select(UserTeam).where(
                and_(UserTeam.user_id == user.id, UserTeam.team_id == team.id)
            )
        )
        user_team = result.scalar_one_or_none()
        
        if not user_team:
            await update.message.reply_text(
                f"❌ Пользователь не состоит в команде '{team_name}'!"
            )
            return
        
        await session.delete(user_team)
        
        # Remove team leader role if exists
        leader_result = await session.execute(
            select(TeamLeader).where(
                and_(TeamLeader.user_id == user.id, TeamLeader.team_id == team.id)
            )
        )
        team_leader = leader_result.scalar_one_or_none()
        if team_leader:
            await session.delete(team_leader)
        
        await session.commit()
        
        username = f"@{user.tg_username}" if user.tg_username else f"ID: {tg_id}"
        logger.info(f"Admin {update.effective_user.id} removed user {tg_id} from team {team_name}")
        await update.message.reply_text(
            f"✅ Пользователь {username} удален из команды '{team_name}'!"
        )


async def deactivate_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_deactivate_user command."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Использование: /admin_deactivate_user <telegram_id>"
        )
        return
    
    try:
        tg_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID должен быть числом!")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(
                f"❌ Пользователь с ID {tg_id} не найден!"
            )
            return
        
        if not user.is_active:
            await update.message.reply_text(
                f"❌ Пользователь уже деактивирован!"
            )
            return
        
        user.is_active = False
        await session.commit()
        
        username = f"@{user.tg_username}" if user.tg_username else f"ID: {tg_id}"
        logger.info(f"Admin {update.effective_user.id} deactivated user {tg_id}")
        await update.message.reply_text(
            f"✅ Пользователь {username} деактивирован!"
        )


async def activate_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_activate_user command."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Использование: /admin_activate_user <telegram_id>"
        )
        return
    
    try:
        tg_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID должен быть числом!")
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(
                f"❌ Пользователь с ID {tg_id} не найден!"
            )
            return
        
        if user.is_active:
            await update.message.reply_text(
                f"❌ Пользователь уже активен!"
            )
            return
        
        user.is_active = True
        await session.commit()
        
        username = f"@{user.tg_username}" if user.tg_username else f"ID: {tg_id}"
        logger.info(f"Admin {update.effective_user.id} activated user {tg_id}")
        await update.message.reply_text(
            f"✅ Пользователь {username} активирован!"
        )


async def get_user_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin_get_user_id command."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Использование: /admin_get_user_id @username"
        )
        return
    
    username = context.args[0].lstrip('@')
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await update.message.reply_text(
                f"❌ Пользователь @{username} не найден в базе данных!"
            )
            return
        
        await update.message.reply_text(
            f"👤 Пользователь @{username}\n"
            f"🆔 Telegram ID: `{user.tg_id}`\n"
            f"📊 Статус: {'Активен' if user.is_active else 'Деактивирован'}",
            parse_mode="Markdown"
        )