import telebot
import random
import os

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = telebot.TeleBot(TOKEN)

# Store who passed captcha and their expected answer
passed_users = {}
captcha_answers = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in passed_users:
        bot.reply_to(message, "✅ You already passed! Send your offer now.")
        return
    
    # Create simple math captcha
    x = random.randint(1, 10)
    y = random.randint(1, 10)
    captcha_answers[user_id] = x + y
    
    bot.reply_to(message, f"🤖 Prove you're human!\n\nWhat is **{x} + {y}**?\n\nJust reply with the number.")

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Check if user is solving captcha
    if user_id in captcha_answers:
        try:
            if int(message.text) == captcha_answers[user_id]:
                passed_users[user_id] = True
                del captcha_answers[user_id]
                bot.reply_to(message, "✅ Correct! Now send your offer or message.")
            else:
                bot.reply_to(message, "❌ Wrong number. Try /start again.")
        except:
            bot.reply_to(message, "❌ Please send only the number.")
        return
    
    # If passed captcha → forward to you
    if user_id in passed_users:
        bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
        bot.send_message(OWNER_ID, f"📨 From: @{message.from_user.username or 'NoUsername'} (ID: {user_id})")
        bot.reply_to(message, "✅ Sent! Waiting for reply...")
        return
    
    bot.reply_to(message, "Please type /start first.")

# Auto reply from you back to the user
@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID)
def owner_reply(message):
    if message.reply_to_message and message.reply_to_message.forward_from:
        original_id = message.reply_to_message.forward_from.id
        bot.send_message(original_id, f"💬 Reply from owner:\n\n{message.text}")
        bot.reply_to(message, "✅ Reply sent!")
    else:
        bot.reply_to(message, "Reply to a forwarded message to answer the user.")

print("Bot is running...")
bot.infinity_polling()
