#!/usr/bin/env python3
"""Blogger API v3 helper for Hermes Agent.

Commands:
  blogger.py blog-id --url URL            # resolve blog id from blog URL
  blogger.py blogs                        # list all blogs you can post to
  blogger.py post --blog-url URL --title T --body B [--draft] [--labels "a,b"]
  blogger.py list --blog-url URL --max N

All commands print JSON to stdout.
"""

import argparse
import json
import sys
from pathlib import Path

# Reuse the google-workspace dependency + token location.
import os
_HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
_WS_SCRIPTS = _HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts"
sys.path.insert(0, str(_WS_SCRIPTS))

from _hermes_home import get_hermes_home  # noqa: E402

TOKEN_PATH = get_hermes_home() / "google_token.json"

BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"


def _service():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    if not TOKEN_PATH.exists():
        print(json.dumps({"error": "NOT_AUTHENTICATED: run setup.py --check / --auth-url first"}))
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), [BLOGGER_SCOPE])
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        TOKEN_PATH.write_text(json.dumps(json.loads(creds.to_json()), indent=2), encoding="utf-8")
    return build("blogger", "v3", credentials=creds)


def _blog_id_from_url(url: str) -> str:
    svc = _service()
    # Try direct fetch by url.
    resp = svc.blogs().getByUrl(url=url).execute()
    return resp["id"]


def cmd_blog_id(args):
    bid = _blog_id_from_url(args.url)
    print(json.dumps({"blogId": bid}))


def cmd_blogs(args):
    svc = _service()
    resp = svc.blogs().listByUser(userId="self").execute()
    items = [
        {"id": b["id"], "name": b["name"], "url": b.get("url")}
        for b in resp.get("items", [])
    ]
    print(json.dumps(items, indent=2))


def cmd_post(args):
    svc = _service()
    bid = _blog_id_from_url(args.blog_url)
    body = {
        "kind": "blogger#post",
        "blog": {"id": bid},
        "title": args.title,
        "content": args.body,
    }
    if args.labels:
        body["labels"] = [l.strip() for l in args.labels.split(",") if l.strip()]

    if args.draft:
        body["isDraft"] = True

    resp = svc.posts().insert(blogId=bid, body=body, isDraft=bool(args.draft)).execute()
    out = {
        "status": "drafted" if args.draft else "published",
        "id": resp.get("id"),
        "title": resp.get("title"),
        "url": resp.get("url"),
    }
    print(json.dumps(out, indent=2))


def cmd_list(args):
    svc = _service()
    bid = _blog_id_from_url(args.blog_url)
    resp = svc.posts().list(blogId=bid, maxResults=args.max).execute()
    items = [
        {"id": p["id"], "title": p["title"], "url": p.get("url"), "published": p.get("published")}
        for p in resp.get("items", [])
    ]
    print(json.dumps(items, indent=2))


def main():
    p = argparse.ArgumentParser(description="Blogger API helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("blog-id")
    b.add_argument("--url", required=True)
    b.set_defaults(func=cmd_blog_id)

    bl = sub.add_parser("blogs")
    bl.set_defaults(func=cmd_blogs)

    po = sub.add_parser("post")
    po.add_argument("--blog-url", required=True)
    po.add_argument("--title", required=True)
    po.add_argument("--body", required=True)
    po.add_argument("--draft", action="store_true")
    po.add_argument("--labels", default="")
    po.set_defaults(func=cmd_post)

    li = sub.add_parser("list")
    li.add_argument("--blog-url", required=True)
    li.add_argument("--max", type=int, default=5)
    li.set_defaults(func=cmd_list)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
