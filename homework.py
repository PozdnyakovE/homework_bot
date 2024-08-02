import logging
import os
import time
import requests

from dotenv import load_dotenv
from telebot import TeleBot, types

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
# PAYLOAD = {'from_date': 1721301623}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    if (PRACTICUM_TOKEN is None
            or TELEGRAM_CHAT_ID is None
            or TELEGRAM_TOKEN is None):
        return False

# @bot.message_handler()
def send_message(bot, message):
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )


def get_api_answer(timestamp):
    homework_statuses = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}).json()
    return homework_statuses
    # homeworks = homework_statuses[0].get('homeworks')
    # current_date = homework_statuses[0].get('current_date')


def check_response(response):
    if ('homeworks' in response
            and 'current_date' in response):
        return True


def parse_status(homework):
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    homework_name = homework.get('homework_name')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


# @bot.message_handler(commands=['start'])
# def wake_up(message):
#     chat = message.chat
#     name = message.chat.first_name
#     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     button = types.KeyboardButton('/newcat')
#     keyboard.add(button)

#     bot.send_message(
#         chat_id=TELEGRAM_CHAT_ID,
#         text=f'Привет, {name}. Посмотри, какого котика я тебе нашёл',
#         reply_markup=keyboard,
#     )


def main():
    """Основная логика работы бота."""

    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    bot.polling()
    timestamp = int(time.time())
    if not check_tokens():
        bot.stop_bot()

    # print(HEADERS)
    # print(PRACTICUM_TOKEN)
    # print(TELEGRAM_TOKEN)
    #print(get_api_answer(1721301623))

    current_status = ''
    # api_answer = get_api_answer(1721301623)
    # print(parse_status(api_answer.get('homeworks')[0]))

    while True:
        try:
            api_answer = get_api_answer(1721301623)
            if check_response(api_answer):
                homework = api_answer.get('homeworks')[0]
            if current_status != parse_status(homework):
                current_status = parse_status(homework)
                send_message(
                    bot,
                    current_status
                )

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        # time.sleep(RETRY_PERIOD)
        time.sleep(20)
    


if __name__ == '__main__':
    main()
