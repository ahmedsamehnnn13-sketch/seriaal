import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208
ADMIN_IDS = [8147516847, 6661924074] # معرفات الأدمنز

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ البوت يعمل بنجاح!\n\n"
        "📝 **طريقة التسجيل:**\n"
        "1️⃣ أرسل سكرين شوت (صورة) واضحة.\n"
        "2️⃣ اكتب في وصف الصورة: @اليوزر | السيريال\n\n"
        "⚠️ سيتم مراجعة طلبك من قبل الإدارة قبل النشر."
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ خطأ! يجب إرسال صورة (سكرين شوت).")
        return

    user_input = update.message.caption
    if not user_input:
        await update.message.reply_text("⚠️ يجب كتابة (اليوزر | السيريال) في وصف الصورة.")
        return

    # التأكد من التنسيق
    valid_format = re.match(r"^@[\w\d_]+\s*[|/-]\s*[\w\d_/]+$", user_input.strip())
    if not valid_format:
        await update.message.reply_text("❌ تنسيق الوصف غير صحيح! استخدم: @Username | 123456")
        return

    # إرسال الطلب للأدمن للموافقة
    photo_id = update.message.photo[-1].file_id
    for admin_id in ADMIN_IDS:
        try:
            keyboard = [
                [
                    InlineKeyboardButton("✅ قبول", callback_data=f"accept_{update.message.chat_id}"),
                    InlineKeyboardButton("❌ رفض", callback_data=f"reject_{update.message.chat_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # تخزين البيانات مؤقتاً عند البوت لإتمام العملية لاحقاً
            context.bot_data[f"data_{update.message.chat_id}"] = user_input
            
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=f"🔔 طلب تسجيل جديد:\nالبيانات: {user_input}\nمن: @{update.effective_user.username}",
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Could not send to admin {admin_id}: {e}")

    await update.message.reply_text("⏳ تم إرسال طلبك للإدارة، سيتم النشر فور الموافقة.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_chat_id = query.data.split("_")
    user_data = context.bot_data.get(f"data_{user_chat_id}")

    if action == "accept":
        try:
            # جلب نص القائمة من القناة
            temp_msg = await context.bot.forward_message(chat_id=query.message.chat_id, from_chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID)
            current_text = temp_msg.text
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=temp_msg.message_id)

            pattern = r"(\d+-\s*\[)\s*(\s*\])" 
            match = re.search(pattern, current_text)
            
            if not match:
                await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ القائمة ممتلئة!")
                return

            current_num_prefix = match.group(1)
            new_entry = f"{current_num_prefix} {user_data} ]"
            updated_text = current_text.replace(match.group(0), new_entry, 1)

            await context.bot.edit_message_text(chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID, text=updated_text)
            await context.bot.send_message(chat_id=user_chat_id, text="✅ مبروك! وافقت الإدارة على طلبك وتم تسجيلك في القناة.")
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ تم القبول والنشر بنجاح.")
            
        except Exception as e:
            await query.edit_message_caption(caption=f"❌ خطأ أثناء النشر: {e}")

    elif action == "reject":
        await context.bot.send_message(chat_id=user_chat_id, text="❌ نعتذر، تم رفض طلب تسجيلك من قبل الإدارة. تأكد من صحة السكرين والبيانات.")
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ تم رفض الطلب.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), 
        lambda u, c: u.message.reply_text("⚠️ أرسل سكرين شوت واكتب البيانات في الوصف.")))

    print("🚀 البوت يعمل بنظام الموافقة الإدارية...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
