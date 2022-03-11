import logging
import backoff
import requests


class NymRest:

    def __init__(self, baseUrl, baseUrlGw):
        self.session = requests.Session()
        self.baseUrl = baseUrl
        self.baseUrlGw = baseUrlGw

        logging.getLogger('backoff').addHandler(logging.StreamHandler())
        logging.getLogger('backoff').setLevel(logging.INFO)
        self.logger = logging.getLogger('nym')

        logging.getLogger('backoff').addHandler(logging.StreamHandler())
        logging.getLogger('backoff').setLevel(logging.INFO)

    @backoff.on_exception(backoff.expo, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    def getStatus(self, idKey):
        endpoint = "status"
        try:
            response = self.session.get(f"{self.baseUrl}/{idKey}/{endpoint}")

            if response.ok:

                data = response.json()

                if data.get('status') == 'not_found':
                    return 'invalid'
                else:
                    return data.get('status')
            else:
                return 'invalid'

        except requests.ConnectionError as e:

            self.logger.exception(f"{e}")
            return None

    @backoff.on_exception(backoff.expo, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    def getStakeSaturation(self, idKey):
        endpoint = "stake-saturation"
        try:
            response = self.session.get(f"{self.baseUrl}/{idKey}/{endpoint}")

            if response.ok:
                if response.content == "mixnode bond not found":
                    return 'invalid'

                data = response.json()
                return data
            else:
                return 'invalid'

        except requests.ConnectionError as e:

            self.logger.exception(f"{e}")
            return None

    @backoff.on_exception(backoff.expo, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    def getRewardEstimation(self, idKey):
        endpoint = "reward-estimation"

        try:
            response = self.session.get(f"{self.baseUrl}/{idKey}/{endpoint}")

            if response.status_code == 404:
                return 'invalid'

            if response.ok:
                if response.content == "mixnode bond not found":
                    return 'invalid'
            else:
                return 'invalid'

                data = response.json()
                print(data)
                return data

        except requests.ConnectionError as e:

            self.logger.exception(f"{e}")
            return None

    @backoff.on_exception(backoff.expo, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    def getGwCoreCount(self, idKey):
        endpoint = "core-status-count"
        try:
            response = self.session.get(f"{self.baseUrlGw}/{idKey}/{endpoint}")

            if response.status_code == 404:
                return 'invalid'

            if response.ok:
                if response.content == "gateway bond not found":
                    return 'invalid'

                data = response.json()['count']
                return data
            else:
                return 'invalid'

        except requests.ConnectionError as e:

            self.logger.exception(f"{e}")
            return None
