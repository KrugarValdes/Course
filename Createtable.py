import sqlite3

import sqlite3

def create_tables():
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Create table for users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT
        )
    ''')

    # Create table for tracking numbers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_numbers (
            id INTEGER PRIMARY KEY,
            tracking_number TEXT UNIQUE,
            user_id INTEGER,
            event_count INTEGER DEFAULT 0,  -- Добавленное поле для количества событий
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create table for events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            tracking_number_id INTEGER,
            event_type TEXT,
            event_date TEXT,
            event_time TEXT,
            event_location TEXT,
            event_courier TEXT,
            event_details TEXT,
            FOREIGN KEY (tracking_number_id) REFERENCES tracking_numbers(id)
        )
    ''')

    conn.commit()
    conn.close()

def add_tracking_number(tracking_number):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Insert tracking number
    cursor.execute('''
        INSERT OR IGNORE INTO tracking_numbers (tracking_number) VALUES (?)
    ''', (tracking_number,))

    conn.commit()
    conn.close()

def add_event(tracking_number, event):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    # Get tracking number id
    cursor.execute('SELECT id FROM tracking_numbers WHERE tracking_number = ?', (tracking_number,))
    tracking_number_id = cursor.fetchone()

    if tracking_number_id:
        tracking_number_id = tracking_number_id[0]
        # Insert event
        cursor.execute('''
            INSERT INTO events
            (tracking_number_id, event_type, event_date, event_time, event_location, event_courier, event_details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tracking_number_id,
              event["status"],
              event["occurrenceDatetime"],
              event["occurrenceDatetime"],
              event["location"],
              event["courierCode"],
              event["statusMilestone"]))

    conn.commit()
    conn.close()

# Example usage
create_tables()
#add_tracking_number("LK201861585CN")
#add_event("LK201861585CN", {"status": "Arrival", "occurrenceDatetime": "2023-12-02T13:18:00", "location": "Some Location", "courierCode": "Courier", "statusMilestone": "In Transit"})

