import os
import requests
import piexif
import argparse
from rich.progress import track
from rich.console import Console
from datetime import datetime
from aulaclient import AulaClient
from cookiefetcher import CookieFetcher


class AlbumToDownload:
    def __init__(self, name, album_type, creation_date, pictures):
        self.name = name
        self.album_type = album_type
        self.creationDate = creation_date
        self.pictures = pictures

    def __str__(self):
        return f"Type: {self.album_type}, CreationDate: {self.creationDate}, Pictures: {len(self.pictures)}, Name: {self.name}"


def parse_date(date_string):
    return datetime.strptime(date_string.split('T')[0], '%Y-%m-%d').date()


def parse_datetime(date_string):
    return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')


def clean_title(title):
    return title.strip().replace('/', '_').replace(':', '_').replace('?', '_')


def picture_has_tags(picture, tags):
    picture_tags = list(map(lambda t: t['name'], picture['tags']))
    for tag in tags:
        if tag in picture_tags:
            return True
    return False


def add_exif_creation_time(image_path, creation_time):
    is_jpeg = image_path.lower().endswith(('.jpg', '.jpeg'))
    if is_jpeg:
        zeroth_ifd = {
            piexif.ImageIFD.DateTime: creation_time.strftime('%Y:%m:%d %H:%M:%S'),
        }
        exif_ifd = {
            piexif.ExifIFD.DateTimeOriginal: creation_time.strftime('%Y:%m:%d %H:%M:%S'),
        }
        exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd}
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, image_path)


def get_albums_to_download_from_gallery(institution_profile_ids):
    print('Get Albums...')
    additional_params = {'limit': 1000}
    albums_to_download = []
    albums = client.get_albums(institution_profile_ids, additional_params)
    albums_with_id = list(filter(lambda a: a['id'] is not None, albums))
    for album in albums_with_id:
        creation_date = parse_date(album['creationDate'])
        is_album_created_after_cutoff_date = creation_date >= cutoffDate
        if not is_album_created_after_cutoff_date:
            continue
        pictures = client.get_pictures(institution_profile_ids, album['id'], additional_params)
        if pictures:
            name = clean_title(album['title'])
            pa = AlbumToDownload(name, "Album", creation_date, pictures)
            albums_to_download.append(pa)
    return albums_to_download


def get_albums_to_download_from_posts(institution_profile_ids, children_ids):
    print('Get Posts...')
    additional_params = {'limit': 1000}
    albums_to_download = []
    get_posts_institution_profile_ids = institution_profile_ids + children_ids
    posts = client.get_posts(get_posts_institution_profile_ids, additional_params)
    for post in posts:
        creation_date = parse_date(post['publishAt'])
        is_post_after_cutoff_date = creation_date >= cutoffDate
        if not is_post_after_cutoff_date:
            continue
        attachments_with_media = list(filter(lambda a: a['media'] is not None, post['attachments']))
        if attachments_with_media:
            name = clean_title(post['title'])
            pa = AlbumToDownload(name, "Post", creation_date, list(map(lambda x: x['media'], attachments_with_media)))
            albums_to_download.append(pa)
    return albums_to_download


def get_albums_to_download_from_messages():
    print('Get Threads...')
    threads_page_param = {'page': 0}
    albums_to_download = []
    threads_response = client.get_threads(threads_page_param)
    threads = threads_response['threads']
    while threads_response['moreMessagesExist']:
        threads_page_param['page'] += 1
        threads_response = client.get_threads(threads_page_param)
        threads += threads_response['threads']
        last_thread_update_time = parse_datetime(threads[-1]['latestMessage']['sendDateTime'])
        if last_thread_update_time.date() < cutoffDate:
            break
    for thread in threads:
        thread_id = thread['id']
        thread_latest_message_time = parse_datetime(thread['latestMessage']['sendDateTime'])
        is_thread_updated_after_cutoff_date = thread_latest_message_time.date() >= cutoffDate
        if not is_thread_updated_after_cutoff_date:
            break  # Following threads won't be updated either, exit
        page_param = {'page': 0}
        messages_response = client.get_messages_for_thread(thread_id, page_param)
        messages = messages_response['messages']
        while messages_response['moreMessagesExist']:
            page_param['page'] += 1
            messages_response = client.get_messages_for_thread(thread_id, page_param)
            messages += messages_response['messages']
        messages_with_attachments = list(filter(lambda x: x['hasAttachments'], messages))
        if len(messages_with_attachments) == 0:
            continue
        for message_index, message in enumerate(messages_with_attachments):
            attachments_with_media = list(filter(lambda a: a['media'] is not None, message['attachments']))
            name = f"{clean_title(thread['subject'])}_{message_index:02d}"
            creation_date = parse_date(thread['startedTime'])
            pictures = list(map(lambda x: x['media'], attachments_with_media))
            if pictures:
                pa = AlbumToDownload(name, "Message", creation_date, pictures)
                albums_to_download.append(pa)
    return albums_to_download


def print_arguments(cutoff_ate, tags_to_find, output_directory):
    param_style = "cyan"
    console.print("Parameters:", style=param_style)
    console.print(f"  outputDirectory: {output_directory}", style=param_style)
    console.print(f"  cutoffDate: {cutoff_ate.strftime('%Y-%m-%d')}", style=param_style)
    if tags_to_find:
        console.print(f"  tags: {tags_to_find.__str__()}", style=param_style)
    console.print()


console = Console()

# Parse arguments
parser = argparse.ArgumentParser(description='Download images from aula.dk.')
parser.add_argument('--outputFolder', required=True, default='output', help='Download images in this folder')
parser.add_argument('--cutoffDate', required=True,
                    help='Only download images that have been posted on or after this date (format: "YYYY-MM-DD")')
parser.add_argument('--tags', required=False, nargs='+',
                    help='Only download pictures having at least one of these tags')
args = parser.parse_args()

cutoffDate = datetime.fromisoformat(args.cutoffDate).date()
tagsToFind = args.tags
outputDirectory = args.outputFolder
print_arguments(cutoffDate, tagsToFind, outputDirectory)

# Init Aula client
cookieFetcher = CookieFetcher()
aulaCookies = cookieFetcher.get_aula_cookies()
client = AulaClient(aulaCookies)

try:
    profiles = client.get_profiles()
except Exception as error:
    console.print(error, style="red")
    console.print("Could not get profiles, exiting.", style="red")
    exit()

institution_profile_ids = list(map(lambda p: p['id'], profiles[0]['institutionProfiles']))
childrenIds = list(map(lambda p: p['id'], profiles[0]['children']))

albumsToDownload = []
albumsToDownload += get_albums_to_download_from_gallery(institution_profile_ids)
albumsToDownload += get_albums_to_download_from_posts(institution_profile_ids, childrenIds)
albumsToDownload += get_albums_to_download_from_messages()

print('Download Pictures...')
for album in track(albumsToDownload, "Albums to download..."):
    if album.creationDate < cutoffDate:
        continue
    print('>', album, end=' ', flush=True)
    for picture in album.pictures:
        if not tagsToFind or (picture['tags'] and picture_has_tags(picture, tagsToFind)):
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
            add_exif_creation_time(imagePath, imageCreationTime)
