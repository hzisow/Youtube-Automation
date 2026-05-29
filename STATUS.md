# RedditStories Uploader — Project Status

Personal automation pipeline that turns public Reddit story posts into short
videos and cross-posts them to YouTube and TikTok via official APIs.

This file is the **single source of truth** for project state. Read this first
when picking the work back up.

Owner: Henry Zisow (`henryzisow@gmail.com`)
Repo:  https://github.com/hzisow/Vibecoding-Projects
Branch:`youtube-automation` (default branch)

---

## What's running right now

- **GitHub Actions workflow** `.github/workflows/daily-brainrot.yml` runs **5
  crons/day** in the cloud — no local machine required:
  - 13:00 / 16:00 / 19:00 / 23:00 / 02:00 UTC (9 AM / 12 PM / 3 PM / 7 PM / 10 PM ET).
  - Each cron uploads **1 story** (manual dispatch defaults to 1 too).
- Cross-posts to **YouTube** (public) and **TikTok** (drafts/inbox).
- Reads stories from `brainrot-pipeline/stories_cache.json`
  (~6,570 stories — enough for years).
- Commits `brainrot-pipeline/used.json` back after each run so stories never repeat.

---

## Current settings

| Setting | Value | Where to change |
|---|---|---|
| Daily upload count | 1 story per cron × 5 crons = 5/day | workflow `count` env / `--count` |
| Split threshold | 2:00 (120s) | `auto.py --max-seconds` default |
| Max parts per story | 3 (anything longer is trimmed) | `pipeline/split.py max_parts` |
| Recap overlap on Part 2+ | 8 seconds | `pipeline/split.py overlap_seconds` |
| Minimum story length | 55 seconds | `auto.py --min-seconds` |
| TTS voice | `en-US-AndrewNeural` | `pipeline/tts.py DEFAULT_VOICE` |
| TTS rate | +28% | `auto.py --rate` default |
| Caption font | Arial bold, size 96 | `pipeline/captions.py DEFAULT_FONT/SIZE` |
| Caption animation | OFF (plain) | `write_ass(animate=...)` default False |
| Caption position | y=1120 (just below center) | `captions.DEFAULT_Y` |
| Caption color | tone-based (subreddit → color map) | `pipeline/tone.py` |
| Caption punctuation | stripped (DONT, THIS, REALLY) | `captions._PUNCT_RE` |
| Reddit title card | shows for spoken-title duration, max 12s | `titlecard.title_end_time` |
| Channel name on card | `Redditstories` | `--channel` |
| Intro ding | bundled `sounds/ding.mp3` (TikTok ding) | `--no-ding` to disable |
| Background music | OFF by default | `--music path` |
| YouTube privacy | `public` | workflow env `YOUTUBE_PRIVACY` |
| TikTok mode | `inbox` (drafts) | workflow env `TIKTOK_MODE` |
| Required TikTok hashtags | `#fyp #viral #trending` always | `descriptions.TIKTOK_REQUIRED` |
| YouTube description | short — credit + next-part hook + hashtags | `descriptions.youtube` |
| Subreddit pool | AITA, tifu, MaliciousCompliance, pettyrevenge, ProRevenge, EntitledParents, confession | `auto.DEFAULT_SUBREDDITS` |
| Video styles | story / screenshot / tweet — rotated across 5 daily crons | `auto.py --style` and workflow `STYLE` switch |
| Vibe music | auto-picked per story from `assets/music/<mood>/` (chill/sad/funny/dramatic/hype/mystery); off if folder empty | `tone.mood_for` + `pipeline/music.py` |
| Daily style rotation | 9AM story · 12PM screenshot · 3PM tweet · 7PM screenshot · 10PM story | workflow `Generate and upload` step |

---

## Required GitHub secrets

At `https://github.com/hzisow/Vibecoding-Projects/settings/secrets/actions`:

| Secret name | What it is |
|---|---|
| `GAMEPLAY_URL` | Direct .mp4 link to the looping gameplay video (currently hosted on a Release asset) |
| `REDDIT_CLIENT_ID` | Reddit "installed app" client ID (only used by local `refresh_stories.py`, but workflow forwards it) |
| `CLIENT_SECRET_JSON` | Contents of `brainrot-pipeline/client_secret.json` (YouTube OAuth client) |
| `TOKEN_JSON` | Contents of `brainrot-pipeline/token.json` (YouTube refresh token cache) |
| `TIKTOK_CLIENT_JSON` | Contents of `brainrot-pipeline/tiktok_client.json` |
| `TIKTOK_TOKEN_JSON` | Contents of `brainrot-pipeline/tiktok_token.json` |

All 4 JSON files are git-ignored locally; never commit them.

---

## What's pending / in progress

### YouTube OAuth verification (Google)
**Goal:** publish the app so refresh tokens stop expiring every 7 days.

- ✅ Search Console verified for `https://hzisow.github.io/Vibecoding-Projects/`
- ✅ Search Console verified for `https://redditstories.henryzisow.com/`
- ✅ Landing page at `docs/index.html` rewritten to satisfy "purpose / app name / ownership"
- ✅ OAuth consent screen updated to use `redditstories.henryzisow.com` URLs and `henryzisow.com` as authorized domain
- ✅ CNAME `redditstories.henryzisow.com → hzisow.github.io` configured at GoDaddy
- ✅ `docs/CNAME` file pushed
- ✅ GitHub Pages HTTPS cert provisioned; both `/` and `/privacy.html` load cleanly
- ⏳ **Currently waiting on:** Google's review of the resubmitted verification.
  Typical wait 2–6 weeks. Google may email asking for clarification or a demo video
  (see "Demo video script" below). Once approved, refresh tokens persist indefinitely
  and the weekly re-auth routine stops being needed.

### TikTok production audit
**Goal:** flip TikTok from drafts to direct public posting.

- ✅ Sandbox mode working (drafts via `video.upload` scope).
- ✅ Have everything ready (app icon `docs/app-icon.png`, ToS `docs/terms.html`, Privacy `docs/privacy.html`).
- ❌ **Production audit not submitted yet.** Steps:
  1. In TikTok dev portal, switch toggle from Sandbox → Production.
  2. Fill the Production form (same content as Sandbox, plus enable Direct Post + add `video.publish` scope).
  3. Update ToS/Privacy URLs to `https://redditstories.henryzisow.com/terms.html` and `.../privacy.html`.
  4. Submit demo video showing the OAuth flow + a direct upload.
  5. Audit takes 2–6 weeks.
  6. After approval: replace `tiktok_client.json` with Production credentials, switch workflow `TIKTOK_MODE`
     env from `inbox` to `direct`, optionally set `--tiktok-privacy PUBLIC_TO_EVERYONE`.

---

## Weekly YouTube re-auth routine (until Google approves verification)

The YouTube OAuth app is in "Testing" mode, so refresh tokens are revoked after
~7 days. When YouTube uploads start failing in the workflow logs:

1. On Windows PC:
   ```powershell
   cd $HOME\vibecoding-projects\brainrot-pipeline
   git pull
   python upload.py --file output\<any.mp4> --title "reauth" --privacy unlisted
   ```
   Browser opens → approve → token.json refreshed.
2. Print and copy the new token:
   ```powershell
   Get-Content token.json -Raw
   ```
3. At `https://github.com/hzisow/Vibecoding-Projects/settings/secrets/actions` →
   click `TOKEN_JSON` → **Update secret** → paste → Save.

Takes ~30 seconds. Stops being necessary once Google approves verification.

---

## File layout

```
brainrot-pipeline/
├── auto.py                  # main runner (used by workflow & local)
├── generate.py              # one-off single-story renderer
├── upload.py                # YouTube uploader (used for re-auth too)
├── tiktok_upload.py         # TikTok uploader (paste-code OAuth flow)
├── refresh_stories.py       # run locally to refresh stories_cache.json
├── stories_cache.json       # ~6,570 stories scraped from Reddit
├── used.json                # IDs already uploaded (committed by workflow each run)
├── requirements.txt
├── sounds/ding.mp3          # bundled TikTok ding intro
├── stories/sample.txt       # demo story for generate.py
├── assets/                  # gitignored: gameplay.mp4 etc.
└── pipeline/
    ├── tts.py               # Edge-TTS voiceover + word timings
    ├── captions.py          # ASS karaoke captions (one word at a time)
    ├── titlecard.py         # Reddit Snoo title card PNG
    ├── video.py             # ffmpeg assembly (1080x1920)
    ├── reddit.py            # Reddit fetch + cache helpers
    ├── tone.py              # subreddit -> caption color map
    ├── split.py             # multi-part splitter (>2 min, max 3 parts, 8s recap)
    ├── descriptions.py      # YouTube/TikTok auto-descriptions + hashtags
    └── sfx.py               # ding generator/loader

docs/                        # served via GitHub Pages at redditstories.henryzisow.com
├── CNAME                    # redditstories.henryzisow.com
├── index.html               # landing page (+ TikTok OAuth callback when ?code=)
├── privacy.html
├── terms.html
├── app-icon.png             # 1024x1024 used in OAuth consent / TikTok app
├── google[hash].html        # Search Console verification file (do not delete)
└── tiktok[hash].txt         # TikTok URL-prefix verification file (do not delete)

.github/workflows/
└── daily-brainrot.yml       # the cron + render + upload pipeline
```

---

## Demo video script (for whenever we submit either review)

60–90 second screen recording:

1. Show File Explorer at `brainrot-pipeline\` (the app folder).
2. PowerShell: `python auto.py --count 1 --tiktok --tiktok-mode direct`
   (For YouTube verification: `python auto.py --count 1 --upload`).
3. Browser opens to the OAuth consent screen → click Allow.
4. Show the redirect to `https://redditstories.henryzisow.com/?code=...` and the code panel.
5. Paste the code into the terminal.
6. Terminal prints upload success.
7. On phone: open YouTube Studio / TikTok app → show the new video on the channel/profile.

Save as <50 MB .mp4.

---

## Honest limits to remember

- **YouTube quota:** ~6 uploads/day per Cloud project (10,000 units, 1,600 per upload).
  At 5 crons/day with 1 part each, fits. Multi-part stories can push over; the workflow
  catches quota errors gracefully (run stops, next day starts fresh).
- **TikTok limit:** 25 uploads/account/day. Way under.
- **GitHub Actions minutes:** unlimited for public repos. (This repo is public.)
- **GitHub Pages:** custom domain HTTPS provisioning can take 30 min – several hours
  after DNS is correct. Just wait.
- **DST shifts** will offset the cron schedule by 1 hour twice a year (US Eastern moves
  off EDT in Nov). Re-tune the cron strings then if needed.

---

## How to extend

- **More daily uploads:** add more cron lines to the workflow. Watch YouTube quota.
- **More subreddits:** edit `DEFAULT_SUBREDDITS` in `auto.py`, then re-run
  `refresh_stories.py` locally to fill the cache from the new subreddits, push.
- **Different gameplay backgrounds:** update the `GAMEPLAY_URL` secret (point at a
  different Release asset).
- **Different voice:** workflow env or `--voice en-US-BrianNeural` /
  `en-US-ChristopherNeural` / `en-US-GuyNeural` etc. List via `edge-tts --list-voices`.
- **Different caption color per video:** `tone.color_for(subreddit, title)` already
  picks per subreddit; edit `_SUBREDDIT_TONE` or `_KEYWORDS` in `pipeline/tone.py`.
- **Refresh stories:** `python refresh_stories.py` on PC, commit `stories_cache.json`,
  push. Existing cache is enough for years; only needed if you want fresher content.

---

## Quick troubleshooting

| Symptom | Probable cause | Fix |
|---|---|---|
| Workflow logs "quota exceeded" on YouTube | Hit ~6 uploads today (multi-part day) | Wait until tomorrow; quota resets at midnight Pacific |
| YouTube uploads suddenly all fail | 7-day token expiry | Run the re-auth routine above |
| TikTok uploads land in drafts only | App still un-audited (Sandbox) | Submit Production audit (above) |
| Workflow shows env var `CLIENT_SECRET_JSON:` blank | Repo secret missing or misnamed | Re-add the secret (case-sensitive) |
| Reddit 403 on `refresh_stories.py` | Rate-limited or IP-blocked | Wait or pass `--sleep 6 --pages 2` |
| Captions look stretched / off-screen | Bug regression in `_layout` | `captions._MAX_LINE_W` controls wrap; lower it |
