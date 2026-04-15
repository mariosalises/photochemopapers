#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Weekly Telegram digest with top-scored papers
#

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from outputs.telegram import TelegramPublisher
from papersbot import PapersBot


MADRID_TZ = ZoneInfo("Europe/Madrid")


def should_send_now(now=None):
    now = now or datetime.now(MADRID_TZ)
    return now.weekday() == 3 and now.hour == 20


def build_digest_text(messages, top_n):
    lines = [
        "🧪 Top papers de la semana",
        "",
        f"Selección automática según el scoring actual. Top {len(messages)}:",
    ]

    for index, message in enumerate(messages[:top_n], start=1):
        lines.extend(
            [
                "",
                f"{index}. {message['title']}",
            ]
        )
        if message.get("source"):
            lines.append(f"📖 {message['source']}")
        lines.append(f"🔗 {message['link']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Send digest regardless of current Europe/Madrid time")
    args = parser.parse_args()

    if not args.force and not should_send_now():
        print("Skipping weekly digest because it is not 20:00 Thursday in Europe/Madrid.")
        return

    bot = PapersBot(dry_run=True)
    config = bot.config
    weekly_config = config.get("weekly_digest", {}) if isinstance(config, dict) else {}
    top_n = weekly_config.get("top_n", 10)

    messages = bot.get_candidate_messages(exclude_posted=False)
    ranked_messages = bot.sort_messages_by_score(messages)[:top_n]

    if not ranked_messages:
        print("No weekly digest candidates found.")
        return

    publisher = TelegramPublisher(config)
    publisher.publish_text(build_digest_text(ranked_messages, top_n))


if __name__ == "__main__":
    main()
