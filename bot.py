import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)")
cur.execute("""
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    link TEXT,
    status TEXT
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Barka da zuwa 👋\nTura link domin submission.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.startswith("http"):
        return
    user_id = update.message.from_user.id
    link = update.message.text
    cur.execute("INSERT INTO submissions (user_id, link, status) VALUES (?, ?, ?)", (user_id, link, "pending"))
    conn.commit()
    sub_id = cur.lastrowid
    keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{sub_id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"reject_{sub_id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 New Submission\nUser ID: {user_id}\nLink: {link}", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("⏳ An karɓi link ɗinka, ana jira dubawa.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, sub_id = query.data.split("_")
    sub_id = int(sub_id)
    cur.execute("SELECT user_id FROM submissions WHERE id = ?", (sub_id,))
    row = cur.fetchone()
    if not row:
        return
    user_id = row[0]
    if action == "approve":
        cur.execute("UPDATE submissions SET status='approved' WHERE id=?", (sub_id,))
        cur.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?, 0)", (user_id,))
        cur.execute("UPDATE users SET points = points + 5 WHERE user_id=?", (user_id,))
        conn.commit()
        await context.bot.send_message(user_id, "✅ Approved! +5 points")
    else:
        cur.execute("UPDATE submissions SET status='rejected' WHERE id=?", (sub_id,))
        conn.commit()
        await context.bot.send_message(user_id, "❌ An ƙi submission ɗinka.")
    await query.edit_message_text("✔️ An gama dubawa")

async def mypoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    await update.message.reply_text(f"⭐ Points ɗinka: {row[0] if row else 0}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mypoints", mypoints))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(button))
app.run_polling()
