import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest 

BOT_TOKEN = "8757097525:AAF9TkLFu7AkTM0mBZ1YHv3aXHZ6X4lTrtI"
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
        "📞 *Phone Number* (e.g., 9876543210)\n"
        "📧 *Email Address*\n\n"
        "⚠️ _All queries are monitored and logged._"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'clear':
        await query.message.delete()
    elif query.data == 'lookup':
        await query.message.reply_text("Provide a target identifier (Username, ID, Phone, or Email) to begin the scan.\n_Use /find in groups._", parse_mode='Markdown')

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

# --- ADVANCED ROUTING LOGIC ---
async def execute_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    user = update.effective_user
    clean_query = query.replace("+", "").replace(" ", "").strip()
    
    await send_log(context, f"Query Executed:\nUser: @{user.username} ({user.id})\nInput: {query}")
    processing_msg = await update.message.reply_text("📡 *ESTABLISHING SECURE UPLINK...*", parse_mode='Markdown')

    search_param = ""

    # 1. EMAIL DETECTION
    if "@" in query:
        search_param = query
        await processing_msg.edit_text("⚙️ *ANALYZING EMAIL ADDRESS...*\n_Scanning ToxicLabs Global Database..._", parse_mode='Markdown')

    # 2. PHONE / NUMERIC ID DETECTION
    elif clean_query.isdigit():
        if len(clean_query) == 10:
            search_param = f"91{clean_query}"
            await processing_msg.edit_text(f"⚙️ *FORMATTING PHONE NUMBER...*\n_Added +91 code. Scanning database..._", parse_mode='Markdown')
        else:
            search_param = clean_query
            await processing_msg.edit_text("⚙️ *PROCESSING NUMERIC ID/PHONE...*\n_Scanning ToxicLabs Global Database..._", parse_mode='Markdown')

    # 3. USERNAME DETECTION (Alphanumeric, no @)
    else:
        await processing_msg.edit_text("⚙️ *EXTRACTING TARGET UID...*\n_Resolving alias to internal Facebook ID..._", parse_mode='Markdown')
        resolved_id = resolve_username_to_id(query)
        if resolved_id:
            search_param = resolved_id
            await processing_msg.edit_text(f"✅ *TARGET ACQUIRED:* `{search_param}`\n_Decrypting database records..._", parse_mode='Markdown')
        else:
            await processing_msg.edit_text("⚠️ *RESOLUTION FAILED*\n_Unable to extract UID from alias. Please provide the exact FB ID, Phone, or Email._", parse_mode='Markdown')
            return

    # Protection Check
    if search_param in PROTECTED_IDS or query in PROTECTED_IDS:
        await processing_msg.edit_text("🛡️ *SECURITY BREACH BLOCKED*\n_Target data is strictly protected by ToxicLabs Protocol. Access Denied._", parse_mode='Markdown')
        await send_log(context, f"Blocked Query Attempt:\nUser: @{user.username}\nTarget: {query}")
        return

    # Database API Call
    try:
        payload = {"key": API_KEY, "query": search_param}
        response = requests.get(API_URL, params=payload, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            result_text = (
                f"🎯 *TOXIC DATABASE MATCH*\n"
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
                f"🔒 _Secured by ToxicLabs_"
            )
            keyboard = [[InlineKeyboardButton("🗑️ Close Intel", callback_data='clear')]]
            await processing_msg.edit_text(result_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            await send_log(context, f"Data Successfully Retrieved:\nTarget: {search_param}\nRequested by: @{user.username}")
        else:
            await processing_msg.edit_text("📭 *NO RECORDS FOUND*\n_Target does not exist in the current database index._", parse_mode='Markdown')

    except Exception as e:
        await processing_msg.edit_text("🛰️ *CONNECTION LOST*\n_API Offline or Connection Timeout. Try again._", parse_mode='Markdown')
        await send_log(context, f"API Error: {str(e)}")

# GROUP COMMAND HANDLER (/find <query>)
async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    if not context.args:
        await update.message.reply_text("⚠️ *SYNTAX ERROR*\n_Usage:_ `/find <username/phone/id/email>`", parse_mode='Markdown')
        return
        
    query = " ".join(context.args).strip()
    await execute_search(update, context, query)

# PRIVATE MESSAGE HANDLER (Direct texts)
async def private_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    # Ignore regular texts if they are sent in a group (forces users to use /find)
    if update.message.chat.type != 'private':
        return
        
    query = update.message.text.strip()
    await execute_search(update, context, query)

def main():
    # Proxy fix included
    t_request = HTTPXRequest(connection_pool_size=20, read_timeout=20)
    app = Application.builder().token(BOT_TOKEN).request(t_request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("protect", protect_user))
    app.add_handler(CommandHandler("find", find_command)) 
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, private_text_handler)) # Direct DM handler
    
    print("Toxic Security Bot is running smoothly with Smart Routing...")
    app.run_polling()

if __name__ == '__main__':
    main()
        
