"""Error handler for the bot."""
import html
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from src.logger import get_logger
from src.config import settings

logger = get_logger(__name__)


async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Collect error information
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    
    # Build the message with some markup
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(str(update_str)[:1000])}</pre>\n\n'
        f'<pre>context.error = {html.escape(str(context.error))}</pre>'
    )
    
    # Log full error
    logger.error(f"Full traceback:\n{tb_string}")
    
    # Send message to admin in production
    if settings.is_production and update.effective_user:
        try:
            await context.bot.send_message(
                chat_id=settings.admin_tg_id,
                text=f"⚠️ Error occurred for user {update.effective_user.id}:\n{message}",
                parse_mode='HTML'
            )
        except Exception:
            logger.exception("Failed to send error notification to admin")
    
    # Send user-friendly error message
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "😔 Произошла ошибка при обработке вашего запроса. "
                "Администратор уже уведомлен. Пожалуйста, попробуйте позже."
            )
        except Exception:
            logger.exception("Failed to send error message to user")