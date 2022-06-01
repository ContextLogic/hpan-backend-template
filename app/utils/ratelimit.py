"""
utils.ratelimit defines the global singleton of ratelimit client class.
the class provides the ratelimit methods.
"""

import json
import logging

from requests import Session, post
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class RatelimitClient:
    """
    RatelimitClient defines a customized http client built on requests for our
    ratelimiting service (https://alki.i.wish.com/).
    """

    _url: str = "http://ratelimit.service.consul:8080"
    _domain: str = "python-backend-worker-template"
    _default_ratelimit_name: str = "default"

    @classmethod
    def init(
        cls,
        host: str,
        domain: str,
        default_ratelimit_name: str,
    ) -> None:
        """
        initialize the ratelimit client
        """
        cls._url = f"http://{host}/json"
        cls._domain = domain
        cls._default_ratelimit_name = default_ratelimit_name
        logging.info("ratelimit client: url - %s, domain - %s", cls._url, cls._domain)

    @classmethod
    def ratelimit(cls, ratelimit_name: str) -> bool:
        """
        Given the ratelimit_name, sends a post request to /json to check if being ratelimited.
        If the ratelimit_name is not given, it will use the default ratelimit_name: default.
        Return True if got a 429 status code, otherwise False. Return False on exception like timeout etc.
        """
        if not ratelimit_name:
            # if ratelimit name is not given, we will use the default ratelimit name under
            # python-backend-worker-template domain
            ratelimit_name = cls._default_ratelimit_name
        try:
            headers = {"Content-type": "application/json"}
            query = {
                "domain": cls._domain,
                "descriptors": [{"entries": [{"key": ratelimit_name}]}],
            }
            payload = json.dumps(query)
            http = Session()
            retry_strategy = Retry(
                total=3,
                status_forcelist=[500, 502, 503, 504, 400],
                method_whitelist=["POST"],
                backoff_factor=1,
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            http.mount("http://", adapter)
            http.mount("https://", adapter)
            resp = http.post(cls._url, data=payload, headers=headers, timeout=0.5)
            # stick to 429 return code
            # because we get rate-limited if only we get 429 explicitly from rate limit service
            # other cases, should consider not ratelimited, even if a ratelimit service outage.
            return resp.status_code == 429
        except Exception as err:
            logging.info("failed to reach ratelimit service: %s", err)
            return False

    @classmethod
    def increase_hit(cls, ratelimit_name: str) -> None:
        """
        Used for increase the ratelimit count on alki(https://alki.i.wish.com/) side. This is to improve the
        ratelimiting accuracy. This function is called when a task is about to run.
        """
        if not ratelimit_name:
            # if ratelimit name is not given, we will use the default ratelimit name under
            # python-backend-worker-template domain
            ratelimit_name = cls._default_ratelimit_name
        try:
            headers = {"Content-type": "application/json"}
            query = {
                "domain": cls._domain,
                "descriptors": [{"entries": [{"key": ratelimit_name}]}],
            }
            payload = json.dumps(query)
            post(cls._url, data=payload, headers=headers, timeout=0.5)
        except Exception as err:
            logging.info("failed to reach ratelimit service: %s", err)
            return
