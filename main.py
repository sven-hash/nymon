import logging

from dotenv import load_dotenv
import os
from bot import TelegramBot
import threading
from data.base import BaseModel
from nymMonitor import NymMonitor
from nymRest import NymRest
from nymLogging import NymLogging
import sys


BASE_URL_MIXNODE = "https://sandbox-validator.nymtech.net/api/v1/status/mixnode"
BASE_URL_GW = "https://sandbox-validator.nymtech.net/api/v1/status/gateway"
BASE_URL_EXPLORER="https://sandbox-explorer.nymtech.net"


def main(telegramToken):

    db = BaseModel()
    nymAPI = NymRest(BASE_URL_MIXNODE,BASE_URL_GW)
    bot = TelegramBot(telegramToken, db, nymAPI,BASE_URL_EXPLORER)

    monitor = NymMonitor(db, nymAPI,bot,BASE_URL_EXPLORER, 60)

    th = threading.Thread(target=monitor.polling)
    th.start()
    thGw = threading.Thread(target=monitor.gateway)
    thGw.start()

    bot.startBot()


if __name__ == '__main__':
    load_dotenv()
    NymLogging()

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    main(TELEGRAM_TOKEN)
