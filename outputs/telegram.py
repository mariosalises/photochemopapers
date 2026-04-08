#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram Publisher
# Uses requests for synchronous Telegram API calls
#

import requests
from bs4 import BeautifulSoup


class TelegramPublisher:
    def __init__(self, config):
        self.config = config
        self.token = None
        self.chat_id = None
        if 'telegram' in config:
            self._init_telegram()

    def _init_telegram(self):
        cred = self.config['telegram']
        if not cred.get('token'):
            raise ValueError("Telegram token is required. Set 'telegram.token' in config.yml")
        if not cred.get('chat_id'):
            raise ValueError("Telegram chat_id is required. Set 'telegram.chat_id' in config.yml")
        self.token = cred['token']
        self.chat_id = cred['chat_id']
        print("Telegram initialized")

    def publish(self, message):
        if not self.token or not self.chat_id:
            return
        # Clean HTML from all text fields
        title = self._clean_html(message['title'])
        source = self._clean_source(message.get('source', ''))
        summary = self._clean_summary(message.get('summary', ''))
        tags = message.get('tags', [])
        link = message['link']

        # Header with emoji
        header = self._get_header(tags)
        text = f"{header} {title}\n"
        if source:
            text += f"📖 {source}\n"
        if summary:
            text += f"📝 {summary}\n"
        text += f"🔗 {link}"

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': None  # Plain text
        }
        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            print("Telegram message sent successfully")
        except requests.exceptions.RequestException as e:
            print(f"Telegram send failed: {e}")
            raise

    def _clean_html(self, text):
        """Remove all HTML tags from text."""
        if not text:
            return ""
        return BeautifulSoup(text, "html.parser").get_text()

    def _get_header(self, tags):
        """Get thematic emoji based on tags."""
        if any(tag in ['PDT', 'PACT', 'photodynamic', 'photoactivated'] for tag in tags):
            return "☀️"
        return "🧪"

    def _clean_source(self, source):
        """Clean and abbreviate source name."""
        if not source:
            return ""
        # Remove common RSS artifacts
        source = source.replace("Table of Contents", "").replace("TOC", "").strip()
        # Extract journal name: assume before colon or dash
        import re
        match = re.match(r'^([^:–]+)', source)
        if match:
            source = match.group(1).strip()
        # Limit length
        if len(source) > 50:
            source = source[:47] + "..."
        return source

    def _clean_summary(self, summary):
        """Clean summary, omit if poor quality."""
        if not summary:
            return ""
        # Remove HTML
        summary = self._clean_html(summary)
        # Check for poor quality: short, or contains metadata
        bad_words = ['EarlyView', 'Online', 'Published', 'DOI', 'Copyright', 'Wiley']
        if len(summary) < 50 or any(word in summary for word in bad_words):
            return ""  # Omit
        # Truncate to 150 chars
        if len(summary) > 150:
            summary = summary[:147] + "..."
        return summary