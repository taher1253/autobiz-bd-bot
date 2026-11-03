
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

CHOOSING_SERVICE, ORDER_DETAILS = range(2)

SERVICES = [
    "🎨 ডিজিটাল ডিজাইন",
    "🌐 ওয়েবসাইট তৈরি",
    "🤖 AutoBiz Smart Solutions"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম AutoBiz BD-তে! 🇧🇩\n\n"
        "/services - আমাদের সেবা\n"
        "/order - অর্ডার করুন\n"
        "/contact - যোগাযোগ\n"
        "/myid - আপনার Telegram ID"
    )

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 AutoBiz BD-এর সেবাসমূহ\n\n"
        "১. 🎨 ডিজিটাল ডিজাইন\n"
        "ফেসবুক পোস্ট, ব্যানার, লোগো ও বিজ্ঞাপন ডিজাইন।\n\n"
        "২. 🌐 ওয়েবসাইট তৈরি\n"
        "ব্যবসার ওয়েবসাইট, ল্যান্ডিং পেজ ও Blogger সাইট।\n\n"
        "৩. 🤖 AutoBiz Smart Solutions\n"
        "Telegram বট, অটোমেশন, অটো রিপ্লাই, Excel হিসাব, PDF ও অফিস ডকুমেন্ট।\n\n"
        "অর্ডার করতে /order লিখুন।"
    )

async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[s] for s in SERVICES]
    await update.message.reply_text(
        "কোন সার্ভিসটি নিতে চান?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
    )
    return CHOOSING_SERVICE

async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    if service not in SERVICES:
        await update.message.reply_text("নিচের বাটন থেকে একটি সার্ভিস বেছে নিন।")
        return CHOOSING_SERVICE

    context.user_data["service"] = service
    await update.message.reply_text(
        "আপনার নাম, মোবাইল নম্বর এবং কাজের বিস্তারিত লিখুন।",
        reply_markup=ReplyKeyboardRemove()
    )
    return ORDER_DETAILS

async def receive_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    service = context.user_data.get("service", "অজানা")
    details = update.message.text
    admin_id = os.environ.get("ADMIN_CHAT_ID")

    if not admin_id:
        await update.message.reply_text(
            "দুঃখিত, অর্ডার নেওয়ার ব্যবস্থা এখনো সম্পূর্ণ চালু হয়নি।"
        )
        context.user_data.clear()
        return ConversationHandler.END

    message = (
        "🆕 নতুন AutoBiz BD অর্ডার\n\n"
        f"সার্ভিস: {service}\n"
        f"গ্রাহক: {user.full_name}\n"
        f"ইউজারনেম: @{user.username or 'নেই'}\n"
        f"Chat ID: {update.effective_chat.id}\n\n"
        f"বিস্তারিত:\n{details}"
    )

    try:
        await context.bot.send_message(chat_id=int(admin_id), text=message)
        await update.message.reply_text(
            "✅ আপনার অর্ডার গ্রহণ করা হয়েছে। ধন্যবাদ!"
        )
    except Exception:
        await update.message.reply_text(
            "অর্ডার পাঠাতে সমস্যা হয়েছে। পরে আবার চেষ্টা করুন।"
        )

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "অর্ডার বাতিল করা হয়েছে।",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "যোগাযোগ করতে /order দিয়ে আপনার প্রয়োজন জানান।"
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"আপনার Telegram Chat ID: {update.effective_chat.id}"
    )

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

    app = Application.builder().token(token).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("order", order_start)],
        states={
            CHOOSING_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_service)
            ],
            ORDER_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_order)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_order)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(conversation)
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("myid", myid))

    app.run_polling()

if __name__ == "__main__":
    main()
