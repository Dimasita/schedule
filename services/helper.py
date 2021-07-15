import json
import requests
from bs4 import BeautifulSoup

from services.exceptions import ExternalError


def get_page(link: str, method: str = 'POST', **kwargs) -> BeautifulSoup:
    response = _make_request(link, method, **kwargs)
    return BeautifulSoup(response.text, 'lxml')


def get_json(link: str, method: str = 'POST', **kwargs) -> json:
    response = _make_request(link, method, **kwargs)
    return response.json()


def _make_request(link: str, method: str = 'POST', **kwargs) -> requests:
    if method == 'POST':
        response = requests.post(link, data={**kwargs})
    else:
        response = requests.get(link, params={**kwargs})
    if response.status_code != 200:
        raise ExternalError('Description')
    return response
