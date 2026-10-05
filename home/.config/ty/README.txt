TY / INTERNET ARCHIVE

  ty                       personal Archive feed
  ty search book of tea    search Archive audio, texts and films
  ty topics                toggle topics
  ty --list                print the feed and source links
  ty --refresh             update public searches
  ty --check               check local setup
  ty 'https://archive.org/details/ITEM'  open an Archive item

Enter opens a chapter/file menu. Audio streams one chapter at normal
speed, with mpv resume-on-quit; it never queues the next chapter.
Films use the existing 540-pixel-height, 24-fps mpv profile.
Public plain-text/OCR files open in a terminal reader; q returns.
Scanned pages, PDF-only items and unavailable streams show their item
information; Ctrl-O opens the original Archive page in Firefox.

Ctrl-L toggles a like, Ctrl-X hides an item, Ctrl-T changes topics,
Ctrl-R refreshes, Ctrl-W toggles row wrapping, Escape quits.
Type to filter; arrows move. Full reasons appear in wrapped rows.
Ctrl-O is optional and requires Firefox; normal browsing stays in the CLI.

Your artist bio, practice proposal, BR-900CD notes and design charter
seed print/books, photography/archives, experimental sound, typography,
minimal computing and Aotearoa creative scenes. Queries, evidence and
source links are editable in ~/.config/ty/interests.json.
Archive field recordings and experimental films are neighbouring
discoveries, rather than asserted favourite genres or artists.

Searches request eight popular results per enabled topic and cache public
metadata for 24 hours. Ranking uses your topic weights, bounded explicit
likes, diversity and a two-items-per-creator limit. Audio, text and film
are interleaved; after two video visits, text/audio moves to the top.
Opened text/film stays out for 21 days; audiobooks remain available so
you can choose another chapter. A player visit counts after 10 seconds
and successful exit; selecting an item does not imply liking it.

The starting audiobook is News from Nowhere by William Morris, read by
Elizabeth Klett. It is selected for craft/design exploration without
inferring political beliefs. Its catalogue and Archive files were checked:
https://librivox.org/news-from-nowhere-by-william-morris/
https://archive.org/details/newsfromnowhere_etk_librivox

Audio prefers 64-kbit MP3 chapters when available. Film selection lists
small streams first. Playback buffers are capped at 8 MiB forward and
2 MiB backward, with a 20-second prefetch target. One file opens at a
time; there is no bulk download.
Plain-text reader requests are capped at 8 MiB; larger text is available
from the item page. Restricted items are omitted from public searches
and direct item access reports restrictions without attempting access.

Interests: ~/.config/ty/interests.json
Local likes/hides/visits: ~/.local/state/ty/feedback.json
Public caches: ~/.cache/ty/
Files are created private (600), new directories 700. Personal documents
are not uploaded; only generic Archive topic queries are sent. Account
cookies are not used. Failed requests pause 15 minutes; Ctrl-R retries.

The CLI command is ty. ~/.local/bin is already in your zsh login PATH;
no shell alias, echo command or sudo installation is necessary.
The original yt URL-only mpv launcher remains separately available.
The former mixed YouTube/Reddit feed is no longer the default command.
No signed-in account settings or histories have been changed.

Design follows the STBL3 charter and current SluntShack palette:
black/white neutral data, grey supporting text, orange current selection
with black text, square geometry. Media and reasons are named in text.

Backup location: ~/.config/ty/installation.json. Its restore.py checks
file hashes before restoring previous commands and removing new config;
it preserves feedback/cache and refuses to overwrite later changes.
