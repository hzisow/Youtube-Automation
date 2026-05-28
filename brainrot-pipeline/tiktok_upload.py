#!/usr/bin/env python3
"""Upload videos to TikTok via the official Content Posting API (free).

One-time setup:
  1. developers.tiktok.com -> create an app -> add the "Content Posting API"
     product. Request scopes: video.upload (drafts/inbox) and, once your app is
     audited, video.publish (direct post).
  2. Add a redirect URI of exactly:  http://localhost:8721/callback
  3. Save your credentials next to this file as tiktok_client.json:
        {"client_key": "...", "client_secret": "..."}
  4. First run opens a browser to authorize; the token is cached in
     tiktok_token.json and auto-refreshed.

Modes:
  - inbox (default): uploads to your TikTok drafts; you tap Post in the app.
    Works for un-audited apps. Use this until your app passes audit.
  - direct: publishes straight to your profile (needs video.publish + an audited
    app). Un-audited apps can only post at SELF_ONLY (private) visibility.

Example:
  python tiktok_upload.py --file output/story.mp4 --title "AITA for..." --mode inbox
"""
import argparse
import http.server
import json
import os
import threading
import time
import urllib.parse
import webbrowser

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.join(HERE, "tiktok_client.json")
TOKEN = os.path.join(HERE, "tiktok_token.json")
REDIRECT_URI = "http://localhost:8721/callback"
REDIRECT_PORT = 8721

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INBOX_INIT = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
DIRECT_INIT = "https://open.tiktokapis.com/v2/post/publish/video/init/"


def _client():
    with open(CLIENT) as f:
        return json.load(f)


def _capture_code(scope: str, client_key: str) -> str:
    """Open the consent screen and capture the OAuth code via a local redirect."""
    box = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.urlparse(self.path).query
            box.update(urllib.parse.parse_qs(q))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"TikTok authorization complete. You can close this tab.")

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    params = {
        "client_key": client_key,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": str(int(time.time())),
    }
    webbrowser.open(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")
    print("A browser window opened for TikTok authorization. Waiting...")
    for _ in range(300):
        if "code" in box:
            return box["code"][0]
        time.sleep(1)
    raise TimeoutError("Did not receive an authorization code from TikTok.")


def _save_token(tok: dict):
    tok["obtained_at"] = time.time()
    with open(TOKEN, "w") as f:
        json.dump(tok, f)


def _token(scope: str) -> str:
    cfg = _client()
    if os.path.exists(TOKEN):
        with open(TOKEN) as f:
            tok = json.load(f)
        if time.time() < tok["obtained_at"] + tok["expires_in"] - 60:
            return tok["access_token"]
        # Refresh.
        r = requests.post(TOKEN_URL, data={
            "client_key": cfg["client_key"],
            "client_secret": cfg["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": tok["refresh_token"],
        }).json()
        if "access_token" in r:
            _save_token(r)
            return r["access_token"]

    code = _capture_code(scope, cfg["client_key"])
    r = requests.post(TOKEN_URL, data={
        "client_key": cfg["client_key"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }).json()
    if "access_token" not in r:
        raise RuntimeError(f"TikTok token exchange failed: {r}")
    _save_token(r)
    return r["access_token"]


def _upload_bytes(upload_url: str, path: str, size: int):
    with open(path, "rb") as f:
        data = f.read()
    headers = {
        "Content-Type": "video/mp4",
        "Content-Length": str(size),
        "Content-Range": f"bytes 0-{size - 1}/{size}",
    }
    resp = requests.put(upload_url, headers=headers, data=data)
    resp.raise_for_status()


def upload(file: str, title: str = "", mode: str = "inbox",
           privacy: str = "SELF_ONLY") -> str:
    """Upload `file` to TikTok. mode='inbox' (draft) or 'direct' (publish)."""
    scope = "video.upload" if mode == "inbox" else "video.publish"
    access = _token(scope)
    size = os.path.getsize(file)
    headers = {"Authorization": f"Bearer {access}",
               "Content-Type": "application/json; charset=UTF-8"}
    source_info = {
        "source": "FILE_UPLOAD",
        "video_size": size,
        "chunk_size": size,        # single chunk (shorts are < 64MB)
        "total_chunk_count": 1,
    }

    if mode == "direct":
        body = {"post_info": {"title": title, "privacy_level": privacy,
                              "disable_comment": False, "disable_duet": False,
                              "disable_stitch": False},
                "source_info": source_info}
        init_url = DIRECT_INIT
    else:
        body = {"source_info": source_info}
        init_url = INBOX_INIT

    r = requests.post(init_url, headers=headers, data=json.dumps(body)).json()
    if r.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok init failed: {r}")
    data = r["data"]
    _upload_bytes(data["upload_url"], file, size)
    print(f"TikTok upload sent (publish_id={data.get('publish_id')}, mode={mode}).")
    if mode == "inbox":
        print("Open the TikTok app -> notifications/drafts to finish posting.")
    return data.get("publish_id", "")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--mode", default="inbox", choices=["inbox", "direct"])
    p.add_argument("--privacy", default="SELF_ONLY",
                   choices=["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS", "PUBLIC_TO_EVERYONE"])
    args = p.parse_args()
    upload(args.file, args.title, args.mode, args.privacy)


if __name__ == "__main__":
    main()
