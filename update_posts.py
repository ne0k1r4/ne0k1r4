#!/usr/bin/env python3
"""
update_posts.py – Fetch the latest writeups/posts from ctf5.vercel.app
and update the BLOG_RSS_START … BLOG_RSS_END block in README.md.
"""

import re
import urllib.request

HTML_URL = "https://ctf5.vercel.app/"
README = "README.md"
MAX_POSTS = 10
ICON = "🦋"
START_TAG = "<!-- BLOG_RSS_START -->"
END_TAG = "<!-- BLOG_RSS_END -->"


def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def build_block(items: list[tuple]) -> str:
    lines = [START_TAG]
    for title, link in items:
        # Strip any formatting/asterisks from title to prevent markdown collision
        clean_title = title.replace("***", "").strip()
        lines.append(f"- {ICON} [***{clean_title}***]({link})")
    lines.append(END_TAG)
    return "\n".join(lines)


def update_readme(new_block: str) -> None:
    with open(README, "r", encoding="utf-8") as fh:
        content = fh.read()

    pattern = re.compile(
        rf"{re.escape(START_TAG)}.*?{re.escape(END_TAG)}",
        re.DOTALL,
    )

    if pattern.search(content):
        updated = pattern.sub(new_block, content)
    else:
        raise RuntimeError(
            f"Markers {START_TAG!r} / {END_TAG!r} not found in {README}."
        )
    with open(README, "w", encoding="utf-8") as fh:
        fh.write(updated)


def main() -> None:
    # 1. Fetch homepage HTML to find the JS bundle asset path
    html = fetch_url(HTML_URL)
    js_match = re.search(r'src="(/assets/index-[^"]+\.js)"', html)
    if not js_match:
        raise RuntimeError("Could not find index.js asset in the homepage HTML.")

    js_url = "https://ctf5.vercel.app" + js_match.group(1)
    print(f"Found JS bundle URL: {js_url}")

    # 2. Fetch the JS bundle content
    js_content = fetch_url(js_url)

    # 3. Parse all posts of the form: {"title":"...","link":"https://blog.light.my.id/posts/..."}
    # (Matches what's compiled in the React/Vite client-side bundle)
    pattern = r'\{"title"\s*:\s*"([^"]+)"\s*,\s*"link"\s*:\s*"([^"]+)"'
    matches = re.findall(pattern, js_content)
    
    # 4. Map links to ctf5.vercel.app
    posts = []
    for title, link in matches:
        ctf5_link = link.replace("https://blog.light.my.id", "https://ctf5.vercel.app")
        posts.append((title, ctf5_link))

    if not posts:
        raise RuntimeError("No posts found in the JS bundle.")

    print(f"Parsed {len(posts)} posts. Formatting top {MAX_POSTS}...")

    # 5. Build block and update README
    block = build_block(posts[:MAX_POSTS])
    update_readme(block)
    print(f"✅ Successfully updated {README} with latest posts.")


if __name__ == "__main__":
    main()
