#!/usr/bin/env python3
"""Publish a carousel (or single image) to @seoyun.dailylook via the Graph API.

The access token is injected by the environment's network secret for
graph.facebook.com, so it never appears here.

Usage:
  python3 tools/publish.py posts/<name>            # dry run: checks URLs, shows the plan
  python3 tools/publish.py posts/<name> --yes      # publish (only after the user approved)
Reads posts/<name>/slides/*.jpg and posts/<name>/caption.txt.
Images must already be pushed to main (the API fetches them from raw.githubusercontent.com).
"""
import glob, json, os, sys, time, urllib.parse, urllib.request

IG_USER = "17841471317374785"
GRAPH = "https://graph.facebook.com"
RAW = "https://raw.githubusercontent.com/seoyundailylook/seoyun-instagram/main/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def call(method, path, **params):
    data = urllib.parse.urlencode(params).encode() if method == "POST" else None
    url = f"{GRAPH}/{path}" + ("" if method == "POST" or not params else "?" + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API error {e.code} on {path}: {e.read().decode()[:500]}")

def wait_ready(cid):
    for _ in range(30):
        st = call("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container {cid} status {st}")
        time.sleep(2)
    raise SystemExit(f"container {cid} not ready")

def main():
    post = sys.argv[1].rstrip("/")
    go = "--yes" in sys.argv
    slides = sorted(glob.glob(os.path.join(ROOT, post, "slides", "*.jpg")))
    caption = open(os.path.join(ROOT, post, "caption.txt"), encoding="utf-8").read().strip()
    urls = [RAW + os.path.relpath(p, ROOT) for p in slides]
    if not 1 <= len(urls) <= 20:
        raise SystemExit(f"need 1-20 slides, found {len(urls)}")
    for u in urls:
        with urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=30) as r:
            if r.status != 200:
                raise SystemExit(f"not reachable: {u}")
    limit = call("GET", f"{IG_USER}/content_publishing_limit", fields="quota_usage,config")
    print(f"{len(urls)} slide(s), caption {len(caption)} chars, publishing quota: {json.dumps(limit.get('data'))}")
    if not go:
        print("DRY RUN. Add --yes to publish.")
        return
    if len(urls) == 1:
        cid = call("POST", f"{IG_USER}/media", image_url=urls[0], caption=caption)["id"]
    else:
        kids = []
        for u in urls:
            kids.append(call("POST", f"{IG_USER}/media", image_url=u, is_carousel_item="true")["id"])
        for k in kids:
            wait_ready(k)
        cid = call("POST", f"{IG_USER}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)["id"]
    wait_ready(cid)
    media_id = call("POST", f"{IG_USER}/media_publish", creation_id=cid)["id"]
    link = call("GET", media_id, fields="permalink").get("permalink")
    print(f"PUBLISHED {media_id} {link}")
    with open(os.path.join(ROOT, post, "published.json"), "w", encoding="utf-8") as fh:
        json.dump({"media_id": media_id, "permalink": link, "published_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, fh, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
