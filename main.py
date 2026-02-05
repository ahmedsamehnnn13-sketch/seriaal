import logging
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت يعمل! أرسل السكرين واكتب البيانات في الوصف.")

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    user_input = update.message.caption
    if not user_input:
        await update.message.reply_text("⚠️ اكتب (اليوزر | السيريال) في وصف الصورة.")
        return

    try:
        # جلب نص القائمة من القناة
        temp_msg = await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID
        )
        current_text = temp_msg.text
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_msg.message_id)

        # البحث عن خانة فارغة [ ]
        pattern = r"(\d+-\s*\[)\s*(\s*\])" 
        match = re.search(pattern, current_text)
        
        if not match:
            await update.message.reply_text("❌ لم يتم العثور على خانات فارغة.")
            return

        current_num = match.group(1)
        new_entry = f"{current_num} {user_input} ]"
        updated_text = current_text.replace(match.group(0), new_entry, 1)

        # تعديل الرسالة
        await context.bot.edit_message_text(
            chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID,
            text=updated_text
        )

        await update.message.reply_text(f"✅ تم تسجيلك في الخانة {current_num.replace('-', '').strip()}")

    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

def main():
    # بناء التطبيق
    application = ApplicationBuilder().token(TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))

    # التشغيل
    print("🚀 البوت بدأ العمل الآن...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
