import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_IDS = {int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()}
DB_PATH = os.environ.get("DB_PATH", "/tmp/accounts.db")
MAX_ACCOUNTS = 5

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        uid TEXT NOT NULL,
        label TEXT NOT NULL DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_id, uid)
    )""")
    return conn

def is_admin(user_id: int) -> bool:
    return not ADMIN_IDS or user_id in ADMIN_IDS

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Thêm UID", callback_data="add"),
         InlineKeyboardButton("📋 Danh sách", callback_data="list")],
        [InlineKeyboardButton("🗑 Xóa tài khoản", callback_data="delete"),
         InlineKeyboardButton("ℹ️ Trợ giúp", callback_data="help")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    await update.message.reply_text(
        "🎮 FREE FIRE ACCOUNT MANAGER\\n\\nQuản lý tối đa 5 UID. "
        "Bản này chỉ lưu UID/ghi chú, không đăng nhập game hoặc tự động chơi trận.",
        reply_markup=menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if not is_admin(uid):
        await q.edit_message_text("Bạn không có quyền sử dụng bot.")
        return
    if q.data == "add":
        context.user_data["awaiting"] = "add"
        await q.message.reply_text("Gửi theo mẫu: UID hoặc UID | tên ghi chú")
    elif q.data == "list":
        conn = db()
        rows = conn.execute("SELECT id, uid, label FROM accounts WHERE owner_id=? ORDER BY id", (uid,)).fetchall()
        conn.close()
        if not rows:
            await q.message.reply_text("Chưa có tài khoản nào được lưu.")
        else:
            await q.message.reply_text("\\n".join(f"{i}. UID: {u}" + (f" — {l}" if l else "") for i,u,l in rows))
    elif q.data == "delete":
        conn = db()
        rows = conn.execute("SELECT id, uid FROM accounts WHERE owner_id=? ORDER BY id", (uid,)).fetchall()
        conn.close()
        if not rows:
            await q.message.reply_text("Danh sách đang trống.")
        else:
            kb = [[InlineKeyboardButton(f"Xóa {u}", callback_data=f"del:{i}")] for i,u in rows]
            await q.message.reply_text("Chọn UID cần xóa:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("del:"):
        account_id = int(q.data.split(":",1)[1])
        conn = db()
        conn.execute("DELETE FROM accounts WHERE id=? AND owner_id=?", (account_id, uid))
        conn.commit()
        conn.close()
        await q.message.reply_text("Đã xóa UID khỏi danh sách.")
    elif q.data == "help":
        await q.message.reply_text("Dùng ➕ Thêm UID để lưu UID và ghi chú; 📋 Danh sách để xem; 🗑 để xóa. Không gửi mật khẩu, Access Token hoặc JWT vào bot.")

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    if context.user_data.get("awaiting") != "add":
        await update.message.reply_text("Chọn chức năng trong menu /start.")
        return
    raw = update.message.text.strip()
    parts = [p.strip() for p in raw.split("|", 1)]
    uid = parts[0]
    label = parts[1] if len(parts) > 1 else ""
    if not uid.isdigit():
        await update.message.reply_text("UID cần là dãy số. Hãy gửi lại theo mẫu: 123456789 hoặc 123456789 | Acc 1")
        return
    conn = db()
    count = conn.execute("SELECT COUNT(*) FROM accounts WHERE owner_id=?", (user.id,)).fetchone()[0]
    exists = conn.execute("SELECT 1 FROM accounts WHERE owner_id=? AND uid=?", (user.id, uid)).fetchone()
    if exists:
        await update.message.reply_text("UID này đã có trong danh sách.")
    elif count >= MAX_ACCOUNTS:
        await update.message.reply_text("Đã đạt giới hạn 5 tài khoản. Hãy xóa một UID trước.")
    else:
        conn.execute("INSERT INTO accounts(owner_id, uid, label) VALUES(?,?,?)", (user.id, uid, label))
        conn.commit()
        await update.message.reply_text(f"Đã lưu UID {uid}.", reply_markup=menu())
    conn.close()
    context.user_data["awaiting"] = None

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
