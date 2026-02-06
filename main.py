import logging
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8545045230:AAFxaE3jbwWVuiAbMLf-7Pd31nrjXd_4-zk'
CHANNEL_USERNAME = '@Serianumber99' 
LIST_MESSAGE_ID = 208 # الرسالة التي تحتوي على القائمة الرئيسية
ADMIN_IDS = [8147516847, 6661924074, 2041293201] # قائمة الإدارة والمساعدين

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **بوت الفحص الذكي جاهز!**\n\n"
        "🔍 سأقوم بفحص الأرشيف من الرسالة 1 إلى 208.\n"
        "✅ إذا كان اللاعب مسجلاً مسبقاً، سأقترح التعديل.\n"
        "🆕 إذا كان لاعباً جديداً، سأقترح الإضافة."
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return
    user_input = update.message.caption
    if not user_input:
        await update.message.reply_text("⚠️ اكتب (اليوزر | السيريال) في وصف الصورة.")
        return

    # استخراج اليوزر والسيريال بدقة
    match_input = re.match(r"^(@[\w\d_]+)\s*[|/-]\s*([\w\d_/]+)$", user_input.strip())
    if not match_input:
        await update.message.reply_text("❌ تنسيق خاطئ! استخدم: @Username | Serial")
        return

    new_user = match_input.group(1)
    new_serial = match_input.group(2)

    status_msg = await update.message.reply_text("🔍 جاري فحص الأرشيف بالكامل، انتظر لحظة...")

    found_info = "✅ بيانات جديدة (إضافة لاعب)."
    
    # الفحص التاريخي (من 1 لـ 208)
    for msg_id in range(1, LIST_MESSAGE_ID + 1):
        try:
            # استخدام forward للقراءة فقط
            old_msg = await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
            content = (old_msg.text or old_msg.caption or "").lower()
            
            if new_serial.lower() in content:
                found_info = f"⚠️ السيريال موجود مسبقاً في الرسالة {msg_id} (عملية تبديل يوزر)"
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
                break
            elif new_user.lower() in content:
                found_info = f"⚠️ اليوزر موجود مسبقاً في الرسالة {msg_id} (عملية تعديل سيريال)"
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
                break
            
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
            await asyncio.sleep(0.05)
        except:
            continue

    await status_msg.delete()

    # إرسال طلب المعالجة للمسؤولين
    for admin_id in ADMIN_IDS:
        try:
            keyboard = [[
                InlineKeyboardButton("✅ قبول التنفيذ", callback_data=f"exec_{update.message.chat_id}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_{update.message.chat_id}")
            ]]
            context.bot_data[f"u_{update.message.chat_id}"] = new_user
            context.bot_data[f"s_{update.message.chat_id}"] = new_serial
            
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=update.message.photo[-1].file_id,
                caption=f"📝 **تقرير الفحص الذكي:**\n{found_info}\n\n👤 اليوزر: {new_user}\n🔢 السيريال: {new_serial}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except: continue

    await update.message.reply_text("⏳ تم الفحص الشامل وإرسال التقرير للمسؤولين.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_chat_id = query.data.split("_")
    
    if action == "exec":
        new_user = context.bot_data.get(f"u_{user_chat_id}")
        new_serial = context.bot_data.get(f"s_{user_chat_id}")
        
        try:
            temp_msg = await context.bot.forward_message(chat_id=query.message.chat_id, from_chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID)
            lines = temp_msg.text.split('\n')
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=temp_msg.message_id)

            updated = False
            # المرحلة الأولى: البحث عن تطابق لتحديث السطر (تبديل يوزر أو تعديل سيريال)
            for i, line in enumerate(lines):
                if new_serial.lower() in line.lower() or new_user.lower() in line.lower():
                    prefix = re.match(r"(\d+-\s*\[)", line)
                    if prefix:
                        lines[i] = f"{prefix.group(1)} {new_user} | {new_serial} ]"
                        updated = True
                        break
            
            # المرحلة الثانية: إذا لم يوجد تطابق، نبحث عن أول خانة فارغة
            if not updated:
                for i, line in enumerate(lines):
                    if "[ ]" in line or "[  ]" in line:
                        prefix = re.match(r"(\d+-\s*\[)", line)
                        if prefix:
                            lines[i] = f"{prefix.group(1)} {new_user} | {new_serial} ]"
                            updated = True
                            break
            
            if updated:
                await context.bot.edit_message_text(chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID, text="\n".join(lines))
                await context.bot.send_message(chat_id=user_chat_id, text="✅ تمت الموافقة وتحديث بياناتك في القناة.")
                await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ تم التحديث بنجاح.")
            else:
                await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ القائمة ممتلئة!")
        except Exception as e:
            await query.edit_message_caption(caption=f"❌ خطأ: {e}")

    elif action == "reject":
        await context.bot.send_message(chat_id=user_chat_id, text="❌ تم رفض طلبك من قبل الإدارة.")
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ مرفوض.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling()

if __name__ == '__main__':
    main()
