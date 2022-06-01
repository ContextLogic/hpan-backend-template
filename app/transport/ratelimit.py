from requests import post, Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import logging
from app.config.config import CONF

logger = logging.getLogger(__name__)


class RatelimitClient:
    def __init__(self, host="ratelimit-dev.service.consul:8080", domain="python-backend-worker-template"):
        self._url = 'http://{}/json'.format(host)
        self._domain = domain

    def ratelimit(self, key):
        if not self._domain:
            # if domain is not defined, i.e. we do not enable ratelimit for this service
            # should not be ratelimited
            return False

        try:
            headers = {'Content-type': 'application/json'}
            query = {
                "domain": self._domain,
                "descriptors": [
                    {
                        "entries": [
                            {
                                "key": key
                            }
                        ]
                    }
                ]
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
            resp = http.post(self._url, data=payload, headers=headers, timeout=0.5)

            # stick to 429 return code
            # because we get rate-limited if only we get 429 explicitly from rate limit service
            # other cases, should consider not ratelimited, even if a ratelimit service outage.
            return resp.status_code == 429
        except Exception:
            return False


Ratelimiter = RatelimitClient(domain=CONF.worker.name, host=CONF.worker.ratelimit_host)
