import telebot
import random
import os
import sys

# ───────────────────────────────────────────────
# Get secrets safely from environment (Render)
# ───────────────────────────────────────────────

TOKEN = os.getenv("TOKEN")
OWNER_ID_STR = os.getenv("OWNER_ID")

# Safety checks → print helpful messages to Render logs
if not TOKEN:
    print("ERROR: Missing TOKEN environment variable!")
    print("→ Go to Render dashboard → Environment → Add variable 'TOKEN'")
    sys.exit(1)

if not OWNER_ID_STR:
    print("ERROR: Missing OWNER_ID environment variable!")
    print("→ Go to Render dashboard → Environment → Add variable 'OWNER_ID'")
    sys.exit(1)

try:
    OWNER_ID = int(OWNER_ID_STR)
except ValueError:
    print(f"ERROR: OWNER_ID must be a valid number. You set: '{OWNER_ID_STR}'")
    sys.exit(1)

print(f"Bot starting | Owner ID: {OWNER_ID} | Token looks valid")

# ───────────────────────────────────────────────
# Initialize bot
# ───────────────────────────────────────────────

bot = telebot.TeleBot(TOKEN)

# Track verified users and their captcha answers
verified_users = set()
captcha_answers = {}   # user_id → expected answer

# ───────────────────────────────────────────────
# /start command – show captcha
# ───────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id

    if user_id in verified_users:
        bot.reply_to(message, "You are already verified. Send your message or offer now.")
        return

    # Generate simple math captcha
    a = random.randint(3, 15)
    b = random.randint(3, 15)
    captcha_answers[user_id] = a + b

    text = (
        "Verification required\\n\\n"
        f"What is **{a} + {b}**?\\n\\n"
        "Reply with **only the number** (example: 12)"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

# ───────────────────────────────────────────────
# Handle all other messages
# ───────────────────────────────────────────────

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # User is answering captcha
    if user_id in captcha_answers:
        try:
            answer = int(text)
            if answer == captcha_answers[user_id]:
                verified_users.add(user_id)
                del captcha_answers[user_id]
                bot.reply_to(message, "Verified! Now send your message, offer, question, etc.")
            else:
                bot.reply_to(message, "Wrong answer. Type /start to try again.")
        except ValueError:
            bot.reply_to(message, "Please reply with only a number.")
        return

    # User already passed → forward to owner
    if user_id in verified_users:
        # Forward the original message
        bot.forward_message(OWNER_ID, message.chat.id, message.message_id)

        # Add sender info
        username = message.from_user.username
        sender_info = f"From: @{username}" if username else f"From ID: {user_id}"
        bot.send_message(OWNER_ID, f"New message\\n{sender_info}")

        bot.reply_to(message, "Message sent to the owner. You'll get a reply soon if they respond.")
        return

    # Fallback – didn't start correctly
    bot.reply_to(message, "Please type /start first.")

# ───────────────────────────────────────────────
# Owner replies to forwarded messages → send back to user
# ───────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID)
def handle_owner_reply(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Reply directly to a forwarded user message to answer them.")
        return

    # Try to get original sender ID from forwarded message
    if message.reply_to_message.forward_from:
        target_id = message.reply_to_message.forward_from.id
        bot.send_message(target_id, f"Reply from owner:\\n\\n{message.text}")
        bot.reply_to(message, "Reply sent.")
    else:
        bot.reply_to(message, "Could not find original sender. Make sure you're replying to a forwarded message.")

# ───────────────────────────────────────────────
# Start polling
# ───────────────────────────────────────────────

print("Starting polling...")
try:
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except Exception as e:
    print(f"Polling crashed: {e}")
    raise
