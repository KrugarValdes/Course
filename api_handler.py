import requests
from datetime import datetime
from googletrans import Translator
import sqlite3
import config
api_key = config.api_key

def get_tracking_info(user_id, tracking_number, username=None):
    url = "https://api.ship24.com/public/v1/trackers/track"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8",
    }
    data = {
        "trackingNumber": tracking_number,
    }

    # Получаем текущее количество событий для трек-номера
    current_event_count = get_event_count_for_tracking_number(tracking_number)
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200 or response.status_code == 201:
        tracking_info = response.json()["data"]["trackings"][0]
        events = tracking_info.get("events", [])

        # Add user and tracking number to the database
        if username:
            add_user_to_database(user_id, username)

        # Если текущее количество событий совпадает с предыдущим, не обновляем базу данных
        if len(events) != current_event_count:
            add_tracking_number(user_id, tracking_number, event_count=len(events))
            # Delete existing events for the tracking number
            conn = sqlite3.connect('tracking_database.db')
            cursor = conn.cursor()
            cursor.execute('''
                        DELETE FROM events
                        WHERE tracking_number_id IN (
                            SELECT id FROM tracking_numbers
                            WHERE user_id = ? AND tracking_number = ?
                        )
                    ''', (user_id, tracking_number))
            conn.commit()

            # Add each event to the database
            for event in events:
                add_tracking_state(user_id, tracking_number, event)

        return events
    elif response.status_code == 401:
        error_data = response.json()
        return [{"Error": f"{response.status_code}, {error_data['errors'][0]['message']}"}]
    else:
        return [{"Error": f"{response.status_code}, {response.text}"}]


def get_events_from_database(user_id, tracking_number):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT event_type, event_date, event_time, event_location, event_courier, event_details
        FROM events
        WHERE tracking_number_id IN (
            SELECT id FROM tracking_numbers
            WHERE user_id = ? AND tracking_number = ?
        )
    ''', (user_id, tracking_number))

    events = cursor.fetchall()

    conn.close()

    formatted_events = []
    for event in events:
        formatted_events.append({
            "Событие": event[0],
            "Дата": event[1],
            "Время": event[2],
            "Место": event[3],
            "Курьер": event[4],
            "Детали": event[5],
        })

    return formatted_events

def add_user_to_database(user_id, username):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username)
        VALUES (?, ?)
    ''', (user_id, username))

    conn.commit()
    conn.close()

def add_tracking_number(user_id, tracking_number, event_count=0):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO tracking_numbers (user_id, tracking_number, event_count)
        VALUES (?, ?, ?)
    ''', (user_id, tracking_number, event_count))

    conn.commit()
    conn.close()

def add_tracking_state(user_id, tracking_number, event):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    formatted_event = format_event(event)

    # Get the tracking_number_id based on user_id and tracking_number
    cursor.execute('''
        SELECT id FROM tracking_numbers
        WHERE user_id = ? AND tracking_number = ?
    ''', (user_id, tracking_number))
    tracking_number_id = cursor.fetchone()

    if tracking_number_id:
        tracking_number_id = tracking_number_id[0]
        cursor.execute('''
            INSERT INTO events
            (tracking_number_id, event_type, event_date, event_time, event_location, event_courier, event_details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tracking_number_id,
              formatted_event["Событие"],
              formatted_event["Дата"],
              formatted_event["Время"],
              formatted_event["Место"],
              formatted_event["Курьер"],
              formatted_event["Детали"]))

    conn.commit()
    conn.close()


def get_event_count_for_tracking_number(tracking_number):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM events
        WHERE tracking_number_id = (
            SELECT id FROM tracking_numbers
            WHERE tracking_number = ?
        )
    ''', (tracking_number,))

    result = cursor.fetchone()
    event_count = result[0] if result is not None else 0

    conn.close()

    return event_count


def get_all_tracking_numbers():
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Выберите все трек-номера из таблицы tracking_numbers
    cursor.execute('SELECT tracking_number FROM tracking_numbers')
    tracking_numbers = cursor.fetchall()

    conn.close()

    # Преобразуйте результат в список
    return [tracking_number[0] for tracking_number in tracking_numbers]

def get_user_id_by_tracking_number(tracking_number):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Найдите user_id по трек-номеру в таблице tracking_numbers
    cursor.execute('SELECT user_id FROM tracking_numbers WHERE tracking_number = ?', (tracking_number,))
    result = cursor.fetchone()

    conn.close()

    # Верните user_id, если он найден, иначе None
    return result[0] if result else None

def get_tracking_numbers_by_user_id(user_id):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Fetch the tracking numbers for the given user_id
    cursor.execute('''
        SELECT tracking_number FROM tracking_numbers WHERE user_id = ?
    ''', (user_id,))

    tracking_numbers = [row[0] for row in cursor.fetchall()]

    conn.close()

    return tracking_numbers

# проверка существования конкретного трек-номера для заданного user_id в базе данных
def is_tracking_number_exist(user_id, tracking_number):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Check if the tracking number exists for the given user_id
    cursor.execute('''
        SELECT 1 FROM tracking_numbers WHERE user_id = ? AND tracking_number = ?
    ''', (user_id, tracking_number))

    result = cursor.fetchone()
    conn.close()

    return result is not None

def delete_tracking_number(user_id, tracking_number):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Получение tracking number ID
    cursor.execute('''
        SELECT id FROM tracking_numbers WHERE user_id = ? AND tracking_number = ?
    ''', (user_id, tracking_number))
    tracking_number_id = cursor.fetchone()

    if tracking_number_id:
        tracking_number_id = tracking_number_id[0]

        # Удаление событий, связанных с номером отслеживания
        cursor.execute('''
            DELETE FROM events WHERE tracking_number_id = ?
        ''', (tracking_number_id,))

        # Удаление трек номера
        cursor.execute('''
            DELETE FROM tracking_numbers WHERE user_id = ? AND tracking_number = ?
        ''', (user_id, tracking_number))

        conn.commit()
        conn.close()
    else:
        conn.close()
        raise ValueError(f"Tracking number {tracking_number} not found for user {user_id}")

def translate_text(text):
    translator = Translator()
    translated_text = translator.translate(text, dest='ru').text
    return translated_text

def format_event(event):
    print(event)
    occurrence_datetime = event.get('occurrenceDatetime')
    event_time = datetime.strptime(occurrence_datetime.split('+')[0], "%Y-%m-%dT%H:%M:%S")
    formatted_date = event_time.strftime("%d.%m.%Y")
    formatted_time = event_time.strftime("%H:%M:%S")
    # Translate event status
    translated_event_status = translate_text(event['status'])
    #translated_event_status = event['status']

    return {
        "Событие": translated_event_status,
        "Дата": formatted_date,
        "Время": formatted_time,
        "Место": event['location'],
        "Курьер": event['courierCode'],
        "Детали": event['statusMilestone']
    }