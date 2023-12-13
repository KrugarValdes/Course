import sqlite3

def add_tracking_state(tracking_number, event_type, event_date, event_time, event_location, event_courier, event_details):
    conn = sqlite3.connect('tracking_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO tracking_states
        (tracking_number, event_type, event_date, event_time, event_location, event_courier, event_details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tracking_number, event_type, event_date, event_time, event_location, event_courier, event_details))

    conn.commit()
    conn.close()
