# linkedin-search

linkedin-search is a Python repository for searching data on LinkedIn.

## Installation

1. Clone the repository:
```bash
git clone git@github.com:naivebird/linkedin-search.git
cd linkedin-search
pip install -r requirements.txt
```
2. Download geckodriver (https://github.com/mozilla/geckodriver/releases) and copy it to your virtualenv/bin folder.
3. Add new accounts to linkedin_search/config.py.

## Usage

```python
from linkedin_search.api import LinkedInSearch

linkedin = LinkedInSearch()
linkedin.log_in()

# Search for jobs:
jobs = linkedin.search_jobs(keywords='software',
                            location='Canada',
                            count=49,
                            start=0,
                            date_posted='Past Month',
                            linkedin_features=['Under 10 Applicants'],
                            experience_level=['Associate', 'Mid-Senior level'],
                            company=['1586', '2646', '3589'],
                            job_function=['eng', 'it'],
                            industry=['4', '6'],
                            job_type=['Full-time'],
                            title=['9', '270'],
                            location_id=['103366113']
                           )
# Search for people:
people = linkedin.search_people(past_company=['1009', '1035'],
                                geo_region=['us', 'in', 'vn', 'gb', 'sg'],
                                industry=['96', '137'],
                                profile_language=['en'],
                                connection_of='ACoAABue12wBU8XczWvO19MP3aI7okMSOymfVEc',
                                first_name='alex',
                                title='CEO')

# Search for companies:
companies = linkedin.search_companies('Apple')

# Search for schools:
schools = linkedin.search_schools('Stanford')

# Search for groups:
groups = linkedin.search_groups('Deep Learning')

# Pagination:
  count = 49
  start = 0
  data = []
  while True:
      results = linkedin.search_jobs(**kwargs)
      data.append(results)
      total = results['data']['paging'].get('total', 0)
      if total <= count + start:
          break
      else:
          start += count
          count = min(count, total - start)
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
