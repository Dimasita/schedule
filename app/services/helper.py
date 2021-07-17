import json
import requests
import aiohttp
from bs4 import BeautifulSoup

from services.exceptions import ExternalError


async def get_page_async(link: str, method: str = 'POST', **kwargs) -> BeautifulSoup:
    page = await _make_async_request(link, method, **kwargs)
    return BeautifulSoup(page, 'lxml')


async def get_json_async(link: str, method: str = 'POST', **kwargs) -> json:
    data = await _make_async_request(link, method, **kwargs)
    return json.loads(data)


async def _make_async_request(link: str, method: str = 'POST', **kwargs):
    async with aiohttp.ClientSession() as session:
        if method == 'POST':
            async with session.post(link, params={**kwargs}) as response:
                status = response.status
                data = await response.read()
        else:
            async with session.get(link, params={**kwargs}) as response:
                status = response.status
                data = await response.read()
    if status != 200:
        raise ExternalError(f'Description {status}\n{link}')
    return data


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
        raise ExternalError(f'Description {response.status_code}\n{link}')
    return response

