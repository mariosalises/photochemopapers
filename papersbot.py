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
from filters.scoring import DEFAULT_SCORING_CONFIG, RuleBasedScorer
from storage.deduplicator import Deduplicator
from outputs.factory import build_publishers


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
    def __init__(self, dry_run=True, outputs=None, test_telegram=False, test_bluesky=False):
        self.feeds = read_feeds_list()
        self.dry_run = dry_run
        self.test_telegram = test_telegram
        self.test_bluesky = test_bluesky

        # Load config
        try:
            with open("config.yml", "r") as f:
                config = yaml.safe_load(f)
        except OSError:
            config = {}
        config = config or {}
        self.config = config

        self.throttle = 1 if (self.test_telegram or self.test_bluesky) else self.config.get("throttle", 0)
        self.wait_time = self.config.get("wait_time", 5)
        self.shuffle_feeds = self.config.get("shuffle_feeds", True)
        self.blacklist = self.config.get("blacklist", [])
        self.blacklist = [__import__('re').compile(s) for s in self.blacklist]
        self.scoring_config = self.config.get("scoring", DEFAULT_SCORING_CONFIG)

        # Initialize modules
        self.reader = RSSReader(self.feeds)
        self.filter = KeywordFilter(self.config.get("keywords", []))
        self.scorer = RuleBasedScorer(self.scoring_config)
        self.deduplicator = Deduplicator()

        # Initialize publishers
        active_outputs = outputs or self.config.get("outputs", ["console"])
        if self.dry_run:
            active_outputs = ["console"]
        elif self.test_telegram:
            active_outputs = ["telegram"]  # Only Telegram for test
        elif self.test_bluesky:
            active_outputs = ["bluesky"]  # Only Bluesky for test
        self.publishers = build_publishers(active_outputs, self.config)

        # Shuffle feeds
        if self.shuffle_feeds:
            random.shuffle(self.feeds)

        print(f"PapersBot initialized. Feeds: {len(self.feeds)}, Outputs: {[type(p).__name__ for p in self.publishers]}")

    def run(self):
        messages = self.get_candidate_messages(exclude_posted=True)
        n_seen = len(messages)
        n_published = 0

        for message in messages:
            self._publish(message)
            if not self.test_telegram and not self.test_bluesky:  # Don't mark as posted in test mode
                self.deduplicator.mark_posted(message["entry_id"])
            n_published += 1
            if self.throttle > 0 and n_published >= self.throttle:
                break
            time.sleep(self.wait_time)

        print(f"Relevant papers: {n_seen}, Published: {n_published}")

    def get_candidate_messages(self, exclude_posted=True):
        entries = self.reader.get_entries()
        messages = []
        seen_entry_ids = set()

        for entry in entries:
            if not self.filter.matches(entry):
                continue
            if self.scorer.is_directly_excluded(entry):
                continue
            if self._is_blacklisted(entry.title):
                continue

            entry_id = entry.id if "id" in entry else entry.link
            if entry_id in seen_entry_ids:
                continue
            if exclude_posted and self.deduplicator.is_posted(entry_id):
                continue

            seen_entry_ids.add(entry_id)
            messages.append(self._build_message(entry))

        return messages

    def _build_message(self, entry):
        entry_id = entry.id if "id" in entry else entry.link
        title = clean_text(entry.title)
        link = entry.id if entry.id.startswith("http") else entry.link
        summary = clean_text(entry.get("summary", ""))[:200] if "summary" in entry else ""
        source = getattr(entry, 'source', {}).get('title', '') if hasattr(entry, 'source') else ''
        tags = self.filter.get_tags(entry)
        score_data = self.scorer.score_entry(entry)
        return {
            "title": title,
            "source": source,
            "summary": summary,
            "tags": tags,
            "link": link,
            "entry_id": entry_id,
            "score": score_data["score"],
            "score_reasons": score_data["reasons"],
            "score_contexts": score_data["contexts"],
        }

    def _is_blacklisted(self, title):
        if not title:
            return False  # Safe if no title
        return any(pattern.search(title) for pattern in self.blacklist)

    def _publish(self, message):
        for publisher in self.publishers:
            publisher.publish(message)

    def sort_messages_by_score(self, messages):
        return self.scorer.sort_messages(messages)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Dry run, only console output")
    parser.add_argument("--outputs", nargs="*", help="Specific outputs to use")
    parser.add_argument("--test-telegram", action="store_true", help="Test mode: send only 1 message to Telegram")
    parser.add_argument("--test-bluesky", action="store_true", help="Test mode: send only 1 post to Bluesky")
    args = parser.parse_args()

    bot = PapersBot(
        dry_run=args.dry_run,
        outputs=args.outputs,
        test_telegram=args.test_telegram,
        test_bluesky=args.test_bluesky,
    )
    bot.run()


if __name__ == "__main__":
    main()
