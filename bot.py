import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PollAnswerHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

user_data_store = {}

QUIZ_QUESTIONS = [
    {
        "question": "Which is the largest ocean on Earth?",
        "options": ["Atlantic Ocean", "Indian Ocean", "Pacific Ocean", "Arctic Ocean"],
        "correct_id": 2,
    },
    {
        "question": "What is the largest planet in our solar system?",
        "options": ["Earth", "Jupiter", "Mars", "Saturn"],
        "correct_id": 1,
    },
    {
        "question": "What is known as the brain of the computer?",
        "options": ["RAM", "Hard Disk", "CPU", "Monitor"],
        "correct_id": 2,
    },
]

def get_user(user_id, name="Player"):
    if user_id not in user_data_store:
        user_data_store[user_id] = {"name": name, "coins": 50, "wins": 0}
    return user_data_store[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.first_name)
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 Play Ludo Dice", callback_data="play_ludo"),
            InlineKeyboardButton("🧠 Play Quiz", callback_data="play_quiz"),
        ],
        [
            InlineKeyboardButton("👤 Profile", callback_data="my_profile"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 Welcome {user.first_name} to GAMEVERSE!\n\n"
        "Choose an option below or type /games:",
        reply_markup=reply_markup,
    )

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Ludo Roll", callback_data="play_ludo")],
        [InlineKeyboardButton("🧠 General Knowledge Quiz", callback_data="play_quiz")],
        [InlineKeyboardButton("🎯 Dart Throw", callback_data="play_darts")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🕹️ Select a game:", reply_markup=reply_markup)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id, user.first_name)
    text = (
        f"👤 **Player Profile**\n"
        f"Name: {data['name']}\n"
        f"Coins: 💰 {data['coins']}\n"
        f"Total Wins: 🏅 {data['wins']}"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_data_store:
        msg = "No scores recorded yet."
    else:
        sorted_users = sorted(
            user_data_store.values(), key=lambda x: x["coins"], reverse=True
        )[:5]
        msg = "🏆 **Top Players** 🏆\n\n"
        for idx, u in enumerate(sorted_users, 1):
            msg += f"{idx}. {u['name']} — 💰 {u['coins']} coins\n"

    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 **Commands List:**\n"
        "/start - Start the bot\n"
        "/games - View game menu\n"
        "/profile - Check your profile\n"
        "/leaderboard - View top scores"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = get_user(user.id, user.first_name)

    if query.data == "play_ludo":
        dice_msg = await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎲")
        value = dice_msg.dice.value
        if value == 6:
            data["coins"] += 20
            data["wins"] += 1
            res = f"🎉 Lucky 6! You won 20 coins!"
        else:
            data["coins"] += 5
            res = f"🎲 You rolled a {value}. Here are 5 participation coins."
        await query.message.reply_text(res)

    elif query.data == "play_darts":
        dart_msg = await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎯")
        if dart_msg.dice.value == 6:
            data["coins"] += 30
            data["wins"] += 1
            await query.message.reply_text("🎯 Bullseye! You won 30 coins!")
        else:
            await query.message.reply_text("🎯 Missed the bullseye. Try again!")

    elif query.data == "play_quiz":
        q = random.choice(QUIZ_QUESTIONS)
        message = await context.bot.send_poll(
            chat_id=query.message.chat_id,
            question=q["question"],
            options=q["options"],
            type="quiz",
            correct_option_id=q["correct_id"],
            is_anonymous=False,
        )
        context.bot_data[message.poll.id] = q["correct_id"]

    elif query.data == "my_profile":
        await profile(update, context)

    elif query.data == "leaderboard":
        await leaderboard(update, context)

async def receive_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    poll_id = answer.poll_id
    user = answer.user
    
    if poll_id in context.bot_data:
        correct_id = context.bot_data[poll_id]
        if answer.option_ids and answer.option_ids[0] == correct_id:
            data = get_user(user.id, user.first_name)
            data["coins"] += 15
            data["wins"] += 1
            await context.bot.send_message(
                chat_id=user.id,
                text=f"✅ Correct answer, {user.first_name}! You won 15 coins. Total: {data['coins']}"
            )

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("games", games))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("coins", profile))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PollAnswerHandler(receive_quiz_answer))

    print("GAMEVERSE BOT is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
