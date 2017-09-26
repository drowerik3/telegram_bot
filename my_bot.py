import requests
import datetime
import os

TELEGRAM_TOKEN = os.environ.get('telegram_token')
WEATHER_TOKEN = os.environ.get('weather_token')
print(TELEGRAM_TOKEN)
print(WEATHER_TOKEN)

HOURLY_TEMPLATE = '''\nHour: {time}\nActual temp: {actual} celsius\nFeels like: {feelslike} celsius\nCondition: {condition}\n'''


def handle_hourly_weather(json):
    forecast = json['hourly_forecast']
    message = ''
    now = datetime.datetime.now()
    for forecast_item in forecast:
        hour = int(forecast_item['FCTTIME']['hour'])
        if hour == 1:
            break

        time = now.replace(hour=hour, minute=0).strftime('%H:%M')
        message += HOURLY_TEMPLATE.format(
            time=time,
            actual=forecast_item['temp']['metric'],
            feelslike=forecast_item['feelslike']['metric'],
            condition=forecast_item['condition']
        )
    return message

URLS = {
    '/weather': (
        'http://api.wunderground.com/api/{token}/hourly/q/UA/Kyiv.json'.format(token=WEATHER_TOKEN),
        handle_hourly_weather
    ),
}


class CommandTypes:
    BOT_COMMAND = 'bot_command'
    OTHER = 'other'


class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self.last_update = None

    def get_updates(self, offset=None, timeout=1000):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_last_update(self, new_offset):
        updates = self.get_updates(new_offset)
        if updates:
            return updates[-1]
        return None

    def parse_input(self, last_update):
        command_type = last_update['message'].get('entities', CommandTypes.OTHER)
        if command_type == CommandTypes.OTHER:
            return

        message = last_update['message']['text']
        url, handler = URLS.get(message)
        if not url:
            return

        return handler(requests.get(url).json())

    def run(self):
        new_offset = None

        while True:
            last_update = self.get_last_update(new_offset)
            if not last_update:
                continue

            if last_update == self.last_update:
                continue
            self.last_update = last_update

            chat_id = last_update['message']['chat']['id']
            update_id = last_update['update_id']

            message = self.parse_input(last_update)
            self.send_message(chat_id, message)

            new_offset = update_id + 1


def main():
    fibi = BotHandler(TELEGRAM_TOKEN)
    fibi.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
