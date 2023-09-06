import argparse
import os
import sys
from datetime import datetime

import requests
import piexif
from rich.progress import track
from rich.console import Console

from aulaclient import AulaClient


class AlbumToDownload:
    def __init__(self, name, album_type, creation_date, pictures):
        self.name = name
        self.album_type = album_type
        self.creation_date = creation_date
        self.pictures = pictures

    def __str__(self):
        return f"Type: {self.album_type}, CreationDate: {self.creation_date}, Pictures: {len(self.pictures)}, Name: {self.name}"


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


def get_albums_to_download_from_gallery(institution_profile_ids, cutoff_date):
    print('Get Albums...')
    additional_params = {'limit': 1000}
    albums_to_download = []
    albums = client.get_albums(institution_profile_ids, additional_params)
    albums_with_id = list(filter(lambda a: a['id'] is not None, albums))
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


def get_albums_to_download_from_posts(institution_profile_ids, children_ids, cutoff_date):
    print('Get Posts...')
    additional_params = {'limit': 1000}
    albums_to_download = []
    get_posts_institution_profile_ids = institution_profile_ids + children_ids
    posts = client.get_posts(get_posts_institution_profile_ids, additional_params)
    for post in posts:
        creation_date = parse_date(post['publishAt'])
        is_post_after_cutoff_date = creation_date >= cutoff_date
        if not is_post_after_cutoff_date:
            continue
        attachments_with_media = list(filter(lambda a: a['media'] is not None, post['attachments']))
        if attachments_with_media:
            name = clean_title(post['title'])
            album = AlbumToDownload(
                name,
                "Post",
                creation_date,
                list(map(lambda x: x['media'], attachments_with_media)))
            albums_to_download.append(album)
    return albums_to_download


def get_albums_to_download_from_messages(cutoff_date):
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
        if last_thread_update_time.date() < cutoff_date:
            break
    for thread in threads:
        thread_id = thread['id']
        thread_latest_message_time = parse_datetime(thread['latestMessage']['sendDateTime'])
        is_thread_updated_after_cutoff_date = thread_latest_message_time.date() >= cutoff_date
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
                album = AlbumToDownload(name, "Message", creation_date, pictures)
                albums_to_download.append(album)
    return albums_to_download


def print_arguments(cutoff_ate, tags_to_find, output_directory):
    param_style = "cyan"
    console.print("Parameters:", style=param_style)
    console.print(f"  outputDirectory: {output_directory}", style=param_style)
    console.print(f"  cutoffDate: {cutoff_ate.strftime('%Y-%m-%d')}", style=param_style)
    if tags_to_find:
        console.print(f"  tags: {tags_to_find}", style=param_style)
    console.print()


def main():
    parser = argparse.ArgumentParser(description='Download images from aula.dk.')
    parser.add_argument(
        '--outputFolder',
        required=True,
        default='output',
        help='Download images in this folder')
    parser.add_argument(
        '--cutoffDate',
        required=True,
        help='Only download images that have been posted on or after this date (format: "YYYY-MM-DD")')
    parser.add_argument(
        '--tags',
        required=False,
        nargs='+',
        help='Only download pictures having at least one of these tags')
    args = parser.parse_args()

    cutoff_date = datetime.fromisoformat(args.cutoffDate).date()
    tags_to_find = args.tags
    output_directory = args.outputFolder
    print_arguments(cutoff_date, tags_to_find, output_directory)

    try:
        profiles = client.get_profiles()
    except Exception as error:
        console.print(error, style="red")
        console.print("Could not get profiles, exiting.", style="red")
        sys.exit()

    institution_profile_ids = list(map(lambda p: p['id'], profiles[0]['institutionProfiles']))
    children_ids = list(map(lambda p: p['id'], profiles[0]['children']))

    albums_to_download = []
    albums_to_download += get_albums_to_download_from_gallery(institution_profile_ids, cutoff_date)
    albums_to_download += get_albums_to_download_from_posts(institution_profile_ids, children_ids, cutoff_date)
    albums_to_download += get_albums_to_download_from_messages(cutoff_date)

    print('Download Pictures...')
    for album in track(albums_to_download, "Albums to download..."):
        if album.creation_date < cutoff_date:
            continue
        print('>', album, end=' ', flush=True)
        for picture in album.pictures:
            if not tags_to_find or (picture['tags'] and picture_has_tags(picture, tags_to_find)):
                album_directory_name = album.creation_date.strftime('%Y%m%d') + ' ' + album.name
                album_directory_path = os.path.join(output_directory, album_directory_name)
                file = picture['file']
                image_creation_time = datetime.strptime(file['created'], '%Y-%m-%dT%H:%M:%S%z')
                image_response = requests.get(file['url'], timeout=30)

                if image_creation_time.date() == album.creation_date:
                    image_directory_path = album_directory_path
                else:
                    folder_name = image_creation_time.strftime('%Y%m%d')
                    image_directory_path = os.path.join(album_directory_path, folder_name)

                os.makedirs(image_directory_path, exist_ok=True)
                image_path = os.path.join(image_directory_path, file['name'])
                with open(image_path, "wb") as file:
                    file.write(image_response.content)
                add_exif_creation_time(image_path, image_creation_time)


if __name__ == '__main__':
    console = Console()
    client = AulaClient()
    main()
