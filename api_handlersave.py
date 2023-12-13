import requests
from datetime import datetime
api_key = "apik_0sRavrCGbq9V8S9DUQl8ASQNzWjW11"

def format_event(event):
    event_time = datetime.strptime(event["occurrenceDatetime"], "%Y-%m-%dT%H:%M:%S").strftime("%d.%m.%Y %H:%M:%S")
    return f"Событие - {event['status']}\nДата - {event_time}\nВремя - {event_time.split()[1]}\nМесто - {event['location']}\nКурьер - {event['courierCode']}\nДетали - {event['statusMilestone']}"

def format_tracking_info(tracking_info):
    shipment_info = tracking_info["shipment"]
    events = tracking_info["events"]
    formatted_events = [format_event(event) for event in events]
    return f"Трек-номер: {tracking_info['tracker']['trackingNumber']}\nСтатус: {shipment_info['statusMilestone']}\n\n" + "\n\n".join(formatted_events)

def get_tracking_info(tracking_number):
    url = "https://api.ship24.com/public/v1/trackers/track"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8",
    }
    data = {
        "trackingNumber": tracking_number,
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200 or response.status_code == 201:
        tracking_info = response.json()["data"]["trackings"][0]
        return format_tracking_info(tracking_info)
    elif response.status_code == 401:
        error_data = response.json()
        return f"Error: {response.status_code}, {error_data['errors'][0]['message']}"
    else:
        return f"Error: {response.status_code}, {response.text}"
print(get_tracking_info("LK201861585CN"))