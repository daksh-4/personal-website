#!/usr/bin/env python3
"""
Rebuilds the "Recently updated" list on index.html from the git history.

An entry is created for:
  - the commit that first added an essay page            ("New essay")
  - every commit whose message starts with "publish:"    (a revision; the
    rest of the message becomes the note shown next to it)

Only essays listed in essays.json are included, so unlisted pages (such as
the MCQ answers) never appear. An essay contributes at most MAX_PER_ESSAY
entries, so a page that changes often cannot crowd out the rest. A commit that touches more than
MAX_PAGES_PER_COMMIT essay pages is treated as a site-wide change (a template
fix, a bulk import) and skipped, so it cannot flood the list.

The list is written as static HTML between the UPDATES markers in index.html,
so the home page needs no JavaScript and makes no API calls.

Usage:  python3 update_feed.py            rewrite index.html
        python3 update_feed.py --dry-run  print the entries, change nothing

publish.py runs this after every publish. A revision only shows up once its
"publish:" commit exists, so the newest one appears the next time this runs.
"""

import html
import json
import re
import subprocess
import sys
from datetime import datetime

LIMIT = 6
MAX_PER_ESSAY = 2
MAX_PAGES_PER_COMMIT = 3
INDEX = "index.html"
START, END = "<!-- UPDATES-START -->", "<!-- UPDATES-END -->"


def git_history():
    """Newest-first list of (date, subject, [(status, path), ...]) for essay pages."""
    out = subprocess.check_output(
        ["git", "log", "--format=%x1e%aI%x1f%s", "--name-status", "--no-renames",
         "--", "essays/*.html"],
        text=True,
    )
    commits = []
    for record in out.split("\x1e"):
        if not record.strip():
            continue
        header, _, body = record.partition("\n")
        date, _, subject = header.partition("\x1f")
        files = []
        for line in body.splitlines():
            parts = line.split("\t")
            if len(parts) == 2 and parts[0] in ("A", "M"):
                files.append((parts[0], parts[1]))
        commits.append((datetime.fromisoformat(date), subject.strip(), files))
    return commits


def clean_note(subject, title):
    """Strip the publish: prefix; drop notes that just repeat the essay title."""
    note = re.sub(r"^publish:\s*", "", subject, flags=re.IGNORECASE).strip()
    if not note:
        return ""
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    if norm(note) == norm(title):
        return ""
    return note[0].upper() + note[1:]


def build_entries(listed):
    commits = git_history()

    # The oldest commit that added each page is its "new essay" event.
    first_added = {}
    for i in range(len(commits) - 1, -1, -1):
        for status, path in commits[i][2]:
            if status == "A" and path in listed:
                first_added.setdefault(path, i)

    entries = []
    for i, (date, subject, files) in enumerate(commits):
        pages = [p for _, p in files if p in listed]
        if not pages or len(pages) > MAX_PAGES_PER_COMMIT:
            continue
        is_publish = subject.lower().startswith("publish:")
        for status, path in files:
            if path not in listed:
                continue
            is_new = first_added.get(path) == i
            if not (is_new or (is_publish and status == "M")):
                continue
            title = listed[path]
            note = clean_note(subject, title) if is_publish else ""
            entries.append({"date": date, "url": path, "title": title,
                            "new": is_new, "note": note})
    entries.sort(key=lambda e: e["date"], reverse=True)

    # A page that is updated often (the MCQs) must not push every other essay
    # off the list, so keep only its most recent MAX_PER_ESSAY entries.
    # An essay's "New essay" line is redundant once a later revision of it is
    # already showing, so it is dropped in that case.
    kept, per_essay = [], {}
    for e in entries:
        n = per_essay.get(e["url"], 0)
        if n >= MAX_PER_ESSAY or (e["new"] and n > 0):
            continue
        per_essay[e["url"]] = n + 1
        kept.append(e)
    return kept[:LIMIT]


def render(entries):
    if not entries:
        return ""
    items = []
    for e in entries:
        # "Title (new essay)", "Title: the note", or "Title (revised)".
        if e["new"]:
            tail = " (new essay)" + (f": {e['note']}" if e["note"] else "")
        else:
            tail = f": {e['note']}" if e["note"] else " (revised)"
        items.append(
            "                <li>"
            f"<span class=\"update-date\">{e['date'].day} {e['date']:%b %Y}</span>"
            f"<span class=\"update-text\"><a href=\"{html.escape(e['url'])}\">{html.escape(e['title'], quote=False)}</a>"
            f"<span class=\"update-note\">{html.escape(tail, quote=False)}</span></span>"
            "</li>"
        )
    return (
        "<div class=\"updates\">\n"
        "            <strong>Recently updated:</strong>\n"
        "            <ul>\n" + "\n".join(items) + "\n            </ul>\n"
        "        </div>"
    )


def main():
    dry_run = "--dry-run" in sys.argv
    try:
        listed = {f"{e['url']}": e["title"] for e in json.load(open("essays.json", encoding="utf-8"))}
        entries = build_entries(listed)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as err:
        print(f"  feed not updated: {err}")
        return

    if dry_run:
        for e in entries:
            kind = "new" if e["new"] else "rev"
            print(f"{e['date']:%Y-%m-%d}  {kind}  {e['title']}  |  {e['note']}")
        return

    with open(INDEX, encoding="utf-8") as f:
        page = f.read()
    if START not in page or END not in page:
        print(f"  feed not updated: markers missing from {INDEX}")
        return
    block = f"{START}\n        {render(entries)}\n        {END}"
    updated = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, page, flags=re.DOTALL)
    if updated != page:
        with open(INDEX, "w", encoding="utf-8") as f:
            f.write(updated)
    print(f"✓ Updated recent changes on {INDEX} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
