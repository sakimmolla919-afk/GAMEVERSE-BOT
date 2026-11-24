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

# লগিং সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ইউজারদের কয়েন ও স্কোর রাখার জন্য সাধারণ মেমোরি স্টোরেজ
user_data_store = {}

# কুইজের প্রশ্নাবলী
QUIZ_QUESTIONS = [
    {
        "question": "পৃথিবীর বৃহত্তম মহাসাগর কোনটি?",
        "options": ["আটলান্টিক মহাসাগর", "ভারত মহাসাগর", "প্রশান্ত মহাসাগর", "আর্কটিক মহাসাগর"],
        "correct_id": 2,
    },
    {
        "question": "সৌরজগতের সবচেয়ে বড় গ্রহ কোনটি?",
        "options": ["পৃথিবী", "বৃহস্পতি", "মঙ্গল", "শনি"],
        "correct_id": 1,
    },
    {
        "question": "কম্পিউটারের মস্তিষ্ক কাকে বলা হয়?",
        "options": ["RAM", "Hard Disk", "CPU", "Monitor"],
        "correct_id": 2,
    },
    {
        "question": "মানবদেহে মোট কয়টি হাড় থাকে?",
        "options": ["২০৬টি", "২০৮টি", "২১০টি", "২০০টি"],
        "correct_id": 0,
    },
]

def get_user(user_id, name="Player"):
    if user_id not in user_data_store:
        user_data_store[user_id] = {"name": name, "coins": 50, "wins": 0}
    return user_data_store[user_id]

# /start কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.first_name)
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 লুডু ডাইস খেলুন", callback_data="play_ludo"),
            InlineKeyboardButton("🧠 কুইজ খেলুন", callback_data="play_quiz"),
        ],
        [
            InlineKeyboardButton("👤 প্রোফাইল", callback_data="my_profile"),
            InlineKeyboardButton("🏆 লিডারবোর্ড", callback_data="leaderboard"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 স্বাগতম {user.first_name}, GAMEVERSE-এ!\n\n"
        "নিচের বাটনগুলো থেকে আপনার পছন্দের গেম বেছে নিন অথবা /games লিখুন:",
        reply_markup=reply_markup,
    )

# /games কমান্ড
async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 লুডু ডাইস (Ludo Roll)", callback_data="play_ludo")],
        [InlineKeyboardButton("🧠 সাধারণ জ্ঞান কুইজ (Quiz)", callback_data="play_quiz")],
        [InlineKeyboardButton("🎯 ডার্ট থ্রো (Darts)", callback_data="play_darts")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🕹️ একটি গেম সিলেক্ট করুন:", reply_markup=reply_markup)

# /profile এবং /coins কমান্ড
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id, user.first_name)
    text = (
        f"👤 **খেলোয়াড়ের প্রোফাইল**\n"
        f"নাম: {data['name']}\n"
        f"💰 কয়েন: {data['coins']}\n"
        f"🏅 মোট জয়: {data['wins']}"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")

# /leaderboard কমান্ড
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_data_store:
        msg = "এখনও কোনো স্কোর তৈরি হয়নি!"
    else:
        sorted_users = sorted(
            user_data_store.values(), key=lambda x: x["coins"], reverse=True
        )[:5]
        msg = "🏆 **টপ প্লেয়ারস (Leaderboard)** 🏆\n\n"
        for idx, u in enumerate(sorted_users, 1):
            msg += f"{idx}. {u['name']} — 💰 {u['coins']} কয়েন\n"

    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown")

# /help কমান্ড
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 **GAMEVERSE কমান্ড তালিকা:**\n"
        "/start - বট চালু করুন\n"
        "/games - গেম মেনু দেখুন\n"
        "/profile - আপনার কয়েন ও স্কোর দেখুন\n"
        "/leaderboard - সেরা খেলোয়াড়দের তালিকা"
    )

# বাটন হ্যান্ডলার
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
            res = f"🎉 ছক্কা পড়েছে ({value})! আপনি ২০ কয়েন জিতেছেন!"
        else:
            data["coins"] += 5
            res = f"🎲 আপনার পয়েন্ট: {value}। অংশগ্রহণের জন্য ৫ কয়েন পেয়েছেন।"
        await query.message.reply_text(res)

    elif query.data == "play_darts":
        dart_msg = await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎯")
        if dart_msg.dice.value == 6:
            data["coins"] += 30
            data["wins"] += 1
            await query.message.reply_text("🎯 বুলস-আই! দারুণ নিশানা! আপনি ৩০ কয়েন জিতেছেন!")
        else:
            await query.message.reply_text("🎯 লক্ষ্যভ্রষ্ট হয়েছে! আবার চেষ্টা করুন।")

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
        # পোল আইডি সেভ রাখা যাতে সঠিক উত্তর দিলে কয়েন দেওয়া যায়
        context.bot_data[message.poll.id] = q["correct_id"]

    elif query.data == "my_profile":
        await profile(update, context)

    elif query.data == "leaderboard":
        await leaderboard(update, context)

# কুইজের উত্তর চেক করা
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
                text=f"✅ সঠিক উত্তর {user.first_name}! আপনি ১৫ কয়েন জিতেছেন। মোট কয়েন: {data['coins']}"
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
