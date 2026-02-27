import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8757097525:AAHQsVICcAk6kJbavPxjmKkgWSzmYUvIj0A"
API_URL = "https://toxiclabs.xyz/api/v2"
API_KEY = "toxic-key-test"
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
        [InlineKeyboardButton("🔍 Lookup Database", callback_data='lookup')],
        [InlineKeyboardButton("📚 API Documentation", url='https://toxiclabs.xyz/api')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"⚡ *Welcome to Toxic Security OSINT Bot, {user.first_name}!*\n\n"
        "Send any target information to query the database:\n"
        "🔹 *FB Username* (e.g., markzuckerberg)\n"
        "🔹 *FB ID* (e.g., 100018888...)\n"
        "🔹 *Phone Number* (e.g., 91987654...)\n"
        "🔹 *Email Address*\n\n"
        "_Note: All queries are logged for security purposes._"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def protect_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Syntax: `/protect <fb_id>`", parse_mode='Markdown')
        return

    target_id = context.args[0]
    PROTECTED_IDS.add(target_id)
    await update.message.reply_text(f"✅ ID `{target_id}` is now securely protected.")
    await send_log(context, f"Admin added Protection for ID: {target_id}")

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    user = update.effective_user
    
    await send_log(context, f"Query Executed:\nUser: @{user.username} ({user.id})\nSearch Term: {query}")
    processing_msg = await update.message.reply_text("🔄 *Encrypting connection & scanning database...*", parse_mode='Markdown')

    search_param = query
    if "@" not in query and not query.isdigit():
        await processing_msg.edit_text("🔄 *Resolving username to Facebook ID...*", parse_mode='Markdown')
        resolved_id = resolve_username_to_id(query)
        if resolved_id:
            search_param = resolved_id
            await processing_msg.edit_text(f"✅ *Resolved ID:* `{search_param}`\n🔄 *Scanning database...*", parse_mode='Markdown')
        else:
            await processing_msg.edit_text("❌ *Failed to resolve username to FB ID. Please enter ID manually.*", parse_mode='Markdown')
            return

    if search_param in PROTECTED_IDS or query in PROTECTED_IDS:
        await processing_msg.edit_text("🛑 *User data protect by Toxic Security*", parse_mode='Markdown')
        await send_log(context, f"Blocked Query (Protected Data):\nUser: @{user.username}\nAttempted: {query}")
        return

    try:
        payload = {"key": API_KEY, "query": search_param}
        response = requests.get(API_URL, params=payload, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            result_text = (
                f"✅ *MATCH FOUND IN DATABASE*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Name:* {data.get('first_name', '')} {data.get('last_name', '')}\n"
                f"🆔 *FB ID:* `{data.get('fb_id', 'N/A')}`\n"
                f"📱 *Phone:* `{data.get('phone', 'N/A')}`\n"
                f"📍 *City:* {data.get('current_city', 'N/A')} ({data.get('hometown', 'N/A')})\n"
                f"💼 *Work:* {data.get('work', 'N/A')}\n"
                f"💍 *Status:* {data.get('relationship', 'N/A')}\n"
                f"🕒 *Last Seen DB:* {data.get('timestamp', 'N/A')}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            keyboard = [[InlineKeyboardButton("🗑️ Clear Result", callback_data='clear')]]
            await processing_msg.edit_text(result_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            await send_log(context, f"Success:\nSent data for {search_param} to @{user.username}")
        else:
            await processing_msg.edit_text("*No matching records found in the database.*", parse_mode='Markdown')

    except Exception as e:
        await processing_msg.edit_text("⚠️ *API Offline or Connection Timeout.*", parse_mode='Markdown')
        await send_log(context, f"API Error: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("protect", protect_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    app.run_polling()

if __name__ == '__main__':
    main()
                                       
