#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Keyword Filter Module
# Configurable keyword-based filtering
#

import re


class KeywordFilter:
    def __init__(self, keywords_config):
        # Flatten keywords from grouped config
        self.keywords = []
        if isinstance(keywords_config, dict):
            for category, terms in keywords_config.items():
                if isinstance(terms, list):
                    self.keywords.extend(terms)
        elif isinstance(keywords_config, list):
            self.keywords = keywords_config

        # Compile regex (case-insensitive, word boundaries for precision)
        pattern = r'\b(?:' + '|'.join(re.escape(kw) for kw in self.keywords) + r')\b'
        self.regex = re.compile(pattern, re.IGNORECASE)

    def matches(self, entry):
        """Check if entry matches any keyword in title or summary."""
        if "title" not in entry:
            return False
        if self.regex.search(entry.title):
            return True
        if "summary" in entry and self.regex.search(entry.summary):
            return True
        return False

    def get_tags(self, entry):
        """Extract matching tags from entry."""
        tags = []
        text = (entry.title or "") + " " + (entry.get("summary", "") or "")
        for kw in self.keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                # Shorten tags: e.g., ruthenium -> Ru, photodynamic -> PDT
                tag_map = {
                    'ruthenium': 'Ru', 'iridium': 'Ir', 'osmium': 'Os',
                    'platinum': 'Pt', 'rhenium': 'Re', 'photodynamic': 'PDT',
                    'photoactivated': 'PACT', 'photosensitizer': 'PS',
                    'singlet oxygen': '¹O₂', 'ROS': 'ROS'
                }
                tags.append(tag_map.get(kw.lower(), kw[:3].upper()))
        return list(set(tags))  # Unique tags
