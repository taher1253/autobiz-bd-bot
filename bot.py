
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম AutoBiz BD-তে!\n\n"
        "/services - আমাদের সেবা\n"
        "/order - অর্ডার\n"
        "/contact - যোগাযোগ"
    )

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "AutoBiz BD-এর সেবাসমূহ শীঘ্রই যুক্ত হবে।"
    )

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "অর্ডার করতে আপনার বিস্তারিত লিখুন।"
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "যোগাযোগ: Admin"
    )

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("order", order))
    app.add_handler(CommandHandler("contact", contact))

    app.run_polling()

if __name__ == "__main__":
    main()
