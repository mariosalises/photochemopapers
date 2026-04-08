#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Deduplicator Module
# Handles posted.dat for deduplication
#

import os


class Deduplicator:
    def __init__(self, posted_file="posted.dat"):
        self.posted_file = posted_file
        self.posted = self._load_posted()

    def _load_posted(self):
        """Load list of already posted URLs."""
        try:
            with open(self.posted_file, "r") as f:
                return set(f.read().splitlines())
        except OSError:
            return set()

    def is_posted(self, url):
        """Check if URL has been posted."""
        return url in self.posted

    def mark_posted(self, url):
        """Mark URL as posted."""
        with open(self.posted_file, "a+") as f:
            print(url, file=f)
        self.posted.add(url)