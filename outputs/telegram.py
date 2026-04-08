#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram Publisher
# Uses requests for synchronous Telegram API calls
#

import os
import requests
from bs4 import BeautifulSoup


class TelegramPublisher:
    def __init__(self, config):
        self.config = config
        self.token = None
        self.chat_id = None
        self._init_telegram()

    def _is_placeholder(self, value):
        if not value or not isinstance(value, str):
            return True
        value = value.strip()
        placeholders = [
            "YOUR_TELEGRAM_TOKEN",
            "YOUR_TELEGRAM_CHAT_ID",
            "${TELEGRAM_TOKEN}",
            "${TELEGRAM_CHAT_ID}",
            "TELEGRAM_TOKEN",
            "TELEGRAM_CHAT_ID",
        ]
        return any(value == placeholder for placeholder in placeholders)

    def _init_telegram(self):
        cred = self.config.get('telegram', {}) if isinstance(self.config, dict) else {}
        token = os.environ.get('TELEGRAM_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

        if not token:
            config_token = cred.get('token')
            if config_token and not self._is_placeholder(config_token):
                token = config_token

        if not chat_id:
            config_chat_id = cred.get('chat_id')
            if config_chat_id and not self._is_placeholder(config_chat_id):
                chat_id = config_chat_id

        if not token:
            raise ValueError(
                "Telegram token is required. Set TELEGRAM_TOKEN in the environment or a real 'telegram.token' in config.yml."
            )
        if not chat_id:
            raise ValueError(
                "Telegram chat_id is required. Set TELEGRAM_CHAT_ID in the environment or a real 'telegram.chat_id' in config.yml."
            )

        self.token = token
        self.chat_id = chat_id
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