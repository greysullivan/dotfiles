GREY / PERSONAL FEED

Run yt to browse. No account or browser is needed for the main feed.

  yt                  mixed personal feed
  yt search xerox art public YouTube search, without changing your interests
  yt topics           toggle topics; Escape returns to the feed
  yt --list           print recommendations and links
  yt --refresh        fetch fresh public results
  yt --check          check local dependencies and configuration
  yt 'YOUTUBE_URL'    existing direct mpv playback

MENU
  Type to filter; arrows move.
  Enter opens a video, Reddit reader, or audiobook chapter menu.
  Ctrl-L toggles an explicit like. A liked marker appears beside the item.
  Ctrl-X hides that individual item from future recommendations.
  Ctrl-T toggles topic interests; Ctrl-R refreshes sources.
  Ctrl-O opens the selected source page in Firefox when desired.
  Escape quits. In the Reddit reader, q returns to the feed.

Videos use your existing 540-pixel-high / 24-fps mpv profile at normal
speed and pitch. After playback, the feed returns; it never autoplays.
Audiobooks stream one chapter at a time in mpv without video, at normal
speed, with mpv's saved-position-on-quit support. Choose a chapter when
returning to a book. Playback keys: space pause, arrows seek, q quit.

WHY THESE INTERESTS
Your artist bio, practice proposal and BR-900CD notes seed books/zines,
experimental printing, photography and archives, Christchurch creative
scenes and unusual guitar effects. The charter and local UX philosophy
seed typography, restrained interfaces and minimal Unix/i3 computing.
Each topic has an evidence note and source link in interests.json.
Music genres and favourite artists are not assumed from these documents.

William Morris's News from Nowhere is an exploratory audiobook pick
about making and everyday life; this does not infer political beliefs.
LibriVox's original catalogue links to the verified Internet Archive item:
https://librivox.org/news-from-nowhere-by-william-morris/
https://archive.org/details/newsfromnowhere_etk_librivox

REDDIT
Communities: r/zines, r/bookbinding, r/Photobooks, r/guitarpedals and
r/unixporn. The feed requests top-of-month public posts. It tries JSON
then the public RSS feed. Reddit can block anonymous JSON: RSS still
supplies titles and links but not vote counts or full comments.
Enter shows available post text and attempts to fetch the top comments;
Ctrl-O opens the original page in Firefox if the reader cannot fetch it.
Image posts list their source links; the terminal does not render images.

If both live routes fail, cached results or a small curated set of real
popular posts remain available. Curated posts, their publication dates,
and votes observed on 2026-10-05 are explicitly labelled. They are not
represented as current top-of-month results. Curated links were checked:
https://www.reddit.com/r/zines/comments/1vq1kdh/
https://www.reddit.com/r/bookbinding/comments/1jen35i/
https://www.reddit.com/r/Photobooks/comments/1vym0y8/
https://www.reddit.com/r/guitarpedals/comments/yhb8uk/
https://www.reddit.com/r/unixporn/comments/1j2mq5i/

HOW THE LOCAL ALGORITHM WORKS
Topics carry editable starting weights and rotating daily public-search
queries. Each topic requests eight flat YouTube search results; this
avoids extracting or downloading every video. Topics remain diverse,
duplicate videos collapse, and a channel contributes at most two items.
Explicit likes raise a topic's weight by 15% each, capped at five likes.
Selecting a video never implies liking it. Hiding removes only that item.

The list alternates two videos, a post, a video, an audiobook, a video,
and another post where those media are available. After two completed
video visits, reading/listening moves to the beginning of the next menu.
This invites a break; you still choose what opens. Closing a player within
10 seconds, or a failed launch, does not count as a completed visit.
Opened videos/posts stay out of the feed for 21 days. Audiobooks remain
available so another chapter can be chosen. Escape never clears feedback.

PRIVACY AND FILES
  ~/.config/yt/interests.json      topics, queries and provenance
  ~/.local/state/yt/feedback.json  explicit likes, hides and visits
  ~/.cache/yt/                    public search/feed caches (24 hours)

Personal source documents are not uploaded. Only generic topic queries
are sent to public YouTube searches. Public Reddit/Archive requests do
not use account cookies. Feedback and private interests stay on this
machine, with files created as mode 600 and directories as mode 700.
Corrupt state/config files are reported and preserved for repair.

This shapes your local CLI recommendations. It does not change signed-in
YouTube history, subscriptions or recommendations. Opening a YouTube page
in Firefox uses your existing browser session and may affect that account
normally. Account cleanup can be handled separately if you request it.

Edit interests.json for weights, queries, communities or audiobook IDs.
Set reddit_enabled or audio_enabled to false to omit those media. Remove
an ID from feedback.json's hidden list to unhide it; preserve JSON syntax.
Caches work offline after the first fetch; Ctrl-R reports failures and
keeps previously successful public results. Failed requests pause for
15 minutes to avoid repeatedly hitting rate limits; Ctrl-R overrides the
pause. Audiobooks use the available 64-kbit MP3 chapter files to reduce
bandwidth, falling back to other original MP3 files when needed.
No new dependencies or sudo
are required beyond the tools already installed on this machine.

DESIGN
The interface follows the STBL3 charter and current SluntShack colour
roles: black/white neutral content, grey metadata, orange selection with
black text, no decorative media-category colours, square/no borders.
Text labels (VIDEO/POST/AUDIO, why, liked) explain meaning without hue.

RESTORE
The installation backup directory is recorded in installation.json.
Run its restore.py to restore the original URL-only yt command and remove
the new config/docs if they have not subsequently changed. It first
checks hashes and refuses to overwrite your later edits. Feedback and
cached public data remain available. Restore this feed before using the
older youtube-art backup, because both versions track the yt launcher.
