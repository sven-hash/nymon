import requests
import nymLogging
import logging

class NymRest:

    def __init__(self,baseUrl):
        self.session = requests.Session()
        self.baseUrl = baseUrl
        logging.getLogger('backoff').addHandler(logging.StreamHandler())
        logging.getLogger('backoff').setLevel(logging.INFO)
        self.logger = logging.getLogger('nym')

    def getStatus(self,idKey):
        endpoint = "status"
        try:
            response = self.session.get(f"{self.baseUrl}/{idKey}/{endpoint}")

            if response.ok:

                data = response.json()

                if data.get('status') == 'not_found':
                    return 'invalid'
                else:
                    return data.get('status')

        except requests.ConnectionError as e:
            self.logger.exception(f"{e}, reponse {response.content}")
            return None

    def getStakeSaturation(self,idKey):
        endpoint = "stake-saturation"
        try:
            response = self.session.get(f"{self.baseUrl}/{idKey}/{endpoint}")

            if response.ok:
                if response.content == "mixnode bond not found":
                    return 'invalid'

                data = response.json()
                return data

        except requests.ConnectionError as e:
            self.logger.exception(f"{e}, reponse {response.content}")
            return None

    def getRewardEstimation(self,idKey):
        endpoint = "reward-estimation"
        try:
            response = self.session.get(f"{self.baseUrl}/{idKey}/{endpoint}")

            if response.ok:
                if response.content == "mixnode bond not found":
                    return 'invalid'

                data = response.json()
                print(data)
                return data

        except requests.ConnectionError as e:
            self.logger.exception(f"{e}, reponse {response.content}")
            return None