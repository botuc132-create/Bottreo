import os
import json
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_IDS = {int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()}
DATA_FILE = Path(os.environ.get("DATA_FILE", "/tmp/ff_accounts.json"))
MAX_ACCOUNTS = 5
MAX_SELECTED = 4

def load_data():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"accounts": {}, "selected": [], "running": False}

def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def allowed(uid):
    return bool(ADMIN_IDS) and uid in ADMIN_IDS

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Thêm UID", callback_data="add"),
         InlineKeyboardButton("📋 Danh sách", callback_data="list")],
        [InlineKeyboardButton("🎯 Chọn tài khoản chạy", callback_data="select"),
         InlineKeyboardButton("▶️ Chạy", callback_data="run")],
        [InlineKeyboardButton("⏹ Dừng tất cả", callback_data="stop"),
         InlineKeyboardButton("🗑 Xóa UID", callback_data="delete")],
        [InlineKeyboardButton("📊 Trạng thái", callback_data="status"),
         InlineKeyboardButton("ℹ️ Trợ giúp", callback_data="help")]
    ])

def account_text(data, owner):
    accts = data["accounts"].get(str(owner), [])
    if not accts:
        return "Chưa có UID nào."
    selected = set(data.get("selected", {}).get(str(owner), []))
    return "\n".join(f"{i+1}. {'☑️' if a['uid'] in selected else '▫️'} UID {a['uid']}" + (f" — {a['label']}" if a.get("label") else "") for i,a in enumerate(accts))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not allowed(uid):
        await update.message.reply_text("Bạn chưa được cấp quyền admin. Hãy đặt ADMIN_IDS trên Railway bằng Telegram ID dạng số của bạn.")
        return
    await update.message.reply_text(
        "🎮 FREE FIRE MANAGER V2\n\n"
        "Quản lý tối đa 5 UID, chọn tối đa 4 UID và điều khiển trạng thái tác vụ.\n"
        "Lưu ý: nút Chạy/Dừng ở bản này chỉ điều khiển trạng thái của bot, chưa khởi chạy game hoặc tự vào trận. Muốn tự chơi cần một môi trường game từ xa tương thích và cơ chế điều khiển được hỗ trợ.",
        reply_markup=main_menu()
    )

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    owner = q.from_user.id
    if not allowed(owner):
        await q.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    data = load_data()
    owner_key = str(owner)
    data.setdefault("accounts", {}).setdefault(owner_key, [])
    data.setdefault("selected", {}).setdefault(owner_key, [])
    action = q.data

    if action == "add":
        if len(data["accounts"][owner_key]) >= MAX_ACCOUNTS:
            await q.message.reply_text("Đã đủ 5 UID. Xóa một UID trước khi thêm.")
            return
        context.user_data["awaiting_add"] = True
        await q.message.reply_text("Gửi UID hoặc theo mẫu: UID | tên ghi chú")
    elif action == "list":
        await q.message.reply_text(account_text(data, owner), reply_markup=main_menu())
    elif action == "select":
        accts = data["accounts"][owner_key]
        if not accts:
            await q.message.reply_text("Hãy thêm UID trước.")
            return
        selected = set(data["selected"][owner_key])
        rows = []
        for a in accts:
            mark = "☑️" if a["uid"] in selected else "⬜"
            rows.append([InlineKeyboardButton(f"{mark} {a['uid']}", callback_data=f"toggle:{a['uid']}")])
        rows.append([InlineKeyboardButton("✅ Xong", callback_data="list")])
        await q.message.reply_text("Chọn tối đa 4 tài khoản:", reply_markup=InlineKeyboardMarkup(rows))
    elif action.startswith("toggle:"):
        uid_value = action.split(":", 1)[1]
        selected = data["selected"][owner_key]
        if uid_value in selected:
            selected.remove(uid_value)
        elif len(selected) >= MAX_SELECTED:
            await q.message.reply_text("Chỉ được chọn tối đa 4 tài khoản.")
            return
        else:
            selected.append(uid_value)
        save_data(data)
        rows = []
        for a in data["accounts"][owner_key]:
            mark = "☑️" if a["uid"] in selected else "⬜"
            rows.append([InlineKeyboardButton(f"{mark} {a['uid']}", callback_data=f"toggle:{a['uid']}")])
        rows.append([InlineKeyboardButton("✅ Xong", callback_data="list")])
        await q.message.reply_text("Đã cập nhật lựa chọn.", reply_markup=InlineKeyboardMarkup(rows))
    elif action == "run":
        selected = data["selected"][owner_key]
        if not selected:
            await q.message.reply_text("Bạn cần chọn ít nhất một UID trước.")
            return
        data.setdefault("running", {})[owner_key] = True
        save_data(data)
        await q.message.reply_text(
            "▶️ Đã bật trạng thái điều phối cho các UID: " + ", ".join(selected) +
            "\n\nChú ý: đây chưa phải trạng thái đang chơi game. Chưa có game worker/API điều khiển được kết nối.",
            reply_markup=main_menu()
        )
    elif action == "stop":
        data.setdefault("running", {})[owner_key] = False
        save_data(data)
        await q.message.reply_text("⏹ Đã đặt trạng thái điều phối thành DỪNG.", reply_markup=main_menu())
    elif action == "status":
        selected = data["selected"][owner_key]
        running = data.get("running", {}).get(owner_key, False)
        await q.message.reply_text(
            f"UID đã lưu: {len(data['accounts'][owner_key])}/5\n"
            f"Đã chọn: {len(selected)}/4\n"
            f"Điều phối: {'ĐANG BẬT' if running else 'ĐANG DỪNG'}\n"
            "Game worker: CHƯA KẾT NỐI",
            reply_markup=main_menu()
        )
    elif action == "delete":
        accts = data["accounts"][owner_key]
        if not accts:
            await q.message.reply_text("Danh sách đang trống.")
            return
        rows = [[InlineKeyboardButton(f"🗑 {a['uid']}", callback_data=f"del:{a['uid']}")] for a in accts]
        await q.message.reply_text("Chọn UID cần xóa:", reply_markup=InlineKeyboardMarkup(rows))
    elif action.startswith("del:"):
        uid_value = action.split(":", 1)[1]
        data["accounts"][owner_key] = [a for a in data["accounts"][owner_key] if a["uid"] != uid_value]
        data["selected"][owner_key] = [u for u in data["selected"][owner_key] if u != uid_value]
        save_data(data)
        await q.message.reply_text("Đã xóa UID khỏi danh sách.", reply_markup=main_menu())
    elif action == "help":
        await q.message.reply_text(
            "Thêm UID: chỉ lưu UID/ghi chú, không phải thông tin đăng nhập.\n"
            "Chọn tài khoản chạy: chọn tối đa 4 trong 5 UID.\n"
            "Chạy/Dừng: điều khiển trạng thái điều phối.\n"
            "Không gửi mật khẩu, Access Token hoặc JWT vào bot. Để tự động chơi cần tích hợp môi trường game từ xa và cơ chế điều khiển hợp lệ.",
            reply_markup=main_menu()
        )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner = update.effective_user.id
    if not allowed(owner) or not context.user_data.get("awaiting_add"):
        return
    raw = update.message.text.strip()
    parts = [p.strip() for p in raw.split("|", 1)]
    uid_value = parts[0]
    label = parts[1] if len(parts) > 1 else ""
    if not uid_value.isdigit():
        await update.message.reply_text("UID phải là số. Ví dụ: 8293727855 | Acc 1")
        return
    data = load_data()
    owner_key = str(owner)
    data.setdefault("accounts", {}).setdefault(owner_key, [])
    data.setdefault("selected", {}).setdefault(owner_key, [])
    accounts = data["accounts"][owner_key]
    if any(a["uid"] == uid_value for a in accounts):
        msg = "UID này đã có trong danh sách."
    elif len(accounts) >= MAX_ACCOUNTS:
        msg = "Đã đủ 5 UID."
    else:
        accounts.append({"uid": uid_value, "label": label})
        save_data(data)
        msg = f"Đã lưu UID {uid_value}. Tiếp theo chọn 🎯 Chọn tài khoản chạy."
    context.user_data["awaiting_add"] = False
    await update.message.reply_text(msg, reply_markup=main_menu())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
