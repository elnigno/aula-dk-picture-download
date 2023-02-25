# aula-dk-picture-download
A python script to download pictures with tags from aula.dk

## Description 
This script downloads images in albums, posts and messages from aula.dk.

For it to work, you must first **log into aula.dk with your browser**.

Accepted parameters:

- `--cutoffDate` (in ISO format "YYYY-MM-DD"): only download images that have been posted on or after this date [required].
- `--tags`: only download having these comma separated tags [required].
- `--outputFolder`: download images in this folder

The script saves images in folders, grouping them by album/post/message. The folders names follow this template: "<YYYY-MM-DD> <Title>"

Tested to work on Windows 10, after logging into aula.dk with Firefox.

This script was initially inspired by this blog post: https://helmstedt.dk/2021/05/aulas-api-en-opdatering/

## Usage Example
```bash
python .\aula_download_albums_with_tags.py --cutoffDate "2023-02-19" --tags "Tag1" "Tag2" --outputFolder "output"
```
