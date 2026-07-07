# YouTube Extraction

All extraction is handled by `scripts/fetch_youtube.py`.
It fetches the title (oEmbed), fetches the transcript (captions API),
parses the WebVTT karaoke format, and saves both files to `knowledge/raw/transcripts/`.

---

## Run the pipeline

```bash
python .claude/skills/insight-extractor/scripts/fetch_youtube.py "<VIDEO_URL>"
```

Example output (stdout):
```
Title:       The Lean Startup Explained
Video ID:    dQw4w9WgXcQ
Language:    en
Words:       ~14,500
VTT file:    knowledge/raw/transcripts/dQw4w9WgXcQ.vtt
Transcript:  knowledge/raw/transcripts/dQw4w9WgXcQ.txt
```

---

## After the script completes

- Use the **Title** field from stdout to derive the insight file's slug.
- Read `knowledge/raw/transcripts/<videoID>.txt` as the content for insight generation.
  The file begins with `TITLE: <title>` followed by the clean transcript.

---

## Failures

| Symptom | Cause | Fix |
|---|---|---|
| `No captions returned` | Video has no captions or they're disabled | No workaround — skip this video |
| `HTTP Error 403` on oEmbed | Private/unlisted video | Title unavailable; derive slug from URL |
| Network timeout | Connectivity issue | Retry; check internet connection |

---

## Insight guidance for YouTube

- Preserve speaker voice in direct quotes (`_"..."_`).
- Note video format in metadata (talk / interview / tutorial / panel).
- Timestamps are not available in the cleaned transcript — attribute quotes to speaker name only.
- For long videos (1h+), the transcript is dense; focus on the most idea-rich segments.
