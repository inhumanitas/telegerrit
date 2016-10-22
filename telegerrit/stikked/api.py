# coding: utf-8
import json
import logging

from urlparse import urljoin
from requests import request

from telegerrit.settings import stikked_api_url

logger = logging.getLogger(__name__)

HTTP_OK = 200


class StikkedException(Exception):
    pass


class Stikked(object):
    base_url = stikked_api_url
    _langs_url = 'api/langs'
    _create_url = 'api/create'

    __langs = None

    def make_req(self, url, method='GET', parse=True, **kwargs):
        response = None
        full_path = urljoin(self.base_url, url)
        try:
            response = request(method=method, url=full_path, **kwargs)
        except Exception as e:
            logger.error(e)
            raise StikkedException(e.message)

        data = {}
        if parse:
            if response and response.status_code == HTTP_OK:
                try:
                    data = json.loads(response.content)
                except ValueError:
                    pass
        elif response:
            data = response.content

        return data

    @property
    def langs(self):
        """Alternative syntax highlighting."""
        if self.__langs:
            return self.__langs

        data = self.make_req(self._langs_url)

        self.__langs = data.keys()
        return self.__langs

    def create_paste(self, text, title='New paste', name='New paste',
                     lang='python', raw=False):
        if lang not in stikked.langs:
            raise StikkedException('Wrong lang param')

        if not text:
            raise StikkedException('Text param is empty. Not allowed')
        data = {
            'text': text,
            'title': title,
            'name': name,
            'lang': lang,
        }

        url = self.make_req(
            self._create_url, method='POST', parse=False, data=data)

        if raw:
            url = url.replace('/view/', '/view/raw/')
        return url


stikked = Stikked()

