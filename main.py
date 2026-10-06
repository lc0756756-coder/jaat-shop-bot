import os, json, sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
UPI_ID = os.getenv("UPI_ID", "your@upi")
API_URL = os.getenv("API_URL", "")
API_KEY = os.getenv("PANEL_API_KEY", "")

# Database Setup
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT, category TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS plans (id TEXT PRIMARY KEY, product_id TEXT, name TEXT, price INTEGER, desc TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS plan_keys (plan_id TEXT, key_data TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT)")
conn.commit()

def get_setting(k, default=""):
    cur.execute("SELECT v FROM settings WHERE k=?", (k,))
    r = cur.fetchone()
    return r[0] if r else default

def set_setting(k,v):
    cur.execute("INSERT OR REPLACE INTO settings(k,v) VALUES(?,?)", (k,v))
    conn.commit()

# --- ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= OWNER_ID: return
    buttons = [
        [InlineKeyboardButton("🖼️ Set Profile Photo", callback_data="set_photo")],
        [InlineKeyboardButton("➕ Add Plan", callback_data="add_plan")],
        [InlineKeyboardButton("🔑 Add Plan Keys", callback_data="add_keys")],
        [InlineKeyboardButton("✏️ Edit Plan", callback_data="edit_plan")],
        [InlineKeyboardButton("🗑️ Delete Plan", callback_data="del_plan")],
        [InlineKeyboardButton("✏️ Edit Product", callback_data="edit_product")],
        [InlineKeyboardButton("🗑️ Delete Product", callback_data="del_product")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("👥 User List", callback_data="user_list")],
        [InlineKeyboardButton("💰 Add User Balance", callback_data="add_balance")],
        [InlineKeyboardButton("📄 Proof Link", callback_data="proof_link")],
        [InlineKeyboardButton("📖 HowTo Link", callback_data="howto_link")],
        [InlineKeyboardButton("💬 Support Username", callback_data="support")],
        [InlineKeyboardButton("🔑 API Key", callback_data="api_key")],
        [InlineKeyboardButton("⬇️ Back to Menu", callback_data="back_menu")],
    ]
    text = "👑 **ADMIN PANEL - Sbsnskksmsm Bot**\n\nJo kaam karna hai button dabao:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    context.user_data['action'] = data

    prompts = {
        "add_product": "Product Add Karo Format me:\n`Name | Category`\nEx: `Netflix | OTT`",
        "add_plan": "Plan Add Karo:\n`ProductID | PlanName | Price | Description`\nEx: `NETFLIX | 1 Month | 149 | 1 Screen`",
        "add_keys": "Plan Keys Add Karo:\n`PlanID | key1,key2,key3`\nEx: `PLAN1 | abc@mail.com:pass123, xyz@mail.com:pass456`",
        "edit_plan": "Edit Plan:\n`PlanID | NewName | NewPrice`",
        "del_plan": "Delete Plan ke liye PlanID bhejo:",
        "edit_product": "Edit Product:\n`ProductID | NewName`",
        "del_product": "Delete Product ke liye ProductID bhejo:",
        "broadcast": "Jo message sab users ko bhejna hai wo likho:",
        "add_balance": "Balance Add:\n`UserID | Amount`\nEx: `123456789 | 100`",
        "proof_link": "Proof Channel Link bhejo:",
        "howto_link": "HowTo Video/Channel Link bhejo:",
        "support": "Support Username bhejo: @username",
        "api_key": f"Current API Key: {API_KEY}\nNayi API Key bhejo ya /skip karo",
        "set_photo": "Bot ki Profile Photo bhejo (Photo as file send karo)"
    }
    if data in prompts:
        await q.message.reply_text(prompts[data])

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= OWNER_ID: return
    action = context.user_data.get('action')
    text = update.message.text

    if action == "add_product":
        try:
            name, cat = [x.strip() for x in text.split("|")]
            pid = name.upper().replace(" ","_")[:10]
            cur.execute("INSERT INTO products VALUES(?,?,?)", (pid, name, cat))
            conn.commit()
            await update.message.reply_text(f"✅ Product Added: {name} ({pid})")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    elif action == "add_plan":
        try:
            prod_id, pname, price, desc = [x.strip() for x in text.split("|")]
            plan_id = f"{prod_id}_{pname}".upper().replace(" ","_")
            cur.execute("INSERT INTO plans VALUES(?,?,?,?,?)", (plan_id, prod_id, pname, int(price), desc))
            conn.commit()
            await update.message.reply_text(f"✅ Plan Added: {plan_id} - ₹{price}")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    elif action == "add_keys":
        try:
            plan_id, keys_str = text.split("|")
            keys = [k.strip() for k in keys_str.split(",")]
            for k in keys:
                cur.execute("INSERT INTO plan_keys VALUES(?,?)", (plan_id.strip().upper(), k))
            conn.commit()
            await update.message.reply_text(f"✅ {len(keys)} Keys Added to {plan_id}")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    elif action == "add_balance":
        uid, amt = [x.strip() for x in text.split("|")]
        cur.execute("INSERT OR IGNORE INTO users(user_id,balance) VALUES(?,0)", (int(uid),))
        cur.execute("UPDATE users SET balance = balance +? WHERE user_id=?", (int(amt), int(uid)))
        conn.commit()
        await update.message.reply_text(f"✅ ₹{amt} Added to {uid}")

    elif action in ["proof_link","howto_link","support","api_key"]:
        set_setting(action, text)
        await update.message.reply_text(f"✅ {action} Save Ho Gaya: {text}")

    context.user_data['action'] = None

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (update.effective_user.id,))
    conn.commit()
    kb = [[InlineKeyboardButton("🛒 Shop", callback_data="shop")],[InlineKeyboardButton("💰 My Balance", callback_data="my_bal")]]
    if update.effective_user.id == OWNER_ID:
        kb.append([InlineKeyboardButton("👑 Admin Panel", callback_data="open_admin")])
    await update.message.reply_text("Welcome To Store 🔥", reply_markup=InlineKeyboardMarkup(kb))

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(admin_panel, pattern="open_admin"))
app.add_handler(CallbackQueryHandler(handle_buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.run_polling()