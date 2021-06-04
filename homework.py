import time
import requests
import telegram
import logging
import os
from dotenv import load_dotenv
from requests.exceptions import ConnectionError

load_dotenv()

API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
RESULTS = {
    'reviewing': 'Работа была отправлена на ревью.',
    'rejected': ('У вас проверили работу "{hw_name}"!'
                 'К сожалению в работе нашлись ошибки.'),
    'approved': ('У вас проверили работу "{hw_name}"!'
                 'Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку.'),
}
logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    filemode='w',
)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] not in RESULTS:
        raise ValueError('Неизвестный статус работы')
    return RESULTS[homework['status']].format(hw_name=homework_name)


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
        )
    except ConnectionError:
        raise ConnectionError('Ошибка соединения')
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(
        chat_id=CHAT_ID,
        text=message,
    )


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Бот запущен')
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                message = parse_homework_status(
                    new_homework.get('homeworks')[0])
                send_message(message, bot_client)
                logging.info(f'Сообщение отправлено: {message}')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(300)
        except Exception as error:
            message = f'Бот столкнулся с ошибкой: {error}'
            logging.error(message, exc_info=True)
            send_message(message)


if __name__ == '__main__':
    main()
