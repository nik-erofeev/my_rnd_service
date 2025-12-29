from urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError, ConnectTimeout

from rnd_connectors.fluent.protocols import FluentdConfigProtocol
from rnd_connectors.fluent.schemas import FluentDBLog, FluentELKLog, FluentZSMLog


class FluentdClient:
    """
    Fluentd adapter handler for base Python`s logger.
    """

    def __init__(self, fluent_config: FluentdConfigProtocol):
        """
        Init
        :param fluent_config: FluentdConfigProtocol
        """
        self.fluentd_config = fluent_config

    def _request_post(self, msg: dict, url: str, timeout: float | None = None):
        try:
            response = requests.post(
                url,
                json=msg,
                verify=self.fluentd_config.cert_path if self.fluentd_config.verify else False,
                timeout=timeout or self.fluentd_config.timeout,
            )
            return response

        except (ConnectTimeout, ConnectionError) as e:
            print(f"connect on problem: {e}")
            return None

        except Exception as e:
            print(f"непредвиденная ошибка: {e}")
            return None

    def send_to_db(self, msg: FluentDBLog, timeout: float | None = None):
        msg_dict = msg.model_dump(exclude_none=True)
        url = urljoin(self.fluentd_config.url, "pim.logger.db")
        return self._request_post(msg_dict, url, timeout)

    def send_to_efk(self, msg: FluentELKLog, timeout: float | None = None):
        msg_dict = msg.model_dump(exclude_none=True)
        url = urljoin(self.fluentd_config.url, "pim.logger.efk/")
        return self._request_post(msg_dict, url, timeout)

    def send_to_metric(self, msg: FluentZSMLog, timeout: float | None = None):
        msg_dict = msg.model_dump(exclude_none=True)
        url = urljoin(self.fluentd_config.url, "pim.metrics.zsm")
        return self._request_post(msg_dict, url, timeout)
