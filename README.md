# aula-dk-picture-download
A python script to download pictures with tags from aula.dk

## Description 
This script downloads images in albums, posts and messages from aula.dk.
For it to work, you must first log into aula.dk with your browser.

Accepted parameters:

- Cutoff date (in ISO format "YYYY-MM-DD"): only download images that have been posted on or after this date [required].
- Tags: only download having these comma separated tags [required].
- Output folder: download images in this folder

The script saves images in folders, grouping them by album/post/message. The folders names follow this template: "<YYYY-MM-DD> <Title>"

Tested to work on Windows 10, after logging into aula.dk with Firefox.

## Usage Example
```bash
python .\aula_download_albums_with_tags.py "2023-01-09" "Name1 Surname1,Name2 Surname2" "output"
```