import asyncio
import logging
from aiogram.utils import markdown
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.filters import CommandStart, Command
import api_handler
import config
import re
dp = Dispatcher()





@dp.message(CommandStart())
async def handle_start(message: types.Message):
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username

    greeting_messages = [
        f"Привет, {message.from_user.full_name}!",
        f"Меня зовут @{bot_username} - незаменимый помощник, помогу отследить любую посылку по трек-коду.",
        "Отправь мне свой трек-код вида XX123456789YY:"
    ]

    for msg in greeting_messages:
        await message.answer(msg)

@dp.message(Command("help"))
async def handle_help(message: types.Message):
    text = "I'm and echo bot.\nSend me any message!"
    await message.answer(text=text)


@dp.message(Command("full"))
async def handle_full(message: types.Message):
    tracking_number = message.text.split()[1]
    tracking_info = api_handler.get_tracking_info(tracking_number)
    await message.answer(tracking_info)

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()

    # Проверяем, является ли текст валидным трек-кодом
    if is_valid_tracking_code(text):
        tracking_info = api_handler.get_tracking_info(text)
        current_status = tracking_info["Events"][0] if tracking_info.get(
            "Events") else "Информация о доставке отсутствует."
        await message.answer(current_status)
    else:
        # Если текст не является трек-кодом, можно выполнить другие действия или проигнорировать
        await message.answer("Пожалуйста, введите валидный трек-код.")


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config.BOT_TOKEN)
    await dp.start_polling(bot)

def is_valid_tracking_code(tracking_code):
    # Проверка длины трек-кода
    if len(tracking_code) not in [13, 14]:
        return False

    # Проверка, что трек-код состоит только из букв и цифр
    if not tracking_code.isalnum():
        return False

    return True

if __name__ == "__main__":
    asyncio.run(main())

    # Define the maximum number of events per page
    EVENTS_PER_PAGE = 5
    from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup


    @dp.message(Command("full"))
    async def handle_full(message: Message):
        tracking_number = message.text.split()[1]
        user_id = message.from_user.id

        # Update the tracking information in the database
        api_handler.get_tracking_info_and_add_to_database(user_id, tracking_number)

        # Retrieve the updated tracking information from the database
        updated_events = api_handler.get_events_from_database(user_id, tracking_number)

        # Format the tracking information into a message
        message_text = f"Трек-номер: {tracking_number}"

        # Initialize the page number
        page = 1

        for idx, event in enumerate(reversed(updated_events), start=1):
            if idx % EVENTS_PER_PAGE == 0 and idx > 1:
                # Create the inline keyboard
                keyboard = InlineKeyboardMarkup()

                # Add buttons for the current page
                for i in range(page, page + 2):
                    if i < len(updated_events):
                        keyboard.add(InlineKeyboardButton(f"#{i}", callback_data=f"event{i}"))

                # Add buttons for navigating between pages
                if page + 2 < len(updated_events):
                    btn_next = InlineKeyboardButton(text="Далее", callback_data='next')
                    keyboard.add(btn_next)
                if page > 1:
                    btn_prev = InlineKeyboardButton(text="Назад", callback_data='prev')
                    keyboard.add(btn_prev)

                # Send the current page and the keyboard
                await message.answer(message_text, reply_markup=keyboard)
                page += 1
                message_text = f"Трек-номер: {tracking_number} - Страница {page}"

            event_type = event.get("Событие", "Нет данных")
            event_date = event.get("Дата", "Нет данных")
            event_time = event.get("Время", "Нет данных")
            event_location = event.get("Место", "Нет данных")
            event_courier = event.get("Курьер", "Нет данных")
            event_details = event.get("Детали", "Нет данных")

            message_text += (
                f"\n\n#{idx}\n"
                f"Событие - {event_type}\n"
                f"Дата - {event_date}\n"
                f"Время - {event_time}\n"
                f"Место - {event_location}\n"
                f"Курьер - {event_courier}\n"
                f"Детали - {event_details}"
            )

        # Send the last page if there are any events left
        if message_text:
            await message.answer(message_text)