import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest # <-- Added to fix the proxy error

BOT_TOKEN = "8757097525:AAHQsVICcAk6kJbavPxjmKkgWSzmYUvIj0A"
API_URL = "http://16.171.30.40:5000/api"
API_KEY = "toxic"
LOG_GROUP_ID = -1002843633996
OWNER_ID = 6944519938

PROTECTED_IDS = set()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def send_log(context: ContextTypes.DEFAULT_TYPE, message: str):
    try:
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=f"🔒 [SYSTEM LOG]\n{message}")
    except Exception as e:
        logging.error(f"Failed to send log: {e}")

def resolve_username_to_id(username: str) -> str:
    try:
        url = f"https://www.facebook.com/{username}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            match = re.search(r'"userID":"(\d+)"', response.text)
            if match:
                return match.group(1)
            
            match_alt = re.search(r'content="fb://profile/(\d+)"', response.text)
            if match_alt:
                return match_alt.group(1)
    except Exception:
        pass
    return ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await send_log(context, f"User Started Bot:\nName: {user.full_name}\nUsername: @{user.username}\nID: {user.id}")

    keyboard = [
        [InlineKeyboardButton("🔍 Lookup Target", callback_data='lookup')],
        [InlineKeyboardButton("📚 API Details", url='https://toxiclabs.xyz/api')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"⚡ *TOXIC OSINT SECURITY BOT*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome, {user.first_name}! This is a secure environment.\n\n"
        "Input any of the following to scan the database:\n"
        "👤 *FB Username* (e.g., markzuckerberg)\n"
        "🆔 *FB ID* (e.g., 100018888...)\n"
        "📞 *Phone Number* (e.g., 91987654...)\n"
        "📧 *Email Address*\n\n"
        "⚠️ _All queries are monitored and logged._"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the inline button clicks to make the UI interactive."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'clear':
        await query.message.delete()
    elif query.data == 'lookup':
        await query.message.reply_text("Provide a target identifier (Username, ID, Phone, or Email) to begin the scan.", parse_mode='Markdown')

async def protect_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ *Syntax:* `/protect <fb_id>`", parse_mode='Markdown')
        return

    target_id = context.args[0]
    PROTECTED_IDS.add(target_id)
    await update.message.reply_text(f"✅ ID `{target_id}` is now securely protected.")
    await send_log(context, f"Admin Protected ID: {target_id}")

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # --- ERROR FIX APPLIED HERE ---
    if not update.message or not update.message.text:
        return
    # ------------------------------

    query = update.message.text.strip()
    user = update.effective_user
    
    await send_log(context, f"Query Executed:\nUser: @{user.username} ({user.id})\nSearch Term: {query}")
    processing_msg = await update.message.reply_text("🔄 *Establishing secure connection & scanning...*", parse_mode='Markdown')

    search_param = query
    if "@" not in query and not query.isdigit():
        await processing_msg.edit_text("🔄 *Resolving username to internal ID...*", parse_mode='Markdown')
        resolved_id = resolve_username_to_id(query)
        if resolved_id:
            search_param = resolved_id
            await processing_msg.edit_text(f"✅ *Target Identified:* `{search_param}`\n🔄 *Extracting data...*", parse_mode='Markdown')
        else:
            await processing_msg.edit_text("❌ *Resolution Failed.* Please provide the exact FB ID, Phone, or Email.", parse_mode='Markdown')
            return

    if search_param in PROTECTED_IDS or query in PROTECTED_IDS:
        await processing_msg.edit_text("🛑 *ACCESS DENIED: User data protected by Toxic Security Protocol.*", parse_mode='Markdown')
        await send_log(context, f"Blocked Query Attempt:\nUser: @{user.username}\nTarget: {query}")
        return

    try:
        payload = {"key": API_KEY, "query": search_param}
        response = requests.get(API_URL, params=payload, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            # Professional UI formatting for OSINT tools
            result_text = (
                f"🎯 *MATCH FOUND IN DATABASE*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Full Name:* `{data.get('first_name', 'N/A')} {data.get('last_name', '')}`\n"
                f"🆔 *Facebook ID:* `{data.get('fb_id', 'N/A')}`\n"
                f"📞 *Mobile No:* `{data.get('phone', 'N/A')}`\n"
                f"🏙️ *Current City:* `{data.get('current_city', 'N/A')}`\n"
                f"🏠 *Hometown:* `{data.get('hometown', 'N/A')}`\n"
                f"💼 *Occupation:* `{data.get('work', 'N/A')}`\n"
                f"💍 *Status:* `{data.get('relationship', 'N/A')}`\n"
                f"⏱️ *Data Timestamp:* `{data.get('timestamp', 'N/A')}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔒 _Secured by Toxic_"
            )
            keyboard = [[InlineKeyboardButton("🗑️ Clear Result", callback_data='clear')]]
            await processing_msg.edit_text(result_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            await send_log(context, f"Data Successfully Retrieved:\nTarget: {search_param}\nRequested by: @{user.username}")
        else:
            await processing_msg.edit_text("❌ *No matching records found in the database.*", parse_mode='Markdown')

    except Exception as e:
        await processing_msg.edit_text("⚠️ *API Offline or Connection Timeout.*", parse_mode='Markdown')
        await send_log(context, f"API Error: {str(e)}")

def main():
    # Use HTTPXRequest to bypass the httpx proxy error
    t_request = HTTPXRequest(connection_pool_size=20, read_timeout=20)
    app = Application.builder().token(BOT_TOKEN).request(t_request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("protect", protect_user))
    app.add_handler(CallbackQueryHandler(button_handler)) # Added handler for inline buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    
    print("Toxic Security Bot is running smoothly...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
