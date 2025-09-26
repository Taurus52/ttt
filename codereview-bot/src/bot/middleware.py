"""Bot middleware for access control."""
from telegram import Update
from telegram.ext import filters
from src.config import settings


class AdminCheckMiddleware(filters.MessageFilter):
    """Filter to check if user is admin."""
    
    def filter(self, message):
        """Check if message is from admin."""
        if not message.from_user:
            return False
        return message.from_user.id == settings.admin_tg_id