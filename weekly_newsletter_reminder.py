#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Weekly Telegram reminder for newsletter subscription
#

import os

import yaml

from outputs.telegram import TelegramPublisher


def load_config():
    try:
        with open("config.yml", "r") as f:
            return yaml.safe_load(f) or {}
    except OSError:
        return {}


def resolve_newsletter_url(config):
    env_url = os.environ.get("NEWSLETTER_URL")
    if env_url:
        return env_url

    newsletter = config.get("newsletter", {}) if isinstance(config, dict) else {}
    configured_url = newsletter.get("url")
    if configured_url and configured_url != "${NEWSLETTER_URL}":
        return configured_url
    return None


def build_message(config):
    newsletter = config.get("newsletter", {}) if isinstance(config, dict) else {}
    url = resolve_newsletter_url(config)
    if not url:
        raise ValueError(
            "Newsletter URL is required. Set NEWSLETTER_URL or configure newsletter.url in config.yml."
        )

    cta = newsletter.get("cta", "Want the weekly roundup in your inbox?")
    closing = newsletter.get("closing", "Subscribe to the newsletter here:")
    return f"{cta}\n\n{closing}\n{url}"


def main():
    config = load_config()
    publisher = TelegramPublisher(config)
    publisher.publish_text(build_message(config))


if __name__ == "__main__":
    main()
