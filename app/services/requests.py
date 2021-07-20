import json
import requests
import aiohttp
import xmltodict
from bs4 import BeautifulSoup
from asyncio import TimeoutError

from services.exceptions import ExternalError


async def get_page_async(link: str, method: str = 'POST', **kwargs) -> BeautifulSoup:
    page = await _make_async_request(link, method, **kwargs)
    return BeautifulSoup(page, 'lxml')


async def get_json_async(link: str, method: str = 'POST', **kwargs) -> json:
    data = await _make_async_request(link, method, **kwargs)
    return json.loads(data)


async def _make_async_request(link: str, method: str = 'POST', **kwargs):
    return await loop(link, method, **kwargs)


async def loop(link: str, method: str = 'POST', **kwargs):
    try:
        async with aiohttp.ClientSession() as session:
            if method == 'POST':
                async with session.post(link, data={**kwargs}) as response:
                    if response.status != 200:
                        raise TimeoutError
                    data = await response.read()
            else:
                async with session.get(link, params={**kwargs}) as response:
                    if response.status != 200:
                        raise TimeoutError
                    data = await response.read()
    except TimeoutError:
        data = await loop(link, method, **kwargs)
    return data


def get_xml(link: str, method: str = 'POST', **kwargs) -> xmltodict:
    response = _make_request(link, method, **kwargs)
    return xmltodict.parse(response.text)


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
        raise ExternalError(f'Request error, code: {response.status_code}, method: {method}\n{link}\n{kwargs}')
    return response
