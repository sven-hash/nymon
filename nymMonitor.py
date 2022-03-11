import time
import telegram
import logging

BASE_URL_EXPLORER = "https://sandbox-explorer.nymtech.net"


class NymMonitor:

    def __init__(self, dbHandler, nymAPI, bot, explorerUrl, pollingTime=10):
        self.pollingTime = pollingTime
        self.db = dbHandler
        self.nymRest = nymAPI
        self.bot = bot
        self.explorerUrl = explorerUrl

        self.logger = logging.getLogger('nym')

    def send(self, user, msg):
        try:
            self.bot.send(int(user), text=msg)
        except telegram.error.NetworkError as e:
            self.logger.exception(f"NymMonitor {e}")

    def polling(self):
        self.logger.debug('Mixnode pooler start')
        while True:

            nodes = self.db.getMixnodes()
            for node in nodes:

                actualStatus = self.nymRest.getStatus(node.get('identityKey'))
                saturation = self.nymRest.getStakeSaturation(node.get('identityKey'))

                if actualStatus != 'invalid' and actualStatus is not None:

                    try:
                        if saturation['saturation'] >= 0.8:
                            msg = "⚠️ "
                            usersByMixnode = self.db.getMixnodesUser(node.get('identityKey'))
                            if saturation.get('saturation') >= 1:
                                msg = "⛔ "

                            msg += f'[{node.get("identityKey")[:5]}...{node.get("identityKey")[-4:]}]({self.explorerUrl}/network-components/mixnode/{node.get("identityKey")}) saturation to {round(saturation.get("saturation") * 100, 3)}%'
                            for user in usersByMixnode:
                                self.logger.debug(f'{node.get("identityKey")} saturation = {saturation.get("saturation")}')
                                self.bot.send(user.get('userid'), msg)
                    except KeyError as e:
                        self.logger.exception(e)

                    if actualStatus != node.get('status'):
                        usersByMixnode = self.db.getMixnodesUser(node.get('identityKey'))

                        for user in usersByMixnode:
                            self.logger.debug(f'{node.get("identityKey")} changes to {actualStatus}')
                            self.bot.send(user.get('userid'),
                                          f'📟 [{node.get("identityKey")[:5]}...{node.get("identityKey")[-4:]}]({self.explorerUrl}/network-components/mixnode/{node.get("identityKey")}) changes to {actualStatus}')

                        self.db.insertMixnode(node.get('identityKey'), actualStatus)
                elif actualStatus == 'invalid':
                    print(node.get('identityKey'))
                    self.db.deleteNode(node.get('identityKey'))
                else:
                    pass

                time.sleep(1)

            time.sleep(self.pollingTime)

    def gateway(self):
        self.logger.debug('GW pooler start')
        while True:
            nodes = self.db.getGw()
            for node in nodes:

                actualCounter = self.nymRest.getGwCoreCount(node.get('identityKey'))
                if actualCounter is not None:

                    if actualCounter == node.get('counter'):
                        usersByNode = self.db.getGwUser(node.get('identityKey'))

                        for user in usersByNode:
                            self.logger.debug(f'{node.get("identityKey")} was used {node.get("counter")}')
                            self.bot.send(user.get('userid'),
                                          f'⏲️ [{node.get("identityKey")[:5]}...{node.get("identityKey")[-4:]}]({self.explorerUrl}/network-components/gateway/{node.get("identityKey")}) was used\n\n🧮 Time selected: {node.get("counter")}')

                        self.db.insertMixnode(node.get('identityKey'), actualCounter)
                elif actualCounter == 'invalid':
                    self.db.deleteNode(node.get('identityKey'), isGw=True)
                else:
                    pass

                time.sleep(1)

            time.sleep(self.pollingTime)
