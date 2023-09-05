# aulaclient.py

import requests


class AulaClient:
    baseUrl = 'https://www.aula.dk/api/v17/'
    defaultLimit = 10

    def __init__(self, cookies):
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
            raise Exception("Cannot request profile, could be due to expired or missing cookies; try to log in.")

        return response_profile['data']['profiles']

    def get_threads(self, custom_params={}):
        default_params = {
            'sortOn': 'date',
            'orderDirection': 'desc',
            'page': 0
        }
        params = self.__merge_params(default_params, custom_params, 'messaging.getThreads')

        response = self.__send_request(params)
        return response['data']

    def get_messages_for_thread(self, thread_id, custom_params={}):
        default_params = {
            'threadId': thread_id,
            'page': 0
        }
        params = self.__merge_params(default_params, custom_params, 'messaging.getMessagesForThread')

        response = self.__send_request(params)
        return response['data']

    def get_posts(self, institution_profile_ids, custom_params={}):
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
        params = self.__merge_params(default_params, custom_params, 'posts.getAllPosts')

        response = self.__send_request(params)
        return response['data']['posts']

    def get_albums(self, institution_profile_ids, custom_params={}):
        default_params = {
            'index': 0,
            'limit': self.defaultLimit,
            'sortOn': 'createdAt',
            'orderDirection': 'desc',
            'filterBy': 'all',
            'filterInstProfileIds[]': institution_profile_ids
        }
        params = self.__merge_params(default_params, custom_params, 'gallery.getAlbums')

        response = self.__send_request(params)
        return response['data']

    def get_pictures(self, institution_profile_ids, album_id, custom_params={}):
        default_params = {
            'albumId': album_id,
            'index': 0,
            'limit': self.defaultLimit,
            'sortOn': 'uploadedAt',
            'orderDirection': 'desc',
            'filterBy': 'all',
            'filterInstProfileIds[]': institution_profile_ids
        }
        params = self.__merge_params(default_params, custom_params, 'gallery.getMedia')

        response = self.__send_request(params)
        return response['data']['results']

    def __send_request(self, params):
        return self.session.get(self.baseUrl, params=params).json()

    def __merge_params(self, default_params, custom_params, method):
        params = default_params | custom_params
        params['method'] = method
        return params
