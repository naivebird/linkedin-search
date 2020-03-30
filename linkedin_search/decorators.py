import logging
from functools import wraps
from itertools import cycle

from requests import RequestException

from linkedin_search.config import account_pool
from linkedin_search.exceptions import LinkedInError

logger = logging.getLogger('Decorators')


def reload_session(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        args[0].load_session()
        return result
    return wrapper


def account_rotation(func):
    """
    Change to a new account if the current one gets block, not reuse.
    """
    def wrapper(*args, **kwargs):
        pool = cycle(account_pool)
        new_account = pool.__next__()
        used_accounts = []
        while new_account not in used_accounts:
            used_accounts.append(new_account)
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                logger.exception(e)
                if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                    new_account = pool.__next__()
                    logger.debug('Session blocked, rotating to a new account: {}'.format(new_account['email']))
                    args[0].email = new_account['email']
                    args[0].password = new_account['password']
                    args[0].log_in()
                    continue
                break
            except Exception as e:
                logger.exception(e)
                break

    return wrapper


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not args[0].is_logged_in:
            raise LinkedInError('Method requires authentication.', 403)
        return func(*args, **kwargs)

    return wrapper
