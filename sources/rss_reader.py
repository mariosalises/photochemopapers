#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# RSS Reader Module
# Extracts RSS feed reading logic from papersbot.py
#

import feedparser


class RSSReader:
    def __init__(self, feeds_list):
        self.feeds = feeds_list

    def get_entries(self):
        """Read all feeds and return a list of entries."""
        all_entries = []
        for feed_url in self.feeds:
            try:
                parsed_feed = feedparser.parse(feed_url)
                all_entries.extend(parsed_feed.entries)
            except Exception as e:
                print(f"Error reading feed {feed_url}: {e}")
        return all_entries