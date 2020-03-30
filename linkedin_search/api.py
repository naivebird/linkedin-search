import contextlib
import logging
import pickle
import time
from os.path import join, dirname

import requests
import selenium.webdriver as webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_search.config import load_config
from linkedin_search.decorators import login_required, account_rotation
from linkedin_search.enpoints import LOG_IN, JOB_SEARCH_URL, SEARCH_URL, build_job_search_params, build_search_params
from linkedin_search.session import CrawlerSession

logger = logging.getLogger('LinkedInSearch')


class LinkedInSearch(object):
    HEADERS = {
        'accept': 'application/vnd.linkedin.normalized+json+2.1',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 '
                      'Safari/537.36',
        'x-li-lang': 'en_US',
        'x-li-page-instance': 'urn:li:page:d_flagship3_search_srp_people;E+2l1Q/GQVGR5QPTNbcHmA==',
        'x-li-track': '{"clientVersion":"1.5.*","osName":"web","timezoneOffset":7,"deviceFormFactor":"DESKTOP",'
                      '"mpName":"voyager-web"}',
        'x-restli-protocol-version': '2.0.0',
    }

    def __init__(self, min_delay_time=1, max_delay_time=3, email=None, password=None):
        self._session = CrawlerSession(min_delay_time=min_delay_time,
                                       max_delay_time=max_delay_time)
        self._session.headers.update(self.HEADERS)
        self.email, self.password = (email, password) or load_config()
        self.session_file = join(dirname(__file__), 'sessions/{email}'.format(email=self.email))
        self.is_logged_in = False

    def log_in(self):
        try:
            self._load_session()
            self.is_logged_in = True
            logger.debug('Loaded session from local file.')
        except IOError:
            logger.debug('Session file not found, creating a new session.')
            self._create_session(email=self.email, password=self.password)
            self._load_session()
            self.is_logged_in = True

    def _load_session(self):
        with open(self.session_file, 'rb') as f:
            cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            self._session.cookies = cookies
            csrf_token = self._session.cookies.get('JSESSIONID').replace('\"', "")
            self._session.headers.update(
                {
                    'csrf-token': csrf_token
                }
            )

            logger.debug("Loaded cookies from session file")

    @staticmethod
    def _element_exists(driver, element_id):
        try:
            driver.find_element_by_id(element_id)
            return True
        except NoSuchElementException:
            return False

    def _create_session(self, email, password, timeout=300):
        options = Options()
        options.headless = False
        with contextlib.closing(webdriver.Firefox(options=options)) as driver:

            driver.get(LOG_IN)
            WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.ID, 'username')))

            input_element = driver.find_element_by_id('username')
            input_element.send_keys(email)
            input_element.submit()
            logger.debug("Filled in email address and submitted.")

            time.sleep(3)
            input_element = driver.find_element_by_id('password')
            input_element.send_keys(password)
            input_element.submit()
            logger.debug("Filled in password and submitted.")
            time.sleep(3)

            if self._element_exists(driver=driver,
                                    element_id='input__email_verification_pin'):
                logger.info('PIN required to log in, get it from your email and type it on the login browser.')
            WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'nav-search-bar')))
            collected = dict()
            for cookie in driver.get_cookies():
                collected[str(cookie['name'])] = str(cookie['value'])
            with open(self.session_file, 'wb') as f:
                pickle.dump(collected, f, protocol=2)
        logger.debug("Session has been seeded, LinkedIn crawler is ready for use.")

    def new_session(self):
        self._create_session(email=self.email, password=self.password)

    @login_required
    @account_rotation
    def search_jobs(self, keywords=None, location=None, sort_by='Most relevant', count=10, start=0, **kwargs):
        """
        Search for jobs on LinkedIn
        Args:
            keywords (str): keywords used in the search bar.
            location (str): location text that found in the location box next to the search bar.
            sort_by (str): accepted values: "Most recent", "Most relevant" (default).
            count (int): number of results per page, maximum 49. Use this with `start` param for pagination.
            start (int): similar to an offset value, used to indicate the number of results to skip in pagination. The
            default value is 0, it should less than totalResultCount - count.
        Keyword Args:
            date_posted (str): used to limit the result to an posted date interval. Accepted values: "Past 24 hours",
            "Past Week", "Past Month".
            linkedin_features (list): used to filter results by LinkedIn features. Accepted values: "In Your Network",
            "Under 10 Applicants", "Easy Apply".
            company (list): used to filter jobs posted by certain employers using company ids found on LinkedIn company
            page urls.
            job_type (str): used to filter results by types of job. Accepted values: "Full-time", "Contract",
            "Part-time", "Internship", "Temporary", "Volunteer", "Other".
            experience_level (list): used to filter results by experience level. Accepted values: "Internship",
            "Entry level", "Associate", "Mid-Senior level", "Director", "Executive".
            industry (list): a list of industry ids found on LinkedIn.
            job_function (list): a list of job function ids found on LinkedIn.
            title (list): a list of title ids found on LinkedIn.
            commute (str): this only have 1 accepted value: "Remote".
            location_id (list): a list of location ids found on LinkedIn.

        Returns: result data in json format.

        """
        params = build_job_search_params(keywords=keywords,
                                         count=count,
                                         start=start,
                                         location=location,
                                         sort_by=sort_by,
                                         **kwargs)
        return self._session.get(JOB_SEARCH_URL.format(params=params)).json()

    @login_required
    @account_rotation
    def _search(self, keywords, count, start, **kwargs):
        params = build_search_params(filters=kwargs,
                                     keywords=keywords,
                                     count=count,
                                     start=start)

        return self._session.get(SEARCH_URL.format(params=params)).json()

    def search_people(self, keywords=None, count=10, start=0, **kwargs):
        """

        Args:
            keywords(str): keywords used in the search bar.
            count (int): number of results per page, maximum 49. Use this with `start` param for pagination.
            start (int): similar to an offset value, used to indicate the number of results to skip in pagination. The
            default value is 0, it should less than totalResultCount - count.

        Keyword Args:
            network (list): a list of network codes. Accepted values: "F" (first), "S" (second), "T" (third).
            connection_of (str): a string code representing a LinkedIn member used to filter people having connection
             with this person.
            geo_region (list): a list of  two-letter country codes.
            current_company (list): a list of company ids found on LinkedIn company page urls.
            past_company (list): a list of company ids found on LinkedIn company page urls.
            industry (list): a list of industry ids found on LinkedIn.
            profile_language (list): a list of language codes. Accepted values: "en" (English), "de" (German),
            "es" (Spanish), "fr" (French), "zh" (Chinese).
            school (list): a list of school ids found on LinkedIn.
            contact_interest (list): a list of contract interests. Accepted values:
            "proBono" (Probono consulting and volunteering), "boardMember" (Joining a nonprofit board).
            first_name (str): used to filter first names containing this text.
            last_name (str): used to filter last names containing this text.
            title (str): used to filter titles containing this text.
            company (str): used to filter companies containing this text.
            school_name (str): used to filter school names containing this text.

        Returns: result data in json format.

        """

        return self._search(keywords=keywords,
                            result_type='PEOPLE',
                            count=count,
                            start=start,
                            **kwargs)

    def search_companies(self, keywords=None, count=10, start=0):
        """

        Args: see args in function `search_people`

        Returns: result data in json format.

        """
        return self._search(keywords=keywords,
                            result_type='COMPANIES',
                            count=count,
                            start=start)

    def search_schools(self, keywords=None, count=10, start=0):
        """

        Args: see args in function `search_people`

        Returns: result data in json format.

        """
        return self._search(keywords=keywords,
                            result_type='SCHOOLS',
                            count=count,
                            start=start)

    def search_groups(self, keywords=None, count=10, start=0):
        """

        Args: see args in function `search_people`

        Returns: result data in json format.

        """
        return self._search(keywords=keywords,
                            result_type='GROUPS',
                            count=count,
                            start=start)
