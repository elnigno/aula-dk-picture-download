import argparse
import os
import sys
from datetime import datetime

import requests
import piexif
from rich.progress import track
from rich.console import Console

from aulaclient import AulaClient


class Arguments:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Download images from aula.dk.')
        parser.add_argument(
            '--outputFolder',
            required=True,
            default='output',
            help='Download images in this folder')
        parser.add_argument(
            '--cutoffDate',
            required=True,
            help='Download images posted on or after this date (format: "YYYY-MM-DD")')
        parser.add_argument(
            '--tags',
            required=False,
            nargs='+',
            help='Download images having at least one of these tags')
        parser.add_argument(
            '--apiVersion',
            required=False,
            default=20,
            help='Aula API version')
        parser.add_argument(
            '--cookie',
            required=False,
            default='',
            help='Aula Cookie')
        args = parser.parse_args()

        self.cutoff_date = datetime.fromisoformat(args.cutoffDate).date()
        self.tags_to_find = args.tags
        self.output_directory = args.outputFolder
        self.api_version = args.apiVersion
        self.session_cookie = args.cookie

    def print_arguments(self):
        param_style = "cyan"
        console.print("Parameters:", style=param_style)
        console.print(f"  outputDirectory: {self.output_directory}", style=param_style)
        console.print(f"  cutoffDate: {self.cutoff_date.strftime('%Y-%m-%d')}", style=param_style)
        if self.tags_to_find:
            console.print(f"  tags: {self.tags_to_find}", style=param_style)
        if self.api_version:
            console.print(f"  apiVersion: {self.api_version}", style=param_style)
        if self.session_cookie:
            console.print(f"  cookie: {self.session_cookie}", style=param_style)
        console.print()


class AlbumToDownload:
    def __init__(self, name, album_type, creation_date, pictures):
        self.name = name
        self.album_type = album_type
        self.creation_date = creation_date
        self.pictures = pictures

    def __str__(self):
        return f"Type: {self.album_type: <8}, CreationDate: {self.creation_date}, \
Pictures: {len(self.pictures): <3}, Name: {self.name}"


def parse_date(date_string):
    return datetime.strptime(date_string.split('T')[0], '%Y-%m-%d').date()


def parse_datetime(date_string):
    return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')


def clean_title(title):
    return title.strip().replace('/', '_').replace(':', '_').replace('?', '_')


def picture_has_tags(picture, tags):
    if not picture['tags']:
        return False

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


def get_albums_from_gallery(client, institution_profile_ids, cutoff_date):
    console.print('Get Albums...')
    additional_params = {'limit': 1000}
    albums_to_download = []
    albums = client.get_albums(institution_profile_ids, additional_params)
    albums_with_id = filter_list_with_property(albums, 'id')
    for album in albums_with_id:
        creation_date = parse_date(album['creationDate'])
        is_album_created_after_cutoff_date = creation_date >= cutoff_date
        if not is_album_created_after_cutoff_date:
            continue
        pictures = client.get_pictures(institution_profile_ids, album['id'], additional_params)
        if pictures:
            name = clean_title(album['title'])
            album = AlbumToDownload(name, "Album", creation_date, pictures)
            albums_to_download.append(album)
    return albums_to_download


def filter_list_with_property(list_to_filter, property_name: str):
    return list(filter(lambda a: a[property_name] is not None, list_to_filter))


def get_albums_from_posts(client, institution_profile_ids, children_ids, cutoff_date):
    console.print('Get Posts...')
    additional_params = {'limit': 1000}
    albums_to_download = []
    get_posts_institution_profile_ids = institution_profile_ids + children_ids
    posts = client.get_posts(get_posts_institution_profile_ids, additional_params)
    for post in posts:
        creation_date = parse_date(post['publishAt'])
        is_post_after_cutoff_date = creation_date >= cutoff_date
        if not is_post_after_cutoff_date:
            continue
        attachments_with_media = filter_list_with_property(post['attachments'], 'media')
        if attachments_with_media:
            name = clean_title(post['title'])
            pictures = list(map(lambda x: x['media'], attachments_with_media))
            if pictures:
                album = AlbumToDownload(name, "Post", creation_date, pictures)
                albums_to_download.append(album)
    return albums_to_download


def get_albums_from_messages(client, cutoff_date):
    console.print('Get Threads...')
    albums_to_download = []
    threads = get_threads(client, cutoff_date)
    for thread in threads:
        thread_id = thread['id']
        thread_latest_message_time = parse_datetime(thread['latestMessage']['sendDateTime'])
        is_thread_updated_after_cutoff_date = thread_latest_message_time.date() >= cutoff_date
        if not is_thread_updated_after_cutoff_date:
            break  # Following threads won't be updated either, exit
        messages_with_attachments = get_messages_with_attachments_in_thread(client, thread_id)
        for message_index, message in enumerate(messages_with_attachments):
            attachments_with_media = filter_list_with_property(message['attachments'], 'media')
            name = f"{clean_title(thread['subject'])}_{message_index:02d}"
            creation_date = parse_date(thread['startedTime'])
            pictures = list(map(lambda x: x['media'], attachments_with_media))
            if pictures:
                album = AlbumToDownload(name, "Message", creation_date, pictures)
                albums_to_download.append(album)
    return albums_to_download


def get_threads(client, cutoff_date):
    threads_page_param = {'page': 0}
    threads_response = client.get_threads(threads_page_param)
    threads = threads_response['threads']
    while threads_response['moreMessagesExist']:
        threads_page_param['page'] += 1
        threads_response = client.get_threads(threads_page_param)
        threads += threads_response['threads']
        last_thread_update_time = parse_datetime(threads[-1]['latestMessage']['sendDateTime'])
        if last_thread_update_time.date() < cutoff_date:
            break
    return threads


def get_messages_with_attachments_in_thread(client, thread_id):
    page_param = {'page': 0}
    messages_response = client.get_messages_for_thread(thread_id, page_param)
    messages = messages_response['messages']
    while messages_response['moreMessagesExist']:
        page_param['page'] += 1
        messages_response = client.get_messages_for_thread(thread_id, page_param)
        messages += messages_response['messages']
    messages_with_attachments = list(filter(lambda x: x['hasAttachments'], messages))
    return messages_with_attachments


def get_image_data(album: AlbumToDownload, output_directory, file_data):
    album_directory_name = album.creation_date.strftime('%Y%m%d') + ' ' + album.name
    album_directory_path = os.path.join(output_directory, album_directory_name)
    image_creation_time = datetime.strptime(file_data['created'], '%Y-%m-%dT%H:%M:%S%z')
    image_response = requests.get(file_data['url'], timeout=30)

    if image_creation_time.date() == album.creation_date:
        image_directory_path = album_directory_path
    else:
        folder_name = image_creation_time.strftime('%Y%m%d')
        image_directory_path = os.path.join(album_directory_path, folder_name)

    return {
        "image_directory_path": image_directory_path,
        "image_content": image_response.content,
        "image_creation_time": image_creation_time
    }


def main():
    args = Arguments()
    args.print_arguments()
    client = AulaClient(args.api_version, args.session_cookie)

    try:
        profiles = client.get_profiles()
    except PermissionError as error:
        console.print(error, style="red")
        console.print("Could not get profiles, exiting.", style="red")
        sys.exit()

    institution_ids = list(map(lambda p: p['id'], profiles[0]['institutionProfiles']))
    children_ids = list(map(lambda p: p['id'], profiles[0]['children']))

    albums_to_download = []
    albums_to_download += get_albums_from_gallery(client, institution_ids, args.cutoff_date)
    albums_to_download += get_albums_from_posts(client, institution_ids, children_ids, args.cutoff_date)
    albums_to_download += get_albums_from_messages(client, args.cutoff_date)

    console.print('Download Pictures...')
    for album in track(albums_to_download, "Albums to download..."):
        if album.creation_date < args.cutoff_date:
            continue
        print('>', album, end=' ', flush=True)
        for picture in album.pictures:
            tags_are_found_or_ignored = (not args.tags_to_find
                                         or picture_has_tags(picture, args.tags_to_find))
            if tags_are_found_or_ignored:
                file_data = picture['file']
                image_data = get_image_data(album, args.output_directory, file_data)

                os.makedirs(image_data["image_directory_path"], exist_ok=True)
                image_path = os.path.join(image_data["image_directory_path"], file_data['name'])
                with open(image_path, "wb") as image_file:
                    image_file.write(image_data["image_content"])
                add_exif_creation_time(image_path, image_data["image_creation_time"])


if __name__ == '__main__':
    console = Console()
    main()
