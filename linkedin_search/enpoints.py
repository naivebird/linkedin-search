from urllib.parse import quote

from linkedin_search.exceptions import LinkedInError

SEARCH_URL = 'https://www.linkedin.com/voyager/api/search/blended?{params}'
JOB_SEARCH_URL = 'https://www.linkedin.com/voyager/api/search/hits?{params}'
LOG_IN = 'https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin'


def _snake_to_camel(word):
    words = word.split('_')
    return words[0] + ''.join(x.capitalize() or '_' for x in words[1:])


def _process_value(criterion, value):
    if isinstance(value, list):
        if criterion == 'geo_region':
            value = '|'.join([item + ':0' for item in value])
        else:
            value = '|'.join(value)
    return quote(value)


def build_search_params(filters, **kwargs):
    criteria = ','.join('{criterion}-%3E{value}'.format(criterion=_snake_to_camel(criterion),
                                                        value=_process_value(criterion=criterion,
                                                                             value=value))
                        for criterion, value in filters.items() if value)
    criteria.replace('schoolName', 'school')

    params = dict(
        **{k: v for k, v in kwargs.items() if v is not None},
        filters='List({criteria})'.format(criteria=criteria),
        queryContext='List(spellCorrectionEnabled-%3Etrue,relatedSearchesEnabled-%3Etrue)',
        origin='FACETED_SEARCH',
        q='all'
    )

    return '&'.join('{param}={value}'.format(param=param, value=value) for param, value in params.items())


def build_job_search_params(**kwargs):
    filter_map = {
        'date_posted': {
            'key': 'f_TPR',
            'values': {
                'Past 24 hours': 'r86400',
                'Past Week': 'r604800',
                'Past Month': 'r2592000'
            }
        },
        'linkedin_features': {
            'key': 'f_LF',
            'values': {
                'In Your Network': 'f_JIYN',
                'Under 10 Applicants': 'f_EA',
                'Easy Apply': 'f_AL'
            }
        },
        'company': {
            'key': 'f_C'
        },
        'sort_by': {
            'key': 'sortBy',
            'values': {
                'Most recent': 'DD',
                'Most relevant': 'R'
            }
        },
        'job_type': {
            'key': 'f_JT',
            'values': {
                'Full-time': 'F',
                'Contract': 'C',
                'Part-time': 'P',
                'Internship': 'I',
                'Temporary': 'T',
                'Other': 'O',
                'Volunteer': 'V'
            }
        },
        'experience_level': {
            'key': 'f_E',
            'values': {
                'Internship': '1',
                'Entry level': '2',
                'Associate': '3',
                'Mid-Senior level': '4',
                'Director': '5',
                'Executive': '6'
            }
        },
        'industry': {
            'key': 'f_I'
        },
        'job_function': {
            'key': 'f_F'
        },
        'title': {
            'key': 'f_T'
        },
        'commute': {
            'key': 'f_CF',
            'values': {
                'Remote': 'f_WRA'
            }
        },
        'location_id': {
            'key': 'f_PP'
        }

    }
    params = dict(
        decorationId='com.linkedin.voyager.deco.jserp.WebJobSearchHit-22',
        facetEnabled='false',
        # geoUrn=quote('urn:li:fs_geo:101174742'),
        isRequestPrefetch='true',
        origin='JOB_SEARCH_RESULTS_PAGE',
        q='jserpAll',
        query='search',
        refresh='true',
        topNRequestedFlavors='List(HIDDEN_GEM,IN_NETWORK,SCHOOL_RECRUIT,COMPANY_RECRUIT,SALARY,JOB_SEEKER_QUALIFIED,PREFERRED_COMMUTE)'
    )
    for param, values in kwargs.items():
        filter_key = filter_map.get(param, {}).get('key')
        if filter_key:
            if isinstance(values, list):
                filter_values = ','.join(
                    [filter_map.get(param, {}).get('values', {}).get(item, item) for item in values])
            elif isinstance(values, str):
                filter_values = filter_map.get(param, {}).get('values', {}).get(values)
            else:
                raise LinkedInError('Filter value must be of type list or string')
            if not (filter_values or values):
                raise LinkedInError('Values missing for param {}'.format(param))
            params[filter_key] = 'List({})'.format(filter_values or values)
        elif param in ['location', 'keywords', 'count', 'start']:
            if values:
                params[param] = quote(str(values))
    filters = '&'.join('{param}={value}'.format(param=param, value=value) for param, value in params.items())
    return filters
