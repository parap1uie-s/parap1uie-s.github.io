#!/usr/bin/env python3
"""Update Google Scholar metrics in index.html.

This script is intentionally dependency-free so it can run in GitHub Actions
without installing packages.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCHOLAR_URL = (
    "https://scholar.google.com.hk/citations?"
    "hl=en&oe=ASCII&user=2GMoPpwAAAAJ&view_op=list_works&sortby=pubdate"
)


def fetch_scholar_html() -> str:
    request = urllib.request.Request(
        SCHOLAR_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("ISO-8859-1", errors="replace")


def parse_metrics(html: str) -> tuple[str, str, str]:
    values = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
    if len(values) < 5:
        raise ValueError("Could not find Scholar metrics in downloaded HTML.")

    citations = values[0]
    h_index = values[2]
    i10_index = values[4]
    return citations, h_index, i10_index


def update_index(index_path: Path, metrics: tuple[str, str, str]) -> bool:
    citations, h_index, i10_index = metrics
    html = index_path.read_text(encoding="utf-8")
    snapshot_date = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%B %d, %Y")
    snapshot_date = snapshot_date.replace(" 0", " ")

    updated, substitutions = re.subn(
        r'(<section class="stats" aria-label="Google Scholar metrics">\s*)'
        r'<div><b>\d+</b><span>Citations</span></div>\s*'
        r'<div><b>\d+</b><span>h-index</span></div>\s*'
        r'<div><b>\d+</b><span>i10-index</span></div>\s*'
        r"<p>[^<]*</p>",
        (
            r"\1"
            f"<div><b>{citations}</b><span>Citations</span></div>\n"
            f"      <div><b>{h_index}</b><span>h-index</span></div>\n"
            f"      <div><b>{i10_index}</b><span>i10-index</span></div>\n"
            f"      <p>Google Scholar snapshot, {snapshot_date}. Metrics and links can be updated manually.</p>"
        ),
        html,
        count=1,
        flags=re.S,
    )
    if substitutions != 1:
        raise ValueError("Could not locate the metrics block in index.html.")

    if updated != html:
        index_path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="index.html", help="Path to index.html")
    args = parser.parse_args()

    index_path = Path(args.index)
    metrics = parse_metrics(fetch_scholar_html())
    changed = update_index(index_path, metrics)
    print(
        f"Scholar metrics: citations={metrics[0]}, h-index={metrics[1]}, "
        f"i10-index={metrics[2]}, changed={changed}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
