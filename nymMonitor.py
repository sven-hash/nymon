import time
import telegram
import logging

BASE_URL_EXPLORER = "https://sandbox-explorer.nymtech.net"

class NymMonitor:

    def __init__(self,dbHandler,nymAPI,bot,explorerUrl,pollingTime=10):
        self.pollingTime = pollingTime
        self.db = dbHandler
        self.nymRest = nymAPI
        self.bot = bot
        self.explorerUrl = explorerUrl

        self.logger = logging.getLogger('nym')

    def send(self,user,msg):
        self.bot.send(int(user), text=msg)

    def polling(self):
        while True:
            nodes = self.db.getMixnodes()
            for node in nodes:
                actualStatus = self.nymRest.getStatus(node.get('identityKey'))
                saturation = self.nymRest.getStakeSaturation(node.get('identityKey'))

                if saturation.get('saturation') >= 0.8:
                    msg = "⚠️ "
                    usersByMixnode = self.db.getMixnodesUser(node.get('identityKey'))
                    if saturation.get('saturation') >= 1:
                        msg = "⛔ "

                    msg += f'[{node.get("identityKey")[:5]}...{node.get("identityKey")[-4:]}]({self.explorerUrl}/network-components/mixnode/{node.get("identityKey")}) saturation to {round(saturation.get("saturation") * 100, 3)}%'
                    for user in usersByMixnode:
                        self.logger.debug(f'{node.get("identityKey")} saturation = {saturation.get("saturation")}')
                        self.bot.send(user.get('userid'),msg)

                if actualStatus != node.get('status'):
                    usersByMixnode = self.db.getMixnodesUser(node.get('identityKey'))

                    for user in usersByMixnode:
                        self.logger.debug(f'{node.get("identityKey")} changes to {actualStatus}')
                        self.bot.send(user.get('userid'), f'📟 [{node.get("identityKey")[:5]}...{node.get("identityKey")[-4:]}]({self.explorerUrl}/network-components/mixnode/{node.get("identityKey")}) changes to {actualStatus}')

                    self.db.insertMixnode(node.get('identityKey'), actualStatus)
                time.sleep(1)

            time.sleep(self.pollingTime)