# Demo recording helper for TikTok app review.
# Start screen recording (Win+G -> record), then run:
#   .\record-demo.ps1
# It runs the live auto.py with Direct Post and prints clear step labels.

$Host.UI.RawUI.WindowTitle = "RedditStories Uploader - TikTok Direct Post Demo"
function Banner($n, $text) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ("  STEP $n  :  $text") -ForegroundColor Yellow
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
}

Banner 1 "Run the desktop tool (Content Posting API: video.publish)"
Write-Host "Command:  python auto.py --count 1 --tiktok --tiktok-mode direct"
Write-Host ""

python auto.py --count 1 --tiktok --tiktok-mode direct

Banner 2 "Open the TikTok app on your phone and show the video on the profile"
Write-Host "(Switch to your phone screen for the next ~5 seconds.)"
