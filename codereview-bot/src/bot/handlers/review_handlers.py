"""Review request handlers."""
import re
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from src.database.engine import async_session
from src.database.models import User, Team, UserTeam, TeamLeader, ReviewRequest
from src.bot.services.review_cycle_service import ReviewCycleService
from src.logger import get_logger

logger = get_logger(__name__)

# Global storage for pending review requests (user_id -> data)
pending_reviews = {}


async def request_review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /request_review command."""
    user = update.effective_user
    
    async with async_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.tg_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user or not db_user.is_active:
            await update.message.reply_text(
                "❌ Вы не можете запрашивать ревью. "
                "Убедитесь, что вы зарегистрированы и активны в системе."
            )
            return
        
        # Get user's teams
        result = await session.execute(
            select(Team)
            .join(UserTeam)
            .where(UserTeam.user_id == db_user.id)
        )
        teams = result.scalars().all()
        
        if not teams:
            await update.message.reply_text(
                "❌ Вы не состоите ни в одной команде!"
            )
            return
        
        if len(teams) == 1:
            # Only one team, proceed directly
            pending_reviews[user.id] = {
                'team_id': teams[0].id,
                'team_name': teams[0].name,
                'author_id': db_user.id
            }
            await update.message.reply_text(
                f"📝 Запрос ревью для команды **{teams[0].name}**\n\n"
                "Отправьте ссылки на Merge Request в GitLab.\n"
                "Можно отправить несколько ссылок через пробел или с новой строки.",
                parse_mode="Markdown"
            )
        else:
            # Multiple teams, ask to choose
            keyboard = []
            for team in teams:
                keyboard.append([
                    InlineKeyboardButton(
                        team.name,
                        callback_data=f"select_team:{team.id}:{team.name}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🤔 В какой команде запрашиваете ревью?",
                reply_markup=reply_markup
            )


async def handle_team_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle team selection callback."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    _, team_id, team_name = query.data.split(':', 2)
    team_id = int(team_id)
    
    user = update.effective_user
    
    async with async_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.tg_id == user.id)
        )
        db_user = result.scalar_one()
        
        pending_reviews[user.id] = {
            'team_id': team_id,
            'team_name': team_name,
            'author_id': db_user.id
        }
    
    await query.edit_message_text(
        f"📝 Запрос ревью для команды **{team_name}**\n\n"
        "Отправьте ссылки на Merge Request в GitLab.\n"
        "Можно отправить несколько ссылок через пробел или с новой строки.",
        parse_mode="Markdown"
    )


async def handle_mr_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle merge request links."""
    user = update.effective_user
    
    if user.id not in pending_reviews:
        return
    
    text = update.message.text
    
    # Extract GitLab MR links
    mr_pattern = r'https?://[^\s]*gitlab\.com[^\s]*merge_requests/\d+'
    links = re.findall(mr_pattern, text)
    
    if not links:
        await update.message.reply_text(
            "❌ Не найдены корректные ссылки на GitLab Merge Requests.\n"
            "Ссылка должна содержать 'gitlab.com' и 'merge_requests'."
        )
        return
    
    # Remove duplicates while preserving order
    links = list(dict.fromkeys(links))
    
    review_data = pending_reviews[user.id]
    
    async with async_session() as session:
        # Get next reviewer
        reviewer = await ReviewCycleService.get_next_reviewer(
            session,
            review_data['team_id'],
            review_data['author_id']
        )
        
        if not reviewer:
            await update.message.reply_text(
                "❌ Не удалось найти доступного ревьюера в команде.\n"
                "Возможно, все участники неактивны или вы единственный активный разработчик."
            )
            del pending_reviews[user.id]
            return
        
        # Create review request
        review_request = ReviewRequest(
            author_id=review_data['author_id'],
            reviewer_id=reviewer.id,
            team_id=review_data['team_id'],
            mr_links=links,
            status='assigned'
        )
        session.add(review_request)
        await session.commit()
        
        # Prepare message for reviewer
        author_username = f"@{user.username}" if user.username else f"ID: {user.id}"
        links_text = "\n".join([f"• {link}" for link in links])
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"review_action:approve:{review_request.id}"),
                InlineKeyboardButton("🔄 Request Changes", callback_data=f"review_action:rework:{review_request.id}")
            ],
            [
                InlineKeyboardButton("➡️ Escalate to TL", callback_data=f"review_action:escalate:{review_request.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send notification to reviewer
        try:
            await context.bot.send_message(
                chat_id=reviewer.tg_id,
                text=f"🔔 **Новый запрос на ревью!**\n\n"
                     f"От: {author_username}\n"
                     f"Команда: {review_data['team_name']}\n\n"
                     f"**Merge Requests:**\n{links_text}\n\n"
                     f"Пожалуйста, проверьте код и выберите действие:",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
            # Confirm to author
            reviewer_username = f"@{reviewer.tg_username}" if reviewer.tg_username else "выбранному ревьюеру"
            await update.message.reply_text(
                f"✅ Запрос на ревью отправлен {reviewer_username}!\n\n"
                f"**Команда:** {review_data['team_name']}\n"
                f"**MR:** {len(links)} ссылок\n\n"
                f"Вы получите уведомление, когда ревьюер примет решение.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send review request: {e}")
            await update.message.reply_text(
                "❌ Не удалось отправить запрос ревьюеру. "
                "Возможно, ревьюер не запускал бота."
            )
    
    # Clear pending review
    del pending_reviews[user.id]


async def handle_review_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle review action buttons."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    _, action, review_id = query.data.split(':', 2)
    review_id = int(review_id)
    
    async with async_session() as session:
        # Get review request with related data
        result = await session.execute(
            select(ReviewRequest)
            .options(
                selectinload(ReviewRequest.author),
                selectinload(ReviewRequest.reviewer),
                selectinload(ReviewRequest.team).selectinload(Team.leader)
            )
            .where(ReviewRequest.id == review_id)
        )
        review = result.scalar_one_or_none()
        
        if not review:
            await query.edit_message_text("❌ Запрос на ревью не найден.")
            return
        
        # Check if the user is the assigned reviewer
        if review.reviewer.tg_id != update.effective_user.id:
            await query.answer("❌ Это не ваш запрос на ревью!", show_alert=True)
            return
        
        author_username = f"@{review.author.tg_username}" if review.author.tg_username else f"ID: {review.author.tg_id}"
        reviewer_username = f"@{review.reviewer.tg_username}" if review.reviewer.tg_username else "Ревьюер"
        links_text = "\n".join([f"• {link}" for link in review.mr_links])
        
        if action == "approve":
            review.status = 'approved'
            await session.commit()
            
            # Update reviewer's message
            await query.edit_message_text(
                f"✅ **Вы одобрили ревью**\n\n"
                f"От: {author_username}\n"
                f"MR:\n{links_text}",
                parse_mode="Markdown"
            )
            
            # Notify author
            await context.bot.send_message(
                chat_id=review.author.tg_id,
                text=f"✅ **Ваш код одобрен!**\n\n"
                     f"Ревьюер: {reviewer_username}\n"
                     f"MR:\n{links_text}",
                parse_mode="Markdown"
            )
            
        elif action == "rework":
            review.status = 'rework'
            await session.commit()
            
            # Update reviewer's message
            await query.edit_message_text(
                f"🔄 **Вы запросили изменения**\n\n"
                f"От: {author_username}\n"
                f"MR:\n{links_text}",
                parse_mode="Markdown"
            )
            
            # Notify author
            await context.bot.send_message(
                chat_id=review.author.tg_id,
                text=f"🔄 **Требуются изменения в коде**\n\n"
                     f"Ревьюер: {reviewer_username}\n"
                     f"MR:\n{links_text}\n\n"
                     f"Пожалуйста, внесите необходимые изменения.",
                parse_mode="Markdown"
            )
            
        elif action == "escalate":
            if not review.team.leader:
                await query.answer("❌ В команде нет тимлида!", show_alert=True)
                return
            
            review.status = 'escalated'
            await session.commit()
            
            # Update reviewer's message
            await query.edit_message_text(
                f"➡️ **Вы эскалировали ревью тимлиду**\n\n"
                f"От: {author_username}\n"
                f"MR:\n{links_text}",
                parse_mode="Markdown"
            )
            
            # Notify team leader
            tl_username = f"@{review.team.leader.user.tg_username}" if review.team.leader.user.tg_username else "Тимлид"
            await context.bot.send_message(
                chat_id=review.team.leader.user.tg_id,
                text=f"⚠️ **Вам эскалировано ревью!**\n\n"
                     f"От: {author_username}\n"
                     f"Ревьюер: {reviewer_username}\n\n"
                     f"**Требуется ваше решение по спорным моментам.**\n\n"
                     f"MR:\n{links_text}",
                parse_mode="Markdown"
            )
            
            # Notify author
            await context.bot.send_message(
                chat_id=review.author.tg_id,
                text=f"➡️ **Ваше ревью эскалировано тимлиду**\n\n"
                     f"Ревьюер {reviewer_username} направил ваш запрос тимлиду {tl_username} "
                     f"для разрешения спорных моментов.\n\n"
                     f"MR:\n{links_text}",
                parse_mode="Markdown"
            )