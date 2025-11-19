import telebot
from telebot import types

# === তোমার তথ্য বসাও ===
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"          # BotFather থেকে নাও
ADMIN_ID = 1651695602                    # তোমার Telegram ID (@nurul_nc এর ID)
PRICE_PER_MAIL = 3                      # প্রতি মেইল ৩ টাকা

PAYMENT_INFO = """💳 Payment Methods:

🔴 bKash: 01815243007
🟢 Nagad: 01815243007
🔵 Rocket: 01815243007

**Total Amount: {total} Taka** ({quantity} × {price} Tk per mail)

📤 Send **screenshot** after payment."""

# === বাকি কোড ===
user_data = {}  # {user_id: {'state': '...', 'quantity': 5, 'total': 15, 'admin_msg_id': ...}}

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn_order = types.InlineKeyboardButton("🛒 Buy .EDU Email", callback_data="order")
    markup.add(btn_order)
    
    bot.send_message(message.chat.id, 
                     "🌟 **.EDU Email Seller Bot** 🌟\n\n"
                     "💰 **Price: 3 Taka per mail**\n"
                     "✅ Instant delivery after payment\n"
                     "🚀 GitHub Pack, Spotify, Office 365, etc.",
                     parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "order")
def order_callback(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="📋 Order .EDU Email")
    
    user_data[call.from_user.id] = {"state": "waiting_quantity"}
    bot.send_message(call.message.chat.id, 
                     "📦 **কতগুলো .EDU মেইল কিনবেন?**\n\n"
                     "শুধু সংখ্যা লিখুন (যেমন: `5`)",
                     parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in user_data and user_data[m.from_user.id]["state"] == "waiting_quantity")
def handle_quantity(message):
    user_id = message.from_user.id
    try:
        quantity = int(message.text.strip())
        if quantity < 1:
            raise ValueError
    except:
        bot.send_message(user_id, "❌ শুধু পজিটিভ সংখ্যা লিখুন (যেমন: 5)")
        return
    
    total = quantity * PRICE_PER_MAIL
    user_data[user_id].update({
        "quantity": quantity,
        "total": total,
        "state": "waiting_screenshot"
    })
    
    bot.send_message(user_id, PAYMENT_INFO.format(
        total=total, quantity=quantity, price=PRICE_PER_MAIL
    ), parse_mode="Markdown")
    
    bot.send_message(user_id, "📤 এখন **পেমেন্ট স্ক্রিনশট** পাঠান।", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'],
                     func=lambda m: m.from_user.id in user_data and user_data[m.from_user.id]["state"] == "waiting_screenshot")
def handle_photo(message):
    user_id = message.from_user.id
    data = user_data[user_id]
    quantity = data["quantity"]
    total = data["total"]
    
    # Forward screenshot
    forwarded = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    
    username = message.from_user.username or "No username"
    full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    
    admin_text = (f"🟢 **NEW ORDER** 🟢\n\n"
                  f"👤 **User**: {full_name}\n"
                  f"🆔 **ID**: <code>{user_id}</code>\n"
                  f"✏️ **Username**: @{username}\n"
                  f"📦 **Quantity**: {quantity} mail(s)\n"
                  f"💰 **Total**: {total} Taka\n\n"
                  f"📸 Screenshot received. Waiting for **Transaction ID**...")
    
    sent = bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_to_message_id=forwarded.message_id)
    
    bot.send_message(user_id, "✅ স্ক্রিনশট পাওয়া গেছে!\n\n🔤 এখন **Transaction ID** লিখুন।", parse_mode="Markdown")
    
    user_data[user_id].update({
        "state": "waiting_txnid",
        "admin_msg_id": sent.message_id
    })

@bot.message_handler(func=lambda m: m.from_user.id in user_data and user_data[m.from_user.id]["state"] == "waiting_txnid")
def handle_txnid(message):
    user_id = message.from_user.id
    txn_id = message.text.strip()
    data = user_data[user_id]
    
    bot.send_message(ADMIN_ID, 
                     f"🔤 **Transaction ID**: <code>{txn_id}</code>", 
                     parse_mode="HTML",
                     reply_to_message_id=data["admin_msg_id"])
    
    bot.send_message(user_id, 
                     "🎯 **অর্ডার গৃহীত!**\n\n"
                     "⏳ এডমিন পেমেন্ট চেক করছেন...\n"
                     f"📦 {data['quantity']}টা মেইল ৫-১০ মিনিটে পাবেন।\n"
                     "ধন্যবাদ ❤️",
                     parse_mode="Markdown")
    
    user_data.pop(user_id, None)

# Admin Approve ( to send multiple mails
@bot.message_handler(commands=['approve'])
def approve_order(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            raise ValueError
        
        target_id = int(parts[1])
        qty_wanted = int(parts[2])
        mails = parts[3:]  # rest are mail:pass
        
        if len(mails) != qty_wanted:
            bot.send_message(ADMIN_ID, f"❌ ভুল! চেয়েছে {qty_wanted}টা, দিয়েছো {len(mails)}টা।")
            return
        
        mail_text = "\n".join([f"📧 <code>{m}</code>" for m in mails])
        
        bot.send_message(target_id,
                         "🎉 **পেমেন্ট ভেরিফাইড!**\n\n"
                         "✅ আপনার .EDU মেইলগুলো:\n\n"
                        f"{mail_text}\n\n"
                         "🔐 তৎক্ষণাৎ পাসওয়ার্ড চেঞ্জ করুন!\n"
                         "❤️ ধন্যবাদ!",
                         parse_mode="HTML")
        
        bot.send_message(ADMIN_ID, f"✅ {qty_wanted}টা মেইল পাঠানো হয়েছে → {target_id}")
    
    except Exception as e:
        bot.send_message(ADMIN_ID, 
                         "❌ **ভুল ফরম্যাট!**\n\n"
                         "ব্যবহার:\n"
                         "<code>/approve user_id qty mail1:pass1 mail2:pass2 ...</code>",
                         parse_mode="HTML")

# Fallback
@bot.message_handler(func=lambda m: True)
def fallback(message):
    if message.from_user.id not in user_data:
        bot.send_message(message.chat.id, "👋 /start চেপে অর্ডার দিন।")

bot.infinity_polling()