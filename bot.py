import logging
import time

import bleach
import telegram
from telegram import ParseMode
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.update import Update

BASE_URL_MIXNODE = "https://sandbox-validator.nymtech.net/api/v1/status/mixnode"
BASE_URL_EXPLORER = "https://sandbox-explorer.nymtech.net"

STATE_INACTIVE = "🟥"
STATE_STANDBY = "🟦"
STATE_ACTIVE = "🟩"
STATE_ERROR = "🟨"

TIME_FORMAT = "%d.%m.%y %H:%M:%S"


class TelegramBot:

    def __init__(self, token, dbHandler, nymAPIHandler, explorerUrl):
        self.token = token
        self.nymRest = nymAPIHandler
        self.updater = Updater(self.token, use_context=True)
        self.db = dbHandler
        self.explorerUrl = explorerUrl

        self.updater.dispatcher.add_handler(CommandHandler('start', self.start))
        self.updater.dispatcher.add_handler(CommandHandler('help', self.help))
        self.updater.dispatcher.add_handler(CommandHandler('mixnode', self.mixnode))
        self.updater.dispatcher.add_handler(CommandHandler('gateway', self.gateway))
        self.updater.dispatcher.add_handler(CommandHandler('gw', self.gateway))
        self.updater.dispatcher.add_handler(CommandHandler('remove', self.remove))
        self.updater.dispatcher.add_handler(CommandHandler('removegw', self.removegw))
        self.updater.dispatcher.add_handler(CommandHandler('rewards', self.rewards))
        self.updater.dispatcher.add_handler(CommandHandler('reward', self.rewards))

        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.unknown))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.command, self.unknown))

        # Filters out unknown messages.
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.unknown_text))

        self.logHandler = logging.getLogger('nym')
        self.logHandler.info(f"Start {__name__}")

    def startBot(self):
        try:
            self.updater.start_polling(bootstrap_retries=20, timeout=20)
        except Exception as e:
            self.logHandler.exception(e)
            self.updater.stop()

    def send(self, user, msg):
        for __ in range(10):
            try:
                bot = telegram.Bot(token=self.token)
                bot.sendMessage(int(user), text=msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            except telegram.error.RetryAfter as ra:
                self.logHandler.exception(e)

                if int(ra.retry_after) > 60:
                    print("Flood control exceeded. Retry in 60 seconds")
                    time.sleep(60)
                else:
                    time.sleep(int(ra.retry_after))
                continue
            except Exception as e:
                self.logHandler.exception(e)
            else:
                break

    def start(self, update: Update, context: CallbackContext):
        username = update.message.from_user.username
        update.message.reply_text(f"Hello, {username}!\n"
                                  f"Set your mixnode identity key to monitor it (/mixnode identity key)")

    def help(self, update: Update, context: CallbackContext):
        update.message.reply_text("Available Commands :"
                                  "\n\t/mixnode <identity key> - To start the mixnode monitoring"
                                  "\n\t/remove <identity key> - To remove the mixnode from monitoring")

    def mixnode(self, update: Update, context: CallbackContext):
        if update.edited_message:
            self.logHandler.error(f"mixnode() Edited message from {update.edited_message.from_user.id}")
            return

        if len(context.args) == 1:
            idKey = bleach.clean(context.args[0])
            status = self.nymRest.getStatus(idKey)
            if status == 'invalid':
                self.logHandler.error(f"mixnode, Data {context.args}")
                update.message.reply_text(f"Mixnode {idKey} not found")
            else:
                if self.setData(update.message.from_user.id, idKey, status, True):
                    text = f"Start Monitoring mixnode"
                    text += f"\n🔑 Identity Key [{idKey[:5]}...{idKey[-4:]}]({self.explorerUrl}/network-components/mixnode/{idKey})"

                    if status == 'inactive':
                        text += f"\n{STATE_INACTIVE} "
                    elif status == 'standby':
                        text += f"\n{STATE_STANDBY} "
                    elif status == 'active':
                        text += f"\n{STATE_ACTIVE} "
                    else:
                        text += f"\n{STATE_ERROR} "

                    text += f"{status.title()}"

                    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
                else:
                    update.message.reply_text(
                        f"Monitoring already exists for mixnode {idKey}")

        else:
            update.message.reply_text(
                f"Error: Usage /mixnode identity key")

    def remove(self, update: Update, context: CallbackContext):
        if update.edited_message:
            self.logHandler.error(f"remove() Edited message from {update.edited_message.from_user.id}")
            return

        if len(context.args) == 1:
            idKey = bleach.clean(context.args[0])
            status = self.nymRest.getStatus(idKey)

            if status == 'invalid':
                self.logHandler.error(f"mixnode, Data {context.args}")
                update.message.reply_text(f"Mixnode {idKey} not found")
            elif status is None:
                self.logHandler.error(f"mixnode, Data {context.args}")
                update.message.reply_text(f"Error with mixnode {idKey}")
            else:
                if self.delData(update.message.from_user.id, idKey, False):
                    update.message.reply_text(
                        f"mixnode {idKey} removed")
                else:
                    update.message.reply_text(
                        f"No mixnode with {idKey} for you")

        else:
            update.message.reply_text(
                f"Error: Usage /mixnode mixnode identity key")

    def removegw(self, update: Update, context: CallbackContext):
        if update.edited_message:
            self.logHandler.error(f"remove() Edited message from {update.edited_message.from_user.id}")
            return

        if len(context.args) == 1:
            idKey = bleach.clean(context.args[0])

            if self.delData(update.message.from_user.id, idKey, False, isGw=True):
                update.message.reply_text(
                    f"gw {idKey} removed")
            else:
                update.message.reply_text(
                    f"No gw with {idKey} for you")

        else:
            update.message.reply_text(
                f"Error: Usage /removegw gateway identity key")


    def rewards(self, update: Update, context: CallbackContext):
        if update.edited_message:
            self.logHandler.error(f"rewards() Edited message from {update.edited_message.from_user.id}")
            return

        if len(context.args) == 1:
            idKey = bleach.clean(context.args[0])
            status = self.nymRest.getRewardEstimation(idKey)

            if status == 'invalid':
                self.logHandler.error(f"rewards(), Data {context.args}")
                update.message.reply_text(f"Mixnode {idKey[:5]}...{idKey[-4:]} not found")
            elif status is None:
                self.logHandler.error(f"rewards(), Data {context.args}")
                update.message.reply_text(f"Error with mixnode {idKey[:5]}...{idKey[-4:]}")
            else:
                self.logHandler.debug(f"rewards(), mixnode {idKey}, data {status}")
                text = f"Rewards for mixnode [{idKey[:5]}...{idKey[-4:]}]({self.explorerUrl}/network-components/mixnode/{idKey})\n"
                text += f"💰Total node: {status.get('estimated_total_node_reward')} uNYM\n"
                text += f"🧍Personnal: {status.get('estimated_operator_reward')} uNYM\n"
                text += f"🫂Delegators: {status.get('estimated_delegators_reward')} uNYM\n"
                # text += f"From {datetime.fromtimestamp(status.get('current_interval_start')).strftime(TIME_FORMAT)} to {datetime.fromtimestamp(status.get('as_at')).strftime(TIME_FORMAT)}\n"

                update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        else:
            update.message.reply_text(
                f"Error: Usage /rewards mixnode identity key")


    def gateway(self, update: Update, context: CallbackContext):
        if update.edited_message:
            self.logHandler.error(f"gateway() Edited message from {update.edited_message.from_user.id}")
            return

        if len(context.args) == 1:
            idKey = bleach.clean(context.args[0])
            status = self.nymRest.getGwCoreCount(idKey)
            if status == 'invalid':
                self.logHandler.error(f"gateway, Data {context.args}")
                update.message.reply_text(f"Gateway {idKey} not found")
            else:
                if self.setData(update.message.from_user.id, idKey, status, True, 'gateway'):
                    text = f"Start Monitoring gateway"
                    text += f"\n🔑 Identity Key [{idKey[:5]}...{idKey[-4:]}]({self.explorerUrl}/network-components/gateway/{idKey})"

                    text += f"\n🧮 Time selected: {status}"

                    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
                else:
                    update.message.reply_text(
                        f"Monitoring already exists for gateway {idKey}")

        else:
            update.message.reply_text(
                f"Error: Usage /gateway identity key")


    def unknown_text(self, update: Update, context: CallbackContext):
        self.logHandler.error(f"unknown_text: {update.message.text}")
        update.message.reply_text(
            "Sorry I can't recognize you , you said '%s'" % update.message.text)


    def unknown(self, update: Update, context: CallbackContext):
        self.logHandler.error(f"unknown: {update.message.text}")
        update.message.reply_text(
            "Sorry '%s' is not a valid command" % update.message.text)


    def setData(self, userId, mixnode, status='inactive', monitor=True, type='mixnode'):
        userId = str(userId)
        if type == 'mixnode':
            self.db.insertMixnode(mixnode, status)
            return self.db.insertUser(userId, mixnode=mixnode, state=monitor)
        elif type == 'gateway':
            self.db.insertGw(mixnode, status)
            return self.db.insertUser(userId, gatewayid=mixnode, state=monitor)


    def delData(self, userId, mixnode, monitor, isGw=False):
        userId = str(userId)
        if not isGw:
            return self.db.insertUser(userId, mixnode, monitor)
        else:
            return self.db.insertUser(userId, gatewayid=mixnode, state=False)
