#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Output publisher factory
#

from outputs.console import ConsolePublisher
from outputs.bluesky import BlueskyPublisher
from outputs.email import EmailPublisher
from outputs.telegram import TelegramPublisher
from outputs.twitter_x import TwitterPublisher
from outputs.whatsapp import WhatsAppPublisher


PUBLISHER_MAP = {
    "console": ConsolePublisher,
    "bluesky": BlueskyPublisher,
    "twitter": TwitterPublisher,
    "whatsapp": WhatsAppPublisher,
    "telegram": TelegramPublisher,
    "email": EmailPublisher,
}


def build_publishers(active_outputs, config):
    publishers = []
    for output_name in active_outputs:
        publisher_cls = PUBLISHER_MAP.get(output_name)
        if publisher_cls is None:
            print(f"Unknown output '{output_name}', skipping")
            continue
        publishers.append(publisher_cls(config))
    return publishers
