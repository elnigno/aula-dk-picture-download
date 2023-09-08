# aulaclient.py

import browser_cookie3
from rich.console import Console
import requests


class CookieFetcher:
    def try_append_aula_cookies(self, aula_cookies, browser_name):
        result = ''
        try:
            cookies = self.get_cookies_from_browser(browser_name)
            if cookies:
                aula_cookies.append(cookies)
                result = 'found'
            else:
                result = 'notFound'
        except browser_cookie3.BrowserCookieError:
            result = 'notFound'
        except Exception:
            result = 'error'

        if result == 'notFound':
            message = "[yellow]not found[/]"
        elif result == 'found':
            message = "[green]found[/]"
        elif result == 'error':
            message = "[red]error occured[/]"
        else:
            message = "[red]unknown error occured[/]"

        console = Console()
        console.print(f"{browser_name} cookies: {message}")

    def get_cookies_from_browser(self, browser_name):
        domain = 'aula.dk'
        if browser_name == 'Chrome':
            cookies = browser_cookie3.chrome(domain_name=domain)
        elif browser_name == 'Chromium':
            cookies = browser_cookie3.chromium(domain_name=domain)
        elif browser_name == 'Opera':
            cookies = browser_cookie3.opera(domain_name=domain)
        elif browser_name == 'Opera GX':
            cookies = browser_cookie3.opera_gx(domain_name=domain)
        elif browser_name == 'Brave':
            cookies = browser_cookie3.brave(domain_name=domain)
        elif browser_name == 'Edge':
            cookies = browser_cookie3.edge(domain_name=domain)
        elif browser_name == 'Vivaldi':
            cookies = browser_cookie3.vivaldi(domain_name=domain)
        elif browser_name == 'Firefox':
            cookies = browser_cookie3.firefox(domain_name=domain)
        elif browser_name == 'Safari':
            cookies = browser_cookie3.safari(domain_name=domain)
        else:
            raise NotImplementedError("Browser not supported")
        return cookies

    def get_aula_cookies(self):
        aula_cookies = []
        self.try_append_aula_cookies(aula_cookies, 'Chrome')
        self.try_append_aula_cookies(aula_cookies, 'Chromium')
        self.try_append_aula_cookies(aula_cookies, 'Opera')
        self.try_append_aula_cookies(aula_cookies, 'Opera GX')
        self.try_append_aula_cookies(aula_cookies, 'Brave')
        self.try_append_aula_cookies(aula_cookies, 'Edge')
        self.try_append_aula_cookies(aula_cookies, 'Vivaldi')
        self.try_append_aula_cookies(aula_cookies, 'Firefox')
        self.try_append_aula_cookies(aula_cookies, 'Safari')
        return aula_cookies


class AulaClient:
    baseUrl = 'https://www.aula.dk/api/v17/'
    defaultLimit = 10

    def __init__(self):
        cookie_fetcher = CookieFetcher()
        cookies = cookie_fetcher.get_aula_cookies()
        self.session = requests.Session()
        self.all_cookies = cookies

    def get_profiles(self):
        params = {
            'method': 'profiles.getProfilesByLogin'
        }

        for cookies in self.all_cookies:
            self.session.cookies = cookies
            response_profile = self.__send_request(params)
            if response_profile['status']['code'] != 448:
                break

        if response_profile['status']['code'] == 448:
            message = "Cannot request profile, cookies may be expired or missing; try to log in."
            raise PermissionError(message)

        return response_profile['data']['profiles']

    def get_threads(self, custom_params=None):
        if custom_params is None:
            custom_params = {}
        default_params = {
            'sortOn': 'date',
            'orderDirection': 'desc',
            'page': 0
        }
        params = self.__merge_params(
            default_params,
            custom_params,
            'messaging.getThreads')

        response = self.__send_request(params)
        return response['data']

    def get_messages_for_thread(self, thread_id, custom_params=None):
        if custom_params is None:
            custom_params = {}
        default_params = {
            'threadId': thread_id,
            'page': 0
        }
        params = self.__merge_params(
            default_params,
            custom_params,
            'messaging.getMessagesForThread')

        response = self.__send_request(params)
        return response['data']

    def get_posts(self, institution_profile_ids, custom_params=None):
        if custom_params is None:
            custom_params = {}
        default_params = {
            'parent': 'profile',
            'index': 0,
            'limit': self.defaultLimit,
            'isUnread': False,
            'isImportant': False,
            # 'creatorPortalRole': '', # guardian, employee
            'ownPost': False,
            'institutionProfileIds[]': institution_profile_ids
        }
        params = self.__merge_params(
            default_params,
            custom_params,
            'posts.getAllPosts')

        response = self.__send_request(params)
        return response['data']['posts']

    def get_albums(self, institution_profile_ids, custom_params=None):
        if custom_params is None:
            custom_params = {}
        default_params = {
            'index': 0,
            'limit': self.defaultLimit,
            'sortOn': 'createdAt',
            'orderDirection': 'desc',
            'filterBy': 'all',
            'filterInstProfileIds[]': institution_profile_ids
        }
        params = self.__merge_params(
            default_params,
            custom_params,
            'gallery.getAlbums')

        response = self.__send_request(params)
        return response['data']

    def get_pictures(self, institution_profile_ids, album_id, custom_params=None):
        if custom_params is None:
            custom_params = {}
        default_params = {
            'albumId': album_id,
            'index': 0,
            'limit': self.defaultLimit,
            'sortOn': 'uploadedAt',
            'orderDirection': 'desc',
            'filterBy': 'all',
            'filterInstProfileIds[]': institution_profile_ids
        }
        params = self.__merge_params(
            default_params,
            custom_params,
            'gallery.getMedia')

        response = self.__send_request(params)
        return response['data']['results']

    def __send_request(self, params):
        return self.session.get(self.baseUrl, params=params).json()

    def __merge_params(self, default_params, custom_params, method):
        params = default_params | custom_params
        params['method'] = method
        return params
