# aulaclient.py

import requests

class AulaClient:
    baseUrl = 'https://www.aula.dk/api/v15/'
    defaultLimit = 10

    def __init__(self, cookies):
        self.session = requests.Session()
        self.session.cookies = cookies

    def getProfiles(self):
        params = {
            'method': 'profiles.getProfilesByLogin'
        }

        response_profile = self.__sendRequest(params)
        if response_profile['status']['code'] == 448:
            raise Exception("Cannot request profile, could be due to expired or missing cookies; try to log in.")

        return response_profile['data']['profiles']

    def getThreads(self, customParams = {}):
        defaultParams = {
            'sortOn': 'date',
            'orderDirection': 'desc',
            'page': 0
        }
        params = self.__mergeParams(defaultParams, customParams, 'messaging.getThreads')

        response = self.__sendRequest(params)
        return response['data']

    def getMessagesForThread(self, threadId, customParams = {}):
        defaultParams = {
            'threadId': threadId,
            'page': 0
        }
        params = self.__mergeParams(defaultParams, customParams, 'messaging.getMessagesForThread')

        response = self.__sendRequest(params)
        return response['data']

    def getPosts(self, institutionProfileIds, customParams = {}):
        defaultParams = {
            'parent': 'profile',
            'index': 0,
            'limit': self.defaultLimit,
            'isUnread': False,
            'isImportant': False,
            #'creatorPortalRole': '', # guardian, employee
            'ownPost': False,
            'institutionProfileIds[]': institutionProfileIds
        }
        params = self.__mergeParams(defaultParams, customParams, 'posts.getAllPosts')

        response = self.__sendRequest(params)
        return response['data']['posts']

    def getAlbums(self, institutionProfileIds, customParams = {}):
        defaultParams = {
            'index': 0,
            'limit': self.defaultLimit,
            'sortOn': 'createdAt',
            'orderDirection': 'desc',
            'filterBy': 'all',
            'filterInstProfileIds[]': institutionProfileIds
        }
        params = self.__mergeParams(defaultParams, customParams, 'gallery.getAlbums')

        response = self.__sendRequest(params)
        return response['data']

    def getPictures(self, institutionProfileIds, albumId, customParams = {}):
        defaultParams = {
            'albumId': albumId,
            'index': 0,
            'limit': self.defaultLimit,
            'sortOn': 'uploadedAt',
            'orderDirection': 'desc',
            'filterBy': 'all',
            'filterInstProfileIds[]': institutionProfileIds
        }
        params = self.__mergeParams(defaultParams, customParams, 'gallery.getMedia')

        response = self.__sendRequest(params)
        return response['data']['results']

    def __sendRequest(self, params):
        return self.session.get(self.baseUrl, params=params).json()

    def __mergeParams(self, defaultParams, customParams, method):
        params = defaultParams | customParams
        params['method'] = method
        return params
