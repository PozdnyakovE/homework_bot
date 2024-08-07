import logging
import os
import requests
import sys
import time

from dotenv import load_dotenv
from http import HTTPStatus
from telebot import TeleBot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

NO_REQUIRED_VARIABLES = 'Не найдены обязательные переменные окружения.'
MESSAGE_SENT = 'Сообщение {key} отправлено'
MESSAGE_NOT_SENT = 'Не удалось отправить сообщение. Ошибка: {key}'
REQUEST_ERROR = 'Ошибка выполнения запроса: {key}'
SERVER_ERROR = 'Сервер ответил с ошибкой {key}'
WRONG_API_RESPONSE = 'Неверный тип данных ответа API'
NO_DATA_IN_API_RESPONSE = 'Ключ {key} не найден в ответе API'
UNEXPECTED_HOMEWORK_STATUS = 'Неожиданный статус домашней работы: {key}'
STATUS_CHANGED = 'Изменился статус проверки работы "{name}". {verdict}'
STATUS_NOT_CHANGED = 'Статус работы не обновлен.'
COMMON_ERROR = 'Сбой в работе программы: {key}'
NO_ACTIVE_HOMEWORKS = 'На данный момент нет домашних работ на проверке'


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия необходимых переменных окружения."""
    if (PRACTICUM_TOKEN is None
            or TELEGRAM_CHAT_ID is None
            or TELEGRAM_TOKEN is None):
        logger.critical(NO_REQUIRED_VARIABLES)
        raise UnboundLocalError(NO_REQUIRED_VARIABLES)


def send_message(bot, message):
    """Функция отправки сообщения в Телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(MESSAGE_SENT.format(key=message))
        return True
    except Exception as error:
        logger.error(MESSAGE_NOT_SENT.format(key=error))


def get_api_answer(timestamp):
    """Получение ответа от API Яндекс Практикум.
    Возвращает ответ в виде словаря.
    """
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp})
    except requests.exceptions.RequestException as error:
        logger.error(REQUEST_ERROR.format(key=error))
        raise SystemError(error)
    if homework_statuses.status_code != HTTPStatus.OK:
        raise requests.exceptions.HTTPError(
            SERVER_ERROR.format(key=homework_statuses.status_code)
        )
    return homework_statuses.json()


def check_response(response):
    """Проверка валидности полученного ответа API.
    Возвращает ответ функции get_api_answer()
    после прохождения проверок.
    """
    if (not isinstance(response, dict)
            or not isinstance(response.get('homeworks'), list)):
        raise TypeError(WRONG_API_RESPONSE)
    if 'homeworks' not in response:
        raise ValueError(NO_DATA_IN_API_RESPONSE.format(key='homeworks'))
    return response


def parse_status(homework):
    """Возвращает ответ API в виде строки с указанием текущего
    статуса и названия домашней работы. Проверяет соответствие ответа
    необходимому формату.
    """
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(UNEXPECTED_HOMEWORK_STATUS.format(key=status))
    verdict = HOMEWORK_VERDICTS.get(status)
    if 'homework_name' not in homework:
        raise ValueError(NO_DATA_IN_API_RESPONSE.format(key='homework_name'))
    homework_name = homework.get('homework_name')
    return STATUS_CHANGED.format(name=homework_name, verdict=verdict)


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_status = ''
    message = ''

    while True:
        try:
            api_answer = check_response(get_api_answer(timestamp))
            homework_list = api_answer.get('homeworks')
            if homework_list == []:
                logger.debug(NO_ACTIVE_HOMEWORKS)
                continue
            timestamp = api_answer.get('current_date')
            message = parse_status(homework_list[0])
        except Exception as error:
            message = COMMON_ERROR.format(key=error)
            logger.error(message)
        finally:
            if current_status != message:
                send_message(bot, message)
                current_status = message
            else:
                logger.debug(STATUS_NOT_CHANGED)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
