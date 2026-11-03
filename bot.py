
import os
import secrets
import httpx

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

STATUSES = {
    "pending": "🟡 Pending (অপেক্ষমাণ)",
    "processing": "🔵 Processing (কাজ চলছে)",
    "completed": "🟢 Completed (সম্পন্ন)"
}


def is_admin(update):
    admin_id = os.environ.get("ADMIN_CHAT_ID")
    return bool(
        admin_id and update.effective_chat
        and str(update.effective_chat.id) == admin_id
    )


def db_url():
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not url:
        raise RuntimeError("SUPABASE_URL missing")
    return url + "/rest/v1/orders"


def db_headers():
    key = os.environ.get("SUPABASE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_KEY missing")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }


async def start(update, context):
    await update.message.reply_text(
        "স্বাগতম AutoBiz BD-তে! 🇧🇩\n\n"
        "/services - আমাদের সেবা\n"
        "/order - অর্ডার করুন\n"
        "/orders - অর্ডার তালিকা (Admin)\n"
        "/contact - যোগাযোগ\n"
        "/myid - Telegram ID"
    )


async def services(update, context):
    await update.message.reply_text(
        "🌟 AutoBiz BD-এর সেবাসমূহ\n\n"
        "১. 🎨 ডিজিটাল ডিজাইন\n"
        "ফেসবুক পোস্ট, ব্যানার, লোগো ও বিজ্ঞাপন ডিজাইন।\n\n"
        "২. 🌐 ওয়েবসাইট তৈরি\n"
        "ব্যবসার ওয়েবসাইট, ল্যান্ডিং পেজ ও Blogger সাইট।\n\n"
        "৩. 🤖 AutoBiz Smart Solutions\n"
        "Telegram বট, অটোমেশন, Excel, PDF ও অফিস ডকুমেন্ট।\n\n"
        "অর্ডার করতে /order লিখুন।"
    )


async def order_start(update, context):
    keyboard = [[s] for s in SERVICES]
    await update.message.reply_text(
        "কোন সার্ভিসটি নিতে চান?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        )
    )
    return CHOOSING_SERVICE


async def choose_service(update, context):
    service = update.message.text

    if service not in SERVICES:
        await update.message.reply_text("নিচের বাটন থেকে সার্ভিস বেছে নিন।")
        return CHOOSING_SERVICE

    context.user_data["service"] = service

    await update.message.reply_text(
        "আপনার নাম, মোবাইল নম্বর এবং কাজের বিস্তারিত লিখুন।",
        reply_markup=ReplyKeyboardRemove()
    )
    return ORDER_DETAILS


async def receive_order(update, context):
    user = update.effective_user
    admin_id = os.environ.get("ADMIN_CHAT_ID")

    if not admin_id:
        await update.message.reply_text("অর্ডার সিস্টেমে সমস্যা হয়েছে।")
        return ConversationHandler.END

    order_id = "ABD-" + secrets.token_hex(3).upper()

    order = {
        "id": order_id,
        "service": context.user_data.get("service", "অজানা"),
        "customer_name": user.full_name,
        "username": user.username or "নেই",
        "chat_id": update.effective_chat.id,
        "details": update.message.text,
        "status": "pending"
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                db_url(),
                headers={**db_headers(), "Prefer": "return=minimal"},
                json=order
            )
            response.raise_for_status()

    except Exception:
        await update.message.reply_text(
            "অর্ডার ডেটাবেজে সংরক্ষণ করা যায়নি। পরে আবার চেষ্টা করুন।"
        )
        context.user_data.clear()
        return ConversationHandler.END

    admin_message = (
        "🆕 নতুন AutoBiz BD অর্ডার\n\n"
        f"Order ID: {order_id}\n"
        f"সার্ভিস: {order['service']}\n"
        f"গ্রাহক: {user.full_name}\n"
        f"ইউজারনেম: @{user.username or 'নেই'}\n"
        f"Chat ID: {order['chat_id']}\n\n"
        f"বিস্তারিত:\n{order['details']}\n\n"
        "স্ট্যাটাস: Pending"
    )

    try:
        await context.bot.send_message(
            chat_id=int(admin_id), text=admin_message
        )
    except Exception:
        pass

    await update.message.reply_text(
        "✅ আপনার অর্ডার গ্রহণ করা হয়েছে!\n\n"
        f"আপনার Order ID: {order_id}\n"
        "বর্তমান অবস্থা: Pending\n\n"
        "আপনার অর্ডারের অগ্রগতি জানানো হবে।"
    )

    context.user_data.clear()
    return ConversationHandler.END


async def orders_command(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ শুধু অ্যাডমিনের জন্য।")
        return

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                db_url(),
                headers=db_headers(),
                params={
                    "select": "id,service,customer_name,status,created_at",
                    "order": "created_at.desc",
                    "limit": "15"
                }
            )
            response.raise_for_status()
            orders = response.json()

    except Exception:
        await update.message.reply_text("ডেটাবেজ থেকে অর্ডার আনা যায়নি।")
        return

    if not orders:
        await update.message.reply_text("এখনো কোনো অর্ডার নেই।")
        return

    lines = ["📋 AutoBiz BD অর্ডার তালিকা\n"]

    for order in orders:
        lines.append(
            f"ID: {order['id']}\n"
            f"সার্ভিস: {order['service']}\n"
            f"গ্রাহক: {order['customer_name']}\n"
            f"অবস্থা: {STATUSES[order['status']]}\n"
        )

    await update.message.reply_text("\n".join(lines))


async def status_command(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ শুধু অ্যাডমিনের জন্য।")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "/status ORDER_ID pending\n"
            "/status ORDER_ID processing\n"
            "/status ORDER_ID completed"
        )
        return

    order_id = context.args[0].upper()
    new_status = context.args[1].lower()

    if new_status not in STATUSES:
        await update.message.reply_text(
            "pending, processing অথবা completed লিখুন।"
        )
        return

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                db_url(),
                headers=db_headers(),
                params={
                    "select": "id,service,chat_id",
                    "id": f"eq.{order_id}",
                    "limit": "1"
                }
            )
            response.raise_for_status()
            rows = response.json()

            if not rows:
                await update.message.reply_text("Order ID পাওয়া যায়নি।")
                return

            order = rows[0]

            response = await client.patch(
                db_url(),
                headers={**db_headers(), "Prefer": "return=minimal"},
                params={"id": f"eq.{order_id}"},
                json={"status": new_status}
            )
            response.raise_for_status()

    except Exception:
        await update.message.reply_text("ডেটাবেজ আপডেট করা যায়নি।")
        return

    try:
        await context.bot.send_message(
            chat_id=order["chat_id"],
            text=(
                "📢 AutoBiz BD অর্ডার আপডেট\n\n"
                f"Order ID: {order_id}\n"
                f"সার্ভিস: {order['service']}\n"
                f"নতুন অবস্থা: {STATUSES[new_status]}"
            )
        )
        await update.message.reply_text(
            f"✅ {order_id}-এর স্ট্যাটাস আপডেট হয়েছে।"
        )

    except Exception:
        await update.message.reply_text(
            "ডেটাবেজে স্ট্যাটাস আপডেট হয়েছে, "
            "কিন্তু গ্রাহককে মেসেজ পাঠানো যায়নি।"
        )


async def cancel_order(update, context):
    context.user_data.clear()
    await update.message.reply_text(
        "অর্ডার বাতিল করা হয়েছে।",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def contact(update, context):
    await update.message.reply_text(
        "যোগাযোগ করতে /order দিয়ে আপনার প্রয়োজন জানান।"
    )


async def myid(update, context):
    await update.message.reply_text(
        f"আপনার Telegram Chat ID: {update.effective_chat.id}"
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")

    app = Application.builder().token(token).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("order", order_start)],
        states={
            CHOOSING_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_service)
            ],
            ORDER_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_order)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_order)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(conversation)
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("status", status_command))

    app.run_polling()


if __name__ == "__main__":
    main()
