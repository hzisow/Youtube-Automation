"""Cross-platform uploader using upload-post.com.

One API call uploads to YouTube + TikTok (and Instagram / X / etc. if your
plan includes them). Replaces the separate YouTube + TikTok OAuth flows.

IMPORTANT: /api/upload is only *sometimes* synchronous. When the file is
big enough that the request would time out, upload-post accepts it, hands
it to a background worker, and returns 200 with:

    {"success": true, "request_id": "...", "job_id": "...",
     "message": "Upload initiated successfully in background..."}

That 200 means ACCEPTED, not POSTED. Whether it actually reached YouTube /
TikTok is only knowable by polling /api/uploadposts/status. Use
wait_for_result() after upload() so a failed hand-off doesn't look like a
success in the logs.

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
import time

import requests

API_BASE = "https://api.upload-post.com/api"
DEFAULT_PLATFORMS = ("tiktok", "youtube")


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Apikey {api_key}",
        "X-Upload-Post-Source": "youtube-automation",
    }


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

    Returns the API response. A 200 with a `request_id` means the upload was
    ACCEPTED and queued -- call wait_for_result(request_id) to find out
    whether it actually posted. Raises requests.HTTPError on non-2xx.
    """
    api_key = api_key or os.environ.get("UPLOADPOST_API_KEY")
    user = user or os.environ.get("UPLOADPOST_USER")
    if not api_key:
        raise RuntimeError("UPLOADPOST_API_KEY env var not set")
    if not user:
        raise RuntimeError("UPLOADPOST_USER env var not set")
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

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
        resp = requests.post(f"{API_BASE}/upload", headers=_headers(api_key),
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


def upload_status(request_id: str, api_key: str | None = None,
                  timeout: float = 60.0) -> dict:
    """One-shot status check for an async upload. Raises on non-2xx."""
    api_key = api_key or os.environ.get("UPLOADPOST_API_KEY")
    if not api_key:
        raise RuntimeError("UPLOADPOST_API_KEY env var not set")
    resp = requests.get(f"{API_BASE}/uploadposts/status",
                         headers=_headers(api_key),
                         params={"request_id": request_id},
                         timeout=timeout)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


# Status strings that mean "stop polling, this is the answer". We don't have
# their schema documented, so this is a best guess over the usual vocabulary
# plus whatever we observe in the logs. wait_for_result() prints every raw
# payload precisely so this set can be tightened once we've seen real ones.
_TERMINAL = {
    "completed", "complete", "success", "succeeded", "done", "finished",
    "failed", "failure", "error", "errored", "partial", "partial_success",
    "cancelled", "canceled", "rejected",
}
_BAD = {"failed", "failure", "error", "errored", "cancelled", "canceled",
        "rejected"}


def terminal_status(payload) -> str | None:
    """Pull a settled status string out of a status payload, or None.

    Defensive about shape: checks a few likely key names at the top level
    and one level down under data/result/results.
    """
    if not isinstance(payload, dict):
        return None
    for key in ("status", "state", "job_status", "upload_status"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip().lower() in _TERMINAL:
            return val.strip().lower()
    for key in ("data", "result", "results", "job"):
        inner = payload.get(key)
        if isinstance(inner, dict):
            found = terminal_status(inner)
            if found:
                return found
    return None


def is_failure(status: str | None) -> bool:
    return bool(status) and status.lower() in _BAD


def wait_for_result(request_id: str, api_key: str | None = None,
                    timeout: float = 300.0, interval: float = 20.0,
                    log=print) -> dict:
    """Poll an async upload until it settles, or until `timeout` elapses.

    Returns the last status payload seen (empty dict if every poll failed).
    Never raises -- a status endpoint that's down shouldn't kill a run whose
    video already uploaded fine.
    """
    deadline = time.monotonic() + timeout
    last: dict = {}
    attempt = 0
    while time.monotonic() < deadline:
        attempt += 1
        try:
            last = upload_status(request_id, api_key=api_key)
        except Exception as e:
            log(f"    status poll {attempt}: request failed "
                f"({type(e).__name__}: {e})")
        else:
            log(f"    status poll {attempt}: {last}")
            if terminal_status(last):
                return last
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval, remaining))
    log(f"    upload did not settle within {timeout:.0f}s; "
        f"last payload: {last}")
    return last
