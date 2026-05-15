from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Настройка логов
logging.basicConfig(level=logging.INFO)

API_TOKEN ="8763448144:AAGP4WLppckSZML8Gxep0qpFmEoZlkzBO0o"  

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    nickname = State()
    stack = State()      # Состояние ожидания стека технологий
    description = State() # Состояние ожидания описания

# Функция для создания главного меню
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📝 Создать анкету"))
    builder.row(types.KeyboardButton(text="🔍 Найти тиммейта"), types.KeyboardButton(text="👤 Мой профиль"))
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        f"Салам, {message.from_user.first_name}! 🤖\n"
        "Это платформа для поиска IT-тиммейтов. Давай создадим твою карточку.",
        reply_markup=main_menu()
    )

@dp.message(F.text == "📝 Создать анкету")
async def create_profile(message: types.Message, state: FSMContext):
    await state.set_state(Form.nickname) # Начинаем с ника
    await message.answer("Придумай себе крутой никнейм для анкеты (например: CyberPunk или Lead Engineer):")

@dp.message(Form.nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text) # Сохраняем ник
    await state.set_state(Form.stack)
    await message.answer("Отлично! Теперь введи свой стек технологий:")

@dp.message(Form.stack)
async def process_stack(message: types.Message, state: FSMContext):
    await state.update_data(stack=message.text) # Сохраняем временно в оперативку
    await state.set_state(Form.description)
    await message.answer("Теперь напиши немного о себе или о проекте:")


@dp.message(Form.description)
async def process_description(message: types.Message, state: FSMContext):
    user_data = await state.get_data() # 1. Достаем всё, что сохранили
    from database import save_user
    
    # 2. Отправляем в базу 
    await save_user(
        message.from_user.id, 
        message.from_user.username, 
        user_data['nickname'], 
        user_data['stack'], 
        message.text
    )
    
    
    await state.clear() 
    
    
    await message.answer("Твоя анкета успешно сохранена в базу! 🦾")

@dp.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    from database import get_user
    user_info = await get_user(message.from_user.id)
    
    if user_info:
        # Распаковываем ровно 3 значения, которые вернул SELECT
        nickname, stack, description = user_info
        
        res = (
            f"Твой профиль, {message.from_user.first_name}:\n\n"
            f"👤 **Никнейм:** {nickname}\n"
            f"💻 **Стек:** {stack}\n"
            f"📝 **О себе:** {description}"
        )
        await message.answer(res)
    else:
        await message.answer("Твоя анкета пока пуста. Нажми «Создать анкету», чтобы начать! 🔥")

@dp.message(F.text == "🔍 Найти тиммейта")
async def search_teammate(message: types.Message):
    from database import get_random_user
    teammate = await get_random_user(message.from_user.id)
    
    if teammate:
    
        user_id, username, nickname, stack, description = teammate
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Лайк", callback_data=f"like_{user_id}")
        builder.button(text="❌ Пропустить", callback_data="next_teammate")
        builder.adjust(2)
        
        res = (
            f"Нашел тебе потенциального тиммейта! 🔥\n\n"
            f"👤 **Тиммейт:** {nickname}\n"
            f"💻 **Стек:** {stack}\n"
            f"📝 **О себе:** {description}\n\n"
            f"Будешь лайкать?"
        )
        await message.answer(res, reply_markup=builder.as_markup())
    else:
        await message.answer("Пока что в базе никого нет, кроме тебя. Подожди немного! 🛠️")

# Обработка лайка
@dp.callback_query(F.data.startswith("like_"))
async def handle_like(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    from database import add_like
    
    
    target_username = await add_like(callback.from_user.id, target_id)
    
    if target_username:
        # 1. Сообщаем тебе
        await callback.message.answer(
            f"🎉 Взаимный интерес! Вот твой тиммейт: @{target_username}"
        )
        
        # 2. Сообщаем второму человеку 
        # Для этого используем bot.send_message
        my_username = callback.from_user.username
        contact = f"@{my_username}" if my_username else "скрыт (напиши ему первым)"
        
        try:
            await callback.bot.send_message(
                target_id, 
                f"⚡️ У тебя новый мэтч! Пользователь заинтересовался твоим стеком. Контакт: {contact}"
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление второму юзеру: {e}")
            
    else:
        await callback.answer("Лайк отправлен! Ждем взаимности ⏳")
    
    # Убираем кнопки
    await callback.message.edit_reply_markup(reply_markup=None)

# Обработка пропустить
@dp.callback_query(F.data == "next_teammate")
async def handle_next(callback: types.CallbackQuery):
    await callback.answer("Ищем дальше...")
    # вызываем функцию поиска заново
    await search_teammate(callback.message)
    # Удаляем старые кнопки
    await callback.message.edit_reply_markup(reply_markup=None)

# Эхо-ответ для всего остального
@dp.message()
async def echo(message: types.Message):
    await message.answer("Я тебя понял, но пока не знаю, что с этим делать. Используй меню ниже 👇")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")

        import asyncio
from aiogram import Bot, Dispatcher
# Импорт функций из соседнего файла
from database import init_db, save_user 

# ... код инициализации бота ...

async def main():
    # Вызываем инициализацию базы из другого файла
    await init_db() 
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
