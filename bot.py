import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

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
        UNIQUE(owner_id, uid)
    )""")
    return conn

def allowed(user_id):
    return not ADMIN_IDS or user_id in ADMIN_IDS

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Thêm UID", callback_data="add"),
         InlineKeyboardButton("📋 Danh sách", callback_data="list")],
        [InlineKeyboardButton("🗑 Xóa UID", callback_data="delete"),
         InlineKeyboardButton("ℹ️ Trợ giúp", callback_data="help")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        await update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    await update.message.reply_text(
        "🎮 FREE FIRE ACCOUNT MANAGER\n\nQuản lý tối đa 5 UID. "
        "Bản này chỉ lưu UID/ghi chú; không đăng nhập game hoặc tự động chơi trận.",
        reply_markup=menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    owner = q.from_user.id
    if not allowed(owner):
        await q.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    if q.data == "add":
        context.user_data["awaiting"] = True
        await q.message.reply_text("Gửi UID hoặc theo mẫu: UID | tên ghi chú")
    elif q.data == "list":
        conn = db()
        rows = conn.execute("SELECT id, uid, label FROM accounts WHERE owner_id=? ORDER BY id", (owner,)).fetchall()
        conn.close()
        await q.message.reply_text("\n".join(f"{n}. UID {u}" + (f" — {label}" if label else "") for n, (_,u,label) in enumerate(rows, 1)) or "Chưa có UID nào.")
    elif q.data == "delete":
        conn = db()
        rows = conn.execute("SELECT id, uid FROM accounts WHERE owner_id=? ORDER BY id", (owner,)).fetchall()
        conn.close()
        if not rows:
            await q.message.reply_text("Danh sách đang trống.")
        else:
            await q.message.reply_text("Chọn UID cần xóa:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Xóa {u}", callback_data=f"del:{i}")] for i,u in rows]))
    elif q.data.startswith("del:"):
        conn = db()
        conn.execute("DELETE FROM accounts WHERE id=? AND owner_id=?", (int(q.data.split(":")[1]), owner))
        conn.commit()
        conn.close()
        await q.message.reply_text("Đã xóa UID.")
    elif q.data == "help":
        await q.message.reply_text("Không gửi mật khẩu, Access Token hoặc JWT vào bot. Dùng menu để thêm, xem hoặc xóa UID.")

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner = update.effective_user.id
    if not allowed(owner) or not context.user_data.get("awaiting"):
        return
    parts = [p.strip() for p in update.message.text.split("|", 1)]
    uid, label = parts[0], parts[1] if len(parts) > 1 else ""
    if not uid.isdigit():
        await update.message.reply_text("UID phải là dãy số. Gửi lại theo mẫu: 123456789 | Acc 1")
        return
    conn = db()
    count = conn.execute("SELECT COUNT(*) FROM accounts WHERE owner_id=?", (owner,)).fetchone()[0]
    exists = conn.execute("SELECT 1 FROM accounts WHERE owner_id=? AND uid=?", (owner, uid)).fetchone()
    if exists:
        msg = "UID này đã được lưu."
    elif count >= MAX_ACCOUNTS:
        msg = "Đã đủ 5 UID. Hãy xóa một UID trước."
    else:
        conn.execute("INSERT INTO accounts(owner_id, uid, label) VALUES(?,?,?)", (owner, uid, label))
        conn.commit()
        msg = f"Đã lưu UID {uid}."
    conn.close()
    context.user_data["awaiting"] = False
    await update.message.reply_text(msg, reply_markup=menu())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
