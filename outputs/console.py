#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Console Publisher
# Prints formatted messages to console for testing
#

class ConsolePublisher:
    def __init__(self, config=None):
        pass  # No config needed

    def publish(self, message):
        """Print message to console."""
        print("=== PAPER ALERT ===")
        print(f"Title: {message['title']}")
        print(f"Score: {message.get('score', 0)}")
        if message.get('score_reasons'):
            print(f"Reasons: {', '.join(message['score_reasons'])}")
        if message.get('source'):
            print(f"Source: {message['source']}")
        if message.get('summary'):
            print(f"Summary: {message['summary'][:100]}...")
        if message.get('tags'):
            print(f"Tags: {', '.join(message['tags'])}")
        print(f"Link: {message['link']}")
        print("-" * 50)
