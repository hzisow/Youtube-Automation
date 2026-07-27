# STATUS — Youtube-Automation

**Single source of truth for project state.** Read this FIRST when picking work
back up or resuming after a compacted chat. Every meaningful change to the
system should land here in the **Recent changes** section before being marked
done. Decisions made in chat that aren't reflected here are at risk of being
forgotten.

- **Owner:** Henry Zisow (`hzisow@gmail.com`)
- **Repo:** https://github.com/hzisow/Youtube-Automation
- **Default branch:** `main`
- **Last reviewed:** 2026-06-19

---

## TL;DR

Personal automation that turns Reddit story posts into vertical Shorts and
cross-posts them to YouTube + TikTok. Runs fully unattended on GitHub Actions
(public repo = unlimited minutes). One service (upload-post.com) handles both
platforms' auth so we don't run any OAuth ourselves anymore. Voice is Piper
TTS (open source, runs in CI). Cadence is intentionally randomized to ~3 posts
per 4 days at varying times so it doesn't look botted. Horror stories from
r/nosleep / r/letsnotmeet get distinctive treatment (deep voice + ambient
music + heavy color grade). Background gameplay clips rotate automatically
from a GitHub Release.

---

## ⚠️ How to make changes to this project

**Push directly via the GitHub MCP** (`mcp__github__push_files` /
`create_or_update_file`). Do NOT generate `.patch` files for the user to
apply with `git am` — we did that for most of this project's history and it
was slow and error-prone (browsers strip dashes from patch filenames, patches
get lost in Downloads, stuck rebases, etc.). Direct push works and takes
seconds.

The only things that still need the user's local machine:
- Anything that modifies `stories_cache.json` (too large to round-trip well)
- Binary uploads over a few MB
- Anything requiring a browser login (OAuth flows, dashboards)

The user's local clone is at `C:\Users\Henry\vibecoding-projects` (folder name
still says vibecoding — the repo was renamed, the folder wasn't).

---

## What's running right now (current production)

- **Cadence:** 2 cron triggers per day (`14 UTC` and `22 UTC`). Each
  independently rolls a **38% dice** to actually post; if yes, sleeps a
  random **0–180 minutes** before kicking off the render. Net rate ≈ 0.76
  posts/day = ~3 posts every 4 days. Post times are never the same twice.
- **Voice engine:** Piper TTS (open source, MIT, ~60 MB voices, CPU-only).
  Default rotation pool of 4 voices; `en_US-ryan-high` is the deepest.
  Edge TTS is still wired up as a fallback — flip `TTS_ENGINE: piper` →
  `edge` in the workflow to swap.
- **Word timings:** Piper doesn't emit word boundaries, so faster-whisper
  re-transcribes the rendered audio to get word timestamps for captions.
  Adds 30–60 sec per video; both Piper voices and Whisper model are cached
  across workflow runs.
- **Uploads:** Both YouTube + TikTok go through https://upload-post.com via
  one API call. No direct Google or TikTok OAuth on our side anymore.
  Plan tier: paid (Henry's), user label: `tiktokuploader`.
  ⚠️ TikTok frequently rejects direct posting with a "daily active-user
  limit" and drops the video into the TikTok **inbox as a draft** instead —
  see "Honest limits" below. YouTube is unaffected.
- **Background clips:** auto-rotated. Every run queries the GitHub Release
  tagged **`assets-v1`**, lists its `.mp4` assets, and picks one at random.
  Additionally each *story* seeks a different offset into the clip, so two
  unrelated shorts don't open on the same frame — but all parts of one
  multi-part story share the clip AND the start frame.
- **Story source:** `brainrot-pipeline/stories_cache.json` (~6,570 drama
  stories; 12 seeded horror stories exist in `seed_horror_stories.py` but
  may not be merged into the cache yet — see TODOs). The cache file is
  committed to the repo. `used.json` tracks IDs already used and is
  auto-committed back at the end of each workflow run.
- **Visual style:** Reddit Snoo title card at the start (kept per user
  preference), MrBeast one-word-at-a-time captions over looping gameplay
  background with cinematic color grade. Horror stories use the horror
  color grade (heavier desat + vignette).
- **Title font:** Inter (bundled in `brainrot-pipeline/assets/fonts/`).
- **Channel name on card:** "Redditstories".

---

## Required GitHub secrets

Set at https://github.com/hzisow/Youtube-Automation/settings/secrets/actions

| Secret | Purpose |
|---|---|
| `UPLOADPOST_API_KEY` | JWT from upload-post.com dashboard. Long-lived (exp year 2125). |
| `UPLOADPOST_USER` | The user label assigned in upload-post.com. Current value: `tiktokuploader`. |
| `GAMEPLAY_URL` | **Fallback only.** Direct .mp4 link, used if the `assets-v1` release has no .mp4 assets. Safe to leave set. |

### Optional / not currently used
- `REDDIT_CLIENT_ID` — installed-app client ID. Only used by local
  `refresh_stories.py`. Reddit's anti-scraping blocks residential IPs; we
  worked around it with `seed_horror_stories.py`. Attempts to register a
  new Reddit app also failed.
- `PEXELS_KEY` — was for the abandoned "explainer" video style.
- `TTS_VOICE` / `TTS_VOICES` — override Edge TTS voice/pool.
- `PIPER_VOICE` / `PIPER_VOICES` — override Piper voice/pool.

### Deleted (intentionally, do not re-add)
`CLIENT_SECRET_JSON`, `TOKEN_JSON`, `TIKTOK_CLIENT_JSON`, `TIKTOK_TOKEN_JSON`
— belonged to the direct YouTube + TikTok OAuth path which we replaced with
upload-post.com. The Python modules (`upload.py`, `tiktok_upload.py`) still
live in the repo as archived reference but aren't called.

---

## upload-post.com API reference

Discovered by reading the official npm client's source
(`github.com/Upload-Post/upload-post-npm`, `index.js`). Implemented in
`brainrot-pipeline/pipeline/uploadpost.py`.

```
POST https://api.upload-post.com/api/upload
Authorization: Apikey <JWT>          # NOT "Bearer"
X-Upload-Post-Source: <any string>
Content-Type: multipart/form-data
```

Form fields we send:

| Field | Notes |
|---|---|
| `video` | the .mp4 file (or an https URL) |
| `user` | the profile label, e.g. `tiktokuploader` |
| `title` | default title for all platforms |
| `description` | default description |
| `platform[]` | **repeated once per platform** — `tiktok`, `youtube` |
| `youtube_title`, `tiktok_title` | per-platform title overrides |
| `youtube_description`, `tiktok_description` | per-platform description overrides |
| `youtube_privacy` | `public` / `unlisted` / `private` |
| `tiktok_privacy_level` | `SELF_ONLY` / `MUTUAL_FOLLOW_FRIENDS` / `PUBLIC_TO_EVERYONE` |

Other endpoints on the same base (not used yet): `/upload_photos`,
`/upload_text`, `/upload_document`, `/uploadposts/status?request_id=...`,
`/uploadposts/history`, `/uploadposts/schedule`. Supports scheduling via
`scheduled_date` + `timezone`, and `async_upload`.

The API key is a JWT tied to `hzisow@gmail.com` with `exp` in year 2125 —
treat it like a password. It was pasted in chat during setup; rotating it
in the upload-post dashboard is cheap defensive hygiene if that ever
matters.

---

## Background clip rotation

Clips live as assets on the GitHub Release tagged **`assets-v1`**:
https://github.com/hzisow/Youtube-Automation/releases/tag/assets-v1

**To add a clip:** Edit release → drag `.mp4` files in → Update release.
That's it. The next run picks it up. No secret edits, no code changes.

**How it works** (in `.github/workflows/daily-brainrot.yml`, step
"Fetch a random gameplay clip"):
1. `curl` the GitHub API for `/releases/tags/assets-v1`.
2. `jq` filters `.assets[]` down to names ending in `.mp4`.
3. `shuf -n 1` picks one at random.
4. `curl` downloads it to `brainrot-pipeline/assets/gameplay.mp4`.
5. If zero `.mp4` assets are found, falls back to the `GAMEPLAY_URL` secret.
   If that's also empty, the step fails with a clear error.

One clip is downloaded per run, so every video rendered in that run —
including all parts of a multi-part story — uses the same clip file.

**Second variety axis:** `pipeline/video.py:render()` takes `bg_offset`
(seconds). `auto.py` passes `hash(story["id"]) % 600`. Seeded on the
**story id, not the slug** — that's deliberate, so Part 1 / Part 2 /
Part 3 all open on the same frame and read as one continuous series,
while unrelated stories land somewhere different. (Voice rotation is
seeded the same way, for the same reason.) `render()` wraps the offset
modulo the clip's real duration via ffprobe so it never seeks past the
end, and `-stream_loop -1` still covers the full narration.

**Why the release and not something else:** unlimited free bandwidth on
public repos, 2 GB/file, same host as the repo (no third-party link rot).
Google Drive / Dropbox direct-download links break constantly. Committing
clips to the repo bloats git history and hits the 100 MB file cap.

**Clip guidance:** 5–10 min each, under ~200 MB, 1080×1920 vertical
preferred (16:9 works, gets center-cropped). Avoid Subway Surfers — it's
so oversaturated it now reads as "low-effort AI" to viewers. Better:
Trackmania, GTA stunts, Minecraft parkour, satisfying mechanical loops,
marble runs, slime/paint mixing.

---

## What multi-part stories share

A story longer than 2 minutes gets split into Part 1 / Part 2 / Part 3
(`pipeline/split.py`, 8s recap overlap, max 3 parts). These are
deliberately kept visually and sonically consistent so they read as one
series:

| Property | Shared across parts? | Seeded on |
|---|---|---|
| Background clip file | Yes | one download per workflow run |
| Background start frame | Yes | `hash(story["id"])` |
| Narrator voice | Yes | `hash(story["id"])` |
| Color grade | Yes | subreddit |
| Music bed | Yes | subreddit / mood |
| Caption color | Yes | subreddit tone |
| Title card text | No — shows "(Part N)" | — |

If you ever want something to vary per part instead, seed it on `slug`
(which is `<base>-p1`, `<base>-p2`, …) rather than `story["id"]`.

---

## File layout

```
.github/workflows/
  daily-brainrot.yml         # cron, dice job, clip rotation, generate+upload

brainrot-pipeline/
  auto.py                    # main runner (cron entrypoint)
  generate.py                # one-off single-story renderer
  upload.py                  # archived: direct YouTube upload (unused)
  tiktok_upload.py           # archived: direct TikTok upload (unused)
  refresh_stories.py         # scrape Reddit -> stories_cache.json (run locally)
  seed_horror_stories.py     # inject 12 hand-written horror stories into cache
  preview_voices.py          # render Edge TTS samples to pick favorites
  fetch_music.py             # download royalty-free music from Pixabay
  make_branding.py           # generate channel banner + profile pic
  stories_cache.json         # ~6,570 stories
  used.json                  # IDs already uploaded; committed back each run
  requirements.txt
  sounds/
    ding.mp3                 # bundled TikTok ding intro
    horror.mp3               # slowed Fallen Down (Undertale), ambient horror bed
  assets/
    .gitkeep                 # most of assets/ is gitignored
    fonts/                   # exception: Inter-Bold.ttf, Inter-Regular.ttf
    music/<mood>/            # gitignored placeholder for vibe music; empty
    gameplay.mp4             # gitignored; fetched at workflow time (random clip)
  pipeline/
    tts.py                   # dispatcher: routes to piper_tts or Edge via TTS_ENGINE
    piper_tts.py             # Piper TTS implementation (open source)
    captions.py              # ASS karaoke captions; Whisper fallback for timings
    titlecard.py             # Reddit Snoo title card PNG (uses Inter)
    video.py                 # ffmpeg assembly; grades + bg_offset seek
    reddit.py                # Reddit fetch + cache helpers
    tone.py                  # subreddit -> caption color + mood map
    split.py                 # multi-part splitter (>2 min, max 3 parts, 8s recap)
    descriptions.py          # YouTube/TikTok auto-descriptions + hashtags
    music.py                 # pick royalty-free track from assets/music/<mood>/
    sfx.py                   # ding generator/loader
    uploadpost.py            # upload-post.com REST client
    # below are kept for reference but not currently used:
    redditpost.py            # scrollable Reddit post renderer (screenshot style)
    scroll.py                # ffmpeg scroll expression builder
    tweetcard.py             # X/Twitter card renderer
    broll.py                 # Pexels B-roll fetcher
    facts.py                 # TIL rephrasing for explainer style

docs/                        # GitHub Pages -> redditstories.henryzisow.com
  CNAME                      # redditstories.henryzisow.com
  index.html                 # landing page (was also TikTok OAuth callback)
  privacy.html
  terms.html
  app-icon.png               # 1024x1024 brand icon
  google[hash].html          # Search Console verification -- KEEP THIS ONE
  tiktok[hash].txt           # TikTok URL-prefix verification

STATUS.md                    # this file
```

The repo root used to also contain `agency-dashboard/` files; those were
moved to `hzisow/agency-dashboard` and cleaned out of this repo 2026-06-15.
A `spaced-repetition` branch (the "Recall" study PWA) was likewise split
out to `hzisow/study-calendar` and its branch deleted here.

---

## The docs/ folder — do we still need it?

Mostly no, but leave it. Since uploads moved to upload-post.com, nothing
in `docs/` is load-bearing for the pipeline. Breakdown:

| File | Still doing work? |
|---|---|
| `google[hash].html` | **Yes** — keeps the Search Console property verified for `redditstories.henryzisow.com`. Keep it. |
| `CNAME` | Yes, if you want the subdomain to keep resolving |
| `index.html` / `privacy.html` / `terms.html` | No — were OAuth consent-screen requirements |
| `app-icon.png` | No — was the OAuth consent screen icon |
| `tiktok[hash].txt` | No — TikTok domain verification, unused now |

Cost of keeping: $0 (GitHub Pages serves static files free). Cost of
deleting: the Google Cloud OAuth client still exists and was approved at
Production status partly on the basis of a working homepage. If Google
ever re-reviews and the homepage 404s, verification could be pulled.
Not worth the risk for zero savings.

`tiktok-developers-site-verification=MsmZGozJ1k8z5soTVwYCtUi8SJBWhpbP` is
a **domain-ownership token, not an API key.** It's public by design and
harmless. Don't confuse it with `UPLOADPOST_API_KEY`.

---

## Google Cloud OAuth client (dormant but intact)

Not used by the pipeline anymore, but it still exists and is fully set up
in case we ever want to go back to direct YouTube uploads:

- Client ID: `688194610787-n5knm70tdilc2j7bfnl0btq29lvgpfmp.apps.googleusercontent.com`
- **Publishing status: In production** (checked 2026-05-31)
- User type: External, 1 / 100 user cap
- Branding: verified

**Why this matters:** "In production" is what makes refresh tokens
persist indefinitely. In "Testing" they expire every 7 days, which is
what forced the old weekly re-auth routine. Google confirmed by email
that personal-use apps under 100 users don't need formal verification.
So if you ever revert to direct YouTube uploads, tokens will not expire.

---

## Voice engine details

Both engines expose the same surface (`DEFAULT_VOICE`, `VOICE_POOL`,
`pick_voice(seed)`, `synthesize(text, out_path, voice, rate)`) so
`auto.py` doesn't care which is active. `pipeline/tts.py` reads the
`TTS_ENGINE` env at import time and configures both sets.

### Piper (current default)
- Voice pool (rotation): `en_US-ryan-high`, `en_US-norman-medium`,
  `en_US-john-medium`, `en_GB-alan-medium`.
- Voices download from HuggingFace on first use into `~/.cache/piper/`
  and are cached across workflow runs by `actions/cache@v4`.
- `pipeline/piper_tts.py` uses the `piper` CLI; Python API as fallback.
- Output: WAV → transcoded to MP3 via ffmpeg to match the rest of the pipeline.

### Edge TTS (fallback)
- Voice pool: `en-US-AndrewMultilingualNeural`, `en-US-BrianMultilingualNeural`,
  `en-US-EmmaMultilingualNeural`, `en-US-AvaMultilingualNeural`,
  `en-US-ChristopherNeural`, `en-US-RogerNeural`.
- Horror voice (forced for scary subs): `en-US-RogerNeural`.
- Edge TTS emits per-word boundaries natively — skips the Whisper step.
- The "Multilingual" variants sound noticeably more natural than the
  plain ones — prefer them if adding more.

### Word timings
- Edge returns word timings → used directly.
- Piper returns `[]` → `captions.timings_ok([])` is False → falls back to
  `pipeline/captions.transcribe_words(audio)` which uses faster-whisper.

### How to swap engines
Edit `.github/workflows/daily-brainrot.yml`, change the `TTS_ENGINE` env at
the top of the file. No code changes needed.

---

## Cadence details

The workflow has TWO jobs:
1. `dice` — runs every trigger, rolls `RANDOM % 100`. If < 38, sets
   `should_post=true`. Manual `workflow_dispatch` always sets true.
2. `generate` — has `if: needs.dice.outputs.should_post == 'true'`. First
   step is a random sleep `0–180 min`. Then checkout + ffmpeg install +
   Python deps + clip fetch + render + upload.

Net effect:
- 2 triggers/day × 38% = 0.76 posts/day = ~3 posts every 4 days.
- 0–180 min random sleep means actual post times vary inside each window.
- Morning window: 10 AM ET trigger → posts 10 AM – 1 PM ET.
- Evening window: 6 PM ET trigger → posts 6 PM – 9 PM ET.
- Some days have 0 posts. Some days have 2. Average evens out.

`timeout-minutes: 300` because the random sleep can be up to 3 hours.

---

## Horror story treatment

Stories from `r/nosleep` or `r/letsnotmeet` automatically get a different
treatment in `auto.py`:
- **Voice:** forced to `en-US-RogerNeural` on the Edge engine. On Piper the
  normal pool is used (its voices are already deep).
- **Music bed:** `sounds/horror.mp3` (slowed/muffled Undertale "Fallen
  Down", 6 min, loops) mixed under voice at ~10% volume. Overrides the
  per-mood music library lookup.
- **Color grade:** "horror" preset (heavier desat + stronger vignette +
  darker shadows) instead of "cinematic".
- Detection lives in the story loop in `auto.py`: looks at
  `story["subreddit"]` lower-cased against `SCARY_SUBS`.

`seed_horror_stories.py` contains 12 original nosleep-style stories
(IDs `seed-h-001` … `seed-h-012`, ~875 chars each so they clear the 55s
narration floor). Run it locally and commit the updated
`stories_cache.json` to get them into rotation — see TODOs. With 12
horror out of ~6,580 total and ~3 posts per 4 days, horror will fire
rarely; add more entries to the script if you want it more often.

---

## Decision log (chronological)

Every meaningful choice that shaped the current state. Add new entries
to the bottom as decisions are made. Don't remove old entries.

- **Repo rename:** `Vibecoding-Projects` → `Youtube-Automation`.
- **Default branch rename:** `youtube-automation` → `main`.
- **Multi-project split:** moved `agency-dashboard` and `spaced-repetition`
  (Recall study app) out to their own repos (`hzisow/agency-dashboard`,
  `hzisow/study-calendar`).
- **Upload mechanism:** dropped direct YouTube Data API + TikTok Content
  Posting API in favor of upload-post.com. Eliminates 4 OAuth secrets,
  the weekly Google token refresh dance, and the TikTok production-audit
  requirement.
- **Cadence:** cut from 5 posts/day fixed times → ~3 posts per 4 days at
  randomized times. Reasoning: research shows post-Sept-2025 YouTube
  Shorts algorithm rewards quality + variety over volume, and the
  inauthentic-content classifier flags high-volume low-variation patterns.
- **Niche:** stuck with Reddit story format. Considered and rejected a
  full pivot to math/physics content despite research suggesting it.
  Horror added as a sub-treatment inside the existing channel rather
  than a separate channel.
- **Snoo card placement:** kept at the start of the video despite
  research suggesting move to corner. User preference.
- **Voice engine:** swapped from Edge TTS → Piper TTS as default
  (open source, runs locally in CI). Edge stays as fallback.
- **ElevenLabs:** declined. Free tier is 10k chars/month ≈ 12–15 videos,
  nowhere near enough. Paid would be $22/mo (Creator) at the current
  cadence or $99/mo (Pro) at 5/day. Open to revisit if Piper output
  isn't enough after a couple weeks of data.
- **Title font:** bundled Inter (OFL) in `assets/fonts/` for consistent
  rendering across local PC + CI.
- **Background clips:** hosted as GitHub Release assets on `assets-v1`,
  auto-discovered and randomly picked per run. Chosen over Drive/Dropbox
  (link rot) and in-repo commits (history bloat, 100 MB cap).
- **Multi-part consistency:** parts of one story deliberately share clip,
  start frame, voice, grade and music so they read as a series. Anything
  that should vary per part must be seeded on `slug`, not `story["id"]`.

---

## Discarded experiments (don't rebuild these)

Things we tried, built, and abandoned. Code mostly still exists in the
repo but isn't called from the workflow. Don't re-implement without a
new reason.

- **Math "Top 5" slideshow** — countdown videos modeled on @euleronpoint
  / @atmathlab. User reverted to pure Reddit stories.
- **Geometry puzzle pipeline** — AndyMath-style problem → 3-2-1
  countdown → answer reveal (matplotlib + SymPy).
- **Python sim loops** — pendulum wave, Galton board, prime spiral,
  Lissajous, double pendulum. Visually striking but no hook structure.
- **Derivation animations** — animated proofs (quadratic formula,
  Euler's identity, derivative from first principles).
- **Screenshot-scroll style** — full Reddit post image on top half,
  gameplay below, scrolls in sync with TTS. User didn't like the look.
- **Tweet card style** — X-style card with embedded image over animal
  background.
- **Explainer style** — Pexels topic-matched B-roll + centered captions.
- **"Did you know" facts pipeline** — TIL rephrased to "Did you know
  that..." narration. Needed a fact-subreddit refresh Reddit kept blocking.
- **Trending TikTok / YouTube sounds via API** — impossible. Both
  platforms only allow sound-catalog selection through their own UI;
  licensing doesn't permit third-party redistribution. No tool exists
  (and won't) that does this legally and automatedly. upload-post has a
  `tiktokAutoAddMusic` flag but it's photo-carousel only.
- **MisoTTS** — 16 GB model, needs 24 GB VRAM. Cannot fit on a GitHub
  Actions free runner (7 GB RAM, no GPU, ~14 GB disk).
- **Math channel rebrand** ("MathBytes") — researched, generated banner
  + profile pic via `make_branding.py`, then user chose to stay on the
  Reddit format.
- **Patch-file workflow** — generating `.patch` files for the user to
  `git am`. Replaced by direct GitHub MCP pushes. See the section at the
  top of this doc.

---

## Outstanding TODOs

- [ ] **Upload background clips** to the `assets-v1` release so rotation
      actually has something to rotate between. Until then every run
      picks the single existing clip (or the `GAMEPLAY_URL` fallback).
- [ ] **Verify the clip-rotation step works.** The jq/GitHub-API query in
      the workflow has never actually executed — it runs for the first
      time on the next run. If it fails, the fallback should catch it,
      but check the "Fetch a random gameplay clip" step log.
- [ ] **TikTok daily-limit problem.** Videos keep landing in the TikTok
      inbox as drafts instead of publishing. Next step: email upload-post
      support and ask whether a plan tier / setting guarantees direct
      TikTok posting. If not, decide between (a) manual finish in the
      TikTok app, or (b) route YouTube-only through upload-post.
- [ ] Watch a Piper-engine cron run end-to-end. If it fails, the one-line
      revert is `TTS_ENGINE: piper` → `edge` in the workflow.
- [ ] (Optional) Run `python seed_horror_stories.py` locally and push the
      resulting `stories_cache.json` so the 12 horror entries land in
      production.
- [ ] (Optional) Populate `assets/music/<mood>/` via `python fetch_music.py`
      (needs `PIXABAY_KEY`). Until then, non-horror videos have no music.
- [ ] (Wait-and-see) Watch the cadence change for ~1 week. If views are
      lower not higher than the old 5/day cadence, revisit.

---

## How to operate

### Add background clips
1. https://github.com/hzisow/Youtube-Automation/releases/tag/assets-v1
2. **Edit release** → drag `.mp4` files in → **Update release**.
3. Done. Next run includes them in the random pick.

### Trigger a test run on demand
1. https://github.com/hzisow/Youtube-Automation/actions
2. **Daily Brainrot Videos** → **Run workflow** → **Run workflow**.
3. Manual runs skip both the dice and the random sleep.
4. Expand **Generate and upload** to see voice / horror / upload log lines.
   Expand **Fetch a random gameplay clip** to see which clip was picked.

### Swap voice engine back to Edge
Edit `.github/workflows/daily-brainrot.yml`:
```yaml
env:
  TTS_ENGINE: "edge"   # was "piper"
```

### Add more voices to the rotation pool
- Piper: edit `_VOICE_HF_PATHS` + `_DEFAULT_POOL` in `pipeline/piper_tts.py`.
- Edge: edit `_EDGE_DEFAULT_POOL` in `pipeline/tts.py`. Use
  `python preview_voices.py --list` to see all available, or
  `python preview_voices.py` to render MP3 samples of 16 curated ones.

### Add more horror stories
Edit the `STORIES` list in `seed_horror_stories.py`, re-run the script,
commit the updated `stories_cache.json`, push.

### Change cadence
Edit the `cron:` lines + the dice `THRESH` (currently 38) in the workflow.

### Refresh Reddit content
Hard on residential IPs — Reddit blocks. If it works:
```powershell
cd $HOME\vibecoding-projects\brainrot-pipeline
$env:REDDIT_CLIENT_ID = "..."
python refresh_stories.py
git add stories_cache.json; git commit -m "refresh stories"; git push
```

### Monitor uploads
- GitHub Actions: https://github.com/hzisow/Youtube-Automation/actions
- upload-post.com dashboard for delivery status to each platform.

---

## Architectural assumptions worth knowing

- **GitHub Actions:** unlimited minutes for public repos. Free tier
  runner = 7 GB RAM, no GPU, ~14 GB disk. This caps which TTS engines
  are feasible — rules out anything >10 GB.
- **upload-post.com:** the cron's single point of failure for uploads.
  If they go down, both platforms miss that day. Tolerable.
- **Cache lifetime:** `actions/cache@v4` keys with `tts-models-v1`.
  Bump to `-v2` to force re-download of Piper/Whisper models.
- **stories_cache.json is committed:** ~6,570 entries, several MB. Git
  history grows but acceptable.
- **used.json is auto-committed** by the workflow's final step. If a run
  dies before that step, the same story might re-render next run.
- **Clip release is public:** `browser_download_url` works without auth.
  The API call uses `${{ github.token }}` only to avoid rate limits.
- **`hash()` is not stable across Python processes** for str inputs when
  `PYTHONHASHSEED` is randomized (the default). So voice and bg_offset
  are stable *within* a run but may differ between runs for the same
  story. That's fine here — each story is only rendered once. Don't rely
  on `hash()` for anything that must reproduce across runs.

---

## Honest limits

- **TikTok daily active-user limit.** TikTok regularly refuses direct
  posting from upload-post and drops the video into the TikTok inbox as
  a draft, emailing "Action needed: your TikTok video is waiting in your
  inbox." This is a TikTok-side throttle on the app, not a bug in our
  code, and it can't be patched away from here. YouTube is unaffected.
- **YouTube algorithm 2026:** has publicly committed (Neal Mohan's Jan
  2026 letter) to suppress "AI slop" patterns — templated AI Reddit
  shorts are exactly that. The July 15 2025 "inauthentic content" policy
  explicitly names "channels that upload narrative stories with only
  superficial differences." We've layered countermeasures (Piper voice
  rotation, randomized cadence, clip rotation + seek offset, color
  grading, horror sub-treatment) but the niche is headwind, not tailwind.
- **Shorts freshness decay:** post-Sept-2025 the Shorts algorithm mostly
  only pushes videos in their first ~28–30 days. Flooding doesn't extend
  reach, it splits your own impression budget. That's the reasoning
  behind the cadence cut.
- **TikTok C2PA detection:** auto-flags AI-generated audio. Disclosing
  has 5–8% reach impact; failing to disclose carries removal risk.
  Disclosure protects you; hiding the AI is what hurts.
- **DST shifts:** US Eastern moves off EDT in November. ET-aligned cron
  comments will be off by an hour until adjusted.
- **Manual sound-pick advantage on TikTok:** giving up automation here
  was deliberate. Trending TikTok sounds boost reach a lot but require
  daily manual touch we explicitly don't want.
- **Realistic expectation:** most videos get very few views. The format
  is saturated and actively downranked. Code changes reduce the obvious
  "AI slop" fingerprints but don't reverse the platform-level headwind.

---

## Recent changes log

Newest first. Update this section every time you make a change.

- **2026-06-19** — STATUS.md expanded with the upload-post API reference,
  the docs/ folder audit, the dormant Google OAuth client details, the
  `hash()` stability caveat, and a note at the top telling future
  sessions to push via the GitHub MCP rather than patch files.
- **2026-06-19** — Multi-part stories now share one background start
  frame. The `bg_offset` seed moved from `slug` (unique per part) to
  `story["id"]` (shared), so Part 1 / Part 2 open on the same frame and
  read as a series. Commit `2fa8b80`.
- **2026-06-19** — Background clips now rotate automatically. Workflow
  queries the `assets-v1` release, filters `.mp4` assets with jq, and
  picks one at random per run (falls back to `GAMEPLAY_URL` if empty).
  Commit `523e218`. Plus `video.render()` gained a `bg_offset` param and
  `auto.py` wires it up — commit `fa397a6`. This restored a change
  requested earlier whose patch never landed.
- **2026-06-19** — Diagnosed "not uploading anymore": renders were fine,
  but the upload call logged nothing on success OR entry, so the logs
  were silent. Added request/response logging around the upload-post
  call. Commit `d66af67`. Root cause turned out to be TikTok's daily
  active-user limit pushing videos to the inbox as drafts.
- **2026-06-15** — Rewrote STATUS.md as a comprehensive single source of
  truth designed to survive chat compaction. Commit `d5b85ce`.
- **2026-06-15** — Removed leftover agency-dashboard files from main
  (Agency-Dashboard.html, leads-import.json, newton_leads.csv, and the
  agency-dashboard/ directory). Still safely in `hzisow/agency-dashboard`.
- **2026-06-15** — Added Piper TTS as a swappable open-source engine,
  set as default. Commit `5a11ac4`. Edge stays as fallback.
- **2026-06-15** — Changed cadence from 5 fixed-time crons/day to
  2 trigger windows + 38% dice + 0–180 min random sleep ≈ 3 posts per
  4 days at random times. Commit `50d98ec`.
- **2026-06-15** — Started pushing code changes directly via the GitHub
  MCP instead of sending patch files for manual `git am`. Much faster.
- **~2026-06-14** — Added 12 seeded horror stories
  (`seed_horror_stories.py`) since Reddit was blocking scraping.
- **~2026-06-14** — Wired horror story treatment: deep voice +
  `sounds/horror.mp3` ambient for nosleep/letsnotmeet subreddits.
- **~2026-06-14** — Added Inter font for cleaner title cards.
- **~2026-06-14** — Voice rotation per story (deterministic by id so
  parts 1/2/3 of a multi-part story share one voice).
- **~2026-06-14** — Color grading: cinematic (default) + horror preset.
- **~2026-06-14** — Added `r/nosleep` + `r/letsnotmeet` to subreddit pool.
- **~2026-06-12** — Swapped to upload-post.com for both YouTube +
  TikTok. Dropped 4 OAuth secrets, added 2. Killed the weekly YouTube
  re-auth dance and the TikTok production-audit requirement.
- **~2026-06-10** — Repo renamed. Default branch renamed to `main`.
  Other projects moved to their own repos.

---

## Troubleshooting quick reference

| Symptom | Likely cause | Fix |
|---|---|---|
| TikTok video in inbox, not posted | TikTok daily active-user limit | Finish in the TikTok app, or contact upload-post support |
| "No .mp4 assets found in release" in the log | `assets-v1` release has no video assets | Upload clips to the release, or set `GAMEPLAY_URL` |
| Every video has the same background | Only one `.mp4` in the release | Upload more clips |
| Part 1 and Part 2 look different | Shouldn't happen — offset is story-seeded | Check `_make_video` still uses `story["id"]` |
| Workflow fails at "Install Python deps" with piper-tts error | Piper package not installable | Switch `TTS_ENGINE: edge` in workflow |
| Piper voice download fails | HuggingFace down or rate-limited | Retry; cache survives partial failures |
| Whisper fallback hangs | Model not cached, slow download | First run only; cache handles the rest |
| All videos posted silent | TTS step failed; ffmpeg ran with no audio | Check "Generate and upload" log for synth errors |
| Wrong account on YouTube/TikTok | `UPLOADPOST_USER` mismatch | Verify the label spelling exactly |
| Captions misaligned with audio | Whisper transcription drifted | Try the next render |
| Cron stopped firing entirely | Repo inactive 60 days (GitHub disables crons) | Push any tiny commit |
| Workflow runs but uploads nothing | Dice rolled `should_post=false` | Expected; check the `dice` job log |
| Want an immediate post | — | Manual `workflow_dispatch` skips dice + sleep |
| Reddit 403 on `refresh_stories.py` | Reddit blocks residential IPs | Use `seed_*` scripts instead; app registration also fails |
