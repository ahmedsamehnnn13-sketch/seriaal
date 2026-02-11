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
GROUP_ID = -1002588398038 # الكروب الذي ستتم فيه الموافقة والرفض
ADMIN_IDS = [8147516847, 6661924074, 2041293201] # قائمة الإدارة والمساعدين
OWNER_ID = 8147516847 # معرفك الشخصي للتحكم في التعديلات

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **بوت الفحص الذكي يعمل بنجاح!**\n\n"
        "🔍 يتم فحص الأرشيف تلقائياً.\n"
        "👥 طلبات الموافقة تظهر في الكروب المخصص للإدارة."
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # السماح بالصور سواء من الخاص أو الكروب (طالما البرايفسي مقفول)
    if not update.message.photo: return
    user_input = update.message.caption
    if not user_input:
        if update.message.chat.type == "private":
            await update.message.reply_text("⚠️ اكتب (اليوزر | السيريال) في وصف الصورة.")
        return

    match_input = re.match(r"^(@[\w\d_]+)\s*[|/-]\s*([\w\d_/]+)$", user_input.strip())
    if not match_input:
        if update.message.chat.type == "private":
            await update.message.reply_text("❌ تنسيق خاطئ! استخدم: @Username | Serial")
        return

    new_user = match_input.group(1)
    new_serial = match_input.group(2)

    status_msg = await update.message.reply_text("🔍 جاري فحص الأرشيف بالكامل (1-208)...")

    found_info = "✅ بيانات جديدة (إضافة لاعب)."
    is_update = False
    
    # الفحص التاريخي
    for msg_id in range(1, LIST_MESSAGE_ID + 1):
        try:
            old_msg = await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
            content = (old_msg.text or old_msg.caption or "").lower()
            
            if new_serial.lower() in content:
                found_info = f"⚠️ السيريال موجود مسبقاً في الرسالة {msg_id} (عملية تبديل يوزر)"
                is_update = True
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
                break
            elif new_user.lower() in content:
                found_info = f"⚠️ اليوزر موجود مسبقاً في الرسالة {msg_id} (عملية تعديل سيريال)"
                is_update = True
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
                break
            
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg.message_id)
            await asyncio.sleep(0.05)
        except:
            continue

    await status_msg.delete()

    # إرسال طلب المعالجة للكروب المخصص فقط
    try:
        keyboard = [[
            InlineKeyboardButton("✅ قبول التنفيذ", callback_data=f"exec_{update.message.chat_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_{update.message.chat_id}")
        ]]
        # حفظ البيانات في bot_data مؤقتاً
        context.bot_data[f"u_{update.message.chat_id}"] = new_user
        context.bot_data[f"s_{update.message.chat_id}"] = new_serial
        context.bot_data[f"is_update_{update.message.chat_id}"] = is_update
        
        await context.bot.send_photo(
            chat_id=GROUP_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"📝 **تقرير فحص جديد:**\n{found_info}\n\n👤 اليوزر: {new_user}\n🔢 السيريال: {new_serial}\n💬 مرسل من: {update.message.from_user.mention_html()}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        if update.message.chat.type == "private":
            await update.message.reply_text("⏳ تم إرسال طلبك للكروب الخاص بالإدارة.")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ في إرسال الطلب للكروب: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[0]
    user_chat_id = data[1]
    
    new_user = context.bot_data.get(f"u_{user_chat_id}")
    new_serial = context.bot_data.get(f"s_{user_chat_id}")
    is_update = context.bot_data.get(f"is_update_{user_chat_id}")

    if action == "exec":
        if not is_update:
            await process_list(query, context, user_chat_id, new_user, new_serial)
        else:
            if query.from_user.id == OWNER_ID:
                keyboard = [
                    [InlineKeyboardButton("🔄 تعديل يوزر", callback_data=f"edituser_{user_chat_id}")],
                    [InlineKeyboardButton("🔄 تعديل تسلسلي", callback_data=f"editserial_{user_chat_id}")]
                ]
                await query.edit_message_caption(caption=f"{query.message.caption}\n\n⚠️ تم العثور على تطابق! اختر نوع العملية المطلوبة:", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.answer("⚠️ هذا الخيار للمالك فقط لتحديد نوع التعديل!", show_alert=True)

    elif action == "edituser" or action == "editserial":
        await process_list(query, context, user_chat_id, new_user, new_serial, edit_type=action)

    elif action == "reject":
        await context.bot.send_message(chat_id=user_chat_id, text="❌ تم رفض طلبك من قبل الإدارة.")
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ تم الرفض بواسطة: {query.from_user.first_name}")

async def process_list(query, context, user_chat_id, new_user, new_serial, edit_type=None):
    try:
        # جلب نص القائمة الحالية (تحسين الطريقة لتجنب الخطأ)
        temp_msg = await context.bot.copy_message(chat_id=query.message.chat_id, from_chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID)
        # الانتظار قليلاً للتأكد من المعالجة
        await asyncio.sleep(0.1)
        
        # قراءة النص من الرسالة المنسوخة
        # ملاحظة: في بعض الأحيان قد لا يظهر النص فوراً، نستخدم محاولة قراءة النص
        msg_obj = await context.bot.send_message(chat_id=query.message.chat_id, text="🔄 جاري سحب القائمة...", visible=False)
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=msg_obj.message_id)
        
        content = query.message.reply_to_message.text if query.message.reply_to_message else ""
        # الطريقة الأكثر ضماناً: الحصول على الرسالة كـ Object
        channel_msg = await context.bot.forward_message(chat_id=query.message.chat_id, from_chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID)
        content = channel_msg.text
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=channel_msg.message_id)
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=temp_msg.message_id)

        lines = content.split('\n')
        updated = False
        
        # محاولة البحث عن سطر للتحديث
        for i, line in enumerate(lines):
            should_update_this_line = False
            if edit_type == "edituser" and new_serial.lower() in line.lower():
                should_update_this_line = True
            elif edit_type == "editserial" and new_user.lower() in line.lower():
                should_update_this_line = True
            
            if should_update_this_line:
                prefix_match = re.match(r"(\d+-\s*\[)", line)
                if prefix_match:
                    lines[i] = f"{prefix_match.group(1)} {new_user} | {new_serial} ]"
                    updated = True
                    break

        # إذا لم يتم التحديث (إضافة جديدة)
        if not updated:
            for i, line in enumerate(lines):
                if "[" in line and "]" in line and (len(line.strip()) < 15 or "|" not in line):
                    prefix_match = re.match(r"(\d+-\s*\[)", line)
                    if prefix_match:
                        lines[i] = f"{prefix_match.group(1)} {new_user} | {new_serial} ]"
                        updated = True
                        break
        
        if updated:
            final_text = "\n".join(lines)
            await context.bot.edit_message_text(chat_id=CHANNEL_USERNAME, message_id=LIST_MESSAGE_ID, text=final_text)
            await context.bot.send_message(chat_id=user_chat_id, text="✅ تمت الموافقة وتحديث بياناتك في القناة.")
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ تم التنفيذ بنجاح بواسطة: {query.from_user.first_name}")
        else:
            await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ فشل: القائمة ممتلئة تماماً.")
            
    except Exception as e:
        await query.edit_message_caption(caption=f"❌ حدث خطأ بالبرمجة أثناء التعديل: {e}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_registration))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling()

if __name__ == '__main__':
    main()
