#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import os
import random
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

README_PATH = Path("README.md")
MEDIUM_USERNAME = "johnny31258"
POST_COUNT = 3
START_MARKER = "<!-- MEDIUM_POSTS_START -->"
END_MARKER = "<!-- MEDIUM_POSTS_END -->"


def fetch_medium_posts(username: str) -> list[tuple[str, str]]:
    feed_url = f"https://medium.com/feed/@{username}"
    request = urllib.request.Request(
        feed_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; GitHubActions/1.0)",
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    posts: list[tuple[str, str]] = []
    seen_links: set[str] = set()

    for item in root.findall(".//item"):
        title_node = item.find("title")
        link_node = item.find("link")

        if title_node is None or link_node is None:
            continue

        title = (title_node.text or "").strip()
        link = (link_node.text or "").strip()
        if not title or not link or link in seen_links:
            continue

        seen_links.add(link)
        posts.append((title, link))

    return posts


def make_post_block(username: str, posts: list[tuple[str, str]], count: int) -> str:
    if not posts:
        return "<p align=\"center\">No Medium posts found.</p>"

    if count <= 0:
        return "<p>No Medium posts configured.</p>"

    total_cards = min(count, len(posts))
    latest_index = 0
    random_needed = max(0, total_cards - 1)

    candidate_indices = list(range(1, len(posts)))
    seed = os.getenv("MEDIUM_RANDOM_SEED", dt.date.today().isoformat())
    rng = random.Random(seed)
    random_indices = (
        rng.sample(candidate_indices, k=min(random_needed, len(candidate_indices)))
        if candidate_indices
        else []
    )

    chosen_indices = [latest_index, *random_indices]

    lines = ["<p align=\"center\">"]
    for order, index in enumerate(chosen_indices, start=1):
        _, link = posts[index]
        card_src = f"https://github-readme-medium-recent-article.vercel.app/medium/@{username}/{index}"
        label = "Latest Medium Article" if index == latest_index else f"Random Medium Article {order - 1}"
        lines.append(f"  <a target=\"_blank\" href=\"{link}\">")
        lines.append(f"    <img src=\"{card_src}\" alt=\"{label}\" />")
        lines.append("  </a>")
    lines.append("</p>")

    return "\n".join(lines)


def update_readme(content: str, block: str) -> str:
    pattern = re.compile(
        rf"({re.escape(START_MARKER)}\n)([\s\S]*?)(\n{re.escape(END_MARKER)})"
    )

    if not pattern.search(content):
        raise RuntimeError("README markers not found.")

    return pattern.sub(rf"\1{block}\3", content)


def main() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    try:
        posts = fetch_medium_posts(MEDIUM_USERNAME)
    except Exception as error:
        print(f"Skip update: failed to fetch Medium feed ({error})")
        return

    block = make_post_block(MEDIUM_USERNAME, posts, POST_COUNT)
    new_text = update_readme(readme_text, block)

    if new_text != readme_text:
        README_PATH.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
