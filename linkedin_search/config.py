from linkedin_search.exceptions import LinkedInError

# add accounts dedicated to crawling here
account_pool = [
    {
        'email': 'your_email@gmail.com',
        'password': 'your_password'
    }

]


def load_config():
    if account_pool and account_pool[0]['email'] != 'your_email@gmail.com':
        return account_pool[0]['email'], account_pool[0]['password']
    else:
        raise LinkedInError('Credentials not found, add new accounts the account pool.')
