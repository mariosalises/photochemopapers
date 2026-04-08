#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PapersBot - Refactored
# Modular system for RSS-based paper alerts
#

import os
import random
import sys
import time
import yaml

from sources.rss_reader import RSSReader
from filters.keyword_filter import KeywordFilter
from storage.deduplicator import Deduplicator
from outputs.console import ConsolePublisher
from outputs.twitter_x import TwitterPublisher
from outputs.whatsapp import WhatsAppPublisher
from outputs.telegram import TelegramPublisher
from outputs.email import EmailPublisher


def read_feeds_list():
    with open("feeds.txt", "r") as f:
        feeds = [s.partition("#")[0].strip() for s in f]
        return [s for s in feeds if s]


def clean_text(s):
    import re
    from bs4 import BeautifulSoup
    s = s.replace("[ASAP]", "").replace("\x0A", "")
    s = re.sub(r"\(arXiv:.+\)", "", s)
    return re.sub(r"\s\s+", " ", s).strip()


class PapersBot:
    def __init__(self, dry_run=True, outputs=None, test_telegram=False):
        self.feeds = read_feeds_list()
        self.dry_run = dry_run
        self.test_telegram = test_telegram

        # Load config
        try:
            with open("config.yml", "r") as f:
                config = yaml.safe_load(f)
        except OSError:
            config = {}

        self.throttle = 1 if self.test_telegram else config.get("throttle", 0)  # Limit to 1 for test
        self.wait_time = config.get("wait_time", 5)
        self.shuffle_feeds = config.get("shuffle_feeds", True)
        self.blacklist = config.get("blacklist", [])
        self.blacklist = [__import__('re').compile(s) for s in self.blacklist]
        # Exclude unwanted publication types
        self.exclude_patterns = [
            __import__('re').compile(r'\b(?:Author Correction|Publisher Correction|Corrigendum|Erratum|Retraction)\b', __import__('re').IGNORECASE)
        ]

        # Initialize modules
        self.reader = RSSReader(self.feeds)
        self.filter = KeywordFilter(config.get("keywords", []))
        self.deduplicator = Deduplicator()

        # Initialize publishers
        active_outputs = outputs or config.get("outputs", ["console"])
        if self.dry_run:
            active_outputs = ["console"]
        elif self.test_telegram:
            active_outputs = ["telegram"]  # Only Telegram for test
        self.publishers = []
        for output in active_outputs:
            if output == "console":
                self.publishers.append(ConsolePublisher(config))
            elif output == "twitter":
                self.publishers.append(TwitterPublisher(config))
            elif output == "whatsapp":
                self.publishers.append(WhatsAppPublisher(config))
            elif output == "telegram":
                self.publishers.append(TelegramPublisher(config))
            elif output == "email":
                self.publishers.append(EmailPublisher(config))

        # Shuffle feeds
        if self.shuffle_feeds:
            random.shuffle(self.feeds)

        print(f"PapersBot initialized. Feeds: {len(self.feeds)}, Outputs: {[type(p).__name__ for p in self.publishers]}")

    def run(self):
        entries = self.reader.get_entries()
        n_seen = 0
        n_published = 0

        for entry in entries:
            if self.filter.matches(entry):
                if self._is_blacklisted(entry.title):
                    continue
                n_seen += 1
                entry_id = entry.id if "id" in entry else entry.link
                if not self.deduplicator.is_posted(entry_id):
                    message = self._build_message(entry)
                    self._publish(message)
                    if not self.test_telegram:  # Don't mark as posted in test mode
                        self.deduplicator.mark_posted(entry_id)
                    n_published += 1
                    if self.throttle > 0 and n_published >= self.throttle:
                        break
                    time.sleep(self.wait_time)

        print(f"Relevant papers: {n_seen}, Published: {n_published}")

    def _build_message(self, entry):
        title = clean_text(entry.title)
        link = entry.id if entry.id.startswith("http") else entry.link
        summary = clean_text(entry.get("summary", ""))[:200] if "summary" in entry else ""
        source = getattr(entry, 'source', {}).get('title', '') if hasattr(entry, 'source') else ''
        tags = self.filter.get_tags(entry)
        return {
            "title": title,
            "source": source,
            "summary": summary,
            "tags": tags,
            "link": link
        }

    def _is_blacklisted(self, title):
        if not title:
            return False  # Safe if no title
        for pattern in self.exclude_patterns:
            if pattern.search(title):
                return True
        return False

    def _publish(self, message):
        for publisher in self.publishers:
            publisher.publish(message)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Dry run, only console output")
    parser.add_argument("--outputs", nargs="*", help="Specific outputs to use")
    parser.add_argument("--test-telegram", action="store_true", help="Test mode: send only 1 message to Telegram")
    args = parser.parse_args()

    bot = PapersBot(dry_run=args.dry_run, outputs=args.outputs, test_telegram=args.test_telegram)
    bot.run()


if __name__ == "__main__":
    main()