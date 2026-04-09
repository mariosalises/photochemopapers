#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Apply the Bluesky self-label "bot" to the current profile
#

import os
import sys

from outputs.bluesky import BlueskyPublisher


def main():
    username = os.environ.get("BLUESKY_USERNAME")
    password = os.environ.get("BLUESKY_PASSWORD")

    if not username or not password:
        print(
            "Bluesky credentials are required. Set BLUESKY_USERNAME and BLUESKY_PASSWORD in the environment.",
            file=sys.stderr,
        )
        return 1

    try:
        labels = BlueskyPublisher.apply_bot_self_label(username, password)
    except Exception as exc:
        print(f"Failed to apply Bluesky bot self-label: {exc}", file=sys.stderr)
        return 1

    print(f"Applied Bluesky self-labels: {', '.join(labels)}")
    print(BlueskyPublisher.bot_profile_disclosure_note())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
