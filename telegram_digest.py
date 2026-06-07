#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram digests based on scored papers
#

import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from outputs.telegram import TelegramPublisher
from papersbot import PapersBot


MADRID_TZ = ZoneInfo("Europe/Madrid")
DIGEST_CONFIG = {
    "weekly": {
        "title": "🧪 Top papers de la semana",
        "weekday": 3,
        "lookback_days": 7,
        "default_top_n": 10,
        "config_key": "weekly_digest",
        "pin": True,
    },
    "daily": {
        "title": "🧪 Papers destacados del día",
        "weekday": None,
        "lookback_days": 1,
        "default_top_n": 5,
        "config_key": "daily_digest",
        "pin": False,
    },
}


def should_send_now(cadence, now=None):
    now = now or datetime.now(MADRID_TZ)
    config = DIGEST_CONFIG[cadence]
    if config["weekday"] is not None and now.weekday() != config["weekday"]:
        return False
    return now.hour == 20


def parse_message_datetime(message):
    published_at = message.get("published_at")
    if not published_at:
        return None
    try:
        return datetime.fromisoformat(published_at)
    except ValueError:
        return None


def filter_recent_messages(messages, cadence, now=None):
    now = now or datetime.now(MADRID_TZ)
    threshold = now.astimezone(ZoneInfo("UTC")) - timedelta(days=DIGEST_CONFIG[cadence]["lookback_days"])
    recent = []

    for message in messages:
        message_dt = parse_message_datetime(message)
        if message_dt is None or message_dt >= threshold:
            recent.append(message)

    return recent


def build_digest_text(messages, top_n, cadence):
    title = DIGEST_CONFIG[cadence]["title"]
    lines = [
        title,
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
    parser.add_argument("--cadence", choices=sorted(DIGEST_CONFIG.keys()), required=True)
    parser.add_argument("--force", action="store_true", help="Send digest regardless of current Europe/Madrid time")
    args = parser.parse_args()

    if not args.force and not should_send_now(args.cadence):
        print(f"Skipping {args.cadence} digest because it is not the configured send time in Europe/Madrid.")
        return

    bot = PapersBot(dry_run=True)
    config = bot.config
    digest_cfg = DIGEST_CONFIG[args.cadence]
    cadence_config = config.get(digest_cfg["config_key"], {}) if isinstance(config, dict) else {}
    top_n = cadence_config.get("top_n", digest_cfg["default_top_n"])
    telegram_config = config.get("telegram", {}) if isinstance(config, dict) else {}
    pin_weekly_summary = telegram_config.get("pin_weekly_summary", False)

    messages = bot.get_candidate_messages(exclude_posted=False)
    recent_messages = filter_recent_messages(messages, args.cadence)
    ranked_messages = bot.sort_messages_by_score(recent_messages)[:top_n]

    if not ranked_messages:
        print(f"No {args.cadence} digest candidates found.")
        return

    publisher = TelegramPublisher(config)
    result = publisher.publish_text(build_digest_text(ranked_messages, top_n, args.cadence))
    message_id = result.get("message_id") if isinstance(result, dict) else None

    if args.cadence == "weekly" and digest_cfg["pin"] and pin_weekly_summary and message_id is not None:
        publisher.pin_message(message_id)


if __name__ == "__main__":
    main()
