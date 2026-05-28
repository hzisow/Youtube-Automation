#!/usr/bin/env python3
"""Auto-upload to YouTube via the official Data API v3 (free, OAuth).

One-time setup:
  1. console.cloud.google.com -> new project -> enable "YouTube Data API v3".
  2. Create OAuth client (type: Desktop) -> download as client_secret.json here.
  3. First run opens a browser to authorize; token is cached to token.json.

Quota note: uploads cost 1600 units; the free daily quota is 10,000 units,
so ~6 uploads/day per project before you must request more or wait for reset.

Example:
  python upload.py --file output/video.mp4 --title "AITA for..." \
      --description "..." --tags reddit aita brainrot --privacy public
"""
import argparse
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

HERE = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = os.path.join(HERE, "client_secret.json")
TOKEN = os.path.join(HERE, "token.json")


def _service():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(file, title, description, tags, privacy="public", made_for_kids=False):
    youtube = _service()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "24",  # Entertainment
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }
    media = MediaFileUpload(file, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")
    print(f"Done -> https://youtu.be/{response['id']}")
    return response["id"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--tags", nargs="*", default=[])
    p.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    p.add_argument("--made-for-kids", action="store_true")
    args = p.parse_args()
    upload(args.file, args.title, args.description, args.tags,
           args.privacy, args.made_for_kids)


if __name__ == "__main__":
    main()
