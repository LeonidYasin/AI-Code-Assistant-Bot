"""Message handler for processing natural language commands"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from .nlp_processor import nlp_processor

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and process them as natural language commands"""
    if not update.message or not update.message.text:
        return
    
    # Skip commands (they are handled by command handlers)
    if update.message.text.startswith('/'):
        return
    
    # Set chat_id for CLI mode
    if not hasattr(context, '_chat_id'):
        context._chat_id = 0  # Default chat_id for CLI
    
    # Process the message
    try:
        success, response = await nlp_processor.process_command(update.message.text, context)
        
        if success:
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text(response)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Произошла ошибка при обработке запроса: {str(e)}")
