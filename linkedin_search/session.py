import logging
import random
import time

import requests

logger = logging.getLogger('Session')


class CrawlerSession(requests.Session):
    DEFAULT_REQUEST_TIMEOUT = 60
    LAST_REQUEST_TIME = 0

    def __init__(self, min_delay_time, max_delay_time):
        super(CrawlerSession, self).__init__()
        self.min_delay_time = min_delay_time
        self.max_delay_time = max_delay_time

    def request(self, *args, **kwargs):
        kwargs['timeout'] = kwargs.get('timeout', self.DEFAULT_REQUEST_TIMEOUT)
        self._delay_request_if_needed()
        logger.debug('%s with params %s' % (' '.join(args), kwargs))
        response = super(CrawlerSession, self).request(*args, **kwargs)
        self.LAST_REQUEST_TIME = time.time()
        response.raise_for_status()
        return response

    def _delay_request_if_needed(self):
        delay_time = random.uniform(self.min_delay_time, self.max_delay_time)
        if delay_time > 0 and self.LAST_REQUEST_TIME > 0:
            process_time = time.time() - self.LAST_REQUEST_TIME
            if process_time < delay_time:
                sleep_time = delay_time - process_time
                logger.debug('Delay request for %ss.' % sleep_time)
                time.sleep(sleep_time)
