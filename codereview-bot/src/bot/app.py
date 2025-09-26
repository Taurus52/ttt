"""Main bot application module."""
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from src.config import settings
from src.logger import get_logger, setup_logging
from src.database.engine import init_db, close_db
from src.bot.handlers import (
    admin_handlers,
    user_handlers,
    review_handlers,
    error_handler
)
from src.bot.middleware import AdminCheckMiddleware

logger = get_logger(__name__)


class CodeReviewBot:
    """Main bot application class."""
    
    def __init__(self):
        """Initialize the bot."""
        self.application = None
        setup_logging()
        
    async def post_init(self, application: Application) -> None:
        """Initialize resources after application is created."""
        logger.info("Initializing bot...")
        await init_db()
        logger.info("Bot initialized successfully")
        
    async def post_shutdown(self, application: Application) -> None:
        """Cleanup resources on shutdown."""
        logger.info("Shutting down bot...")
        await close_db()
        logger.info("Bot shutdown complete")
        
    def setup_handlers(self, app: Application) -> None:
        """Register all command and message handlers."""
        
        # Admin commands (with middleware check)
        admin_middleware = AdminCheckMiddleware()
        
        app.add_handler(CommandHandler("admin_create_team", admin_handlers.create_team_handler, filters=admin_middleware))
        app.add_handler(CommandHandler("admin_list_teams", admin_handlers.list_teams_handler, filters=admin_middleware))
        app.add_handler(CommandHandler("admin_add_user", admin_handlers.add_user_handler, filters=admin_middleware))
        app.add_handler(CommandHandler("admin_set_team_leader", admin_handlers.set_team_leader_handler, filters=admin_middleware))
        app.add_handler(CommandHandler("admin_remove_user", admin_handlers.remove_user_handler, filters=admin_middleware))
        app.add_handler(CommandHandler("admin_deactivate_user", admin_handlers.deactivate_user_handler, filters=admin_middleware))
        app.add_handler(CommandHandler("admin_activate_user", admin_handlers.activate_user_handler, filters=admin_middleware))
        app.add_handler(CommandHandler("admin_get_user_id", admin_handlers.get_user_id_handler, filters=admin_middleware))
        
        # User commands
        app.add_handler(CommandHandler("start", user_handlers.start_handler))
        app.add_handler(CommandHandler("help", user_handlers.help_handler))
        app.add_handler(CommandHandler("my_teams", user_handlers.my_teams_handler))
        
        # Review commands
        app.add_handler(CommandHandler("request_review", review_handlers.request_review_handler))
        
        # Callback query handlers
        app.add_handler(CallbackQueryHandler(review_handlers.handle_team_selection, pattern="^select_team:"))
        app.add_handler(CallbackQueryHandler(review_handlers.handle_review_action, pattern="^review_action:"))
        
        # Message handlers
        app.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'gitlab\.com.*merge_requests') & ~filters.COMMAND,
            review_handlers.handle_mr_links
        ))
        
        # Error handler
        app.add_error_handler(error_handler.handle_error)
        
        logger.info("All handlers registered")
        
    def create_application(self) -> Application:
        """Create and configure the bot application."""
        application = (
            Application.builder()
            .token(settings.bot_token)
            .post_init(self.post_init)
            .post_shutdown(self.post_shutdown)
            .build()
        )
        
        self.setup_handlers(application)
        self.application = application
        return application
        
    def run(self):
        """Run the bot."""
        if not self.application:
            self.application = self.create_application()
            
        logger.info("Starting bot...")
        self.application.run_polling(drop_pending_updates=True)


def main():
    """Main entry point."""
    bot = CodeReviewBot()
    bot.run()


if __name__ == "__main__":
    main()