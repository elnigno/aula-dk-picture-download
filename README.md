# aula-dk-picture-download
A python script to download pictures with tags from aula.dk

## Description 
This script downloads images in albums, posts and messages from aula.dk.

For it to work, you must first **log into aula.dk with your browser**. Then you can either copy the session cookie (instructions below) and supply it as an argument or let the script attempt to retrieve it automatically.

Accepted parameters:

- `--cutoffDate CUTOFFDATE` Only download images that have been posted on or after this date (format: "YYYY-MM-DD")
- `--outputFolder OUTPUTFOLDER` Download images in this folder
- `--tags TAGS [TAGS ...]` (Optional) Only download pictures having at least one of these tags
- `--apiVersion APIVERSION` (Optional, default=19) Select the Aula API version
- `--cookie COOKIE` (Optional) Session cookie from the browser for authentication, wrapped in double quotes (**"**)

The script saves images in folders, grouping them by album/post/message. The folders names follow the template "Date Title", where the date is in ISO format (yyyymmdd) and the title is the album/post/message title.

Tested to work on Windows 10, after logging into aula.dk with MitID on Firefox and Chrome.

This script was initially inspired by this blog post: https://helmstedt.dk/2021/05/aulas-api-en-opdatering/

## Usage Example
```bash
python .\aula_download_albums_with_tags.py --cutoffDate "2023-02-19" --tags "Tag1" "Tag2" --outputFolder "output"
```

## Retrieving the session cookie

In your browser (should apply to most):
- Login to aula.dk with MitID
- Press F12 to open the developer tools
- Select the Network tab
- Visit any Aula page
- Notice that a number of requests appear; select the first one
- Go to the Request Headers and copy the value of the "Cookie" header (e.g. initialLogin=true; Csrfp-Token=somehexadecimalsequence; PHPSESSID=somealphanumericsequence; profile_change=8)

## Known issues

- The script might crash if you login with unilogin and attempt to download images from messages marked as sensitive. The issue does not occur when logging in with MitID, so use that if possible. 
- The script might break when Aula moves to a new API version; to work around that, use the `--apiVersion` parameter to try another version.
