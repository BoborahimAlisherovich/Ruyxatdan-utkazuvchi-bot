from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart,Command
from aiogram import F
from aiogram.types import Message
from data import config
import asyncio
import logging
import sys
from menucommands.set_bot_commands  import set_default_commands
from baza.sqlite import Database
from filterss.admin import IsBotAdminFilter
from filterss.check_sub_channel import IsCheckSubChannels
from keyboard_buttons import admin_keyboard
from aiogram.fsm.context import FSMContext
from middlewares.throttling import ThrottlingMiddleware #new
from states.reklama import Adverts
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states.states import Form
import time 
import re
ADMINS = config.ADMINS
TOKEN = config.BOT_TOKEN
CHANNELS = config.CHANNELS

dp = Dispatcher()


@dp.message(CommandStart())
async def start_command(message:Message):
    full_name = message.from_user.full_name
    telegram_id = message.from_user.id
    try:
        db.add_user(full_name=full_name,telegram_id=telegram_id)
        await message.answer(text="Assalomu alaykum, bizning Navoi shahar kasb hunar maktabining ruyxatdan utkazuvchi botiga hush kelibsiz\nbot nma qiladi /help\nRuyxatdan utish /regist\ndasturchi haqida va kolij haqida mlunot /abaut")
    except:
        await message.answer(text="Assalomu alaykum, bizning Navoi shahar kasb hunar maktabining ruyxatdan utkazuvchi botiga hush kelibsiz\nbot nma qiladi /help\nRuyxatdan utish /regist\ndasturchi haqida va kolij haqida mlunot /abaut")


@dp.message(IsCheckSubChannels())
async def kanalga_obuna(message:Message):
    text = ""
    inline_channel = InlineKeyboardBuilder()
    for index,channel in enumerate(CHANNELS):
        ChatInviteLink = await bot.create_chat_invite_link(channel)
        inline_channel.add(InlineKeyboardButton(text=f"{index+1}-kanal",url=ChatInviteLink.invite_link))
    inline_channel.adjust(1,repeat=True)
    button = inline_channel.as_markup()
    await message.answer(f"{text} kanallarga azo bo'ling",reply_markup=button)


@dp.message(Command("help"))
async def is_admin(message:Message):
    await message.answer(text="Bu bot orqali siz Navoi shahar kasb hunara maktabiga ollayn tarzda ruyxatdan utishingiz mumkin va siz kursatmalarni tug'ri bersangiz")


@dp.message(Command("abaut"))
async def is_admin(message:Message):
    await message.answer(text="Dasturchi Rustamqulov Boborahim @Alisherov1ch_002 bot haqida savollar bo'lsa utib qoldirishilar mumkin\nNavoi shahar kasb hunar maktabi 2-yillik uquv tizimi bulib siz 9- sinfni bitirganlik haqidagi shahodotnoma bilan qabul qilinasiz")

#Admin panel uchun
@dp.message(Command("admin"))
async def is_admin(message:Message):
    await message.answer(text="Admin menu",reply_markup=admin_keyboard.admin_button)


@dp.message(F.text=="Foydalanuvchilar soni")
async def users_count(message:Message):
    counts = db.count_users()
    text = f"Botimizda {counts[0]} ta foydalanuvchi bor"
    await message.answer(text=text)

@dp.message(F.text=="Reklama yuborish")
async def advert_dp(message:Message,state:FSMContext):
    await state.set_state(Adverts.adverts)
    await message.answer(text="Reklama yuborishingiz mumkin !")

@dp.message(Adverts.adverts)
async def send_advert(message:Message,state:FSMContext):
    
    message_id = message.message_id
    from_chat_id = message.from_user.id
    users = await db.all_users_id()
    count = 0
    for user in users:
        try:
            await bot.copy_message(chat_id=user[0],from_chat_id=from_chat_id,message_id=message_id)
            count += 1
        except:
            pass
        time.sleep(0.5)
    
    await message.answer(f"Reklama {count}ta foydalanuvchiga yuborildi")
    await state.clear()


@dp.message(Command("regist"))
async def command_start_handler(message: Message,state:FSMContext) -> None:
    await state.set_state(Form.first_name)
    full_name = message.from_user.full_name
    text = f"Assalomu alaykum,{full_name} Ro'yhatdan o'tish uchun ismingizni kiriting!"
    await message.reply(text=text)

@dp.message(Form.first_name,F.text)
async def get_first_name(message:Message,state:FSMContext): 
     first_name = message.text
     await state.update_data(first_name=first_name)

     await state.set_state(Form.last_name)
     text = f"Familyangizni  kiriting!"
     await message.reply(text=text)

@dp.message(Form.first_name)
async def not_get_first_name(message:Message,state:FSMContext):
    text = f"Iltimos ismingizni kiriting!"
    await message.reply(text=text)  

        
@dp.message(Form.last_name,F.text)
async def get_last_name(message:Message,state:FSMContext):
     
     last_name = message.text
     await state.update_data(last_name=last_name)

     await state.set_state(Form.email)
     text = f"Emailingizni kiriting!"
     await message.reply(text=text) 

@dp.message(Form.last_name)
async def not_get_last_name(message:Message,state:FSMContext):
    text = f"Iltimos familiyangizni yuboring!"
    await message.reply(text=text)    

@dp.message(Form.email)
async def get_email(message:Message,state:FSMContext):
    pattern = "[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+"
    if re.match(pattern,message.text):

        email = message.text
        await state.update_data(email=email)

        await state.set_state(Form.photo)
        text = f"Rasmingizni yuboring!"
        await message.reply(text=text)
    
    else:
        await message.reply(text="Emailingizni noto'g'ri kiritdingiz")

@dp.message(Form.photo,F.photo)
async def get_photo(message:Message,state:FSMContext):

    photo = message.photo[-1].file_id 
    await state.update_data(photo=photo)
    await state.set_state(Form.phone_number)
    text = f"Telefon nomeringizni kiriting!"
    await message.reply(text=text)

@dp.message(Form.photo)
async def not_get_photo(message:Message,state:FSMContext):
    text = f"Iltimos rasm yuboring!"
    await message.reply(text=text)




@dp.message(Form.phone_number)
async def get_phone_number(message:Message,state:FSMContext):
    pattern = "^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$"
    if re.match(pattern,message.text):

        phone_number = message.text
        await state.update_data(phone_number=phone_number)

        await state.set_state(Form.address)
        text = f"Addressingizni kiriting!"
        await message.reply(text=text)
    
    else:
        await message.reply(text="telefon nomeringizni noto'g'ri kiritdingiz")     

      


@dp.message(Form.address)
async def get_address(message:Message,state:FSMContext):
    address = message.text
    await state.update_data(address=address)

    data = await state.get_data()    
    my_photo = data.get("photo")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    phone_number = data.get("phone_number")
    address = data.get("address")
    email = data.get("email")
    photo = data.get("photo")

    text = f"<b>Yangi uquvchi </b>\nIsmi: {first_name}\nFamilya: {last_name}\nTel: {phone_number}\nManzil: {address}\nGmail: {email}"
    
    
    for admin in ADMINS:
        await bot.send_photo(admin,photo=my_photo,caption=text)
        # print(first_name,last_name,phone_number,address,email,photo)
    

    await state.clear()
    text = f"Siz muvaffaqiyatli tarzda ro'yhatdan o'tdingiz🎉"
    await message.reply(text=text)





@dp.startup()
async def on_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=int(admin),text="Bot ishga tushdi")
        except Exception as err:
            logging.exception(err)

#bot ishga tushganini xabarini yuborish
@dp.shutdown()
async def off_startup_notify(bot: Bot):
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=int(admin),text="Bot ishdan to'xtadi!")
        except Exception as err:
            logging.exception(err)




async def main() -> None:
    global bot,db
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    db = Database(path_to_db="main.db")
    db.create_table_users()
    await set_default_commands(bot)
    dp.message.middleware(ThrottlingMiddleware(slow_mode_delay=0.5))
    await dp.start_polling(bot)
    




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())
