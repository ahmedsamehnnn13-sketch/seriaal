import logging
import re
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# مكتبات معالجة الصور (أخف لـ Railway)
try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("يرجى التأكد من إضافة Pillow و pytesseract في requirements.txt")

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت يعمل! أرسل السكرين واكتب (اليوزر | السيريال) في الوصف.\n⚠️ يجب أن يكون السيريال مطابقاً للموجود بالصورة.")

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. إذا لم يرسل صورة (الشرط الأول)
    if not update.message.photo:
        await update.message.reply_text("⚠️ خطأ! يجب إرسال سكرين شوت (صورة) لإتمام التسجيل.")
        return

    user_input = update.message.caption
    if not user_input:
        await update.message.reply_text("⚠️ اكتب (اليوزر | السيريال) في وصف الصورة.")
        return

    # 2. التأكد من تنسيق الوصف (يوزر | سيريال)
    valid_format = re.match(r"^@?[\w\d_]+\s*[|/-]\s*([\w\d_/]+)$", user_input.strip())
    if not valid_format:
        await update.message.reply_text("❌ تنسيق الوصف خاطئ! استخدم:\n@Username | 123456")
        return

    extracted_serial = valid_format.group(1) # استخراج السيريال من النص

    try:
        status_msg = await update.message.reply_text("🔍 جاري التحقق من مطابقة السيريال بالصورة...")
        
        # تحميل الصورة
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        img = Image.open(io.BytesIO(photo_bytes))
        
        # 3. قراءة النص من الصورة للتأكد من السيريال
        image_text = pytesseract.image_to_string(img)
        
        if extracted_serial.lower() not in image_text.lower():
            await status_msg.edit_text(f"❌ السيريال ({extracted_serial}) غير موجود بالصورة! يرجى إرسال سكرين صحيح.")
            return

        # 4. التسجيل في القناة (تكملة الكود الأصلي)
        temp_msg = await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID
        )
        current_text = temp_msg.text
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_msg.message_id)

        pattern = r"(\d+-\s*\[)\s*(\s*\])" 
        match = re.search(pattern, current_text)
        
        if not match:
            await status_msg.edit_text("❌ القائمة ممتلئة!")
            return

        current_num = match.group(1)
        new_entry = f"{current_num} {user_input} ]"
        updated_text = current_text.replace(match.group(0), new_entry, 1)

        await context.bot.edit_message_text(
            chat_id=CHANNEL_USERNAME,
            message_id=LIST_MESSAGE_ID,
            text=updated_text
        )

        await status_msg.edit_text(f"✅ تم المطابقة بنجاح وتسجيلك في الخانة {current_num.replace('-', '').strip()}")

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, handle_registration))
    print("🚀 البوت بدأ العمل بنظام المطابقة الذكي...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
