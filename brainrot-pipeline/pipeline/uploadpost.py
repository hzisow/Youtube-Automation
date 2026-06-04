"""Cross-platform uploader using upload-post.com.

One API call uploads to YouTube + TikTok (and Instagram / X / etc. if your
plan includes them). Replaces the separate YouTube + TikTok OAuth flows.

Setup:
  1. Create an account at https://upload-post.com and connect your
     YouTube + TikTok accounts in their dashboard.
  2. Note the "user" label you assigned to your social profiles
     (in our setup that's "tiktokuploader").
  3. Expose these as env vars / GitHub Actions secrets:
       UPLOADPOST_API_KEY = "<your JWT>"
       UPLOADPOST_USER    = "tiktokuploader"
"""
import os
import requests

API_BASE = "https://api.upload-post.com/api"
DEFAULT_PLATFORMS = ("tiktok", "youtube")


def upload(video_path: str, title: str, description: str = "",
           platforms: tuple = DEFAULT_PLATFORMS,
           api_key: str | None = None, user: str | None = None,
           youtube_title: str | None = None,
           tiktok_title: str | None = None,
           youtube_description: str | None = None,
           tiktok_description: str | None = None,
           youtube_privacy: str = "public",
           tiktok_privacy: str | None = None) -> dict:
    """Upload one video to one or more platforms in a single call.

    Returns the API response. Raises requests.HTTPError on non-2xx.
    """
    api_key = api_key or os.environ.get("UPLOADPOST_API_KEY")
    user = user or os.environ.get("UPLOADPOST_USER")
    if not api_key:
        raise RuntimeError("UPLOADPOST_API_KEY env var not set")
    if not user:
        raise RuntimeError("UPLOADPOST_USER env var not set")
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    headers = {
        "Authorization": f"Apikey {api_key}",
        "X-Upload-Post-Source": "youtube-automation",
    }

    form: list[tuple] = [
        ("user", (None, user)),
        ("title", (None, title)),
    ]
    if description:
        form.append(("description", (None, description)))
    for p in platforms:
        form.append(("platform[]", (None, p)))

    if youtube_title:
        form.append(("youtube_title", (None, youtube_title)))
    if tiktok_title:
        form.append(("tiktok_title", (None, tiktok_title)))
    if youtube_description:
        form.append(("youtube_description", (None, youtube_description)))
    if tiktok_description:
        form.append(("tiktok_description", (None, tiktok_description)))
    form.append(("youtube_privacy", (None, youtube_privacy)))
    if tiktok_privacy:
        form.append(("tiktok_privacy_level", (None, tiktok_privacy)))

    with open(video_path, "rb") as f:
        files = form + [("video", (os.path.basename(video_path), f, "video/mp4"))]
        resp = requests.post(f"{API_BASE}/upload", headers=headers,
                              files=files, timeout=600)

    if resp.status_code >= 400:
        msg = resp.text
        try:
            j = resp.json()
            msg = j.get("message") or j.get("detail") or msg
        except Exception:
            pass
        raise requests.HTTPError(
            f"upload-post {resp.status_code}: {msg}", response=resp
        )
    return resp.json() if resp.content else {}
