from dotenv import load_dotenv
import os
from bot import TelegramBot
import threading
from data.base import BaseModel
from nymMonitor import NymMonitor
from nymRest import NymRest
from nymLogging import NymLogging


BASE_URL_MIXNODE = "https://sandbox-validator.nymtech.net/api/v1/status/mixnode"
BASE_URL_EXPLORER="https://sandbox-explorer.nymtech.net"


def main(telegramToken):

    db = BaseModel()
    nymAPI = NymRest(BASE_URL_MIXNODE)
    bot = TelegramBot(telegramToken, db, nymAPI,BASE_URL_EXPLORER)

    monitor = NymMonitor(db, nymAPI,bot,BASE_URL_EXPLORER, 60)
    threading.Thread(target=monitor.polling).start()
    bot.startBot()




if __name__ == '__main__':
    load_dotenv()
    NymLogging()

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    main(TELEGRAM_TOKEN)
