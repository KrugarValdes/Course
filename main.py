import asyncio
import logging, os
from aiogram import Bot
from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
import api_handler
import config
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username

    greeting_messages = [
        f"Привет, {message.from_user.full_name}!",
        f"Меня зовут @{bot_username} - незаменимый помощник, помогу отследить твою посылку по трек-коду.",
        f"Сначала добавь трек код в базу данных c помощью команды /add трек-код (тестовые коды можно взять в /test)",
        f"Для получения информации отправь мне свой зарегестрированный трек-код вида XX123456789YY или обратись в /help"
    ]

    for msg in greeting_messages:
        await message.answer(msg)

@dp.message(Command("help"))
async def handle_help(message: types.Message):
    text = ("Команды дл взаимодействия с ботом:\n"
            "/add *трек-код* для добавления трек кода в базу данных\n"
            "/full *трек-код* для вывода всей ветки доставки\n"
            "/delete *трек-код* для удаления трек кода из базы данных\n"
            "/start_updates для принудительного запуска фонового обновления трек кодов")
    await message.answer(text=text)


@dp.message(Command("test"))
async def handle_test(message: types.Message):
    # Путь к файлу
    file_path = 'track.txt'

    try:
        # Открываем файл и читаем его содержимое
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()

        # Отправляем содержимое файла в ответе
        await message.answer(file_content)
    except FileNotFoundError:
        # В случае, если файл не найден
        await message.answer("Файл не найден.")
    except Exception as e:
        # В случае возникновения других ошибок
        await message.answer(f"Произошла ошибка: {str(e)}")

@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    # Проверка наличия трек-номера в команде
    if len(message.text.split()) > 1:
        tracking_number_to_delete = message.text.split()[1]

        # Проверка валидности трек-кода
        if is_valid_tracking_code(tracking_number_to_delete):
            user_id = message.from_user.id

            # Проверка наличия указанного трек-номера в базе данных для пользователя
            if api_handler.is_tracking_number_exist(user_id, tracking_number_to_delete):
                # Удаление трек-номера из базы данных
                api_handler.delete_tracking_number(user_id, tracking_number_to_delete)
                await message.answer(f"Трек-номер {tracking_number_to_delete} успешно удален.")
            else:
                await message.answer(f"Трек-номер {tracking_number_to_delete} не найден.")
        else:
            await message.answer("Некорректный трек-номер. Пожалуйста, убедитесь, что трек-номер имеет правильную запись.")
    else:
        await message.answer("Пожалуйста, укажите трек-номер для удаления.")

@dp.message(Command("list"))
async def cmd_mytracks(message: types.Message):
    user_id = message.from_user.id

    # Get all tracking numbers for the user from the database
    tracking_numbers = api_handler.get_tracking_numbers_by_user_id(user_id)

    if not tracking_numbers:
        await message.answer("У вас нет добавленных трек-номеров.")
        return

    # Format the tracking numbers into a message
    message_text = "Ваши трек-номера:\n" + "\n".join(tracking_numbers)

    await message.answer(message_text)




# Команда "add"
@dp.message(Command("add"))
async def handle_add(message: types.Message):
    if len(message.text.split()) > 1:
        tracking_number = message.text.split()[1]
        # Проверка валидности трек-кода
        if is_valid_tracking_code(tracking_number):
            user_id = message.from_user.id
            username = message.from_user.username
            # Обновите информацию о трекинге в базе данных
            api_handler.get_tracking_info(user_id, tracking_number, username)

            await message.answer(f"Информация о трек-номере {tracking_number} успешно обновлена в базе данных.")
        else:
            await message.answer("Некорректный трек-номер. Пожалуйста, убедитесь, что трек-номер имеет правильную запись.")
    else:
        await message.answer("Пожалуйста, укажите трек-номер.")


@dp.message(Command("full"))
async def handle_full(message: types.Message):
    if len(message.text.split()) > 1:
        tracking_number = message.text.split()[1]

        # Проверка валидности трек-кода
        if is_valid_tracking_code(tracking_number):
            user_id = message.from_user.id

            # Получение обновленной информации о трекинге из базы данных
            updated_events = api_handler.get_events_from_database(user_id, tracking_number)

            # Форматирование информации о трекинге в сообщение
            message_text = f"Трек-номер: {tracking_number}"

            page_number = 1
            for idx, event in enumerate(reversed(updated_events), start=1):
                if idx % config.EVENTS_PER_PAGE == 0 and idx > 1:
                    # Отправка текущей страницы и сброс message_text
                    await message.answer(message_text)
                    page_number += 1
                    message_text = f"Трек-номер: {tracking_number} - Страница {page_number}"

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

            # Отправка последней страницы
            if message_text:
                await message.answer(message_text)
        else:
            await message.answer("Некорректный трек-номер. Пожалуильную запись.")
    else:
        await message.answer("Пожалуйста, укажите трек-номер.")

# Команда для запуска функции обновления
@dp.message(Command("start_updates"))
async def handle_start_updates(message: types.Message):
    # Запускаем функцию обновления в фоновом режиме
    asyncio.create_task(update_tracking_info())
    await message.answer("Фоновое обновление трек-номеров запущено.")






def is_valid_tracking_code(tracking_code):
    # Проверка длины трек-кода
    if len(tracking_code) not in [13, 14]:
        return False

    # Проверка, что трек-код состоит только из букв и цифр
    if not tracking_code.isalnum():
        return False

    return True
@dp.message()
async def handle_message(message: types.Message):
    tracking_number = message.text
    user_id = message.from_user.id

    # Проверяем, является ли текст валидным трек-кодом
    if is_valid_tracking_code(tracking_number):
        # Получаем информацию о событиях трек-кода из базы данных
        tracking_info = api_handler.get_events_from_database(user_id, tracking_number)

        # Assuming tracking_info is a list
        if tracking_info:
            # Take only the first event from the list
            first_event = tracking_info[0]
            await message.answer("Текущие данные о посылке:")
            # Format the first event into a message
            message_text = (
                f"Трек-номер: {tracking_number}\n"
                f"Событие - {first_event.get('Событие', 'Нет данных')}\n"
                f"Дата - {first_event.get('Дата', 'Нет данных')}\n"
                f"Время - {first_event.get('Время', 'Нет данных')}\n"
                f"Место - {first_event.get('Место', 'Нет данных')}\n"
                f"Курьер - {first_event.get('Курьер', 'Нет данных')}\n"
                f"Детали - {first_event.get('Детали', 'Нет данных')}"
            )

            # Send the formatted message to the user
            await message.answer(message_text)
        else:
            # If there are no events, provide a message
            await message.answer("Информация о доставке отсутствует.")
    else:
        # If the text is not a valid tracking code, provide a message
        await message.answer("Пожалуйста, введите валидный трек-код.")

async def update_tracking_info():
    while True:
        # Получите все трек-номера из базы данных
        tracking_numbers = api_handler.get_all_tracking_numbers()
        print("start-update")
        # Создайте словарь для хранения предыдущего количества событий для каждого трек-номера
        previous_event_counts = {}

        # Обновите информацию для каждого трек-номера
        for tracking_number in tracking_numbers:
            user_id = api_handler.get_user_id_by_tracking_number(tracking_number)
            # Получите предыдущее количество событий
            previous_event_count = api_handler.get_event_count_for_tracking_number(tracking_number)
            print(previous_event_count)
            previous_event_counts[tracking_number] = previous_event_count

            api_handler.get_tracking_info(user_id, tracking_number)

            # Получите текущее количество событий
            current_event_count = api_handler.get_event_count_for_tracking_number(tracking_number)
            print(previous_event_count,current_event_count)
            # Сравните предыдущее и текущее количество событий
            if current_event_count != previous_event_count:
                # Отправьте уведомление пользователю о изменении количества событий
                await send_notification(user_id, tracking_number)

        # Ждем 10 минут перед следующим обновлением
        await asyncio.sleep(600)

async def send_notification(user_id, tracking_number):
    message = f"Количество событий для трек-номера {tracking_number} изменилось."
    bot = Bot(token=config.BOT_TOKEN)
    await bot.send_message(user_id, message)

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config.BOT_TOKEN)
    # Запустите функцию обновления трек-номеров в фоновом режиме
    asyncio.create_task(update_tracking_info())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

