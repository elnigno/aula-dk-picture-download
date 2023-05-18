import os
import requests
import browser_cookie3
import piexif
import argparse
from rich.progress import track
from rich.console import Console
from datetime import datetime
from aulaclient import AulaClient

class AlbumToDownload:
    def __init__(self, name, type, creationDate, pictures):
        self.name = name
        self.type = type
        self.creationDate = creationDate
        self.pictures = pictures

    def __str__(self):
        return f"Type: {self.type}, CreationDate: {self.creationDate}, Pictures: {len(self.pictures)}, Name: {self.name}"

def parseDate(dateString):
    return datetime.strptime(dateString.split('T')[0], '%Y-%m-%d').date()

def parseDateTime(dateString):
    return datetime.strptime(dateString, '%Y-%m-%dT%H:%M:%S%z')

def cleanTitle(title):
    return title.strip().replace('/', '_').replace(':', '_').replace('?', '_')

def pictureHasTags(picture, tags):
    pictureTags = list(map(lambda t: t['name'], picture['tags']))
    for tag in tags:
        if tag in pictureTags:
            return True
    return False

def addExifCreationTime(imagePath, creationTime):
    isJpeg=imagePath.lower().endswith(('.jpg', '.jpeg'))
    if isJpeg:
        zeroth_ifd = {
            piexif.ImageIFD.DateTime: creationTime.strftime('%Y:%m:%d %H:%M:%S'),
        }
        exif_ifd = {
            piexif.ExifIFD.DateTimeOriginal: creationTime.strftime('%Y:%m:%d %H:%M:%S'),
        }
        exif_dict = { "0th":zeroth_ifd, "Exif":exif_ifd }
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, imagePath)

def getAlbumsToDownloadFromGallery(institutionProfileIds):
    print('Get Albums...')
    additionalParams = { 'limit': 1000 }
    albumsToDownload = []
    albums = client.getAlbums(institutionProfileIds, additionalParams)
    albumsWithId = list(filter(lambda a: a['id'] is not None, albums))
    for album in albumsWithId:
        creationDate = parseDate(album['creationDate'])
        isAlbumCreatedAfterCutoffDate = creationDate >= cutoffDate
        if not isAlbumCreatedAfterCutoffDate:
            continue
        pictures = client.getPictures(institutionProfileIds, album['id'], additionalParams)
        if pictures:
            name = cleanTitle(album['title'])
            pa = AlbumToDownload(name, "Album", creationDate, pictures)
            albumsToDownload.append(pa)
    return albumsToDownload

def getAlbumsToDownloadFromPosts(institutionProfileIds, childrenIds):
    print('Get Posts...')
    additionalParams = { 'limit': 1000 }
    albumsToDownload = []
    getPostsinstitutionProfileIds = institutionProfileIds + childrenIds
    posts = client.getPosts(getPostsinstitutionProfileIds, additionalParams)
    for post in posts:
        creationDate = parseDate(post['publishAt'])
        isPostAfterCutoffDate = creationDate >= cutoffDate
        if not isPostAfterCutoffDate:
            continue
        attachmentsWithMedia = list(filter(lambda a: a['media'] is not None, post['attachments']))
        if attachmentsWithMedia:
            name = cleanTitle(post['title'])
            pa = AlbumToDownload(name, "Post", creationDate, list(map(lambda x: x['media'], attachmentsWithMedia)))
            albumsToDownload.append(pa)
    return albumsToDownload

def getAlbumsToDownloadFromMessages():
    print('Get Threads...')
    threadsPageParam = { 'page': 0 }
    albumsToDownload = []
    threadsResponse = client.getThreads(threadsPageParam)
    threads = threadsResponse['threads']
    while threadsResponse['moreMessagesExist']:
        threadsPageParam['page'] += 1
        threadsResponse = client.getThreads(threadsPageParam)
        threads += threadsResponse['threads']
        lastThreadUpdateTime = parseDateTime(threads[-1]['latestMessage']['sendDateTime'])
        if lastThreadUpdateTime.date() < cutoffDate:
            break;
    for thread in threads:
        threadId = thread['id']
        threadLatestMessageTime = parseDateTime(thread['latestMessage']['sendDateTime'])
        isThreadUpdatedAfterCutoffDate = threadLatestMessageTime.date() >= cutoffDate
        if not isThreadUpdatedAfterCutoffDate:
            break # Following threads won't be updated either, exit
        pageParam = { 'page': 0 }
        messagesResponse = client.getMessagesForThread(threadId, pageParam)
        messages = messagesResponse['messages']
        while messagesResponse['moreMessagesExist']:
            pageParam['page'] += 1
            messagesResponse = client.getMessagesForThread(threadId, pageParam)
            messages += messagesResponse['messages']
        messagesWithAttachments = list(filter(lambda x: x['hasAttachments'], messages))
        if len(messagesWithAttachments) == 0:
            continue
        for messageIndex, message in enumerate(messagesWithAttachments):
            attachmentsWithMedia = list(filter(lambda a: a['media'] is not None, message['attachments']))
            name = f"{cleanTitle(thread['subject'])}_{messageIndex:02d}"
            creationDate = parseDate(thread['startedTime'])
            pictures = list(map(lambda x: x['media'], attachmentsWithMedia))
            if pictures:
                pa = AlbumToDownload(name, "Message", creationDate, pictures)
                albumsToDownload.append(pa)
    return albumsToDownload

def printArguments(cutoffDate, tagsToFind, outputDirectory):
    paramStyle="cyan"
    console.print("Parameters:", style=paramStyle)
    console.print(f"  outputDirectory: {outputDirectory}", style=paramStyle)
    console.print(f"  cutoffDate: {cutoffDate.strftime('%Y-%m-%d')}", style=paramStyle)
    if (tagsToFind):
        console.print(f"  tags: {tagsToFind.__str__()}", style=paramStyle)
    console.print()

def tryAppendAulaCookies(aulaCookies, browserName, cookieCallback):
    try:
        cookies = cookieCallback()
        aulaCookies.append(cookies)
        console.print(f"{browserName} cookies: [green]found[/]")
    except browser_cookie3.BrowserCookieError as error:
        console.print(f"{browserName} cookies: [yellow]not found[/]")

def getAulaCookies():
    aulaCookies = []
    tryAppendAulaCookies(aulaCookies, 'Chrome', lambda: browser_cookie3.chrome(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Chromium', lambda: browser_cookie3.chromium(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Opera', lambda: browser_cookie3.opera(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Opera GX', lambda: browser_cookie3.opera_gx(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Brave', lambda: browser_cookie3.brave(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Edge', lambda: browser_cookie3.edge(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Vivaldi', lambda: browser_cookie3.vivaldi(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Firefox', lambda: browser_cookie3.firefox(domain_name='aula.dk'))
    tryAppendAulaCookies(aulaCookies, 'Safari', lambda: browser_cookie3.safari(domain_name='aula.dk'))
    return aulaCookies

console = Console()

# Parse arguments
parser = argparse.ArgumentParser(description='Download images from aula.dk.')
parser.add_argument('--outputFolder', required=True, default='output', help='Download images in this folder')
parser.add_argument('--cutoffDate', required=True, help='Only download images that have been posted on or after this date (format: "YYYY-MM-DD")')
parser.add_argument('--tags', required=False, nargs='+', help='Only download pictures having at least one of these tags')
args = parser.parse_args()

cutoffDate = datetime.fromisoformat(args.cutoffDate).date()
tagsToFind = args.tags
outputDirectory = args.outputFolder
printArguments(cutoffDate, tagsToFind, outputDirectory)

# Init Aula client
aulaCookies = getAulaCookies()
client = AulaClient(aulaCookies)

try:
    profiles = client.getProfiles()
except Exception as error:
    console.print(error, style="red")
    console.print("Could not get profiles, exiting.", style="red")
    exit()

institutionProfileIds = list(map(lambda p: p['id'], profiles[0]['institutionProfiles']))
childrenIds = list(map(lambda p: p['id'], profiles[0]['children']))

albumsToDownload = []
albumsToDownload += getAlbumsToDownloadFromGallery(institutionProfileIds)
albumsToDownload += getAlbumsToDownloadFromPosts(institutionProfileIds, childrenIds)
albumsToDownload += getAlbumsToDownloadFromMessages()

print('Download Pictures...')
for album in track(albumsToDownload, "Albums to download..."):
    if album.creationDate < cutoffDate:
        continue
    print('>', album, end = ' ', flush = True)
    for picture in album.pictures:
        if not tagsToFind or (picture['tags'] and pictureHasTags(picture, tagsToFind)):
            albumDirectoryName = album.creationDate.strftime('%Y%m%d') + ' ' + album.name
            albumDirectoryPath = os.path.join(outputDirectory, albumDirectoryName)
            file = picture['file']
            imageCreationTime = datetime.strptime(file['created'], '%Y-%m-%dT%H:%M:%S%z')
            imageResponse = requests.get(file['url'])

            if imageCreationTime.date() == album.creationDate:
                imageDirectoryPath = albumDirectoryPath
            else:
                imageDirectoryPath = os.path.join(albumDirectoryPath, imageCreationTime.strftime('%Y%m%d'))

            os.makedirs(imageDirectoryPath, exist_ok=True)
            imagePath = os.path.join(imageDirectoryPath, file['name'])
            open(imagePath, "wb").write(imageResponse.content)
            addExifCreationTime(imagePath, imageCreationTime)
